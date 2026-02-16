# NK-3 Lowering Core v1.0

**Version:** 1.0  
**Status:** Spec-closed (no soft edges)  
**Depends on:** NEC v1.0 + NK-1 v1.0 + NK-2 v1.0  
**Canon source:** NSC.v1 (typed, normalized IR)

---

## Overview

NK-3 takes a canonical NSC program and produces the **only three runtime-ready artifacts** that NK-2 needs (plus a module receipt):

1. **OpSet** — Fully specified ops with footprints + bounds
2. **DAG** — Precedence/hazard + explicit control edges only
3. **ExecPlan** — Policy-bound scheduler configuration
4. **ModuleReceipt** — Binds program digest + all artifact digests

NK-3 is the **lowering layer** that bridges the Noetica Specification Code (NSC) to the NK-2 runtime executor.

---

## Mission

NK-3 provides:

| Capability | Description |
|------------|-------------|
| **Deterministic Lowering** | Pure function from NSC bytes → OpSet/DAG/ExecPlan/Receipt |
| **Hygienic OpIDs** | Collision-resistant, deterministic operation naming |
| **Explicit Hazard Edges** | WAW/WAR edges only, no hidden quantifiers |
| **Join Barrier Insertion** | Explicit control-flow join enforcement |
| **Policy-Bound Execution** | Scheduler configuration locked to policy bundle |

---

## Scope

```
┌─────────────────────────────────────────────────────────────┐
│                    Noetica Language                          │
├─────────────────────────────────────────────────────────────┤
│  NK-3: Lowering Core (this spec)                           │
│    - NSC → OpSet/DAG/ExecPlan/ModuleReceipt               │
│    - Deterministic lowering (no optimization)              │
│    - Join barrier insertion                               │
├─────────────────────────────────────────────────────────────┤
│  NK-2: Runtime Exec + Scheduler                            │
│    - ExecPlan + OpSpec                                     │
│    - Greedy.curv.v1 scheduler                              │
│    - Batch attempt semantics                               │
│    - Deterministic rescheduling                            │
├─────────────────────────────────────────────────────────────┤
│  NK-1: Measured Gate Runtime                               │
│    - DebtUnit arithmetic                                   │
│    - V(x) measurement engine                               │
│    - Gate decision logic                                   │
│    - Receipt/verifier pipeline                            │
├─────────────────────────────────────────────────────────────┤
│  CK-0: Mathematical Foundations                            │
│    - State space, invariants                              │
│    - Violation functional V(x)                           │
│    - Budget/Debt/Law                                      │
│    - Curvature interaction bounds                         │
└─────────────────────────────────────────────────────────────┘
```

---

## What "Done" Means

NK-3 v1.0 is complete when:

1. ✅ **Canon Inputs** — NSC.v1 program bytes + PolicyBundle + KernelRegistry
2. ✅ **OpSet** — Deterministic list of OpSpecs sorted by op_id
3. ✅ **DAG** — Canonical lex-toposort with WAW/WAR/control edges
4. ✅ **ExecPlan** — Policy-bound scheduler configuration
5. ✅ **ModuleReceipt** — Binds all digests + toolchain IDs
6. ✅ **KernelRegistry Interface** — Static and param-decidable footprints
7. ✅ **Join Barrier Insertion** — Explicit control-flow joins
8. ✅ **Conformance Tests** — Golden vectors + negative tests + replay

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial NK-3 specification |

### Version Bump Criteria

**Major bump required if:**
- OpSet schema changes
- DAG edge kinds change
- ExecPlan schema changes
- ModuleReceipt schema changes
- Lowering purity axiom changes

**Minor bump allowed for:**
- New conformance vectors
- Documentation clarifications

---

## Document Spine

| Document | Description |
|----------|-------------|
| [`1_canon_inputs.md`](1_canon_inputs.md) | NSC.v1, PolicyBundle, KernelRegistry |
| [`2_canon_outputs.md`](2_canon_outputs.md) | OpSet, DAG, ExecPlan, ModuleReceipt |
| [`3_kernel_registry.md`](3_kernel_registry.md) | KernelRegistry interface |
| [`4_opset.md`](4_opset.md) | OpSet v1 specification |
| [`5_dag.md`](5_dag.md) | DAG v1 specification |
| [`6_execplan.md`](6_execplan.md) | ExecPlan v1 specification |
| [`7_module_receipt.md`](7_module_receipt.md) | ModuleReceipt v1 specification |
| [`8_hazard_control.md`](8_hazard_control.md) | Hazard + control edge construction |
| [`9_conformance.md`](9_conformance.md) | Conformance test requirements |

---

## Dependencies

NK-3 requires these upstream artifacts:

| Artifact | Source | Description |
|----------|--------|-------------|
| `program_nsc_bytes` | Frontend | Canonical NSC.v1 byte encoding |
| `program_nsc_digest` | Hash | H_R(program_nsc_bytes) |
| `policy_digest` | NK-1 | PolicyBundle digest (chain-locked) |
| `kernel_registry_digest` | NK-1 | KernelRegistry digest |
| Kernel specs | NK-1 | Footprints, bounds, mode flags |

NK-3 produces artifacts consumed by NK-2:

| Artifact | Consumer | Description |
|----------|----------|-------------|
| OpSet | NK-2 | Operation universe with footprints |
| DAG | NK-2 | Precedence constraints |
| ExecPlan | NK-2 | Scheduler configuration |
| ModuleReceipt | NK-1/NK-2 | Digest chain verification |

---

## Key Design Principles

1. **Lowering purity is non-negotiable**: No time, host info, filesystem, randomness
2. **No optimization in v1.0**: Only canonical normalization + deterministic lowering
3. **Explicit edges only**: No hidden hazard edges, no safety edges
4. **Lex-toposort order**: Canonical node ordering for determinism
5. **Hygienic OpIDs**: SHA256-based, collision-resistant

---

## Meaning Preservation Claim

**NK-3 preservation claim (v1.0):**

For all initial states (x_0) satisfying schema validity and policy constraints:

```
H_X(〚P〛_NSC(x_0))
======================================================
H_X(π_X(ExecNK2(LowerNK3(P), x_0)))
```

Receipt chains may differ in batching but must verify under NK-1/NK-2 and bind the same module receipt digest.

---

## Tokenless Decision Gate

### v1.0 Stance

Tokenless is **not** a Phase 1 requirement. NK-3 v1.0 is frontend-agnostic.

### Gate NK-3.G1 (future)

A tokenless frontend is admitted iff it emits **identical canonical NSC.v1 bytes** for the same program meaning.
