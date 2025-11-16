"""
JOLT - JSON-Optimized Lightweight Tokens
A compact, LLM-native, human-readable structured data format
"""

__version__ = "0.2.0"
__author__ = "Doppler/Edward & AI Enhancement Team"

# Core functionality
from .encoder import json_to_jolt
from .decoder import jolt_to_json

# Streaming support
from .streaming import (
    JoltStreamParser,
    stream_jolt_to_json,
    filter_jolt_stream,
    StreamEvent,
    StreamEventType
)

# Schema validation
from .schema import (
    JoltSchema,
    SchemaNode,
    JoltType,
    ValidationError,
    create_schema_from_sample
)

# Optimization
from .optimizer import (
    JoltOptimizer,
    AdaptiveOptimizer,
    OptimizationStats
)

# Benchmarking
from .benchmark import (
    JoltBenchmark,
    BenchmarkResult,
    BenchmarkSuite,
    TokenCounter
)

# Framework integrations
from .integrations import (
    get_available_integrations,
    print_integration_status
)

# Conditional imports for optional integrations
try:
    from .integrations import setup_fastapi_jolt, JoltResponse, JoltRequest
except ImportError:
    pass

try:
    from .integrations import setup_flask_jolt
except ImportError:
    pass

try:
    from .integrations import JoltOutputParser, JoltPromptTemplate, JoltCallbackHandler
except ImportError:
    pass

try:
    from .integrations import dataframe_to_jolt, jolt_to_dataframe
except ImportError:
    pass

try:
    from .integrations import JoltType as SQLAlchemyJoltType
except ImportError:
    pass

try:
    from .integrations import JoltRedis
except ImportError:
    pass

__all__ = [
    # Core
    'json_to_jolt',
    'jolt_to_json',
    # Streaming
    'JoltStreamParser',
    'stream_jolt_to_json', 
    'filter_jolt_stream',
    'StreamEvent',
    'StreamEventType',
    # Schema
    'JoltSchema',
    'SchemaNode',
    'JoltType',
    'ValidationError',
    'create_schema_from_sample',
    # Optimization
    'JoltOptimizer',
    'AdaptiveOptimizer',
    'OptimizationStats',
    # Benchmarking
    'JoltBenchmark',
    'BenchmarkResult',
    'BenchmarkSuite',
    'TokenCounter',
    # Utilities
    'get_available_integrations',
    'print_integration_status'
]
