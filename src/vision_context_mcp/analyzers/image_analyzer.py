"""
Image Analyzer Module

Provides comprehensive image analysis combining all preprocessors and generates
context for LLM consumption.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

from ..preprocessors import edges, depth, pose, segmentation
from . import entity_extractor

logger = logging.getLogger(__name__)


async def build_context(
    image_path: str,
    include_pose: bool = True,
    include_depth: bool = True,
    include_objects: bool = True
) -> dict[str, Any]:
    """
    Build comprehensive context from image for LLM consumption.
    
    Args:
        image_path: Path to the image file
        include_pose: Include pose analysis
        include_depth: Include depth analysis
        include_objects: Include object detection
    
    Returns:
        Dictionary with complete image context
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _build_context_sync,
        image_path,
        include_pose,
        include_depth,
        include_objects
    )


def _build_context_sync(
    image_path: str,
    include_pose: bool,
    include_depth: bool,
    include_objects: bool
) -> dict[str, Any]:
    """Synchronous context building."""
    
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    context = {
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0],
            "channels": image.shape[2] if len(image.shape) > 2 else 1
        },
        "file_info": {
            "format": path.suffix.lower(),
            "name": path.name
        }
    }
    
    # Run edge analysis (always included)
    try:
        edge_result = edges._analyze_edges_sync(image_path, "canny", 100, 200)
        context["edge_analysis"] = {
            "edge_density": edge_result["edge_statistics"]["edge_density"],
            "contour_count": edge_result["edge_statistics"]["contour_count"],
            "main_contours": edge_result["contours"][:5]
        }
    except Exception as e:
        logger.warning(f"Edge analysis failed: {e}")
        context["edge_analysis"] = {"error": str(e)}
    
    # Run depth analysis
    if include_depth:
        try:
            depth_result = depth._analyze_depth_sync(image_path, "midas")
            context["depth_analysis"] = {
                "spatial_regions": depth_result["spatial_regions"],
                "depth_statistics": depth_result["depth_statistics"],
                "focal_analysis": depth_result["focal_analysis"]
            }
        except Exception as e:
            logger.warning(f"Depth analysis failed: {e}")
            context["depth_analysis"] = {"error": str(e)}
    
    # Run segmentation
    try:
        seg_result = segmentation._analyze_segmentation_sync(image_path)
        context["segmentation"] = {
            "scene_type": seg_result["scene_composition"]["scene_type"],
            "dominant_objects": seg_result["scene_composition"]["dominant_objects"],
            "detected_regions": seg_result["detected_regions"][:10],
            "spatial_relationships": seg_result["spatial_relationships"]
        }
    except Exception as e:
        logger.warning(f"Segmentation failed: {e}")
        context["segmentation"] = {"error": str(e)}
    
    # Run pose detection
    if include_pose:
        try:
            pose_result = pose._analyze_pose_sync(image_path, True, False)
            context["pose_analysis"] = {
                "person_count": pose_result["person_count"],
                "poses": [
                    {
                        "pose_type": p.get("pose_type", "unknown"),
                        "action": p.get("detected_action", {}).get("primary_action", "neutral"),
                        "confidence": p.get("confidence", 0)
                    }
                    for p in pose_result["poses"]
                ],
                "scene_interactions": pose_result["scene_analysis"]["interactions"]
            }
        except Exception as e:
            logger.warning(f"Pose analysis failed: {e}")
            context["pose_analysis"] = {"error": str(e)}
    
    # Run object detection
    if include_objects:
        try:
            obj_result = entity_extractor._detect_objects_sync(image_path, 0.5, include_depth)
            context["object_detection"] = {
                "object_count": obj_result["object_count"],
                "objects": [
                    {
                        "label": obj["label"],
                        "confidence": obj["confidence"],
                        "position": obj["center"],
                        "depth": obj.get("depth", {})
                    }
                    for obj in obj_result["objects"]
                ]
            }
        except Exception as e:
            logger.warning(f"Object detection failed: {e}")
            context["object_detection"] = {"error": str(e)}
    
    # Generate summary
    context["summary"] = _generate_summary(context)
    
    return context


def _generate_summary(context: dict) -> str:
    """Generate a text summary of the image context."""
    parts = []
    
    # Dimensions
    dims = context.get("image_dimensions", {})
    parts.append(f"Image: {dims.get('width', 0)}x{dims.get('height', 0)} pixels")
    
    # Scene type
    seg = context.get("segmentation", {})
    if "scene_type" in seg:
        parts.append(f"Scene type: {seg['scene_type']}")
    
    # Dominant objects
    if "dominant_objects" in seg:
        objects = [o["name"] for o in seg["dominant_objects"][:3]]
        if objects:
            parts.append(f"Dominant elements: {', '.join(objects)}")
    
    # People
    pose = context.get("pose_analysis", {})
    if "person_count" in pose and pose["person_count"] > 0:
        parts.append(f"Detected {pose['person_count']} person(s)")
    
    # Objects
    obj = context.get("object_detection", {})
    if "object_count" in obj and obj["object_count"] > 0:
        parts.append(f"Found {obj['object_count']} objects")
    
    return ". ".join(parts) + "."


async def describe_for_3d(
    image_path: str,
    detail_level: str = "detailed"
) -> str:
    """
    Generate description optimized for 3D model generation.
    
    Args:
        image_path: Path to the image file
        detail_level: Level of detail (basic, detailed, comprehensive)
    
    Returns:
        Text description suitable for 3D generation
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _describe_for_3d_sync,
        image_path,
        detail_level
    )


def _describe_for_3d_sync(image_path: str, detail_level: str) -> str:
    """Generate 3D-oriented description."""
    
    # Get full context
    context = _build_context_sync(image_path, True, True, True)
    
    description_parts = []
    
    # Scene overview
    seg = context.get("segmentation", {})
    scene_type = seg.get("scene_type", "unknown")
    description_parts.append(f"A 3D scene representing {scene_type}")
    
    # Depth structure
    depth = context.get("depth_analysis", {})
    if "spatial_regions" in depth:
        regions = depth["spatial_regions"]
        region_names = [r["name"] for r in regions if r.get("percentage", 0) > 5]
        if region_names:
            description_parts.append(f"with {', '.join(region_names)} depth layers")
    
    # Main objects
    obj = context.get("object_detection", {})
    if "objects" in obj:
        main_objects = [o["label"] for o in obj["objects"][:5]]
        if main_objects:
            description_parts.append(f"containing {', '.join(main_objects)}")
    
    # People
    pose = context.get("pose_analysis", {})
    if pose.get("person_count", 0) > 0:
        poses = [p.get("pose_type", "standing") for p in pose.get("poses", [])]
        description_parts.append(f"with {pose['person_count']} person(s) {' and '.join(poses)}")
    
    # Spatial relationships
    if "spatial_relationships" in seg:
        rels = seg["spatial_relationships"][:3]
        for rel in rels:
            description_parts.append(f"{rel['object1']} is {rel['relationship']} {rel['object2']}")
    
    base_description = ". ".join(description_parts) + "."
    
    # Add detail based on level
    if detail_level == "detailed":
        # Add object dimensions
        if "objects" in obj:
            for o in obj["objects"][:3]:
                bbox = o.get("bounding_box", {})
                w, h = bbox.get("width", 0), bbox.get("height", 0)
                base_description += f" {o['label']} measures approximately {w}x{h} pixels."
    
    elif detail_level == "comprehensive":
        # Add all available details
        base_description += f"\n\nScene Composition:\n"
        
        for region in seg.get("detected_regions", [])[:5]:
            base_description += f"- {region['class_name']}: {region['percentage']:.1f}% of image\n"
        
        if "depth_statistics" in depth:
            stats = depth["depth_statistics"]
            base_description += f"\nDepth Statistics:\n"
            base_description += f"- Mean depth: {stats.get('mean_depth', 0):.2f}\n"
            base_description += f"- Depth variance: {stats.get('depth_variance', 0):.2f}\n"
    
    return base_description


def get_visual_summary(context: dict) -> dict[str, Any]:
    """Get a visual summary suitable for rendering."""
    return {
        "scene_type": context.get("segmentation", {}).get("scene_type", "unknown"),
        "depth_layers": context.get("depth_analysis", {}).get("spatial_regions", []),
        "main_objects": context.get("object_detection", {}).get("objects", [])[:5],
        "people": context.get("pose_analysis", {}).get("poses", []),
        "composition": context.get("segmentation", {}).get("scene_composition", {})
    }