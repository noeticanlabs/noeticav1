# NEC Split Law

**Related:** [`5_gate_law.md`](5_gate_law.md), [`7_receipt_witness.md`](7_receipt_witness.md)

---

## 6.1 Split Trigger

### Definition 6.1: Split Condition

When gate fails:

```
gate(x, B) = FAIL
```

The batch must be split according to the split law.

### Split Trigger Conditions

| Condition | Action |
|----------|--------|
| |ε_B| > ε̂_B | Split batch |
| Batch size > max_size | Split |
| Timeout | Split |

---

## 6.2 Deterministic Split

### Definition 6.2: Lexicographic Split

Split batch B into:

```
B_1 = { o_min }
B_2 = B \ { o_min }
```

Where o_min is the lexicographically smallest operator in B.

### Lexicographic Order

Operators are ordered by their canonical ID bytes:

```
o_1 < o_2  ⇔  bytes(o_1.ID) < bytes(o_2.ID)
```

This is deterministic and replay-stable.

---

## 6.3 Recursive Split

### Algorithm

```
function split(x, B):
    if |B| == 1:
        # Singleton - cannot split further
        return SPLIT_FAILED
    
    if gate(x, B) == PASS:
        return [B]  # Already valid
    
    # Split and recurse
    o_min = lexmin(B)
    B1 = {o_min}
    B2 = B \ {o_min}
    
    result1 = split(x, B1)  # Will pass (singleton)
    result2 = split(x, B2)   # May need more splitting
    
    return result1 + result2
```

### Complexity

- Each split reduces batch size by 1
- Maximum splits = |B| - 1
- Termination guaranteed

---

## 6.4 Singleton Failure

### Definition 6.3: Singleton Failure

If a singleton operator fails the gate:

```
gate(x, {o}) = FAIL
```

This is a **terminal failure**.

### Handling

| Case | Result |
|------|--------|
| Singleton gate fails | Terminal halt |
| Hard invariant violated | Reject |
| Resource cap hit | Terminal halt |

### No Retry

Singleton failures do not retry:
- Deterministic
- Replay-stable
- Terminal

---

## 6.5 Split Receipts

### Receipt on Split

When a batch is split:

```
split_receipt = {
    original_batch: B,
    split_point: o_min,
    sub_batch_1: B1,
    sub_batch_2: B2,
    gate_result: FAIL
}
```

### No Receipts on Failed Attempt

Per NEC, failed batch attempts do NOT emit receipts:

```
if gate(x, B) == FAIL:
    # No receipt emitted
    # Split and retry sub-batches
```

Receipts only on successful commit.

---

## 6.6 Replay Stability

### Determinism Requirement

The split law must be deterministic:

- Same initial state → same split sequence
- Same final result
- Replay-verifiable

### Lexicographic Choice

Lexicographic ordering ensures:
- No random choices
- No timing dependencies
- Deterministic across implementations

---

## 6.7 Relationship to NK-2

| NK-2 Concept | NEC Split Law |
|--------------|--------------|
| Scheduler.split | Implements split law |
| Batch attempt | Gate check |
| Failure handling | Singleton → halt |
| append_log | Lex order preserved |

NK-2 scheduler implements the NEC split law.

---

## 6.8 Implementation

### Split Function

```
def split_batch(x, B):
    if len(B) == 1:
        return SPLIT_FAILED
    
    if gate(x, B):
        return [B]
    
    # Sort by canonical ID
    sorted_ops = sorted(B, key=lambda o: o.id_bytes)
    o_min = sorted_ops[0]
    
    B1 = [o_min]
    B2 = sorted_ops[1:]
    
    return split_batch(x, B1) + split_batch(x, B2)
```

### Gate Check for Singleton

```
def gate_singleton(x, o):
    # Singleton always passes if operator is valid
    # Only checks hard invariants and bounds
    return check_invariants(x, o) and check_bounds(x, o)
```
