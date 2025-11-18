"""
JOLT Optimizer v0.3 - Decoder-aware compression strategies
Like Marie Kondo for your data - sparking joy through minimalism!
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from collections import Counter, defaultdict
from dataclasses import dataclass, field
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
    optimizations_applied: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        parts = [
            f"Optimization Results:",
            f"  Original: {self.original_size} chars",
            f"  Optimized: {self.optimized_size} chars",
            f"  Saved: {self.tokens_saved} tokens (~{self.compression_ratio:.1%} reduction)",
        ]
        
        if self.optimizations_applied:
            techniques = ', '.join(f'{k}({v})' for k, v in self.optimizations_applied.items())
            parts.append(f"  Techniques: {techniques}")
        
        if self.warnings:
            parts.append(f"  Warnings: {len(self.warnings)}")
            for warning in self.warnings[:3]:
                parts.append(f"    - {warning}")
        
        return "\n".join(parts)


class JoltOptimizer:
    """
    Advanced optimizer for JOLT format v0.3
    
    Now with 100% more decoder-awareness!  No more creating structures
    that look great but can't be decoded.  It's like making a sandwich
    that not only looks delicious but is actually edible!
    """
    
    def __init__(self,
                 enable_abbreviations: bool = True,
                 enable_type_inference: bool = True,
                 enable_pattern_detection: bool = False,  # DISABLED by default in v0.3
                 enable_value_pooling: bool = False,      # DISABLED by default in v0.3
                 enable_sparse_arrays: bool = False,      # DISABLED by default in v0.3
                 custom_abbreviations: Optional[Dict[str, str]] = None,
                 safe_mode: bool = True):  # NEW in v0.3
        """
        Initialize optimizer with strategies
        
        Args:
            enable_abbreviations: Use smart key abbreviations
            enable_type_inference: Optimize based on inferred types
            enable_pattern_detection: Detect and compress patterns (EXPERIMENTAL)
            enable_value_pooling: Pool repeated values (EXPERIMENTAL)
            enable_sparse_arrays: Optimize sparse arrays (EXPERIMENTAL)
            custom_abbreviations: User-defined abbreviations
            safe_mode: Only apply decoder-compatible optimizations
        """
        self.enable_abbreviations = enable_abbreviations
        self.enable_type_inference = enable_type_inference
        self.enable_pattern_detection = enable_pattern_detection
        self.enable_value_pooling = enable_value_pooling
        self.enable_sparse_arrays = enable_sparse_arrays
        self.custom_abbreviations = custom_abbreviations or {}
        self.safe_mode = safe_mode
        
        # Common abbreviations (conservative for v0.3)
        self.default_abbreviations = {
            'identifier': 'id',
            'description': 'desc',
            'configuration': 'config',
            'properties': 'props',
            'attributes': 'attrs',
            'parameters': 'params',
            'timestamp': 'ts',
            'datetime': 'dt',
            'username': 'user',
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
            'reference': 'ref',
            'document': 'doc',
        }
        
        self.stats = defaultdict(int)
        self.warnings = []
    
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
        self.warnings.clear()
        
        original_json = json.dumps(data, separators=(',', ':'))
        
        # Apply optimizations
        optimized = self._optimize_recursive(data, context)
        
        # Calculate stats
        optimized_json = json.dumps(optimized, separators=(',', ':'))
        
        # Rough token estimation
        original_tokens = self._estimate_tokens(original_json)
        optimized_tokens = self._estimate_tokens(optimized_json)
        
        stats = OptimizationStats(
            original_size=len(original_json),
            optimized_size=len(optimized_json),
            tokens_saved=original_tokens - optimized_tokens,
            compression_ratio=1 - (optimized_tokens / original_tokens) if original_tokens > 0 else 0,
            optimizations_applied=dict(self.stats),
            warnings=self.warnings.copy()
        )
        
        return optimized, stats
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Like counting calories - not perfect, but good enough for planning!
        """
        # Simple heuristic: ~4 chars per token for English text
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
        
        # Abbreviate keys (safe operation)
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
        
        return optimized
    
    def _optimize_array(self, arr: List[Any], context: Optional[str]) -> Union[List[Any], Dict[str, Any]]:
        """Optimize array"""
        if not arr:
            return arr
        
        # NOTE: Pattern detection, value pooling, and sparse arrays are DISABLED
        # in safe_mode by default in v0.3 because they create non-standard structures
        # that may not round-trip correctly through the decoder
        
        if not self.safe_mode:
            # Only apply experimental optimizations if explicitly enabled
            if self.enable_sparse_arrays:
                sparse_repr = self._try_sparse_representation(arr)
                if sparse_repr:
                    self.stats['sparse_arrays'] += 1
                    self.warnings.append("Sparse array optimization may not decode correctly")
                    return sparse_repr
            
            if self.enable_pattern_detection:
                pattern = self._detect_array_pattern(arr)
                if pattern:
                    self.stats['pattern_compression'] += 1
                    self.warnings.append("Pattern compression may not decode correctly")
                    return pattern
            
            if self.enable_value_pooling and len(arr) > 5:
                pooled = self._try_value_pooling(arr)
                if pooled:
                    self.stats['value_pooling'] += 1
                    self.warnings.append("Value pooling may not decode correctly")
                    return pooled
        
        # Regular optimization (always safe)
        return [self._optimize_recursive(item, context) for item in arr]
    
    def _optimize_scalar(self, value: Any, context: Optional[str]) -> Any:
        """Optimize scalar value"""
        if isinstance(value, str):
            # Remove unnecessary whitespace (safe)
            trimmed = value.strip()
            if trimmed != value and value.startswith(' ') or value.endswith(' '):
                # Only trim if there's leading/trailing whitespace
                self.stats['whitespace_trimming'] += 1
                return trimmed
        
        elif isinstance(value, float):
            # Round floats to reasonable precision (safe if tolerance is small)
            if self.enable_type_inference:
                # Be conservative - only round very small differences
                rounded = round(value, 10)
                if rounded != value and abs(rounded - value) < 1e-10:
                    self.stats['float_rounding'] += 1
                    return rounded
        
        return value
    
    def _create_key_abbreviations(self, keys: Set[str]) -> Dict[str, str]:
        """
        Create abbreviation mapping for keys
        
        Like creating nicknames - but only the ones that make sense!
        """
        mapping = {}
        
        for key in keys:
            # Check custom abbreviations first
            if key in self.custom_abbreviations:
                mapping[key] = self.custom_abbreviations[key]
            # Check default abbreviations
            elif key.lower() in self.default_abbreviations:
                mapping[key] = self.default_abbreviations[key.lower()]
            # Only abbreviate if there's significant savings
            elif len(key) > 10:
                abbrev = self._generate_abbreviation(key)
                # Only use if it saves at least 3 characters
                if len(abbrev) <= len(key) - 3:
                    mapping[key] = abbrev
                else:
                    mapping[key] = key
            else:
                mapping[key] = key
        
        # Ensure no collisions
        used = set()
        for key in list(mapping.keys()):
            abbrev = mapping[key]
            if abbrev in used and abbrev != key:
                # Collision - use original key
                mapping[key] = key
                self.warnings.append(f"Abbreviation collision for '{key}', using original")
            else:
                used.add(abbrev)
        
        return mapping
    
    def _generate_abbreviation(self, key: str) -> str:
        """Generate smart abbreviation for a key"""
        # Handle camelCase and PascalCase
        if any(c.isupper() for c in key[1:]):
            capitals = ''.join(c.lower() for c in key if c.isupper())
            if len(capitals) >= 2:
                return capitals
        
        # Handle snake_case
        if '_' in key:
            parts = key.split('_')
            abbrev = ''.join(p[0] for p in parts if p)
            if len(abbrev) >= 2:
                return abbrev
        
        # Handle kebab-case
        if '-' in key:
            parts = key.split('-')
            abbrev = ''.join(p[0] for p in parts if p)
            if len(abbrev) >= 2:
                return abbrev
        
        # Default: first few chars
        if len(key) > 5:
            return key[:4]
        
        return key
    
    # EXPERIMENTAL METHODS (disabled by default in v0.3)
    
    def _try_sparse_representation(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Try to represent sparse array more efficiently (EXPERIMENTAL)"""
        if len(arr) < 10:
            return None
        
        # Count non-null/non-zero values
        non_empty = [(i, v) for i, v in enumerate(arr) 
                     if v is not None and v != 0 and v != "" and v != False]
        
        # If less than 20% filled, use sparse representation
        if len(non_empty) < len(arr) * 0.2:
            return {
                "_sparse": True,
                "_length": len(arr),
                "_values": {str(i): v for i, v in non_empty}
            }
        
        return None
    
    def _detect_array_pattern(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Detect patterns in array (EXPERIMENTAL)"""
        if len(arr) < 4:
            return None
        
        # Only work with numbers
        if not all(isinstance(x, (int, float)) for x in arr):
            return None
        
        # Check for arithmetic progression
        diffs = [arr[i+1] - arr[i] for i in range(len(arr)-1)]
        if all(abs(d - diffs[0]) < 0.001 for d in diffs):
            return {
                "_pattern": "arithmetic",
                "_start": arr[0],
                "_step": diffs[0],
                "_count": len(arr)
            }
        
        # Check for geometric progression
        if all(x != 0 for x in arr):
            ratios = [arr[i+1] / arr[i] for i in range(len(arr)-1)]
            if all(abs(r - ratios[0]) < 0.001 for r in ratios):
                return {
                    "_pattern": "geometric",
                    "_start": arr[0],
                    "_ratio": ratios[0],
                    "_count": len(arr)
                }
        
        return None
    
    def _try_value_pooling(self, arr: List[Any]) -> Optional[Dict[str, Any]]:
        """Pool repeated values in array (EXPERIMENTAL)"""
        try:
            counter = Counter(arr)
        except TypeError:
            return None
        
        # Find most common values
        common = counter.most_common(5)
        
        # Only pool if top values account for >70% of array
        total_common = sum(count for _, count in common)
        if total_common <= len(arr) * 0.7:
            return None
        
        # Create pool
        pool = [v for v, _ in common]
        pool_index = {v: i for i, v in enumerate(pool)}
        
        # Create pooled array
        pooled_arr = []
        for item in arr:
            if item in pool_index:
                pooled_arr.append(f"${pool_index[item]}")
            else:
                pooled_arr.append(item)
        
        return {
            "_pool": pool,
            "_data": pooled_arr
        }