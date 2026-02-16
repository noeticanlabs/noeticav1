# NK-1 Runtime Core v1.0

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`../ck0/0_overview.md`](../ck0/0_overview.md)

---

## Overview

NK-1 is the **certificate-side substrate** for deterministic gating - the runtime kernel that transforms CK-0 from a coherent theory into a **replay-verifiable execution engine**.

While CK-0 defines the mathematical foundations (invariants, violation functional, service law, curvature bounds), NK-1 provides the **mechanical implementation** that hostile implementers cannot wiggle through.

---

## Mission

NK-1 provides:

| Capability | Description |
|------------|-------------|
| **Un-wedgeable Parsing** | Parse actions with zero ambiguity |
| **Deterministic Evaluation** | Compute ΔV and matrix interactions in exact DebtUnit |
| **Mechanical Enforcement** | Enforce GLB + CK-0 Law-of-Coherence programmatically |
| **Replay-Verifiable Receipts** | Emit receipts that independently verify |

NK-1 is **not** the full Noetica language. NK-1 is the **runtime kernel for measured_gate.v1**.

---

## Scope

```
┌─────────────────────────────────────────────────────────────┐
│                    Noetica Language                          │
├─────────────────────────────────────────────────────────────┤
│  NK-1: Measured Gate Runtime (this spec)                   │
│    - DebtUnit arithmetic                                    │
│    - V(x) measurement engine                                │
│    - Gate decision logic                                   │
│    - Receipt/verifier pipeline                             │
├─────────────────────────────────────────────────────────────┤
│  CK-0: Mathematical Foundations                             │
│    - State space, invariants                               │
│    - Violation functional V(x)                             │
│    - Budget/Debt/Law                                       │
│    - Curvature interaction bounds                          │
└─────────────────────────────────────────────────────────────┘
```

---

## What "Done" Means

NK-1 v1.0 is complete when:

1. ✅ **DebtUnit arithmetic library** - exact, canonical, no floats
2. ✅ **Contract measurement engine** - V(x) computation in DebtUnit
3. ✅ **Measured gate** - ΔV comparison, budget law enforcement
4. ✅ **Curvature registry + M-entry parser** - rational_scaled.v1
5. ✅ **Receipt pipeline** - hash-chained, canonical JSON
6. ✅ **Replay verifier** - standalone, byte-for-byte verification
7. ✅ **Conformance suite** - golden vectors for all components

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-16 | Initial NK-1 specification |

### Version Bump Criteria

**Major bump required if:**
- DebtUnit encoding changes
- Rounding rule changes
- Action canonicalization changes
- Receipt schema changes
- Matrix entry mode changes

**Minor bump allowed for:**
- New conformance vectors
- Additional allowlisted matrix IDs
- Documentation clarifications

---

## Document Spine

| Document | Description |
|----------|-------------|
| [`1_constants.md`](1_constants.md) | NK-1 locked constants (v1.0) |
| [`2_debtunit.md`](2_debtunit.md) | DebtUnit arithmetic library |
| [`3_contracts.md`](3_contracts.md) | Contract measurement engine (V(x)) |
| [`4_measured_gate.md`](4_measured_gate.md) | Measured gate v1 implementation |
| [`5_curvature.md`](5_curvature.md) | Curvature registry + M-entry |
| [`6_actions.md`](6_actions.md) | Action parsing + canonicalization |
| [`7_receipts.md`](7_receipts.md) | Receipt schema + pipeline |
| [`8_verifier.md`](8_verifier.md) | Replay verifier |
| [`9_conformance.md`](9_conformance.md) | Conformance suite |
| [`A_reference_impl.md`](A_reference_impl.md) | Reference implementation guide |
| [`B_soundness.md`](B_soundness.md) | Measured Gate soundness proof |

---

## Relationship to CK-0

NK-1 implements the following CK-0 components:

| CK-0 Concept | NK-1 Implementation |
|--------------|---------------------|
| `V(x)` violation functional | [`3_contracts.md`](3_contracts.md) |
| Service law `S(D,B)` | [`4_measured_gate.md`](4_measured_gate.md) |
| Disturbance policies DP0-DP3 | [`4_measured_gate.md`](4_measured_gate.md) |
| Curvature matrix M | [`5_curvature.md`](5_curvature.md) |
| Receipt schema | [`7_receipts.md`](7_receipts.md) |
| Replay verifier | [`8_verifier.md`](8_verifier.md) |

---

*See also: [`../ck0/0_overview.md`](../ck0/0_overview.md)*
