# System Patterns - Vision Context MCP

## Arquitectura General

### Patrón MCP Server
```
┌─────────────────────────────────────────┐
│           MCP Server (server.py)        │
├─────────────────────────────────────────┤
│  @server.list_tools()                   │
│  @server.call_tool()                    │
├─────────────────────────────────────────┤
│          Tool Definitions               │
│  (14 herramientas con schemas)          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│ Preprocessors │       │   Analyzers   │
├───────────────┤       ├───────────────┤
│ edges.py      │       │ image_analyzer│
│ depth.py      │       │ video_analyzer│
│ pose.py       │       │ entity_extract│
│ segmentation  │       └───────────────┘
└───────────────┘
```

## Patrones de Diseño Implementados

### 1. Facade Pattern
**Ubicación**: `server.py` y `image_analyzer.py`
**Uso**: Simplifica la complejidad de múltiples preprocessors
```python
# El usuario llama a una herramienta
await call_tool("build_image_context", {...})

# Internamente coordina múltiples análisis
edge_result = edges._analyze_edges_sync(...)
depth_result = depth._analyze_depth_sync(...)
seg_result = segmentation._analyze_segmentation_sync(...)
```

### 2. Strategy Pattern
**Ubicación**: `edges.py`, `depth.py`
**Uso**: Intercambiar algoritmos sin cambiar interfaz
```python
if method == "canny":
    edges = _canny_detection(gray, low, high)
elif method == "hed":
    edges = _hed_detection(image)
elif method == "mlsd":
    edges = _mlsd_detection(image)
```

### 3. Template Method Pattern
**Ubicación**: Todos los preprocessors
**Uso**: Estructura común con implementaciones variables
```python
async def analyze_*(image_path: str, **kwargs) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_*_sync,  # Método abstracto implementado
        image_path,
        **kwargs
    )
```

### 4. Fallback Pattern
**Ubicación**: Todos los módulos
**Uso**: Degradación graceful cuando dependencias no disponibles
```python
try:
    from controlnet_aux import HEDdetector
    # Usar modelo avanzado
except ImportError:
    # Usar fallback OpenCV
    logger.warning("controlnet-aux not installed, using fallback")
```

### 5. Cache Pattern
**Ubicación**: `depth.py`, `segmentation.py`, `entity_extractor.py`
**Uso**: Reutilizar modelos cargados
```python
_model_cache = {}

def _midas_depth(image):
    if "midas" not in _model_cache:
        _model_cache["midas"] = MidasDetector.from_pretrained(...)
    return _model_cache["midas"](image)
```

## Patrones de Comunicación

### Async/Await con Thread Pools
```python
async def analyze_edges(image_path: str, ...) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # ThreadPoolExecutor por defecto
        _analyze_edges_sync,  # Función síncrona
        image_path, ...  # Argumentos
    )
```

**Beneficios**:
- No bloquea el event loop de MCP
- Permite paralelismo real con CPU-bound tasks
- Compatible con el modelo de ejecución de MCP

### Error Handling Consistente
```python
try:
    result = await _execute_tool(name, arguments)
    return [TextContent(type="text", text=json.dumps(result))]
except FileNotFoundError as e:
    return [TextContent(type="text", text=f"Error: File not found - {str(e)}")]
except ValueError as e:
    return [TextContent(type="text", text=f"Error: Invalid input - {str(e)}")]
except Exception as e:
    logger.exception(f"Tool execution failed: {name}")
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

## Patrones de Datos

### Estructura de Respuesta Estándar
```python
{
    "success": True,
    "image_path": str,
    "image_dimensions": {"width": int, "height": int},
    # Datos específicos del análisis
    "statistics": {...},
    "regions": [...],
    # Metadatos
    "model": str,
    "method": str
}
```

### Normalización de Coordenadas
```python
# Posición normalizada 0-1
norm_x = center["x"] / image_width
norm_y = center["y"] / image_height
norm_z = depth / 255.0  # Profundidad normalizada
```

### Formato de Herramientas MCP
```python
Tool(
    name="analyze_edges",
    description="""Descripción detallada...""",
    inputSchema={
        "type": "object",
        "properties": {
            "image_path": {"type": "string"},
            "method": {"type": "string", "enum": [...]},
        },
        "required": ["image_path"]
    }
)
```

## Convenciones de Código

### Naming Conventions
- **Funciones públicas**: `async def analyze_edges(...)`
- **Funciones síncronas**: `def _analyze_edges_sync(...)`
- **Funciones auxiliares**: `def _canny_detection(...)`
- **Constantes**: `CONTROLNET_AVAILABLE`, `COCO_CLASSES`

### Import Structure
```python
# Imports estándar
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

# Imports de terceros
import cv2
import numpy as np
from PIL import Image

# Imports opcionales con try/except
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
```

### Logging Pattern
```python
logger = logging.getLogger(__name__)

# Warning para fallbacks
logger.warning("controlnet-aux not installed, using fallback")

# Exception para errores críticos
logger.exception(f"Tool execution failed: {name}")
```

## Testing Patterns (Pendiente)

### Estructura de Tests Propuesta
```
tests/
├── test_preprocessors/
│   ├── test_edges.py
│   ├── test_depth.py
│   ├── test_pose.py
│   └── test_segmentation.py
├── test_analyzers/
│   ├── test_image_analyzer.py
│   ├── test_video_analyzer.py
│   └── test_entity_extractor.py
└── test_server.py
```

### Mock Pattern para Modelos
```python
@pytest.fixture
def mock_detector(monkeypatch):
    def mock_from_pretrained(name):
        return MockDetector()
    monkeypatch.setattr(HEDdetector, "from_pretrained", mock_from_pretrained)
```

---

**Última Actualización**: 21 de marzo de 2026