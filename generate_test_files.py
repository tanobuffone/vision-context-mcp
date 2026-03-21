"""
Script para generar archivos de prueba para el testeo extenso
"""

import os
import sys
import random
import numpy as np
from PIL import Image, ImageDraw
import cv2

# Configurar paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "test_images")
TEST_VIDEOS_DIR = os.path.join(BASE_DIR, "test_videos")
TEST_FILES_DIR = os.path.join(BASE_DIR, "test_files")

# Crear directorios si no existen
os.makedirs(TEST_DIR, exist_ok=True)
os.makedirs(TEST_VIDEOS_DIR, exist_ok=True)
os.makedirs(TEST_FILES_DIR, exist_ok=True)

def generate_test_image(filename: str, width: int, height: int, format: str = "jpg"):
    """Generar imagen de prueba"""
    # Crear imagen con contenido aleatorio
    img = Image.new('RGB', (width, height), color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # Agregar formas aleatorias
    draw = ImageDraw.Draw(img)
    for _ in range(random.randint(1, 5)):
        shape = random.choice(['rectangle', 'ellipse', 'line'])
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        
        if shape == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], outline=(255, 255, 255), width=2)
        elif shape == 'ellipse':
            draw.ellipse([x1, y1, x2, y2], outline=(255, 255, 255), width=2)
        elif shape == 'line':
            draw.line([x1, y1, x2, y2], fill=(255, 255, 255), width=2)
    
    # Guardar imagen
    img.save(os.path.join(TEST_DIR, filename), format=format.upper())

def generate_test_video(filename: str, width: int, height: int, duration: int, fps: int = 30):
    """Generar video de prueba"""
    # Crear video con frames aleatorios
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(os.path.join(TEST_VIDEOS_DIR, filename), fourcc, fps, (width, height))
    
    for i in range(duration * fps):
        # Crear frame aleatorio
        frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        
        # Agregar texto con número de frame
        cv2.putText(frame, f"Frame {i}", (10, height-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Escribir frame
        out.write(frame)
    
    out.release()

def generate_corrupt_image(filename: str, width: int, height: int):
    """Generar imagen corrupta"""
    # Crear archivo con datos aleatorios
    with open(os.path.join(TEST_FILES_DIR, filename), "wb") as f:
        f.write(os.urandom(width * height * 3))

def generate_empty_image(filename: str, width: int, height: int):
    """Generar imagen vacía"""
    # Crear archivo vacío
    with open(os.path.join(TEST_FILES_DIR, filename), "wb") as f:
        f.write(b"")

def main():
    print("Generando archivos de prueba...")

    # Generar imágenes de prueba
    generate_test_image("image1.jpg", 1024, 768)
    generate_test_image("image2.png", 1920, 1080)
    generate_test_image("image3.tiff", 4000, 3000)

    # Generar videos de prueba
    generate_test_video("video1.mp4", 1920, 1080, duration=150)  # 2:30
    generate_test_video("video2.avi", 1280, 720, duration=105)   # 1:45
    generate_test_video("video3.mov", 3840, 2160, duration=300)  # 5:00

    # Generar archivos corruptos
    generate_corrupt_image("corrupt.jpg", 100, 100)
    generate_empty_image("empty.png", 100, 100)

    # Generar archivo de texto inválido
    with open(os.path.join(TEST_FILES_DIR, "invalid.txt"), "w") as f:
        f.write("Este es un archivo de texto inválido para procesamiento de imágenes")

    print("Archivos de prueba generados exitosamente")
    +++++++ REPLACE

if __name__ == "__main__":
    main()