#!/usr/bin/env python3
"""
Test all MCP tools to validate deployment.
"""

import asyncio
import json
import sys
import os

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vision_context_mcp.preprocessors import edges, depth, pose, segmentation
from vision_context_mcp.analyzers import image_analyzer, video_analyzer, entity_extractor

TEST_IMAGE = "/tmp/test_image_vision_mcp.jpg"

TOOLS_TO_TEST = [
    ("analyze_edges", lambda: edges.analyze_edges(TEST_IMAGE, "canny")),
    ("analyze_depth", lambda: depth.analyze_depth(TEST_IMAGE, "midas")),
    ("analyze_pose", lambda: pose.analyze_pose(TEST_IMAGE)),
    ("analyze_segmentation", lambda: segmentation.analyze_segmentation(TEST_IMAGE)),
    ("detect_objects", lambda: entity_extractor.detect_objects(TEST_IMAGE)),
    ("build_image_context", lambda: image_analyzer.build_context(TEST_IMAGE)),
    ("describe_for_3d", lambda: image_analyzer.describe_for_3d(TEST_IMAGE)),
    ("extract_entities_3d", lambda: entity_extractor.extract_entities_3d(TEST_IMAGE)),
]

async def test_all_tools():
    """Test all tools and report results."""
    
    if not os.path.exists(TEST_IMAGE):
        print(f"ERROR: Test image not found: {TEST_IMAGE}")
        print("Run: python scripts/validation/create_test_image.py")
        return False
    
    print("=" * 60)
    print("TESTING ALL MCP TOOLS")
    print("=" * 60)
    
    results = []
    
    for tool_name, tool_func in TOOLS_TO_TEST:
        print(f"\nTesting: {tool_name}...", end=" ")
        
        try:
            result = await tool_func()
            
            if isinstance(result, dict):
                if result.get("success") is False:
                    results.append((tool_name, "WARNING", result.get("error", "Unknown error")))
                    print("WARNING")
                else:
                    results.append((tool_name, "OK", ""))
                    print("OK")
            else:
                results.append((tool_name, "OK", ""))
                print("OK")
                
        except Exception as e:
            results.append((tool_name, "ERROR", str(e)[:100]))
            print(f"ERROR: {str(e)[:50]}")
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    for tool_name, status, error in results:
        symbol = "OK" if status == "OK" else "WARNING" if status == "WARNING" else "ERROR"
        print(f"[{symbol}] {tool_name}")
        if error:
            print(f"     -> {error}")
    
    passed = sum(1 for _, s, _ in results if s == "OK")
    warnings = sum(1 for _, s, _ in results if s == "WARNING")
    failed = sum(1 for _, s, _ in results if s == "ERROR")
    
    print(f"\nTotal: {len(results)} tools")
    print(f"  Passed: {passed}")
    print(f"  Warnings: {warnings}")
    print(f"  Failed: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)