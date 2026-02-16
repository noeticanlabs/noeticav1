# NK-2 Runtime Exec + Scheduler Core v1.0

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`../nk1/0_overview.md`](../nk1/0_overview.md), [`../ck0/0_overview.md`](../ck0/0_overview.md)

---

## Overview

NK-2 defines **how work gets executed** on top of NK-1 (state/receipt/norm/gate/matrix/policy bundle) and NEC (theory layer):

* How ops become **Ready**
* How Ready ops become **batches**
* How batches are **attempted**
* How failures trigger **deterministic rescheduling**
* How the system **halts** (singleton failures, policy veto, resource caps)
* How the system stays **replay-stable** (no attempt receipts in v1.0)
* How the output is a **commit chain** consistent with NEC + NK-1

NK-2 is a *runtime* module. It does **not** define Noetica syntax or lowering (that's NK-3). It assumes you already have an OpDAG + per-op contracts.

---

## Mission

NK-2 provides:

| Capability | Description |
|------------|-------------|
| **Deterministic Scheduling** | Greedy curvature-aware batching with no improvisation |
| **Deterministic Batching** | Conflict detection + mode constraints |
| **Deterministic Gating** | epsilon_measured ≤ epsilon_hat verification |
| **Deterministic Failure Recovery** | Split lexmin + removal transforms |
| **Deterministic Halting** | Resource caps + singleton terminal rules |
| **Replay Stability** | No attempt receipts - only successful commits |

---

## Scope

```
┌─────────────────────────────────────────────────────────────┐
│                    Noetica Language                          │
├─────────────────────────────────────────────────────────────┤
│  NK-2: Runtime Exec + Scheduler (this spec)                │
│    - ExecPlan + OpSpec                                      │
│    - Greedy.curv.v1 scheduler                               │
│    - Batch attempt semantics                                │
│    - Deterministic rescheduling                             │
│    - Resource caps                                          │
├─────────────────────────────────────────────────────────────┤
│  NK-1: Measured Gate Runtime                               │
│    - DebtUnit arithmetic                                    │
│    - V(x) measurement engine                                │
│    - Gate decision logic                                    │
│    - Receipt/verifier pipeline                              │
├─────────────────────────────────────────────────────────────┤
│  CK-0: Mathematical Foundations                             │
│    - State space, invariants                                │
│    - Violation functional V(x)                             │
│    - Budget/Debt/Law                                       │
│    - Curvature interaction bounds                          │
└─────────────────────────────────────────────────────────────┘
```

---

## What "Done" Means

NK-2 v1.0 is complete when:

1. ✅ **ExecPlan + OpSpec** - Deterministic job spec with all required fields
2. ✅ **Runtime State** - Immutable state, ledger anchor, dependency bookkeeping
3. ✅ **Greedy.curv.v1 Scheduler** - Curvature-aware marginal cost batching
4. ✅ **Batch Attempt** - Planning checks, kernel execution, δ-bound, gate
5. ✅ **Commit Receipts** - Local + commit receipts with proper hashes
6. ✅ **Failure Handling** - Deterministic rescheduling transforms
7. ✅ **Resource Caps** - Deterministic reject on cap violations
8. ✅ **Main Loop** - Canonical termination algorithm
9. ✅ **Conformance Tests** - Determinism, rescheduling, no-attempt tests

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial NK-2 specification |

### Version Bump Criteria

**Major bump required if:**
- Scheduler rule changes
- Batch attempt semantics change
- Receipt schema changes
- Failure handling transform changes

**Minor bump allowed for:**
- New conformance vectors
- Documentation clarifications

---

## Document Spine

| Document | Description |
|----------|-------------|
| [`1_exec_plan.md`](1_exec_plan.md) | ExecPlan + OpSpec runtime input structures |
| [`2_runtime_state.md`](2_runtime_state.md) | Runtime state, dependency bookkeeping |
| [`3_scheduler.md`](3_scheduler.md) | Greedy.curv.v1 scheduler algorithm |
| [`4_batch_attempt.md`](4_batch_attempt.md) | Batch attempt semantics + execution |
| [`5_commit_receipts.md`](5_commit_receipts.md) | Local + commit receipt schemas |
| [`6_failure_handling.md`](6_failure_handling.md) | Deterministic rescheduling transforms |
| [`7_resource_caps.md`](7_resource_caps.md) | Resource caps + deterministic reject |
| [`8_main_loop.md`](8_main_loop.md) | Canonical main loop algorithm |
| [`9_conformance.md`](9_conformance.md) | Conformance test requirements |
| [`A_reference_impl.md`](A_reference_impl.md) | Reference implementation |
| [`B_soundness.md`](B_soundness.md) | Soundness properties |

---

## Dependencies

NK-2 requires these NK-1 services:

| Service | Description |
|---------|-------------|
| `State.hash()` | hash_canon.v1 |
| `Receipt.hash()` | canon_receipt_bytes.v1 + H_R |
| `delta_norm_check(op, x, x_o)` | NK-1 §1.5 exact integer rule |
| `V_DU(x)` | NK-1 §1.6 state-only DebtUnit integer |
| `epsilon_measured(batch, x)` | NK-1 §1.6 exact definition |
| `epsilon_hat(batch)` | NK-1 §1.7 from matrix registry |
| `PolicyBundle` | Verification + chain lock |
| Merkle root builder | NK-1 §1.4 for locals |

---

## Key Design Principles

1. **Determinism is non-negotiable**: All ordering must be canonical (sorted by op_id bytes)
2. **No attempt receipts**: Only successful commits emit receipts
3. **Hard pins**: Mode pins, policy locks, resource caps are enforced
4. **Split lexmin**: Execution-time failures always peel lexmin op
5. **Terminal singletons**: Failed singletons halt immediately
