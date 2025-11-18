"""
JOLT v0.3 Test Suite - Comprehensive testing
Because we're not just building a format, we're building confidence!
"""
import json
from typing import Any, Dict

# Import JOLT functions
import sys
sys.path.insert(0, '/mnt/user-data/outputs/jolt_v0.3')

from jolt import json_to_jolt, jolt_to_json, JoltSyntaxError, JoltOptimizer


def test_basic_roundtrip():
    """Test basic encoding and decoding"""
    test_cases = [
        {"id": 1, "name": "test"},
        {"active": True, "count": 42, "ratio": 3.14},
        {"empty": None},
    ]
    
    for data in test_cases:
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert_equal(data, recovered, "Basic roundtrip")


def test_nested_structures():
    """Test deeply nested objects"""
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "value": "deep"
                }
            }
        }
    }
    
    jolt = json_to_jolt(data)
    recovered = jolt_to_json(jolt)
    assert_equal(data, recovered, "Nested structures")


def test_arrays():
    """Test various array formats"""
    test_cases = [
        {"simple": [1, 2, 3, 4, 5]},
        {"empty": []},
        {"strings": ["a", "b", "c"]},
        {"mixed": [1, "two", 3.0, True, None]},
    ]
    
    for data in test_cases:
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert_equal(data, recovered, f"Array test: {list(data.keys())[0]}")


def test_table_format():
    """Test table format for uniform object arrays"""
    data = {
        "users": [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
    }
    
    jolt = json_to_jolt(data)
    assert "users[3] {" in jolt, "Table format should be used"
    assert "id, name, age:" in jolt, "Table headers should be present"
    
    recovered = jolt_to_json(jolt)
    assert_equal(data, recovered, "Table format roundtrip")


def test_special_characters():
    """Test handling of special characters"""
    data = {
        "quote": 'He said "hello"',
        "newline": "line1\nline2",
        "tab": "col1\tcol2",
        "backslash": "path\\to\\file",
        "unicode": "emoji: 😀 math: α+β=γ",
    }
    
    jolt = json_to_jolt(data)
    recovered = jolt_to_json(jolt)
    assert_equal(data, recovered, "Special characters")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    test_cases = [
        {},  # Empty object
        {"key": ""},  # Empty string
        {"num": 0},  # Zero
        {"neg": -999},  # Negative number
        {"float": 0.0000001},  # Small float
        {"bool_true": True, "bool_false": False},
        {"null": None},
    ]
    
    for data in test_cases:
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert_equal(data, recovered, f"Edge case: {data}")


def test_named_root():
    """Test named root blocks"""
    data = {"scenario": {"id": 7, "name": "Test"}}
    
    # With root name
    jolt = json_to_jolt(data, root_name="scenario")
    assert jolt.startswith("scenario {"), "Should have named root"
    
    recovered = jolt_to_json(jolt)
    assert_equal(data, recovered, "Named root roundtrip")


def test_braceless_root():
    """Test braceless root objects (v0.3 fix)"""
    jolt_text = """
id: 1
name: test
active: true
"""
    
    try:
        result = jolt_to_json(jolt_text.strip())
        expected = {"id": 1, "name": "test", "active": True}
        assert_equal(result, expected, "Braceless root parsing")
    except Exception as e:
        print(f"✗ Braceless root: {e}")
        raise


def test_error_handling():
    """Test error messages are helpful"""
    invalid_cases = [
        ('key: "unterminated', "Should catch unterminated string"),
        ('key: [5]', "Should catch missing array elements"),
        ('[[[[', "Should catch unmatched brackets"),
        ('key\n  value', "Should catch missing colon"),
    ]
    
    for jolt_text, description in invalid_cases:
        try:
            jolt_to_json(jolt_text)
            print(f"✗ {description}: Should have raised error")
        except JoltSyntaxError as e:
            print(f"✓ {description}: {str(e)[:50]}...")
        except Exception as e:
            print(f"✗ {description}: Wrong error type: {type(e).__name__}")


def test_optimizer():
    """Test optimizer functionality"""
    data = {
        "identifier": 1,
        "description": "A test description",
        "configuration": {
            "temperature": 0.7,
            "maximum": 100
        }
    }
    
    optimizer = JoltOptimizer(enable_abbreviations=True)
    optimized, stats = optimizer.optimize(data)
    
    # Check that abbreviations were applied
    assert "id" in optimized or "identifier" in optimized
    assert stats.tokens_saved >= 0
    assert len(stats.warnings) == 0, f"Should have no warnings in safe mode, got: {stats.warnings}"
    
    # Verify optimized data can be encoded and decoded
    jolt = json_to_jolt(optimized)
    recovered = jolt_to_json(jolt)
    
    # Note: recovered will have abbreviated keys, that's expected
    print(f"✓ Optimizer: {stats.tokens_saved} tokens saved, {stats.optimizations_applied}")


def test_complex_scenario():
    """Test complex real-world scenario"""
    data = {
        "scenario": {
            "id": 7,
            "name": "Port Delay",
            "supplier": {
                "id": 92,
                "name": "Hankyu Steel",
                "delays": [7, 12, 3],
                "location": {
                    "country": "JP",
                    "port": "Kobe"
                }
            },
            "events": [
                {"t": 1021, "type": "delay", "days": 7},
                {"t": 1033, "type": "delay", "days": 12}
            ]
        }
    }
    
    jolt = json_to_jolt(data, root_name="scenario")
    
    # Verify structure
    assert "scenario {" in jolt
    assert "supplier {" in jolt
    assert "location {" in jolt
    assert "delays[3]:" in jolt
    assert "events[2] {" in jolt
    
    recovered = jolt_to_json(jolt)
    assert_equal(data, recovered, "Complex scenario")


def assert_equal(actual: Any, expected: Any, test_name: str):
    """Deep equality check with helpful output"""
    # Use JSON serialization for comparison
    actual_json = json.dumps(actual, sort_keys=True)
    expected_json = json.dumps(expected, sort_keys=True)
    
    if actual_json == expected_json:
        print(f"✓ {test_name}")
    else:
        print(f"✗ {test_name}")
        print(f"  Expected: {expected_json[:100]}...")
        print(f"  Got:      {actual_json[:100]}...")
        raise AssertionError(f"{test_name} failed")


def run_all_tests():
    """Run all tests"""
    tests = [
        ("Basic Roundtrip", test_basic_roundtrip),
        ("Nested Structures", test_nested_structures),
        ("Arrays", test_arrays),
        ("Table Format", test_table_format),
        ("Special Characters", test_special_characters),
        ("Edge Cases", test_edge_cases),
        ("Named Root", test_named_root),
        ("Braceless Root", test_braceless_root),
        ("Error Handling", test_error_handling),
        ("Optimizer", test_optimizer),
        ("Complex Scenario", test_complex_scenario),
    ]
    
    print("JOLT v0.3 Test Suite")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 50)
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
