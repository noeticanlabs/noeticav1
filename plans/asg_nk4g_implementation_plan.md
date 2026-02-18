# ASG + NK-4G Implementation Plan

**Date:** 2026-02-18  
**Status:** Draft  
**Scope:** Complete ASG spectral module and NK-4G runtime integration for Noetica v1.0

---

## Architecture Overview (Clean Spine)

```
Symbolic Layer
   ↓
NK-3 (Meaning Preservation)

Execution Layer
   ↓
NK-2 (Deterministic Scheduler)

Policy Layer
   ↓
NK-1 (Governance Thresholds)

Violation Layer
   ↓
CK-0 (Residual Definition)

Dynamics Layer
   ↓
NEC (Proximal Correction Law)

Curvature Layer
   ↓
ASG (Spectral & Semantic Certificate)

Audit Layer
   ↓
NK-4G (Receipt Protocol)
```

---

## Layer Ownership Summary

| Layer | Mathematical Object | Responsibilities |
|-------|---------------------|------------------|
| NK-3 | L: NSC IR → OpSet | Meaning preservation, IR normalization |
| NK-2 | E: OpSet → Ordered Execution | Deterministic batching, failure handling |
| NK-1 | P: {thresholds, caps, invariants} | Policy gates, pass/fail decisions |
| CK-0 | V(u) = ½ Σ wᵢ |rᵢ(u)|² | Violation measurement |
| NEC | zₖ = U_τ xₖ, xₖ₊₁ = prox_{λₖV}(zₖ) | Proximal dynamics, witness inequality |
| ASG | H = OᵀO, κ₀ = λₘᵢₙ(H⊥), Γₛₑₘ | Spectral certificates, semantic margins |
| NK-4G | Receipt fields | Audit protocol, consistency verification |

---

## Part A: Documentation Fixes

### A1: NEC Prox Witness (docs/nec/7_receipt_witness.md)

**Issues:**
- Uses yₖ as "proximal point" but conflates with drift anchor
- Claims "V never increases" universally (false in split model)
- Inconsistent τ vs lambda naming

**Canonical Correction:**

| Old | New | Definition |
|-----|-----|------------|
| yₖ | zₖ | Drift point: zₖ = U_τ xₖ (proposal from model) |
| x_{k+1} | x_{k+1} | Correction: x_{k+1} = prox_{λₖV}(zₖ) |
| witness | witness | V(x_{k+1}) ≤ V(zₖ) - (1/2λₖ)||x_{k+1}-zₖ||² |

**Receipt Fields to Add:**
- `z_k` (drift point) - replaces `y_k`
- `z_hash` / `z_emb` (canonical bytes for verifier)
- `lambda_k` (rename tau_factor consistently)

### A2: NK-4G Spectral Doc (docs/nk4g/4_spectral_analysis.md)

**Issues:**
- Claims Hessian is PSD because "coherence implies convex-like behavior" (not guaranteed)
- Presents (I + τH)⁻¹(I + τA) as canonical NK-4G scheme (should be unitary drift + prox)
- Lemma 4.1 step-size bound is heuristic

**Canonical Correction:**

| Section | Change |
|---------|--------|
| Hessian PSD claim | Add [ASSUMPTION]: local smooth surrogate Φ exists with H = ∇²Φ PSD, OR [MODEL]: use ASG's computable quadratic model (H = O⊥ᵀO⊥) always PSD by construction |
| Step operator | Clarify NK-4G uses unitary drift + prox, not (I+τA) form |
| Lemma 4.1 | Mark as [HEURISTIC] pending formal derivation |

---

## Part B: Implementation Modules

### B1: ASG Module (src/asg/)

```
src/asg/
├── __init__.py
├── types.py              # ASGParams, ASGReceipt, ASGStateLayout
├── operators.py         # Discrete gradient operators, P⊥ projector
├── assembly.py           # O matrix assembly, H = OᵀO, digests
├── spectral.py          # κ₀ estimation, Γₛₑₘ computation
├── watchdog.py          # Prox watchdog receipts
└── demo/                # Optional demo scripts
```

#### B1.1 types.py

```python
@dataclass
class ASGStateLayout:
    """State vector layout: u = (ρ, θ, G, ζ) ∈ R^{4N}"""
    rho_start: int       # ρ block start index
    theta_start: int     # θ block start index
    gamma_start: int     # G block start index
    zeta_start: int      # ζ block start index
    dimension: int       # N (system size)

@dataclass
class ASGParams:
    """ASG computation parameters"""
    state_layout: ASGStateLayout
    weights: List[float]
    alpha_l: float      # α_L: linguistic coupling strength
    alpha_g: float      # α_G: gradient coupling strength
    w_theta: float      # w_θ: theta penalty weight

@dataclass
class ASGReceipt:
    """Spectral certificate receipt"""
    kappa_est: float
    gamma_sem: float
    semantic_margin: float
    projector_id: str
    operator_digest: str
    estimation_method: str  # "eigsh", "lobpcg", etc.
```

#### B1.2 operators.py

```python
def build_gradient_operator_1d_ring(N: int) -> np.ndarray:
    """Build discrete gradient operator for 1D ring topology.
    
    Returns: D matrix (N × N) where D[i,j] = 1 if j=i+1, -1 if j=i-1
    """

def build_gradient_operator_2d_torus(M: int, N: int) -> np.ndarray:
    """Build discrete gradient operator for 2D torus topology."""

def build_mean_zero_projector(dimension: int) -> np.ndarray:
    """Build P_⊥ = I - (1/N) 11^T that removes mean(θ) mode.
    
    Returns: Projection matrix that enforces Σ θ_i = 0
    """
```

#### B1.3 assembly.py

```python
def assemble_jacobian(params: ASGParams, residuals: List[Callable]) -> np.ndarray:
    """Assemble O matrix: O = [√w_i J_i]
    
    Returns: Jacobian matrix (m × 4N)
    """

def assemble_hessian_model(jacobian: np.ndarray) -> np.ndarray:
    """Compute H = O^T O (always PSD by construction)
    
    Returns: Hessian model matrix (4N × 4N)
    """

def compute_operator_digest(params: ASGParams, hessian: np.ndarray) -> str:
    """Compute SHA-256 digest of operator structure + parameters.
    
    Returns: Hex digest string
    """
```

#### B1.4 spectral.py

```python
def estimate_kappa_0(hessian_perp: np.ndarray, method: str = "eigsh") -> float:
    """Estimate κ₀ = λ_min(H_⊥) - smallest eigenvalue of reduced Hessian.
    
    Args:
        hessian_perp: Projected Hessian (P_⊥ H P_⊥)
        method: Estimation method ("eigsh", "lobpcg", "power")
    
    Returns:
        κ₀ estimate (≥ 0 by construction)
    """

def compute_semantic_direction(state: np.ndarray, layout: ASGStateLayout) -> np.ndarray:
    """Compute semantic direction v_sem = (0, G, -θ, 0)
    
    Returns: Semantic direction vector
    """

def compute_semantic_rayleigh(hessian_perp: np.ndarray, v_sem: np.ndarray) -> float:
    """Compute Γ_sem = (v_sem^T H_⊥ v_sem) / (v_sem^T v_sem)
    
    Returns: Semantic stiffness
    """

def compute_margin(gamma_sem: float, kappa_0: float) -> float:
    """Compute M = Γ_sem / κ₀
    
    Returns: Semantic margin
    """
```

#### B1.5 watchdog.py

```python
class ProxWatchdog:
    """Prox inequality verification"""
    
    def __init__(self, params: ASGParams):
        self.params = params
    
    def verify_prox_inequality(
        self,
        v_before: float,
        v_after: float,
        drift_point: np.ndarray,
        correction_point: np.ndarray,
        lambda_k: float
    ) -> bool:
        """Verify: V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||²
        
        Returns: True if inequality holds
        """
    
    def check_structural_drift(
        self,
        drift_point: np.ndarray,
        original_state: np.ndarray
    ) -> bool:
        """Verify drift is within allowed bounds"""
    
    def emit_watchdog_receipt(
        self,
        v_before: float,
        v_after: float,
        drift_point: np.ndarray,
        correction_point: np.ndarray,
        lambda_k: float,
        prox_pass: bool,
        drift_pass: bool
    ) -> ASGReceipt:
        """Emit deterministic watchdog receipt"""
```

### B2: NK-4G Module (src/nk4g/)

```
src/nk4g/
├── __init__.py
├── receipt_fields.py     # NK-4G receipt schema extensions
├── verifier.py          # NK-4G consistency verification
└── policy.py            # NK-4G policy threshold enforcement
```

#### B2.1 receipt_fields.py

```python
@dataclass
class NK4GReceiptExtension:
    """NK-4G specific receipt fields for spectral certificates"""
    kappa_est: float
    gamma_sem: float
    semantic_margin: float
    projector_id: str          # e.g., "mean_zero_theta_v1"
    operator_digest: str       # Hash of operator structure
    estimation_method: str     # "eigsh", "lobpcg", "exact"
    spectral_gate_passed: bool
    margin_warned: bool
```

#### B2.2 verifier.py

```python
class NK4GVerifier:
    """Verify NK-4G receipt consistency"""
    
    def verify_receipt_fields(self, receipt: NK4GReceiptExtension) -> bool:
        """Verify all required fields present and consistent"""
    
    def verify_prox_witness(self, receipt: NK4GReceiptExtension) -> bool:
        """Verify prox witness inequality fields consistent"""
    
    def verify_policy_thresholds(
        self,
        receipt: NK4GReceiptExtension,
        policy: PolicyBundle
    ) -> bool:
        """Verify κ₀ ≥ NK4G_KAPPA_MIN and margin thresholds"""
```

#### B2.3 policy.py

```python
class NK4GPolicyKeys:
    """Policy keys for NK-4G/ASG governance"""
    
    NK4G_KAPPA_MIN = "nk4g_kappa_min"           # Minimum κ₀ threshold
    NK4G_MARGIN_MIN = "nk4g_margin_min"         # Minimum semantic margin
    NK4G_PROJECTOR_ID = "nk4g_projector_id"      # Required projector
    ASG_MODEL_ID = "asg_model_id"                # Residual architecture version
    ASG_ESTIMATION_METHOD = "asg_estimation"    # κ₀ estimation method
```

---

## Part C: Conformance

### C1: ASG Golden Vectors

| File | Description |
|------|-------------|
| `conformance/asg_operator_digest_golden.json` | κ₀ on 1D ring N=32, 2D torus 8×8 |
| `conformance/asg_kappa0_golden.json` | κ₀ estimates with tolerance |
| `conformance/asg_gamma_sem_golden.json` | Γₛₑₘ for canonical semantic vector |
| `conformance/asg_watchdog_receipt_golden.json` | PASS/FAIL cases |

### C2: NK-4G Receipt Extensions

| File | Description |
|------|-------------|
| `conformance/nk4g_receipt_extension_golden.json` | Receipt schema validation |

### C3: Policy Bundle Updates

Add to `src/nk1/policy_bundle.py` and `conformance/policy_golden.json`:
- `NK4G_KAPPA_MIN`
- `NK4G_MARGIN_MIN`
- `NK4G_PROJECTOR_ID`
- `ASG_MODEL_ID`
- `ASG_ESTIMATION_METHOD`

---

## Part D: Tests

### D1: ASG Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_asg_operator_digest.py` | O matrix assembly, H = OᵀO PSD |
| `tests/test_asg_kappa0_monotone.py` | κ₀ increases with w_θ (monotone trend) |
| `tests/test_asg_massless_projection.py` | With α_L=0, κ₀ collapses without P⊥ |
| `tests/test_asg_semantic_margin.py` | Γₛₑₘ computation, margin M finite |
| `tests/test_asg_prox_watchdog.py` | Prox inequality PASS/FAIL |

### D2: NK-4G Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_nk4g_receipt_schema.py` | Receipt field validation |
| `tests/test_nk4g_policy_thresholds.py` | κ₀, margin threshold enforcement |

---

## Part E: Documentation

### E1: New ASG Documentation Spine

```
docs/asg/
├── 0_overview.md          # ASG scope and positioning
├── 1_state_model.md       # u = (ρ, θ, G, ζ) layout
├── 2_residual_model.md    # Φ(u), Jacobian assembly
├── 3_spectral_quantities.md # κ₀, Γₛₑₘ, M definitions
├── 4_integration_nec.md  # NEC split semantics
├── 5_integration_nk4g.md # Receipt protocol
└── 6_proof_obligations.md # Open problems, assumptions
```

### E2: NK-4G Documentation Updates

- `docs/nk4g/0_overview.md`: Add "ASG integration slot"
- `docs/nk4g/7_verifier_consistency.md`: Define required certificate fields

---

## Part F: Canonical Naming

### Split Vocabulary (Frozen)

| Canonical | Deprecated |
|-----------|------------|
| zₖ (drift point) | y_k, proximal point, tau_factor |
| x_{k+1} (correction) | y_k output |
| λₖ (prox parameter) | tau, g_k, tau_factor |
| H = OᵀO | Hessian (generic) |
| κ₀ | lambda_min, eigenvalue_floor |
| Γₛₑₘ | semantic_stiffness, rayleigh_quotient |

---

## Implementation Order

1. **Fix NEC witness doc** (A1)
2. **Fix NK-4G spectral doc** (A2)
3. **Add ASG types + operators** (B1.1, B1.2)
4. **Add ASG assembly + spectral** (B1.3, B1.4)
5. **Add ASG watchdog** (B1.5)
6. **Add NK-4G receipt fields + verifier** (B2.1, B2.2)
7. **Update policy bundle** (C2)
8. **Add ASG tests** (D1)
9. **Add NK-4G tests** (D2)
10. **Add ASG docs** (E1)
11. **Update NK-4G docs** (E2)
12. **Canonical naming pass** (F)

---

## Completion Criteria

ASG + NK-4G is complete when:
- [ ] κ₀ stable under refinement
- [ ] Margin M measurable
- [ ] NEC witness aligned
- [ ] NK-4G receipt consistent
- [ ] No document contradicts split semantics
- [ ] All golden vectors pass
- [ ] All tests pass
