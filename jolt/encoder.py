from __future__ import annotations
from typing import Any, Dict, List, Union


JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def json_to_jolt(
    obj: JsonType,
    *,
    root_name: str | None = None,
    indent: int = 2,
) -> str:
    """
    Convert a JSON-like object (Python dict/list) into JOLT format.

    v0.1 supports:
    - nested dicts
    - arrays of scalars
    - arrays of uniform dicts (table form)
    """

    lines: List[str] = []

    def write(line: str, level: int) -> None:
        lines.append(" " * (indent * level) + line)

    def encode_scalar(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)

        s = str(value)
        if s == "" or any(ch.isspace() for ch in s) or ":" in s or "," in s:
            return f'"{s}"'
        return s

    def is_uniform_dict_list(lst: List[Any]) -> bool:
        if not lst:
            return False
        if not all(isinstance(x, dict) for x in lst):
            return False
        first_keys = set(lst[0].keys())
        if not first_keys:
            return False
        return all(set(d.keys()) == first_keys for d in lst[1:])

    def encode_object(mapping: Dict[str, Any], level: int) -> None:
        for key, value in mapping.items():

            if isinstance(value, dict):
                write(f"{key} {{", level)
                encode_object(value, level + 1)
                write("}", level)

            elif isinstance(value, list):
                if not value:
                    write(f"{key}[0]:", level)
                    continue

                if is_uniform_dict_list(value):
                    n = len(value)
                    cols = list(value[0].keys())
                    cols_line = ", ".join(cols)
                    write(f"{key}[{n}] {{", level)
                    write(f"{cols_line}:", level + 1)
                    for row in value:
                        row_vals = ", ".join(encode_scalar(row[c]) for c in cols)
                        write(row_vals, level + 1)
                    write("}", level)

                else:
                    n = len(value)
                    rendered = ",".join(
                        encode_scalar(v) if not isinstance(v, dict) else encode_scalar(v)
                        for v in value
                    )
                    write(f"{key}[{n}]: {rendered}", level)

            else:
                scalar = encode_scalar(value)
                write(f"{key}: {scalar}", level)

    # Unwrap {"scenario": {...}} when root_name == "scenario"
    if isinstance(obj, dict) and root_name and list(obj.keys()) == [root_name]:
        obj = obj[root_name]

    if isinstance(obj, dict):
        if root_name:
            write(f"{root_name} {{", 0)
            encode_object(obj, 1)
            write("}", 0)
        else:
            encode_object(obj, 0)
    else:
        raise TypeError("json_to_jolt expects a dict at the root for v0.1.")

    return "\n".join(lines)
