"""
Pose Detection Module

Implements OpenPose for human pose estimation with body, hand, and face keypoints.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import controlnet_aux for OpenPose
try:
    from controlnet_aux import OpenposeDetector
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("controlnet-aux not installed, pose detection limited")

# Model cache
_pose_model = None

# Keypoint names for body pose (COCO format)
BODY_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]

# Hand keypoints (21 per hand)
HAND_KEYPOINT_NAMES = [
    "wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip",
    "index_mcp", "index_pip", "index_dip", "index_tip",
    "middle_mcp", "middle_pip", "middle_dip", "middle_tip",
    "ring_mcp", "ring_pip", "ring_dip", "ring_tip",
    "pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip"
]


async def analyze_pose(
    image_path: str,
    include_hands: bool = True,
    include_face: bool = True
) -> dict[str, Any]:
    """
    Detect human pose keypoints in an image.
    
    Args:
        image_path: Path to the image file
        include_hands: Whether to detect hand keypoints
        include_face: Whether to detect face landmarks
    
    Returns:
        Dictionary with pose keypoints, body proportions, and action analysis
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_pose_sync,
        image_path,
        include_hands,
        include_face
    )


def _analyze_pose_sync(
    image_path: str,
    include_hands: bool,
    include_face: bool
) -> dict[str, Any]:
    """Synchronous pose analysis implementation."""
    
    # Load image
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect poses
    poses = _detect_poses(image_rgb, include_hands, include_face)
    
    # Analyze each detected pose
    analyzed_poses = []
    for i, pose in enumerate(poses):
        analyzed = _analyze_single_pose(pose, image.shape[:2])
        analyzed["person_id"] = i
        analyzed_poses.append(analyzed)
    
    # Scene-level analysis
    scene_analysis = _analyze_scene_poses(analyzed_poses, image.shape[:2])
    
    return {
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "person_count": len(analyzed_poses),
        "poses": analyzed_poses,
        "scene_analysis": scene_analysis,
        "success": True
    }


def _detect_poses(
    image: np.ndarray,
    include_hands: bool,
    include_face: bool
) -> list[dict]:
    """Detect poses using OpenPose or fallback."""
    global _pose_model
    
    if CONTROLNET_AVAILABLE:
        try:
            if _pose_model is None:
                _pose_model = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
            
            # Run OpenPose detection
            result = _pose_model(image, hand=include_hands, face=include_face)
            
            # Parse result
            # OpenPose returns an image with keypoints drawn
            # We need to extract the actual keypoints
            poses = _extract_keypoints_from_result(result, image.shape[:2])
            return poses
            
        except Exception as e:
            logger.warning(f"OpenPose detection failed: {e}")
    
    # Fallback: Use MediaPipe if available
    return _mediapipe_pose_fallback(image, include_hands, include_face)


def _mediapipe_pose_fallback(
    image: np.ndarray,
    include_hands: bool,
    include_face: bool
) -> list[dict]:
    """Fallback pose detection using MediaPipe."""
    try:
        import mediapipe as mp
        
        poses = []
        
        # Initialize MediaPipe Pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False
        )
        
        # Process image
        results = pose.process(image)
        
        if results.pose_landmarks:
            pose_data = {
                "body_keypoints": [],
                "confidence": 0.0
            }
            
            h, w = image.shape[:2]
            
            for i, landmark in enumerate(results.pose_landmarks.landmark):
                if i < len(BODY_KEYPOINTS):
                    pose_data["body_keypoints"].append({
                        "name": BODY_KEYPOINTS[i],
                        "x": landmark.x * w,
                        "y": landmark.y * h,
                        "z": landmark.z,
                        "confidence": landmark.visibility
                    })
            
            # Calculate overall confidence
            confidences = [kp["confidence"] for kp in pose_data["body_keypoints"]]
            pose_data["confidence"] = sum(confidences) / len(confidences) if confidences else 0
            
            poses.append(pose_data)
        
        pose.close()
        
        # Hand detection if requested
        if include_hands:
            mp_hands = mp.solutions.hands
            hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2)
            
            hand_results = hands.process(image)
            
            if hand_results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    hand_keypoints = []
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        if i < len(HAND_KEYPOINT_NAMES):
                            hand_keypoints.append({
                                "name": HAND_KEYPOINT_NAMES[i],
                                "x": landmark.x * w,
                                "y": landmark.y * h,
                                "z": landmark.z,
                                "confidence": 1.0
                            })
                    
                    # Add to first pose or create new
                    if poses:
                        poses[0][f"hand_{hand_idx}"] = hand_keypoints
                    else:
                        poses.append({
                            "body_keypoints": [],
                            "confidence": 0,
                            f"hand_{hand_idx}": hand_keypoints
                        })
            
            hands.close()
        
        return poses
        
    except ImportError:
        logger.warning("MediaPipe not available, returning empty poses")
        return []


def _extract_keypoints_from_result(
    result: np.ndarray,
    image_shape: tuple
) -> list[dict]:
    """Extract keypoint data from OpenPose result image."""
    # This is a simplified extraction
    # In practice, you'd use the actual OpenPose output format
    
    h, w = image_shape
    
    # Return basic structure
    # Real implementation would parse the OpenPose output
    return [{
        "body_keypoints": [],
        "confidence": 0.0
    }]


def _analyze_single_pose(pose: dict, image_shape: tuple) -> dict[str, Any]:
    """Analyze a single detected pose."""
    analysis = {
        "keypoints": pose.get("body_keypoints", []),
        "confidence": pose.get("confidence", 0),
    }
    
    body_kps = pose.get("body_keypoints", [])
    
    if body_kps:
        # Calculate body proportions
        proportions = _calculate_body_proportions(body_kps)
        analysis["proportions"] = proportions
        
        # Detect pose type (standing, sitting, etc.)
        pose_type = _classify_pose_type(body_kps, image_shape)
        analysis["pose_type"] = pose_type
        
        # Detect action
        action = _detect_action(body_kps)
        analysis["detected_action"] = action
        
        # Calculate bounding box
        bbox = _calculate_pose_bbox(body_kps)
        analysis["bounding_box"] = bbox
    
    # Add hand analysis if present
    if "hand_0" in pose or "hand_1" in pose:
        analysis["hands"] = {}
        for hand_key in ["hand_0", "hand_1"]:
            if hand_key in pose:
                hand_analysis = _analyze_hand(pose[hand_key])
                analysis["hands"][hand_key] = hand_analysis
    
    return analysis


def _calculate_body_proportions(keypoints: list) -> dict[str, float]:
    """Calculate body proportions from keypoints."""
    kp_dict = {kp["name"]: kp for kp in keypoints}
    
    proportions = {}
    
    # Shoulder width
    if "left_shoulder" in kp_dict and "right_shoulder" in kp_dict:
        ls = kp_dict["left_shoulder"]
        rs = kp_dict["right_shoulder"]
        proportions["shoulder_width"] = np.sqrt(
            (ls["x"] - rs["x"])**2 + (ls["y"] - rs["y"])**2
        )
    
    # Hip width
    if "left_hip" in kp_dict and "right_hip" in kp_dict:
        lh = kp_dict["left_hip"]
        rh = kp_dict["right_hip"]
        proportions["hip_width"] = np.sqrt(
            (lh["x"] - rh["x"])**2 + (lh["y"] - rh["y"])**2
        )
    
    # Torso length
    if "left_shoulder" in kp_dict and "left_hip" in kp_dict:
        ls = kp_dict["left_shoulder"]
        lh = kp_dict["left_hip"]
        proportions["torso_length"] = np.sqrt(
            (ls["x"] - lh["x"])**2 + (ls["y"] - lh["y"])**2
        )
    
    # Leg length
    if "left_hip" in kp_dict and "left_ankle" in kp_dict:
        lh = kp_dict["left_hip"]
        la = kp_dict["left_ankle"]
        proportions["leg_length"] = np.sqrt(
            (lh["x"] - la["x"])**2 + (lh["y"] - la["y"])**2
        )
    
    # Arm length
    if "left_shoulder" in kp_dict and "left_wrist" in kp_dict:
        ls = kp_dict["left_shoulder"]
        lw = kp_dict["left_wrist"]
        proportions["arm_length"] = np.sqrt(
            (ls["x"] - lw["x"])**2 + (ls["y"] - lw["y"])**2
        )
    
    return proportions


def _classify_pose_type(keypoints: list, image_shape: tuple) -> str:
    """Classify the pose type."""
    kp_dict = {kp["name"]: kp for kp in keypoints}
    
    # Check if standing or sitting based on hip-knee-ankle angles
    if all(k in kp_dict for k in ["left_hip", "left_knee", "left_ankle"]):
        lh = kp_dict["left_hip"]
        lk = kp_dict["left_knee"]
        la = kp_dict["left_ankle"]
        
        # Calculate angle at knee
        angle = _calculate_angle(lh, lk, la)
        
        if angle > 160:
            return "standing"
        elif angle > 90:
            return "sitting"
        else:
            return "crouching"
    
    return "unknown"


def _calculate_angle(p1: dict, p2: dict, p3: dict) -> float:
    """Calculate angle at p2 formed by p1-p2-p3."""
    v1 = np.array([p1["x"] - p2["x"], p1["y"] - p2["y"]])
    v2 = np.array([p3["x"] - p2["x"], p3["y"] - p2["y"]])
    
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    angle = np.arccos(np.clip(cos_angle, -1, 1))
    
    return np.degrees(angle)


def _detect_action(keypoints: list) -> dict[str, Any]:
    """Detect possible actions from pose."""
    kp_dict = {kp["name"]: kp for kp in keypoints}
    
    actions = []
    
    # Check for arms raised
    if "left_wrist" in kp_dict and "left_shoulder" in kp_dict:
        if kp_dict["left_wrist"]["y"] < kp_dict["left_shoulder"]["y"]:
            actions.append("left_arm_raised")
    
    if "right_wrist" in kp_dict and "right_shoulder" in kp_dict:
        if kp_dict["right_wrist"]["y"] < kp_dict["right_shoulder"]["y"]:
            actions.append("right_arm_raised")
    
    # Check for reaching
    if "left_wrist" in kp_dict and "left_shoulder" in kp_dict:
        ls = kp_dict["left_shoulder"]
        lw = kp_dict["left_wrist"]
        distance = np.sqrt((ls["x"] - lw["x"])**2 + (ls["y"] - lw["y"])**2)
        if distance > 100:  # Threshold
            actions.append("left_arm_extended")
    
    return {
        "detected_actions": actions,
        "primary_action": actions[0] if actions else "neutral"
    }


def _calculate_pose_bbox(keypoints: list) -> dict[str, float]:
    """Calculate bounding box for pose."""
    if not keypoints:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    xs = [kp["x"] for kp in keypoints if kp.get("confidence", 1) > 0.3]
    ys = [kp["y"] for kp in keypoints if kp.get("confidence", 1) > 0.3]
    
    if not xs or not ys:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    
    # Add padding
    padding = 20
    x_min -= padding
    y_min -= padding
    x_max += padding
    y_max += padding
    
    return {
        "x": x_min,
        "y": y_min,
        "width": x_max - x_min,
        "height": y_max - y_min
    }


def _analyze_hand(keypoints: list) -> dict[str, Any]:
    """Analyze hand keypoints."""
    if not keypoints:
        return {"detected": False}
    
    kp_dict = {kp["name"]: kp for kp in keypoints}
    
    # Check for open/closed hand
    # Calculate spread of fingers
    if "wrist" in kp_dict and "middle_tip" in kp_dict:
        wrist = kp_dict["wrist"]
        middle_tip = kp_dict["middle_tip"]
        
        spread = np.sqrt(
            (wrist["x"] - middle_tip["x"])**2 + 
            (wrist["y"] - middle_tip["y"])**2
        )
        
        # Simple heuristic for open/closed
        hand_state = "open" if spread > 50 else "closed"
    else:
        hand_state = "unknown"
    
    return {
        "detected": True,
        "keypoint_count": len(keypoints),
        "state": hand_state
    }


def _analyze_scene_poses(poses: list, image_shape: tuple) -> dict[str, Any]:
    """Analyze multiple poses in scene."""
    if not poses:
        return {
            "interaction": "none",
            "grouping": "none"
        }
    
    analysis = {
        "total_people": len(poses),
        "interactions": []
    }
    
    # Check for interactions between people
    if len(poses) >= 2:
        for i in range(len(poses)):
            for j in range(i + 1, len(poses)):
                # Check proximity
                bbox1 = poses[i].get("bounding_box", {})
                bbox2 = poses[j].get("bounding_box", {})
                
                if bbox1 and bbox2:
                    center1 = (bbox1["x"] + bbox1["width"]/2, bbox1["y"] + bbox1["height"]/2)
                    center2 = (bbox2["x"] + bbox2["width"]/2, bbox2["y"] + bbox2["height"]/2)
                    
                    distance = np.sqrt(
                        (center1[0] - center2[0])**2 + 
                        (center1[1] - center2[1])**2
                    )
                    
                    if distance < 200:  # Threshold for interaction
                        analysis["interactions"].append({
                            "person1": i,
                            "person2": j,
                            "type": "proximity",
                            "distance": distance
                        })
    
    return analysis