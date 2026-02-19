# PhaseLoom Notation Ledger

**Canon Doc Spine v1.0.0** — Section 2

---

## 1. Base Objects

### 1.1 State Space

| Symbol | Type | Description |
|--------|------|-------------|
| (X) | Set | Base state space (Hilbert space, manifold, discrete state set) |
| (x \in X) | Element | Base execution state |
| (V: X \to \mathbb R_{\ge 0}) | Function | CK-0 violation functional |
| (v := V(x)) | Scalar | Violation value at state x |
| (v^+ := V(x^+)) | Scalar | Violation value at next state |
| (\Delta v := v^+ - v) | Scalar | Violation change |

### 1.2 Coh Object

| Symbol | Type | Description |
|--------|------|-------------|
| (\mathcal S) | CohObject | Coherence object (X, V, RV) |
| (\mathrm{RV}) | Set | Receipt/verification triples |
| (C_{\mathcal S}) | Subset | Admissible set: \{x \in X \mid V(x) = 0\} |

---

## 2. Extended PhaseLoom Coordinates

### 2.1 Memory Fiber

M := \mathbb R_{\ge 0} \times \mathbb R_{\ge 0} \times \mathbb R_{\ge 0} \times \mathbb R_{\ge 0}

| Symbol | Type | Description |
|--------|------|-------------|
| (C \in \mathbb R_{\ge 0}) | Scalar | Curvature accumulator (net amp over dissipation, decayed) |
| (T \in \mathbb R_{\ge 0}) | Scalar | Tension accumulator (braid inconsistency, decayed) |
| (b \in \mathbb R_{\ge 0}) | Scalar | Remaining budget |
| (a \in \mathbb R_{\ge 0}) | Scalar | Cumulative authority injected |

### 2.2 Extended State

| Symbol | Type | Description |
|--------|------|-------------|
| (\tilde X = X \times M) | Set | Extended state space |
| (\tilde x = (x, C, T, b, a)) | Element | Extended state tuple |

---

## 3. Derived Per-Step Quantities

### 3.1 Amplification and Dissipation

| Symbol | Definition | Description |
|--------|------------|-------------|
| (A) | (\Delta v)_+ = \max(\Delta v, 0) | Amplification (positive violation change) |
| (D) | (-\Delta v)_+ = \max(-\Delta v, 0) | Dissipation (negative violation change) |

### 3.2 Memory Updates

| Symbol | Definition | Description |
|--------|------------|-------------|
| (C^+) | \rho_C \cdot C + (A - D) | Next curvature value |
| (T^+) | \rho_T \cdot T + \Delta T_{\mathrm{inc}} - \Delta T_{\mathrm{res}} | Next tension value |
| (b^+) | b - \Delta b | Next budget |
| (a^+) | a + \Delta a | Next authority |

---

## 4. Governance Parameters (Fixed-Point)

### 4.1 Decay Parameters

| Symbol | Type | Range | Description |
|--------|------|-------|-------------|
| (\rho_C) | Fixed-point | [0, 1) | Curvature decay factor |
| (\rho_T) | Fixed-point | [0, 1) | Tension decay factor |

### 4.2 Cost Parameters

| Symbol | Type | Description |
|--------|------|-------------|
| (\kappa_A > 0) | Fixed-point | Amplification budget price |
| (\kappa_T > 0) | Fixed-point | Tension-increase budget price |
| (b_{\min} \ge 0) | Fixed-point | Interlock floor for budget |
| (\Theta) | Fixed-point | Admissibility threshold (optional) |

### 4.3 Weight Parameters

| Symbol | Type | Description |
|--------|------|-------------|
| (w_0 > 0) | Fixed-point | Weight for V(x) |
| (w_C > 0) | Fixed-point | Weight for curvature |
| (w_T > 0) | Fixed-point | Weight for tension |
| (w_b > 0) | Fixed-point | Weight for barrier |
| (w_a > 0) | Fixed-point | Weight for authority |
| (\epsilon > 0) | Fixed-point | Barrier constant |

---

## 5. Receipts and Hashes

### 5.1 Cryptographic Primitives

| Symbol | Type | Description |
|--------|------|-------------|
| (R_i) | Receipt | Atomic receipt |
| (\omega_i := H(R_i)) | Digest | Receipt hash |
| (M_S) | MerkleRoot | Merkle root for slab S |
| (H) | HashFunction | Canonical hash function |

### 5.2 Receipt Fields

| Symbol | Description |
|--------|-------------|
| (state\_hash\_prev) | Previous state hash |
| (state\_hash\_next) | Next state hash |
| (v\_prev) | Previous violation value |
| (v\_next) | Next violation value |
| (C\_prev, C\_next) | Curvature before/after |
| (T\_prev, T\_next) | Tension before/after |
| (b\_prev, b\_next) | Budget before/after |
| (a\_prev, a\_next) | Authority before/after |
| (delta\_T\_inc) | Tension increment |
| (delta\_T\_res) | Tension resolution |

---

## 6. Step Types

| Symbol | Description |
|--------|-------------|
| SOLVE | Standard solver step |
| REPAIR | Repair step (under interlock) |
| RESOLVE | Tension resolution step |
| AUTH\_INJECT | Authority injection step |

---

## 7. Threading Model

| Symbol | Type | Description |
|--------|------|-------------|
| (k(i)) | Function | Thread assignment for step i |
| (\sigma) | Label | Policy label |
| (op\_class) | Enum | solve/repair/resolve |

---

## 8. PhaseLoom Potential

### 8.1 Definition

\mathcal{V}_{PL}(\tilde x) := w_0 V(x) + w_C \max(C,0) + w_T T + w_b \psi(b) + w_a a

### 8.2 Barrier Function

\psi(b) := \frac{1}{b + \epsilon}

---

## 9. Fixed-Point Arithmetic

| Operation | Rule |
|-----------|------|
| Multiplication | mul\_fix(a, b) - truncate toward zero |
| Division | div\_fix(a, b) - truncate toward zero |
| Overflow | Consensus reject |
| Representation | Integer scaled (e.g., 10^6 for 6 decimal places) |

---

## 10. Serialization

| Rule | Description |
|------|-------------|
| JSON format | Canonical JSON (sorted keys, no whitespace) |
| Number normalization | Fixed-point string or scaled integer |
| UTF-8 | All strings in UTF-8 |
| Digest | SHA3-256 with prefix 'h:' |

---

*This notation ledger is authoritative. All implementations must use these exact definitions.*
