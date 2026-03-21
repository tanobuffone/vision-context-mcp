"""
Vision Context MCP - Image and Video Analysis Server

A comprehensive MCP server that provides:
- ControlNet preprocessors (Canny, Depth, OpenPose, etc.)
- Object detection for 3D entity extraction
- Video analysis with scene detection
- Context generation for LLMs
"""

__version__ = "0.1.0"
__author__ = "gdrick"

from .server import _execute_tool

__all__ = ["_execute_tool"]
