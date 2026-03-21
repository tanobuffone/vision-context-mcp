# Contributing to Vision Context MCP

¡Gracias por tu interés en contribuir a Vision Context MCP! Este documento describe cómo puedes ayudar a mejorar el proyecto.

## 🚀 Formas de Contribuir

### 1. Reportar Bugs
- Usa el template de issues de GitHub
- Incluye pasos para reproducir el bug
- Proporciona información del sistema y versiones

### 2. Sugerir Funcionalidades
- Abre un issue con la etiqueta "enhancement"
- Describe el caso de uso y beneficio esperado
- Incluye ejemplos si es posible

### 3. Enviar Pull Requests
- Fork el repositorio
- Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
- Commit tus cambios (`git commit -m 'feat: add amazing feature'`)
- Push a la rama (`git push origin feature/amazing-feature`)
- Abre un Pull Request

## 📋 Guías de Desarrollo

### Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/vision-context-mcp.git
cd vision-context-mcp

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Instalar pre-commit hooks (opcional)
pre-commit install
```

### Estandares de Código

#### Python
- Sigue PEP 8
- Usa type hints para todas las funciones
- Escribe docstrings para módulos, clases y funciones públicas
- Línea máxima: 100 caracteres

#### Formato
```bash
# Formatear con black
black src/ tests/

# Linting con ruff
ruff check src/ tests/

# Type checking (opcional)
mypy src/
```

### Estructura de Commits

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Tipos**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (sin cambio de lógica)
- `refactor`: Refactoring sin cambio de funcionalidad
- `test`: Añadir o corregir tests
- `chore`: Cambios en build o herramientas

**Ejemplos**:
```
feat(edges): add SoftEdge detection method
fix(depth): handle missing model gracefully
docs(readme): update installation instructions
test(segmentation): add unit tests for ADE20K classes
```

### Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con coverage
pytest --cov=vision_context_mcp --cov-report=html

# Ejecutar tests específicos
pytest tests/test_edges.py

# Ejecutar tests async
pytest -v tests/
```

#### Escribir Tests

```python
import pytest
from vision_context_mcp.preprocessors import edges

@pytest.mark.asyncio
async def test_analyze_edges_canny(tmp_path):
    # Crear imagen de prueba
    image_path = tmp_path / "test.jpg"
    # ... crear imagen
    
    result = await edges.analyze_edges(
        str(image_path),
        method="canny"
    )
    
    assert result["success"] is True
    assert "edge_statistics" in result
    assert result["edge_statistics"]["contour_count"] > 0
```

### Documentación

- Actualiza README.md si cambias la interfaz pública
- Añade docstrings a nuevas funciones
- Ejemplos de uso en docstrings cuando sea apropiado

```python
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
    
    Example:
        >>> result = await analyze_edges("image.jpg", method="canny")
        >>> print(result["edge_statistics"]["edge_density"])
        0.15
    """
```

## 🔧 Añadir Nuevas Herramientas

### 1. Crear el Preprocessor

```python
# src/vision_context_mcp/preprocessors/new_feature.py

async def analyze_new_feature(
    image_path: str,
    option: str = "default"
) -> dict[str, Any]:
    """Implement new feature analysis."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _analyze_new_feature_sync,
        image_path,
        option
    )

def _analyze_new_feature_sync(image_path: str, option: str) -> dict:
    # Implementación síncrona
    pass
```

### 2. Añadir al Server

```python
# src/vision_context_mcp/server.py

TOOLS = [
    # ... herramientas existentes
    Tool(
        name="analyze_new_feature",
        description="Description of the new feature...",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "option": {"type": "string", "default": "default"}
            },
            "required": ["image_path"]
        }
    ),
]

async def _execute_tool(name: str, arguments: dict) -> dict:
    # ... casos existentes
    elif name == "analyze_new_feature":
        return await new_feature.analyze_new_feature(
            image_path=arguments["image_path"],
            option=arguments.get("option", "default")
        )
```

### 3. Añadir Tests

```python
# tests/test_preprocessors/test_new_feature.py

import pytest
from vision_context_mcp.preprocessors import new_feature

@pytest.mark.asyncio
async def test_analyze_new_feature(tmp_path):
    result = await new_feature.analyze_new_feature(
        str(tmp_path / "test.jpg")
    )
    assert result["success"] is True
```

## 📝 Pull Request Checklist

Antes de enviar un PR, asegúrate de:

- [ ] Código sigue los estándares de estilo
- [ ] Tests pasan localmente (`pytest`)
- [ ] Nuevas funcionalidades tienen tests
- [ ] Documentación actualizada
- [ ] Commits siguen conventional commits
- [ ] PR description explica los cambios
- [ ] No hay secrets o credenciales en el código

## 🐛 Reportar Bugs

### Template de Bug Report

```markdown
**Descripción**
Descripción clara y concisa del bug.

**Pasos para Reproducir**
1. Ir a '...'
2. Click en '...'
3. Scroll down hasta '...'
4. Ver error

**Comportamiento Esperado**
Descripción de lo que debería pasar.

**Comportamiento Actual**
Descripción de lo que realmente pasa.

**Screenshots**
Si aplica, añade screenshots.

**Entorno:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11]
- Versión: [e.g., 0.1.0]
- Dependencias: [output de `pip list`]

**Contexto Adicional**
Cualquier otro contexto sobre el problema.
```

## 💡 Sugerir Funcionalidades

### Template de Feature Request

```markdown
**Problema**
Descripción del problema que esta funcionalidad resolvería.

**Solución Propuesta**
Descripción de la solución que te gustaría.

**Alternativas Consideradas**
Descripción de alternativas que consideraste.

**Contexto Adicional**
Cualquier otro contexto o screenshots.
```

## 📞 Contacto

- Issues: [GitHub Issues](https://github.com/yourusername/vision-context-mcp/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/vision-context-mcp/discussions)

## 🙏 Agradecimientos

¡Gracias a todos los contribuidores que han ayudado a mejorar este proyecto!

---

**Última Actualización**: 21 de marzo de 2026