"""
JOLT Schema Validation and Type System
Because even compact formats need rules - like haiku has 5-7-5
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import re


class JoltType(Enum):
    """JOLT data types"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NULL = "null"
    OBJECT = "object"
    ARRAY = "array"
    TABLE = "table"
    ANY = "any"


@dataclass
class ValidationError:
    """Validation error details"""
    path: List[str]
    message: str
    expected: Any = None
    actual: Any = None
    
    def __str__(self) -> str:
        path_str = ".".join(self.path) if self.path else "root"
        msg = f"Validation error at {path_str}: {self.message}"
        if self.expected is not None:
            msg += f" (expected: {self.expected}, got: {self.actual})"
        return msg


@dataclass
class SchemaNode:
    """Node in JOLT schema tree"""
    type: Union[JoltType, List[JoltType]]
    required: bool = True
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    properties: Optional[Dict[str, 'SchemaNode']] = None
    items: Optional['SchemaNode'] = None
    table_schema: Optional[Dict[str, 'SchemaNode']] = None
    custom_validator: Optional[Callable[[Any, List[str]], Optional[str]]] = None
    description: Optional[str] = None
    
    def validate(self, value: Any, path: List[str] = None) -> List[ValidationError]:
        """Validate a value against this schema node"""
        if path is None:
            path = []
        
        errors = []
        
        # Handle null/missing values
        if value is None:
            if self.required and self.default is None:
                errors.append(ValidationError(
                    path, 
                    "Required field is null",
                    expected="non-null value",
                    actual="null"
                ))
            return errors
        
        # Type validation
        types = self.type if isinstance(self.type, list) else [self.type]
        type_valid = False
        
        for jolt_type in types:
            if jolt_type == JoltType.ANY:
                type_valid = True
                break
            elif jolt_type == JoltType.STRING and isinstance(value, str):
                type_valid = True
            elif jolt_type == JoltType.INTEGER and isinstance(value, int) and not isinstance(value, bool):
                type_valid = True
            elif jolt_type == JoltType.FLOAT and isinstance(value, (int, float)) and not isinstance(value, bool):
                type_valid = True
            elif jolt_type == JoltType.NUMBER and isinstance(value, (int, float)) and not isinstance(value, bool):
                type_valid = True
            elif jolt_type == JoltType.BOOLEAN and isinstance(value, bool):
                type_valid = True
            elif jolt_type == JoltType.NULL and value is None:
                type_valid = True
            elif jolt_type == JoltType.OBJECT and isinstance(value, dict):
                type_valid = True
            elif jolt_type == JoltType.ARRAY and isinstance(value, list):
                type_valid = True
            elif jolt_type == JoltType.TABLE and isinstance(value, list) and all(isinstance(x, dict) for x in value):
                type_valid = True
            
            if type_valid:
                break
        
        if not type_valid:
            errors.append(ValidationError(
                path,
                f"Type mismatch",
                expected=[t.value for t in types],
                actual=type(value).__name__
            ))
            return errors  # No point continuing if type is wrong
        
        # String validations
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                errors.append(ValidationError(
                    path,
                    f"String too short",
                    expected=f"min length {self.min_length}",
                    actual=f"length {len(value)}"
                ))
            
            if self.max_length is not None and len(value) > self.max_length:
                errors.append(ValidationError(
                    path,
                    f"String too long",
                    expected=f"max length {self.max_length}",
                    actual=f"length {len(value)}"
                ))
            
            if self.pattern:
                if not re.match(self.pattern, value):
                    errors.append(ValidationError(
                        path,
                        f"String does not match pattern",
                        expected=self.pattern,
                        actual=value
                    ))
        
        # Number validations
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min_value is not None and value < self.min_value:
                errors.append(ValidationError(
                    path,
                    f"Value too small",
                    expected=f">= {self.min_value}",
                    actual=value
                ))
            
            if self.max_value is not None and value > self.max_value:
                errors.append(ValidationError(
                    path,
                    f"Value too large",
                    expected=f"<= {self.max_value}",
                    actual=value
                ))
        
        # Enum validation
        if self.enum_values is not None:
            if value not in self.enum_values:
                errors.append(ValidationError(
                    path,
                    f"Value not in allowed set",
                    expected=self.enum_values,
                    actual=value
                ))
        
        # Array validations
        if isinstance(value, list):
            if self.min_length is not None and len(value) < self.min_length:
                errors.append(ValidationError(
                    path,
                    f"Array too short",
                    expected=f"min length {self.min_length}",
                    actual=f"length {len(value)}"
                ))
            
            if self.max_length is not None and len(value) > self.max_length:
                errors.append(ValidationError(
                    path,
                    f"Array too long",
                    expected=f"max length {self.max_length}",
                    actual=f"length {len(value)}"
                ))
            
            # Validate array items
            if self.items:
                for i, item in enumerate(value):
                    item_errors = self.items.validate(item, path + [f"[{i}]"])
                    errors.extend(item_errors)
            
            # Validate table schema
            if self.table_schema:
                for i, row in enumerate(value):
                    if not isinstance(row, dict):
                        errors.append(ValidationError(
                            path + [f"[{i}]"],
                            "Table row must be an object",
                            expected="object",
                            actual=type(row).__name__
                        ))
                        continue
                    
                    for col, schema in self.table_schema.items():
                        if col in row:
                            col_errors = schema.validate(row[col], path + [f"[{i}].{col}"])
                            errors.extend(col_errors)
                        elif schema.required:
                            errors.append(ValidationError(
                                path + [f"[{i}].{col}"],
                                f"Required column missing",
                                expected=col,
                                actual="missing"
                            ))
        
        # Object validations
        if isinstance(value, dict):
            if self.properties:
                # Check required properties
                for prop, schema in self.properties.items():
                    if prop in value:
                        prop_errors = schema.validate(value[prop], path + [prop])
                        errors.extend(prop_errors)
                    elif schema.required:
                        if schema.default is None:
                            errors.append(ValidationError(
                                path + [prop],
                                f"Required property missing",
                                expected=prop,
                                actual="missing"
                            ))
                
                # Check for unexpected properties (strict mode)
                for prop in value:
                    if prop not in self.properties:
                        errors.append(ValidationError(
                            path + [prop],
                            f"Unexpected property",
                            expected=list(self.properties.keys()),
                            actual=prop
                        ))
        
        # Custom validation
        if self.custom_validator:
            error_msg = self.custom_validator(value, path)
            if error_msg:
                errors.append(ValidationError(path, error_msg))
        
        return errors


class JoltSchema:
    """
    JOLT Schema definition and validation
    Like a strict teacher, but for data formats
    """
    
    def __init__(self, schema: Union[Dict[str, Any], SchemaNode], strict: bool = True):
        """
        Initialize JOLT schema
        
        Args:
            schema: Schema definition (dict or SchemaNode)
            strict: If True, reject unknown properties
        """
        self.strict = strict
        if isinstance(schema, dict):
            self.root = self._build_schema_node(schema)
        else:
            self.root = schema
    
    def _build_schema_node(self, schema_def: Dict[str, Any]) -> SchemaNode:
        """Build SchemaNode from dictionary definition"""
        # Parse type
        type_def = schema_def.get('type', 'any')
        if isinstance(type_def, str):
            jolt_type = JoltType(type_def) if type_def != 'any' else JoltType.ANY
        else:
            jolt_type = [JoltType(t) for t in type_def]
        
        # Build node
        node = SchemaNode(
            type=jolt_type,
            required=schema_def.get('required', True),
            default=schema_def.get('default'),
            min_value=schema_def.get('min'),
            max_value=schema_def.get('max'),
            min_length=schema_def.get('minLength'),
            max_length=schema_def.get('maxLength'),
            pattern=schema_def.get('pattern'),
            enum_values=schema_def.get('enum'),
            description=schema_def.get('description')
        )
        
        # Handle nested schemas
        if 'properties' in schema_def:
            node.properties = {
                key: self._build_schema_node(value)
                for key, value in schema_def['properties'].items()
            }
        
        if 'items' in schema_def:
            node.items = self._build_schema_node(schema_def['items'])
        
        if 'tableSchema' in schema_def:
            node.table_schema = {
                key: self._build_schema_node(value)
                for key, value in schema_def['tableSchema'].items()
            }
        
        return node
    
    def validate(self, data: Any) -> List[ValidationError]:
        """
        Validate data against schema
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self.root.validate(data)
    
    def is_valid(self, data: Any) -> bool:
        """Check if data is valid against schema"""
        return len(self.validate(data)) == 0
    
    def to_jolt_schema_format(self) -> str:
        """
        Convert schema to JOLT Schema Format (JSF)
        A compact representation of the schema itself
        """
        def node_to_jsf(node: SchemaNode, indent: int = 0) -> List[str]:
            lines = []
            spaces = "  " * indent
            
            # Type definition
            if isinstance(node.type, list):
                type_str = "|".join(t.value for t in node.type)
            else:
                type_str = node.type.value
            
            # Build constraint string
            constraints = []
            if not node.required:
                constraints.append("optional")
            if node.default is not None:
                constraints.append(f"default={node.default}")
            if node.min_value is not None:
                constraints.append(f"min={node.min_value}")
            if node.max_value is not None:
                constraints.append(f"max={node.max_value}")
            if node.min_length is not None:
                constraints.append(f"minLen={node.min_length}")
            if node.max_length is not None:
                constraints.append(f"maxLen={node.max_length}")
            if node.pattern:
                constraints.append(f"pattern=/{node.pattern}/")
            if node.enum_values:
                enum_str = ",".join(str(v) for v in node.enum_values)
                constraints.append(f"enum=[{enum_str}]")
            
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            
            # Format based on type
            if node.properties:
                lines.append(f"{spaces}{type_str}{constraint_str} {{")
                for key, child in node.properties.items():
                    lines.append(f"{spaces}  {key}:")
                    lines.extend(node_to_jsf(child, indent + 2))
                lines.append(f"{spaces}}}")
            elif node.items:
                lines.append(f"{spaces}{type_str}[]{constraint_str} {{")
                lines.extend(node_to_jsf(node.items, indent + 1))
                lines.append(f"{spaces}}}")
            elif node.table_schema:
                lines.append(f"{spaces}table{constraint_str} {{")
                for col, schema in node.table_schema.items():
                    lines.append(f"{spaces}  {col}:")
                    lines.extend(node_to_jsf(schema, indent + 2))
                lines.append(f"{spaces}}}")
            else:
                lines.append(f"{spaces}{type_str}{constraint_str}")
            
            return lines
        
        return "\n".join(node_to_jsf(self.root))


def create_schema_from_sample(data: Any) -> JoltSchema:
    """
    Generate schema from sample data
    Like reverse engineering, but for data formats
    """
    def infer_type(value: Any) -> JoltType:
        if value is None:
            return JoltType.NULL
        elif isinstance(value, bool):
            return JoltType.BOOLEAN
        elif isinstance(value, int):
            return JoltType.INTEGER
        elif isinstance(value, float):
            return JoltType.FLOAT
        elif isinstance(value, str):
            return JoltType.STRING
        elif isinstance(value, dict):
            return JoltType.OBJECT
        elif isinstance(value, list):
            if not value:
                return JoltType.ARRAY
            # Check if it's a table (uniform dict list)
            if all(isinstance(x, dict) for x in value):
                first_keys = set(value[0].keys())
                if all(set(d.keys()) == first_keys for d in value):
                    return JoltType.TABLE
            return JoltType.ARRAY
        else:
            return JoltType.ANY
    
    def build_schema_def(value: Any) -> Dict[str, Any]:
        schema = {'type': infer_type(value).value}
        
        if isinstance(value, str):
            schema['maxLength'] = len(value) * 2  # Allow some flexibility
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            schema['min'] = value * 0.5
            schema['max'] = value * 2
        elif isinstance(value, list):
            schema['minLength'] = 0
            schema['maxLength'] = len(value) * 2
            
            if value and infer_type(value) == JoltType.TABLE:
                # Build table schema
                columns = {}
                for key in value[0].keys():
                    # Infer column type from all rows
                    col_values = [row[key] for row in value if key in row]
                    if col_values:
                        columns[key] = build_schema_def(col_values[0])
                schema['tableSchema'] = columns
            elif value:
                # Regular array - infer from first item
                schema['items'] = build_schema_def(value[0])
        elif isinstance(value, dict):
            schema['properties'] = {
                key: build_schema_def(val)
                for key, val in value.items()
            }
        
        return schema
    
    return JoltSchema(build_schema_def(data))
