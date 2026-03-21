"""
Edge Detection Module

Implements Canny, HED, MLSD, and SoftEdge detection for image analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import controlnet_aux for advanced edge detection
try:
    from controlnet_aux import CannyDetector, HEDdetector, MLSDdetector
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("controlnet-aux not installed, using OpenCV fallbacks")


async def analyze_edges(
    image_path: str,
    method: str = "canny",
    low_threshold: int = 100,
    high_threshold: int = 200
) -> dict[str, Any]:
    """
    Analyze edges in an image using specified method.
    
    Args:
        image_path: Path to the image file
        method: Edge detection method (canny, hed, mlsd, softedge)
        low_threshold: Low threshold for Canny (0-255)
        high_threshold: High threshold for Canny (0-255)
    
    Returns:
        Dictionary with edge map, statistics, and detected contours
    """
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_edges_sync,
        image_path,
        method,
        low_threshold,
        high_threshold
    )


def _analyze_edges_sync(
    image_path: str,
    method: str,
    low_threshold: int,
    high_threshold: int
) -> dict[str, Any]:
    """Synchronous edge analysis implementation."""
    
    # Load image
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply edge detection based on method
    if method == "canny":
        edges = _canny_detection(gray, low_threshold, high_threshold)
    elif method == "hed":
        edges = _hed_detection(image)
    elif method == "mlsd":
        edges = _mlsd_detection(image)
    elif method == "softedge":
        edges = _softedge_detection(gray)
    else:
        raise ValueError(f"Unknown edge detection method: {method}")
    
    # Calculate statistics
    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.shape[0] * edges.shape[1]
    edge_density = edge_pixels / total_pixels
    
    # Find contours
    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Analyze contours
    contour_analysis = []
    for i, contour in enumerate(contours[:50]):  # Limit to top 50
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, w, h = cv2.boundingRect(contour)
        
        contour_analysis.append({
            "id": i,
            "area": float(area),
            "perimeter": float(perimeter),
            "bounding_box": {"x": x, "y": y, "width": w, "height": h},
            "centroid": {
                "x": x + w // 2,
                "y": y + h // 2
            }
        })
    
    # Sort by area (largest first)
    contour_analysis.sort(key=lambda c: c["area"], reverse=True)
    
    return {
        "method": method,
        "image_path": str(path),
        "image_dimensions": {
            "width": image.shape[1],
            "height": image.shape[0]
        },
        "edge_statistics": {
            "edge_pixel_count": int(edge_pixels),
            "total_pixels": int(total_pixels),
            "edge_density": float(edge_density),
            "contour_count": len(contours)
        },
        "contours": contour_analysis[:20],  # Top 20 contours
        "edge_map_shape": list(edges.shape),
        "success": True
    }


def _canny_detection(gray: np.ndarray, low: int, high: int) -> np.ndarray:
    """Standard Canny edge detection."""
    # Apply Gaussian blur for noise reduction
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny edge detection
    edges = cv2.Canny(blurred, low, high)
    
    return edges


def _hed_detection(image: np.ndarray) -> np.ndarray:
    """Holistically-Nested Edge Detection."""
    if CONTROLNET_AVAILABLE:
        try:
            detector = HEDdetector.from_pretrained("lllyasviel/Annotators")
            result = detector(image)
            return np.array(result)
        except Exception as e:
            logger.warning(f"HED failed, using fallback: {e}")
    
    # Fallback: Use Laplacian with morphological operations
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
    edges = np.uint8(np.absolute(laplacian) > 30) * 255
    
    # Morphological cleaning
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    return edges


def _mlsd_detection(image: np.ndarray) -> np.ndarray:
    """Mobile Line Segment Detection for straight lines."""
    if CONTROLNET_AVAILABLE:
        try:
            detector = MLSDdetector.from_pretrained("lllyasviel/Annotators")
            result = detector(image)
            return np.array(result)
        except Exception as e:
            logger.warning(f"MLSD failed, using fallback: {e}")
    
    # Fallback: Use LSD (Line Segment Detector)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Create LSD detector
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    lines = lsd.detect(gray)[0]
    
    # Draw lines on blank image
    edges = np.zeros_like(gray)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = map(int, line[0])
            cv2.line(edges, (x1, y1), (x2, y2), 255, 1)
    
    return edges


def _softedge_detection(gray: np.ndarray) -> np.ndarray:
    """Soft edge detection using HED-like approach."""
    # Multiple scale edge detection
    edges = np.zeros_like(gray, dtype=np.float32)
    
    # Different Gaussian blurs
    for sigma in [1, 2, 3]:
        blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
        grad_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        edges += magnitude / (sigma * 2)
    
    # Normalize
    edges = edges / edges.max() * 255
    edges = edges.astype(np.uint8)
    
    return edges


def get_edge_map_base64(edges: np.ndarray) -> str:
    """Convert edge map to base64 encoded PNG."""
    import base64
    from io import BytesIO
    
    pil_image = Image.fromarray(edges)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    
    return base64.b64encode(buffer.getvalue()).decode("utf-8")