"""
Script de prueba simple para Vision Context MCP
Usa las herramientas directamente sin async
"""

import sys
import json
import cv2
import numpy as np

def test_simple():
    try:
        # Probar análisis de bordes simple con OpenCV
        image = cv2.imread("test_images/test1.jpg")
        if image is None:
            print("❌ No se pudo cargar la imagen de prueba")
            sys.exit(1)
        
        # Análisis de bordes Canny
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        print(f"✅ Análisis de bordes Canny: densidad = {edge_density:.2f}")
        
        # Detección de objetos simple (solo contornos)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"✅ Contornos detectados: {len(contours)}")
        
        print("\n✅ Pruebas simples completadas exitosamente")
        
    except Exception as e:
        print(f"❌ Error en pruebas simples: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_simple()