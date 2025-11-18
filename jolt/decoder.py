"""
JOLT Decoder v0.3 - Enhanced JOLT to JSON conversion
Like a universal translator, but for data formats!
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Token types for JOLT parsing"""
    IDENTIFIER = "IDENTIFIER"
    COLON = "COLON"
    COMMA = "COMMA"
    OPEN_BRACE = "OPEN_BRACE"
    CLOSE_BRACE = "CLOSE_BRACE"
    OPEN_BRACKET = "OPEN_BRACKET"
    CLOSE_BRACKET = "CLOSE_BRACKET"
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"


@dataclass
class Token:
    """A token in the JOLT stream with location info"""
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.value}, {repr(self.value)}, L{self.line}:C{self.column})"


class JoltSyntaxError(Exception):
    """Custom exception for JOLT syntax errors with helpful messages"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0, context: str = ""):
        self.message = message
        self.line = line
        self.column = column
        self.context = context
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        msg = f"JOLT Syntax Error at line {self.line}, column {self.column}: {self.message}"
        if self.context:
            msg += f"\n  Near: {self.context}"
        return msg


class JoltLexer:
    """
    Enhanced tokenizer for JOLT format v0.3
    
    Think of this as a sushi chef carefully separating ingredients - 
    except the ingredients are characters and the sushi is tokens!
    """
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]
        
    def error(self, msg: str) -> JoltSyntaxError:
        """Create a helpful error with context"""
        # Get context (line containing error)
        line_start = self.text.rfind('\n', 0, self.pos) + 1
        line_end = self.text.find('\n', self.pos)
        if line_end == -1:
            line_end = len(self.text)
        context = self.text[line_start:line_end].strip()
        
        return JoltSyntaxError(msg, self.line, self.column, context)
    
    def peek(self, offset: int = 0) -> Optional[str]:
        """Look ahead without consuming"""
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None
    
    def advance(self) -> Optional[str]:
        """Consume and return next character"""
        if self.pos < len(self.text):
            char = self.text[self.pos]
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return char
        return None
    
    def skip_whitespace(self, skip_newline: bool = True) -> None:
        """Skip horizontal whitespace and optionally newlines"""
        while self.peek() and self.peek() in (' ', '\t', '\r'):
            self.advance()
        if skip_newline and self.peek() == '\n':
            self.advance()
    
    def read_string(self) -> str:
        """Read a quoted string with escape sequence support"""
        self.advance()  # Skip opening quote
        chars = []
        
        while self.peek() and self.peek() != '"':
            if self.peek() == '\\':
                self.advance()  # Skip backslash
                next_char = self.peek()
                
                if next_char == 'n':
                    chars.append('\n')
                    self.advance()
                elif next_char == 't':
                    chars.append('\t')
                    self.advance()
                elif next_char == 'r':
                    chars.append('\r')
                    self.advance()
                elif next_char == '\\':
                    chars.append('\\')
                    self.advance()
                elif next_char == '"':
                    chars.append('"')
                    self.advance()
                elif next_char:
                    # Unknown escape - keep literal
                    chars.append(next_char)
                    self.advance()
                else:
                    raise self.error("Unexpected end of string")
            else:
                chars.append(self.advance())
        
        if self.peek() != '"':
            raise self.error("Unterminated string")
        
        self.advance()  # Skip closing quote
        return ''.join(chars)
    
    def read_unquoted(self) -> str:
        """Read an unquoted value until delimiter"""
        chars = []
        delimiters = (',', ':', '{', '}', '[', ']', '\n', '\r', ' ', '\t')
        
        while self.peek() and self.peek() not in delimiters:
            chars.append(self.advance())
        
        return ''.join(chars)
    
    def read_number(self) -> Union[int, float]:
        """Read a number (integer or float)"""
        chars = []
        has_dot = False
        
        # Handle negative numbers
        if self.peek() == '-':
            chars.append(self.advance())
        
        # Read digits and decimal point
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if has_dot:
                    break  # Second dot - not part of number
                has_dot = True
            chars.append(self.advance())
        
        num_str = ''.join(chars)
        if not num_str or num_str == '-' or num_str == '.':
            raise self.error(f"Invalid number: {num_str}")
        
        try:
            return float(num_str) if has_dot else int(num_str)
        except ValueError:
            raise self.error(f"Invalid number format: {num_str}")
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire JOLT text
        
        This is where the magic happens - we transform a string into a sequence
        of meaningful tokens, like turning a sentence into words!
        """
        while self.pos < len(self.text):
            # Handle newlines and indentation
            if self.peek() == '\n':
                token = Token(TokenType.NEWLINE, '\n', self.line, self.column)
                self.tokens.append(token)
                self.advance()
                
                # Measure indentation on next line
                indent_level = 0
                while self.peek() == ' ':
                    indent_level += 1
                    self.advance()
                
                # Skip blank lines
                if self.peek() == '\n':
                    continue
                
                # Skip comment lines (if we decide to support them later)
                if self.peek() == '#':
                    while self.peek() and self.peek() != '\n':
                        self.advance()
                    continue
                
                # Generate INDENT/DEDENT tokens
                if indent_level > self.indent_stack[-1]:
                    self.indent_stack.append(indent_level)
                    self.tokens.append(Token(TokenType.INDENT, indent_level, self.line, self.column))
                elif indent_level < self.indent_stack[-1]:
                    while len(self.indent_stack) > 1 and indent_level < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(Token(TokenType.DEDENT, indent_level, self.line, self.column))
                    
                    # Check for indentation error
                    if indent_level != self.indent_stack[-1]:
                        raise self.error(f"Indentation mismatch: expected {self.indent_stack[-1]}, got {indent_level}")
                
                continue
            
            # Skip horizontal whitespace
            if self.peek() in (' ', '\t', '\r'):
                self.advance()
                continue
            
            # Single character tokens
            char = self.peek()
            
            if char == ':':
                self.tokens.append(Token(TokenType.COLON, ':', self.line, self.column))
                self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.column))
                self.advance()
            elif char == '{':
                self.tokens.append(Token(TokenType.OPEN_BRACE, '{', self.line, self.column))
                self.advance()
            elif char == '}':
                self.tokens.append(Token(TokenType.CLOSE_BRACE, '}', self.line, self.column))
                self.advance()
            elif char == '[':
                # Read array size
                self.advance()
                size_chars = []
                while self.peek() and self.peek().isdigit():
                    size_chars.append(self.advance())
                
                if not size_chars:
                    raise self.error("Array size expected after '['")
                
                size = int(''.join(size_chars))
                
                if self.peek() == ']':
                    self.advance()
                    self.tokens.append(Token(TokenType.OPEN_BRACKET, size, self.line, self.column))
                else:
                    raise self.error(f"Expected ']' after array size, got '{self.peek()}'")
            
            # Quoted strings
            elif char == '"':
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, self.line, self.column))
            
            # Numbers, booleans, null, or identifiers
            else:
                value = self.read_unquoted()
                
                if not value:
                    raise self.error(f"Unexpected character: '{char}'")
                
                # Check if this looks like a key (followed by colon or bracket)
                # If so, treat as identifier even if it's a keyword
                next_char = self.peek()
                is_key = next_char in (':', '[')
                
                # Check for keywords (only if not a key)
                if not is_key and value == 'true':
                    self.tokens.append(Token(TokenType.BOOLEAN, True, self.line, self.column))
                elif not is_key and value == 'false':
                    self.tokens.append(Token(TokenType.BOOLEAN, False, self.line, self.column))
                elif not is_key and value == 'null':
                    self.tokens.append(Token(TokenType.NULL, None, self.line, self.column))
                # Check for numbers
                elif value[0].isdigit() or (value[0] == '-' and len(value) > 1):
                    try:
                        num_value = float(value) if '.' in value else int(value)
                        self.tokens.append(Token(TokenType.NUMBER, num_value, self.line, self.column))
                    except ValueError:
                        # Not a valid number - treat as identifier
                        self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column))
                else:
                    # Identifier
                    self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column))
        
        # Add final DEDENT tokens to close all levels
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line, self.column))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


class JoltParser:
    """
    Enhanced parser for JOLT format v0.3
    
    Like a master assembler putting together IKEA furniture - 
    except the instructions actually make sense!
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def error(self, msg: str) -> JoltSyntaxError:
        """Create a helpful error at current position"""
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            return JoltSyntaxError(msg, token.line, token.column, f"token: {token}")
        return JoltSyntaxError(f"Parser error at end of input: {msg}", 0, 0, "")
    
    def peek(self, offset: int = 0) -> Optional[Token]:
        """Look ahead at token without consuming"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def advance(self) -> Optional[Token]:
        """Consume and return next token"""
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return None
    
    def skip_newlines(self) -> None:
        """Skip over newline tokens"""
        while self.peek() and self.peek().type == TokenType.NEWLINE:
            self.advance()
    
    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type"""
        token = self.advance()
        if not token or token.type != token_type:
            expected = token_type.value
            actual = token.type.value if token else 'EOF'
            raise self.error(f"Expected {expected}, got {actual}")
        return token
    
    def parse_value(self) -> Any:
        """Parse a single value (scalar or structure start)"""
        self.skip_newlines()
        token = self.peek()
        
        if not token:
            raise self.error("Unexpected end of input")
        
        if token.type == TokenType.STRING:
            self.advance()
            return token.value
        elif token.type == TokenType.NUMBER:
            self.advance()
            return token.value
        elif token.type == TokenType.BOOLEAN:
            self.advance()
            return token.value
        elif token.type == TokenType.NULL:
            self.advance()
            return None
        elif token.type == TokenType.IDENTIFIER:
            # Could be unquoted string or start of named object
            next_token = self.peek(1)
            if next_token and next_token.type == TokenType.OPEN_BRACE:
                # Named object block - parse as object which returns {name: {...}}
                return self.parse_object()
            else:
                # Unquoted string value
                self.advance()
                return token.value
        elif token.type == TokenType.OPEN_BRACE:
            # Anonymous object
            return self.parse_object()
        else:
            raise self.error(f"Unexpected token type: {token.type.value}")
    
    def parse_array(self, size: int) -> List[Any]:
        """Parse an array with known size"""
        self.skip_newlines()
        
        # Check if it's a table format
        if self.peek() and self.peek().type == TokenType.OPEN_BRACE:
            return self.parse_table(size)
        
        # Regular array - parse comma-separated values
        values = []
        for i in range(size):
            if i > 0:
                self.expect(TokenType.COMMA)
                self.skip_newlines()
            values.append(self.parse_value())
        
        return values
    
    def parse_table(self, size: int) -> List[Dict[str, Any]]:
        """Parse a table format (array of uniform objects)"""
        self.expect(TokenType.OPEN_BRACE)
        self.skip_newlines()
        
        # Parse column headers (must have INDENT)
        self.expect(TokenType.INDENT)
        columns = []
        
        # Read column names
        while True:
            self.skip_newlines()
            token = self.peek()
            if not token or token.type != TokenType.IDENTIFIER:
                break
            columns.append(token.value)
            self.advance()
            
            # Check for comma (more columns) or colon (end of headers)
            if self.peek() and self.peek().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
            elif self.peek() and self.peek().type == TokenType.COLON:
                break
        
        if not columns:
            raise self.error("Table must have at least one column")
        
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        # Parse rows
        rows = []
        for row_idx in range(size):
            row = {}
            for col_idx, col in enumerate(columns):
                if col_idx > 0:
                    self.expect(TokenType.COMMA)
                    self.skip_newlines()
                row[col] = self.parse_value()
            rows.append(row)
            self.skip_newlines()
        
        self.expect(TokenType.DEDENT)
        self.expect(TokenType.CLOSE_BRACE)
        
        return rows
    
    def parse_object(self) -> Dict[str, Any]:
        """Parse a named or anonymous object"""
        obj: Dict[str, Any] = {}
        name: Optional[str] = None

        # Check for named object: identifier { ... }
        if self.peek() and self.peek().type == TokenType.IDENTIFIER:
            name_token = self.peek()
            # Check if next token is {, making this a named block
            if self.peek(1) and self.peek(1).type == TokenType.OPEN_BRACE:
                name = self.advance().value
                self.skip_newlines()
                self.expect(TokenType.OPEN_BRACE)
            else:
                # Just a regular brace block, no name
                self.expect(TokenType.OPEN_BRACE)
        else:
            self.expect(TokenType.OPEN_BRACE)

        self.skip_newlines()

        # Expect INDENT for object content
        if self.peek() and self.peek().type == TokenType.INDENT:
            self.advance()

        # Parse key-value pairs
        while True:
            self.skip_newlines()
            if not self.peek() or self.peek().type != TokenType.IDENTIFIER:
                break

            key = self.advance().value

            # Check for array notation: key[n]
            if self.peek() and self.peek().type == TokenType.OPEN_BRACKET:
                size = self.advance().value
                
                # Check if it's a table format key[n] { ... }
                self.skip_newlines()
                if self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                    obj[key] = self.parse_table(size)
                else:
                    self.expect(TokenType.COLON)
                    self.skip_newlines()
                    obj[key] = self.parse_array(size)
            # Check for nested named object: key { ... } (no colon!)
            elif self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                # This is a nested named object, parse it recursively
                # The name is the key, and parse_object will handle the braces
                self.skip_newlines()
                nested_obj = self.parse_object()
                # parse_object returns the inner dict without name wrapping for nested objects
                obj[key] = nested_obj
            else:
                self.expect(TokenType.COLON)
                self.skip_newlines()
                value = self.parse_value()
                # If value is a dict with single key, it might be a named block that should be unwrapped
                # But we need to be careful - only unwrap if it came from a named block parse
                obj[key] = value

            self.skip_newlines()

        # Expect DEDENT to close object
        if self.peek() and self.peek().type == TokenType.DEDENT:
            self.advance()

        self.expect(TokenType.CLOSE_BRACE)

        # Return with or without wrapping
        # Only wrap with name if this is a top-level or root named block
        if name is not None:
            return {name: obj}
        return obj
    
    def parse_root_object(self) -> Dict[str, Any]:
        """
        Parse a top-level braceless object
        
        Format:
            key1: value1
            key2: value2
            array[3]: 1,2,3
            table[2] { ... }
            nested { ... }
        """
        obj: Dict[str, Any] = {}

        while True:
            self.skip_newlines()
            if not self.peek() or self.peek().type != TokenType.IDENTIFIER:
                break

            key = self.advance().value

            # Check for array notation: key[n]
            if self.peek() and self.peek().type == TokenType.OPEN_BRACKET:
                size = self.advance().value
                
                # Check if it's a table format key[n] { ... }
                self.skip_newlines()
                if self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                    obj[key] = self.parse_table(size)
                else:
                    self.expect(TokenType.COLON)
                    self.skip_newlines()
                    obj[key] = self.parse_array(size)
            # Check for nested named object: key { ... } (no colon!)
            elif self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                # This is a nested named object, parse it recursively
                self.skip_newlines()
                nested_obj = self.parse_object()
                obj[key] = nested_obj
            else:
                self.expect(TokenType.COLON)
                self.skip_newlines()
                obj[key] = self.parse_value()

        return obj
    
    def parse(self) -> Any:
        """
        Parse the entire JOLT document
        
        Handles various root formats:
        - Named block: name { ... }
        - Braceless object: key: value
        - Anonymous object: { ... }
        - Array: [n] { ... } or [n]: ...
        - Scalar: value
        """
        self.skip_newlines()

        if not self.peek() or self.peek().type == TokenType.EOF:
            return {}  # Empty document

        # Determine document type
        first = self.peek()
        second = self.peek(1)

        if first.type == TokenType.IDENTIFIER:
            if second and second.type == TokenType.OPEN_BRACE:
                # Named block: name { ... }
                result = self.parse_object()
            elif second and second.type in (TokenType.COLON, TokenType.OPEN_BRACKET):
                # Braceless object: key: value or key[n]: ...
                result = self.parse_root_object()
            else:
                # Single identifier value
                result = self.parse_value()
        elif first.type == TokenType.OPEN_BRACE:
            # Anonymous object: { ... }
            result = self.parse_object()
        elif first.type == TokenType.OPEN_BRACKET:
            # Root array
            size = self.advance().value
            self.skip_newlines()
            
            if self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                result = self.parse_table(size)
            else:
                self.expect(TokenType.COLON)
                self.skip_newlines()
                result = [self.parse_value() for _ in range(size)]
        else:
            # Try to parse as single value
            result = self.parse_value()

        # Verify we consumed everything
        self.skip_newlines()
        if self.peek() and self.peek().type != TokenType.EOF:
            raise self.error(f"Unexpected token after document: {self.peek().type.value}")

        return result


def jolt_to_json(
    jolt_text: str,
    *,
    wrap_root: bool = False
) -> Any:
    """
    Convert JOLT format text back to JSON-compatible Python object.
    
    v0.3 improvements:
    - Better error messages with line/column info
    - Robust handling of edge cases
    - Support for all JOLT constructs
    
    Args:
        jolt_text: JOLT formatted text
        wrap_root: If True, preserve root name wrapping (legacy)
    
    Returns:
        Python dict/list that can be serialized to JSON
        
    Raises:
        JoltSyntaxError: If the JOLT text is malformed
        
    Example:
        >>> jolt = '''
        ... user {
        ...   id: 1
        ...   name: Alice
        ... }
        ... '''
        >>> result = jolt_to_json(jolt)
        >>> result
        {'user': {'id': 1, 'name': 'Alice'}}
    """
    try:
        # Tokenize
        lexer = JoltLexer(jolt_text)
        tokens = lexer.tokenize()
        
        # Parse
        parser = JoltParser(tokens)
        result = parser.parse()
        
        return result
        
    except JoltSyntaxError:
        # Re-raise with original error
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise JoltSyntaxError(f"Unexpected error during parsing: {str(e)}", 0, 0) from e