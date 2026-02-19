# Coh Canon Specification v1.0.0 vs Existing Documentation Gap Analysis

**Date:** 2026-02-19  
**Status:** Draft  
**Scope:** Comparison of provided Coh Canon Specification v1.0.0 against existing `docs/coh/` documentation

---

## Executive Summary

The provided Coh Canon Specification v1.0.0 represents a **newly formalized** canonical specification that differs significantly from the existing `docs/coh/` documentation. The existing docs were written from a different perspective (category theory focused with 5-tuple objects) while the spec v1.0.0 takes a more practical engineering approach (triple objects with emphasis on determinism and receipt verification).

**Overall Coverage Assessment:** ~60-70% — Major structural and terminological differences require significant updates.

---

## 1. Structural Differences

### 1.1 Object Definition

| Aspect | Spec v1.0.0 | Existing Docs | Gap |
|--------|-------------|---------------|-----|
| Definition | Triple `(X, V, RV)` | 5-tuple `(X, Rec, V, Δ, RV)` | **MAJOR** |
| State Space | X | X | ✓ |
| Receipt Set | Implicit in RV | Rec (explicit) | **MAJOR** |
| Potential | V | V | ✓ |
| Budget Map | Implicit (in RV) | Δ (explicit) | MEDIUM |
| Validator | RV (predicate) | RV (relation) | MEDIUM |

**Impact:** The spec simplifies the object definition by combining receipt handling into RV. Existing docs treat receipts as a separate algebraic structure.

---

## 2. Terminology Differences

### 2.1 Key Terms

| Spec v1.0.0 | Existing Docs | Notes |
|-------------|---------------|-------|
| Faithfulness Potential | Potential functional / Violation functional | Spec uses "faithfulness" explicitly |
| Receipt-Verifier Predicate | Validator relation | Spec emphasizes decidability/predicate |
| Admissible Set C | C = V⁻¹(0) | Same definition |
| Morphism receipt map `f_R` | Morphism receipt map `f_♯` | Different notation |
| Chain Digest / Ledger | Not explicitly named | Spec adds Ω concept |
| Determinism Canon | Axiom A3 (deterministic validity) | Spec has dedicated Section 7 |

---

## 3. Missing Content from Existing Docs

### 3.1 High Priority Gaps

| Section | Spec Content | Existing Doc | Status |
|---------|--------------|--------------|--------|
| §3.2 | Bounded-Tube Admissibility | Not present | **MISSING** |
| §7 | Determinism Canon | Partial (Axiom A3) | **INCOMPLETE** |
| §6 | Trace Closure Principle | Not present | **MISSING** |
| §11 | Implementation Contract | Not present | **MISSING** |
| §12 | Minimal Proof Obligations | Not present | **MISSING** |
| §13 | Versioning and Drift Prevention | Not present | **MISSING** |

### 3.2 Section-by-Section Coverage

| Spec Section | Topic | Doc File | Coverage |
|--------------|-------|----------|----------|
| §1 | Notation Ledger | Partial | ⚠️ Partial |
| §2 | Core Definition (Coh Object) | `1_objects.md` | ⚠️ Different structure |
| §3 | Admissibility Axioms | `1_objects.md` | ⚠️ Missing bounded-tube |
| §4 | Transitions and Receipts | `1_objects.md` | ⚠️ Different presentation |
| §5 | Morphisms | `2_morphisms.md` | ✓ Similar but notation differs |
| §6 | Receipt Category / Trace Closure | Not present | **MISSING** |
| §7 | Determinism Canon | `1_objects.md` A3 | **INCOMPLETE** |
| §8 | CK-0 as Subcategory | `6_ck0_integration.md` | ✓ Present |
| §9 | PhaseLoom Extension | `phaseloom/2_coh_integration.md` | ⚠️ Different structure |
| §10 | Universal Invariants | Not present | **MISSING** |
| §11 | Implementation Contract | Not present | **MISSING** |
| §12 | Proof Obligations | Not present | **MISSING** |
| §13 | Versioning | Not present | **MISSING** |

---

## 4. Specific Issues

### Issue 1: Bounded-Tube Admissibility (HIGH PRIORITY)

**Spec Requirement (§3.2):**
```
C_S(θ) := {x ∈ X : V(x) ≤ θ}
```

**Current State:** Not present in existing docs. Only zero-set admissibility (V⁻¹(0)) is documented.

**Impact:** Cannot represent systems with "within tolerance" validity.

**Action:** Add new section to `1_objects.md` for bounded-tube admissibility.

---

### Issue 2: Determinism Canon - Missing Numeric Profile (HIGH PRIORITY)

**Spec Requirement (§7.2):**
- Canonical JSON (RFC 8785 JCS) or frozen binary
- UTF-8 NFC normalization
- Fixed key ordering
- No floating point in receipts
- Canonical numeric profile: scaled integers (QFixed), integer rationals, or interval arithmetic

**Current State:** Only "deterministic validity" axiom present (A3 in `1_objects.md`).

**Impact:** No guidance on numeric representation, serialization, or rounding.

**Action:** Add new section on Determinism Canon to docs/coh/.

---

### Issue 3: Trace Closure Principle (MEDIUM PRIORITY)

**Spec Requirement (§6):**
Legal steps compose into legal histories because receipts chain deterministically (hash + schema + policy + canon profile).

**Current State:** Not explicitly documented.

**Impact:** No guarantee of trace-level closure in categorical framework.

**Action:** Add to `3_category.md` or create new section.

---

### Issue 4: Implementation Contract (MEDIUM PRIORITY)

**Spec Requirement (§11):**
A Coh module must define:
1. `state_space` - canonical type representation of X
2. `potential` - deterministic evaluator V(x)
3. `receipt_schema` - canonical serialization and required fields
4. `verifier` - deterministic RV(x,r,x')
5. `canon_profile` - numeric representation, rounding rules, hash rules

**Current State:** Only type signatures in implementation notes (`1_objects.md` line 139-148).

**Action:** Expand implementation notes or add dedicated section.

---

### Issue 5: Minimal Proof Obligations (MEDIUM PRIORITY)

**Spec Requirement (§12):**
- Determinism Lemma
- Closure Lemma
- Soundness Lemma (Object-specific)

**Current State:** Not present.

**Action:** Add to docs or reference as requirements for implementations.

---

### Issue 6: Versioning and Drift Prevention (LOW PRIORITY)

**Spec Requirement (§13):**
Must freeze: schema_id, canon_profile_hash, policy_hash, verifier version, serialization version.

**Current State:** Not present.

**Action:** Add as implementation guidance.

---

## 5. CK-0 Integration Differences

### 5.1 Subcategory Definition

| Aspect | Spec v1.0.0 | Existing Docs | Status |
|--------|-------------|---------------|--------|
| Full subcategory | Coh_CK0 ⊆ Coh | Same | ✓ |
| V form | Weighted residual norm | Weighted residual norm | ✓ |
| Receipt fields | policy_id, budget, debt, residuals, hash | Same | ✓ |

**Consensus:** CK-0 integration is well-aligned between spec and existing docs.

---

## 6. PhaseLoom Differences

### 6.1 Functor Presentation

| Aspect | Spec v1.0.0 | Existing Docs | Status |
|--------|-------------|---------------|--------|
| As Endofunctor | PL: Coh → Coh | Same | ✓ |
| Memory coordinates | C, T, B, A | C, T, b, a | ✓ Minor notation |
| Potential form | w₀V + w_C C + w_T T + Φ(B) | Same | ✓ |

**Consensus:** PhaseLoom integration is well-aligned.

---

## 7. Proposed Updates

### Priority 1 (Must Fix)

1. **Update `docs/coh/1_objects.md`:**
   - Add Bounded-Tube Admissibility section (§3.2)
   - Revise object definition to optionally include 3-tuple form
   - Expand Determinism section

2. **Create `docs/coh/determinism_canon.md`:**
   - Section 7 content from spec
   - Canonical JSON rules
   - Numeric profile requirements

### Priority 2 (Should Fix)

3. **Update `docs/coh/3_category.md`:**
   - Add Trace Closure Principle

4. **Update `docs/coh/1_objects.md`:**
   - Add Implementation Contract section

5. **Update `docs/coh/2_morphisms.md`:**
   - Clarify morphism notation (consider adding f_R)

### Priority 3 (Nice to Have)

6. Add Proof Obligations as appendix or reference
7. Add Versioning section

---

## 8. Summary of Changes Required

| File | Changes Needed | Priority |
|------|----------------|----------|
| `docs/coh/1_objects.md` | Add bounded-tube, expand determinism, add implementation contract | HIGH |
| `docs/coh/2_morphisms.md` | Clarify notation | MEDIUM |
| `docs/coh/3_category.md` | Add trace closure | MEDIUM |
| New: `determinism_canon.md` | Full section 7 content | HIGH |
| `docs/coh/0_overview.md` | Update to reflect new structure | LOW |

---

## 9. Backward Compatibility Note

The existing docs are **not wrong** — they represent a valid categorical perspective on Coh. The spec v1.0.0 adds:

1. More practical engineering details (determinism, receipts, versioning)
2. Bounded-tube admissibility for practical systems
3. Formal proof obligations
4. Implementation contract requirements

The update should **extend** rather than replace the existing docs, adding the missing content while preserving the categorical foundations.
