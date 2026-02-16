# NK-1 Reference Implementation Guide

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_constants.md`](1_constants.md), [`2_debtunit.md`](2_debtunit.md)

---

## Overview

This guide provides implementation recommendations for NK-1. The specification is language-agnostic, but this guide assumes Python 3.11+ for the reference implementation.

---

## Project Structure

```
nk1/
├── __init__.py
├── pyproject.toml
├── nk1/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── debtunit.py          # DebtUnit arithmetic
│   │   ├── canon.py             # Canonicalization utilities
│   │   ├── hashchain.py         # Hash chain utilities
│   │   ├── receipt.py           # Receipt class
│   │   └── errors.py            # Custom exceptions
│   │
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── contract_set.py      # ContractSet and Contract
│   │   ├── residuals.py         # Residual function registry
│   │   ├── normalizers.py       # Sigma computation
│   │   ├── weights.py           # Weight parsing
│   │   └── violation.py         # V(x) computation
│   │
│   ├── gate/
│   │   ├── __init__.py
│   │   ├── measured_gate.py     # measured_gate.v1
│   │   ├── glb.py              # Global law bound checks
│   │   ├── service_law.py      # S(D,B) implementation
│   │   └── disturbance.py      # DP0-DP3 enforcement
│   │
│   ├── curvature/
│   │   ├── __init__.py
│   │   ├── registry.py          # CurvatureRegistry
│   │   ├── m_entry.py          # MEntry parsing
│   │   ├── matrix.py           # CurvatureMatrix
│   │   └── interactions.py     # Interaction bounds
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── encoding.py          # Canonical state bytes
│   │   └── snapshot.py         # State snapshots
│   │
│   ├── actions/
│   │   ├── __init__.py
│   │   ├── schema.json         # Action JSON schema
│   │   ├── canon_actions.py    # Canonicalization rules
│   │   └── parse.py            # Action parsing
│   │
│   └── conformance/
│       ├── __init__.py
│       ├── vectors/            # Golden vectors
│       │   ├── debtunit/
│       │   ├── vx/
│       │   ├── gate/
│       │   ├── matrix/
│       │   └── replay/
│       ├── test_debtunit.py
│       ├── test_violation.py
│       ├── test_gate.py
│       ├── test_m_entry.py
│       ├── test_matrix.py
│       └── test_replay.py
```

---

## Core Dependencies

```toml
# pyproject.toml
[project]
name = "nk1"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "pydantic>=2.0",
    "jsonschema>=4.0",
    "pycryptodome>=3.0",  # For SHA3-256
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

---

## Implementation Order

### Phase 1: Core Numeric (Days 1-2)

1. **DebtUnit class** - Exact arithmetic
2. **Canonical encoding** - String representation
3. **Hash utilities** - SHA3-256 wrapper

### Phase 2: Contracts (Days 3-4)

1. **Contract/ContractSet** - Data structures
2. **Residual registry** - Allowlisted functions
3. **Weight parsing** - Rational reduction
4. **V(x) computation** - Main algorithm

### Phase 3: Gate (Days 5-7)

1. **Service law** - S(D,B) implementation
2. **Disturbance policies** - DP0-DP3
3. **Measured gate** - Full decision logic
4. **Receipt creation** - Hash chaining

### Phase 4: Curvature (Days 8-9)

1. **M-entry parsing** - Rational_scaled.v1
2. **Matrix validation** - Symmetry, nonnegativity
3. **Registry** - Allowlist enforcement
4. **Interaction bounds** - Computation interface

### Phase 5: Actions (Days 10-11)

1. **JSON schema** - Action validation
2. **Canonicalization** - Un-wedgeable parsing
3. **Policy header** - Policy commitment

### Phase 6: Verifier (Days 12-14)

1. **Receipt parsing** - From JSON
2. **Hash chain verification** - Continuity
3. **V(x) recomputation** - Independent check
4. **Law inequality** - Full verification

### Phase 7: Conformance (Days 15-16)

1. **Golden vectors** - Expected outputs
2. **Test harness** - Run all tests
3. **CI integration** - Automated testing

---

## Key Implementation Notes

### DebtUnit: No Floats

```python
# BAD: Use floats
def from_float(value: float) -> DebtUnit:
    scaled = int(value * 1_000_000)  # Loses precision!
    return DebtUnit(scaled)

# GOOD: Use rationals
def from_rational(p: int, q: int) -> DebtUnit:
    # Exact computation
    scaled = (p * 1_000_000) // q
    return DebtUnit(scaled)
```

### Deterministic Hashing

```python
import json
import hashlib

def canonical_json(data: dict) -> bytes:
    """Serialize dict to canonical JSON bytes."""
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

def hash_bytes(data: bytes) -> str:
    """Compute SHA3-256 hash as hex string."""
    return hashlib.sha3_256(data).hexdigest()
```

### Immutable Receipts

```python
# Receipts should be immutable once created
# Use frozen dataclass
from dataclasses import dataclass

@dataclass(frozen=True)
class Receipt:
    prev_receipt_hash: str
    receipt_hash: str
    # ... other fields
```

### Error Handling

```python
class NK1Error(Exception):
    """Base exception for NK-1."""
    pass

class DebtUnitError(NK1Error):
    """DebtUnit-specific errors."""
    pass

class ContractError(NK1Error):
    """Contract-related errors."""
    pass

class GateError(NK1Error):
    """Gate decision errors."""
    pass

class VerificationError(NK1Error):
    """Verification failures."""
    pass
```

---

## Testing Strategy

### Unit Tests

```python
# test_debtunit.py
import pytest
from nk1.core.debtunit import DebtUnit

def test_addition():
    a = DebtUnit(1_000_000)  # 1.0
    b = DebtUnit(500_000)    # 0.5
    result = a + b
    assert result.int_value == 1_500_000

def test_half_even_rounding():
    # 1.5 → 2 (rounds to even)
    du = DebtUnit.from_rational(3, 2)
    assert du.int_value == 2
```

### Integration Tests

```python
# test_gate.py
def test_gate_accept():
    # Full gate test
    gate = MeasuredGate()
    result = gate.execute(gate_input)
    assert result.decision == GateDecision.ACCEPT
```

### Golden Vector Tests

```python
# test_golden.py
def test_debtunit_golden_vectors():
    for vector in load_golden_vectors("debtunit"):
        result = execute_test(vector)
        assert result == vector.expected
```

---

## Performance Considerations

### Memory

- **Receipt storage**: ~1KB per receipt
- **10K steps**: ~10MB for chain
- **Verifying 10K steps**: ~100ms on modern hardware

### Speed

- **DebtUnit ops**: ~1μs each
- **V(x) computation**: ~10μs per contract
- **Gate decision**: ~100μs
- **Full verification**: ~10ms per receipt

---

## Debugging Tips

### Enable Tracing

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("nk1")
```

### Dump Receipts

```python
# Pretty-print receipt
print(receipt.to_json(indent=2))
```

### Hash Debugging

```python
# Trace hash computation
def compute_receipt_hash(receipt: Receipt) -> str:
    data = receipt.to_canonical_bytes()
    print(f"Hash input: {data[:100]}...")
    return hash_bytes(data)
```

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|-------------|
| Float leakage | Unit tests for DebtUnit only |
| Non-deterministic ordering | Always sort dict keys |
| Mutable receipts | Use frozen dataclass |
| Hash format mismatch | Use canonical bytes |
| Missing policy IDs | Validate all policy fields |

---

## Next Steps

1. **Initialize project**: `python -m nk1 init`
2. **Run tests**: `python -m nk1 test`
3. **Build docs**: `python -m nk1 docs`
4. **Release**: `python -m nk1 release`

---

*See also: [`9_conformance.md`](9_conformance.md)*
