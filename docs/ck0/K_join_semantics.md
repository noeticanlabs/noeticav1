# CK-0 Join Op Semantics

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 Pre-Build Tightening  
**Related:** [`0_overview.md`](0_overview.md), [`6_transition_contract.md`](6_transition_contract.md), [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md)

---

## 1. Purpose

This document establishes the canonical semantics for the `op.join.v1` operator. These semantics are locked for Phase 0 and shall not be modified without explicit version bump to v2.0. All claims herein are stated with sufficient rigor to withstand adversarial review.

---

## 2. Formal Definition

### 2.1 Operator Identity

```
op.join.v1 : OperationID
```

- **OpID Format:** `join:<deterministic_hash>` where the hash is computed over the join's control-flow context
- **Version:** v1 (canonical)
- **Classification:** Explicit control-flow join barrier

---

## 3. Semantics Properties

### 3.1 Local Receipt Emission: YES

**Theorem.** Every execution of `op.join.v1` emits a local receipt.

**Proof.** By definition, `op.join.v1` is an explicit barrier operation in the scheduling DAG. The CK-0 receipt schema (see [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md)) mandates that every operation participating in the DAG transition from step `k` to `k+1` must produce a receipt. Join nodes are explicitly inserted into the DAG (per NK-3 v1.0 join insertion rules). Therefore, by structural induction on DAG construction, `op.join.v1` emits a receipt.

**Corollaries:**
- The receipt includes `state_before` and `state_after` hashes
- The receipt includes the `op_id` field with value `join:<hash>`
- The receipt participates in the Ω-ledger hash chain

---

### 3.2 Participates in Scheduling DAG: YES

**Theorem.** `op.join.v1` is a first-class node in the NK-3 v1.0 scheduling DAG.

**Proof.** The NK-3 DAG specification (see [`nk3/5_dag.md`](nk3/5_dag.md)) defines node types as any operation with a valid OpID. Join nodes are explicitly constructed via the join insertion algorithm (see [`nk3/8_hazard_control.md`](nk3/8_hazard_control.md) Section 3.3). The algorithm adds join nodes to `dag.nodes` and adds explicit control edges from predecessor branch nodes to the join node.

**DAG Properties:**
- Node type: `control.explicit` barrier
- Incoming edges: From all predecessor branches (e.g., then-branch, else-branch of IF construct)
- Outgoing edges: To subsequent operations in the control flow
- Toposort position: After all predecessors complete, before any successor executes

---

### 3.3 Has State Effect: NO (W = ∅)

**Definition.** The write set `W` of an operation is the set of state fields modified by its execution.

**Theorem.** For `op.join.v1`, `W = ∅`.

**Proof.** Join nodes are explicit synchronization barriers, not state-modifying operations. Per the JoinNode definition in NK-3 v1.0:

```python
@dataclass(frozen=True)
class JoinNode:
    op_id: str          # "join:" + hash
    R: tuple = ()       # Empty read set
    W: tuple = ()       # Empty write set  ← DEFINITIVE
    block_index: bool = False
    float_touch: bool = False
    delta_bound: None = None
    requires_modeD: bool = False
```

The write set is explicitly declared as the empty tuple. This is not an implementation detail—it is a semantic invariant. Any implementation that permits `op.join.v1` to modify state is NON-CONFORMANT to NK-3 v1.0.

**Implications:**
- `op.join.v1` does not contribute to violation functional computation
- State hash before and after join must be identical: `H(state_before) = H(state_after)`
- The receipt fields `debt_before`, `debt_after`, `budget`, `service_applied` remain unchanged across the join

---

### 3.4 Never Removed by NK-3 v1.0 (No Optimization Clause)

**Theorem.** `op.join.v1` nodes are invariant under all NK-3 v1.0 optimization passes.

**Proof.** NK-3 v1.0 operates under the following constraints:
1. **No hidden quantifiers** (Section 4.1 of [`nk3/8_hazard_control.md`](nk3/8_hazard_control.md)): All edges must be explicitly constructed from NSC constructs
2. **Explicit join insertion** (Section 3.1): Join nodes are REQUIRED when NSC contains control-flow joins (IF, SEQ with branches, nested conditionals)
3. **Deterministic lowering** (Section 5.1 of [`nk3/6_execplan.md`](nk3/6_execplan.md)): No optimization passes may remove or merge join barriers

The join node is the sole enforcement mechanism for control-flow synchronization. Removing it would violate the explicit control dependency semantics, breaking the DAG's acyclic guarantee. Therefore, NK-3 v1.0 explicitly forbids join node elimination.

**No-Optimization Clause (Formal):**

```
∀ dag ∈ DAGs_v1.0, ∀ join ∈ dag.nodes where join.op_id.starts_with("join:"):
    join ∈ dag.nodes'  where dag' = NK3_v1.0_optimize(dag)
```

---

### 3.5 Has Deterministic Input Semantics (Waits for All Predecessors)

**Theorem.** `op.join.v1` exhibits deterministic input semantics: it waits for ALL predecessor operations to complete before firing.

**Proof.** The join node semantics are defined by the control edges entering it:

1. **Explicit construction:** Join nodes are created only when NSC constructs require synchronization (IF, SEQ branches, nested conditionals)
2. **Control edge binding:** For each predecessor branch, an edge of kind `control.explicit` is added:
   ```python
   DAGEdge(src=branch.op_id, dst=join.op_id, kind="control.explicit")
   ```
3. **Scheduling constraint:** The NK-3 scheduler (see [`nk3/3_scheduler.md`](nk3/3_scheduler.md)) enforces that a node may execute only after ALL its incoming edges have been satisfied
4. **Determinism:** Since edges are explicitly enumerated and the scheduler uses deterministic toposort (lex-toposort per [`nk3/5_dag.md`](nk3/5_dag.md) Section 1.2), the join's firing time is deterministic

**Formal Semantics:**

```
let preds(join) = { n ∈ dag.nodes | ∃ e ∈ dag.edges where e.dst = join.op_id }
join_ready(join, executed) ↔ ∀ n ∈ preds(join): n ∈ executed
execute(join) ↔ join_ready(join, executed) ∧ time = max(time(n) for n ∈ preds(join)) + ε
```

The `+ ε` represents the minimal scheduling delay after the last predecessor completes, ensuring deterministic ordering.

---

## 4. Receipt Schema for op.join.v1

```json
{
  "receipt_version": 1,
  "receipt_id": "uuid-v4",
  "step_index": 42,
  "op_id": "join:abc123...",
  "op_type": "op.join.v1",
  
  "state_before": "hash_same",
  "state_after": "hash_same",
  
  "R": [],
  "W": [],
  
  "predecessor_count": 2,
  "predecessor_op_ids": ["then_branch:xyz", "else_branch:uvw"],
  
  "dag_digest": "...",
  
  "law_satisfied": true,
  "invariant_status": "pass"
}
```

**Note:** For join operations, `state_before` and `state_after` hashes MUST be identical, as `W = ∅`.

---

## 5. Conformance Claims

| Property | Claim | Evidence |
|----------|-------|----------|
| Local receipt emission | YES | DAG participation + receipt schema |
| DAG participation | YES | Explicit node in NK-3 DAG |
| State effect | NO (W=∅) | JoinNode definition, empty W set |
| NK-3 v1.0 optimization | NEVER removed | No-optimization clause, explicit construct |
| Deterministic input | YES | Explicit control edges, deterministic toposort |

---

## 6. Invariant Violations (Non-Conformant Cases)

The following are DEFINITIVE violations of `op.join.v1` semantics:

1. **Join node not in DAG:** Any implementation that omits join nodes from the scheduling DAG
2. **Non-empty write set:** Any join node with `W ≠ ∅`
3. **Implicit edge creation:** Any join node where predecessor edges are not explicitly `control.explicit`
4. **Early firing:** Any scheduler that permits join execution before ALL predecessors complete
5. **Receipt omission:** Any execution path that does not emit a receipt for join execution

---

## 7. Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-02-17 | Initial canonical specification |
