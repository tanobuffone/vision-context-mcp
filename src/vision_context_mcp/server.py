"""
Vision Context MCP Server

A comprehensive MCP server that provides visual analysis tools for images and videos,
generating context for LLMs and 3D model generation.
"""

import asyncio
import json
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

# Import analyzers and preprocessors
from .preprocessors import edges, depth, pose, segmentation
from .analyzers import image_analyzer, video_analyzer, entity_extractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("vision-context-mcp")


# Define available tools
TOOLS = [
    # === Image Analysis Tools ===
    Tool(
        name="analyze_edges",
        description="""Analyze edges in an image using various detection methods.
        
Methods available:
- canny: Classic Canny edge detection (fast, reliable)
- hed: Holistically-Nested Edge Detection (deep learning, detailed)
- mlsd: Mobile Line Segment Detection (straight lines, architectural)
- softedge: Soft edge detection (artistic, smooth)

Returns edge density, contours, and shape information useful for 3D modeling.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "method": {
                    "type": "string",
                    "enum": ["canny", "hed", "mlsd", "softedge"],
                    "default": "canny",
                    "description": "Edge detection method to use"
                },
                "low_threshold": {
                    "type": "integer",
                    "default": 100,
                    "minimum": 0,
                    "maximum": 255,
                    "description": "Low threshold for Canny detection"
                },
                "high_threshold": {
                    "type": "integer",
                    "default": 200,
                    "minimum": 0,
                    "maximum": 255,
                    "description": "High threshold for Canny detection"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="analyze_depth",
        description="""Generate depth map from an image using deep learning models.

Models available:
- midas: MiDaS depth estimation (balanced)
- zoedepth: ZoeDepth (detailed, metric depth)
- dpt: Dense Prediction Transformer (high quality)

Returns depth map, spatial regions (foreground/midground/background), and focal analysis.
Essential for understanding 3D structure from 2D images.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "model": {
                    "type": "string",
                    "enum": ["midas", "zoedepth", "dpt"],
                    "default": "midas",
                    "description": "Depth estimation model to use"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="analyze_pose",
        description="""Detect human poses in an image with body, hand, and face keypoints.

Returns:
- Person count and locations
- Pose type (standing, sitting, crouching)
- Body proportions and measurements
- Detected actions (arms raised, reaching, etc.)
- Scene interactions between people

Useful for character modeling, animation reference, and understanding human presence.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "include_hands": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to detect hand keypoints"
                },
                "include_face": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to detect face landmarks"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="analyze_segmentation",
        description="""Perform semantic segmentation to identify objects and regions.

Uses ADE20K model (150 classes) to segment:
- Indoor: walls, floors, furniture, appliances
- Outdoor: sky, trees, roads, buildings
- Objects: people, cars, animals, items

Returns:
- Detected regions with class names and percentages
- Scene type inference (bedroom, outdoor, urban, etc.)
- Spatial relationships between objects
- Dominant objects and composition

Critical for understanding scene structure and composition.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="detect_objects",
        description="""Detect objects in an image with bounding boxes and depth positioning.

Uses DETR (DEtection TRansformer) trained on COCO dataset (80 classes).

Returns:
- Object labels and confidence scores
- 2D bounding boxes
- 3D positions with depth estimation
- Primitive type inference for 3D modeling

Ideal for extracting entities to place in 3D scenes.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "confidence": {
                    "type": "number",
                    "default": 0.5,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Minimum confidence threshold"
                },
                "include_depth": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to estimate 3D depth positions"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="build_image_context",
        description="""Build comprehensive context from an image for LLM consumption.

Combines all analysis tools:
- Edge detection and contour analysis
- Depth estimation and spatial regions
- Semantic segmentation and scene type
- Pose detection (if people present)
- Object detection with positions

Returns a complete JSON context ready for LLM prompting.
This is the primary tool for image understanding.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "include_pose": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include pose analysis"
                },
                "include_depth": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include depth analysis"
                },
                "include_objects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include object detection"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="describe_for_3d",
        description="""Generate a description optimized for 3D model/scene generation.

Creates text descriptions suitable for prompting 3D generation tools:
- Scene structure and depth layers
- Object positions and dimensions
- Spatial relationships
- Primitive type suggestions

Detail levels:
- basic: Quick overview
- detailed: With dimensions
- comprehensive: Full breakdown with statistics

Perfect for generating prompts for Blender, Unreal, or AI 3D tools.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["basic", "detailed", "comprehensive"],
                    "default": "detailed",
                    "description": "Level of detail in the description"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    Tool(
        name="extract_entities_3d",
        description="""Extract objects as 3D entities with positions and dimensions.

Returns entities with:
- 3D position (x, y, z normalized coordinates)
- Dimensions (width, height, depth)
- Primitive type (box, sphere, cylinder, humanoid)
- Rotation (default identity)
- Semantic properties (animate, category)

Output formats:
- json: Full data structure
- obj: Wavefront OBJ format (future)
- glb: GLTF binary (future)

Ready for direct use in 3D rendering engines.""",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["json"],
                    "default": "json",
                    "description": "Output format for 3D data"
                }
            },
            "required": ["image_path"]
        }
    ),
    
    # === Video Analysis Tools ===
    Tool(
        name="extract_video_frames",
        description="""Extract frames from a video at specified rate.

Options:
- fps: Frames per second to extract (default: 1.0)
- max_frames: Maximum frames to extract (default: 100)
- output_dir: Optional directory to save frames as JPG

Returns frame information with timestamps.
Useful for analyzing video content frame-by-frame.""",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Optional directory to save extracted frames"
                },
                "fps": {
                    "type": "number",
                    "default": 1.0,
                    "minimum": 0.1,
                    "maximum": 30.0,
                    "description": "Frames per second to extract"
                },
                "max_frames": {
                    "type": "integer",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Maximum number of frames to extract"
                }
            },
            "required": ["video_path"]
        }
    ),
    
    Tool(
        name="detect_scene_changes",
        description="""Detect scene changes and cuts in a video.

Analyzes frame-to-frame differences to find:
- Scene boundaries with timestamps
- Scene durations
- Transition points

Returns scene segments for further analysis.
Useful for breaking down videos into distinct scenes.""",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "threshold": {
                    "type": "number",
                    "default": 30.0,
                    "description": "Change detection threshold (lower = more sensitive)"
                },
                "min_scene_length": {
                    "type": "integer",
                    "default": 10,
                    "description": "Minimum frames between scene changes"
                }
            },
            "required": ["video_path"]
        }
    ),
    
    Tool(
        name="analyze_video_motion",
        description="""Analyze motion patterns in a video.

Detects:
- Motion regions and their locations
- Motion intensity over time
- Activity level (high/moderate/low)
- Motion statistics

Useful for:
- Action detection
- Activity analysis
- Identifying dynamic vs static scenes""",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "sample_rate": {
                    "type": "integer",
                    "default": 30,
                    "description": "Analyze every N frames"
                }
            },
            "required": ["video_path"]
        }
    ),
    
    Tool(
        name="get_video_context",
        description="""Get comprehensive context from a video.

Analyzes:
- Video metadata (resolution, fps, duration)
- Scene structure and changes
- Motion patterns and activity levels
- Overall video summary

This is the primary tool for video understanding.
Returns a complete JSON context ready for LLM prompting.""",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "extract_keyframes": {
                    "type": "boolean",
                    "default": True,
                    "description": "Extract keyframe information"
                },
                "analyze_temporal": {
                    "type": "boolean",
                    "default": True,
                    "description": "Analyze temporal patterns (motion, scenes)"
                }
            },
            "required": ["video_path"]
        }
    ),
    
    Tool(
        name="extract_keyframe",
        description="""Extract a specific frame from video by timestamp.

Extracts a single frame at the specified time position.
Can optionally save to a file for further analysis.

Useful for:
- Getting representative frames
- Analyzing specific moments
- Creating thumbnails""",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file"
                },
                "timestamp": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Timestamp in seconds"
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional path to save the extracted frame"
                }
            },
            "required": ["video_path", "timestamp"]
        }
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
    try:
        result = await _execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: File not found - {str(e)}")]
    
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: Invalid input - {str(e)}")]
    
    except Exception as e:
        logger.exception(f"Tool execution failed: {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool and return results."""
    
    # Image analysis tools
    if name == "analyze_edges":
        return await edges.analyze_edges(
            image_path=arguments["image_path"],
            method=arguments.get("method", "canny"),
            low_threshold=arguments.get("low_threshold", 100),
            high_threshold=arguments.get("high_threshold", 200)
        )
    
    elif name == "analyze_depth":
        return await depth.analyze_depth(
            image_path=arguments["image_path"],
            model=arguments.get("model", "midas")
        )
    
    elif name == "analyze_pose":
        return await pose.analyze_pose(
            image_path=arguments["image_path"],
            include_hands=arguments.get("include_hands", True),
            include_face=arguments.get("include_face", True)
        )
    
    elif name == "analyze_segmentation":
        return await segmentation.analyze_segmentation(
            image_path=arguments["image_path"]
        )
    
    elif name == "detect_objects":
        return await entity_extractor.detect_objects(
            image_path=arguments["image_path"],
            confidence=arguments.get("confidence", 0.5),
            include_depth=arguments.get("include_depth", True)
        )
    
    elif name == "build_image_context":
        return await image_analyzer.build_context(
            image_path=arguments["image_path"],
            include_pose=arguments.get("include_pose", True),
            include_depth=arguments.get("include_depth", True),
            include_objects=arguments.get("include_objects", True)
        )
    
    elif name == "describe_for_3d":
        return await image_analyzer.describe_for_3d(
            image_path=arguments["image_path"],
            detail_level=arguments.get("detail_level", "detailed")
        )
    
    elif name == "extract_entities_3d":
        return await entity_extractor.extract_entities_3d(
            image_path=arguments["image_path"],
            output_format=arguments.get("output_format", "json")
        )
    
    # Video analysis tools
    elif name == "extract_video_frames":
        return await video_analyzer.extract_frames(
            video_path=arguments["video_path"],
            output_dir=arguments.get("output_dir"),
            fps=arguments.get("fps", 1.0),
            max_frames=arguments.get("max_frames", 100)
        )
    
    elif name == "detect_scene_changes":
        return await video_analyzer.detect_scene_changes(
            video_path=arguments["video_path"],
            threshold=arguments.get("threshold", 30.0),
            min_scene_length=arguments.get("min_scene_length", 10)
        )
    
    elif name == "analyze_video_motion":
        return await video_analyzer.analyze_motion(
            video_path=arguments["video_path"],
            sample_rate=arguments.get("sample_rate", 30)
        )
    
    elif name == "get_video_context":
        return await video_analyzer.get_video_context(
            video_path=arguments["video_path"],
            extract_keyframes=arguments.get("extract_keyframes", True),
            analyze_temporal=arguments.get("analyze_temporal", True)
        )
    
    elif name == "extract_keyframe":
        return await video_analyzer.extract_keyframe_at(
            video_path=arguments["video_path"],
            timestamp=arguments["timestamp"],
            output_path=arguments.get("output_path")
        )
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()