# Product Context - Vision Context MCP

## Problema que Resuelve

### Gap en el Ecosistema MCP
Antes de Vision Context MCP, no existía una solución MCP completa para análisis visual que:
- Combinara múltiples técnicas de visión por computadora
- Generara contexto estructurado para LLMs
- Proveyera descripciones optimizadas para generación 3D
- Soportara análisis temporal de videos

### Necesidades del Usuario
1. **Desarrolladores de LLMs**: Necesitan contexto visual estructurado para razonamiento multimodal
2. **Artistas 3D**: Requieren descripciones precisas de escenas para recreación
3. **Investigadores**: Buscan herramientas de análisis visual integradas
4. **Creadores de Contenido**: Necesitan análisis automático de videos

## Solución Propuesta

### Flujo de Trabajo Típico

1. **Análisis de Imagen**:
   ```
   Usuario → build_image_context → JSON estructurado → LLM
   ```

2. **Generación 3D**:
   ```
   Imagen → describe_for_3d → Descripción → Blender/Unity
   ```

3. **Análisis de Video**:
   ```
   Video → get_video_context → Resumen temporal → Editor
   ```

## Casos de Uso Principales

### 1. Análisis para LLMs
**Usuario**: "Analiza esta imagen y dime qué objetos hay"
**Herramienta**: `build_image_context`
**Output**: JSON con objetos, posiciones, profundidad, relaciones espaciales

### 2. Generación de Escenas 3D
**Usuario**: "Genera una descripción para recrear esta escena en Blender"
**Herramienta**: `describe_for_3d`
**Output**: "A 3D scene representing outdoor with foreground, midground, background depth layers containing person, car, tree..."

### 3. Edición de Video
**Usuario**: "¿Cuántas escenas tiene este video y dónde están los cambios?"
**Herramienta**: `detect_scene_changes`
**Output**: Lista de timestamps con cambios de escena

### 4. Caracterización de Personas
**Usuario**: "Describe las poses de las personas en la imagen"
**Herramienta**: `analyze_pose`
**Output**: Keypoints, tipo de pose, acciones detectadas

## Experiencia de Usuario

### Integración Simple
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

## Valor Diferencial

### Ventajas Competitivas
1. **Todo-en-uno**: Un servidor para todas las necesidades de análisis visual
2. **Optimizado para 3D**: Generación de descripciones específicas para modelos 3D
3. **Arquitectura Robusta**: Fallbacks y manejo de errores sofisticado
4. **Documentación Excelente**: Guías completas y ejemplos prácticos

## Roadmap de Producto

### v0.1.0 (Actual) - Fundación
- ✅ 14 herramientas básicas
- ✅ Documentación completa
- ✅ Integración MCP estándar

### v0.2.0 - Optimización
- 🔄 Suite de testing completa
- 🔄 Métricas de rendimiento
- 🔄 Caching de modelos

### v0.3.0 - Expansión
- 📋 Streaming de video
- 📋 Más modelos de detección
- 📋 API REST opcional

---

**Última Actualización**: 21 de marzo de 2026
**Propietario**: gdrick