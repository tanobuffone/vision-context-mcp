"""
Validation Module for Vision Context MCP Server

Provides comprehensive input validation, custom exceptions, file path
verification, and JSON sanitization utilities.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# =============================================================================
# Configuration Constants
# =============================================================================

# File size limits (in bytes) - DoS protection
MAX_IMAGE_SIZE_BYTES = 50 * 1024 * 1024   # 50 MB
MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024   # 500 MB

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}

# JSON output limits
MAX_JSON_DEPTH = 20
MAX_LIST_LENGTH = 10000
MAX_STRING_LENGTH = 100000


# =============================================================================
# Custom Exception Classes
# =============================================================================

class ValidationError(Exception):
    """Base validation error with actionable message."""

    def __init__(self, message: str, field: str | None = None, suggestion: str | None = None):
        self.field = field
        self.suggestion = suggestion
        parts = [message]
        if suggestion:
            parts.append(f"Suggestion: {suggestion}")
        super().__init__(" | ".join(parts))


class FileValidationError(ValidationError):
    """File-related validation error."""

    def __init__(self, message: str, path: str, suggestion: str | None = None):
        self.path = path
        super().__init__(message, field="file_path", suggestion=suggestion)


class FileNotFoundValidationError(FileValidationError):
    """File does not exist."""

    def __init__(self, path: str):
        resolved = str(Path(path).resolve()) if path else "<empty>"
        super().__init__(
            message=f"File not found: '{path}' (resolved: '{resolved}')",
            path=path,
            suggestion=(
                "Verify the file path is correct and the file exists. "
                "Use absolute paths or check relative path resolution."
            ),
        )


class FileExtensionError(FileValidationError):
    """File has an unsupported extension."""

    def __init__(self, path: str, allowed: set[str]):
        ext = Path(path).suffix.lower()
        super().__init__(
            message=f"Unsupported file extension '{ext}' for: '{path}'",
            path=path,
            suggestion=f"Allowed extensions: {', '.join(sorted(allowed))}",
        )


class FileSizeError(FileValidationError):
    """File exceeds maximum allowed size."""

    def __init__(self, path: str, size_bytes: int, max_bytes: int):
        size_mb = size_bytes / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)
        super().__init__(
            message=f"File too large: '{path}' is {size_mb:.1f} MB (max: {max_mb:.0f} MB)",
            path=path,
            suggestion=(
                f"Reduce file size to under {max_mb:.0f} MB. "
                "For images, consider compressing or resizing. "
                "For videos, reduce resolution or duration."
            ),
        )


class FilePermissionError(FileValidationError):
    """File is not readable."""

    def __init__(self, path: str):
        super().__init__(
            message=f"Permission denied: cannot read '{path}'",
            path=path,
            suggestion="Check file permissions with 'ls -l <path>' and ensure read access.",
        )


class ParameterValidationError(ValidationError):
    """Parameter value is invalid."""

    def __init__(self, field: str, value: Any, message: str, suggestion: str | None = None):
        self.value = value
        super().__init__(
            message=f"Invalid value for '{field}': {message} (got: {value!r})",
            field=field,
            suggestion=suggestion,
        )


class ToolNotFoundError(ValidationError):
    """Requested tool does not exist."""

    def __init__(self, tool_name: str, available_tools: list[str]):
        super().__init__(
            message=f"Unknown tool: '{tool_name}'",
            field="tool_name",
            suggestion=f"Available tools: {', '.join(sorted(available_tools))}",
        )


# =============================================================================
# Path Validation Functions
# =============================================================================

def validate_file_exists(path: str) -> Path:
    """
    Validate that a file path exists.

    Args:
        path: File path to validate.

    Returns:
        Resolved Path object.

    Raises:
        FileNotFoundValidationError: If file does not exist.
    """
    if not path or not isinstance(path, str):
        raise ValidationError(
            "File path must be a non-empty string",
            field="path",
            suggestion="Provide a valid absolute or relative file path.",
        )

    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundValidationError(path)

    return resolved


def validate_file_extension(path: Path, allowed_extensions: set[str]) -> None:
    """
    Validate that a file has an allowed extension.

    Args:
        path: Path object to validate.
        allowed_extensions: Set of allowed extensions (e.g., {'.jpg', '.png'}).

    Raises:
        FileExtensionError: If extension is not allowed.
    """
    ext = path.suffix.lower()
    if ext not in allowed_extensions:
        raise FileExtensionError(str(path), allowed_extensions)


def validate_file_size(path: Path, max_size_bytes: int) -> None:
    """
    Validate that a file does not exceed the maximum size.

    Args:
        path: Path object to validate.
        max_size_bytes: Maximum allowed size in bytes.

    Raises:
        FileSizeError: If file exceeds the size limit.
    """
    try:
        size = path.stat().st_size
    except OSError as e:
        raise FileValidationError(
            f"Cannot access file metadata: {e}",
            path=str(path),
            suggestion="Ensure the file is not locked or being written to.",
        ) from e

    if size > max_size_bytes:
        raise FileSizeError(str(path), size, max_size_bytes)


def validate_file_readable(path: Path) -> None:
    """
    Validate that a file is readable by the current process.

    Args:
        path: Path object to validate.

    Raises:
        FilePermissionError: If file is not readable.
    """
    if not os.access(path, os.R_OK):
        raise FilePermissionError(str(path))


def validate_image_path(path: str) -> Path:
    """
    Comprehensive validation for image file paths.

    Checks: existence, extension, size, permissions.

    Args:
        path: Image file path.

    Returns:
        Resolved Path object.

    Raises:
        Various FileValidationError subclasses on failure.
    """
    resolved = validate_file_exists(path)
    validate_file_extension(resolved, ALLOWED_IMAGE_EXTENSIONS)
    validate_file_size(resolved, MAX_IMAGE_SIZE_BYTES)
    validate_file_readable(resolved)
    return resolved


def validate_video_path(path: str) -> Path:
    """
    Comprehensive validation for video file paths.

    Checks: existence, extension, size, permissions.

    Args:
        path: Video file path.

    Returns:
        Resolved Path object.

    Raises:
        Various FileValidationError subclasses on failure.
    """
    resolved = validate_file_exists(path)
    validate_file_extension(resolved, ALLOWED_VIDEO_EXTENSIONS)
    validate_file_size(resolved, MAX_VIDEO_SIZE_BYTES)
    validate_file_readable(resolved)
    return resolved


def validate_output_directory(path: str | None) -> Path | None:
    """
    Validate an output directory path, creating it if necessary.

    Args:
        path: Output directory path (can be None).

    Returns:
        Resolved Path object or None.

    Raises:
        ValidationError: If directory cannot be created or is not writable.
    """
    if path is None:
        return None

    if not isinstance(path, str) or not path.strip():
        raise ValidationError(
            "Output directory path must be a non-empty string",
            field="output_dir",
            suggestion="Provide a valid directory path or omit the parameter.",
        )

    resolved = Path(path).resolve()
    try:
        resolved.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ValidationError(
            f"Cannot create output directory '{path}': {e}",
            field="output_dir",
            suggestion="Ensure parent directories exist and you have write permissions.",
        ) from e

    if not os.access(resolved, os.W_OK):
        raise ValidationError(
            f"Output directory is not writable: '{path}'",
            field="output_dir",
            suggestion="Check directory permissions with 'ls -ld <path>'.",
        )

    return resolved


# =============================================================================
# Parameter Validation Dataclasses
# =============================================================================

@dataclass
class AnalyzeEdgesParams:
    """Validated parameters for analyze_edges tool."""

    image_path: str
    method: str = "canny"
    low_threshold: int = 100
    high_threshold: int = 200

    VALID_METHODS = {"canny", "hed", "mlsd", "softedge"}

    def __post_init__(self):
        if self.method not in self.VALID_METHODS:
            raise ParameterValidationError(
                "method", self.method,
                f"must be one of: {', '.join(sorted(self.VALID_METHODS))}",
            )
        if not 0 <= self.low_threshold <= 255:
            raise ParameterValidationError(
                "low_threshold", self.low_threshold,
                "must be between 0 and 255",
            )
        if not 0 <= self.high_threshold <= 255:
            raise ParameterValidationError(
                "high_threshold", self.high_threshold,
                "must be between 0 and 255",
            )
        if self.low_threshold >= self.high_threshold:
            raise ParameterValidationError(
                "low_threshold", self.low_threshold,
                f"must be less than high_threshold ({self.high_threshold})",
            )


@dataclass
class AnalyzeDepthParams:
    """Validated parameters for analyze_depth tool."""

    image_path: str
    model: str = "midas"

    VALID_MODELS = {"midas", "zoedepth", "dpt"}

    def __post_init__(self):
        if self.model not in self.VALID_MODELS:
            raise ParameterValidationError(
                "model", self.model,
                f"must be one of: {', '.join(sorted(self.VALID_MODELS))}",
            )


@dataclass
class AnalyzePoseParams:
    """Validated parameters for analyze_pose tool."""

    image_path: str
    include_hands: bool = True
    include_face: bool = True


@dataclass
class AnalyzeSegmentationParams:
    """Validated parameters for analyze_segmentation tool."""

    image_path: str


@dataclass
class DetectObjectsParams:
    """Validated parameters for detect_objects tool."""

    image_path: str
    confidence: float = 0.5
    include_depth: bool = True

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ParameterValidationError(
                "confidence", self.confidence,
                "must be between 0.0 and 1.0",
            )


@dataclass
class BuildImageContextParams:
    """Validated parameters for build_image_context tool."""

    image_path: str
    include_pose: bool = True
    include_depth: bool = True
    include_objects: bool = True


@dataclass
class DescribeFor3DParams:
    """Validated parameters for describe_for_3d tool."""

    image_path: str
    detail_level: str = "detailed"

    VALID_LEVELS = {"basic", "detailed", "comprehensive"}

    def __post_init__(self):
        if self.detail_level not in self.VALID_LEVELS:
            raise ParameterValidationError(
                "detail_level", self.detail_level,
                f"must be one of: {', '.join(sorted(self.VALID_LEVELS))}",
            )


@dataclass
class ExtractEntities3DParams:
    """Validated parameters for extract_entities_3d tool."""

    image_path: str
    output_format: str = "json"

    VALID_FORMATS = {"json"}

    def __post_init__(self):
        if self.output_format not in self.VALID_FORMATS:
            raise ParameterValidationError(
                "output_format", self.output_format,
                f"must be one of: {', '.join(sorted(self.VALID_FORMATS))}",
            )


@dataclass
class ExtractVideoFramesParams:
    """Validated parameters for extract_video_frames tool."""

    video_path: str
    output_dir: str | None = None
    fps: float = 1.0
    max_frames: int = 100

    def __post_init__(self):
        if not 0.1 <= self.fps <= 30.0:
            raise ParameterValidationError(
                "fps", self.fps,
                "must be between 0.1 and 30.0",
            )
        if not 1 <= self.max_frames <= 1000:
            raise ParameterValidationError(
                "max_frames", self.max_frames,
                "must be between 1 and 1000",
            )


@dataclass
class DetectSceneChangesParams:
    """Validated parameters for detect_scene_changes tool."""

    video_path: str
    threshold: float = 30.0
    min_scene_length: int = 10

    def __post_init__(self):
        if self.threshold < 0:
            raise ParameterValidationError(
                "threshold", self.threshold,
                "must be non-negative",
            )
        if self.min_scene_length < 1:
            raise ParameterValidationError(
                "min_scene_length", self.min_scene_length,
                "must be at least 1",
            )


@dataclass
class AnalyzeVideoMotionParams:
    """Validated parameters for analyze_video_motion tool."""

    video_path: str
    sample_rate: int = 30

    def __post_init__(self):
        if self.sample_rate < 1:
            raise ParameterValidationError(
                "sample_rate", self.sample_rate,
                "must be at least 1",
            )


@dataclass
class GetVideoContextParams:
    """Validated parameters for get_video_context tool."""

    video_path: str
    extract_keyframes: bool = True
    analyze_temporal: bool = True


@dataclass
class ExtractKeyframeParams:
    """Validated parameters for extract_keyframe tool."""

    video_path: str
    timestamp: float
    output_path: str | None = None

    def __post_init__(self):
        if self.timestamp < 0:
            raise ParameterValidationError(
                "timestamp", self.timestamp,
                "must be non-negative",
            )


# =============================================================================
# Parameter Validation Dispatcher
# =============================================================================

PARAM_VALIDATORS: dict[str, type] = {
    "analyze_edges": AnalyzeEdgesParams,
    "analyze_depth": AnalyzeDepthParams,
    "analyze_pose": AnalyzePoseParams,
    "analyze_segmentation": AnalyzeSegmentationParams,
    "detect_objects": DetectObjectsParams,
    "build_image_context": BuildImageContextParams,
    "describe_for_3d": DescribeFor3DParams,
    "extract_entities_3d": ExtractEntities3DParams,
    "extract_video_frames": ExtractVideoFramesParams,
    "detect_scene_changes": DetectSceneChangesParams,
    "analyze_video_motion": AnalyzeVideoMotionParams,
    "get_video_context": GetVideoContextParams,
    "extract_keyframe": ExtractKeyframeParams,
}

IMAGE_TOOLS = {
    "analyze_edges", "analyze_depth", "analyze_pose",
    "analyze_segmentation", "detect_objects", "build_image_context",
    "describe_for_3d", "extract_entities_3d",
}

VIDEO_TOOLS = {
    "extract_video_frames", "detect_scene_changes",
    "analyze_video_motion", "get_video_context", "extract_keyframe",
}


def validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize tool arguments.

    Performs:
    1. Tool existence check
    2. Parameter type/range validation via dataclass
    3. File path validation (existence, extension, size, permissions)

    Args:
        tool_name: Name of the tool being called.
        arguments: Raw arguments dictionary.

    Returns:
        Validated and normalized arguments dictionary.

    Raises:
        ToolNotFoundError: If tool_name is not recognized.
        ValidationError: If arguments are invalid.
    """
    available_tools = list(PARAM_VALIDATORS.keys())
    if tool_name not in PARAM_VALIDATORS:
        raise ToolNotFoundError(tool_name, available_tools)

    # Validate parameters via dataclass
    validator_class = PARAM_VALIDATORS[tool_name]
    try:
        validated = validator_class(**arguments)
    except TypeError as e:
        missing = []
        extra = []
        msg = str(e)
        if "required" in msg or "missing" in msg.lower():
            # Extract missing field names from error
            import re
            found = re.findall(r"'(\w+)'", msg)
            missing = found
        raise ValidationError(
            f"Invalid arguments for '{tool_name}': {e}",
            field="arguments",
            suggestion=f"Check the tool schema for required and optional parameters.",
        ) from e

    validated_dict = {k: v for k, v in vars(validated).items()}

    # Validate file paths
    if tool_name in IMAGE_TOOLS:
        validate_image_path(validated_dict["image_path"])
    elif tool_name in VIDEO_TOOLS:
        validate_video_path(validated_dict["video_path"])

    # Validate optional output directories
    if "output_dir" in validated_dict and validated_dict["output_dir"]:
        validate_output_directory(validated_dict["output_dir"])
    if "output_path" in validated_dict and validated_dict["output_path"]:
        output_path = validated_dict["output_path"]
        parent = Path(output_path).parent
        if parent != Path("."):
            validate_output_directory(str(parent))

    return validated_dict


# =============================================================================
# JSON Sanitization
# =============================================================================

def sanitize_for_json(obj: Any, depth: int = 0) -> Any:
    """
    Sanitize an object for safe JSON serialization.

    Handles:
    - numpy types (ndarray, float32/64, int32/64)
    - Path objects
    - Deep recursion protection
    - Large list truncation
    - String length limits

    Args:
        obj: Object to sanitize.
        depth: Current recursion depth.

    Returns:
        JSON-serializable object.
    """
    if depth > MAX_JSON_DEPTH:
        return f"<max depth {MAX_JSON_DEPTH} exceeded>"

    if obj is None:
        return None

    if isinstance(obj, (str, int, bool)):
        if isinstance(obj, str) and len(obj) > MAX_STRING_LENGTH:
            return obj[:MAX_STRING_LENGTH] + f"... <truncated, {len(obj)} chars total>"
        return obj

    if isinstance(obj, float):
        # Handle NaN and Inf
        if obj != obj or obj == float("inf") or obj == float("-inf"):
            return str(obj)
        return obj

    if isinstance(obj, Path):
        return str(obj)

    # numpy types
    try:
        import numpy as np

        if isinstance(obj, np.ndarray):
            if obj.size > MAX_LIST_LENGTH:
                return {
                    "type": "ndarray",
                    "shape": list(obj.shape),
                    "dtype": str(obj.dtype),
                    "truncated": True,
                    "note": f"Array too large ({obj.size} elements), showing statistics only",
                    "min": sanitize_for_json(float(np.min(obj)), depth + 1),
                    "max": sanitize_for_json(float(np.max(obj)), depth + 1),
                    "mean": sanitize_for_json(float(np.mean(obj)), depth + 1),
                }
            return sanitize_for_json(obj.tolist(), depth + 1)

        if isinstance(obj, (np.integer,)):
            return int(obj)

        if isinstance(obj, (np.floating,)):
            val = float(obj)
            if val != val or val == float("inf") or val == float("-inf"):
                return str(val)
            return val

        if isinstance(obj, (np.bool_,)):
            return bool(obj)

    except ImportError:
        pass

    if isinstance(obj, dict):
        return {
            str(k): sanitize_for_json(v, depth + 1)
            for k, v in obj.items()
        }

    if isinstance(obj, (list, tuple)):
        if len(obj) > MAX_LIST_LENGTH:
            truncated = list(obj[:MAX_LIST_LENGTH])
            result = [sanitize_for_json(item, depth + 1) for item in truncated]
            result.append(f"<truncated, {len(obj)} items total>")
            return result
        return [sanitize_for_json(item, depth + 1) for item in obj]

    if hasattr(obj, "__dict__"):
        return sanitize_for_json(vars(obj), depth + 1)

    # Fallback: convert to string
    try:
        return str(obj)
    except Exception:
        return "<unserializable>"


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize an object to JSON string.

    Sanitizes the object first to handle numpy types, paths,
    and other non-JSON-native types.

    Args:
        obj: Object to serialize.
        **kwargs: Additional arguments passed to json.dumps.

    Returns:
        JSON string.
    """
    sanitized = sanitize_for_json(obj)
    kwargs.setdefault("indent", 2)
    kwargs.setdefault("default", str)
    return json.dumps(sanitized, **kwargs)
