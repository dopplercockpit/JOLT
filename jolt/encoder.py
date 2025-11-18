"""
JOLT Encoder v0.3 - Enhanced JSON to JOLT conversion
Now with 20% more clarity and 100% fewer confusing edge cases!
"""
from __future__ import annotations
from typing import Any, Dict, List, Union, Set


JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def json_to_jolt(
    obj: JsonType,
    *,
    root_name: str | None = None,
    indent: int = 2,
    _level: int = 0,
) -> str:
    """
    Convert a JSON-like object (Python dict/list) into JOLT format.

    v0.3 improvements:
    - Better handling of nested structures
    - Consistent quote escaping
    - Cleaner indentation logic
    - Support for mixed array types

    Args:
        obj: The data to encode (dict, list, or scalar)
        root_name: Optional name for root object block
        indent: Spaces per indentation level
        _level: Internal recursion depth tracker

    Returns:
        JOLT formatted string

    Example:
        >>> data = {"user": {"id": 1, "name": "Alice"}}
        >>> print(json_to_jolt(data))
        user {
          id: 1
          name: Alice
        }
    """
    lines: List[str] = []

    def write(line: str, level: int) -> None:
        """Write a line with proper indentation"""
        lines.append(" " * (indent * level) + line)

    def encode_scalar(value: Any) -> str:
        """
        Encode a scalar value with minimal quoting.
        
        Think of this like packing for a trip - only bring quotes if you absolutely need them!
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            # Handle special float values
            if isinstance(value, float):
                if value != value:  # NaN
                    return "null"
                if value == float('inf'):
                    return "null"
                if value == float('-inf'):
                    return "null"
                # Avoid scientific notation for small numbers
                if abs(value) < 0.0001 and value != 0:
                    # Format with enough precision
                    return f"{value:.15f}".rstrip('0').rstrip('.')
            return str(value)

        # String handling
        s = str(value)
        
        # Empty strings always need quotes
        if s == "":
            return '""'
        
        # Check if we need quotes
        needs_quotes = (
            any(ch.isspace() for ch in s) or  # Contains whitespace
            ":" in s or "," in s or  # Contains delimiters
            "{" in s or "}" in s or  # Contains structure chars
            "[" in s or "]" in s or
            s in ("null", "true", "false") or  # Reserved words
            s[0].isdigit() or s[0] == "-"  # Looks like a number
        )
        
        if needs_quotes:
            # Escape special characters properly
            escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
            return f'"{escaped}"'
        
        return s

    def is_uniform_dict_list(lst: List[Any]) -> bool:
        """
        Check if a list is suitable for table format.
        
        Like checking if all your LEGO pieces are the same shape - makes building easier!
        """
        if not lst:
            return False
        if not all(isinstance(x, dict) for x in lst):
            return False
        if not lst[0]:  # Empty dict
            return False
        
        first_keys = set(lst[0].keys())
        return all(set(d.keys()) == first_keys for d in lst[1:])

    def encode_object(mapping: Dict[str, Any], level: int) -> None:
        """Encode a dictionary as JOLT object"""
        for key, value in mapping.items():
            if isinstance(value, dict):
                # Nested object
                write(f"{key} {{", level)
                encode_object(value, level + 1)
                write("}", level)

            elif isinstance(value, list):
                encode_array(key, value, level)

            else:
                # Scalar value
                scalar = encode_scalar(value)
                write(f"{key}: {scalar}", level)

    def encode_array(key: str, arr: List[Any], level: int) -> None:
        """Encode an array with appropriate format"""
        if not arr:
            write(f"{key}[0]:", level)
            return

        # Check for table format (uniform dict list)
        if is_uniform_dict_list(arr):
            n = len(arr)
            cols = list(arr[0].keys())
            cols_line = ", ".join(cols)
            write(f"{key}[{n}] {{", level)
            write(f"{cols_line}:", level + 1)
            for row in arr:
                row_vals = ", ".join(encode_scalar(row[c]) for c in cols)
                write(row_vals, level + 1)
            write("}", level)
        else:
            # Regular array - inline format
            n = len(arr)
            # Check if all elements are scalars
            if all(not isinstance(v, (dict, list)) for v in arr):
                rendered = ",".join(encode_scalar(v) for v in arr)
                write(f"{key}[{n}]: {rendered}", level)
            else:
                # Mixed or complex array - use multi-line format
                write(f"{key}[{n}]:", level)
                for item in arr:
                    if isinstance(item, dict):
                        write("{", level + 1)
                        encode_object(item, level + 2)
                        write("}", level + 1)
                    elif isinstance(item, list):
                        # Nested array - encode inline if possible
                        if all(not isinstance(v, (dict, list)) for v in item):
                            rendered = "[" + ",".join(encode_scalar(v) for v in item) + "]"
                            write(rendered, level + 1)
                        else:
                            write("[...]", level + 1)  # Deep nesting fallback
                    else:
                        write(encode_scalar(item), level + 1)

    # Main encoding logic
    # Handle root wrapping/unwrapping
    if isinstance(obj, dict) and root_name:
        # Check if we need to unwrap
        if list(obj.keys()) == [root_name]:
            obj = obj[root_name]
        
        # Write as named root
        write(f"{root_name} {{", _level)
        if isinstance(obj, dict):
            encode_object(obj, _level + 1)
        write("}", _level)
    elif isinstance(obj, dict):
        # Braceless root object
        encode_object(obj, _level)
    elif isinstance(obj, list):
        # Root-level array (uncommon but supported)
        if is_uniform_dict_list(obj):
            n = len(obj)
            cols = list(obj[0].keys()) if obj else []
            cols_line = ", ".join(cols)
            write(f"[{n}] {{", _level)
            if cols:
                write(f"{cols_line}:", _level + 1)
                for row in obj:
                    row_vals = ", ".join(encode_scalar(row[c]) for c in cols)
                    write(row_vals, _level + 1)
            write("}", _level)
        else:
            # Simple array at root
            write(f"[{len(obj)}]:", _level)
            for item in obj:
                write(encode_scalar(item), _level + 1)
    else:
        # Root-level scalar (edge case)
        lines.append(encode_scalar(obj))

    return "\n".join(lines)