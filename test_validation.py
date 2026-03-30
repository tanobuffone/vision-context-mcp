#!/usr/bin/env python3
"""Tests for validation module."""
import sys
sys.path.insert(0, 'src')

from vision_context_mcp.validation import (
    validate_tool_arguments,
    safe_json_dumps,
    sanitize_for_json,
    FileNotFoundValidationError,
    FileExtensionError,
    FileSizeError,
    ParameterValidationError,
    ToolNotFoundError,
)
import json

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name}: {e}")
        failed += 1

def test_tool_not_found():
    try:
        validate_tool_arguments('fake_tool', {})
        assert False, "Should have raised"
    except ToolNotFoundError as e:
        assert 'fake_tool' in str(e)

def test_invalid_method():
    try:
        validate_tool_arguments('analyze_edges', {'image_path': '/tmp/test.jpg', 'method': 'invalid'})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'method' in str(e)

def test_threshold_order():
    try:
        validate_tool_arguments('analyze_edges', {'image_path': '/tmp/test.jpg', 'low_threshold': 250, 'high_threshold': 100})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'low_threshold' in str(e)

def test_file_not_found():
    try:
        validate_tool_arguments('analyze_edges', {'image_path': '/nonexistent/image.jpg'})
        assert False, "Should have raised"
    except FileNotFoundValidationError as e:
        assert '/nonexistent/image.jpg' in str(e)

def test_confidence_range():
    try:
        validate_tool_arguments('detect_objects', {'image_path': '/tmp/test.jpg', 'confidence': 1.5})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'confidence' in str(e)

def test_video_fps_range():
    try:
        validate_tool_arguments('extract_video_frames', {'video_path': '/tmp/test.mp4', 'fps': 50.0})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'fps' in str(e)

def test_video_max_frames():
    try:
        validate_tool_arguments('extract_video_frames', {'video_path': '/tmp/test.mp4', 'max_frames': 5000})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'max_frames' in str(e)

def test_detail_level():
    try:
        validate_tool_arguments('describe_for_3d', {'image_path': '/tmp/test.jpg', 'detail_level': 'super'})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'detail_level' in str(e)

def test_json_nan():
    result = {'value': float('nan'), 'normal': 3.14}
    output = safe_json_dumps(result)
    parsed = json.loads(output)
    assert parsed['value'] == 'nan'
    assert parsed['normal'] == 3.14

def test_json_inf():
    result = {'inf': float('inf'), 'neg_inf': float('-inf')}
    output = safe_json_dumps(result)
    parsed = json.loads(output)
    assert parsed['inf'] == 'inf'
    assert parsed['neg_inf'] == '-inf'

def test_json_depth():
    deep = {'level': 0}
    for i in range(25):
        deep = {'level': i, 'child': deep}
    output = safe_json_dumps(deep)
    assert '<max depth' in output

def test_json_long_list():
    big_list = list(range(15000))
    output = safe_json_dumps(big_list)
    parsed = json.loads(output)
    assert len(parsed) == 10001
    assert '<truncated' in parsed[-1]

def test_json_long_string():
    long_str = 'A' * 200000
    output = safe_json_dumps({'text': long_str})
    parsed = json.loads(output)
    assert '<truncated' in parsed['text']

def test_json_numpy():
    import numpy as np
    result = {'arr': np.array([1.0, 2.0, 3.0]), 'int': np.int64(42), 'float': np.float32(3.14)}
    output = safe_json_dumps(result)
    parsed = json.loads(output)
    assert parsed['arr'] == [1.0, 2.0, 3.0]
    assert parsed['int'] == 42
    assert isinstance(parsed['float'], float)

def test_json_path():
    from pathlib import Path
    result = {'path': Path('/tmp/test.jpg')}
    output = safe_json_dumps(result)
    parsed = json.loads(output)
    assert parsed['path'] == '/tmp/test.jpg'

def test_timestamp_negative():
    try:
        validate_tool_arguments('extract_keyframe', {'video_path': '/tmp/test.mp4', 'timestamp': -1.0})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'timestamp' in str(e)

def test_threshold_negative():
    try:
        validate_tool_arguments('detect_scene_changes', {'video_path': '/tmp/test.mp4', 'threshold': -5.0})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'threshold' in str(e)

def test_sample_rate_zero():
    try:
        validate_tool_arguments('analyze_video_motion', {'video_path': '/tmp/test.mp4', 'sample_rate': 0})
        assert False, "Should have raised"
    except ParameterValidationError as e:
        assert 'sample_rate' in str(e)

def test_json_numpy_large_array():
    import numpy as np
    arr = np.zeros(100000)
    result = {'big_arr': arr}
    output = safe_json_dumps(result)
    parsed = json.loads(output)
    assert parsed['big_arr']['type'] == 'ndarray'
    assert parsed['big_arr']['truncated'] is True

# Run all tests
print("Running validation tests...\n")
test("Tool not found", test_tool_not_found)
test("Invalid method", test_invalid_method)
test("Threshold order", test_threshold_order)
test("File not found", test_file_not_found)
test("Confidence range", test_confidence_range)
test("Video FPS range", test_video_fps_range)
test("Video max_frames", test_video_max_frames)
test("Detail level", test_detail_level)
test("JSON NaN", test_json_nan)
test("JSON Inf", test_json_inf)
test("JSON depth limit", test_json_depth)
test("JSON long list", test_json_long_list)
test("JSON long string", test_json_long_string)
test("JSON numpy types", test_json_numpy)
test("JSON Path object", test_json_path)
test("Timestamp negative", test_timestamp_negative)
test("Threshold negative", test_threshold_negative)
test("Sample rate zero", test_sample_rate_zero)
test("JSON large numpy array", test_json_numpy_large_array)

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
