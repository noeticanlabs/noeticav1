# Noetica Refinement Profile v1

**Version:** 1.0  
**Status:** Draft  
**Related:** [`3_type_system.md`](3_type_system.md), [`5_concrete_syntax.md`](5_concrete_syntax.md)

---

## 4.1 Allowed Predicate Fragment

Refinement predicates in Noetica must be in the **Quantifier-Free Linear Arithmetic over Fixed-Point Rationals** (QF-LRA-FP) fragment.

### Predicate Form

A refinement predicate has the form:

```
a₀ + a₁·C + a₂·T + a₃·v + a₄·b < Θ
```

Where:

| Symbol | Description | Type |
|--------|-------------|------|
| `a₀` | Constant term | Fixed-point integer |
| `a₁` | Curvature coefficient | Fixed-point integer |
| `C` | Curvature accumulator | Variable |
| `a₂` | Tension coefficient | Fixed-point integer |
| `T` | Tension accumulator | Variable |
| `a₃` | Value coefficient | Fixed-point integer |
| `v` | V(x) measurement | Variable |
| `a₄` | Budget coefficient | Fixed-point integer |
| `b` | Budget | Variable |
| `Θ` | Threshold | Fixed-point constant |

### Restrictions

- **No products of variables**: `C × T` is illegal
- **No exponentials**: `C²` is illegal
- **No nonlinear terms**: `sin(C)`, `log(v)` are illegal
- **No quantifiers**: ∀, ∉ are illegal
- **No division by variables**: Only division by constants permitted

### Decision Domain

| Domain | Supported |
|--------|-----------|
| QF-LRA-FP | ✓ Full |
| QF-NRA | ✗ Not supported |
| QF-UF | ✗ Not supported |
| Linear integer arithmetic | ✓ With fixed scale |
| Mixed real/integer | ✗ Not supported |

---

## 4.2 Canonical Profile

The canonical profile defines fixed parameters for all refinement computations:

```json
{
  "version": "v1.0",
  "scale": 1000,
  "curvature_bound": 1000000,
  "tension_bound": 1000000,
  "budget_threshold": 1000000,
  "refinement_epsilon": 1,
  "truncation": "toward_zero"
}
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `scale` | 1000 | Fixed-point decimal places |
| `curvature_bound` | 10⁶ | Maximum curvature value |
| `tension_bound` | 10⁶ | Maximum tension value |
| `budget_threshold` | 10⁶ | Maximum budget threshold |
| `refinement_epsilon` | 1 | Minimum refinement step |
| `truncation` | toward_zero | Rounding mode |

---

## 4.3 Determinism Rules

To ensure deterministic lowering and verification:

### Fixed Scale Rule

All fixed-point values use the same scale (1000 by default). No per-value scales.

### Truncation Rule

All truncations round toward zero. No banker's rounding in refinement checks.

### No Solver Timeouts

The refinement prover must:
- Either prove the predicate
- Or fail to prove (not timeout)
- Failure to prove is a compile error

### Deterministic Prover

The refinement prover must be:
- Complete for QF-LRA-FP
- Terminating for all inputs
- Output-unique for same input

---

## 4.4 Refinement Checking Algorithm

### Algorithm

```
function check_refinement(predicate, env):
    1. Parse predicate into QF-LRA-FP form
    2. Validate all coefficients are integers
    3. Validate no prohibited terms (products, exponentials)
    4. Substitute current values from env
    5. Evaluate predicate
    6. If unprovable: raise compile error
    7. If false: raise compile error
    8. Otherwise: accept
```

### Compile-Time vs Runtime

| Check | When | Failure Mode |
|-------|------|--------------|
| Predicate syntax | Compile | Compile error |
| Predicate fragment | Compile | Compile error |
| Predicate provability | Compile | Compile error |
| Predicate truth | Runtime | STF rejection |

---

## 4.5 Refinement Profiles

### Default Profile

```
profile: default_v1
scale: 1000
threshold_formula: b > 0
```

### Strict Profile

```
profile: strict_v1
scale: 10000
threshold_formula: b > 100
```

### Relaxed Profile

```
profile: relaxed_v1
scale: 100
threshold_formula: b >= 0
```

---

## 4.6 Examples

### Valid Predicates

```
b > 0
C + T < 1000
v + b <= 2000
1000 * C < 500000
```

### Invalid Predicates

```
C * T < 1000        ✗ Product of variables
C^2 < 1000          ✗ Exponential
sin(C) < 1          ✗ Nonlinear
forall x. b > x     ✗ Quantifier
```

---

## 4.7 Integration with CK-0

Refinement predicates map to CK-0 violation functional:

```
V(x) = Σ w_k · ||r_k(x)/σ_k(x)||²
```

The refinement bound Θ corresponds to the CK-0 budget threshold from PolicyBundle.

See: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)

---

## 4.8 References

- Type system: [`3_type_system.md`](3_type_system.md)
- Syntax: [`5_concrete_syntax.md`](5_concrete_syntax.md)
- Integration: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)
