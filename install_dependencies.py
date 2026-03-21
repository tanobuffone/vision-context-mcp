"""
Script para instalar dependencias del proyecto Vision Context MCP
"""

import subprocess
import sys

def install_package(package: str):
    """Instalar un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Instalado: {package}")
    except subprocess.CalledProcessError as e:
        print(f"Error instalando {package}: {e}")

def install_requirements():
    """Instalar todas las dependencias del proyecto"""
    print("Instalando dependencias del proyecto Vision Context MCP...")

    # Dependencias principales
    packages = [
        "opencv-python",      # Procesamiento de imágenes y video
        "numpy",              # Cálculos numéricos
        "pillow",             # Procesamiento de imágenes
        "psutil",             # Monitoreo de recursos del sistema
        "pytest",             # Framework de testing
        "pytest-asyncio",     # Testing asíncrono
        "coverage",           # Medición de cobertura de código
        "memory-profiler",    # Profiling de memoria
    ]

    # Instalar cada paquete
    for package in packages:
        install_package(package)

    print("Dependencias instaladas exitosamente")

if __name__ == "__main__":
    install_requirements()