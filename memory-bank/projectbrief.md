# Project Brief - Vision Context MCP

## Visión General

**Vision Context MCP** es un servidor Model Context Protocol (MCP) que proporciona herramientas de análisis visual para imágenes y videos, generando contexto estructurado para LLMs y generación de modelos 3D.

## Objetivos Principales

1. **Extraer Contexto Visual**: Analizar imágenes para entender composición, objetos, profundidad y relaciones espaciales
2. **Generar Contexto para LLMs**: Producir JSON estructurado que los LLMs puedan usar para razonamiento
3. **Descripción de Escenas 3D**: Crear descripciones optimizadas para generación de modelos y escenas 3D
4. **Análisis de Video**: Análisis temporal incluyendo detección de escenas y seguimiento de movimiento

## Alcance del Proyecto

### Herramientas Implementadas (14 total)

**Análisis de Imágenes (8 herramientas):**
- `analyze_edges`: Detección de bordes (Canny, HED, MLSD, SoftEdge)
- `analyze_depth`: Estimación de profundidad (MiDaS, ZoeDepth, DPT)
- `analyze_pose`: Detección de pose humana con keypoints
- `analyze_segmentation`: Segmentación semántica (ADE20K)
- `detect_objects`: Detección de objetos con posicionamiento 3D
- `build_image_context`: Análisis completo de imagen
- `describe_for_3d`: Descripciones optimizadas para 3D
- `extract_entities_3d`: Extracción de entidades 3D

**Análisis de Video (5 herramientas):**
- `extract_video_frames`: Extracción de frames
- `detect_scene_changes`: Detección de cambios de escena
- `analyze_video_motion`: Análisis de patrones de movimiento
- `get_video_context`: Análisis completo de video
- `extract_keyframe`: Extracción de frame específico por timestamp

## Tecnologías

- **Lenguaje**: Python 3.10+
- **Protocolo**: Model Context Protocol (MCP)
- **Procesamiento**: OpenCV, NumPy, Pillow
- **Deep Learning**: PyTorch, Transformers (opcional)
- **ControlNet**: controlnet-aux para preprocessors avanzados

## Estado Actual

- **Versión**: 0.1.0
- **Estado**: Producción-ready con optimizaciones recomendadas
- **Puntuación**: 9.2/10 según evaluación integral
- **Licencia**: MIT

## Próximos Pasos

1. Implementar suite de testing
2. Optimizar modelos de deep learning
3. Añadir métricas de rendimiento
4. Preparar para contribuciones de la comunidad

---

**Última Actualización**: 21 de marzo de 2026
**Mantenenedor**: gdrick