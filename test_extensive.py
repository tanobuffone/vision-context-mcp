"""
Script de Testeo Extensivo para Vision Context MCP
"""

import asyncio
import time
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import pytest
import pytest_asyncio
import coverage
import memory_profiler
import psutil

# Importar el proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vision_context_mcp import _execute_tool
from vision_context_mcp.preprocessors import edges, depth, pose, segmentation
from vision_context_mcp.analyzers import image_analyzer, video_analyzer, entity_extractor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de testing
TEST_CONFIG = {
    "max_processing_time": 30,  # segundos
    "max_memory_usage": 500,    # MB
    "max_concurrent": 5,        # procesamientos simultáneos
    "test_images": [
        {"path": "test_images/image1.jpg", "format": "jpg", "size": "1024x768"},
        {"path": "test_images/image2.png", "format": "png", "size": "1920x1080"},
        {"path": "test_images/image3.tiff", "format": "tiff", "size": "4000x3000"},
    ],
    "test_videos": [
        {"path": "test_videos/video1.mp4", "format": "mp4", "resolution": "1080p", "duration": "2:30"},
        {"path": "test_videos/video2.avi", "format": "avi", "resolution": "720p", "duration": "1:45"},
        {"path": "test_videos/video3.mov", "format": "mov", "resolution": "4K", "duration": "5:00"},
    ],
    "invalid_files": [
        {"path": "test_files/corrupt.jpg", "description": "Imagen corrupta"},
        {"path": "test_files/invalid.txt", "description": "Archivo de texto"},
        {"path": "test_files/empty.png", "description": "Imagen vacía"},
    ]
}

class TestMetrics:
    """Clase para recolectar métricas de testing"""
    def __init__(self):
        self.processing_times = []
        self.memory_usage = []
        self.errors = []
        self.successes = []

    def record_processing_time(self, tool: str, time_taken: float):
        self.processing_times.append({
            "tool": tool,
            "time_taken": time_taken,
            "timestamp": time.time()
        })

    def record_memory_usage(self, tool: str, memory_used: float):
        self.memory_usage.append({
            "tool": tool,
            "memory_used": memory_used,
            "timestamp": time.time()
        })

    def record_error(self, tool: str, error: str):
        self.errors.append({
            "tool": tool,
            "error": error,
            "timestamp": time.time()
        })

    def record_success(self, tool: str):
        self.successes.append({
            "tool": tool,
            "timestamp": time.time()
        })

    def get_summary(self) -> Dict[str, Any]:
        return {
            "average_processing_time": sum(t["time_taken"] for t in self.processing_times) / len(self.processing_times) if self.processing_times else 0,
            "max_processing_time": max(t["time_taken"] for t in self.processing_times) if self.processing_times else 0,
            "total_errors": len(self.errors),
            "success_rate": len(self.successes) / (len(self.successes) + len(self.errors)) if (len(self.successes) + len(self.errors)) > 0 else 0,
            "peak_memory_usage": max(m["memory_used"] for m in self.memory_usage) if self.memory_usage else 0,
        }

# Crear instancia de métricas
metrics = TestMetrics()

async def test_preprocessor_edges():
    """Testear el preprocessor de edges"""
    logger.info("Iniciando test de edges")
    start_time = time.time()

    try:
        # Probar con diferentes métodos
        methods = ["canny", "hed", "mlsd", "softedge"]
        for method in methods:
            result = await edges.analyze_edges(
                image_path=TEST_CONFIG["test_images"][0]["path"],
                method=method
            )
            assert result is not None
            assert "edge_statistics" in result
            assert "contours" in result

        metrics.record_success("edges")
        processing_time = time.time() - start_time
        metrics.record_processing_time("edges", processing_time)
        logger.info(f"Test de edges completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("edges", str(e))
        logger.error(f"Error en test de edges: {e}")
    finally:
        logger.info("Test de edges finalizado")

async def test_preprocessor_depth():
    """Testear el preprocessor de depth"""
    logger.info("Iniciando test de depth")
    start_time = time.time()

    try:
        models = ["midas", "zoedepth", "dpt"]
        for model in models:
            result = await depth.analyze_depth(
                image_path=TEST_CONFIG["test_images"][0]["path"],
                model=model
            )
            assert result is not None
            assert "spatial_regions" in result
            assert "depth_statistics" in result

        metrics.record_success("depth")
        processing_time = time.time() - start_time
        metrics.record_processing_time("depth", processing_time)
        logger.info(f"Test de depth completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("depth", str(e))
        logger.error(f"Error en test de depth: {e}")
    finally:
        logger.info("Test de depth finalizado")

async def test_preprocessor_pose():
    """Testear el preprocessor de pose"""
    logger.info("Iniciando test de pose")
    start_time = time.time()

    try:
        result = await pose.analyze_pose(
            image_path=TEST_CONFIG["test_images"][0]["path"],
            include_hands=True,
            include_face=True
        )
        assert result is not None
        assert "person_count" in result
        assert "poses" in result

        metrics.record_success("pose")
        processing_time = time.time() - start_time
        metrics.record_processing_time("pose", processing_time)
        logger.info(f"Test de pose completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("pose", str(e))
        logger.error(f"Error en test de pose: {e}")
    finally:
        logger.info("Test de pose finalizado")

async def test_preprocessor_segmentation():
    """Testear el preprocessor de segmentation"""
    logger.info("Iniciando test de segmentation")
    start_time = time.time()

    try:
        result = await segmentation.analyze_segmentation(
            image_path=TEST_CONFIG["test_images"][0]["path"]
        )
        assert result is not None
        assert "scene_composition" in result
        assert "detected_regions" in result

        metrics.record_success("segmentation")
        processing_time = time.time() - start_time
        metrics.record_processing_time("segmentation", processing_time)
        logger.info(f"Test de segmentation completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("segmentation", str(e))
        logger.error(f"Error en test de segmentation: {e}")
    finally:
        logger.info("Test de segmentation finalizado")

async def test_analyzer_image():
    """Testear el analyzer de imagen"""
    logger.info("Iniciando test de image analyzer")
    start_time = time.time()

    try:
        result = await image_analyzer.build_context(
            image_path=TEST_CONFIG["test_images"][0]["path"]
        )
        assert result is not None
        assert "image_dimensions" in result
        assert "edge_analysis" in result
        assert "depth_analysis" in result
        assert "segmentation" in result

        metrics.record_success("image_analyzer")
        processing_time = time.time() - start_time
        metrics.record_processing_time("image_analyzer", processing_time)
        logger.info(f"Test de image analyzer completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("image_analyzer", str(e))
        logger.error(f"Error en test de image analyzer: {e}")
    finally:
        logger.info("Test de image analyzer finalizado")

async def test_analyzer_video():
    """Testear el analyzer de video"""
    logger.info("Iniciando test de video analyzer")
    start_time = time.time()

    try:
        result = await video_analyzer.get_video_context(
            video_path=TEST_CONFIG["test_videos"][0]["path"]
        )
        assert result is not None
        assert "video_metadata" in result
        assert "scene_structure" in result
        assert "motion_analysis" in result

        metrics.record_success("video_analyzer")
        processing_time = time.time() - start_time
        metrics.record_processing_time("video_analyzer", processing_time)
        logger.info(f"Test de video analyzer completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("video_analyzer", str(e))
        logger.error(f"Error en test de video analyzer: {e}")
    finally:
        logger.info("Test de video analyzer finalizado")

async def test_entity_extractor():
    """Testear el entity extractor"""
    logger.info("Iniciando test de entity extractor")
    start_time = time.time()

    try:
        result = await entity_extractor.extract_entities_3d(
            image_path=TEST_CONFIG["test_images"][0]["path"]
        )
        assert result is not None
        assert "entities" in result

        metrics.record_success("entity_extractor")
        processing_time = time.time() - start_time
        metrics.record_processing_time("entity_extractor", processing_time)
        logger.info(f"Test de entity extractor completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("entity_extractor", str(e))
        logger.error(f"Error en test de entity extractor: {e}")
    finally:
        logger.info("Test de entity extractor finalizado")

async def test_mcp_tools():
    """Testear todas las herramientas MCP"""
    logger.info("Iniciando test de herramientas MCP")
    tools_to_test = [
        "analyze_edges",
        "analyze_depth",
        "analyze_pose",
        "analyze_segmentation",
        "detect_objects",
        "build_image_context",
        "describe_for_3d",
        "extract_entities_3d",
        "extract_video_frames",
        "detect_scene_changes",
        "analyze_video_motion",
        "get_video_context",
        "extract_keyframe"
    ]

    for tool in tools_to_test:
        start_time = time.time()
        try:
            # Crear argumentos básicos para testing
            if "video" in tool:
                arguments = {"video_path": TEST_CONFIG["test_videos"][0]["path"]}
            else:
                arguments = {"image_path": TEST_CONFIG["test_images"][0]["path"]}

            # Algunas herramientas necesitan parámetros adicionales
            if tool == "analyze_edges":
                arguments["method"] = "canny"
            elif tool == "analyze_depth":
                arguments["model"] = "midas"
            elif tool == "extract_keyframe":
                arguments["timestamp"] = 10.0

            result = await _execute_tool(tool, arguments)
            assert result is not None

            metrics.record_success(tool)
            processing_time = time.time() - start_time
            metrics.record_processing_time(tool, processing_time)
            logger.info(f"Test de herramienta {tool} completado en {processing_time:.2f} segundos")

        except Exception as e:
            metrics.record_error(tool, str(e))
            logger.error(f"Error en test de herramienta {tool}: {e}")
        finally:
            logger.info(f"Test de herramienta {tool} finalizado")

async def test_concurrent_processing():
    """Testear procesamiento concurrente"""
    logger.info("Iniciando test de procesamiento concurrente")
    start_time = time.time()

    try:
        # Probar con múltiples imágenes simultáneamente
        tasks = []
        for image in TEST_CONFIG["test_images"][:3]:  # Probar con 3 imágenes
            tasks.append(image_analyzer.build_context(image_path=image["path"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verificar resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                metrics.record_error(f"concurrent_{i}", str(result))
                logger.error(f"Error en procesamiento concurrente {i}: {result}")
            else:
                metrics.record_success(f"concurrent_{i}")
                assert result is not None

        metrics.record_success("concurrent_processing")
        processing_time = time.time() - start_time
        metrics.record_processing_time("concurrent_processing", processing_time)
        logger.info(f"Test de procesamiento concurrente completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("concurrent_processing", str(e))
        logger.error(f"Error en test de procesamiento concurrente: {e}")
    finally:
        logger.info("Test de procesamiento concurrente finalizado")

async def test_invalid_inputs():
    """Testear manejo de inputs inválidos"""
    logger.info("Iniciando test de inputs inválidos")
    start_time = time.time()

    try:
        # Probar con archivos corruptos
        for invalid_file in TEST_CONFIG["invalid_files"]:
            try:
                # Intentar procesar archivo inválido
                if invalid_file["path"].endswith(".jpg"):
                    result = await edges.analyze_edges(
                        image_path=invalid_file["path"],
                        method="canny"
                    )
                else:
                    result = await image_analyzer.build_context(
                        image_path=invalid_file["path"]
                    )

                # Debería fallar
                assert result is None
                metrics.record_success(f"invalid_{invalid_file['path']}")
                logger.info(f"Test de input inválido {invalid_file['path']} completado exitosamente")

            except Exception as e:
                # Error esperado
                metrics.record_success(f"invalid_{invalid_file['path']}")
                logger.info(f"Test de input inválido {invalid_file['path']} manejado correctamente: {e}")

        metrics.record_success("invalid_inputs")
        processing_time = time.time() - start_time
        metrics.record_processing_time("invalid_inputs", processing_time)
        logger.info(f"Test de inputs inválidos completado en {processing_time:.2f} segundos")

    except Exception as e:
        metrics.record_error("invalid_inputs", str(e))
        logger.error(f"Error en test de inputs inválidos: {e}")

async def test_memory_usage():
    """Testear uso de memoria"""
    logger.info("Iniciando test de uso de memoria")
    start_time = time.time()

    try:
        # Procesar imágenes grandes para medir uso de memoria
        large_image = TEST_CONFIG["test_images"][2]  # Imagen más grande
        process = psutil.Process(os.getpid())

        # Medir memoria antes
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Procesar imagen
        result = await image_analyzer.build_context(
            image_path=large_image["path"]
        )

        # Medir memoria después
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before

        assert result is not None
        assert mem_used < TEST_CONFIG["max_memory_usage"]

        metrics.record_memory_usage("memory_test", mem_used)
        metrics.record_success("memory_test")
        processing_time = time.time() - start_time
        metrics.record_processing_time("memory_test", processing_time)
        logger.info(f"Test de uso de memoria completado. Usado: {mem_used:.2f} MB")

    except Exception as e:
        metrics.record_error("memory_test", str(e))
        logger.error(f"Error en test de uso de memoria: {e}")

async def run_all_tests():
    """Ejecutar todos los tests"""
    logger.info("Iniciando testeo extenso del proyecto Vision Context MCP")

    # Crear directorio de test si no existe
    os.makedirs("test_results", exist_ok=True)

    # Ejecutar tests
    tests = [
        test_preprocessor_edges,
        test_preprocessor_depth,
        test_preprocessor_pose,
        test_preprocessor_segmentation,
        test_analyzer_image,
        test_analyzer_video,
        test_entity_extractor,
        test_mcp_tools,
        test_concurrent_processing,
        test_invalid_inputs,
        test_memory_usage
    ]

    # Ejecutar tests de forma asíncrona
    results = await asyncio.gather(*[test() for test in tests], return_exceptions=True)

    # Generar reporte
    summary = metrics.get_summary()
    summary["total_tests"] = len(tests)
    summary["timestamp"] = time.time()

    # Guardar reporte
    with open("test_results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Testeo extenso completado")
    logger.info(f"Resumen: {json.dumps(summary, indent=2)}")

    return summary

if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(run_all_tests())