# PhaseLoom CK-0 / Coh Integration

**Canon Doc Spine v1.0.0** — Section 3

---

## 1. CK-0 Faithfulness Axiom

### 1.1 Statement

**Axiom A1 (Faithfulness):**

[
V(x)=0 \iff x\in C_{\mathcal S}.
]

Where:
- (V: X \to \mathbb R_{\ge 0}) is the CK-0 violation functional
- (C_{\mathcal S} \subseteq X) is the admissible set
- (V(x) = 0) iff x is exactly admissible

### 1.2 Implementation Reference

See [`src/ck0/violation.py`](/src/ck0/violation.py) for V(x) implementation.

```python
# Faithfulness check
def is_admissible(state, eps0=0.0):
    return abs(V(state) - 0.0) <= eps0
```

---

## 2. Coh Object Definition

### 2.1 Base Coh Object

A Coh object is a 5-tuple:

\mathcal S = (X, V, \mathrm{RV})

Where:
- (X): State space (Hilbert space, manifold, discrete set)
- (V: X \to \mathbb R_{\ge 0}): Violation functional
- (\mathrm{RV}): Receipt/verification triples

### 2.2 Implementation Reference

See [`src/coh/objects.py`](/src/coh/objects.py) for CohObject definition.

```python
@dataclass
class CohObject:
    """CohObject: (X, Rec, V, Δ, RV)"""
    state_carrier: StateCarrier
    receipt_carrier: ReceiptCarrier
    violation_fn: Callable[[Any], float]
    delta_fn: Callable[[Any, Any], Delta]
    rv_fn: Callable[[Any], List[Tuple]]
```

---

## 3. PhaseLoom as Endofunctor

### 3.1 Functor Definition

Define the PhaseLoom endofunctor:

[
\mathrm{PL}:\mathbf{Coh}\to\mathbf{Coh}
]

### 3.2 Object Map

\mathrm{PL}(X,V,\mathrm{RV}) = (\tilde X, V_{PL}, \mathrm{RV}_{PL})

Where:
- (\tilde X = X \times M): Extended state space
- (M = \mathbb R_{\ge 0}^4): Geometric memory fiber
- (V_{PL}): Extended violation functional
- (\mathrm{RV}_{PL}): Extended receipt/verification

### 3.3 Morphism Map

For a morphism (f: \mathcal S \to \mathcal S') in \mathbf{Coh}, define:

\mathrm{PL}(f): \mathrm{PL}(\mathcal S) \to \mathrm{PL}(\mathcal S')

With:
- State component: (x, C, T, b, a) \mapsto (f_X(x), C', T', b', a')
- Receipt component: Tracked via PhaseLoom receipts

---

## 4. Extended Violation Functional

### 4.1 Definition

V_{PL}(\tilde x) combines base violation with geometric memory:

V_{PL}(\tilde x) = w_0 \cdot V(x) + w_C \cdot \max(C, 0) + w_T \cdot T + w_b \cdot \psi(b) + w_a \cdot a

### 4.2 Weights

| Weight | Description | Typical Value |
|--------|-------------|---------------|
| (w_0) | Base violation weight | 1.0 |
| (w_C) | Curvature weight | 0.1 |
| (w_T) | Tension weight | 0.05 |
| (w_b) | Budget barrier weight | 0.01 |
| (w_a) | Authority weight | 0.001 |

---

## 5. Functor Laws Verification

### 5.1 Identity Law

\mathrm{PL}(\mathrm{id}_{\mathcal S}) = \mathrm{id}_{\mathrm{PL}(\mathcal S)}

Verification:
```python
def test_identity_law():
    S = create_coh_object()
    PL_S = PL_functor.apply(S)
    id_PL_S = PL_functor.apply_identity(S)
    assert PL_S.state_map == id_PL_S.state_map
```

### 5.2 Composition Law

\mathrm{PL}(g \circ f) = \mathrm{PL}(g) \circ \mathrm{PL}(f)

Verification:
```python
def test_composition_law():
    f: S -> S'
    g: S' -> S''
    PL_gf = PL_functor.apply_compose(g, f)
    PL_g_PL_f = PL_functor.compose(PL_functor.apply(g), PL_functor.apply(f))
    assert PL_gf.state_map == PL_g_PL_f.state_map
```

---

## 6. Integration with Existing Modules

### 6.1 CK-0 Integration Points

| CK-0 Component | PhaseLoom Usage |
|----------------|-----------------|
| Violation V(x) | Base term in V_PL |
| State space X | Base of extended \tilde X |
| Budget law | Extended with curvature cost |
| Receipts | Extended with PL fields |

### 6.2 Coh Category Integration

| Coh Component | PhaseLoom Usage |
|---------------|-----------------|
| CohObject | Extended to PL object |
| CohMorphism | Extended to PL morphism |
| TimeFunctor | Extended with memory |
| Functor laws | Verified for PL |

### 6.3 NK-1 Integration

| NK-1 Component | PhaseLoom Usage |
|----------------|-----------------|
| ReceiptCanon | Extended to PL receipts |
| Policy bundle | Threading model |
| Delta norms | Delta T computation |

### 6.4 NK-2 Integration

| NK-2 Component | PhaseLoom Usage |
|----------------|-----------------|
| Scheduler | Interlock enforcement |
| Batch | Step type selection |
| ExecPlan | Memory updates |

---

## 7. Receipt Schema Integration

### 7.1 Base Receipt Fields (NK-1)

```python
# From src/nk1/receipt_canon.py
ReceiptCanon fields:
- receipt_type
- state_hash_before
- state_hash_after
- debt_before
- debt_after
- operations
- batch_id
- timestamp
- policy_digest
```

### 7.2 PhaseLoom Extensions

Additional fields for `coh.receipt.pl.v1`:
```python
PLReceipt fields:
- C_prev, C_next      # Curvature
- T_prev, T_next      # Tension  
- b_prev, b_next      # Budget
- a_prev, a_next      # Authority
- delta_T_inc         # Tension increment
- delta_T_res         # Tension resolution
- step_type           # SOLVE/REPAIR/RESOLVE/AUTH_INJECT
```

---

## 8. Status

- [x] Faithfulness axiom defined
- [x] Coh object integration specified
- [x] Endofunctor structure defined
- [ ] Functor law verification (implementation)
- [ ] Receipt schema integration (implementation)

---

*This document defines how PhaseLoom integrates with CK-0 and Coh. All implementations must respect these integration points.*
