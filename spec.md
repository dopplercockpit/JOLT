# JOLT Specification (v0.1 Draft)

JOLT — **JSON-Optimized Lightweight Tokens** — is a compact, human-readable,
LLM-native encoding for structured data.

It is designed as a *prompt-time* transport format:
JSON remains the system-of-record, JOLT is the format you feed into models.

---

## 1. Design Goals

1. Reduce token usage vs. JSON for typical agent workloads.
2. Preserve full information (lossless round-trip to JSON).
3. Support nested objects and arrays.
4. Be easy for humans to read and debug.
5. Be easy for LLMs to parse (no ambiguous indentation games).
6. Map cleanly to existing JSON types.

---

## 2. Value Types

JOLT supports the same logical value types as JSON:

- object (mapping)
- array (list)
- string
- number
- boolean
- null

---

## 3. Objects

Objects are represented as **blocks**:

```jolt
identifier {
  key: value
  nested {
    key: value
  }
}

