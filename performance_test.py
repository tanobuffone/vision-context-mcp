"""
Script para testeo de rendimiento y carga del proyecto Vision Context MCP
"""

import os
import sys
import time
import json
import logging
import psutil
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Clase para recolectar métricas de rendimiento"""
    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_usage = []
        self.network_usage = []
        self.processing_times = []

    def record_cpu_usage(self, usage: float):
        self.cpu_usage.append({
            "timestamp": time.time(),
            "usage": usage
        })

    def record_memory_usage(self, usage: float):
        self.memory_usage.append({
            "timestamp": time.time(),
            "usage": usage
        })

    def record_disk_usage(self, usage: float):
        self.disk_usage.append({
            "timestamp": time.time(),
            "usage": usage
        })

    def record_network_usage(self, usage: float):
        self.network_usage.append({
            "timestamp": time.time(),
            "usage": usage
        })

    def record_processing_time(self, tool: str, time_taken: float):
        self.processing_times.append({
            "tool": tool,
            "time_taken": time_taken,
            "timestamp": time.time()
        })

    def get_summary(self) -> Dict[str, Any]:
        return {
            "average_cpu_usage": sum(m["usage"] for m in self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
            "peak_memory_usage": max(m["usage"] for m in self.memory_usage) if self.memory_usage else 0,
            "total_processing_time": sum(t["time_taken"] for t in self.processing_times),
            "average_processing_time": sum(t["time_taken"] for t in self.processing_times) / len(self.processing_times) if self.processing_times else 0,
        }

async def monitor_resources(metrics: PerformanceMetrics, duration: int = 60):
    """Monitorear recursos del sistema durante el test"""
    logger.info(f"Monitoreando recursos por {duration} segundos")
    start_time = time.time()

    while time.time() - start_time < duration:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.record_cpu_usage(cpu_percent)

        # Memory usage
        memory_info = psutil.virtual_memory()
        metrics.record_memory_usage(memory_info.percent)

        # Disk usage
        disk_info = psutil.disk_usage('/')
        metrics.record_disk_usage(disk_info.percent)

        # Network usage
        net_info = psutil.net_io_counters()
        metrics.record_network_usage(net_info.bytes_sent + net_info.bytes_recv)

        await asyncio.sleep(1)

async def test_concurrent_processing(metrics: PerformanceMetrics, num_tasks: int = 10):
    """Testear procesamiento concurrente con carga"""
    logger.info(f"Probando procesamiento concurrente con {num_tasks} tareas")

    start_time = time.time()
    tasks = []

    # Crear tareas de procesamiento
    for i in range(num_tasks):
        tasks.append(asyncio.create_task(simulate_processing(f"task_{i}")))

    # Esperar que todas las tareas completen
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processing_time = time.time() - start_time
    metrics.record_processing_time("concurrent_processing", processing_time)

    # Contar errores
    errors = sum(1 for r in results if isinstance(r, Exception))
    logger.info(f"Procesamiento concurrente completado. Errores: {errors}/{num_tasks}")

    return results

async def simulate_processing(task_name: str):
    """Simular procesamiento de una tarea"""
    # Simular procesamiento aleatorio
    processing_time = random.uniform(0.5, 3.0)
    await asyncio.sleep(processing_time)
    return f"{task_name}_result"

async def test_memory_stress(metrics: PerformanceMetrics, max_memory_mb: int = 500):
    """Testear manejo de memoria bajo estrés"""
    logger.info(f"Probando estrés de memoria (max {max_memory_mb} MB)")

    start_time = time.time()
    large_array = None

    try:
        # Crear array grande
        large_array = np.random.rand(1000, 1000, 100)  # ~800MB

        # Procesar datos
        result = np.sum(large_array)
        processing_time = time.time() - start_time
        metrics.record_processing_time("memory_stress", processing_time)

        logger.info(f"Test de estrés de memoria completado. Resultado: {result}")
        return result

    except Exception as e:
        logger.error(f"Error en test de estrés de memoria: {e}")
        return None

    finally:
        # Liberar memoria
        if large_array is not None:
            del large_array

async def test_cpu_stress(metrics: PerformanceMetrics, duration: int = 30):
    """Testear carga de CPU"""
    logger.info(f"Probando estrés de CPU por {duration} segundos")

    start_time = time.time()
    cpu_intensive_task()

    processing_time = time.time() - start_time
    metrics.record_processing_time("cpu_stress", processing_time)
    logger.info(f"Test de estrés de CPU completado en {processing_time:.2f} segundos")

def cpu_intensive_task():
    """Tarea intensiva de CPU"""
    # Calcular primos (tarea intensiva)
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    primes = [n for n in range(100000) if is_prime(n)]
    return primes

async def run_performance_tests():
    """Ejecutar todos los tests de rendimiento"""
    logger.info("Iniciando testeo de rendimiento y carga")

    metrics = PerformanceMetrics()

    # Crear directorio de resultados
    os.makedirs("performance_results", exist_ok=True)

    # Ejecutar tests de rendimiento
    tests = [
        test_concurrent_processing,
        test_memory_stress,
        test_cpu_stress
    ]

    # Ejecutar tests de forma asíncrona
    results = await asyncio.gather(*[test(metrics) for test in tests], return_exceptions=True)

    # Monitorear recursos durante los tests
    monitor_task = asyncio.create_task(monitor_resources(metrics, duration=60))
    await monitor_task

    # Generar reporte
    summary = metrics.get_summary()
    summary["timestamp"] = time.time()
    summary["total_tests"] = len(tests)

    # Guardar reporte
    with open("performance_results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Testeo de rendimiento completado")
    logger.info(f"Resumen: {json.dumps(summary, indent=2)}")

    return summary

if __name__ == "__main__":
    asyncio.run(run_performance_tests())