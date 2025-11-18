"""
JOLT v0.3 - JSON-Optimized Lightweight Tokens
A compact, human-readable, LLM-native structured data format

What's New in v0.3:
- 🛡️ Robust error handling with helpful messages
- 🎯 Decoder-aware optimizations (no more non-decodable structures!)
- 🧪 Comprehensive test coverage
- 📚 Improved documentation
- 🐛 Fixed: braceless root objects, nested named blocks, edge cases
- ⚡ Better performance and memory efficiency

Example Usage:
    >>> from jolt import json_to_jolt, jolt_to_json
    >>> 
    >>> data = {"user": {"id": 1, "name": "Alice", "scores": [95, 87, 92]}}
    >>> jolt = json_to_jolt(data)
    >>> print(jolt)
    user {
      id: 1
      name: Alice
      scores[3]: 95,87,92
    }
    >>> 
    >>> recovered = jolt_to_json(jolt)
    >>> assert data == recovered  # Perfect round-trip!
"""

__version__ = "0.3.0"
__author__ = "doppler/edward & AI Enhancement Team"

# Core functionality
from .encoder import json_to_jolt
from .decoder import jolt_to_json, JoltSyntaxError

# Optimization
from .optimizer import (
    JoltOptimizer,
    OptimizationStats
)

# Schema validation (if we keep it)
try:
    from .schema import (
        JoltSchema,
        SchemaNode,
        JoltType,
        ValidationError,
        create_schema_from_sample
    )
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False

# Streaming support (if we keep it)
try:
    from .streaming import (
        JoltStreamParser,
        stream_jolt_to_json,
        filter_jolt_stream,
        StreamEvent,
        StreamEventType
    )
    HAS_STREAMING = True
except ImportError:
    HAS_STREAMING = False

# Benchmarking (if we keep it)
try:
    from .benchmark import (
        JoltBenchmark,
        BenchmarkResult,
        BenchmarkSuite,
        TokenCounter
    )
    HAS_BENCHMARK = True
except ImportError:
    HAS_BENCHMARK = False

__all__ = [
    # Core
    'json_to_jolt',
    'jolt_to_json',
    'JoltSyntaxError',
    # Optimization
    'JoltOptimizer',
    'OptimizationStats',
    # Version
    '__version__',
]

# Add optional exports if available
if HAS_SCHEMA:
    __all__.extend([
        'JoltSchema',
        'SchemaNode',
        'JoltType',
        'ValidationError',
        'create_schema_from_sample',
    ])

if HAS_STREAMING:
    __all__.extend([
        'JoltStreamParser',
        'stream_jolt_to_json',
        'filter_jolt_stream',
        'StreamEvent',
        'StreamEventType',
    ])

if HAS_BENCHMARK:
    __all__.extend([
        'JoltBenchmark',
        'BenchmarkResult',
        'BenchmarkSuite',
        'TokenCounter',
    ])


def get_version() -> str:
    """Get JOLT version string"""
    return __version__


def quick_test() -> bool:
    """
    Quick sanity test for JOLT functionality
    
    Returns:
        True if all tests pass
        
    Example:
        >>> from jolt import quick_test
        >>> quick_test()
        ✓ Basic encoding/decoding
        ✓ Nested structures
        ✓ Arrays and tables
        ✓ Special characters
        True
    """
    test_cases = [
        # Basic
        ({"id": 1, "name": "test"}, "Basic encoding/decoding"),
        # Nested
        ({"user": {"profile": {"name": "Alice"}}}, "Nested structures"),
        # Arrays
        ({"items": [1, 2, 3], "users": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]}, "Arrays and tables"),
        # Special chars
        ({"quote": 'He said "hello"', "newline": "line1\nline2"}, "Special characters"),
    ]
    
    all_passed = True
    for data, description in test_cases:
        try:
            jolt = json_to_jolt(data)
            recovered = jolt_to_json(jolt)
            
            # Deep equality check
            import json
            if json.dumps(data, sort_keys=True) == json.dumps(recovered, sort_keys=True):
                print(f"✓ {description}")
            else:
                print(f"✗ {description}: Data mismatch")
                all_passed = False
        except Exception as e:
            print(f"✗ {description}: {e}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    # Run quick test when module is executed
    print(f"JOLT v{__version__} - Quick Test")
    print("=" * 40)
    success = quick_test()
    print("=" * 40)
    if success:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed ❌")
    exit(0 if success else 1)