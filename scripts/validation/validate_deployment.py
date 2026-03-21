#!/usr/bin/env python3
"""
Complete pre-deployment validation script.
Runs all validation phases to ensure deployment readiness.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n-> {description}")
    print(f"   Command: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   FAILED: {result.stderr[:200]}")
        return False
    
    print(f"   OK")
    if result.stdout:
        print(f"   {result.stdout[:150]}")
    return True

def main():
    """Run all validation phases."""
    
    project_dir = "/home/gdrick/vision-context-mcp"
    
    print("=" * 70)
    print("VISION CONTEXT MCP - PRE-DEPLOYMENT VALIDATION")
    print("=" * 70)
    
    phases = [
        ("Phase 1: Environment Check", [
            ("python --version", "Check Python version"),
            (f"pip show mcp opencv-python pillow numpy | grep -E 'Name|Version'", "Check core dependencies"),
        ]),
        ("Phase 2: Installation", [
            (f"cd {project_dir} && pip install -e . -q", "Install package"),
            ('python -c "from vision_context_mcp import server; print(\'Import OK\')"', "Test import"),
        ]),
        ("Phase 3: Create Test Data", [
            (f"python {project_dir}/scripts/validation/create_test_image.py", "Create test image"),
        ]),
        ("Phase 4: Test Tools", [
            (f"python {project_dir}/tests/validation/test_all_tools.py", "Test all MCP tools"),
        ]),
    ]
    
    all_passed = True
    
    for phase_name, commands in phases:
        print(f"\n{'=' * 70}")
        print(f"  {phase_name}")
        print(f"{'=' * 70}")
        
        for cmd, desc in commands:
            if not run_command(cmd, desc):
                all_passed = False
                print(f"\nSTOPPED: Failed at '{desc}'")
                break
        
        if not all_passed:
            break
    
    print(f"\n{'=' * 70}")
    if all_passed:
        print("RESULT: ALL VALIDATION PHASES PASSED")
        print("The project is ready for deployment.")
    else:
        print("RESULT: VALIDATION FAILED")
        print("Fix the issues above before deploying.")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())