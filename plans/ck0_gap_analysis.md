# CK-0 v1.0 Specification vs Implementation Gap Analysis

**Date:** 2026-02-16  
**Status:** Draft - Needs Review  
**Scope:** Comparison of detailed CK-0 v1.0 spec against existing `docs/ck0/` documentation

---

## Executive Summary

The existing `docs/ck0/` documentation provides **strong coverage** (~85-90%) of the CK-0 v1.0 specification. Most core concepts are present and well-documented. However, there are **specific gaps** that need to be addressed to achieve full spec compliance.

---

## 1. Coverage Assessment by Spec Section

| Spec Section | Doc File | Coverage | Notes |
|--------------|----------|----------|-------|
| 1. State Space | `1_state_space.md` | ✅ Complete | Typed state space, field blocks |
| 2. Hard Invariants | `2_invariants.md` | ✅ Complete | I(x) definition, categories |
| 3. Violation Functional V(x) | `3_violation_functional.md` | ✅ Complete | Normalized residuals, aggregation |
| 4. Debt/Budget/Law | `4_budget_debt_law.md` | ⚠️ Partial | Missing explicit service_policy_id |
| 5. NEC Closure | `5_curvature_interaction_bounds.md` | ✅ Complete | Hessian bounds, rectangle identity |
| 6. Canonical Arithmetic | `7_rounding_canonicalization.md` | ✅ Complete | DebtUnit, rounding, reduction |
| 7. Receipts | `8_receipts_omega_ledger.md` | ⚠️ Partial | Missing service_policy_id, service_instance_id |
| 8. Verifier | `9_replay_verifier.md` | ✅ Complete | Verification checklist |
| 9. Conformance Tests | `10_conformance_tests.md` | ✅ Complete | Golden vectors, replay tests |

---

## 2. Identified Gaps

### Gap 1: Service Policy IDs (HIGH PRIORITY)

**Spec Requirement:**
- `service_policy_id = "CK0.service.v1"` 
- `service_instance_id = "linear_capped.mu:<value>"`

**Current State:**
- Exists in `4_budget_debt_law.md` as CK0.svc.lin but NOT as formal policy IDs
- NOT present in receipt schema (`8_receipts_omega_ledger.md`)

**Impact:** Verifier cannot verify which service law was used

**Action:** Add `service_policy_id` and `service_instance_id` fields to receipt schema

---

### Gap 2: Disturbance Accounting Rule (HIGH PRIORITY)

**Spec Requirement:**
> "Either (E_k) is logged explicitly (even if 0), or the verifier assumes (E_k=0) by policy. No silent disturbances."

**Current State:**
- Disturbance is logged in receipts (found in search results)
- NO explicit "disturbance accounting rule" documentation

**Impact:** E_k could become unbounded "excuse field" - classic loophole

**Action:** Add explicit disturbance accounting rule section to `4_budget_debt_law.md`

---

### Gap 3: Service Law Admissibility Conditions (MEDIUM PRIORITY)

**Spec Requirement (A1-A6):**
- A1: Determinism
- A2: Monotonicity
- A3: Zero-debt consistency Φ(0,B)=0
- A4: Zero-budget identity Φ(D,0)=D
- A5: Lipschitz control in debt
- A6: Continuity

**Current State:**
- Documented in `5_curvature_interaction_bounds.md` as A1-A4 but different context (curvature)
- NOT explicitly enumerated as service law admissibility conditions in `4_budget_debt_law.md`

**Action:** Add formal admissibility conditions section to `4_budget_debt_law.md`

---

### Gap 4: Per-Contract Receipt Fields (MEDIUM PRIORITY)

**Spec Requirement:** Each contract k needs:
- `contract_id`
- `active` (true/false)
- `m_k` (dimension)
- `sigma_spec_id`
- `weight_spec_id`
- `r2_k = ||tilde_r_k||_2^2` (DebtUnit)
- optional `r_hash_k`

**Current State:**
- Found in `8_receipts_omega_ledger.md` lines 174-177: weight_spec_id, r2, r_inf, r_hash
- `m_k` dimension NOT clearly documented

**Action:** Verify and clarify per-contract fields in receipt schema

---

### Gap 5: V(x) One-Line Canon Summary (LOW PRIORITY)

**Spec Requirement:**
```
Phase 0 / CK-0: I(x) hard, V(x)=sum_k w_k |r_k(x)/σ_k(x)|*2^2, D_{k+1}≤D_k-S(D_k,B_k)+E_k, all replay-verifiable.
```

**Current State:**
- Present in `0_overview.md` as CK-0 Core Definition (lines 34-46)
- Slightly different formatting

**Action:** Add exact one-line canon to `0_overview.md` for spec compliance

---

## 3. Discrepancies Found

### Discrepancy 1: Receipt Field Naming

| Spec Field | Doc Field | Notes |
|------------|-----------|-------|
| `hash_chain_prev` | `prev_receipt_hash` | Semantic equivalent ✅ |
| `hash_chain_curr` | `receipt_hash` | Semantic equivalent ✅ |
| `invariants_pass` | `invariant_status` | Different naming but present ✅ |
| `law_check_pass` | `law_satisfied` | Different naming but present ✅ |

**Verdict:** Acceptable - semantic equivalents exist

---

### Discrepancy 2: Robust Extension (CK-0R)

**Spec Note:** "CK-0R may be defined later via (ρ)-penalties"

**Current State:** Not documented

**Verdict:** Not a gap - explicitly marked as future extension

---

## 4. Recommendations

### Priority 1 (Must Fix)
1. Add `service_policy_id` and `service_instance_id` to receipt schema
2. Add disturbance accounting rule to prevent silent disturbance loophole

### Priority 2 (Should Fix)
3. Formalize service law admissibility conditions (A1-A6)
4. Verify per-contract fields include `m_k` dimension

### Priority 3 (Nice to Have)
5. Add exact one-line canon summary to overview
6. Consider adding CK0.svc.lin → service_instance_id mapping reference

---

## 5. Spec Completeness Check

| Requirement | Status |
|-------------|--------|
| Hard invariants I(x) | ✅ Documented |
| Canonical V(x) | ✅ Documented |
| Disturbance-separated law | ✅ Documented |
| Default linear_capped service | ✅ Documented |
| Receipt requirements | ⚠️ Partial |
| Verifier obligations | ✅ Documented |
| Conformance tests | ✅ Documented |
| Disturbance accounting rule | ❌ Missing |
| Service policy IDs | ❌ Missing |

---

## 6. Files to Modify

1. `docs/ck0/8_receipts_omega_ledger.md` - Add service_policy_id, service_instance_id
2. `docs/ck0/4_budget_debt_law.md` - Add disturbance accounting rule, admissibility conditions
3. `docs/ck0/0_overview.md` - Add one-line canon summary (optional)

---

## 7. Next Steps

1. Review this gap analysis with stakeholders
2. Approve priority items for implementation
3. Create implementation plan for fixes

---

*Generated from comparison of CK-0 v1.0 detailed spec vs docs/ck0/ directory*
