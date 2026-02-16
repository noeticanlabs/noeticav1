# NK-2 ExecPlan + OpSpec Runtime Input

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`../nk1/3_contracts.md`](../nk1/3_contracts.md)

---

## Overview

This document defines the **deterministic job spec** that NK-2 executes. The ExecPlan and OpSpec structures contain all information needed for deterministic execution, receipt reconstruction, and verification.

---

## 1. ExecPlan (Runtime Input)

The ExecPlan is the canonical job specification that NK-2 executes. It must be deterministic and hashable.

### 1.1 ExecPlan Schema

```python
@dataclass(frozen=True)
class ExecPlan:
    """Deterministic job spec for NK-2 runtime."""
    
    # Core identifiers
    plan_id: OpID                    # Unique plan identifier
    policy_bundle_id: PolicyID        # Policy bundle reference
    policy_digest: Hash256           # Chain-locked policy digest
    
    # State anchor
    initial_state_hash: Hash256      # Must match chain state
    
    # Operation universe
    ops: tuple[OpSpec, ...]          # Immutable tuple for hashability
    dag_edges: tuple[tuple[OpID, OpID], ...]  # (a, b) means a ≺ b
    
    # Scheduler configuration
    max_parallel_width_P: int        # Must respect policy caps
    scheduler_rule_id: str           # "greedy.curv.v1"
    scheduler_mode: str               # "id:mode.S" or "id:mode.D"
    
    # Resource constraints (policy-locked)
    resource_caps: ResourceCaps      # Immutable resource limits
    
    # Execution policy
    abort_on_kernel_error: bool = True  # Policy-locked
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation for hashing."""
        parts = [
            self.plan_id.encode('utf-8'),
            self.policy_bundle_id.encode('utf-8'),
            self.policy_digest.bytes,
            self.initial_state_hash.bytes,
            b''.join(op.canonical_bytes() for op in sorted(self.ops, key=lambda o: o.op_id)),
            b''.join(a.encode('utf-8') + b.encode('utf-8') for a, b in sorted(self.dag_edges)),
            str(self.max_parallel_width_P).encode('utf-8'),
            self.scheduler_rule_id.encode('utf-8'),
            self.scheduler_mode.encode('utf-8'),
            self.resource_caps.canonical_bytes(),
        ]
        return b'||'.join(parts)
    
    def hash(self) -> Hash256:
        """Hash of canonical representation."""
        return Hash256(sha256(self.canonical_bytes()))
```

### 1.2 Required Fields

| Field | Type | Description | Determinism Rule |
|-------|------|-------------|------------------|
| `plan_id` | OpID | Unique identifier | Must be pre-determined |
| `policy_bundle_id` | PolicyID | Policy bundle reference | Must match allowlist |
| `policy_digest` | Hash256 | Chain-locked digest | Must be constant chain-wide |
| `initial_state_hash` | Hash256 | State anchor | Must match actual state |
| `ops` | list[OpSpec] | Operation universe | Must be canonically ordered |
| `dag_edges` | list[(OpID, OpID)] | Precedence constraints | Must be sorted |
| `max_parallel_width_P` | Int | Max batch width | Must respect policy |
| `scheduler_rule_id` | str | Scheduler identifier | Must be "greedy.curv.v1" |
| `scheduler_mode` | str | Mode (S or D) | Must be valid mode ID |
| `resource_caps` | ResourceCaps | Resource limits | Must be policy-locked |
| `abort_on_kernel_error` | bool | Error handling | Must be true (policy-locked) |

### 1.3 Determinism Rules

1. **Canonicalization**: ExecPlan must be canonicalized before hashing
2. **Hash stability**: Same ExecPlan + same initial state → identical hashes
3. **No improvisation**: NK-2 may only use contents of ExecPlan + state values

---

## 2. OpSpec (Per-Operation)

Each operation in the ExecPlan must include all fields needed for receipt reconstruction and verification.

### 2.1 OpSpec Schema

```python
@dataclass(frozen=True)
class OpSpec:
    """Per-operation specification for NK-2."""
    
    # Core identifiers
    op_id: OpID                      # Unique operation identifier
    kernel_hash: Hash256             # Kernel code hash
    footprint_digest: Hash256        # Memory footprint hash
    
    # Read/Write sets (for conflict detection)
    R_o: frozenset[FieldID]         # Read fields
    W_o: frozenset[FieldID]         # Write fields
    
    # Block and bounds
    block_index: int                 # = i(o), curvature matrix index
    delta_bound_a: DebtUnit          # = a_o, max δ-norm
    
    # Mode constraints
    requires_modeD: bool             # True if any non-numeric write
    float_touch: bool                # True if float-policy affects this op
    
    # Kernel type
    glb_mode_id: str                 # "id:kernel_type_erasure.v1"
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation."""
        return b'||'.join([
            self.op_id.encode('utf-8'),
            self.kernel_hash.bytes,
            self.footprint_digest.bytes,
            b','.join(sorted(f.encode('utf-8') for f in self.R_o)),
            b','.join(sorted(f.encode('utf-8') for f in self.W_o)),
            str(self.block_index).encode('utf-8'),
            str(self.delta_bound_a).encode('utf-8'),
            str(self.requires_modeD).encode('utf-8'),
            str(self.float_touch).encode('utf-8'),
            self.glb_mode_id.encode('utf-8'),
        ])
```

### 2.2 Required Fields

| Field | Type | Description | Purpose |
|-------|------|-------------|---------|
| `op_id` | OpID | Unique identifier | Receipt binding |
| `kernel_hash` | Hash256 | Kernel code hash | Verification |
| `footprint_digest` | Hash256 | Memory footprint | Receipt reconstruction |
| `R_o` | set[FieldID] | Read fields | Conflict detection |
| `W_o` | set[FieldID] | Write fields | Conflict detection |
| `block_index` | Int | Curvature index | ε̂ computation |
| `delta_bound_a` | DebtUnit | δ-bound | Numeric check |
| `requires_modeD` | bool | Mode requirement | Batch mode decision |
| `float_touch` | bool | Float policy flag | Policy veto check |
| `glb_mode_id` | str | Kernel type | Must match bundle |

### 2.3 Field Set Properties

For any valid OpSpec:

```
1. R_o ∩ W_o = ∅  (no self-conflict)
2. block_index ∈ ℤ≥0
3. delta_bound_a > 0
```

---

## 3. ResourceCaps

Policy-locked resource constraints that cannot be exceeded.

### 3.1 ResourceCaps Schema

```python
@dataclass(frozen=True)
class ResourceCaps:
    """Immutable resource limits (policy-locked)."""
    
    max_bigint_bits: int             # Maximum BigInt bit length
    max_matrix_accum_terms: int      # Maximum matrix accumulation terms
    max_fields_touched_per_op: int   # Maximum fields per operation
    max_v_eval_cost: int             # Maximum V(x) evaluation cost
    max_batch_size_p: int | None     # Optional chain-locked batch size
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation."""
        return b'||'.join([
            b'max_bigint_bits:' + str(self.max_bigint_bits).encode('utf-8'),
            b'max_matrix_accum_terms:' + str(self.max_matrix_accum_terms).encode('utf-8'),
            b'max_fields_touched_per_op:' + str(self.max_fields_touched_per_op).encode('utf-8'),
            b'max_v_eval_cost:' + str(self.max_v_eval_cost).encode('utf-8'),
            (b'max_batch_size_p:' + str(self.max_batch_size_p).encode('utf-8')) if self.max_batch_size_p else b'max_batch_size_p:unlimited',
        ])
    
    def check(self, resource: str, value: int) -> bool:
        """Check if resource usage is within caps."""
        caps_map = {
            'bigint_bits': self.max_bigint_bits,
            'matrix_accum_terms': self.max_matrix_accum_terms,
            'fields_touched': self.max_fields_touched_per_op,
            'v_eval_cost': self.max_v_eval_cost,
            'batch_size': self.max_batch_size_p or float('inf'),
        }
        return value <= caps_map.get(resource, float('inf'))
```

---

## 4. Type Definitions

### 4.1 Core Type Aliases

```python
# Operation identifiers
OpID = str                          # e.g., "id:op.increment.001"
PolicyID = str                      # e.g., "id:policy.standard.v1"
FieldID = str                       # e.g., "id:field.balance"
Hash256 = bytes                     # 32-byte SHA-256 hash

# Numeric types (from NK-1)
DebtUnit = int                      # Exact integer in DebtUnit space
```

### 4.2 Scheduler Mode IDs

| Mode ID | Description |
|---------|-------------|
| `id:mode.S` | Single-precision mode (default) |
| `id:mode.D` | Double-precision mode (measured gate required) |

### 4.3 Scheduler Rule IDs

| Rule ID | Description |
|---------|-------------|
| `greedy.curv.v1` | Canonical greedy curvature-aware scheduler |

---

## 5. Validation Rules

### 5.1 ExecPlan Validation

```python
def validate_exec_plan(plan: ExecPlan, policy_bundle: PolicyBundle) -> ValidationResult:
    """Validate ExecPlan against policy bundle."""
    errors = []
    
    # 1. Check policy digest matches
    if plan.policy_digest != policy_bundle.digest:
        errors.append("policy_digest_mismatch")
    
    # 2. Check scheduler rule is allowlisted
    if plan.scheduler_rule_id not in policy_bundle.allowed_scheduler_rules:
        errors.append("scheduler_rule_not_allowlisted")
    
    # 3. Check max_parallel_width respects policy
    if plan.max_parallel_width_P > policy_bundle.max_parallel_width:
        errors.append("max_parallel_width_exceeds_policy")
    
    # 4. Check DAG is acyclic
    if not is_dag(plan.dag_edges):
        errors.append("dag_has_cycles")
    
    # 5. Check all ops reference valid block indices
    max_block = max(op.block_index for op in plan.ops)
    if max_block >= policy_bundle.curvature_matrix_size:
        errors.append("block_index_out_of_bounds")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 5.2 OpSpec Validation

```python
def validate_op_spec(op: OpSpec, policy_bundle: PolicyBundle) -> ValidationResult:
    """Validate OpSpec against policy bundle."""
    errors = []
    
    # 1. Check kernel_hash is allowlisted
    if op.kernel_hash not in policy_bundle.allowed_kernel_hashes:
        errors.append("kernel_hash_not_allowlisted")
    
    # 2. Check glb_mode_id matches bundle
    if op.glb_mode_id != policy_bundle.glb_mode_id:
        errors.append("glb_mode_id_mismatch")
    
    # 3. Check delta_bound is positive
    if op.delta_bound_a <= 0:
        errors.append("delta_bound_must_be_positive")
    
    # 4. Check read/write sets are disjoint
    if op.R_o & op.W_o:
        errors.append("read_write_sets_must_be_disjoint")
    
    # 5. Check float_touch policy
    if op.float_touch and not policy_bundle.float_policy_allows_tensor:
        errors.append("float_policy_restricts_tensor")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
```

---

## 6. Canonical Ordering

All sets that become sequences must be **sorted by op_id bytes** for determinism.

```python
def canonical_order(ops: list[OpSpec]) -> list[OpSpec]:
    """Return ops in canonical (sorted) order."""
    return sorted(ops, key=lambda o: o.op_id.encode('utf-8'))

def canonical_order_edges(edges: list[tuple[OpID, OpID]]) -> list[tuple[OpID, OpID]]:
    """Return edges in canonical (sorted) order."""
    return sorted(edges, key=lambda e: (e[0].encode('utf-8'), e[1].encode('utf-8')))
```

---

## 7. Example ExecPlan

```python
example_plan = ExecPlan(
    plan_id="id:plan.payment.001",
    policy_bundle_id="id:policy.standard.v1",
    policy_digest=Hash256(sha256(b"policy_content")),
    initial_state_hash=Hash256(sha256(b"initial_state")),
    ops=(
        OpSpec(
            op_id="id:op.transfer.001",
            kernel_hash=Hash256(sha256(b"kernel_transfer")),
            footprint_digest=Hash256(sha256(b"footprint_transfer")),
            R_o=frozenset({"id:field.balance", "id:field.limit"}),
            W_o=frozenset({"id:field.balance"}),
            block_index=0,
            delta_bound_a=DebtUnit(1000),
            requires_modeD=False,
            float_touch=False,
            glb_mode_id="id:kernel_type_erasure.v1",
        ),
        OpSpec(
            op_id="id:op.validate.001",
            kernel_hash=Hash256(sha256(b"kernel_validate")),
            footprint_digest=Hash256(sha256(b"footprint_validate")),
            R_o=frozenset({"id:field.balance", "id:field.limit"}),
            W_o=frozenset({"id:field.status"}),
            block_index=1,
            delta_bound_a=DebtUnit(100),
            requires_modeD=False,
            float_touch=False,
            glb_mode_id="id:kernel_type_erasure.v1",
        ),
    ),
    dag_edges=(
        ("id:op.transfer.001", "id:op.validate.001"),  # transfer ≺ validate
    ),
    max_parallel_width_P=4,
    scheduler_rule_id="greedy.curv.v1",
    scheduler_mode="id:mode.S",
    resource_caps=ResourceCaps(
        max_bigint_bits=4096,
        max_matrix_accum_terms=10000,
        max_fields_touched_per_op=100,
        max_v_eval_cost=1000000,
        max_batch_size_p=None,
    ),
    abort_on_kernel_error=True,
)
```
