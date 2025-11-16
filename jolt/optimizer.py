"""
JOLT Optimizer - Advanced compression and optimization strategies
Like a data compression ninja - silent, efficient, and deadly to unnecessary tokens
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
import re


@dataclass
class OptimizationStats:
    """Statistics about optimization results"""
    original_size: int
    optimized_size: int
    tokens_saved: int
    compression_ratio: float
    optimizations_applied: Dict[str, int]
    
    def __str__(self) -> str:
        return (
            f"Optimization Results:\n"
            f"  Original: {self.original_size} chars\n"
            f"  Optimized: {self.optimized_size} chars\n"
            f"  Saved: {self.tokens_saved} tokens (~{self.compression_ratio:.1%} reduction)\n"
            f"  Techniques: {', '.join(f'{k}({v})' for k, v in self.optimizations_applied.items())}"
        )


class JoltOptimizer:
    """
    Advanced optimizer for JOLT format
    Applies multiple strategies to minimize token usage
    """
    
    def __init__(self,
                 enable_abbreviations: bool = True,
                 enable_type_inference: bool = True,
                 enable_pattern_detection: bool = True,
                 enable_value_pooling: bool = True,
                 enable_sparse_arrays: bool = True,
                 custom_abbreviations: Optional[Dict[str, str]] = None):
        """
        Initialize optimizer with strategies
        
        Args:
            enable_abbreviations: Use smart key abbreviations
            enable_type_inference: Optimize based on inferred types
            enable_pattern_detection: Detect and compress patterns
            enable_value_pooling: Pool repeated values
            enable_sparse_arrays: Optimize sparse arrays
            custom_abbreviations: User-defined abbreviations
        """
        self.enable_abbreviations = enable_abbreviations
        self.enable_type_inference = enable_type_inference
        self.enable_pattern_detection = enable_pattern_detection
        self.enable_value_pooling = enable_value_pooling
        self.enable_sparse_arrays = enable_sparse_arrays
        self.custom_abbreviations = custom_abbreviations or {}
        
        # Common abbreviations for frequent keys
        self.default_abbreviations = {
            'identifier': 'id',
            'description': 'desc',
            'configuration': 'config',
            'properties': 'props',
            'attributes': 'attrs',
            'parameters': 'params',
            'coordinates': 'coords',
            'timestamp': 'ts',
            'datetime': 'dt',
            'username': 'user',
            'password': 'pass',
            'telephone': 'tel',
            'address': 'addr',
            'message': 'msg',
            'response': 'resp',
            'request': 'req',
            'maximum': 'max',
            'minimum': 'min',
            'average': 'avg',
            'temperature': 'temp',
            'quantity': 'qty',
            'category': 'cat',
            'reference': 'ref',
            'document': 'doc',
            'customer': 'cust',
            'product': 'prod',
            'transaction': 'tx',
            'metadata': 'meta'
        }
        
        self.stats = defaultdict(int)
    
    def optimize(self, data: Any, context: Optional[str] = None) -> Tuple[Any, OptimizationStats]:
        """
        Optimize data for JOLT encoding
        
        Args:
            data: Input data to optimize
            context: Optional context hint for domain-specific optimization
            
        Returns:
            Tuple of (optimized_data, stats)
        """
        self.stats.clear()
        original_json = json.dumps(data, separators=(',', ':'))
        
        # Apply optimizations
        optimized = self._optimize_recursive(data, context)
        
        # Calculate stats
        optimized_json = json.dumps(optimized, separators=(',', ':'))
        
        # Rough token estimation (GPT-style tokenization)
        original_tokens = self._estimate_tokens(original_json)
        optimized_tokens = self._estimate_tokens(optimized_json)
        
        stats = OptimizationStats(
            original_size=len(original_json),
            optimized_size=len(optimized_json),
            tokens_saved=original_tokens - optimized_tokens,
            compression_ratio=1 - (optimized_tokens / original_tokens) if original_tokens > 0 else 0,
            optimizations_applied=dict(self.stats)
        )
        
        return optimized, stats
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple heuristic: ~4 chars per token for English text
        # More sophisticated: could use tiktoken or other tokenizer
        return len(text) // 4
    
    def _optimize_recursive(self, data: Any, context: Optional[str]) -> Any:
        """Recursively optimize data structure"""
        if isinstance(data, dict):
            return self._optimize_object(data, context)
        elif isinstance(data, list):
            return self._optimize_array(data, context)
        else:
            return self._optimize_scalar(data, context)
    
    def _optimize_object(self, obj: Dict[str, Any], context: Optional[str]) -> Dict[str, Any]:
        """Optimize object/dictionary"""
        optimized = {}
        
        # Abbreviate keys
        if self.enable_abbreviations:
            key_mapping = self._create_key_abbreviations(obj.keys())
            for key, value in obj.items():
                new_key = key_mapping.get(key, key)
                if new_key != key:
                    self.stats['key_abbreviations'] += 1
                optimized[new_key] = self._optimize_recursive(value, context)
        else:
            for key, value in obj.items():
                optimized[key] = self._optimize_recursive(value, context)
        
        # Detect and flatten single-child objects
        if len(optimized) == 1 and self.enable_pattern_detection:
            key, value = next(iter(optimized.items()))
            if isinstance(value, dict) and len(value) == 1:
                # Flatten: {"a": {"b": value}} -> {"a.b": value}
                nested_key, nested_value = next(iter(value.items()))
                flattened_key = f"{key}.{nested_key}"
                if len(flattened_key) < len(key) + len(nested_key) + 10:
                    self.stats['object_flattening'] += 1
                    return {flattened_key: nested_value}
        
        return optimized
    
    def _optimize_array(self, arr: List[Any], context: Optional[str]) -> Union[List[Any], Dict[str, Any]]:
        """Optimize array"""
        if not arr:
            return arr
        
        # Check for sparse arrays
        if self.enable_sparse_arrays:
            sparse_repr = self._try_sparse_representation(arr)
            if sparse_repr:
                self.stats['sparse_arrays'] += 1
                return sparse_repr
        
        # Check for patterns
        if self.enable_pattern_detection:
            pattern = self._detect_array_pattern(arr)
            if pattern:
                self.stats['pattern_compression'] += 1
                return pattern
        
        # Check for value pooling opportunity
        if self.enable_value_pooling and len(arr) > 5:
            pooled = self._try_value_pooling(arr)
            if pooled:
                self.stats['value_pooling'] += 1
                return pooled
        
        # Regular optimization
        return [self._optimize_recursive(item, context) for item in arr]
    
    def _optimize_scalar(self, value: Any, context: Optional[str]) -> Any:
        """Optimize scalar value"""
        if isinstance(value, str):
            # Remove unnecessary whitespace
            trimmed = value.strip()
            if trimmed != value:
                self.stats['whitespace_trimming'] += 1
                return trimmed
            
            # Detect and optimize ISO dates to compact format
            if self.enable_type_inference:
                compact_date = self._try_compact_date(value)
                if compact_date:
                    self.stats['date_compaction'] += 1
                    return compact_date
        
        elif isinstance(value, float):
            # Round floats to reasonable precision
            if self.enable_type_inference:
                rounded = round(value, 6)
                if rounded != value and abs(rounded - value) < 0.000001:
                    self.stats['float_rounding'] += 1
                    return rounded
        
        return value
    
    def _create_key_abbreviations(self, keys: Set[str]) -> Dict[str, str]:
        """Create abbreviation mapping for keys"""
        mapping = {}
        
        for key in keys:
            # Check custom abbreviations first
            if key in self.custom_abbreviations:
                mapping[key] = self.custom_abbreviations[key]
            # Check default abbreviations
            elif key.lower() in self.default_abbreviations:
                mapping[key] = self.default_abbreviations[key.lower()]
            # Create smart abbreviation for long keys
            elif len(key) > 8:
                abbrev = self._generate_abbreviation(key)
                if len(abbrev) < len(key) - 2:
                    mapping[key] = abbrev
                else:
                    mapping[key] = key
            else:
                mapping[key] = key
        
        # Ensure no collisions
        used = set()
        for key, abbrev in mapping.items():
            if abbrev in used:
                # Collision - use original
                mapping[key] = key
            else:
                used.add(abbrev)
        
        return mapping
    
    def _generate_abbreviation(self, key: str) -> str:
        """Generate smart abbreviation for a key"""
        # Handle camelCase and PascalCase
        if any(c.isupper() for c in key[1:]):
            # Extract capitals
            capitals = ''.join(c.lower() for c in key if c.isupper())
            if len(capitals) >= 2:
                return capitals
        
        # Handle snake_case
        if '_' in key:
            parts = key.split('_')
            abbrev = ''.join(p[0] for p in parts if p)
            return abbrev
        
        # Handle kebab-case
        if '-' in key:
            parts = key.split('-')
            abbrev = ''.join(p[0] for p in parts if p)
            return abbrev
        
        # Default: first 3 chars + last char
        if len(key) > 4:
            return key[:3] + key[-1]
        
        return key
    
    def _try_sparse_representation(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Try to represent sparse array more efficiently"""
        if len(arr) < 10:
            return None
        
        # Count non-null values
        non_null = [(i, v) for i, v in enumerate(arr) if v is not None and v != 0 and v != ""]
        
        # If less than 30% filled, use sparse representation
        if len(non_null) < len(arr) * 0.3:
            return {
                "_sparse": True,
                "_length": len(arr),
                "_values": {str(i): v for i, v in non_null}
            }
        
        return None
    
    def _detect_array_pattern(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Detect patterns in array (arithmetic/geometric progressions, etc.)"""
        if len(arr) < 5:
            return None
        
        # Check if all numbers
        if not all(isinstance(x, (int, float)) for x in arr):
            return None
        
        # Check for arithmetic progression
        diffs = [arr[i+1] - arr[i] for i in range(len(arr)-1)]
        if all(abs(d - diffs[0]) < 0.0001 for d in diffs):
            return {
                "_pattern": "arithmetic",
                "_start": arr[0],
                "_step": diffs[0],
                "_count": len(arr)
            }
        
        # Check for geometric progression
        if all(x != 0 for x in arr):
            ratios = [arr[i+1] / arr[i] for i in range(len(arr)-1)]
            if all(abs(r - ratios[0]) < 0.0001 for r in ratios):
                return {
                    "_pattern": "geometric",
                    "_start": arr[0],
                    "_ratio": ratios[0],
                    "_count": len(arr)
                }
        
        return None
    
    def _try_value_pooling(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Pool repeated values in array"""
        # Count value frequencies
        counter = Counter(str(v) for v in arr)
        
        # Find most common values
        common = counter.most_common(3)
        
        # If top values account for >60% of array, use pooling
        total_common = sum(count for _, count in common)
        if total_common > len(arr) * 0.6:
            pool = {str(v): i for i, (v, _) in enumerate(common)}
            pooled_arr = []
            
            for item in arr:
                str_item = str(item)
                if str_item in pool:
                    pooled_arr.append(f"${pool[str_item]}")
                else:
                    pooled_arr.append(item)
            
            return {
                "_pool": [eval(v) for v, _ in common],
                "_data": pooled_arr
            }
        
        return None
    
    def _try_compact_date(self, value: str) -> Optional[str]:
        """Try to compact ISO date strings"""
        # ISO date pattern
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?$'
        if re.match(iso_pattern, value):
            # Convert to compact format: YYYYMMDD.HHMMSS
            parts = value.replace('T', '.').replace(':', '').replace('-', '')
            parts = parts.split('.')[0] + '.' + parts.split('.')[1][:6]
            if len(parts) < len(value):
                return parts
        
        return None


class AdaptiveOptimizer:
    """
    Machine learning-inspired adaptive optimizer
    Learns from your data patterns to optimize better over time
    """
    
    def __init__(self):
        self.pattern_cache = {}
        self.key_frequency = Counter()
        self.value_patterns = defaultdict(list)
        self.optimization_success = defaultdict(int)
        self.optimization_attempts = defaultdict(int)
        
    def learn(self, data: Any) -> None:
        """Learn from data patterns"""
        self._analyze_recursive(data)
    
    def _analyze_recursive(self, data: Any, path: str = "") -> None:
        """Recursively analyze data structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                self.key_frequency[key] += 1
                self._analyze_recursive(value, f"{path}.{key}")
        elif isinstance(data, list):
            if data:
                # Sample first few items
                for item in data[:5]:
                    self._analyze_recursive(item, f"{path}[]")
        else:
            # Record value patterns
            self.value_patterns[path].append(data)
    
    def suggest_schema(self) -> Dict[str, Any]:
        """Suggest optimal schema based on learned patterns"""
        suggestions = {
            "frequent_keys": self.key_frequency.most_common(10),
            "recommended_abbreviations": {},
            "array_optimizations": {},
            "value_patterns": {}
        }
        
        # Suggest abbreviations for frequent long keys
        for key, count in self.key_frequency.items():
            if len(key) > 6 and count > 5:
                suggestions["recommended_abbreviations"][key] = self._suggest_abbreviation(key)
        
        # Analyze value patterns
        for path, values in self.value_patterns.items():
            if len(values) > 10:
                # Check for enums
                unique = set(values)
                if len(unique) < len(values) * 0.3:
                    suggestions["value_patterns"][path] = {
                        "type": "enum",
                        "values": list(unique)[:10]
                    }
        
        return suggestions
    
    def _suggest_abbreviation(self, key: str) -> str:
        """Suggest abbreviation based on key structure"""
        # Use consonants for abbreviation
        consonants = ''.join(c for c in key.lower() if c not in 'aeiou')
        if len(consonants) >= 3:
            return consonants[:4]
        return key[:3]
