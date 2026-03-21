"""
3D Entity Extractor Module

Extracts objects from images and represents them as 3D entities with positions, 
dimensions, and depth for rendering.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import object detection models
try:
    import torch
    from transformers import DetrImageProcessor, DetrForObjectDetection
    DETR_AVAILABLE = True
except ImportError:
    DETR_AVAILABLE = False

# Model cache
_detection_model = None
_processor = None

# COCO class names
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"
]


async def detect_objects(
    image_path: str,
    confidence: float = 0.5,
    include_depth: bool = True
) -> dict[str, Any]:
    """
    Detect objects in an image.
    
    Args:
        image_path: Path to the image file
        confidence: Minimum confidence threshold
        include_depth: Whether to estimate depth for 3D positioning
    
    Returns:
        Dictionary with detected objects, bounding boxes, and 3D positions
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _detect_objects_sync,
        image_path,
        confidence,
        include_depth
    )


def _detect_objects_sync(
    image_path: str,
    confidence: float,
    include_depth: bool
) -> dict[str, Any]:
    """Synchronous object detection implementation."""
    
    # Load image
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Run object detection
    detections = _run_detection(image_rgb, confidence)
    
    # Estimate depth if requested
    if include_depth:
        depth_map = _estimate_depth_for_objects(image_rgb)
        detections = _add_depth_to_detections(detections, depth_map, image.shape[:2])
    
    return {
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "object_count": len(detections),
        "objects": detections,
        "success": True
    }


async def extract_entities_3d(
    image_path: str,
    output_format: str = "json"
) -> dict[str, Any]:
    """
    Extract objects as 3D entities.
    
    Args:
        image_path: Path to the image file
        output_format: Output format (json, obj, glb)
    
    Returns:
        Dictionary with 3D entity data
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _extract_entities_3d_sync,
        image_path,
        output_format
    )


def _extract_entities_3d_sync(
    image_path: str,
    output_format: str
) -> dict[str, Any]:
    """Synchronous 3D entity extraction."""
    
    # Load image
    path = Path(image_path)
    image = cv2.imread(str(path))
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect objects
    detections = _run_detection(image_rgb, confidence=0.3)
    
    # Get depth map
    depth_map = _estimate_depth_for_objects(image_rgb)
    
    # Create 3D entities
    entities = []
    
    for det in detections:
        entity = _create_3d_entity(det, depth_map, image.shape[:2])
        entities.append(entity)
    
    # Create scene structure
    scene = {
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "entities": entities,
        "entity_count": len(entities),
        "coordinate_system": {
            "origin": "top_left",
            "x_axis": "right",
            "y_axis": "down",
            "z_axis": "into_screen"
        }
    }
    
    return scene


def _run_detection(image: np.ndarray, confidence: float) -> list[dict]:
    """Run object detection model."""
    global _detection_model, _processor
    
    if DETR_AVAILABLE:
        try:
            if _detection_model is None:
                model_name = "facebook/detr-resnet-50"
                _processor = DetrImageProcessor.from_pretrained(model_name)
                _detection_model = DetrForObjectDetection.from_pretrained(model_name)
            
            # Process image
            from PIL import Image
            pil_image = Image.fromarray(image)
            inputs = _processor(images=pil_image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = _detection_model(**inputs)
            
            # Post-process
            target_sizes = torch.tensor([image.shape[:2]])
            results = _processor.post_process_object_detection(
                outputs, threshold=confidence, target_sizes=target_sizes
            )[0]
            
            detections = []
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                box = [int(i) for i in box.tolist()]
                label_idx = label.item()
                class_name = COCO_CLASSES[label_idx] if label_idx < len(COCO_CLASSES) else f"class_{label_idx}"
                
                detections.append({
                    "label": class_name,
                    "confidence": round(score.item(), 3),
                    "bounding_box": {
                        "x": box[0],
                        "y": box[1],
                        "width": box[2] - box[0],
                        "height": box[3] - box[1]
                    },
                    "center": {
                        "x": (box[0] + box[2]) // 2,
                        "y": (box[1] + box[3]) // 2
                    }
                })
            
            return detections
            
        except Exception as e:
            logger.warning(f"DETR detection failed: {e}")
    
    # Fallback: Simple contour-based detection
    return _simple_object_detection(image, confidence)


def _simple_object_detection(image: np.ndarray, confidence: float) -> list[dict]:
    """Simple object detection using contours."""
    detections = []
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and create detections
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        
        # Filter small objects
        if area < 1000:
            continue
        
        x, y, w, h = cv2.boundingRect(contour)
        
        detections.append({
            "label": "object",
            "confidence": 0.5,
            "bounding_box": {
                "x": x,
                "y": y,
                "width": w,
                "height": h
            },
            "center": {
                "x": x + w // 2,
                "y": y + h // 2
            }
        })
    
    return detections


def _estimate_depth_for_objects(image: np.ndarray) -> np.ndarray:
    """Estimate depth map for objects."""
    try:
        from ..preprocessors.depth import _simple_depth_estimation
        return _simple_depth_estimation(image)
    except Exception:
        # Fallback to simple estimation
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
        h = gray.shape[0]
        vertical_gradient = np.linspace(1, 0, h).reshape(-1, 1)
        return (vertical_gradient * 255).astype(np.float32)


def _add_depth_to_detections(
    detections: list,
    depth_map: np.ndarray,
    image_shape: tuple
) -> list[dict]:
    """Add depth information to detections."""
    for det in detections:
        bbox = det["bounding_box"]
        center = det["center"]
        
        # Get depth at center
        center_depth = depth_map[int(center["y"]), int(center["x"])]
        
        # Get average depth in bounding box
        x1 = max(0, bbox["x"])
        y1 = max(0, bbox["y"])
        x2 = min(image_shape[1], bbox["x"] + bbox["width"])
        y2 = min(image_shape[0], bbox["y"] + bbox["height"])
        
        avg_depth = np.mean(depth_map[y1:y2, x1:x2])
        
        det["depth"] = {
            "center_depth": float(center_depth),
            "average_depth": float(avg_depth),
            "normalized_depth": float(avg_depth / 255.0)
        }
    
    return detections


def _create_3d_entity(
    detection: dict,
    depth_map: np.ndarray,
    image_shape: tuple
) -> dict[str, Any]:
    """Create a 3D entity from detection."""
    bbox = detection["bounding_box"]
    center = detection["center"]
    depth = detection.get("depth", {})
    
    # Normalize coordinates to 0-1 range
    norm_x = center["x"] / image_shape[1]
    norm_y = center["y"] / image_shape[0]
    norm_z = depth.get("normalized_depth", 0.5)
    
    # Calculate dimensions
    norm_width = bbox["width"] / image_shape[1]
    norm_height = bbox["height"] / image_shape[0]
    
    # Estimate depth extent (approximation)
    depth_extent = norm_width * 0.5  # Rough estimate
    
    # Infer primitive type based on object
    primitive_type = _infer_primitive_type(detection["label"])
    
    return {
        "id": f"entity_{detection['label']}_{center['x']}_{center['y']}",
        "label": detection["label"],
        "confidence": detection["confidence"],
        "primitive_type": primitive_type,
        "position": {
            "x": norm_x,
            "y": norm_y,
            "z": norm_z
        },
        "dimensions": {
            "width": norm_width,
            "height": norm_height,
            "depth": depth_extent
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "bounding_box_2d": bbox,
        "depth_info": depth,
        "properties": _get_entity_properties(detection["label"])
    }


def _infer_primitive_type(label: str) -> str:
    """Infer 3D primitive type from object label."""
    # Map common objects to primitive types
    box_objects = ["car", "bus", "truck", "refrigerator", "microwave", "oven", 
                   "suitcase", "bench", "couch", "bed", "dining table", "tv", 
                   "laptop", "keyboard", "book", "box"]
    
    sphere_objects = ["ball", "orange", "apple", "pizza", "donut", "cake", 
                      "frisbee", "sports ball"]
    
    cylinder_objects = ["bottle", "wine glass", "cup", "vase", "bowl", 
                        "banana", "carrot", "hot dog"]
    
    person_objects = ["person"]
    
    if label in box_objects:
        return "box"
    elif label in sphere_objects:
        return "sphere"
    elif label in cylinder_objects:
        return "cylinder"
    elif label in person_objects:
        return "humanoid"
    else:
        return "box"  # Default


def _get_entity_properties(label: str) -> dict[str, Any]:
    """Get additional properties for entity."""
    properties = {}
    
    # Add semantic properties
    if label == "person":
        properties["animate"] = True
        properties["category"] = "human"
    elif label in ["car", "bus", "truck", "bicycle", "motorcycle"]:
        properties["animate"] = False
        properties["category"] = "vehicle"
    elif label in ["chair", "couch", "bed", "table"]:
        properties["animate"] = False
        properties["category"] = "furniture"
    elif label in ["dog", "cat", "bird", "horse", "cow", "sheep"]:
        properties["animate"] = True
        properties["category"] = "animal"
    else:
        properties["animate"] = False
        properties["category"] = "object"
    
    return properties