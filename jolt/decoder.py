"""
JOLT Decoder - Converts JOLT format back to JSON
Think of this as the reverse translator - like converting haiku back into a novel
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
    """A token in the JOLT stream"""
    type: TokenType
    value: Any
    line: int
    column: int


class JoltLexer:
    """
    Tokenizer for JOLT format
    Like a sushi chef carefully separating each ingredient before assembly
    """
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]
        
    def error(self, msg: str) -> Exception:
        return ValueError(f"Lexer error at line {self.line}, column {self.column}: {msg}")
    
    def peek(self, offset: int = 0) -> Optional[str]:
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None
    
    def advance(self) -> Optional[str]:
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
        while self.peek() and self.peek() in (' ', '\t', '\r'):
            self.advance()
        if skip_newline and self.peek() == '\n':
            self.advance()
    
    def read_string(self) -> str:
        """Read a quoted string"""
        self.advance()  # Skip opening quote
        chars = []
        while self.peek() and self.peek() != '"':
            if self.peek() == '\\':
                self.advance()
                next_char = self.advance()
                if next_char == 'n':
                    chars.append('\n')
                elif next_char == 't':
                    chars.append('\t')
                elif next_char == 'r':
                    chars.append('\r')
                elif next_char == '\\':
                    chars.append('\\')
                elif next_char == '"':
                    chars.append('"')
                else:
                    chars.append(next_char)
            else:
                chars.append(self.advance())
        self.advance()  # Skip closing quote
        return ''.join(chars)
    
    def read_unquoted(self) -> str:
        """Read an unquoted value until delimiter"""
        chars = []
        while self.peek() and self.peek() not in (',', ':', '{', '}', '[', ']', '\n', '\r', ' ', '\t'):
            chars.append(self.advance())
        return ''.join(chars)
    
    def read_number(self) -> Union[int, float]:
        """Read a number"""
        chars = []
        has_dot = False
        
        # Handle negative numbers
        if self.peek() == '-':
            chars.append(self.advance())
        
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if has_dot:
                    break
                has_dot = True
            chars.append(self.advance())
        
        num_str = ''.join(chars)
        return float(num_str) if has_dot else int(num_str)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire JOLT text"""
        while self.pos < len(self.text):
            # Handle newlines and indentation
            if self.peek() == '\n':
                token = Token(TokenType.NEWLINE, '\n', self.line, self.column)
                self.tokens.append(token)
                self.advance()
                
                # Check indentation on next line
                indent_level = 0
                while self.peek() == ' ':
                    indent_level += 1
                    self.advance()
                
                # Skip empty lines
                if self.peek() == '\n':
                    continue
                
                # Generate INDENT/DEDENT tokens
                if indent_level > self.indent_stack[-1]:
                    self.indent_stack.append(indent_level)
                    self.tokens.append(Token(TokenType.INDENT, indent_level, self.line, self.column))
                elif indent_level < self.indent_stack[-1]:
                    while len(self.indent_stack) > 1 and indent_level < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(Token(TokenType.DEDENT, indent_level, self.line, self.column))
                
                continue
            
            # Skip whitespace
            if self.peek() in (' ', '\t', '\r'):
                self.advance()
                continue
            
            # Single character tokens
            if self.peek() == ':':
                self.tokens.append(Token(TokenType.COLON, ':', self.line, self.column))
                self.advance()
            elif self.peek() == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.column))
                self.advance()
            elif self.peek() == '{':
                self.tokens.append(Token(TokenType.OPEN_BRACE, '{', self.line, self.column))
                self.advance()
            elif self.peek() == '}':
                self.tokens.append(Token(TokenType.CLOSE_BRACE, '}', self.line, self.column))
                self.advance()
            elif self.peek() == '[':
                # Read array size
                self.advance()
                size_chars = []
                while self.peek() and self.peek().isdigit():
                    size_chars.append(self.advance())
                size = int(''.join(size_chars)) if size_chars else 0
                
                if self.peek() == ']':
                    self.advance()
                    self.tokens.append(Token(TokenType.OPEN_BRACKET, size, self.line, self.column))
                else:
                    raise self.error(f"Expected ']' after array size")
            
            # Quoted strings
            elif self.peek() == '"':
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, self.line, self.column))
            
            # Numbers, booleans, null, or identifiers
            else:
                value = self.read_unquoted()
                
                if value == 'true':
                    self.tokens.append(Token(TokenType.BOOLEAN, True, self.line, self.column))
                elif value == 'false':
                    self.tokens.append(Token(TokenType.BOOLEAN, False, self.line, self.column))
                elif value == 'null':
                    self.tokens.append(Token(TokenType.NULL, None, self.line, self.column))
                elif value and (value[0].isdigit() or value[0] == '-'):
                    try:
                        num_value = float(value) if '.' in value else int(value)
                        self.tokens.append(Token(TokenType.NUMBER, num_value, self.line, self.column))
                    except ValueError:
                        self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column))
                elif value:
                    self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column))
        
        # Add final DEDENT tokens
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line, self.column))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


class JoltParser:
    """
    Parser for JOLT format
    Like a master assembler putting together a complex LEGO set from tiny pieces
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def error(self, msg: str) -> Exception:
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            return ValueError(f"Parser error at line {token.line}, column {token.column}: {msg}")
        return ValueError(f"Parser error: {msg}")
    
    def peek(self, offset: int = 0) -> Optional[Token]:
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def advance(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return None
    
    def skip_newlines(self) -> None:
        while self.peek() and self.peek().type == TokenType.NEWLINE:
            self.advance()
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.advance()
        if not token or token.type != token_type:
            raise self.error(f"Expected {token_type}, got {token.type if token else 'EOF'}")
        return token
    
    def parse_value(self) -> Any:
        """Parse a single value"""
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
            # Could be an unquoted string or start of an object
            if self.peek(1) and self.peek(1).type == TokenType.OPEN_BRACE:
                return self.parse_object()
            else:
                self.advance()
                return token.value
        else:
            raise self.error(f"Unexpected token: {token.type}")
    
    def parse_array(self, size: int) -> List[Any]:
        """Parse an array with known size"""
        self.skip_newlines()
        
        # Check if it's a table format (array of uniform objects)
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
        
        # Parse column headers
        self.expect(TokenType.INDENT)
        columns = []
        
        while True:
            self.skip_newlines()
            token = self.peek()
            if not token or token.type != TokenType.IDENTIFIER:
                break
            columns.append(token.value)
            self.advance()
            
            if self.peek() and self.peek().type == TokenType.COMMA:
                self.advance()
            elif self.peek() and self.peek().type == TokenType.COLON:
                break
        
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        # Parse rows
        rows = []
        for _ in range(size):
            row = {}
            for i, col in enumerate(columns):
                if i > 0:
                    self.expect(TokenType.COMMA)
                    self.skip_newlines()
                row[col] = self.parse_value()
            rows.append(row)
            self.skip_newlines()
        
        self.expect(TokenType.DEDENT)
        self.expect(TokenType.CLOSE_BRACE)
        
        return rows
    
    def parse_object(self) -> Dict[str, Any]:
        """Parse an object"""
        obj = {}
        
        # Check for named object
        if self.peek() and self.peek().type == TokenType.IDENTIFIER:
            name = self.advance().value
            self.skip_newlines()
            self.expect(TokenType.OPEN_BRACE)
            # For now, we ignore the name and just parse the object
        else:
            self.expect(TokenType.OPEN_BRACE)
        
        self.skip_newlines()
        
        # Expect indent for object content
        if self.peek() and self.peek().type == TokenType.INDENT:
            self.advance()
        
        while True:
            self.skip_newlines()
            
            # Check for end of object
            if self.peek() and self.peek().type in (TokenType.DEDENT, TokenType.CLOSE_BRACE):
                break
            
            # Parse key
            if not self.peek() or self.peek().type != TokenType.IDENTIFIER:
                break
            
            key = self.advance().value
            
            # Check for array notation
            if self.peek() and self.peek().type == TokenType.OPEN_BRACKET:
                size = self.advance().value
                self.expect(TokenType.COLON)
                self.skip_newlines()
                obj[key] = self.parse_array(size)
            
            # Check for nested object
            elif self.peek() and self.peek().type == TokenType.OPEN_BRACE:
                obj[key] = self.parse_object()
            
            # Regular key-value pair
            else:
                self.expect(TokenType.COLON)
                self.skip_newlines()
                obj[key] = self.parse_value()
            
            self.skip_newlines()
        
        # Handle dedent if present
        if self.peek() and self.peek().type == TokenType.DEDENT:
            self.advance()
        
        # Expect closing brace
        self.expect(TokenType.CLOSE_BRACE)
        
        return obj
    
    def parse(self) -> Any:
        """Parse the entire JOLT document"""
        self.skip_newlines()
        
        # Check if document starts with a named block
        if self.peek() and self.peek().type == TokenType.IDENTIFIER:
            if self.peek(1) and self.peek(1).type == TokenType.OPEN_BRACE:
                result = self.parse_object()
            else:
                # Single value document
                result = self.parse_value()
        else:
            # Try to parse as object or value
            result = self.parse_value()
        
        # Ensure we've consumed all tokens
        self.skip_newlines()
        if self.peek() and self.peek().type != TokenType.EOF:
            raise self.error(f"Unexpected token after document: {self.peek().type}")
        
        return result


def jolt_to_json(
    jolt_text: str,
    *,
    wrap_root: bool = False
) -> Any:
    """
    Convert JOLT format text back to JSON-compatible Python object.
    
    Args:
        jolt_text: JOLT formatted text
        wrap_root: If True and a root name is detected, wrap result in {root_name: ...}
    
    Returns:
        Python dict/list that can be serialized to JSON
    """
    # Tokenize
    lexer = JoltLexer(jolt_text)
    tokens = lexer.tokenize()
    
    # Parse
    parser = JoltParser(tokens)
    result = parser.parse()
    
    # Handle root wrapping if needed
    if wrap_root and isinstance(result, dict):
        # Try to detect if there was a root name
        # This is a simplified approach - in production we'd track this during parsing
        lines = jolt_text.strip().split('\n')
        if lines and '{' in lines[0]:
            root_name = lines[0].split('{')[0].strip()
            if root_name:
                result = {root_name: result}
    
    return result
