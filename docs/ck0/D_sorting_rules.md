# CK-0 Sorting Rules

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 (Pre-Build Tightening)

---

## Overview

This document defines mandatory sorting rules for all collections in Noetica. These rules exist to **prevent locale-aware or non-bytewise sorting** that could cause nondeterministic behavior across environments, toolchains, or platforms.

**THE RULE:** All sorting MUST be bytewise. No exceptions. No locale-aware collation. No Unicode collation algorithms.

---

## 1. Sorting Algorithm Specification

### 1.1 Core Algorithm

For all sortable collections, use **unsigned byte comparison** on the canonical encoding:

| Identifier Type | Sort By | Byte Representation |
|-----------------|---------|---------------------|
| FieldID | Decoded bytes | 16 bytes (from 32 hex chars) |
| Hash | Decoded bytes | 32 bytes (from 64 hex chars) |
| OpID | Raw UTF-8 bytes | Variable (ASCII-only per spec) |
| SchemaID | Raw UTF-8 bytes | Variable (ASCII-only per spec) |
| PolicyID | Raw UTF-8 bytes | Variable |

### 1.2 Implementation Pattern

```python
# CORRECT: Bytewise comparison
def sort_fieldids(fieldids: list[str]) -> list[str]:
    return sorted(fieldids, key=lambda f: bytes.fromhex(f))

# CORRECT: Direct string sort for ASCII-only identifiers
def sort_opids(opids: list[str]) -> list[str]:
    return sorted(opids)  # UTF-8 byte sort == string sort for ASCII

# INCORRECT: Locale-aware sorting (FORBIDDEN)
def sort_fieldids_wrong(fieldids: list[str]) -> list[str]:
    import locale
    return sorted(fieldids, key=locale.strxfrm)  # BAN THIS

# INCORRECT: Unicode collation (FORBIDDEN)
def sort_fieldids_wrong(fieldids: list[str]) -> list[str]:
    import unicodedata
    return sorted(fieldids, key=unicodedata.normalize)  # BAN THIS
```

### 1.3 Platform Requirements

- Sorting MUST produce identical results on all platforms.
- The `LC_ALL`, `LC_COLLATE`, and `LANG` environment variables MUST NOT influence sorting.
- The `PYTHONPATH` or any Python locale settings MUST NOT influence sorting.
- If your language runtime uses locale-aware sorting by default, you MUST override it.

---

## 2. Collections Requiring Sorted Ordering

### 2.1 Op Ordering (DAG Nodes)

**Location:** [`nk3/5_dag.md`](../nk3/5_dag.md)

Nodes in the DAG MUST be in **canonical lex-toposort order**:

1. Lexicographic sort by OpID (bytewise UTF-8)
2. Topological sort respecting dependencies
3. Result is deterministic and frozen

```python
# CORRECT
sorted_nodes = tuple(sorted(opids))  # Bytewise UTF-8 sort

# INCORRECT
sorted_nodes = tuple(sorted(opids, key=lambda x: x.lower()))  # BAN
```

### 2.2 Field Ordering (R/W Sets)

**Location:** [`nk3/3_kernel_registry.md`](../nk3/3_kernel_registry.md)

Static footprint R and W sets MUST be sorted arrays:

| Collection | Sort Key | Requirements |
|------------|----------|--------------|
| `R` (read set) | FieldID bytes | Sorted ascending, deduplicated |
| `W` (write set) | FieldID bytes | Sorted ascending, deduplicated |

```python
# CORRECT
R_sorted = tuple(sorted(fieldids, key=lambda f: bytes.fromhex(f)))

# INCORRECT
R_sorted = tuple(sorted(fieldids))  # String sort may differ from byte sort for hex
```

### 2.3 Receipt Key Ordering

**Location:** [`ck0/8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md)

Receipts in the Ω-ledger are ordered by:
1. `step_index` (ascending numeric)
2. For duplicate step indices: `receipt_id` UUID (bytewise)

When serializing receipt metadata (e.g., for hashing), keys MUST be sorted bytewise:

```python
# CORRECT: Bytewise key sort for JSON canonicalization
def canonicalize_receipt(receipt: dict) -> bytes:
    sorted_keys = sorted(receipt.keys())  # Bytewise UTF-8 sort
    # ... build canonical string

# INCORRECT
def canonicalize_receipt_wrong(receipt: dict) -> bytes:
    sorted_keys = sorted(receipt.keys(), key=str.lower)  # BAN
```

### 2.4 DAG Edge Ordering

**Location:** [`nk3/5_dag.md`](../nk3/5_dag.md)

Edges MUST be sorted by tuple `(src, dst, kind)` using bytewise comparison:

```python
# CORRECT
sorted_edges = tuple(sorted(edges, key=lambda e: (
    e.src.encode('utf-8'),
    e.dst.encode('utf-8'),
    e.kind.value.encode('utf-8')
)))

# INCORRECT
sorted_edges = tuple(sorted(edges, key=lambda e: (e.dst, e.src, e.kind)))  # Wrong order
```

### 2.5 KernelRegistry Ordering

**Location:** [`nk3/3_kernel_registry.md`](../nk3/3_kernel_registry.md)

The KernelRegistry entries MUST be ordered by:
1. `kernel_id` (bytewise UTF-8 sort)

For param-decidable footprints, the footprint function output MUST also be sorted:

```python
# CORRECT
R_sorted = tuple(sorted(R, key=lambda f: bytes.fromhex(f)))
W_sorted = tuple(sorted(W, key=lambda f: bytes.fromhex(f)))

# INCORRECT
R_sorted = tuple(sorted(R))  # May not match bytewise hex sort
```

---

## 3. Prohibited Patterns

### 3.1 Explicitly Banned

| Pattern | Why Banned | Detection |
|---------|------------|-----------|
| `locale.strxfrm()` | Locale-dependent | Static analysis |
| `unicodedata.normalize()` | Adds nondeterminism | Static analysis |
| `sorted(..., key=lambda x: x.lower())` | Case folding varies | Static analysis |
| `sorted(..., key=lambda x: x.casefold())` | Case folding varies | Static analysis |
| `sorted(..., cmp=locale.strcoll)` | Locale-dependent | Static analysis |
| ICU collation | Locale-dependent | Static analysis |

### 3.2 Implicitly Banned

Any sorting mechanism not explicitly documented as bytewise is implicitly banned.

---

## 4. Correct vs Incorrect Examples

### 4.1 FieldID Sorting

```python
fieldids = [
    "abc123def456789012345678901234",
    "ABC123DEF456789012345678901234",  # Note: uppercase (invalid per spec)
    "1a2b3c4d5e6f708192a3b4c5d6e7f809",
]

# CORRECT: Bytewise hex sort
sorted_ids = sorted(fieldids, key=lambda f: bytes.fromhex(f))
# Result: ["1a2b3c4d...", "abc123d...", "ABC123..."]

# INCORRECT: String sort (gives wrong order)
sorted_ids_wrong = sorted(fieldids)
# Result: ["1a2b3c4d...", "ABC123...", "abc123..."]  # WRONG

# INCORRECT: Locale sort (gives platform-dependent order)
sorted_ids_wrong = sorted(fieldids, key=locale.strxfrm)
# Result: DEPENDS ON LOCALE - BAN THIS
```

### 4.2 OpID Sorting

```python
opids = [
    "abc123:layer0/attention/query:0",
    "abc123:layer0/attention/key:1",
    "abc123:layer0/attention/query:1",
]

# CORRECT: UTF-8 byte sort (equivalent to string sort for ASCII)
sorted_ops = sorted(opids)
# Result: ["abc123:layer0/attention/key:1", 
#          "abc123:layer0/attention/query:0",
#          "abc123:layer0/attention/query:1"]

# INCORRECT: Sorting by individual components without proper encoding
sorted_ops_wrong = sorted(opids, key=lambda x: x.split(':'))
# Result: May produce inconsistent ordering - BAN THIS
```

### 4.3 DAG Edge Sorting

```python
edges = [
    DAGEdge(src="op3", dst="op1", kind="control"),
    DAGEdge(src="op1", dst="op2", kind="hazard.WAW"),
    DAGEdge(src="op1", dst="op2", kind="control"),
]

# CORRECT: Tuple sort by (src, dst, kind)
sorted_edges = sorted(edges, key=lambda e: (
    e.src.encode('utf-8'),
    e.dst.encode('utf-8'),
    e.kind.value.encode('utf-8')
))
# Result: [op1->op2(hazard), op1->op2(control), op3->op1(control)]

# INCORRECT: Only sort by source
sorted_edges_wrong = sorted(edges, key=lambda e: e.src)
# Result: Incomplete ordering - BAN THIS
```

---

## 5. Verification

### 5.1 Test Requirements

All sorting implementations MUST pass these verification checks:

1. **Determinism Test:** Sorting the same collection twice MUST produce identical results.
2. **Cross-Platform Test:** Sorting on different platforms (Linux, macOS, Windows) MUST produce identical results.
3. **Locale Independence Test:** Sorting with `LC_ALL=C`, `LC_ALL=en_US.UTF-8`, `LC_ALL=de_DE.UTF-8` MUST produce identical results.
4. **Bytewise Equivalence Test:** For string-based sorts of ASCII identifiers, the result MUST match bytewise sorting.

### 5.2 Conformance

Any implementation that uses non-bytewise sorting is a **protocol violation** and MUST be rejected by verifiers.

---

## 6. Reference Implementation

```python
from typing import TypeVar, Callable, Sequence
import heapq

T = TypeVar('T')

def bytewise_sort(items: Sequence[str], key: Callable[[str], bytes] | None = None) -> tuple[str, ...]:
    """
    Sort items bytewise. For hex-encoded identifiers, provide key to decode.
    For ASCII identifiers, key=None works because UTF-8 byte sort == string sort.
    """
    if key is None:
        # Assume ASCII-only: string sort == byte sort
        return tuple(sorted(items))
    
    return tuple(sorted(items, key=key))

def sort_fieldids_hex(fieldids: list[str]) -> tuple[str, ...]:
    """Sort FieldIDs by decoded hex bytes."""
    return bytewise_sort(fieldids, key=lambda f: bytes.fromhex(f))

def sort_hashes_hex(hashes: list[str]) -> tuple[str, ...]:
    """Sort Hashes by decoded hex bytes."""
    return bytewise_sort(hashes, key=lambda h: bytes.fromhex(h))

def sort_opids(opids: list[str]) -> tuple[str, ...]:
    """Sort OpIDs by UTF-8 bytes (ASCII-only, so string sort works)."""
    return bytewise_sort(opids)  # No key needed for ASCII

def sort_dag_edges(edges: list[tuple[str, str, str]]) -> tuple[tuple[str, str, str], ...]:
    """Sort DAG edges by (src, dst, kind) using bytewise comparison."""
    return tuple(sorted(edges, key=lambda e: (
        e[0].encode('utf-8'),
        e[1].encode('utf-8'),
        e[2].encode('utf-8')
    )))
```

---

## Summary

| Collection | Sort Key | Implementation |
|------------|----------|-----------------|
| OpIDs | UTF-8 bytes | `sorted(opids)` |
| FieldIDs | Hex-decoded bytes | `sorted(fieldids, key=bytes.fromhex)` |
| Hashes | Hex-decoded bytes | `sorted(hashes, key=bytes.fromhex)` |
| DAG edges | (src, dst, kind) as UTF-8 bytes | Tuple sort with `.encode('utf-8')` |
| Receipt keys | UTF-8 bytes | `sorted(keys)` |
| KernelRegistry | kernel_id UTF-8 bytes | `sorted(entries, key=lambda e: e.kernel_id)` |

**There is no exception to bytewise sorting. Any locale-aware, Unicode-collated, or case-folding sort is a protocol violation.**
