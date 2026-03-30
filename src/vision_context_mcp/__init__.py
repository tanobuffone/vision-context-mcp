"""
Vision Context MCP - Image and Video Analysis Server

A comprehensive MCP server that provides:
- ControlNet preprocessors (Canny, Depth, OpenPose, etc.)
- Object detection for 3D entity extraction
- Video analysis with scene detection
- Context generation for LLMs
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "gdrick"


def __getattr__(name: str):
    """Lazy imports for heavy dependencies."""
    if name == "_execute_tool":
        from .server import _execute_tool
        return _execute_tool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from .validation import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
    FileNotFoundValidationError,
    FileValidationError,
    ParameterValidationError,
    ToolNotFoundError,
    ValidationError,
)

__all__ = [
    "_execute_tool",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_VIDEO_EXTENSIONS",
    "MAX_IMAGE_SIZE_BYTES",
    "MAX_VIDEO_SIZE_BYTES",
    "FileNotFoundValidationError",
    "FileValidationError",
    "ParameterValidationError",
    "ToolNotFoundError",
    "ValidationError",
]
