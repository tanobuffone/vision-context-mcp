"""
Depth Estimation Module

Implements MiDaS, ZoeDepth, and DPT for depth map generation and spatial analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import torch and transformers for depth models
try:
    import torch
    from transformers import DPTForDepthEstimation, DPTImageProcessor
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch/transformers not installed, depth estimation limited")

# Try controlnet_aux for MiDaS
try:
    from controlnet_aux import MidasDetector
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False

# Model cache
_model_cache = {}


async def analyze_depth(
    image_path: str,
    model: str = "midas"
) -> dict[str, Any]:
    """
    Generate depth map from image.
    
    Args:
        image_path: Path to the image file
        model: Depth estimation model (midas, zoedepth, dpt)
    
    Returns:
        Dictionary with depth map, spatial information, and statistics
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_depth_sync,
        image_path,
        model
    )


def _analyze_depth_sync(
    image_path: str,
    model: str
) -> dict[str, Any]:
    """Synchronous depth analysis implementation."""
    
    # Load image
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Generate depth map
    if model == "midas":
        depth_map = _midas_depth(image_rgb)
    elif model == "zoedepth":
        depth_map = _zoedepth_depth(image_rgb)
    elif model == "dpt":
        depth_map = _dpt_depth(image_rgb)
    else:
        raise ValueError(f"Unknown depth model: {model}")
    
    # Analyze depth statistics
    depth_stats = _compute_depth_statistics(depth_map)
    
    # Detect spatial regions
    regions = _detect_spatial_regions(depth_map)
    
    # Generate depth histogram
    histogram = _compute_depth_histogram(depth_map)
    
    # Estimate focal plane and depth of field
    focal_info = _estimate_focal_plane(depth_map)
    
    return {
        "model": model,
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "depth_statistics": depth_stats,
        "spatial_regions": regions,
        "depth_histogram": histogram,
        "focal_analysis": focal_info,
        "depth_map_shape": list(depth_map.shape),
        "depth_range": {
            "min": float(depth_map.min()),
            "max": float(depth_map.max())
        },
        "success": True
    }


def _midas_depth(image: np.ndarray) -> np.ndarray:
    """MiDaS depth estimation."""
    global _model_cache
    
    if CONTROLNET_AVAILABLE:
        try:
            if "midas" not in _model_cache:
                _model_cache["midas"] = MidasDetector.from_pretrained("lllyasviel/Annotators")
            
            detector = _model_cache["midas"]
            result = detector(image)
            return np.array(result)
        except Exception as e:
            logger.warning(f"MiDaS via controlnet_aux failed: {e}")
    
    if TORCH_AVAILABLE:
        try:
            return _dpt_depth_fallback(image)
        except Exception as e:
            logger.warning(f"DPT fallback failed: {e}")
    
    # Ultimate fallback: Simple depth from blur/edges
    return _simple_depth_estimation(image)


def _zoedepth_depth(image: np.ndarray) -> np.ndarray:
    """ZoeDepth estimation (requires torch)."""
    if not TORCH_AVAILABLE:
        logger.warning("ZoeDepth requires PyTorch, using MiDaS fallback")
        return _midas_depth(image)
    
    try:
        # ZoeDepth is available via torch hub
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Try to load ZoeDepth
        repo = "isl-org/ZoeDepth"
        model_zoe = torch.hub.load(repo, "ZoeD_NK", pretrained=True).to(device)
        
        pil_image = Image.fromarray(image)
        depth = model_zoe.infer_pil(pil_image)
        
        return depth
    except Exception as e:
        logger.warning(f"ZoeDepth failed: {e}")
        return _midas_depth(image)


def _dpt_depth(image: np.ndarray) -> np.ndarray:
    """DPT (Dense Prediction Transformer) depth estimation."""
    return _dpt_depth_fallback(image)


def _dpt_depth_fallback(image: np.ndarray) -> np.ndarray:
    """DPT depth estimation using HuggingFace transformers."""
    if not TORCH_AVAILABLE:
        return _simple_depth_estimation(image)
    
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
        model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large").to(device)
        
        pil_image = Image.fromarray(image)
        inputs = processor(images=pil_image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            predicted_depth = outputs.predicted_depth
        
        # Interpolate to original size
        depth = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
        
        depth = depth.cpu().numpy()
        
        # Normalize to 0-255
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255
        return depth.astype(np.uint8)
        
    except Exception as e:
        logger.warning(f"DPT failed: {e}")
        return _simple_depth_estimation(image)


def _simple_depth_estimation(image: np.ndarray) -> np.ndarray:
    """Simple depth estimation using image features."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    # Use multiple cues for depth estimation
    
    # 1. Vertical position (objects higher in image are usually farther)
    height = gray.shape[0]
    vertical_gradient = np.linspace(1, 0, height).reshape(-1, 1)
    vertical_gradient = np.tile(vertical_gradient, (1, gray.shape[1]))
    
    # 2. Blur level (blurry areas are often background)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    blur_metric = np.abs(gray - blurred) / 255.0
    
    # 3. Saturation (desaturated areas are often background)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1].astype(np.float32) / 255.0
    
    # Combine cues
    depth = (vertical_gradient * 0.4 + (1 - blur_metric) * 0.3 + (1 - saturation) * 0.3)
    
    # Apply bilateral filter to smooth
    depth = cv2.bilateralFilter((depth * 255).astype(np.uint8), 9, 75, 75)
    
    return depth.astype(np.float32)


def _compute_depth_statistics(depth_map: np.ndarray) -> dict[str, float]:
    """Compute statistical measures of depth map."""
    return {
        "mean_depth": float(np.mean(depth_map)),
        "median_depth": float(np.median(depth_map)),
        "std_depth": float(np.std(depth_map)),
        "min_depth": float(np.min(depth_map)),
        "max_depth": float(np.max(depth_map)),
        "depth_variance": float(np.var(depth_map))
    }


def _detect_spatial_regions(depth_map: np.ndarray) -> list[dict[str, Any]]:
    """Detect foreground, midground, and background regions."""
    # Normalize depth
    normalized = ((depth_map - depth_map.min()) / 
                  (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)
    
    # Define thresholds
    fg_threshold = 50
    bg_threshold = 180
    
    regions = []
    
    # Foreground (closest)
    fg_mask = normalized < fg_threshold
    if fg_mask.any():
        fg_coords = np.where(fg_mask)
        regions.append({
            "name": "foreground",
            "pixel_count": int(np.sum(fg_mask)),
            "percentage": float(np.sum(fg_mask) / fg_mask.size * 100),
            "centroid": {
                "x": int(np.mean(fg_coords[1])),
                "y": int(np.mean(fg_coords[0]))
            },
            "depth_range": "near"
        })
    
    # Midground
    mid_mask = (normalized >= fg_threshold) & (normalized < bg_threshold)
    if mid_mask.any():
        mid_coords = np.where(mid_mask)
        regions.append({
            "name": "midground",
            "pixel_count": int(np.sum(mid_mask)),
            "percentage": float(np.sum(mid_mask) / mid_mask.size * 100),
            "centroid": {
                "x": int(np.mean(mid_coords[1])),
                "y": int(np.mean(mid_coords[0]))
            },
            "depth_range": "medium"
        })
    
    # Background (farthest)
    bg_mask = normalized >= bg_threshold
    if bg_mask.any():
        bg_coords = np.where(bg_mask)
        regions.append({
            "name": "background",
            "pixel_count": int(np.sum(bg_mask)),
            "percentage": float(np.sum(bg_mask) / bg_mask.size * 100),
            "centroid": {
                "x": int(np.mean(bg_coords[1])),
                "y": int(np.mean(bg_coords[0]))
            },
            "depth_range": "far"
        })
    
    return regions


def _compute_depth_histogram(depth_map: np.ndarray, bins: int = 10) -> dict[str, Any]:
    """Compute depth histogram."""
    normalized = ((depth_map - depth_map.min()) / 
                  (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)
    
    hist, bin_edges = np.histogram(normalized.flatten(), bins=bins, range=(0, 255))
    
    return {
        "bins": bins,
        "counts": hist.tolist(),
        "bin_edges": bin_edges.tolist(),
        "dominant_range": {
            "min": float(bin_edges[np.argmax(hist)]),
            "max": float(bin_edges[np.argmax(hist) + 1])
        }
    }


def _estimate_focal_plane(depth_map: np.ndarray) -> dict[str, Any]:
    """Estimate the focal plane and depth of field."""
    # Find most common depth (likely in focus)
    normalized = ((depth_map - depth_map.min()) / 
                  (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)
    
    hist, bin_edges = np.histogram(normalized.flatten(), bins=256)
    
    # Find peak
    peak_idx = np.argmax(hist)
    focal_depth = (bin_edges[peak_idx] + bin_edges[peak_idx + 1]) / 2
    
    # Calculate depth of field (range around peak with significant pixels)
    threshold = hist.max() * 0.1
    in_range = hist > threshold
    dof_min = bin_edges[np.where(in_range)[0][0]] if in_range.any() else 0
    dof_max = bin_edges[np.where(in_range)[0][-1] + 1] if in_range.any() else 255
    
    return {
        "focal_depth": float(focal_depth),
        "depth_of_field": {
            "min": float(dof_min),
            "max": float(dof_max),
            "range": float(dof_max - dof_min)
        },
        "focus_quality": "sharp" if hist.max() > hist.mean() * 2 else "soft"
    }


def get_depth_map_normalized(depth_map: np.ndarray) -> np.ndarray:
    """Normalize depth map to 0-255 range for visualization."""
    return ((depth_map - depth_map.min()) / 
            (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)