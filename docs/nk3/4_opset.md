# NK-3 OpSet v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`2_canon_outputs.md`](2_canon_outputs.md), [`../nk2/1_exec_plan.md`](../nk2/1_exec_plan.md)

---

## Overview

This document defines the OpSet v1 artifact. The OpSet is a deterministic list of OpSpecs sorted by op_id.

---

## 1. OpSet Schema

### 1.1 Definition

```python
@dataclass(frozen=True)
class OpSet:
    """Deterministic operation set for NK-2."""
    
    ops: tuple[OpSpec, ...]  # Sorted by op_id
    opset_digest: Hash256
    
    @staticmethod
    def from_ops(ops: list[OpSpec]) -> OpSet:
        """Create OpSet from list of ops."""
        sorted_ops = tuple(sorted(ops, key=lambda o: o.op_id))
        return OpSet(
            ops=sorted_ops,
            opset_digest=Hash256(sha256(OpSet._canonical_bytes(sorted_ops)))
        )
    
    @staticmethod
    def _canonical_bytes(ops: tuple[OpSpec, ...]) -> bytes:
        """Produce canonical byte representation."""
        return b''.join(op.canonical_bytes() for op in ops)
```

### 1.2 Ordering Rule

Ops must be sorted by `op_id` bytes (lexicographic, ascending).

---

## 2. OpSpec

### 2.1 OpSpec Schema

```python
@dataclass(frozen=True)
class OpSpec:
    """Single operation specification."""
    
    op_id: OpID              # Hygienic, deterministic
    kernel_id: KernelID      # Reference to kernel
    kernel_hash: Hash256     # Hash of kernel implementation
    op_params: ValueCanon    # Parameters (canonical form)
    R: tuple[FieldID, ...]  # Read set (sorted, deduped)
    W: tuple[FieldID, ...]  # Write set (sorted, deduped)
    block_index: bool        # Uses block indexing
    float_touch: bool        # Touches floating-point
    delta_bound: DebtUnit | None  # Delta bound (None = not_applicable)
    requires_modeD: bool     # Requires D mode execution
```

### 2.2 Required Fields

| Field | Type | Description | Determinism Rule |
|-------|------|-------------|------------------|
| `op_id` | OpID | Unique operation identifier | Derived deterministically |
| `kernel_id` | KernelID | Kernel reference | Must exist in registry |
| `kernel_hash` | Hash256 | Kernel hash | Must match registry |
| `op_params` | ValueCanon | Parameters | Canonical form only |
| `R` | tuple[FieldID] | Read set | Sorted + deduped |
| `W` | tuple[FieldID] | Write set | Sorted + deduped |
| `block_index` | bool | Block indexing | From kernel spec |
| `float_touch` | bool | Float touching | From kernel spec |
| `delta_bound` | DebtUnit \| None | Delta bound | Computed or N/A |
| `requires_modeD` | bool | Requires D mode | Computed from policy |

---

## 3. OpID Derivation

### 3.1 Derivation Algorithm

Recommended v1.0 formula:

```
op_id := "op:" + hex(SHA256(program_nsc_digest | node_path | binder_index))
```

### 3.2 Requirements

| Requirement | Description |
|-------------|-------------|
| No human names | Derivation must be algorithmic |
| Collision-resistant | Use SHA256 or equivalent |
| Source-bound | Include NSC source path |

### 3.3 Canonical Form

OpID must be:
- Valid UTF-8 string
- Prefix `"op:"` to distinguish from other IDs
- Hex-encoded to avoid special characters

---

## 4. OpSpec Canonicalization

### 4.1 Parameter Canonicalization

`op_params` must be in ValueCanon form:

| Type | Rule |
|------|------|
| Numbers | Integer (DebtUnit) only |
| Strings | UTF-8, no special chars in key position |
| Arrays | Sorted if set semantics |
| Maps | Sorted key-value pairs |

### 4.2 Read/Write Set Canonicalization

R and W sets must be:
- Sorted lexicographically by FieldID
- Deduplicated
- Represented as arrays (not objects)

---

## 5. Delta Bound Computation

### 5.1 Delta Bound Modes

| Mode | Description |
|------|-------------|
| `additive` | Delta bound = sum of field weights |
| `multiplicative` | Delta bound = product of factors |
| `not_applicable` | No delta bound available |

### 5.2 Computation Rules

From kernel spec:
1. If `delta_bound_mode = not_applicable`: set `delta_bound = None`
2. Otherwise: compute bound using kernel's bound function

---

## 6. requires_modeD Propagation

### 6.1 Conditions

An op must have `requires_modeD = true` if ANY of:

| Condition | Description |
|-----------|-------------|
| Non-numeric writes | op writes any non-numeric field |
| Delta bound N/A | `delta_bound_mode = not_applicable` |
| Policy veto | Policy forbids static bounds for op class |
| Float touch | Kernel has `float_touch=true` and tensor policy requires D |

### 6.2 Propagation Algorithm

```python
def compute_requires_modeD(op: OpSpec, policy: PolicyBundle) -> bool:
    """Compute requires_modeD flag."""
    
    # Check non-numeric writes
    for field in op.W:
        if not is_numeric_field(field):
            return True
    
    # Check delta bound
    if op.delta_bound is None:
        return True
    
    # Check policy
    if policy.forbids_static_bounds(op.kernel_id):
        return True
    
    # Check float touch
    if op.float_touch and policy.tensor_requires_D():
        return True
    
    return False
```

---

## 7. Validation Rules

### 7.1 Static Checks

| Check | Description |
|-------|-------------|
| R/W sets sorted | Lexicographic by FieldID |
| R/W sets deduped | No duplicate FieldIDs |
| Kernel exists | kernel_id in registry |
| Kernel hash match | kernel_hash matches registry |
| Delta bound valid | DebtUnit or None |
| Mode flag valid | Boolean |

### 7.2 Rejection Criteria

| Reason | Description |
|--------|-------------|
| Unknown kernel | kernel_id not in registry |
| Hash mismatch | kernel_hash != registry[kernel_id] |
| Duplicate op_id | Collision in op_id derivation |
| Invalid params | op_params fails schema validation |
