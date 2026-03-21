"""
Script para ejecutar el testeo extenso completo del proyecto Vision Context MCP
"""

import os
import sys
import subprocess
import time
import json
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command: str, description: str):
    """Ejecutar un comando y mostrar su progreso"""
    logger.info(f"Ejecutando: {description}")
    start_time = time.time()
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"Completado: {description} en {time.time() - start_time:.2f} segundos")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en {description}: {e.stderr}")
        return None

def main():
    logger.info("Iniciando testeo extenso del proyecto Vision Context MCP")

    # 1. Instalar dependencias
    logger.info("Paso 1: Instalando dependencias")
    run_command("python install_dependencies.py", "Instalación de dependencias")

    # 2. Generar archivos de prueba
    logger.info("Paso 2: Generando archivos de prueba")
    run_command("python generate_test_files.py", "Generación de archivos de prueba")

    # 3. Ejecutar testeo extenso
    logger.info("Paso 3: Ejecutando testeo extenso")
    run_command("python test_extensive.py", "Testeo extenso de funcionalidad")

    # 4. Generar reporte final
    logger.info("Paso 4: Generando reporte final")
    summary_path = "test_results/summary.json"
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            summary = json.load(f)
            logger.info("Testeo extenso completado exitosamente")
            logger.info(f"Resumen: {json.dumps(summary, indent=2)}")
    else:
        logger.error("No se encontró el reporte de testeo")

    logger.info("Testeo extenso finalizado")

if __name__ == "__main__":
    main()