# Noetica v1 — A Coherence-Enforcing Language Over CK-0/Coh

**Version:** 1.0  
**Status:** Draft  
**Related:** [`../ck0/0_overview.md`](../ck0/0_overview.md), [`../phaseloom/0_overview.md`](../phaseloom/0_overview.md)

---

## Purpose

Define Noetica as:

> A linear, phase-typed, refinement-checked language that compiles to deterministic WASM and emits CK-0/PhaseLoom-consistent receipts.

Noetica provides the **programmable surface** for the Noeticav1 coherence framework. It sits atop the mathematical foundations (CK-0, Coh) and runtime kernels (NK), adding syntactic sugar and static guarantees while preserving the deterministic, verifiable nature of the underlying system.

---

## Layer Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Noetica Language Layer                    │
│  (this module)                                              │
│    - Linear type system                                      │
│    - 10 kernel constructs                                    │
│    - Refinement profile v1                                   │
├─────────────────────────────────────────────────────────────┤
│  L4: NK Runtime + STF                                        │
│    - NK-1: DebtUnit, contracts, gates                       │
│    - NK-2: Scheduler, execution                             │
│    - NK-3: Lowering, DAG                                    │
│    - NK-4G: Receipt verification                            │
├─────────────────────────────────────────────────────────────┤
│  L3: PhaseLoom Geometric Memory                              │
│    - PLState, PLParams                                       │
│    - V_PL potential                                          │
│    - Interlock mechanism                                     │
├─────────────────────────────────────────────────────────────┤
│  L2: CK-0 Mathematical Foundations                          │
│    - DebtUnit exact arithmetic                               │
│    - Violation functional V(x)                              │
│    - Curvature matrix M                                      │
│    - Invariants                                             │
├─────────────────────────────────────────────────────────────┤
│  L1: Coh Category of Coherent Spaces                        │
│    - CohObject, CohMorphism                                  │
│    - Functors, limits                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Constraints

| Constraint | Requirement | Rationale |
|------------|-------------|------------|
| **No floats in consensus** | All monetary/quantitative values in DebtUnit | Eliminates precision attacks |
| **Linear resource discipline** | Every resource must be consumed exactly once | Prevents double-spend |
| **Decidable refinement** | QF-LRA-FP fragment only | Compile-time proof obligation |
| **Deterministic lowering** | Same source + profile = same WASM | Replay verification |
| **Zero-cost coherence** | Hot loops contain no refinement checks | Performance |

---

## What "Done" Means

Noetica v1.0 is complete when:

1. ✅ **10 kernel constructs** - Complete semantics for mint, burn, solve, repair, freeze, thaw, measure, emit, move, phase_match
2. ✅ **Linear type system** - Sound with respect to resource conservation
3. ✅ **Refinement profile** - QF-LRA-FP decidable fragment
4. ✅ **WASM ABI** - Deterministic host boundary
5. ✅ **CK-0/PhaseLoom integration** - Formal mapping of constructs to underlying modules
6. ✅ **Lean proof targets** - Type soundness, conservation, phase exclusion

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-19 | Initial Noetica specification |

### Version Bump Criteria

**Major bump required if:**
- Kernel construct semantics change
- Linear type rules change
- Refinement profile fragment expands
- WASM ABI encoding changes

---

## References

- CK-0: [`../ck0/0_overview.md`](../ck0/0_overview.md)
- PhaseLoom: [`../phaseloom/0_overview.md`](../phaseloom/0_overview.md)
- Coh: [`../coh/0_overview.md`](../coh/0_overview.md)
- NK-1: [`../nk1/0_overview.md`](../nk1/0_overview.md)
- NK-4G Verifier: [`../nk4g/0_overview.md`](../nk4g/0_overview.md)
