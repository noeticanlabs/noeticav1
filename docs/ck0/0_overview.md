# CK-0 Overview

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 (Mathematical Substrate)

---

## Mission

CK-0 defines **Coherence** as an enforceable dynamical law:

1. Invariants are declared
2. Violation is measurable
3. Reduction of violation requires declared service (budget)
4. Every step is replay-verifiable via receipts

CK-0 is **language-agnostic** and **solver-agnostic**.

---

## What is CK-0?

CK-0 is the canonical mathematical substrate that collapses "Phase 0" into a single, rigorously defined coherence framework. It treats NK-0/NK-1 as consumers of its contracts.

**CK-0 = Phase 0 (math + enforceable contracts)**

Everything else is an interface layer.

---

## NEC: CK-0.5 Operational Layer

**See also:** [`../nec/0_overview.md`](../nec/0_overview.md)

NEC (Noetica Execution Calculus) sits between CK-0 (mathematical substrate) and NK-1/2/3 (runtime implementations). NEC defines the operational calculus that the runtime actually executes:

| Layer | Type | Role |
|-------|------|------|
| CK-0 | Mathematical substrate | Defines V, invariants, service law |
| NEC (CK-0.5) | Operational calculus | Defines batch execution, gate, split, receipts |
| NK-1/2/3 | Implementation | Runtime implementations of NEC |

NEC provides:
- Deterministic batching semantics
- Gate law for safe aggregation
- Split law for deterministic failure handling
- Receipt witness for verifiable descent

---

## CK-0 Core Definition

A system is **coherent** over a run if, for every step *k*:

1. **Hard invariants** `I(x_k)` hold
2. **Violation** `D_k := V(x_k)` is well-defined and deterministic
3. The declared **budget** `B_k` and **disturbance bound** `E_k` satisfy the CK-0 law:
   
   ```
   D_{k+1} ≤ D_k - S(D_k, B_k) + E_k
   ```
   
   where `S` is the servicing map with `S(D,0) = 0`
4. The transition and all measurements are **replay-verifiable** by the CK-0 verifier from the receipt chain

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CK-0 CANON                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Constants  │→ │ State Space │→ │    Invariants      │  │
│  │ (B_ref)     │  │ (1_state)   │  │    (2_invariants)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         ↓                ↓                   ↓              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │            Violation Functional V(x)                   ││
│  │            (3_violation_functional)                     ││
│  │  V(x) = Σ w_k ||r_k(x)/σ_k(x)||²                       ││
│  └─────────────────────────────────────────────────────────┘│
│         ↓                                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │            Budget/Debt Law (4_budget_debt_law)        ││
│  │  D_{k+1} ≤ D_k - S(D_k, B_k) + E_k                    ││
│  └─────────────────────────────────────────────────────────┘│
│         ↓                ↓                ↓                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Curvature  │  │ Transition  │  │   Receipts Ω       │  │
│  │  (5_curv)   │  │ Contract    │  │   (8_receipts)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                              ↓              │
│                                    ┌─────────────────────┐  │
│                                    │   Replay Verifier   │  │
│                                    │   (9_replay)        │  │
│                                    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Document Spine

| File | Purpose |
|------|---------|
| [`1_state_space.md`](1_state_space.md) | State space and typing |
| [`2_invariants.md`](2_invariants.md) | Hard constraints |
| [`3_violation_functional.md`](3_violation_functional.md) | Coherence metric V(x) |
| [`4_budget_debt_law.md`](4_budget_debt_law.md) | Law of coherence |
| [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md) | NEC closure |
| [`6_transition_contract.md`](6_transition_contract.md) | Deterministic evolution |
| [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) | Anti-wedgeability |
| [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) | Receipt schema |
| [`9_replay_verifier.md`](9_replay_verifier.md) | Truth machine |
| [`10_conformance_tests.md`](10_conformance_tests.md) | Test vectors |
| [`A_glossary.md`](A_glossary.md) | Terminology |
| [`B_reference_constants.md`](B_reference_constants.md) | Canon constants |

---

## Policy IDs

| Policy | ID | Description |
|--------|-----|-------------|
| Violation Functional | `CK0.v1` | Default squared norm form |
| Robust Variant | `CK0R.v1:<ρ_id>` | Robust penalties (extension) |
| Servicing (default) | `CK0.svc.lin` | Linear capped servicing |

---

## Out of Scope (Delegated to NK)

- Glyph syntax and parsing details
- NSC action set specifics
- Measured_gate versions
- Curvature matrix registry formats
- CTD, RFE, GR solvers

CK-0 only requires the **mathematical contracts** and **receipt mechanics**.

---

## Versioning

Any implementation that changes a CK-0 constant **must** bump the CK-0 version. See [`B_reference_constants.md`](B_reference_constants.md).

---

*CK-0 is the truth machine. Everything else is an interface.*
