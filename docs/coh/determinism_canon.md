# Determinism Canon

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §7 (Coh Canon Specification v1.0.0)

---

## 1. Overview

This section defines the **determinism contract** — the non-negotiable rules that ensure Coh verifiers produce reproducible, replay-stable decisions. This is the "consensus safety" layer of the category.

---

## 2. Canonical Serialization

All receipts must serialize canonically under a declared profile.

### 2.1 v1 Standard

| Requirement | Description |
|------------|-------------|
| JSON Profile | Canonical JSON (RFC 8785 JCS) or frozen binary encoding |
| Text Normalization | UTF-8 NFC for all text fields |
| Key Ordering | Fixed lexicographical order (if JSON) |
| Floating Point | **Not allowed** in receipts |

### 2.2 Binary Profile (Alternative)

If not using JSON:
- Fixed-width field encoding
- Little-endian for integers
- No padding that could vary between implementations

---

## 3. Canonical Numeric Profile

Verifiers must **not** depend on IEEE-754 floating-point behavior.

### 3.1 Allowed Numeric Domains

Choose one and freeze it per object:

| Domain | Description | Use Case |
|--------|-------------|----------|
| `QFixed(p)` | Scaled integers with p decimal places | General purpose |
| Integer Rationals | numerator/denominator as bigints | Exact arithmetic |
| Interval Arithmetic | Bounded intervals over scaled integers | Bound verification (preferred) |

### 3.2 Example: QFixed

```python
class QFixed:
    """Fixed-point arithmetic with p decimal places."""
    
    def __init__(self, value: int, precision: int = 6):
        self.value = value  # Integer representing value * 10^precision
        self.precision = precision
    
    def __eq__(self, other):
        return self.value == other.value and self.precision == other.precision
    
    def __add__(self, other):
        assert self.precision == other.precision
        return QFixed(self.value + other.value, self.precision)
```

---

## 4. Deterministic Validation

A Coh verifier must satisfy:

### 4.1 Total

The verifier always returns ACCEPT or REJECT — no exceptions, no timeouts.

### 4.2 Deterministic

Same bytes → same decision. The verifier is a pure function:

```
validate(x, r, x') = ACCEPT  ⇒  same inputs always ACCEPT
validate(x, r, x') = REJECT  ⇒  same inputs always REJECT
```

### 4.3 Side-Effect Free

No:
- Randomness
- Clock/timer dependencies
- Hidden state
- Network calls

### 4.4 Implementation Pattern

```python
def validate(obj, x, receipt, x_prime):
    """
    Deterministic verifier for Coh transitions.
    
    Args:
        obj: Coh object
        x: source state
        receipt: serialized receipt bytes (canonical form)
        x_prime: target state
    
    Returns:
        bool: ACCEPT (True) or REJECT (False)
    """
    # 1. Deserialize receipt canonically
    receipt_data = deserialize_canonical(receipt)
    
    # 2. Verify schema and required fields
    if not verify_schema(receipt_data):
        return False
    
    # 3. Compute/verify potential change
    v_x = obj.potential(x)
    v_x_prime = obj.potential(x_prime)
    
    # 4. Apply budget/debt rules from receipt
    delta = receipt_data.get('delta', 0)
    budget = receipt_data.get('budget', 0)
    
    # 5. Verify inequality: V(x') ≤ V(x) - delta + budget
    if v_x_prime > v_x - delta + budget:
        return False
    
    # 6. Additional policy checks...
    
    return True
```

---

## 5. Receipt Chain Determinism

### 5.1 Trace Closure Principle

Legal steps compose into legal histories because receipts chain deterministically:

- Hash of previous receipt included in current receipt
- Schema ID frozen in each receipt
- Policy ID frozen in each receipt
- Canon profile hash included

### 5.2 Chain Digest Rule

For a chain of receipts `r₀ → r₁ → ... → rₙ`, each receipt must include:

```
chain_digest = hash(prior_receipt_hash || schema_id || policy_id || canon_profile_hash)
```

---

## 6. Nondeterminism Prohibitions

The following are **explicitly prohibited** in Coh verifiers:

| Prohibited | Reason |
|-----------|--------|
| IEEE-754 NaN comparisons | Platform-dependent |
| Float rounding modes | Varies by implementation |
| Hash map iteration order | Undefined in many languages |
| Time-dependent checks | Not reproducible |
| Random numbers | Not deterministic |

---

## 7. Proof Obligations

Every Coh implementation must provide:

### 7.1 Determinism Lemma

> **Lemma:** For all states x, receipts r, and states x', the verifier returns the same decision on repeated calls with identical inputs.

**Test:**
```python
def test_determinism(obj):
    x = ...
    r = serialize_canonical(...)
    x_prime = ...
    
    results = [obj.validate(x, r, x_prime) for _ in range(1000)]
    assert all(r == results[0] for r in results)
```

### 7.2 Closure Lemma

> **Lemma:** If step receipts are accepted in sequence, the chain digest and linkage is accepted.

**Test:**
```python
def test_closure(obj):
    trace = generate_valid_trace(obj)
    for i in range(len(trace) - 1):
        assert obj.validate(trace[i], trace.receipts[i], trace[i+1])
    # Final chain digest check
    assert verify_chain_digest(trace.receipts)
```

---

## 8. Versioning

Each Coh system must freeze:

| Field | Purpose |
|-------|---------|
| `schema_id` | Receipt schema version |
| `canon_profile_hash` | Serialization/numeric profile |
| `policy_hash` | Policy/ruleset identifier |
| `verifier_version` | Verifier implementation version |
| `serialization_version` | Serialization format version |

Any change to these produces a **new object identity** in Coh.

---

## 9. Conformance Checklist

| Requirement | Verification |
|-------------|-------------|
| Canonical JSON/binary | Test round-trip serialization |
| Fixed key ordering | Compare serialized output |
| No floats in receipts | Schema validation |
| QFixed/rationals only | Numeric type checking |
| Total verifier | Test edge cases, empty inputs |
| Deterministic | Repeated call test |
| Side-effect free | No global state, no I/O in validate |
| Chain closure | Generate and verify trace |
| Version freezing | Verify all version fields present |

---

## References

- RFC 8785: Canonical JSON
- Coh Canon Specification v1.0.0 — §7
