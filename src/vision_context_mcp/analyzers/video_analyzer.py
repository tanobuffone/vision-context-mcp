"""
Video Analyzer Module

Provides video analysis including frame extraction, temporal analysis,
scene change detection, and motion tracking.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


async def extract_frames(
    video_path: str,
    output_dir: Optional[str] = None,
    fps: float = 1.0,
    max_frames: int = 100
) -> dict[str, Any]:
    """
    Extract frames from a video.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save frames (optional)
        fps: Frames per second to extract
        max_frames: Maximum number of frames to extract
    
    Returns:
        Dictionary with extracted frame information
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _extract_frames_sync,
        video_path,
        output_dir,
        fps,
        max_frames
    )


def _extract_frames_sync(
    video_path: str,
    output_dir: Optional[str],
    fps: float,
    max_frames: int
) -> dict[str, Any]:
    """Synchronous frame extraction."""
    
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps if video_fps > 0 else 0
    
    frame_interval = int(video_fps / fps) if fps > 0 else 1
    
    frames = []
    frame_count = 0
    extracted_count = 0
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    while cap.isOpened() and extracted_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            frame_info = {
                "frame_number": frame_count,
                "timestamp": frame_count / video_fps if video_fps > 0 else 0,
                "shape": list(frame.shape)
            }
            
            if output_dir:
                frame_filename = f"frame_{extracted_count:06d}.jpg"
                frame_path = output_path / frame_filename
                cv2.imwrite(str(frame_path), frame)
                frame_info["path"] = str(frame_path)
            
            frames.append(frame_info)
            extracted_count += 1
        
        frame_count += 1
    
    cap.release()
    
    return {
        "video_path": str(path),
        "video_info": {
            "fps": video_fps,
            "total_frames": total_frames,
            "duration_seconds": duration,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        },
        "extraction_config": {
            "target_fps": fps,
            "frame_interval": frame_interval,
            "max_frames": max_frames
        },
        "extracted_frames": frames,
        "frame_count": len(frames),
        "success": True
    }


async def detect_scene_changes(
    video_path: str,
    threshold: float = 30.0,
    min_scene_length: int = 10
) -> dict[str, Any]:
    """
    Detect scene changes in a video.
    
    Args:
        video_path: Path to the video file
        threshold: Threshold for scene change detection
        min_scene_length: Minimum frames between scene changes
    
    Returns:
        Dictionary with scene change information
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _detect_scene_changes_sync,
        video_path,
        threshold,
        min_scene_length
    )


def _detect_scene_changes_sync(
    video_path: str,
    threshold: float,
    min_scene_length: int
) -> dict[str, Any]:
    """Synchronous scene change detection."""
    
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    scene_changes = []
    prev_frame = None
    frame_count = 0
    last_change = -min_scene_length
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if prev_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(prev_frame, gray)
            diff_score = np.mean(diff)
            
            # Check for scene change
            if diff_score > threshold and (frame_count - last_change) >= min_scene_length:
                scene_changes.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count / video_fps if video_fps > 0 else 0,
                    "change_score": float(diff_score)
                })
                last_change = frame_count
        
        prev_frame = gray
        frame_count += 1
    
    cap.release()
    
    # Create scene segments
    scenes = []
    for i, change in enumerate(scene_changes):
        start_frame = scene_changes[i-1]["frame_number"] if i > 0 else 0
        end_frame = change["frame_number"]
        
        scenes.append({
            "scene_id": i,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "duration_frames": end_frame - start_frame,
            "duration_seconds": (end_frame - start_frame) / video_fps if video_fps > 0 else 0
        })
    
    # Add last scene
    if scene_changes:
        last_change_frame = scene_changes[-1]["frame_number"]
        scenes.append({
            "scene_id": len(scene_changes),
            "start_frame": last_change_frame,
            "end_frame": total_frames,
            "duration_frames": total_frames - last_change_frame,
            "duration_seconds": (total_frames - last_change_frame) / video_fps if video_fps > 0 else 0
        })
    
    return {
        "video_path": str(path),
        "total_frames": total_frames,
        "video_duration_seconds": total_frames / video_fps if video_fps > 0 else 0,
        "scene_changes": scene_changes,
        "scenes": scenes,
        "scene_count": len(scenes),
        "success": True
    }


async def analyze_motion(
    video_path: str,
    sample_rate: int = 30
) -> dict[str, Any]:
    """
    Analyze motion in a video.
    
    Args:
        video_path: Path to the video file
        sample_rate: Analyze every N frames
    
    Returns:
        Dictionary with motion analysis
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_motion_sync,
        video_path,
        sample_rate
    )


def _analyze_motion_sync(video_path: str, sample_rate: int) -> dict[str, Any]:
    """Synchronous motion analysis."""
    
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    
    motion_data = []
    prev_frame = None
    frame_count = 0
    
    # Initialize background subtractor
    fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % sample_rate == 0:
            # Apply background subtraction
            fgmask = fgbg.apply(frame)
            
            # Calculate motion metrics
            motion_pixels = np.sum(fgmask > 0)
            total_pixels = fgmask.shape[0] * fgmask.shape[1]
            motion_ratio = motion_pixels / total_pixels
            
            # Find motion contours
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_regions = []
            for contour in contours[:5]:  # Top 5 regions
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                if area > 100:  # Filter small noise
                    motion_regions.append({
                        "bounding_box": {"x": x, "y": y, "width": w, "height": h},
                        "area": float(area)
                    })
            
            motion_data.append({
                "frame_number": frame_count,
                "timestamp": frame_count / video_fps if video_fps > 0 else 0,
                "motion_ratio": float(motion_ratio),
                "motion_pixel_count": int(motion_pixels),
                "motion_regions": motion_regions
            })
        
        frame_count += 1
    
    cap.release()
    
    # Calculate motion statistics
    if motion_data:
        motion_ratios = [m["motion_ratio"] for m in motion_data]
        motion_stats = {
            "mean_motion": float(np.mean(motion_ratios)),
            "max_motion": float(np.max(motion_ratios)),
            "min_motion": float(np.min(motion_ratios)),
            "std_motion": float(np.std(motion_ratios)),
            "high_motion_frames": sum(1 for r in motion_ratios if r > 0.1),
            "low_motion_frames": sum(1 for r in motion_ratios if r < 0.01)
        }
    else:
        motion_stats = {}
    
    return {
        "video_path": str(path),
        "sample_rate": sample_rate,
        "motion_statistics": motion_stats,
        "motion_data": motion_data,
        "total_analyzed_frames": len(motion_data),
        "success": True
    }


async def get_video_context(
    video_path: str,
    extract_keyframes: bool = True,
    analyze_temporal: bool = True
) -> dict[str, Any]:
    """
    Get comprehensive context from a video.
    
    Args:
        video_path: Path to the video file
        extract_keyframes: Extract keyframes
        analyze_temporal: Analyze temporal patterns
    
    Returns:
        Dictionary with video context
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _get_video_context_sync,
        video_path,
        extract_keyframes,
        analyze_temporal
    )


def _get_video_context_sync(
    video_path: str,
    extract_keyframes: bool,
    analyze_temporal: bool
) -> dict[str, Any]:
    """Synchronous video context extraction."""
    
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / video_fps if video_fps > 0 else 0
    
    context = {
        "video_path": str(path),
        "video_info": {
            "fps": video_fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "resolution": f"{width}x{height}",
            "aspect_ratio": width / height if height > 0 else 0
        }
    }
    
    cap.release()
    
    # Scene changes
    try:
        scene_result = _detect_scene_changes_sync(video_path, 30.0, 30)
        context["scene_analysis"] = {
            "scene_count": scene_result["scene_count"],
            "scenes": scene_result["scenes"],
            "change_timestamps": [s["timestamp"] for s in scene_result["scene_changes"]]
        }
    except Exception as e:
        logger.warning(f"Scene detection failed: {e}")
        context["scene_analysis"] = {"error": str(e)}
    
    # Motion analysis
    if analyze_temporal:
        try:
            motion_result = _analyze_motion_sync(video_path, 30)
            context["motion_analysis"] = motion_result["motion_statistics"]
            context["motion_summary"] = {
                "activity_level": "high" if motion_result["motion_statistics"].get("mean_motion", 0) > 0.1 
                                   else "low" if motion_result["motion_statistics"].get("mean_motion", 0) < 0.05 
                                   else "moderate",
                "has_significant_motion": motion_result["motion_statistics"].get("high_motion_frames", 0) > 0
            }
        except Exception as e:
            logger.warning(f"Motion analysis failed: {e}")
            context["motion_analysis"] = {"error": str(e)}
    
    # Generate summary
    context["summary"] = _generate_video_summary(context)
    
    return context


def _generate_video_summary(context: dict) -> str:
    """Generate a text summary of the video."""
    parts = []
    
    info = context.get("video_info", {})
    parts.append(f"Video: {info.get('width', 0)}x{info.get('height', 0)}, "
                 f"{info.get('duration_seconds', 0):.1f}s at {info.get('fps', 0):.1f} fps")
    
    scene = context.get("scene_analysis", {})
    if "scene_count" in scene:
        parts.append(f"Contains {scene['scene_count']} scenes")
    
    motion = context.get("motion_analysis", {})
    if "mean_motion" in motion:
        activity = "high" if motion["mean_motion"] > 0.1 else "low" if motion["mean_motion"] < 0.05 else "moderate"
        parts.append(f"Motion activity: {activity}")
    
    return ". ".join(parts) + "."


async def extract_keyframe_at(
    video_path: str,
    timestamp: float,
    output_path: Optional[str] = None
) -> dict[str, Any]:
    """
    Extract a specific frame from video by timestamp.
    
    Args:
        video_path: Path to the video file
        timestamp: Timestamp in seconds
        output_path: Path to save the frame (optional)
    
    Returns:
        Dictionary with frame information
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _extract_keyframe_at_sync,
        video_path,
        timestamp,
        output_path
    )


def _extract_keyframe_at_sync(
    video_path: str,
    timestamp: float,
    output_path: Optional[str]
) -> dict[str, Any]:
    """Extract frame at specific timestamp."""
    
    path = Path(video_path)
    cap = cv2.VideoCapture(str(path))
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    target_frame = int(timestamp * video_fps)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError(f"Could not extract frame at timestamp {timestamp}")
    
    result = {
        "video_path": str(path),
        "timestamp": timestamp,
        "frame_number": target_frame,
        "frame_shape": list(frame.shape)
    }
    
    if output_path:
        cv2.imwrite(output_path, frame)
        result["output_path"] = output_path
    
    return result