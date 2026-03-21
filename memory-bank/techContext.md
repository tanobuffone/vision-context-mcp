# Tech Context - Vision Context MCP

## Stack Tecnológico

### Lenguaje y Runtime
- **Python**: 3.10+
- **Async**: asyncio nativo
- **Type System**: Type hints completos (PEP 484)

### Framework MCP
- **mcp**: >=1.0.0
- **Server**: stdio_server (comunicación por stdin/stdout)
- **Protocol**: JSON-RPC 2.0 sobre stdio

### Procesamiento de Imagen
- **opencv-python**: >=4.8.0 - Procesamiento básico
- **pillow**: >=10.0.0 - Manejo de formatos de imagen
- **numpy**: >=1.24.0 - Operaciones numéricas

### Deep Learning (Opcional)
- **torch**: >=2.0.0 - Framework de deep learning
- **torchvision**: >=0.17.0 - Modelos de visión
- **transformers**: >=4.35.0 - Modelos HuggingFace (DETR, DPT)
- **accelerate**: >=0.25.0 - Optimización de modelos

### ControlNet Preprocessors (Opcional)
- **controlnet-aux**: >=0.0.7 - Preprocessors avanzados
  - HEDdetector
  - MLSDdetector
  - MidasDetector
  - OpenposeDetector
  - SegformerForSemanticSegmentation

### MediaPipe (Opcional)
- **mediapipe**: >=0.10.0 - Detección de pose alternativa

### Herramientas de Desarrollo
- **pytest**: >=8.0.0 - Testing
- **pytest-asyncio**: >=0.23.0 - Tests async
- **black**: >=24.0.0 - Formateo de código
- **ruff**: >=0.2.0 - Linting

## Configuración del Proyecto

### pyproject.toml
```toml
[project]
name = "vision-context-mcp"
version = "0.1.0"
requires-python = ">=3.10"

[project.optional-dependencies]
full = ["controlnet-aux", "torch", "transformers", ...]
dev = ["pytest", "pytest-asyncio", "black", "ruff"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/vision_context_mcp"]
```

### Estructura de Paquetes
```
src/vision_context_mcp/
├── __init__.py
├── server.py           # Entry point MCP
├── preprocessors/
│   ├── __init__.py
│   ├── edges.py        # Canny, HED, MLSD, SoftEdge
│   ├── depth.py        # MiDaS, ZoeDepth, DPT
│   ├── pose.py         # OpenPose, MediaPipe
│   └── segmentation.py # ADE20K Segformer
└── analyzers/
    ├── __init__.py
    ├── image_analyzer.py    # Análisis combinado
    ├── video_analyzer.py    # Análisis temporal
    └── entity_extractor.py  # Extracción 3D
```

## Dependencias por Funcionalidad

### Core (Siempre Requerido)
| Paquete | Versión | Uso |
|---------|---------|-----|
| mcp | >=1.0.0 | Protocolo MCP |
| opencv-python | >=4.8.0 | Procesamiento imagen |
| pillow | >=10.0.0 | Formatos imagen |
| numpy | >=1.24.0 | Operaciones numéricas |

### Edge Detection
| Paquete | Requerido | Uso |
|---------|-----------|-----|
| controlnet-aux | Opcional | HED, MLSD avanzado |
| OpenCV | Core | Canny, LSD fallback |

### Depth Estimation
| Paquete | Requerido | Uso |
|---------|-----------|-----|
| controlnet-aux | Opcional | MiDaS |
| torch + transformers | Opcional | DPT, ZoeDepth |
| OpenCV + NumPy | Core | Simple depth fallback |

### Pose Detection
| Paquete | Requerido | Uso |
|---------|-----------|-----|
| controlnet-aux | Opcional | OpenPose |
| mediapipe | Opcional | Pose alternativa |

### Segmentation
| Paquete | Requerido | Uso |
|---------|-----------|-----|
| transformers | Opcional | Segformer ADE20K |
| OpenCV + NumPy | Core | Color segmentation fallback |

### Object Detection
| Paquete | Requerido | Uso |
|---------|-----------|-----|
| torch + transformers | Opcional | DETR |
| OpenCV | Core | Contour detection fallback |

## Configuración de MCP

### Para Cline/VS Code
```json
{
  "mcpServers": {
    "vision-context": {
      "command": "uvx",
      "args": ["vision-context-mcp"]
    }
  }
}
```

### Para Desarrollo
```json
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

### Para Claude Desktop
```json
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

## Variables de Entorno

### Cache de Modelos
```bash
# HuggingFace cache
export HF_HOME=/path/to/hf-cache

# PyTorch cache
export TORCH_HOME=/path/to/torch-cache
```

### Logging
```bash
# Nivel de logging
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Rendimiento y Optimización

### Thread Pool Execution
- Operaciones CPU-bound en thread pool
- No bloquea event loop de MCP
- Paralelismo real con múltiples cores

### Caching de Modelos
- Modelos se cargan una vez
- Cache en memoria durante sesión
- `_model_cache` dict global

### Fallback Strategy
- Si dependencia opcional no disponible → fallback
- Si modelo falla → método simple
- Si archivo no existe → error claro

### Memory Management
- OpenCV lee imágenes bajo demanda
- NumPy arrays se liberan automáticamente
- Torch tensors en CPU por defecto (GPU opcional)

## Configuración de Herramientas

### Black
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

### Ruff
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

### Pytest
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## Compatibilidad

### Sistemas Operativos
- ✅ Linux (Ubuntu 20.04+)
- ✅ macOS (11+)
- ✅ Windows (10+)

### Versiones de Python
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ⚠️ Python 3.9 (sin soporte completo de type hints)

### Arquitecturas
- ✅ x86_64
- ✅ ARM64 (Apple Silicon)
- ⚠️ ARM32 (limitado por PyTorch)

---

**Última Actualización**: 21 de marzo de 2026