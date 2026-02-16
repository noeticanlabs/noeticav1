# CK-0 Canonical IDs

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 (Pre-Build Tightening)

---

## Overview

This document defines the canonical encoding rules for all identifier types in Noetica. These rules are **frozen** and **binding** for v1.0. Any deviation constitutes a protocol break.

The principle: **All ID comparisons must be byte-exact. No normalization allowed.**

---

## 1. FieldID

### Encoding Specification

| Property | Value |
|----------|-------|
| Format | base16 (hexadecimal) |
| Case | lowercase only |
| Length | 32 hex characters (16 bytes) |

### Rules

1. FieldID MUST be exactly 32 hex characters.
2. Characters MUST be `0-9` or `a-f` (lowercase).
3. No prefix (no `0x`).
4. No padding characters outside the 32-char limit.

### Comparison

- Byte-exact comparison only.
- No case folding.
- No whitespace normalization.
- No leading-zero stripping.

### Examples

```
Valid:   1a2b3c4d5e6f708192a3b4c5d6e7f809
Invalid: 1A2B3C4D5E6F708192A3B4C5D6E7F809 (uppercase)
Invalid: 1a2b3c4d5e6f708192a3b4c5d6e7f80 (too short)
Invalid: 01a2b3c4d5e6f708192a3b4c5d6e7f809 (leading zero)
```

---

## 2. Hash

### Encoding Specification

| Property | Value |
|----------|-------|
| Format | base16 (hexadecimal) |
| Case | lowercase only |
| Length | 64 hex characters (32 bytes) |
| Algorithm | SHA3-256 |

### Rules

1. Hash MUST be exactly 64 hex characters.
2. Characters MUST be `0-9` or `a-f` (lowercase).
3. No prefix (no `0x`).
4. Output from SHA3-256, represented as hex string.

### Comparison

- Byte-exact comparison only.
- No case folding.
- No normalization of any kind.

### Examples

```
Valid:   1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809
Invalid: 1A2B3C4D5E6F708192A3B4C5D6E7F8091A2B3C4D5E6F708192A3B4C5D6E7F809 (uppercase)
Invalid: 1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8 (truncated)
```

---

## 3. OpID

### Encoding Specification

| Property | Value |
|----------|-------|
| Derivation | Computed from recipe |
| Format | Concatenation of three components |
| Output | Variable length |

### Derivation Recipe

OpID is derived using the following exact recipe:

```
OpID = module_digest + ":" + node_path + ":" + binder_index
```

Where:

| Component | Type | Rules |
|-----------|------|-------|
| `module_digest` | Hash | 64 hex chars, SHA3-256 of module bytes |
| `node_path` | String | ASCII, forward slash `/` separator, no leading/trailing slash |
| `binder_index` | Integer | Non-negative decimal, no leading zeros except for "0" |

### Stability Requirement

The OpID derivation MUST produce the same value across all toolchains. This means:

1. Module digest MUST be computed on **canonically encoded** module bytes.
2. Node path separator is exactly `/` (no variation).
3. Binder index uses decimal with no leading zeros.

### Comparison

- Byte-exact comparison only.
- No Unicode normalization on node_path.
- No case folding.

### Examples

```
Valid:   1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809:layer0/attention/query:0
Valid:   1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809:layer0/attention/key:1
Invalid: 1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809:layer0\\attention\\query:0 (backslashes)
Invalid: 1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809:Layer0/attention/query:0 (uppercase)
Invalid: 1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809:layer0/attention/query:00 (leading zero)
```

---

## 4. SchemaID

### Encoding Specification

| Property | Value |
|----------|-------|
| Format | ASCII string |
| Characters | ASCII printable only (0x20-0x7E) |
| Length | Variable |
| Unicode | NOT ALLOWED |

### Rules

1. SchemaID MUST contain only ASCII printable characters (code points 0x20-0x7E).
2. No Unicode characters.
3. No Unicode normalization (NFC, NFD, etc.) - not applicable since Unicode is banned.
4. No leading or trailing whitespace.
5. Empty SchemaID is NOT valid.

### Comparison

- Byte-exact comparison only.
- No case folding.
- No whitespace normalization.
- No Unicode normalization (irrelevant due to ban).

### Examples

```
Valid:   schema_v1_attention
Valid:   custom.layer.v2
Invalid: schema_v1_日本語 (Unicode)
Invalid:  schema_spaced  (leading space)
Invalid: schema_spaced   (trailing space)
```

---

## 5. PolicyID

### Encoding Specification

| Property | Value |
|----------|-------|
| Format | ASCII string |
| Characters | ASCII printable only (0x20-0x7E) |
| Length | Variable |
| Unicode | NOT ALLOWED |

### Rules

1. PolicyID MUST contain only ASCII printable characters (code points 0x20-0x7E).
2. No Unicode characters.
3. No Unicode normalization - not applicable.
4. No leading or trailing whitespace.
5. Empty PolicyID is NOT valid.

### Comparison

- Byte-exact comparison only.
- No case folding.
- No normalization.

### Examples

```
Valid:   policy_budget_enforce_v1
Valid:   policy.max_budget_v2
Invalid: policy_日本語_v1 (Unicode)
Invalid:  policy_spaced (leading space)
```

---

## 6. KernelID

### Encoding Specification

| Property | Value |
|----------|-------|
| Format | ASCII string |
| Characters | ASCII printable only (0x20-0x7E) |
| Length | Variable |
| Unicode | NOT ALLOWED |

### Rules

1. KernelID MUST contain only ASCII printable characters (code points 0x20-0x7E).
2. No Unicode characters.
3. No Unicode normalization - not applicable.
4. No leading or trailing whitespace.
5. Empty KernelID is NOT valid.

### Comparison

- Byte-exact comparison only.
- No case folding.
- No normalization.

### Examples

```
Valid:   kernel_matmul_f32
Valid:   kernel.gelu_v3
Invalid: kernel_日本語 (Unicode)
Invalid:  kernel_spaced (leading space)
```

---

## 7. General Comparison Rules

### Byte-Exact Requirement

All ID comparisons in Noetica MUST use byte-exact comparison:

1. Compare raw bytes directly.
2. If lengths differ, they are NOT equal.
3. No normalization of any kind before comparison.

### Banned Operations

The following operations are **FORBIDDEN** in ID comparison paths:

- Case folding (uppercase/lowercase conversion)
- Unicode normalization (NFC, NFD, NFKC, NFKD)
- Whitespace trimming or normalization
- Leading/trailing whitespace removal
- Leading zero stripping
- Locale-aware collation
- String trimming that changes byte representation

### Sorting Rules

When sorting collections of IDs:

- Sort by raw bytes of canonical encoding.
- For FieldID/Hash: sort by decoded bytes (numeric comparison of hex values).
- For OpID/SchemaID/PolicyID/KernelID: sort by raw ASCII bytes.

### Rejection Criteria

An ID that violates these rules is **invalid** and MUST be rejected at the earliest validation point:

1. Invalid character set → reject
2. Invalid length → reject
3. Case mismatch → reject (for hex encodings)
4. Unicode present → reject (for ASCII-only IDs)
5. Whitespace present → reject (leading/trailing)

---

## 8. Implementation Notes

### Validation Functions

Each ID type requires a validation function:

```pseudo
function validate_fieldid(bytes) -> bool:
    if length(bytes) != 32: return false
    if not all(c in '0123456789abcdef'): return false
    return true

function validate_hash(bytes) -> bool:
    if length(bytes) != 64: return false
    if not all(c in '0123456789abcdef'): return false
    return true

function validate_opid(string) -> bool:
    parts = split(string, ':')
    if length(parts) != 3: return false
    if not validate_hash(parts[0]): return false
    if not validate_node_path(parts[1]): return false
    if not validate_binder_index(parts[2]): return false
    return true

function validate_schemaid(string) -> bool:
    if is_empty(string): return false
    if not all(0x20 <= ord(c) <= 0x7E): return false
    return true
```

### Canonical Form Storage

IDs MUST be stored in their canonical form:

1. FieldID: lowercase hex, 32 chars
2. Hash: lowercase hex, 64 chars
3. OpID: exact recipe output
4. SchemaID/PolicyID/KernelID: as provided, validated at input

---

## 9. Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial canonical definition |

---

## Related Documents

- [`0_overview.md`](0_overview.md) - CK-0 Overview
- [`B_reference_constants.md`](B_reference_constants.md) - Reference Constants
- [`A_glossary.md`](A_glossary.md) - Glossary
