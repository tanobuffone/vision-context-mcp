"""
Script para ejecutar todos los tests del proyecto Vision Context MCP
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_script(script_name: str, description: str):
    """Ejecutar un script de test"""
    logger.info(f"Ejecutando {description}...")
    start_time = time.time()
    try:
        result = subprocess.run(
            ["python", script_name],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"{description} completado en {time.time() - start_time:.2f} segundos")
        return {
            "status": "success",
            "output": result.stdout,
            "time": time.time() - start_time
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en {description}: {e.stderr}")
        return {
            "status": "error",
            "output": e.stderr,
            "time": time.time() - start_time
        }

def main():
    logger.info("Iniciando ejecución de todos los tests del proyecto Vision Context MCP")

    # Crear directorios de resultados
    os.makedirs("test_results", exist_ok=True)
    os.makedirs("performance_results", exist_ok=True)
    os.makedirs("security_results", exist_ok=True)
    os.makedirs("production_results", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Ejecutar tests en orden
    tests = [
        ("test_extensive.py", "Testeo extenso de funcionalidad"),
        ("performance_test.py", "Testeo de rendimiento y carga"),
        ("security_test.py", "Testeo de robustez y seguridad"),
        ("production_validation.py", "Validación de producción"),
        ("generate_final_report.py", "Generación de reporte final")
    ]

    results = {}

    for script, description in tests:
        result = run_test_script(script, description)
        results[description] = result

        # Verificar si hubo error para detener ejecución
        if result["status"] == "error":
            logger.error(f"Error en {description}. Deteniendo ejecución.")
            break

    # Generar resumen general
    summary = {
        "timestamp": time.time(),
        "total_tests": len(tests),
        "successful_tests": len([r for r in results.values() if r["status"] == "success"]),
        "failed_tests": len([r for r in results.values() if r["status"] == "error"]),
        "test_results": results
    }

    # Guardar resumen
    with open("reports/execution_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Ejecución de todos los tests completada")
    logger.info(f"Resumen: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    main()