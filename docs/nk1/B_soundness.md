# NK-1 Theorem Module — Measured Gate Soundness

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_measured_gate.md`](4_measured_gate.md), [`7_receipts.md`](7_receipts.md), [`8_verifier.md`](8_verifier.md)

---

## Overview

This document provides a **theorem-module style formalization** of NK-1 Measured Gate v1 with a **soundness proof sketch** that is tight enough for hostile readers but still implementable.

We are explicit about what is **proved**, what is **assumed**, and what is **verified mechanically**.

---

## Module Information

**Suggested module name:** `NK1.MeasuredGate.Soundness.v1`

**Purpose:** Prove that if NK-1 emits an **ACCEPT** receipt under `measured_gate.v1`, then the step is **CK-0 coherent** (i.e., satisfies invariants, determinism obligations, and the CK-0 Law of Coherence for the declared policy header).

This is a "certificate soundness" theorem: the receipt is a verifiable proof object.

---

## 0. Dependencies (Imports / Assumptions)

### 0.1 CK-0 Definitions

Assume CK-0 v1.0 is sealed and provides:

* **State space** (X)
* **Hard invariants** (I: X → {true, false})
* **Contract set** (𝒦), with deterministic residual maps (r_k), normalizers (σ_k > 0), weights (w_k)
* **Violation functional**:
  $$V(x) = \sum_{k=1}^{K} w_k \left\|\frac{r_k(x)}{\sigma_k(x)}\right\|_2^2$$
* **Debt**: D := V(x)
* **Disturbance policies** DP0–DP3 (deterministically checkable)
* **Service law** specified via S(D,B) with:
  * S(D, 0) = 0
  * 0 ≤ S(D, B) ≤ D
  * monotone in (D, B)
  * deterministic + canonicalizable
* **CK-0 Law** (canonical inequality):
  $$D_{k+1} \le D_k - S(D_k, B_k) + E_k$$

### 0.2 NK-1 Deterministic Substrate

Assume NK-1 v1.0 provides:

* Canonical arithmetic on DebtUnit (no floats)
* Canonical action descriptor parsing + hashing
* Canonical state serialization + hashing
* Receipt hashing and chaining
* Deterministic transition function (T: X × U → X) for allowed action types (U)

### 0.3 Well-Formed Policy Header

Assume a policy header (H) exists containing (at minimum):

* `contract_set_id`
* `V_policy_id` (must be `CK0.v1`)
* `service_policy_id`, `service_instance_id`
* `disturbance_policy_id`
* canonicalization/version identifiers

And (H) is hash-committed into the receipt chain.

---

## 1. Definitions

### 1.1 Measured Gate Step Relation

Given:

* current state x ∈ X
* action descriptor u ∈ U
* budget B ≥ 0
* disturbance E ≥ 0 (provided per DP1/DP2, computed per DP3, or E=0 in DP0)

Define:

* x' := T(x, u)
* D := V(x)
* D' := V(x')

Define gate acceptance predicate:

$$\text{ACCEPT}(x, u, B, E) \iff \Big(I(x) = \text{true}\Big) \land \Big(I(x') = \text{true}\Big) \land \Big(\text{DP}(E; H, x, u)\Big) \land \Big(D' \le D - S(D, B) + E\Big)$$

Where DP(·) is the disturbance policy check implied by H.

### 1.2 Receipt Object

A measured gate receipt R is a structured record containing at least:

| Field | Description |
|-------|-------------|
| `state_hash_pre` | hash(encode(x)) |
| `state_hash_post` | hash(encode(x')) |
| `action_hash` | hash(canon(u)) |
| `policy_header_hash` | hash(H) |
| `D_pre` | D |
| `D_post` | D' |
| `B` | budget |
| `E` | disturbance |
| `S_applied` | S(D, B) (recommended) |
| `decision` | ACCEPT |
| `invariants_pass` | true |
| `disturbance_check_pass` | true |
| `law_check_pass` | true |
| receipt hash chain fields | - |

NK-1 defines a deterministic `encode_receipt(R)` that hashes to `receipt_hash`.

---

## 2. Soundness Theorem (NK-1 → CK-0 Coherence)

### Theorem: Measured Gate Soundness v1

Let H be a fixed policy header satisfying CK-0/NK-1 well-formedness.

Let NK-1 execute one measured gate step on inputs (x, u, B) under H, producing receipt R with `decision = ACCEPT`.

Assume:

1. NK-1 canonical parsing/canonicalization succeeds (schema-valid).
2. NK-1 computes x' = T(x, u) deterministically.
3. NK-1 computes D = V(x) and D' = V(x') deterministically in DebtUnit.
4. Disturbance policy check passes under H.
5. Receipt hash chain verifies.

**Then** the transition x → x' is **CK-0 coherent** for that step, i.e.:

* Hard invariants hold (per CK-0 rail policy)
* The debt update inequality holds:
  $$V(x') \le V(x) - S(V(x), B) + E$$
* And the step is replay-verifiable from R and the allowlisted policy header H.

### Intuition

An ACCEPT receipt is a machine-checkable proof that the CK-0 law holds for that step.

---

## 3. Proof Sketch (What the Verifier Proves)

The proof splits into three parts: (i) identity, (ii) measurement, (iii) law enforcement.

### 3.1 Identity / Determinism (Receipt Correctness)

Because NK-1 uses canonical encodings:

* `state_hash_pre` commits to x
* `action_hash` commits to canonicalized u
* `policy_header_hash` commits to H

The verifier recomputes these hashes; equality implies the receipt binds the exact inputs.

**This prevents "wedgeable parse" ambiguity.**

### 3.2 Measurement Correctness (Debt Values Are What They Claim)

Given the committed x and H:

* The contract set is identified by `contract_set_id`
* The residual, sigma, weight specs are allowlisted/declared by that set
* Canonical arithmetic ensures V(x) is computed uniquely

The verifier either:

* recomputes V(x) and V(x') exactly, or
* verifies commitments (hashes) plus sufficient statistics, depending on policy

**Thus the receipt's D_pre and D_post are validated as V(x) and V(x').**

### 3.3 Service/Disturbance Correctness

From `service_policy_id/service_instance_id` and (D, B):

* Verifier recomputes S(D, B) deterministically.
* From `disturbance_policy_id`, verifier checks E is allowed:
  * **DP0**: E = 0
  * **DP1**: E ≤ Ē
  * **DP2**: E ≤ β(event)
  * **DP3**: E = ℰ(x, u; θ)

**Thus the computed servicing and disturbance are policy-compliant.**

### 3.4 Law Enforcement

Finally, verifier checks the inequality:

$$D' \le D - S(D, B) + E$$

Given 3.2 and 3.3, this is exactly:

$$V(x') \le V(x) - S(V(x), B) + E$$

**So the CK-0 law holds for that step.**

### 3.5 Conclusion

All CK-0 step obligations required for coherence (as frozen by policy header H) are satisfied and replay-checkable from the receipt.

Therefore the ACCEPT receipt is a **sound certificate of CK-0 coherence** for that step.

∎

---

## 4. "No Hidden Assumptions" Checklist (Hostile Review Appendix)

To prevent reviewers from claiming handwaving, explicitly list what is assumed and where it is enforced:

| # | Assumption | Where Enforced |
|---|------------|----------------|
| 1 | Residual definitions are allowlisted and versioned | `contract_set_id` |
| 2 | Canonical arithmetic is frozen | DebtUnit + rounding rules |
| 3 | Transition function is deterministic for allowed action types | Runtime conformance |
| 4 | Policy header is hash committed in receipts | Receipt field |
| 5 | E policy is bounded by DP0–DP3 | No "excuse term" |
| 6 | Acceptance implies inequality check passed | Receipt field + verifier |
| 7 | Replay implies same decision | Verifier recomputes all checks |

**No proof step requires "trust the runtime" beyond the frozen canonicalization + allowlist.**

---

## 5. Strengthening Lemmas (Optional but Useful)

These aren't required for soundness, but they're powerful:

### Lemma A: Deterministic Decision

If two compliant implementations share the same:

* policy header H
* state x
* action descriptor u
* budget B

Then they produce the same decision ACCEPT/REJECT and the same receipt hash.

**Proof sketch:** canonical parsing + DebtUnit arithmetic + deterministic T and V.

### Lemma B: Compositional Coherence

If steps k = 0..n-1 each have ACCEPT receipts that verify, then the full run is CK-0 coherent over those steps.

**Proof sketch:** apply step-soundness inductively; hash chain ensures sequencing.

---

## 6. Lean-Shaped Skeleton (Minimal)

If you want this Lean-ready, the core statement looks like:

```lean
-- Define acceptance predicate
def Accept (x : X) (u : U) (B : DebtUnit) (R : Receipt) : Prop :=
  InvariantsHold x ∧
  InvariantsHold (T x u) ∧
  DisturbancePolicyCheckPassed R E ∧
  V (T x u) ≤ V x - S (V x) B + E

-- Define verification predicate  
def Verifies (R : Receipt) : Prop :=
  HashChainValid R ∧
  PolicyHeaderValid R ∧
  DebtComputationValid R ∧
  ServiceLawValid R ∧
  LawInequalityHolds R

-- Main soundness theorem
theorem soundness (R : Receipt) (h : Verifies R) (d : decision R = ACCEPT) :
  CK0_Coherent (state_pre R) (state_post R) (budget R) (disturbance R) :=
  -- ... proof steps from sections 3.1-3.5
```

---

## 7. Summary

| Concept | What It Means |
|---------|---------------|
| **ACCEPT receipt** | Machine-checkable proof of CK-0 coherence |
| **Soundness** | ACCEPT → CK-0 law holds |
| **Verification** | Independent recomputation from receipt + policy |
| **Determinism** | Same inputs → same outputs |
| **No hidden assumptions** | Everything checked or allowlisted |

---

*See also: [`4_measured_gate.md`](4_measured_gate.md), [`7_receipts.md`](7_receipts.md), [`8_verifier.md`](8_verifier.md)*
