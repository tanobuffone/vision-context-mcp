"""
Semantic Segmentation Module

Implements ADE20K and other segmentation models for scene parsing.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import controlnet_aux for segmentation
try:
    from controlnet_aux import SegformerForSemanticSegmentation
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("controlnet-aux not installed, segmentation limited")

# Try to import transformers
try:
    from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Model cache
_seg_model = None
_processor = None

# ADE20K class names (150 classes)
ADE20K_CLASSES = [
    "wall", "building", "sky", "floor", "tree", "ceiling", "road", "bed",
    "windowpane", "grass", "cabinet", "sidewalk", "person", "earth", "door",
    "table", "mountain", "plant", "curtain", "chair", "car", "water",
    "painting", "sofa", "shelf", "house", "sea", "mirror", "rug", "field",
    "armchair", "seat", "fence", "desk", "rock", "wardrobe", "lamp",
    "bathtub", "railing", "cushion", "base", "box", "column", "signboard",
    "chest of drawers", "counter", "sand", "sink", "skyscraper", "fireplace",
    "refrigerator", "grandstand", "path", "stairs", "runway", "case",
    "pool table", "pillow", "screen door", "stairway", "river", "bridge",
    "bookcase", "blind", "coffee table", "toilet", "flower", "book",
    "hill", "bench", "countertop", "stove", "palm", "kitchen island",
    "computer", "swivel chair", "boat", "bar", "arcade machine",
    "hovel", "bus", "towel", "light", "truck", "tower", "chandelier",
    "awning", "streetlight", "booth", "television", "airplane", "dirt track",
    "apparel", "pole", "land", "bannister", "escalator", "ottoman", "bottle",
    "buffet", "poster", "stage", "van", "ship", "fountain", "conveyer belt",
    "canopy", "washer", "plaything", "swimming pool", "stool", "barrel",
    "basket", "waterfall", "tent", "bag", "minibike", "cradle", "oven",
    "ball", "food", "step", "tank", "trade name", "microwave", "pot",
    "animal", "bicycle", "lake", "dishwasher", "screen", "blanket",
    "sculpture", "hood", "sconce", "vase", "traffic light", "tray",
    "ashcan", "fan", "pier", "crt screen", "plate", "monitor", "bulletin board",
    "shower", "radiator", "glass", "clock", "flag"
]


async def analyze_segmentation(image_path: str) -> dict[str, Any]:
    """
    Perform semantic segmentation on an image.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dictionary with segmentation map, detected regions, and scene composition
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_segmentation_sync,
        image_path
    )


def _analyze_segmentation_sync(image_path: str) -> dict[str, Any]:
    """Synchronous segmentation analysis implementation."""
    
    # Load image
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Run segmentation
    segmentation_map = _run_segmentation(image_rgb)
    
    # Analyze segments
    regions = _analyze_regions(segmentation_map)
    
    # Scene composition
    composition = _analyze_composition(regions, image.shape[:2])
    
    # Spatial relationships
    relationships = _analyze_spatial_relationships(regions)
    
    return {
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "detected_regions": regions,
        "scene_composition": composition,
        "spatial_relationships": relationships,
        "segmentation_map_shape": list(segmentation_map.shape),
        "unique_classes": len(np.unique(segmentation_map)),
        "success": True
    }


def _run_segmentation(image: np.ndarray) -> np.ndarray:
    """Run semantic segmentation model."""
    global _seg_model, _processor
    
    # Try transformers first
    if TRANSFORMERS_AVAILABLE:
        try:
            if _seg_model is None:
                model_name = "nvidia/segformer-b5-finetuned-ade-640-640"
                _processor = AutoImageProcessor.from_pretrained(model_name)
                _seg_model = AutoModelForSemanticSegmentation.from_pretrained(model_name)
            
            # Process image
            pil_image = Image.fromarray(image)
            inputs = _processor(images=pil_image, return_tensors="pt")
            
            import torch
            with torch.no_grad():
                outputs = _seg_model(**inputs)
                logits = outputs.logits
            
            # Resize to original size
            logits = torch.nn.functional.interpolate(
                logits,
                size=image.shape[:2],
                mode="bilinear",
                align_corners=False
            )
            
            # Get class predictions
            segmentation = logits.argmax(dim=1).squeeze().numpy()
            
            return segmentation
            
        except Exception as e:
            logger.warning(f"Segformer failed: {e}")
    
    # Fallback: Simple color-based segmentation
    return _simple_color_segmentation(image)


def _simple_color_segmentation(image: np.ndarray) -> np.ndarray:
    """Simple color-based segmentation fallback."""
    # Convert to different color spaces
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    
    # K-means clustering for color quantization
    pixels = image.reshape(-1, 3).astype(np.float32)
    
    # Define criteria and apply kmeans
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    k = 8  # Number of clusters
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Reshape labels to image shape
    segmentation = labels.reshape(image.shape[:2])
    
    # Map to approximate ADE20K classes based on color
    # This is a rough approximation
    mapped_segmentation = np.zeros_like(segmentation)
    
    for i, center in enumerate(centers):
        # Simple heuristics for class mapping
        r, g, b = center
        
        # Sky detection (blue-ish, top of image)
        if b > r and b > g and b > 100:
            mapped_segmentation[segmentation == i] = 2  # sky
        
        # Vegetation (green-ish)
        elif g > r and g > b:
            mapped_segmentation[segmentation == i] = 4  # tree/plant
        
        # Building/wall (gray-ish)
        elif abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
            mapped_segmentation[segmentation == i] = 0  # wall
        
        # Default
        else:
            mapped_segmentation[segmentation == i] = 1  # building
    
    return mapped_segmentation


def _analyze_regions(segmentation_map: np.ndarray) -> list[dict[str, Any]]:
    """Analyze detected regions."""
    regions = []
    unique_classes = np.unique(segmentation_map)
    
    for class_id in unique_classes:
        # Get class name
        class_name = ADE20K_CLASSES[class_id] if class_id < len(ADE20K_CLASSES) else f"class_{class_id}"
        
        # Create mask for this class
        mask = (segmentation_map == class_id).astype(np.uint8)
        
        # Calculate statistics
        pixel_count = np.sum(mask)
        
        if pixel_count == 0:
            continue
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get bounding box
        coords = np.where(mask)
        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()
        
        # Calculate centroid
        centroid = {
            "x": int(np.mean(coords[1])),
            "y": int(np.mean(coords[0]))
        }
        
        regions.append({
            "class_id": int(class_id),
            "class_name": class_name,
            "pixel_count": int(pixel_count),
            "percentage": float(pixel_count / mask.size * 100),
            "bounding_box": {
                "x": int(x_min),
                "y": int(y_min),
                "width": int(x_max - x_min),
                "height": int(y_max - y_min)
            },
            "centroid": centroid,
            "contour_count": len(contours),
            "is_connected": len(contours) == 1
        })
    
    # Sort by pixel count (largest first)
    regions.sort(key=lambda r: r["pixel_count"], reverse=True)
    
    return regions


def _analyze_composition(regions: list, image_shape: tuple) -> dict[str, Any]:
    """Analyze scene composition."""
    h, w = image_shape
    
    # Divide image into thirds
    thirds_h = h // 3
    thirds_w = w // 3
    
    composition = {
        "dominant_objects": [],
        "foreground_objects": [],
        "background_objects": [],
        "scene_type": "unknown"
    }
    
    for region in regions[:10]:  # Top 10 regions
        class_name = region["class_name"]
        centroid = region["centroid"]
        
        # Determine position in frame
        if centroid["y"] < thirds_h:
            position = "top"
        elif centroid["y"] > 2 * thirds_h:
            position = "bottom"
        else:
            position = "middle"
        
        # Classify as foreground/background based on size and position
        if region["percentage"] > 10:
            composition["dominant_objects"].append({
                "name": class_name,
                "position": position,
                "size": region["percentage"]
            })
        
        # Scene type inference
        if class_name in ["sky", "mountain", "tree", "grass", "road"]:
            if class_name not in [o["name"] for o in composition["background_objects"]]:
                composition["background_objects"].append({
                    "name": class_name,
                    "position": position
                })
        
        if class_name in ["person", "car", "chair", "table", "bed"]:
            if class_name not in [o["name"] for o in composition["foreground_objects"]]:
                composition["foreground_objects"].append({
                    "name": class_name,
                    "position": position
                })
    
    # Infer scene type
    class_names = [r["class_name"] for r in regions]
    
    if any(c in class_names for c in ["bed", "pillow", "wardrobe"]):
        composition["scene_type"] = "bedroom"
    elif any(c in class_names for c in ["sofa", "television", "coffee table"]):
        composition["scene_type"] = "living_room"
    elif any(c in class_names for c in ["stove", "refrigerator", "kitchen island"]):
        composition["scene_type"] = "kitchen"
    elif any(c in class_names for c in ["sky", "tree", "grass", "road"]):
        composition["scene_type"] = "outdoor"
    elif any(c in class_names for c in ["building", "sidewalk", "car"]):
        composition["scene_type"] = "urban"
    
    return composition


def _analyze_spatial_relationships(regions: list) -> list[dict[str, Any]]:
    """Analyze spatial relationships between objects."""
    relationships = []
    
    # Compare top regions
    for i, region1 in enumerate(regions[:5]):
        for j, region2 in enumerate(regions[:5]):
            if i >= j:
                continue
            
            bbox1 = region1["bounding_box"]
            bbox2 = region2["bounding_box"]
            
            # Determine spatial relationship
            rel = _determine_relationship(bbox1, bbox2, region1["class_name"], region2["class_name"])
            
            if rel:
                relationships.append(rel)
    
    return relationships


def _determine_relationship(
    bbox1: dict, bbox2: dict,
    name1: str, name2: str
) -> Optional[dict[str, Any]]:
    """Determine spatial relationship between two objects."""
    
    # Calculate centers
    center1 = (bbox1["x"] + bbox1["width"] / 2, bbox1["y"] + bbox1["height"] / 2)
    center2 = (bbox2["x"] + bbox2["width"] / 2, bbox2["y"] + bbox2["height"] / 2)
    
    dx = center2[0] - center1[0]
    dy = center2[1] - center1[1]
    
    # Determine horizontal relationship
    if abs(dx) > abs(dy):
        if dx > 0:
            position = "right"
        else:
            position = "left"
    else:
        if dy > 0:
            position = "below"
        else:
            position = "above"
    
    # Check for overlap
    x_overlap = max(0, min(bbox1["x"] + bbox1["width"], bbox2["x"] + bbox2["width"]) - 
                    max(bbox1["x"], bbox2["x"]))
    y_overlap = max(0, min(bbox1["y"] + bbox1["height"], bbox2["y"] + bbox2["height"]) - 
                    max(bbox1["y"], bbox2["y"]))
    
    overlap = x_overlap > 0 and y_overlap > 0
    
    if overlap:
        position = "overlapping"
    
    return {
        "object1": name1,
        "object2": name2,
        "relationship": position,
        "distance": np.sqrt(dx**2 + dy**2)
    }


def get_segmentation_colored(segmentation_map: np.ndarray) -> np.ndarray:
    """Convert segmentation map to colored visualization."""
    # Create color palette
    np.random.seed(42)
    colors = np.random.randint(0, 255, (256, 3), dtype=np.uint8)
    
    # Map segmentation to colors
    colored = colors[segmentation_map]
    
    return colored