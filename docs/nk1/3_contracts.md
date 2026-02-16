# NK-1 Contract Measurement Engine

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_constants.md`](1_constants.md), [`2_debtunit.md`](2_debtunit.md), [`../ck0/3_violation_functional.md`](../ck0/3_violation_functional.md)

---

## Overview

The Contract Measurement Engine implements CK-0's canonical violation functional:

```
V(x) = Σ_{k=1}^{K} w_k · ||r̃_k(x)||₂²

where r̃_k(x) = r_k(x) / σ_k(x)
      if A_k(x) = false, then r̃_k(x) ≡ 0
```

All computations use **DebtUnit** exclusively.

---

## Contract Definition

### Contract Fields

Each contract contains:

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | string | Unique identifier |
| `residual_fn_id` | string | Allowlisted residual function ID |
| `dim_m_k` | int | Dimension of residual vector |
| `sigma_spec_id` | string | Normalizer spec (constant or computed) |
| `weight_spec_id` | string | Weight fraction p/q |
| `applicability_predicate_id` | string | Optional activation predicate |
| `units_id` | string | Optional unit declaration |
| `version` | int | Contract version |

### ContractSet Structure

```python
class Contract:
    contract_id: str
    residual_fn_id: str          # Allowlisted identifier
    dim_m_k: int                 # Residual dimension
    sigma_spec_id: str           # Normalizer spec
    weight_spec_id: str          # Weight p/q as string
    applicability_predicate_id: str | None
    units_id: str | None
    version: int = 1

class ContractSet:
    contracts: list[Contract]     # Ordered list
    
    @property
    def contract_set_id(self) -> str:
        """Hash of canonical contract list bytes."""
        return hash(canonical_contract_list_bytes(self.contracts))
```

---

## Weight Canonicalization

### Reduction to Lowest Terms

All weights MUST be reduced before use:

```python
def reduce_weight(p: int, q: int) -> tuple[int, int]:
    """Reduce fraction p/q to lowest terms."""
    if q == 0:
        raise ValueError("Denominator cannot be zero")
    
    g = gcd(abs(p), abs(q))
    return (p // g, q // g)
```

### LCM Aggregation

When combining weights, compute Q:

```python
def compute_lcm(denominators: list[int]) -> int:
    """Compute LCM of denominators."""
    if not denominators:
        return 1
    
    result = denominators[0]
    for d in denominators[1:]:
        result = lcm(result, d)
    return result

def lcm(a: int, b: int) -> int:
    """Compute LCM of two integers."""
    return abs(a * b) // gcd(a, b)
```

---

## Residual Measurement

### Residual Function Registry

NK-1 maintains an **allowlist** of residual functions - never executes unknown code.

```python
class ResidualRegistry:
    """Allowlist of known residual functions."""
    
    @staticmethod
    def compute(residual_fn_id: str, state: State) -> list[DebtUnit]:
        """
        Compute residual vector r_k(x) for given residual function ID.
        All outputs are DebtUnit.
        """
        # Dispatch to allowlisted implementations
        if residual_fn_id == "identity_zero":
            return [DebtUnit(0)] * state.dim
        elif residual_fn_id == "position_bound":
            # Example: bound on position coordinates
            return [max(DebtUnit(0), state.position[i] - bound) for i in range(state.dim)]
        # ... more allowlisted functions
        else:
            raise ValueError(f"Unknown residual_fn_id: {residual_fn_id}")
```

### Normalizer Computation

```python
def compute_sigma(sigma_spec_id: str, state: State) -> DebtUnit:
    """
    Compute normalizer σ_k(x).
    Returns DebtUnit, must be positive.
    """
    if sigma_spec_id.startswith("constant:"):
        # Parse constant value
        value = parse_constant(sigma_spec_id.split(":")[1])
        sigma = DebtUnit.from_rational(*value)
        sigma.require_nonnegative("sigma")
        return sigma
    elif sigma_spec_id.startswith("computed:"):
        # Dispatch to allowlisted computation
        return compute_computed_sigma(sigma_spec_id, state)
    else:
        raise ValueError(f"Unknown sigma_spec_id: {sigma_spec_id}")
```

---

## V(x) Computation

### Core Algorithm

```python
def compute_v(contract_set: ContractSet, state: State) -> DebtUnit:
    """
    Compute V(x) for given contract set and state.
    
    V(x) = Σ w_k · ||r̃_k(x)||₂²
    where r̃_k = r_k / σ_k
    """
    total_v = DebtUnit(0)
    
    for contract in contract_set.contracts:
        # Check applicability
        if not is_applicable(contract, state):
            continue  # r̃_k ≡ 0 when not applicable
        
        # Compute residual vector
        r_k = ResidualRegistry.compute(contract.residual_fn_id, state)
        
        # Compute normalizer
        sigma = compute_sigma(contract.sigma_spec_id, state)
        sigma.require_nonnegative("sigma")
        
        # Normalize: r̃_k = r_k / σ_k
        r_tilde = [r_i.div_int(sigma.int_value) for r_i in r_k]
        
        # Compute ||r̃_k||₂² = Σ r̃_k[i]²
        r_squared_sum = DebtUnit(0)
        for r_i in r_tilde:
            r_squared_sum = r_squared_sum + (r_i * r_i)
        
        # Get weight as DebtUnit
        weight = parse_weight(contract.weight_spec_id)
        
        # Add weighted contribution
        # w_k · ||r̃_k||₂²
        total_v = total_v + weight.mul_int(r_squared_sum.int_value)
    
    return total_v
```

### Per-Contract Summary

Each contract produces:

```python
class ContractResult:
    contract_id: str
    active: bool                    # Whether applicability was true
    r2_k: DebtUnit                  # ||r̃_k||₂² as DebtUnit
    r_inf_k: DebtUnit | None       # Optional: max absolute residual
    r_hash_k: str | None           # Optional: commitment hash
```

---

## Contract Result Output

### Full Measurement Output

```python
class MeasurementOutput:
    """Full measurement output for a state."""
    
    # Policy identification
    v_policy_id: str = "CK0.v1"
    v_output_mode: str = "debtunit_only.v1"  # State-only, DebtUnit-only
    
    # Total violation
    v_total: DebtUnit
    
    # Per-contract results
    contract_results: list[ContractResult]
    
    # Metadata
    contract_set_id: str
    state_hash: str
    
    def to_canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Deterministic field ordering
        return json.dumps({
            "v_policy_id": self.v_policy_id,
            "v_output_mode": self.v_output_mode,
            "v_total": self.v_total.canonical(),
            "contract_set_id": self.contract_set_id,
            "state_hash": self.state_hash,
            "contracts": [
                {
                    "contract_id": cr.contract_id,
                    "active": cr.active,
                    "r2_k": cr.r2_k.canonical(),
                }
                for cr in self.contract_results
            ]
        }, sort_keys=True).encode("utf-8")
```

---

## Determinism Requirements

| Requirement | Implementation |
|-------------|----------------|
| No floating-point non-determinism | All DebtUnit, all arithmetic exact |
| Rational reduction | gcd reduction before any aggregation |
| Rounding mode | half_even.v1 (canonical) |
| Ordering | Lexicographic contract ordering |
| No hidden state | Stateless computation from state + contract set |

---

## Weight Parsing

```python
def parse_weight(weight_spec_id: str) -> DebtUnit:
    """
    Parse weight specification to DebtUnit.
    
    Formats:
    - "p_q:<p>_<q>" - rational p/q
    - "constant:<decimal>" - decimal constant
    """
    if weight_spec_id.startswith("p_q:"):
        parts = weight_spec_id[4:].split("_")
        p = int(parts[0])
        q = int(parts[1])
        p_red, q_red = reduce_weight(p, q)
        return DebtUnit.from_rational(p_red, q_red)
    elif weight_spec_id.startswith("constant:"):
        return DebtUnit.from_decimal(weight_spec_id[9:])
    else:
        raise ValueError(f"Unknown weight format: {weight_spec_id}")
```

---

## Applicability Predicates

```python
def is_applicable(contract: Contract, state: State) -> bool:
    """
    Check if contract is applicable to state.
    
    If applicability_predicate_id is None, always applicable.
    """
    if contract.applicability_predicate_id is None:
        return True
    
    # Dispatch to allowlisted predicates
    if contract.applicability_predicate_id == "always":
        return True
    elif contract.applicability_predicate_id == "never":
        return False
    elif contract.applicability_predicate_id.startswith("block_active:"):
        block_id = contract.applicability_predicate_id.split(":")[1]
        return state.is_block_active(block_id)
    else:
        raise ValueError(f"Unknown applicability predicate: {contract.applicability_predicate_id}")
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| σ_k ≤ 0 | Hard invariant failure (reject) |
| Unknown residual_fn_id | Reject (allowlist only) |
| Unknown sigma_spec_id | Reject (allowlist only) |
| Negative weight | Reject (weights must be ≥ 0) |
| Division by zero | Hard invariant failure |

---

*See also: [`4_measured_gate.md`](4_measured_gate.md), [`../ck0/3_violation_functional.md`](../ck0/3_violation_functional.md)*
