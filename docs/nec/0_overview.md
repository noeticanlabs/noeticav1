# NEC v1.0

**Noetica Execution Calculus**

**Status:** Structural  
**Layer:** CK-0.5 (operational calculus between math and runtime)  
**Depends on:** CK-0 (coherence metric), PolicyBundle  
**Used by:** NK-1, NK-2, NK-3

---

## Position in Architecture

```
Coh (L1 Category Foundation)
        ↓
Coh_CK0 (CK-0 as Full Subcategory)
        ↓
CK-0 (Mathematical Substrate)
        ↓
NEC (Execution Calculus) ← CK-0.5
        ↓
NK-1 → NK-2 → NK-3
```

**See also:** [`../coh/0_overview.md`](../coh/0_overview.md)

NEC sits between the mathematical substrate (CK-0) and the runtime implementations (NK-1/2/3). It defines the **operational calculus** that the runtime actually executes.

---

## What NEC Defines

NEC defines the algebraic execution law:

| Component | Definition |
|-----------|------------|
| State evolution | Deterministic patch semantics |
| V functional | Coherence violation metric |
| δ-bounds | Per-operator displacement bounds |
| Batch residual ε | Non-additivity measure |
| Gate law | Safe aggregation condition |
| Receipt witness | Verifiable descent inequality |

---

## What NEC Guarantees

NEC guarantees:

- **Batching deterministic**: Same inputs → same outputs
- **Concurrency safe**: Interaction bounded by ε
- **Receipts verifiable**: Witness inequality ensures descent
- **Stability measurable**: Finite energy bound

---

## NEC vs NK-4G

| Layer | Type | Role |
|-------|------|------|
| NEC | Structural | Execution algebra - what runs |
| NK-4G | Interpretive | Geometric lens on NEC |

Remove NK-4G → NEC still valid.  
Remove NEC → NK-4G collapses.

---

## Document Spine

| Document | Content |
|----------|---------|
| [`1_state_space.md`](1_state_space.md) | State space X, V functional |
| [`2_contract_structure.md`](2_contract_structure.md) | Contract C = (H, S, Θ) |
| [`3_delta_norms.md`](3_delta_norms.md) | δ_o bounds, G-norm |
| [`4_batch_residual.md`](4_batch_residual.md) | ε_B computation |
| [`5_gate_law.md`](5_gate_law.md) | Gate condition |
| [`6_split_law.md`](6_split_law.md) | Deterministic splitting |
| [`7_receipt_witness.md`](7_receipt_witness.md) | ProxWitness inequality |
| [`8_compositionality.md`](8_compositionality.md) | Why NEC composes |
| [`9_soundness_theorems.md`](9_soundness_theorems.md) | Core theorems |
| [`10_limits.md`](10_limits.md) | Guarantees and non-guarantees |

---

## Version

- **NEC v1.0**: Initial structural release
- Changes require explicit version bump
- NK-1/2/3 implementations must conform to NEC semantics
