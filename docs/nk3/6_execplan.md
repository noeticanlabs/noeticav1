# NK-3 ExecPlan v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`2_canon_outputs.md`](2_canon_outputs.md), [`../nk2/1_exec_plan.md`](../nk2/1_exec_plan.md)

---

## Overview

This document defines the ExecPlan v1 artifact. The ExecPlan is a policy-bound execution plan that NK-2 uses to schedule and execute operations.

---

## 1. ExecPlan Schema

### 1.1 Definition

```python
@dataclass(frozen=True)
class ExecPlan:
    """Policy-bound execution plan for NK-2."""
    
    # Core identifiers
    plan_id: str
    policy_bundle_id: PolicyID
    policy_digest: Hash256
    kernel_registry_digest: Hash256
    
    # Operation references
    opset_digest: Hash256
    dag_digest: Hash256
    
    # Scheduler configuration
    scheduler_rule_id: str          # "greedy.curv.v1"
    scheduler_mode_default: str     # "id:mode.S" or "id:mode.D"
    max_parallel_width_P: int
    
    # Tensor policy
    tensor_policy_id: str
    
    # Resource caps (v1.0 deterministic halt)
    resource_cap_mode_id: str
    
    # Control modes (explicit constructs only)
    join_mode: str
    control_mode: str
    
    # Toolchain
    toolchain_ids: tuple[str, ...]
    
    # No optimization clause
    no_optimization_clause: bool = True
    
    # Digest
    execplan_digest: Hash256
    
    @staticmethod
    def create(...) -> ExecPlan:
        """Create ExecPlan with all required fields."""
        # ... implementation
```

### 1.2 Required Fields

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| `plan_id` | str | Unique plan identifier | Must be deterministic |
| `policy_bundle_id` | PolicyID | Policy bundle reference | Must match allowlist |
| `policy_digest` | Hash256 | Policy digest | Chain-locked |
| `kernel_registry_digest` | Hash256 | Registry digest | Chain-locked |
| `opset_digest` | Hash256 | OpSet reference | Must match OpSet |
| `dag_digest` | Hash256 | DAG reference | Must match DAG |
| `scheduler_rule_id` | str | Scheduler identifier | Must be "greedy.curv.v1" |
| `scheduler_mode_default` | str | Default mode | "id:mode.S" or "id:mode.D" |
| `max_parallel_width_P` | int | Max batch width | Must respect policy |
| `tensor_policy_id` | str | Tensor policy | Policy-bound |
| `resource_cap_mode_id` | str | Resource cap mode | v1.0 deterministic |
| `join_mode` | str | Join handling | Explicit only |
| `control_mode` | str | Control handling | Explicit only |
| `toolchain_ids` | tuple[str] | Toolchain versions | Immutable |
| `no_optimization_clause` | bool | No optimization flag | Must be true |

---

## 2. Scheduler Configuration

### 2.1 Scheduler Rule ID

| Value | Description |
|-------|-------------|
| `greedy.curv.v1` | Greedy curvature-aware scheduler |

### 2.2 Scheduler Mode Default

| Value | Description |
|-------|-------------|
| `id:mode.S` | Static mode (default) |
| `id:mode.D` | Dynamic mode |

### 2.3 Mode Consistency

The default scheduler mode must be consistent with any `requires_modeD` flags in OpSet:
- If any op has `requires_modeD = true`, default must be `id:mode.D`
- Or scheduler must handle mode switching dynamically

---

## 3. Policy Binding

### 3.1 Policy Digest

The ExecPlan must bind the policy digest:

```
policy_digest = H_R(policy_bundle_bytes)
```

### 3.2 Allowlist Verification

NK-3 must verify:
- `policy_digest` is in the allowlist
- `kernel_registry_digest` is in the allowlist

---

## 4. Resource Caps

### 4.1 Resource Cap Mode ID

| Value | Description |
|-------|-------------|
| `deterministic_halt.v1` | Halt on cap violation |

### 4.2 Cap Rules

v1.0 resource caps are deterministic:
- No probabilistic early termination
- Hard caps enforced strictly

---

## 5. Control Modes

### 5.1 Join Mode

| Value | Description |
|-------|-------------|
| `explicit.v1` | Only explicit join barriers |

### 5.2 Control Mode

| Value | Description |
|-------|-------------|
| `explicit.v1` | Only explicit control edges |

---

## 6. No Optimization Clause

### 6.1 v1.0 Rule

NK-3 v1.0 performs **no semantic transformations** beyond:
- Canonical NSC normalization (already in NSC.v1)
- Deterministic lowering into OpSpecs
- Deterministic hazard/control edge construction
- Deterministic join barrier insertion

### 6.2 Flag Value

| Field | Value | Meaning |
|-------|-------|---------|
| `no_optimization_clause` | `true` | No optimization performed |

---

## 7. Validation Rules

### 7.1 Static Checks

| Check | Description |
|-------|-------------|
| Policy digest valid | In allowlist |
| Registry digest valid | In allowlist |
| Scheduler rule valid | Must be "greedy.curv.v1" |
| Mode consistent | With requires_modeD flags |
| Max width valid | Positive integer, respects policy |
| No optimization | Must be true |

### 7.2 Rejection Criteria

| Reason | Description |
|--------|-------------|
| Policy digest unknown | Not in allowlist |
| Registry digest unknown | Not in allowlist |
| Invalid scheduler | Unknown scheduler_rule_id |
| Mode inconsistency | Conflicts with requires_modeD |
| Invalid width | Negative or exceeds policy |

---

## 8. Example ExecPlan

### 8.1 Example

```json
{
  "plan_id": "plan:abc123...",
  "policy_bundle_id": "nk1.policy.standard.v1",
  "policy_digest": "sha256:policy123...",
  "kernel_registry_digest": "sha256:registry456...",
  "opset_digest": "sha256:opset789...",
  "dag_digest": "sha256:dag012...",
  "scheduler_rule_id": "greedy.curv.v1",
  "scheduler_mode_default": "id:mode.S",
  "max_parallel_width_P": 4,
  "tensor_policy_id": "tensor.standard.v1",
  "resource_cap_mode_id": "deterministic_halt.v1",
  "join_mode": "explicit.v1",
  "control_mode": "explicit.v1",
  "toolchain_ids": ["parser:1.0", "typechecker:1.0", "lowerer:1.0"],
  "no_optimization_clause": true
}
```
