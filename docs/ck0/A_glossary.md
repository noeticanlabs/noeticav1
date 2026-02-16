# CK-0 Glossary

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md)

---

## A

### Applicability Predicate
A predicate `A_k(x)` that determines whether a contract is active for state `x`. If `false`, the contract contributes zero to `V(x)`.

---

## B

### Budget (`B_k`)
The declared service capacity for step `k`. Non-negative integer representing resources available to reduce debt.

---

## C

### Canonical Encoding
The unique, deterministic representation of a data structure. No wedgeable forms, no equivalent alternatives.

### CK-0
The canonical mathematical substrate for Phase 0 coherence enforcement. Defines Coherence as an enforceable dynamical law.

### Contract
A declaration of residual `r_k`, normalizer `σ_k`, weight `w_k`, and applicability `A_k` that contributes to the violation functional.

### Contract Set
An ordered collection of contracts `𝒦 = (1, ..., K)`.

---

## D

### Debt (`D_k`)
The violation value at step `k`, defined as `D_k := V(x_k)`. Represents how "incoherent" the system is.

### Disturbance (`E_k`)
The declared external disturbance bound for step `k`. Non-negative value representing "stuff that happens to you."

### Disturbance-Separated Form
The CK-0 law form where `Φ(D,0)=D`, meaning all disturbance effects are explicitly in `E_k`, not hidden in the servicing map.

---

## E

### Enforceable
A property that can be verified by an independent party without trusting the prover.

---

## G

### Gate Decision
The outcome of coherence verification: `accept`, `reject`, or `repair`.

---

## H

### Hash Chain
A linked sequence of receipts where each receipt references the previous via hash, forming a tamper-evident ledger.

### Hessian
The matrix of second derivatives of the violation functional. Used in curvature bounds.

---

## I

### Invariant (`I(x)`)
A hard constraint that must hold. Unlike `V(x)`, invariant failures are terminal or classified events.

---

## L

### Ledger (Ω-Ledger)
The complete sequence of receipts `Ω = [receipt_0, receipt_1, ..., receipt_k]`.

---

## N

### NEC (No-Extraneous-Curvature)
The theorem module providing curvature interaction bounds that prevent implementation cheating.

### Normalizer (`σ_k`)
A positive scale factor for contract residuals. Used in computing normalized residuals.

---

## O

### Ω-Ledger
See Ledger.

---

## R

### Receipt
An immutable record of a single step's execution, containing all fields needed for replay verification.

### Residual (`r_k(x)`)
The deviation of state `x` from the ideal for contract `k`.

### Replay Verification
The process of verifying a run by recomputing from receipts without trusting the original execution.

---

## S

### Servicing Map (`S(D, B)`)
A function that computes how much debt is reduced by budget. Defined with constraints: `S(D,0)=0`, `0 ≤ S(D,B) ≤ D`.

---

## T

### Transition Contract (`T(x, u)`)
The deterministic function defining state evolution: `x_{k+1} = T(x_k, u_k)`.

---

## V

### Violation Functional (`V(x)`)
The CK-0 coherence metric: `V(x) = Σ w_k ||r_k(x)/σ_k(x)||²`. Zero means coherent.

---

## W

### Weight (`w_k`)
A non-negative scalar multiplier for a contract's contribution to `V(x)`.
