# PhaseLoom Implementation Plan

**Canon Doc Spine v1.0.0**

---

## 1. Overview

This plan outlines the implementation roadmap for PhaseLoom Potential — Geometric Memory, integrating with the existing CK-0 / Coh infrastructure.

---

## 2. Implementation Phases

### Phase 1: Core Types and Infrastructure

**Timeline:** Week 1-2

| Task | Status | Dependencies |
|------|--------|--------------|
| Create src/phaseloom/types.py | ✅ Done | None |
| Create src/phaseloom/__init__.py | ✅ Done | types.py |
| Create FixedPoint arithmetic | ✅ Done | None |

**Deliverables:**
- Core type definitions (PLState, PLParams, MemoryState, Weights)
- Fixed-point arithmetic with deterministic truncation

---

### Phase 2: Core Dynamics

**Timeline:** Week 2-3

| Task | Status | Dependencies |
|------|--------|--------------|
| Create src/phaseloom/functor.py | ✅ Done | types.py |
| Create src/phaseloom/potential.py | ✅ Done | types.py |
| Create src/phaseloom/interlock.py | ✅ Done | types.py, potential.py |
| Create src/phaseloom/verifier.py | ✅ Done | types.py, interlock.py |

**Deliverables:**
- PhaseLoom endofunctor implementation
- V_PL computation
- Scheduler interlock enforcement
- LoomVerifier STF

---

### Phase 3: Extended Features

**Timeline:** Week 3-4

| Task | Status | Dependencies |
|------|--------|--------------|
| Create curvature.py | ⏳ Pending | types.py |
| Create tension.py | ⏳ Pending | types.py |
| Create authority.py | ⏳ Pending | types.py |
| Create receipt.py | ⏳ Pending | verifier.py |
| Create compression.py | ⏳ Pending | receipt.py |

**Deliverables:**
- Curvature accumulator C
- Tension accumulator T
- Authority injection
- Receipt contract v1
- Slab compression

---

### Phase 4: Integration

**Timeline:** Week 4-5

| Task | Status | Dependencies |
|------|--------|--------------|
| Integrate with src/ck0/ | ⏳ Pending | Phase 2 complete |
| Integrate with src/coh/ | ⏳ Pending | Phase 2 complete |
| Integrate with src/nk1/ | ⏳ Pending | Phase 3 complete |
| Integrate with src/nk2/ | ⏳ Pending | Phase 2 complete |

**Deliverables:**
- CK-0 violation functional integration
- Coh functor integration
- Receipt schema integration
- Scheduler integration

---

### Phase 5: Testing

**Timeline:** Week 5-6

| Task | Status | Dependencies |
|------|--------|--------------|
| Create test_phaseloom_types.py | ⏳ Pending | types.py |
| Create test_phaseloom_potential.py | ⏳ Pending | potential.py |
| Create test_phaseloom_interlock.py | ⏳ Pending | interlock.py |
| Create test_phaseloom_verifier.py | ⏳ Pending | verifier.py |
| Integration tests | ⏳ Pending | Phase 4 complete |

---

## 3. Documentation Status

### Completed Documentation

| Document | Status |
|----------|--------|
| docs/phaseloom/0_overview.md | ✅ Complete |
| docs/phaseloom/1_notation_ledger.md | ✅ Complete |
| docs/phaseloom/2_coh_integration.md | ✅ Complete |
| docs/phaseloom/3_geometric_memory.md | ✅ Complete |
| docs/phaseloom/4_curvature_accumulator.md | ✅ Complete |
| docs/phaseloom/5_tension_accumulator.md | ✅ Complete |
| docs/phaseloom/6_budget_authority.md | ✅ Complete |
| docs/phaseloom/7_potential.md | ✅ Complete |
| docs/phaseloom/8_interlock.md | ✅ Complete |
| docs/phaseloom/9_authority_injection.md | ✅ Complete |
| docs/phaseloom/10_descent_theorem.md | ✅ Complete |
| docs/phaseloom/11_receipt_contract.md | ✅ Complete |
| docs/phaseloom/12_stf_verifier.md | ✅ Complete |
| docs/phaseloom/13_compression.md | ✅ Complete |
| docs/phaseloom/14_security_model.md | ✅ Complete |

---

## 4. Code Status

### Implemented Modules

| Module | Status |
|--------|--------|
| src/phaseloom/__init__.py | ✅ Done |
| src/phaseloom/types.py | ✅ Done |
| src/phaseloom/functor.py | ✅ Done |
| src/phaseloom/potential.py | ✅ Done |
| src/phaseloom/interlock.py | ✅ Done |
| src/phaseloom/verifier.py | ✅ Done |
| src/phaseloom/curvature.py | ⏳ Pending |
| src/phaseloom/tension.py | ⏳ Pending |
| src/phaseloom/authority.py | ⏳ Pending |
| src/phaseloom/receipt.py | ⏳ Pending |
| src/phaseloom/compression.py | ⏳ Pending |

---

## 5. v1 Deployment Profile (Consensus Safe)

### Recommended v1 Enforcement

| Feature | Enforcement |
|---------|-------------|
| C recurrence | Enforce |
| Budget charge law | Enforce |
| Interlock (b and A) | Enforce |
| Full V_PL on-chain | Not required |
| T deterministic formula | Audit-only |
| Authority injection | Require multisig |

### v1 Parameters

```python
PLParams(
    rho_C=0.9,
    rho_T=0.9,
    kappa_A=1.0,
    kappa_T=1.0,
    b_min=0,  # Allow zero budget
    strong_mode=False,
    Theta=None,
)
```

---

## 6. Integration Points

### CK-0 Integration

| Component | Integration |
|-----------|-------------|
| V(x) | Base term in V_PL |
| State space X | Base of extended X~ |
| Budget law | Extended with curvature cost |
| Receipts | Extended with PL fields |

### Coh Integration

| Component | Integration |
|-----------|-------------|
| CohObject | Extended to PL object |
| CohMorphism | Extended to PL morphism |
| TimeFunctor | Extended with memory |

### NK-1 Integration

| Component | Integration |
|-----------|-------------|
| ReceiptCanon | Extended to PL receipts |
| Policy bundle | Threading model |

### NK-2 Integration

| Component | Integration |
|-----------|-------------|
| Scheduler | Interlock enforcement |
| Batch | Step type selection |

---

## 7. Next Steps

1. **Complete Phase 3:** Create remaining modules (curvature, tension, authority, receipt, compression)
2. **Integration:** Connect with existing CK-0/Coh/NK-1/NK-2 modules
3. **Testing:** Create comprehensive test suite
4. **Documentation:** Add inline docs and API reference
5. **Deployment:** Prepare v1 deployment configuration

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Fixed-point overflow | Strict bounds checking |
| Non-determinism | Deterministic arithmetic only |
| Integration complexity | Incremental integration testing |
| Theorem proof gaps | Mark assumptions clearly |

---

## 9. Success Criteria

- [ ] All core modules implemented
- [ ] Integration with existing modules complete
- [ ] Comprehensive test coverage (>80%)
- [ ] Determinism verified
- [ ] v1 deployment ready

---

*This plan is a living document and will be updated as implementation progresses.*
