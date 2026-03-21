# Vision Context MCP Server

A comprehensive Model Context Protocol (MCP) server that provides visual analysis tools for images and videos, generating structured context for LLMs and 3D model generation.

## 🎯 Purpose

This server bridges the gap between visual content and AI understanding by:

1. **Extracting Visual Context**: Analyze images to understand composition, objects, depth, and spatial relationships
2. **Generating LLM-Ready Context**: Produce structured JSON that LLMs can use for reasoning
3. **3D Scene Description**: Create descriptions optimized for 3D model and scene generation
4. **Video Analysis**: Temporal analysis including scene detection and motion tracking

## 🛠️ Tools Overview

### Image Analysis Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `analyze_edges` | Edge detection (Canny, HED, MLSD, SoftEdge) | Shape extraction, 3D modeling |
| `analyze_depth` | Depth estimation (MiDaS, ZoeDepth, DPT) | Spatial understanding, layering |
| `analyze_pose` | Human pose detection with keypoints | Character modeling, animation |
| `analyze_segmentation` | Semantic segmentation (ADE20K) | Scene parsing, object identification |
| `detect_objects` | Object detection with 3D positioning | Entity extraction |
| `build_image_context` | Comprehensive image analysis | Full understanding |
| `describe_for_3d` | 3D-optimized descriptions | Prompting 3D tools |
| `extract_entities_3d` | 3D entity extraction | Direct 3D engine integration |

### Video Analysis Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `extract_video_frames` | Frame extraction at configurable rate | Frame-by-frame analysis |
| `detect_scene_changes` | Scene cut detection | Video segmentation |
| `analyze_video_motion` | Motion pattern analysis | Activity detection |
| `get_video_context` | Comprehensive video analysis | Full video understanding |
| `extract_keyframe` | Extract specific frame by timestamp | Moment analysis |

## 📦 Installation

### Requirements

- Python 3.10+
- OpenCV
- NumPy
- PyTorch (optional, for advanced models)
- Transformers (optional, for DETR/DPT)

### Install

```bash
# Clone the repository
git clone https://github.com/yourusername/vision-context-mcp.git
cd vision-context-mcp

# Install with pip
pip install -e .

# Or install with all optional dependencies
pip install -e ".[all]"
```

### MCP Configuration

Add to your MCP settings (e.g., `cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "vision-context": {
      "command": "uvx",
      "args": ["vision-context-mcp"],
      "env": {}
    }
  }
}
```

Or for development:

```json
{
  "mcpServers": {
    "vision-context": {
      "command": "python",
      "args": ["-m", "vision_context_mcp.server"],
      "cwd": "/path/to/vision-context-mcp",
      "env": {}
    }
  }
}
```

## 🚀 Quick Start

### Basic Image Analysis

```python
# Via MCP tool call
result = await mcp.call_tool("build_image_context", {
    "image_path": "/path/to/image.jpg"
})
```

Returns comprehensive JSON with:
- Edge analysis and contours
- Depth estimation and spatial regions
- Semantic segmentation and scene type
- Object detection with positions
- Pose detection (if people present)

### 3D Description Generation

```python
description = await mcp.call_tool("describe_for_3d", {
    "image_path": "/path/to/scene.jpg",
    "detail_level": "detailed"
})
```

Output example:
```
A 3D scene representing outdoor with foreground, midground, background depth layers
containing person, car, tree. person is standing. car measures approximately 200x150 pixels.
```

### Video Analysis

```python
context = await mcp.call_tool("get_video_context", {
    "video_path": "/path/to/video.mp4"
})
```

Returns video metadata, scene segments, and motion analysis.

## 📊 Tool Details

### analyze_edges

Detects edges and contours in images.

**Methods:**
- `canny`: Fast, reliable edge detection
- `hed`: Deep learning-based, captures fine details
- `mlsd`: Optimized for straight lines (architecture)
- `softedge`: Artistic, smooth edges

**Returns:**
```json
{
  "edge_density": 0.15,
  "contour_count": 42,
  "contours": [
    {
      "area": 5000,
      "perimeter": 300,
      "bounding_box": {"x": 100, "y": 150, "width": 80, "height": 60}
    }
  ]
}
```

### analyze_depth

Estimates depth maps from single images.

**Models:**
- `midas`: Balanced performance (default)
- `zoedepth`: Metric depth, more accurate
- `dpt`: Highest quality, slower

**Returns:**
```json
{
  "spatial_regions": [
    {"name": "foreground", "percentage": 25.5, "centroid": {"x": 320, "y": 240}},
    {"name": "midground", "percentage": 45.0},
    {"name": "background", "percentage": 29.5}
  ],
  "focal_analysis": {
    "focal_depth": 128,
    "focus_quality": "sharp"
  }
}
```

### analyze_segmentation

Performs semantic segmentation using ADE20K (150 classes).

**Returns:**
```json
{
  "scene_type": "living_room",
  "detected_regions": [
    {"class_name": "sofa", "percentage": 15.2, "bounding_box": {...}},
    {"class_name": "floor", "percentage": 30.5}
  ],
  "spatial_relationships": [
    {"object1": "sofa", "object2": "floor", "relationship": "above"}
  ]
}
```

### detect_objects

Detects objects with COCO classes (80 categories).

**Returns:**
```json
{
  "objects": [
    {
      "label": "person",
      "confidence": 0.95,
      "bounding_box": {"x": 100, "y": 50, "width": 80, "height": 200},
      "depth": {"normalized_depth": 0.35}
    }
  ]
}
```

### extract_entities_3d

Extracts objects as 3D entities.

**Returns:**
```json
{
  "entities": [
    {
      "id": "entity_person_320_240",
      "label": "person",
      "primitive_type": "humanoid",
      "position": {"x": 0.5, "y": 0.5, "z": 0.35},
      "dimensions": {"width": 0.1, "height": 0.3, "depth": 0.05},
      "properties": {"animate": true, "category": "human"}
    }
  ]
}
```

## 🔧 Advanced Usage

### Combining with Blender MCP

1. Extract 3D entities from image
2. Pass entities to Blender MCP for rendering

```python
# Get entities
entities = await mcp.call_tool("extract_entities_3d", {
    "image_path": "/path/to/scene.jpg"
})

# Create in Blender
for entity in entities["entities"]:
    await blender_mcp.call_tool("create_primitive", {
        "type": entity["primitive_type"],
        "position": entity["position"],
        "scale": entity["dimensions"]
    })
```

### Integration with LLMs

The `build_image_context` tool produces structured JSON perfect for LLM reasoning:

```python
context = await mcp.call_tool("build_image_context", {
    "image_path": "/path/to/image.jpg"
})

# Pass to LLM
response = await llm.generate(f"""
Analyze this image context and suggest improvements for 3D recreation:
{json.dumps(context, indent=2)}
""")
```

## 📁 Project Structure

```
vision-context-mcp/
├── src/vision_context_mcp/
│   ├── __init__.py
│   ├── server.py           # MCP server implementation
│   ├── preprocessors/
│   │   ├── __init__.py
│   │   ├── edges.py        # Edge detection
│   │   ├── depth.py        # Depth estimation
│   │   ├── pose.py         # Pose detection
│   │   └── segmentation.py # Semantic segmentation
│   └── analyzers/
│       ├── __init__.py
│       ├── entity_extractor.py  # 3D entity extraction
│       ├── image_analyzer.py    # Image context builder
│       └── video_analyzer.py    # Video analysis
├── pyproject.toml
└── README.md
```

## 🔌 Dependencies

### Core
- `mcp>=1.0.0` - Model Context Protocol
- `opencv-python>=4.8.0` - Image processing
- `numpy>=1.24.0` - Numerical operations
- `Pillow>=10.0.0` - Image handling

### Optional (for advanced features)
- `torch>=2.0.0` - Deep learning
- `transformers>=4.35.0` - DETR, DPT models
- `controlnet-aux>=0.0.7` - ControlNet preprocessors
- `mediapipe>=0.10.0` - Pose detection fallback

## 🤝 Integration Examples

### With Cline/VS Code

```json
// .vscode/mcp.json
{
  "servers": {
    "vision-context": {
      "command": "uvx",
      "args": ["vision-context-mcp"]
    }
  }
}
```

### With Claude Desktop

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "vision-context": {
      "command": "python",
      "args": ["-m", "vision_context_mcp.server"],
      "cwd": "/path/to/vision-context-mcp"
    }
  }
}
```

## 📝 Example Prompts

### For Image Analysis
```
Use build_image_context on /path/to/image.jpg and tell me what would be needed 
to recreate this scene in a 3D game engine.
```

### For 3D Generation
```
Use describe_for_3d with comprehensive detail on /path/to/reference.jpg, 
then suggest how to improve the description for better 3D model generation.
```

### For Video Analysis
```
Use get_video_context on /path/to/video.mp4 to understand its structure, 
then identify the most interesting frames for detailed analysis.
```

## 🐛 Troubleshooting

### Model Download Issues
Models are downloaded on first use. If downloads fail:
1. Check internet connection
2. Set `HF_HOME` environment variable for cache location
3. Use `TORCH_HOME` for PyTorch model cache

### Memory Issues
Large images or videos may consume significant memory:
1. Resize images before processing
2. Use lower `fps` for video frame extraction
3. Set `max_frames` limit for videos

### Import Errors
If you get import errors for optional dependencies:
```bash
pip install vision-context-mcp[all]
```

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Intel for DPT depth estimation models
- Facebook AI for DETR object detection
- ControlNet for preprocessor implementations
- HuggingFace for model hosting
- Anthropic for MCP specification

## 📮 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Made with ❤️ for the MCP ecosystem**