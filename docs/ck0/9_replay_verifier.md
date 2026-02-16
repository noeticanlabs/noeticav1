# CK-0 Replay Verifier

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md)

---

## Overview

The **replay verifier** is CK-0's "truth machine." It verifies that every step satisfies all coherence requirements without trusting the prover.

---

## What the Verifier Does NOT Need

The verifier does **not** need to understand:
- NK-0 glyphs
- NSC action set specifics
- Solver internals

The verifier only needs:
- Action descriptor (canonicalized)
- Transition contract
- Receipt chain

---

## Verification Checklist

The verifier checks the following in order:

### V1: Hash Chain Integrity

```
receipt[i].prev_receipt_hash == receipt[i-1].receipt_hash
```

For genesis: `prev_receipt_hash == null`

### V2: Invariant Evaluation

```
invariant_status == "pass"
```

Re-evaluate invariants on `state_before` and verify.

### V3: Violation Recomputation

```
V(state_before) == debt_before
```

Recompute V(x) from contract set and verify matches receipt.

### V4: Budget Non-Negativity

```
budget >= 0
disturbance >= 0
debt_before >= 0
debt_after >= 0
```

### V5: Coherence Law Inequality

```
debt_after <= debt_before - S(debt_before, budget) + disturbance
```

Where `S` is the declared servicing map.

### V6: Determinism / Canonicalization

- `state_after` matches `H(canonical_encoding(T(state_before, action)))`
- JSON field order is canonical
- Numbers are in canonical form

### V7: Transition Contract

Verify transition is within declared bounds and Lipschitz constants.

---

## Verification Algorithm

```python
def verify(ledger: List[Receipt], spec: CK0Spec) -> VerificationResult:
    # V1: Hash chain
    for i, receipt in enumerate(ledger):
        if i == 0:
            assert receipt.prev_receipt_hash is None
        else:
            assert receipt.prev_receipt_hash == ledger[i-1].receipt_hash
        assert receipt.receipt_hash == H(canonical(receipt))
    
    # V2: Invariants
    for receipt in ledger:
        state = decode(receipt.state_before)
        assert evaluate_invariants(state) == "pass"
    
    # V3: V recomputation
    for receipt in ledger:
        state = decode(receipt.state_before)
        V = compute_V(state, spec.contract_set)
        assert V == receipt.debt_before
    
    # V4: Non-negativity
    for receipt in ledger:
        assert receipt.budget >= 0
        assert receipt.disturbance >= 0
        assert receipt.debt_before >= 0
        assert receipt.debt_after >= 0
    
    # V5: Budget law
    for receipt in ledger:
        S = compute_service(receipt.debt_before, receipt.budget, spec.servicing_map)
        assert receipt.debt_after <= receipt.debt_before - S + receipt.disturbance
    
    # V6: Canonicalization
    for receipt in ledger:
        assert is_canonical_json(receipt)
        assert receipt.state_after == H(canonical(receipt.state_after))
    
    return VerificationResult(valid=True)
```

---

## Verification Failure Codes

| Code | Description |
|------|-------------|
| `VFY_HASH_CHAIN_BROKEN` | Hash chain integrity failed |
| `VFY_INVARIANT_FAILED` | Invariant evaluation failed |
| `VFY_V_MISMATCH` | V recomputation doesn't match |
| `VFY_DEBT_NEGATIVE` | Negative debt detected |
| `VFY_BUDGET_NEGATIVE` | Negative budget detected |
| `VFY_LAW_VIOLATED` | Budget law inequality violated |
| `VFY_CANONICAL_VIOLATION` | Canonicalization rules violated |
| `VFY_TRANSITION_BOUNDS` | Transition out of bounds |

---

## What Gets Verified Per-Step

| Check | Source |
|-------|--------|
| Hash chain | Receipts |
| Invariants | State + spec |
| V(x) | State + contracts |
| Budget law | Receipt fields |
| Determinism | Receipt + spec |
| Transition | Receipt + spec |

---

## Trusted Components

The verifier trusts:

1. **CK-0 spec** (constants, policies, transition contract)
2. **Genesis state** (trusted initial state)
3. **Hash algorithm** (SHA3_256 by default)

Everything else is verified.

---

## Receipt Requirements for Verification

To verify, receipts must contain:

- All fields listed in [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md)
- Canonical encoding
- Complete hash chain

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ Verifier: Checks hash chain, invariants, V, budget law,   │
│          determinism, transition bounds - no trust needed  │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`10_conformance_tests.md`](10_conformance_tests.md) - Test vectors
- [`4_budget_debt_law.md`](4_budget_debt_law.md) - Budget law
- [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md) - Bounds

---

*The verifier doesn't trust. It verifies.*
