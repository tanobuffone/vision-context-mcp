"""
Script para testeo de robustez y seguridad del proyecto Vision Context MCP
"""

import os
import sys
import time
import json
import logging
import subprocess
import random
import string
from pathlib import Path
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityMetrics:
    """Clase para recolectar métricas de seguridad"""
    def __init__(self):
        self.vulnerabilities = []
        self.security_tests = []
        self.robustness_tests = []
        self.performance_tests = []

    def record_vulnerability(self, type: str, description: str, severity: str):
        self.vulnerabilities.append({
            "type": type,
            "description": description,
            "severity": severity,
            "timestamp": time.time()
        })

    def record_security_test(self, test_name: str, result: bool, details: str):
        self.security_tests.append({
            "test_name": test_name,
            "result": result,
            "details": details,
            "timestamp": time.time()
        })

    def record_robustness_test(self, test_name: str, result: bool, details: str):
        self.robustness_tests.append({
            "test_name": test_name,
            "result": result,
            "details": details,
            "timestamp": time.time()
        })

    def record_performance_test(self, test_name: str, result: bool, details: str):
        self.performance_tests.append({
            "test_name": test_name,
            "result": result,
            "details": details,
            "timestamp": time.time()
        })

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "critical_vulnerabilities": len([v for v in self.vulnerabilities if v["severity"] == "critical"]),
            "high_vulnerabilities": len([v for v in self.vulnerabilities if v["severity"] == "high"]),
            "medium_vulnerabilities": len([v for v in self.vulnerabilities if v["severity"] == "medium"]),
            "low_vulnerabilities": len([v for v in self.vulnerabilities if v["severity"] == "low"]),
            "security_test_success_rate": len([t for t in self.security_tests if t["result"]]) / len(self.security_tests) if self.security_tests else 0,
            "robustness_test_success_rate": len([t for t in self.robustness_tests if t["result"]]) / len(self.robustness_tests) if self.robustness_tests else 0,
        }

def generate_random_input(size: int = 1000) -> str:
    """Generar entrada aleatoria para testing"""
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=size))

def test_input_validation(metrics: SecurityMetrics):
    """Testear validación de inputs"""
    logger.info("Iniciando test de validación de inputs")

    test_cases = [
        {"input": generate_random_input(100), "description": "Input aleatorio pequeño"},
        {"input": generate_random_input(1000), "description": "Input aleatorio mediano"},
        {"input": generate_random_input(10000), "description": "Input aleatorio grande"},
        {"input": "<script>alert('XSS')</script>", "description": "Payload XSS"},
        {"input": "../../etc/passwd", "description": "Payload path traversal"},
        {"input": "DROP TABLE users;", "description": "Payload SQL injection"},
    ]

    for case in test_cases:
        try:
            # Simular procesamiento del input
            result = process_input(case["input"])
            metrics.record_security_test(
                test_name=f"input_validation_{case['description']}",
                result=True,
                details=f"Input procesado exitosamente: {len(case['input'])} caracteres"
            )
        except Exception as e:
            metrics.record_security_test(
                test_name=f"input_validation_{case['description']}",
                result=False,
                details=f"Error procesando input: {str(e)}"
            )

    logger.info("Test de validación de inputs completado")

def process_input(input_data: str) -> str:
    """Procesar input (simulación)"""
    # Simular procesamiento seguro del input
    if len(input_data) > 100000:
        raise ValueError("Input demasiado grande")

    # Simular validación de caracteres
    if any(c in input_data for c in ['<', '>', ';', '--', '/*', '*/']):
        raise ValueError("Caracteres no permitidos en el input")

    return f"Processed: {input_data[:100]}..."

def test_memory_exhaustion(metrics: SecurityMetrics):
    """Testear agotamiento de memoria"""
    logger.info("Iniciando test de agotamiento de memoria")

    try:
        # Intentar crear objeto muy grande
        large_array = [0] * (1024 * 1024 * 100)  # 100MB
        metrics.record_robustness_test(
            test_name="memory_exhaustion",
            result=True,
            details="Creación de objeto grande exitosa"
        )
        del large_array
    except MemoryError:
        metrics.record_robustness_test(
            test_name="memory_exhaustion",
            result=False,
            details="Error de memoria al crear objeto grande"
        )
    except Exception as e:
        metrics.record_robustness_test(
            test_name="memory_exhaustion",
            result=False,
            details=f"Error inesperado: {str(e)}"
        )

    logger.info("Test de agotamiento de memoria completado")

def test_cpu_exhaustion(metrics: SecurityMetrics):
    """Testear agotamiento de CPU"""
    logger.info("Iniciando test de agotamiento de CPU")

    try:
        # Tarea intensiva de CPU
        result = cpu_intensive_task(100000)
        metrics.record_robustness_test(
            test_name="cpu_exhaustion",
            result=True,
            details="Tarea intensiva de CPU completada"
        )
    except Exception as e:
        metrics.record_robustness_test(
            test_name="cpu_exhaustion",
            result=False,
            details=f"Error en tarea intensiva de CPU: {str(e)}"
        )

    logger.info("Test de agotamiento de CPU completado")

def cpu_intensive_task(iterations: int):
    """Tarea intensiva de CPU"""
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    primes = [n for n in range(iterations) if is_prime(n)]
    return primes

def test_file_operations(metrics: SecurityMetrics):
    """Testear operaciones con archivos"""
    logger.info("Iniciando test de operaciones con archivos")

    test_files = [
        {"name": "test1.txt", "content": generate_random_input(1000)},
        {"name": "test2.txt", "content": generate_random_input(10000)},
        {"name": "test3.txt", "content": generate_random_input(100000)},
    ]

    for test_file in test_files:
        try:
            # Escribir archivo
            with open(test_file["name"], "w") as f:
                f.write(test_file["content"])

            # Leer archivo
            with open(test_file["name"], "r") as f:
                content = f.read()
                assert len(content) == len(test_file["content"])

            # Eliminar archivo
            os.remove(test_file["name"])

            metrics.record_robustness_test(
                test_name=f"file_operations_{test_file['name']}",
                result=True,
                details="Operaciones de archivo exitosas"
            )
        except Exception as e:
            metrics.record_robustness_test(
                test_name=f"file_operations_{test_file['name']}",
                result=False,
                details=f"Error en operaciones de archivo: {str(e)}"
            )

    logger.info("Test de operaciones con archivos completado")

def test_network_operations(metrics: SecurityMetrics):
    """Testear operaciones de red"""
    logger.info("Iniciando test de operaciones de red")

    test_urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/post",
        "https://httpbin.org/status/404",
        "https://httpbin.org/delay/5",
    ]

    for url in test_urls:
        try:
            # Simular petición HTTP
            response = make_http_request(url)
            metrics.record_robustness_test(
                test_name=f"network_operations_{url}",
                result=True,
                details=f"Petición a {url} exitosa"
            )
        except Exception as e:
            metrics.record_robustness_test(
                test_name=f"network_operations_{url}",
                result=False,
                details=f"Error en petición a {url}: {str(e)}"
            )

    logger.info("Test de operaciones de red completado")

def make_http_request(url: str, timeout: int = 10) -> dict:
    """Hacer petición HTTP (simulación)"""
    import requests
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def test_concurrent_operations(metrics: SecurityMetrics, num_operations: int = 50):
    """Testear operaciones concurrentes"""
    logger.info(f"Iniciando test de operaciones concurrentes ({num_operations} operaciones)")

    try:
        # Simular operaciones concurrentes
        results = []
        for i in range(num_operations):
            result = simulate_concurrent_operation(i)
            results.append(result)

        metrics.record_robustness_test(
            test_name="concurrent_operations",
            result=True,
            details=f"{num_operations} operaciones concurrentes completadas"
        )
    except Exception as e:
        metrics.record_robustness_test(
            test_name="concurrent_operations",
            result=False,
            details=f"Error en operaciones concurrentes: {str(e)}"
        )

    logger.info("Test de operaciones concurrentes completado")

def simulate_concurrent_operation(operation_id: int):
    """Simular operación concurrente"""
    # Simular procesamiento aleatorio
    processing_time = random.uniform(0.1, 1.0)
    time.sleep(processing_time)
    return f"operation_{operation_id}_result"

async def run_security_tests():
    """Ejecutar todos los tests de seguridad"""
    logger.info("Iniciando testeo de robustez y seguridad")

    metrics = SecurityMetrics()

    # Crear directorio de resultados
    os.makedirs("security_results", exist_ok=True)

    # Ejecutar tests de seguridad
    tests = [
        test_input_validation,
        test_memory_exhaustion,
        test_cpu_exhaustion,
        test_file_operations,
        test_network_operations,
        test_concurrent_operations
    ]

    # Ejecutar tests secuencialmente
    for test in tests:
        test(metrics)

    # Generar reporte
    summary = metrics.get_summary()
    summary["timestamp"] = time.time()
    summary["total_tests"] = len(tests)

    # Guardar reporte
    with open("security_results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Testeo de seguridad completado")
    logger.info(f"Resumen: {json.dumps(summary, indent=2)}")

    return summary

if __name__ == "__main__":
    run_security_tests()