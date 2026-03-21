"""
Script de prueba básica para Vision Context MCP
"""

import sys
import json
from vision_context_mcp.server import _execute_tool

def test_basic():
    try:
        # Probar análisis de bordes simple
        result = _execute_tool("analyze_edges", {
            "image_path": "test_images/test1.jpg",
            "method": "canny"
        })
        print("Análisis de bordes exitoso:")
        print(json.dumps(result, indent=2))
        
        # Probar detección de objetos
        result = _execute_tool("detect_objects", {
            "image_path": "test_images/test1.jpg",
            "confidence": 0.5
        })
        print("\nDetección de objetos exitosa:")
        print(json.dumps(result, indent=2))
        
        print("\n✅ Pruebas básicas completadas exitosamente")
        
    except Exception as e:
        print(f"❌ Error en pruebas básicas: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_basic()