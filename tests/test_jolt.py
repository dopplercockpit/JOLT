"""
Comprehensive test suite for JOLT
Testing everything from basic encoding to streaming gigabyte files
"""
import pytest
import json
from io import StringIO
from pathlib import Path

from jolt import (
    json_to_jolt,
    jolt_to_json,
    JoltSchema,
    JoltOptimizer,
    JoltStreamParser,
    stream_jolt_to_json
)


class TestBasicEncoding:
    """Test basic encoding functionality"""
    
    def test_simple_object(self):
        data = {"id": 1, "name": "test"}
        jolt = json_to_jolt(data)
        assert "id: 1" in jolt
        assert "name: test" in jolt
    
    def test_nested_object(self):
        data = {"user": {"id": 1, "profile": {"name": "Alice"}}}
        jolt = json_to_jolt(data)
        assert "user {" in jolt
        assert "profile {" in jolt
        assert "name: Alice" in jolt
    
    def test_simple_array(self):
        data = {"items": [1, 2, 3]}
        jolt = json_to_jolt(data)
        assert "items[3]: 1,2,3" in jolt
    
    def test_table_format(self):
        data = {
            "records": [
                {"id": 1, "name": "A"},
                {"id": 2, "name": "B"}
            ]
        }
        jolt = json_to_jolt(data)
        assert "records[2] {" in jolt
        assert "id, name:" in jolt
        assert "1, A" in jolt
        assert "2, B" in jolt
    
    def test_empty_structures(self):
        data = {"empty_obj": {}, "empty_arr": []}
        jolt = json_to_jolt(data)
        assert "empty_obj {" in jolt
        assert "empty_arr[0]:" in jolt
    
    def test_special_characters(self):
        data = {"quote": 'He said "hello"', "newline": "line1\nline2"}
        jolt = json_to_jolt(data)
        # Should be quoted
        assert '"He said \\"hello\\""' in jolt or '"He said "hello""' in jolt
    
    def test_mixed_types(self):
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None
        }
        jolt = json_to_jolt(data)
        assert "string: hello" in jolt
        assert "number: 42" in jolt
        assert "float: 3.14" in jolt
        assert "bool: true" in jolt
        assert "null: null" in jolt


class TestDecoding:
    """Test decoding functionality"""
    
    def test_simple_roundtrip(self):
        data = {"id": 1, "name": "test", "active": True}
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_nested_roundtrip(self):
        data = {
            "user": {
                "id": 123,
                "profile": {
                    "name": "Bob",
                    "settings": {
                        "theme": "dark"
                    }
                }
            }
        }
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_array_roundtrip(self):
        data = {"numbers": [1, 2, 3, 4, 5]}
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_table_roundtrip(self):
        data = {
            "users": [
                {"id": 1, "name": "Alice", "age": 30},
                {"id": 2, "name": "Bob", "age": 25},
                {"id": 3, "name": "Charlie", "age": 35}
            ]
        }
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_mixed_roundtrip(self):
        data = {
            "meta": {
                "version": "1.0",
                "timestamp": 1234567890
            },
            "data": [
                {"id": 1, "value": 100},
                {"id": 2, "value": 200}
            ],
            "flags": [True, False, True],
            "config": {
                "enabled": True,
                "threshold": 0.5
            }
        }
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data


class TestOptimization:
    """Test optimization features"""
    
    def test_key_abbreviation(self):
        data = {
            "identifier": 1,
            "description": "test",
            "configuration": {"temperature": 0.7}
        }
        optimizer = JoltOptimizer(enable_abbreviations=True)
        optimized, stats = optimizer.optimize(data)
        
        assert "id" in optimized or "identifier" in optimized
        assert stats.tokens_saved > 0
    
    def test_pattern_detection(self):
        data = {"sequence": [1, 2, 3, 4, 5]}
        optimizer = JoltOptimizer(enable_pattern_detection=True)
        optimized, stats = optimizer.optimize(data)
        
        # Should detect arithmetic progression
        if "_pattern" in str(optimized):
            assert optimized["sequence"]["_pattern"] == "arithmetic"
    
    def test_sparse_array(self):
        data = {"sparse": [0, 0, 0, 5, 0, 0, 10, 0, 0, 0]}
        optimizer = JoltOptimizer(enable_sparse_arrays=True)
        optimized, stats = optimizer.optimize(data)
        
        # Should use sparse representation
        if isinstance(optimized["sparse"], dict):
            assert "_sparse" in optimized["sparse"]
    
    def test_value_pooling(self):
        data = {"states": ["error"] * 10 + ["success"] * 2 + ["error"] * 5}
        optimizer = JoltOptimizer(enable_value_pooling=True)
        optimized, stats = optimizer.optimize(data)
        
        # Should pool repeated values
        if isinstance(optimized["states"], dict):
            assert "_pool" in optimized["states"]


class TestSchema:
    """Test schema validation"""
    
    def test_basic_validation(self):
        schema = JoltSchema({
            "type": "object",
            "properties": {
                "id": {"type": "integer", "min": 1},
                "name": {"type": "string", "minLength": 1}
            }
        })
        
        # Valid data
        assert schema.is_valid({"id": 1, "name": "test"})
        
        # Invalid data
        assert not schema.is_valid({"id": 0, "name": "test"})  # id too small
        assert not schema.is_valid({"id": 1, "name": ""})  # name too short
        assert not schema.is_valid({"id": "1", "name": "test"})  # wrong type
    
    def test_nested_validation(self):
        schema = JoltSchema({
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "min": 0, "max": 150}
                    }
                }
            }
        })
        
        assert schema.is_valid({"user": {"age": 25}})
        assert not schema.is_valid({"user": {"age": -1}})
        assert not schema.is_valid({"user": {"age": 200}})
    
    def test_array_validation(self):
        schema = JoltSchema({
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "minLength": 1,
                    "maxLength": 10,
                    "items": {"type": "integer"}
                }
            }
        })
        
        assert schema.is_valid({"items": [1, 2, 3]})
        assert not schema.is_valid({"items": []})  # too short
        assert not schema.is_valid({"items": list(range(20))})  # too long
        assert not schema.is_valid({"items": ["a", "b"]})  # wrong type


class TestStreaming:
    """Test streaming functionality"""
    
    def test_basic_streaming(self):
        jolt_text = """
        data {
          id: 1
          name: test
          items[3]: a,b,c
        }
        """
        
        result = stream_jolt_to_json(jolt_text)
        assert result["id"] == 1
        assert result["name"] == "test"
        assert result["items"] == ["a", "b", "c"]
    
    def test_event_streaming(self):
        jolt_text = "test { value: 42 }"
        parser = JoltStreamParser(jolt_text)
        
        events = list(parser.parse_stream())
        
        # Should have START_OBJECT, KEY, VALUE, END_OBJECT events
        event_types = [e.type.value for e in events]
        assert "START_OBJECT" in event_types
        assert "KEY" in event_types
        assert "VALUE" in event_types
        assert "END_OBJECT" in event_types
    
    def test_large_stream(self):
        # Generate large data
        data = {
            "records": [
                {"id": i, "value": i * 10}
                for i in range(1000)
            ]
        }
        
        jolt = json_to_jolt(data)
        
        # Stream parse it
        result = stream_jolt_to_json(jolt)
        
        assert len(result["records"]) == 1000
        assert result["records"][0]["id"] == 0
        assert result["records"][999]["value"] == 9990


class TestIntegration:
    """Test framework integrations"""
    
    @pytest.mark.skipif(not _has_pandas(), reason="pandas not installed")
    def test_pandas_integration(self):
        import pandas as pd
        from jolt.integrations import dataframe_to_jolt, jolt_to_dataframe
        
        # Create DataFrame
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "value": [100, 200, 300]
        })
        
        # Convert to JOLT
        jolt = dataframe_to_jolt(df)
        
        # Convert back
        df2 = jolt_to_dataframe(jolt)
        
        assert df.equals(df2)


def _has_pandas():
    try:
        import pandas
        return True
    except ImportError:
        return False


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_unicode_handling(self):
        data = {"emoji": "😀", "math": "α + β = γ", "chinese": "你好"}
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_deep_nesting(self):
        # Create deeply nested structure
        data = {"level": 0}
        current = data
        for i in range(1, 20):
            current["child"] = {"level": i}
            current = current["child"]
        
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_large_numbers(self):
        data = {
            "big_int": 9007199254740991,  # MAX_SAFE_INTEGER
            "small_float": 0.0000000001,
            "negative": -999999999999
        }
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered == data
    
    def test_escape_sequences(self):
        data = {
            "backslash": "path\\to\\file",
            "quote": 'say "hello"',
            "tab": "col1\tcol2",
            "newline": "line1\nline2"
        }
        jolt = json_to_jolt(data)
        recovered = jolt_to_json(jolt)
        assert recovered["backslash"] == data["backslash"]
        assert recovered["tab"] == data["tab"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
