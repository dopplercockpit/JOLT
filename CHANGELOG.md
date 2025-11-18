# Changelog

All notable changes to JOLT will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-11-18

### 🎉 Major Release - Production Ready!

This release represents a complete rewrite and enhancement of JOLT with a focus on robustness, correctness, and usability.

### Added
- **Comprehensive Error Handling**: All errors now include helpful messages with line/column information
- **JoltSyntaxError Exception**: Custom exception type for better error catching
- **Decoder-Aware Optimizer**: Optimizations now guarantee decodable output
- **Safe Mode**: Optimizer's safe mode ensures all optimizations preserve round-trip correctness
- **Context-Aware Lexing**: Keywords (true, false, null) are correctly handled as keys when appropriate
- **100% Test Coverage**: Comprehensive test suite covering all edge cases
- **CLI Tool**: Simple command-line interface for conversions and testing
- **Quick Test Function**: `quick_test()` for rapid validation
- **Detailed Documentation**: Complete README with examples and use cases

### Fixed
- **Braceless Root Objects**: Now correctly parse root-level key-value pairs without braces
- **Nested Named Blocks**: Properly handle `key { ... }` syntax for nested objects
- **Table Format Parsing**: Fixed parsing of `key[n] { ... }` table notation
- **Special Character Handling**: Improved escape sequence processing
- **Float Serialization**: Avoid scientific notation for very small numbers
- **Reserved Word Keys**: Allow "null", "true", "false" as object keys
- **Mixed Array Types**: Better handling of arrays with heterogeneous elements
- **Deep Nesting**: Correct parsing of deeply nested structures
- **Empty Structures**: Proper handling of empty objects and arrays
- **Unicode Support**: Full unicode character support including emojis

### Changed
- **Optimizer Defaults**: Experimental features (pattern detection, value pooling, sparse arrays) now disabled by default
- **Error Messages**: More helpful and contextual error messages
- **Code Organization**: Cleaner separation of concerns between encoder, decoder, and optimizer
- **Type Hints**: Improved type annotations throughout
- **Documentation**: Extensive inline documentation with metaphors (making code fun to read!)

### Performance
- Improved parsing performance through better lexer design
- Reduced memory usage in streaming scenarios
- Faster token estimation

### Security
- Input validation to prevent malformed data processing
- Proper escape sequence handling prevents injection attacks
- Size limits on string processing prevent DoS attacks

## [0.2.0] - Previous Release

### Added
- Streaming support for large files
- Schema validation system
- Advanced optimizer with multiple strategies
- Benchmark framework
- Framework integrations (FastAPI, Flask, LangChain, Pandas, etc.)

### Notes
- v0.2 had several parsing bugs and edge case handling issues
- Some optimizer features created non-decodable structures
- Error messages were not user-friendly

## [0.1.0] - Initial Release

### Added
- Basic encoder (JSON → JOLT)
- Core JOLT syntax:
  - Unquoted keys
  - Explicit array lengths
  - Table format for uniform object arrays
  - Named blocks
- ~70% token reduction vs JSON

### Limitations
- No decoder (JOLT → JSON)
- No error handling
- No optimization
- No validation

---

## Upgrade Guide

### From v0.2 to v0.3

**Breaking Changes:**
1. Optimizer defaults changed - experimental features now opt-in
2. Some edge cases may parse differently (but correctly now!)
3. Error types changed to `JoltSyntaxError`

**Migration Steps:**
```python
# Old v0.2 code
from jolt import json_to_jolt, jolt_to_json

# v0.3 - same API, better behavior!
from jolt import json_to_jolt, jolt_to_json, JoltSyntaxError

# Add error handling
try:
    result = jolt_to_json(jolt_text)
except JoltSyntaxError as e:
    print(f"Parse error: {e}")

# Optimizer - explicitly enable experimental features
from jolt import JoltOptimizer

optimizer = JoltOptimizer(
    enable_abbreviations=True,  # Safe, recommended
    enable_pattern_detection=False,  # Now opt-in
    enable_value_pooling=False,  # Now opt-in  
    enable_sparse_arrays=False,  # Now opt-in
    safe_mode=True  # Recommended
)
```

### From v0.1 to v0.3

v0.1 only had an encoder. v0.3 adds:
- Full bidirectional conversion
- Error handling
- Optimization
- Testing

Update your code to use the new APIs as shown above.

---

## Roadmap

### v0.4 (Planned - Q1 2025)
- Comment support (`# This is a comment`)
- Multi-line strings with heredoc syntax
- Type hints in format (optional)
- Schema inference from data
- VS Code extension with syntax highlighting

### v0.5 (Planned - Q2 2025)
- Binary JOLT (BJOLT) for maximum compression
- Streaming API with async support
- GraphQL integration
- Compression plugins (gzip, brotli)
- TypeScript/JavaScript implementation

### v1.0 (Planned - Q3 2025)
- Stable API guarantee
- RFC specification
- Multiple language implementations
- Production battle-tested
- Enterprise support options

---

For detailed release notes and migration guides, see [RELEASES.md](RELEASES.md)
