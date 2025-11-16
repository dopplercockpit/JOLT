"""
JOLT Benchmarking Suite - Comprehensive performance analysis
Because if you can't measure it, you can't optimize it
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import time
import zlib
import base64
import statistics
from pathlib import Path
from enum import Enum

# Optional imports for token counting
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


class TokenCounter:
    """
    Advanced token counting with multiple encoding strategies
    """
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.encoder = None
        
        if HAS_TIKTOKEN:
            try:
                # Try to get the encoding for the specified model
                self.encoder = tiktoken.encoding_for_model(model)
            except:
                # Fall back to cl100k_base (GPT-4 default)
                self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: rough estimation
            # Average ~4 characters per token for English text
            return len(text) // 4
    
    def count_json_tokens(self, data: Any) -> int:
        """Count tokens in JSON representation"""
        json_str = json.dumps(data, separators=(',', ':'))
        return self.count_tokens(json_str)
    
    def count_jolt_tokens(self, data: Any, encoder_func: Callable) -> int:
        """Count tokens in JOLT representation"""
        jolt_str = encoder_func(data)
        return self.count_tokens(jolt_str)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    name: str
    format: str
    size_bytes: int
    token_count: int
    encode_time_ms: float
    decode_time_ms: float
    compression_ratio: float  # vs JSON
    token_reduction: float  # vs JSON
    correctness: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results"""
    timestamp: datetime
    results: List[BenchmarkResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        lines = [
            f"# JOLT Benchmark Report",
            f"Generated: {self.timestamp.isoformat()}",
            "",
            "## Summary",
            f"- Tests run: {len(self.results)}",
            f"- Average token reduction: {self.summary.get('avg_token_reduction', 0):.1%}",
            f"- Average size reduction: {self.summary.get('avg_size_reduction', 0):.1%}",
            f"- Average encode speed: {self.summary.get('avg_encode_ms', 0):.2f}ms",
            f"- Average decode speed: {self.summary.get('avg_decode_ms', 0):.2f}ms",
            "",
            "## Detailed Results",
            "",
            "| Test | Format | Size (B) | Tokens | Encode (ms) | Decode (ms) | Token Reduction | Correct |",
            "|------|--------|----------|--------|-------------|-------------|-----------------|---------|"
        ]
        
        for result in self.results:
            lines.append(
                f"| {result.name} | {result.format} | {result.size_bytes} | "
                f"{result.token_count} | {result.encode_time_ms:.2f} | "
                f"{result.decode_time_ms:.2f} | {result.token_reduction:.1%} | "
                f"{'✓' if result.correctness else '✗'} |"
            )
        
        return "\n".join(lines)


class JoltBenchmark:
    """
    Comprehensive benchmarking framework for JOLT
    """
    
    def __init__(self,
                 jolt_encoder: Callable,
                 jolt_decoder: Callable,
                 token_model: str = "gpt-4"):
        """
        Initialize benchmark framework
        
        Args:
            jolt_encoder: Function to encode JSON to JOLT
            jolt_decoder: Function to decode JOLT to JSON
            token_model: Model for token counting
        """
        self.jolt_encoder = jolt_encoder
        self.jolt_decoder = jolt_decoder
        self.token_counter = TokenCounter(token_model)
        self.test_suites = {}
        self._load_default_tests()
    
    def _load_default_tests(self):
        """Load default test cases"""
        self.test_suites['basic'] = [
            {
                "name": "simple_object",
                "data": {"id": 1, "name": "test", "active": True}
            },
            {
                "name": "nested_object",
                "data": {
                    "user": {
                        "id": 123,
                        "profile": {
                            "name": "Alice",
                            "age": 30
                        }
                    }
                }
            },
            {
                "name": "array_simple",
                "data": {"items": [1, 2, 3, 4, 5]}
            },
            {
                "name": "table_format",
                "data": {
                    "records": [
                        {"id": 1, "name": "A", "value": 100},
                        {"id": 2, "name": "B", "value": 200},
                        {"id": 3, "name": "C", "value": 300}
                    ]
                }
            }
        ]
        
        self.test_suites['complex'] = [
            {
                "name": "deep_nesting",
                "data": self._generate_deep_nesting(5)
            },
            {
                "name": "wide_object",
                "data": {f"field_{i}": i for i in range(50)}
            },
            {
                "name": "large_table",
                "data": {
                    "data": [
                        {"id": i, "value": i*10, "name": f"item_{i}"}
                        for i in range(100)
                    ]
                }
            },
            {
                "name": "mixed_types",
                "data": {
                    "string": "hello",
                    "number": 42,
                    "float": 3.14,
                    "bool": True,
                    "null": None,
                    "array": [1, "two", 3.0, True, None],
                    "object": {"nested": "value"}
                }
            }
        ]
        
        self.test_suites['edge_cases'] = [
            {
                "name": "empty_structures",
                "data": {"empty_obj": {}, "empty_arr": []}
            },
            {
                "name": "special_characters",
                "data": {
                    "quotes": 'He said "hello"',
                    "newlines": "line1\nline2",
                    "unicode": "emoji: 😀 symbols: α β γ"
                }
            },
            {
                "name": "long_strings",
                "data": {
                    "description": "Lorem ipsum " * 50
                }
            }
        ]
    
    def _generate_deep_nesting(self, depth: int) -> Dict:
        """Generate deeply nested structure"""
        if depth == 0:
            return {"value": "leaf"}
        return {"level": depth, "child": self._generate_deep_nesting(depth - 1)}
    
    def benchmark_single(self, 
                        test_data: Any, 
                        test_name: str = "unnamed",
                        iterations: int = 10) -> BenchmarkResult:
        """
        Benchmark a single test case
        
        Args:
            test_data: Data to benchmark
            test_name: Name of test
            iterations: Number of iterations for timing
            
        Returns:
            BenchmarkResult
        """
        # JSON baseline
        json_str = json.dumps(test_data, separators=(',', ':'))
        json_size = len(json_str.encode('utf-8'))
        json_tokens = self.token_counter.count_tokens(json_str)
        
        # JSON timing
        json_encode_times = []
        json_decode_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            encoded = json.dumps(test_data)
            json_encode_times.append((time.perf_counter() - start) * 1000)
            
            start = time.perf_counter()
            decoded = json.loads(encoded)
            json_decode_times.append((time.perf_counter() - start) * 1000)
        
        # JOLT benchmark
        jolt_encode_times = []
        jolt_decode_times = []
        jolt_str = None
        correctness = True
        
        for _ in range(iterations):
            try:
                start = time.perf_counter()
                jolt_str = self.jolt_encoder(test_data)
                jolt_encode_times.append((time.perf_counter() - start) * 1000)
                
                start = time.perf_counter()
                decoded = self.jolt_decoder(jolt_str)
                jolt_decode_times.append((time.perf_counter() - start) * 1000)
                
                # Verify correctness (only once)
                if correctness and decoded != test_data:
                    # Try normalizing both for comparison
                    if json.dumps(decoded, sort_keys=True) != json.dumps(test_data, sort_keys=True):
                        correctness = False
            except Exception as e:
                correctness = False
                jolt_encode_times.append(0)
                jolt_decode_times.append(0)
        
        # Calculate JOLT metrics
        jolt_size = len(jolt_str.encode('utf-8')) if jolt_str else 0
        jolt_tokens = self.token_counter.count_tokens(jolt_str) if jolt_str else 0
        
        return BenchmarkResult(
            name=test_name,
            format="JOLT",
            size_bytes=jolt_size,
            token_count=jolt_tokens,
            encode_time_ms=statistics.mean(jolt_encode_times) if jolt_encode_times else 0,
            decode_time_ms=statistics.mean(jolt_decode_times) if jolt_decode_times else 0,
            compression_ratio=jolt_size / json_size if json_size > 0 else 1,
            token_reduction=1 - (jolt_tokens / json_tokens) if json_tokens > 0 else 0,
            correctness=correctness,
            metadata={
                "json_size": json_size,
                "json_tokens": json_tokens,
                "json_encode_ms": statistics.mean(json_encode_times),
                "json_decode_ms": statistics.mean(json_decode_times)
            }
        )
    
    def benchmark_suite(self, 
                       suite_name: str = "basic",
                       iterations: int = 10) -> BenchmarkSuite:
        """
        Run a complete benchmark suite
        
        Args:
            suite_name: Name of test suite to run
            iterations: Number of iterations per test
            
        Returns:
            BenchmarkSuite with results
        """
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown suite: {suite_name}")
        
        results = []
        for test in self.test_suites[suite_name]:
            result = self.benchmark_single(
                test['data'],
                test['name'],
                iterations
            )
            results.append(result)
        
        # Calculate summary statistics
        summary = {
            "suite_name": suite_name,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.correctness),
            "avg_token_reduction": statistics.mean(r.token_reduction for r in results),
            "avg_size_reduction": statistics.mean(1 - r.compression_ratio for r in results),
            "avg_encode_ms": statistics.mean(r.encode_time_ms for r in results),
            "avg_decode_ms": statistics.mean(r.decode_time_ms for r in results),
            "max_token_reduction": max(r.token_reduction for r in results),
            "min_token_reduction": min(r.token_reduction for r in results)
        }
        
        return BenchmarkSuite(
            timestamp=datetime.now(),
            results=results,
            summary=summary
        )
    
    def benchmark_all(self, iterations: int = 10) -> Dict[str, BenchmarkSuite]:
        """Run all benchmark suites"""
        all_results = {}
        for suite_name in self.test_suites:
            all_results[suite_name] = self.benchmark_suite(suite_name, iterations)
        return all_results
    
    def compare_formats(self, 
                       test_data: Any,
                       formats: Dict[str, Tuple[Callable, Callable]]) -> List[BenchmarkResult]:
        """
        Compare multiple formats
        
        Args:
            test_data: Data to test
            formats: Dict of format_name -> (encoder, decoder) tuples
            
        Returns:
            List of BenchmarkResult for each format
        """
        results = []
        
        # Get JSON baseline
        json_str = json.dumps(test_data, separators=(',', ':'))
        json_size = len(json_str.encode('utf-8'))
        json_tokens = self.token_counter.count_tokens(json_str)
        
        for format_name, (encoder, decoder) in formats.items():
            try:
                # Encode
                start = time.perf_counter()
                encoded = encoder(test_data)
                encode_time = (time.perf_counter() - start) * 1000
                
                # Decode
                start = time.perf_counter()
                decoded = decoder(encoded)
                decode_time = (time.perf_counter() - start) * 1000
                
                # Metrics
                size = len(encoded.encode('utf-8')) if isinstance(encoded, str) else len(encoded)
                tokens = self.token_counter.count_tokens(str(encoded))
                
                # Verify correctness
                correctness = json.dumps(decoded, sort_keys=True) == json.dumps(test_data, sort_keys=True)
                
                results.append(BenchmarkResult(
                    name=f"compare_{format_name}",
                    format=format_name,
                    size_bytes=size,
                    token_count=tokens,
                    encode_time_ms=encode_time,
                    decode_time_ms=decode_time,
                    compression_ratio=size / json_size,
                    token_reduction=1 - (tokens / json_tokens),
                    correctness=correctness
                ))
            except Exception as e:
                results.append(BenchmarkResult(
                    name=f"compare_{format_name}",
                    format=format_name,
                    size_bytes=0,
                    token_count=0,
                    encode_time_ms=0,
                    decode_time_ms=0,
                    compression_ratio=1,
                    token_reduction=0,
                    correctness=False,
                    metadata={"error": str(e)}
                ))
        
        return results
    
    def profile_token_distribution(self, test_data: Any) -> Dict[str, Any]:
        """
        Analyze token distribution in different representations
        """
        json_str = json.dumps(test_data, separators=(',', ':'))
        jolt_str = self.jolt_encoder(test_data)
        
        # Character frequency analysis
        json_chars = {}
        for char in json_str:
            json_chars[char] = json_chars.get(char, 0) + 1
        
        jolt_chars = {}
        for char in jolt_str:
            jolt_chars[char] = jolt_chars.get(char, 0) + 1
        
        # Structural overhead
        json_structural = sum(json_chars.get(c, 0) for c in '{}[],"":')
        jolt_structural = sum(jolt_chars.get(c, 0) for c in '{}[],:')
        
        return {
            "json": {
                "total_chars": len(json_str),
                "structural_chars": json_structural,
                "structural_ratio": json_structural / len(json_str) if json_str else 0,
                "tokens": self.token_counter.count_tokens(json_str)
            },
            "jolt": {
                "total_chars": len(jolt_str),
                "structural_chars": jolt_structural,
                "structural_ratio": jolt_structural / len(jolt_str) if jolt_str else 0,
                "tokens": self.token_counter.count_tokens(jolt_str)
            },
            "improvement": {
                "char_reduction": 1 - (len(jolt_str) / len(json_str)) if json_str else 0,
                "structural_reduction": 1 - (jolt_structural / json_structural) if json_structural else 0,
                "token_reduction": 1 - (self.token_counter.count_tokens(jolt_str) / 
                                      self.token_counter.count_tokens(json_str)) if json_str else 0
            }
        }
