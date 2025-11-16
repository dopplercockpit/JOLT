"""
JOLT Streaming Parser - Process large JOLT documents efficiently
Like a sushi train that delivers data piece by piece instead of dumping the whole ocean on your plate
"""
from __future__ import annotations
from typing import Any, Iterator, Optional, Dict, List, Callable, Union
from dataclasses import dataclass
from enum import Enum
import io


class StreamEventType(Enum):
    """Types of events in the JOLT stream"""
    START_OBJECT = "START_OBJECT"
    END_OBJECT = "END_OBJECT"
    START_ARRAY = "START_ARRAY"
    END_ARRAY = "END_ARRAY"
    KEY = "KEY"
    VALUE = "VALUE"
    START_TABLE = "START_TABLE"
    TABLE_HEADERS = "TABLE_HEADERS"
    TABLE_ROW = "TABLE_ROW"
    END_TABLE = "END_TABLE"


@dataclass
class StreamEvent:
    """An event in the JOLT stream"""
    type: StreamEventType
    data: Any = None
    path: List[str] = None
    depth: int = 0


class JoltStreamParser:
    """
    Streaming parser for JOLT format
    Processes data incrementally, perfect for large files or real-time data
    """
    
    def __init__(self, 
                 stream: Union[io.TextIOBase, str],
                 buffer_size: int = 4096):
        """
        Initialize streaming parser
        
        Args:
            stream: Input stream or string
            buffer_size: Size of read buffer for efficiency
        """
        if isinstance(stream, str):
            self.stream = io.StringIO(stream)
        else:
            self.stream = stream
        
        self.buffer_size = buffer_size
        self.buffer = ""
        self.pos = 0
        self.line = 1
        self.column = 1
        self.path_stack: List[str] = []
        self.depth = 0
        
    def _read_more(self) -> bool:
        """Read more data into buffer"""
        if self.pos >= len(self.buffer):
            chunk = self.stream.read(self.buffer_size)
            if chunk:
                self.buffer = self.buffer[self.pos:] + chunk
                self.pos = 0
                return True
            return False
        return True
    
    def _peek(self, offset: int = 0) -> Optional[str]:
        """Peek at character without consuming"""
        pos = self.pos + offset
        if pos < len(self.buffer):
            return self.buffer[pos]
        elif self._read_more():
            return self._peek(offset)
        return None
    
    def _advance(self) -> Optional[str]:
        """Consume and return next character"""
        char = self._peek()
        if char:
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char
    
    def _skip_whitespace(self, skip_newline: bool = False) -> None:
        """Skip whitespace characters"""
        while self._peek() and self._peek() in (' ', '\t', '\r'):
            self._advance()
        if skip_newline:
            while self._peek() == '\n':
                self._advance()
                while self._peek() and self._peek() in (' ', '\t', '\r'):
                    self._advance()
    
    def _read_until(self, delimiters: str) -> str:
        """Read until one of the delimiter characters"""
        chars = []
        while self._peek() and self._peek() not in delimiters:
            if self._peek() == '"':
                # Handle quoted strings
                chars.append(self._advance())  # Include opening quote
                while self._peek() and self._peek() != '"':
                    if self._peek() == '\\':
                        chars.append(self._advance())
                    chars.append(self._advance())
                if self._peek() == '"':
                    chars.append(self._advance())  # Include closing quote
            else:
                chars.append(self._advance())
        return ''.join(chars).strip()
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a value string into appropriate type"""
        if not value_str:
            return None
        
        # Handle quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
        
        # Handle special literals
        if value_str == 'null':
            return None
        elif value_str == 'true':
            return True
        elif value_str == 'false':
            return False
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            return value_str
    
    def parse_stream(self) -> Iterator[StreamEvent]:
        """
        Parse JOLT document as a stream of events
        
        Yields:
            StreamEvent objects representing document structure
        """
        self._skip_whitespace(skip_newline=True)
        
        # Check for root object
        root_name = None
        if self._peek() and self._peek() not in '{[':
            # Read potential root name
            name = self._read_until('{\n')
            if name and self._peek() == '{':
                root_name = name
                self.path_stack.append(root_name)
        
        # Main parsing loop
        while self._peek():
            self._skip_whitespace(skip_newline=True)
            
            char = self._peek()
            if not char:
                break
            
            if char == '{':
                # Start of object
                self._advance()
                self.depth += 1
                yield StreamEvent(
                    StreamEventType.START_OBJECT, 
                    data=self.path_stack[-1] if self.path_stack else None,
                    path=self.path_stack.copy(),
                    depth=self.depth
                )
                
            elif char == '}':
                # End of object
                self._advance()
                yield StreamEvent(
                    StreamEventType.END_OBJECT,
                    path=self.path_stack.copy(),
                    depth=self.depth
                )
                self.depth -= 1
                if self.path_stack:
                    self.path_stack.pop()
                
            elif char == '[':
                # Array notation
                self._advance()
                size_str = self._read_until(']')
                size = int(size_str) if size_str else 0
                self._advance()  # Skip ']'
                
                # Check for table format
                self._skip_whitespace(skip_newline=True)
                if self._peek() == '{':
                    yield from self._parse_table(size)
                else:
                    # Regular array
                    yield StreamEvent(
                        StreamEventType.START_ARRAY,
                        data=size,
                        path=self.path_stack.copy(),
                        depth=self.depth
                    )
                    
                    # Parse array elements
                    self._skip_whitespace()
                    if self._peek() == ':':
                        self._advance()
                        self._skip_whitespace()
                        
                        for i in range(size):
                            if i > 0:
                                if self._peek() == ',':
                                    self._advance()
                                    self._skip_whitespace()
                            
                            value_str = self._read_until(',\n}')
                            yield StreamEvent(
                                StreamEventType.VALUE,
                                data=self._parse_value(value_str),
                                path=self.path_stack.copy(),
                                depth=self.depth
                            )
                    
                    yield StreamEvent(
                        StreamEventType.END_ARRAY,
                        path=self.path_stack.copy(),
                        depth=self.depth
                    )
                
        else:
            # Key-value pair or identifier (also supports key[n] array syntax)
            raw_key = self._read_until(':{\n}')
            base_key = raw_key
            array_size: Optional[int] = None

            # Detect array notation: items[3]
            if '[' in raw_key and raw_key.endswith(']'):
                bracket = raw_key.index('[')
                base_key = raw_key[:bracket]
                size_str = raw_key[bracket + 1:-1]
                array_size = int(size_str) if size_str else 0

            if self._peek() == ':':
                # Key-value pair
                self._advance()
                self._skip_whitespace()

                self.path_stack.append(base_key)
                yield StreamEvent(
                    StreamEventType.KEY,
                    data=base_key,
                    path=self.path_stack.copy(),
                    depth=self.depth
                )

                if array_size is not None:
                    # Inline array: key[n]: v1,v2,...
                    yield StreamEvent(
                        StreamEventType.START_ARRAY,
                        data=array_size,
                        path=self.path_stack.copy(),
                        depth=self.depth
                    )

                    for i in range(array_size):
                        if i > 0:
                            if self._peek() == ',':
                                self._advance()
                                self._skip_whitespace()

                        value_str = self._read_until(',\n}')
                        yield StreamEvent(
                            StreamEventType.VALUE,
                            data=self._parse_value(value_str),
                            path=self.path_stack.copy(),
                            depth=self.depth
                        )

                    yield StreamEvent(
                        StreamEventType.END_ARRAY,
                        path=self.path_stack.copy(),
                        depth=self.depth
                    )

                    # Done with this key
                    self.path_stack.pop()

                else:
                    # Non-array value or nested object
                    if self._peek() == '{':
                        # Nested object - handled in subsequent iterations
                        pass
                    elif self._peek() and self._peek() not in '{\n':
                        # Simple scalar
                        value_str = self._read_until(',\n}')
                        yield StreamEvent(
                            StreamEventType.VALUE,
                            data=self._parse_value(value_str),
                            path=self.path_stack.copy(),
                            depth=self.depth
                        )
                        self.path_stack.pop()

                    
            elif self._peek() == '{':
                    # Named object   
                self.path_stack.append(key)
                    # Object start will be handled in next iteration
                
    def _parse_table(self, size: int) -> Iterator[StreamEvent]:
        """Parse table format and yield events"""
        self._advance()  # Skip '{'
        self._skip_whitespace(skip_newline=True)
        
        yield StreamEvent(
            StreamEventType.START_TABLE,
            data=size,
            path=self.path_stack.copy(),
            depth=self.depth
        )
        
        # Parse headers
        headers = []
        while self._peek() and self._peek() not in ':\n':
            header = self._read_until(',:')
            if header:
                headers.append(header.strip())
            if self._peek() == ',':
                self._advance()
                self._skip_whitespace()
        
        if self._peek() == ':':
            self._advance()
        
        yield StreamEvent(
            StreamEventType.TABLE_HEADERS,
            data=headers,
            path=self.path_stack.copy(),
            depth=self.depth
        )
        
        # Parse rows
        for row_idx in range(size):
            self._skip_whitespace(skip_newline=True)
            row_data = {}
            
            for col_idx, header in enumerate(headers):
                if col_idx > 0:
                    if self._peek() == ',':
                        self._advance()
                        self._skip_whitespace()
                
                value_str = self._read_until(',\n}')
                row_data[header] = self._parse_value(value_str)
            
            yield StreamEvent(
                StreamEventType.TABLE_ROW,
                data=row_data,
                path=self.path_stack.copy(),
                depth=self.depth
            )
        
        # Skip to closing brace
        self._skip_whitespace(skip_newline=True)
        if self._peek() == '}':
            self._advance()
        
        yield StreamEvent(
            StreamEventType.END_TABLE,
            path=self.path_stack.copy(),
            depth=self.depth
        )


class JoltStreamBuilder:
    """
    Build JSON objects from JOLT stream events
    Like assembling IKEA furniture but the instructions actually make sense
    """
    
    def __init__(self):
        self.stack: List[Any] = []
        self.current = None
        self.root = None
        
    def process_event(self, event: StreamEvent) -> Optional[Any]:
        """
        Process a stream event and build JSON structure
        
        Returns:
            Complete object when fully parsed, None otherwise
        """
        if event.type == StreamEventType.START_OBJECT:
            obj = {}
            if self.current is not None:
                if isinstance(self.current, dict) and event.path:
                    key = event.path[-1]
                    self.current[key] = obj
                elif isinstance(self.current, list):
                    self.current.append(obj)
            else:
                self.root = obj
            
            self.stack.append(self.current)
            self.current = obj
            
        elif event.type == StreamEventType.END_OBJECT:
            if self.stack:
                self.current = self.stack.pop()
            else:
                return self.root
                
        elif event.type == StreamEventType.START_ARRAY:
            arr = []
            if isinstance(self.current, dict) and event.path:
                key = event.path[-1]
                self.current[key] = arr
            
            self.stack.append(self.current)
            self.current = arr
            
        elif event.type == StreamEventType.END_ARRAY:
            if self.stack:
                self.current = self.stack.pop()
                
        elif event.type == StreamEventType.VALUE:
            if isinstance(self.current, dict) and event.path:
                key = event.path[-1]
                self.current[key] = event.data
            elif isinstance(self.current, list):
                self.current.append(event.data)
                
        elif event.type == StreamEventType.START_TABLE:
            arr = []
            if isinstance(self.current, dict) and event.path:
                key = event.path[-1]
                self.current[key] = arr
            
            self.stack.append(self.current)
            self.current = arr
            
        elif event.type == StreamEventType.TABLE_ROW:
            if isinstance(self.current, list):
                self.current.append(event.data)
                
        elif event.type == StreamEventType.END_TABLE:
            if self.stack:
                self.current = self.stack.pop()
        
        return None


def stream_jolt_to_json(jolt_stream: Union[io.TextIOBase, str]) -> Any:
    """
    Convert JOLT stream to JSON object
    
    Args:
        jolt_stream: Input stream or string
        
    Returns:
        Complete JSON object
    """
    parser = JoltStreamParser(jolt_stream)
    builder = JoltStreamBuilder()
    
    for event in parser.parse_stream():
        result = builder.process_event(event)
        if result is not None:
            return result
    
    return builder.root


def filter_jolt_stream(
    jolt_stream: Union[io.TextIOBase, str],
    path_filter: Callable[[List[str]], bool],
    value_processor: Optional[Callable[[Any, List[str]], Any]] = None
) -> Iterator[StreamEvent]:
    """
    Filter and process JOLT stream events
    
    Args:
        jolt_stream: Input stream
        path_filter: Function to determine if path should be included
        value_processor: Optional function to transform values
        
    Yields:
        Filtered and processed stream events
    """
    parser = JoltStreamParser(jolt_stream)
    
    for event in parser.parse_stream():
        if path_filter(event.path or []):
            if event.type == StreamEventType.VALUE and value_processor:
                event.data = value_processor(event.data, event.path)
            yield event
