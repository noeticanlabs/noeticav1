# ASG Jacobian Assembly & PhaseLoom Integration Analysis

**Date:** 2026-02-19  
**Status:** Analysis Complete

---

## Issue 1: ASG Jacobian Assembly - Incomplete Implementation

### Current State

The Jacobian assembly in [`src/asg/assembly.py`](src/asg/assembly.py:11) contains placeholder code:

```python
# Lines 34-38 - ACTUAL CODE (placeholder)
for i, res_fn in enumerate(residuals):
    # Note: In practice, we'd need the actual state. For now, return shape info
    # This is a placeholder - actual implementation would compute J_i
    pass

# Lines 40-52 - FALLBACK (diagonal approximation)
# Diagonal blocks for each residual type
for i, res_config in enumerate(params.residuals):
    # Fill diagonal block with sqrt(weight) * identity
    O[row_start:row_start+N, col_start:col_start+N] = np.sqrt(weight) * np.eye(N)
```

### Impact

The diagonal approximation:
- Uses `√weight × I` instead of actual Jacobian blocks
- Produces overly optimistic κ₀ estimates
- Underestimates the true condition number of H_⊥
- May cause false positives in spectral verification

### Root Cause

The `assemble_jacobian` function requires:
1. A concrete state vector to compute residuals at
2. Residual functions that are differentiable (or finite-difference capability)
3. Proper block structure for cross-term coupling (ρ-θ, θ-G, etc.)

### Required Fix

Implement actual Jacobian computation:

```python
def assemble_jacobian(
    params: ASGParams,
    state: np.ndarray,
    residuals: List[Callable[[np.ndarray], np.ndarray]]
) -> np.ndarray:
    """Assemble true Jacobian from residual functions."""
    N = params.state_layout.dimension
    eps = 1e-8  # Finite difference step
    
    jacobian_blocks = []
    for res_fn in residuals:
        # Compute residual at current point
        r0 = res_fn(state)
        
        # Compute Jacobian columns via finite differences
        J_i = np.zeros((len(r0), len(state)))
        for j in range(len(state)):
            state_perturbed = state.copy()
            state_perturbed[j] += eps
            r_perturbed = res_fn(state_perturbed)
            J_i[:, j] = (r_perturbed - r0) / eps
        
        jacobian_blocks.append(J_i)
    
    # Stack and weight blocks
    return np.vstack([np.sqrt(w) * J for w, J in zip(params.weights, jacobian_blocks)])
```

### Dependencies

- Requires residual functions to be provided at call time (not just config)
- May need caching for performance
- Consider analytical Jacobians where available

---

## Issue 2: PhaseLoom Integration - Missing Dependencies

### Current State

PhaseLoom declares compatibility in [`src/phaseloom/__init__.py`](src/phaseloom/__init__.py:33):

```python
# Lines 33-36 - DECLARED BUT NOT IMPLEMENTED
COMPAT_CK0 = "ck0.v1"
COMPAT_COH = "coh.v1"
COMPAT_NK1 = "nk1.v1"
COMPAT_NK2 = "nk2.v1"
```

But has **zero imports** from these modules:

```bash
# Search results: NO external imports found in src/phaseloom/
```

### Evidence

| Module | Declares Compatibility | Has Import |
|--------|----------------------|------------|
| PhaseLoom | CK-0, Coh, NK-1, NK-2 | ✗ None |
| NK-1 | Uses CK-0 | ✓ Yes |
| NK-4G | Uses ASG | ✓ Yes |

### Impact

1. **No CK-0 DebtUnit**: PhaseLoom uses its own `FixedPoint` instead of CK-0's exact `DebtUnit`
2. **No Coh category**: PhaseLoom types don't implement CohObject interface
3. **No NK integration**: PhaseLoom receipts aren't compatible with NK-4G verifier
4. **Semantic boundary**: The float/integer boundary exists at PhaseLoom

### Root Cause

PhaseLoom was likely developed as a theoretical extension ahead of integration work. The documentation describes the intended integration, but the code doesn't enforce it.

### Required Fix (Two Options)

#### Option A: Full Integration (Recommended)

Add imports and type bridges:

```python
# src/phaseloom/types.py additions
from ck0.debtunit import DebtUnit
from coh.types import CohObject, CohMorphism

# Converters
def debtunit_to_fixedpoint(du: DebtUnit) -> FixedPoint:
    """Convert CK-0 DebtUnit to PhaseLoom FixedPoint."""
    return FixedPoint(scaled_value=du.value, scale=1000)

def fixedpoint_to_debtunit(fp: FixedPoint) -> DebtUnit:
    """Convert PhaseLoom FixedPoint to CK-0 DebtUnit."""
    return DebtUnit(fp.scaled_value)
```

#### Option B: Document as Layer Separation

If PhaseLoom is intentionally separate (for WASM isolation), document this architectural decision:

```
PhaseLoom operates in a separate trust domain:
- Internal: FixedPoint arithmetic (performance)
- Boundary: Convert to DebtUnit for NK verification
```

---

## Summary Table

| Issue | Severity | Effort | Recommendation |
|-------|----------|--------|----------------|
| ASG Jacobian | High | Medium | Implement finite-difference Jacobian |
| PhaseLoom CK-0 | Medium | High | Add DebtUnit bridge or document |
| PhaseLoom Coh | Low | Medium | Implement CohObject if needed |
| PhaseLoom NK | Medium | Medium | Bridge to NK-4G receipts |

---

## Files Affected

### ASG Jacobian Fix
- [`src/asg/assembly.py`](src/asg/assembly.py) - Implement true Jacobian
- [`src/asg/types.py`](src/asg/types.py) - May need residual function type
- [`tests/test_asg_operators.py`](tests/test_asg_operators.py) - Update golden vectors

### PhaseLoom Integration
- [`src/phaseloom/types.py`](src/phaseloom/types.py) - Add CK-0 imports
- [`src/phaseloom/receipt.py`](src/phaseloom/receipt.py) - Bridge to NK receipts
- [`docs/phaseloom/2_coh_integration.md`](docs/phaseloom/2_coh_integration.md) - Update docs

---

## References

- ASG overview: [`docs/asg/0_overview.md`](docs/asg/0_overview.md)
- PhaseLoom overview: [`docs/phaseloom/0_overview.md`](docs/phaseloom/0_overview.md)
- CK-0 DebtUnit: [`docs/ck0/2_debtunit.md`](docs/ck0/2_debtunit.md)
- NK-4G verifier: [`docs/nk4g/0_overview.md`](docs/nk4g/0_overview.md)
