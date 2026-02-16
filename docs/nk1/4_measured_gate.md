# NK-1 Measured Gate v1

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`3_contracts.md`](3_contracts.md), [`5_curvature.md`](5_curvature.md), [`../ck0/4_budget_debt_law.md`](../ck0/4_budget_debt_law.md)

---

## Overview

The **Measured Gate** is the authoritative accept/reject mechanism in NK-1. Given a state, action, and budget, it determines whether the transition maintains coherence according to the CK-0 Law:

```
D_{k+1} ≤ D_k - S(D_k, B_k) + E_k
```

---

## Gate Interface

```python
@dataclass
class GateInput:
    """Input to the measured gate."""
    state: State                      # Current state x
    action: ActionDescriptor          # Proposed action u
    budget: DebtUnit                 # B_k - service budget
    disturbance: DebtUnit            # E_k - disturbance (or computed)
    disturbance_policy_id: str       # DP0/DP1/DP2/DP3
    contract_set: ContractSet        # Contract set for V(x) computation
    service_policy_id: str           # Service law policy
    service_instance_id: str         # Service instance (e.g., "linear_capped.mu:1.0")
    prev_receipt_hash: str | None    # Previous receipt hash (for chaining)

@dataclass
class GateOutput:
    """Output from the measured gate."""
    decision: GateDecision           # accept / reject / repair
    failure_code: str | None        # Failure reason if rejected
    receipt: Receipt                # Full receipt for this step
```

### Decision Enum

```python
class GateDecision(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    REPAIR = "repair"  # If allowed by rail policy
```

---

## Measured Gate Algorithm

### Step 1: Decode and Canonicalize Action

```python
def decode_action(action: ActionDescriptor) -> ActionDescriptor:
    """Validate and canonicalize action descriptor."""
    # Validate required fields
    if not action.action_type:
        raise ValueError("Missing action_type")
    if not action.target_blocks:
        raise ValueError("Missing target_blocks")
    
    # Ensure sorted, unique target blocks
    action.target_blocks = sorted(set(action.target_blocks))
    
    # Validate no unknown fields
    validate_no_unknown_fields(action)
    
    # Canonicalize numeric encoding
    action.budget = canonicalize_debtunit(action.budget)
    
    return action
```

### Step 2: Check Invariant Preconditions

```python
def check_invariants(state: State) -> tuple[bool, str | None]:
    """
    Check hard invariants before processing.
    
    Returns (passes, failure_reason).
    """
    # Check all hard invariants
    for invariant in state.invariants:
        if not invariant.check(state):
            return False, f"invariant_violation:{invariant.id}"
    
    return True, None
```

### Step 3: Compute Pre-Transition Debt

```python
def compute_debt_pre(contract_set: ContractSet, state: State) -> DebtUnit:
    """Compute D_pre = V(x) before transition."""
    return compute_v(contract_set, state)
```

### Step 4: Apply Candidate Transition (Sandboxed)

```python
def apply_transition(state: State, action: ActionDescriptor) -> State:
    """
    Apply candidate transition in sandbox.
    
    Returns new state x' = T(x, u).
    This should be a deterministic patch computation.
    """
    # Validate action applicability to state
    if not is_action_applicable(action, state):
        raise ValueError("Action not applicable to current state")
    
    # Apply deterministic transition
    new_state = transition_function(action.transition_fn_id, state, action.payload)
    
    return new_state
```

### Step 5: Compute Post-Transition Debt

```python
def compute_debt_post(contract_set: ContractSet, state: State) -> DebtUnit:
    """Compute D_post = V(x') after transition."""
    return compute_v(contract_set, state)
```

### Step 6: Compute Delta V

```python
def compute_delta_v(debt_post: DebtUnit, debt_pre: DebtUnit) -> DebtUnit:
    """Compute ΔV = D_post - D_pre."""
    return debt_post - debt_pre
```

### Step 7: Compute Service Amount

```python
def compute_service(debt_pre: DebtUnit, budget: DebtUnit, 
                   service_policy_id: str, service_instance_id: str) -> DebtUnit:
    """
    Compute S(D_pre, B_k) according to service law.
    
    Default: S_lin(D, B) = min(D, μ * B)
    """
    # Parse service instance parameters
    if service_instance_id.startswith("linear_capped.mu:"):
        mu = Decimal(service_instance_id.split(":")[1])
        mu_debt = DebtUnit.from_decimal(str(mu))
        
        # S(D, B) = min(D, μ * B)
        service_cap = budget.mul_int(mu_debt.int_value)
        return min(debt_pre, service_cap)
    else:
        raise ValueError(f"Unknown service instance: {service_instance_id}")
```

### Step 8: Gate Decision

```python
def gate_decision(debt_pre: DebtUnit, debt_post: DebtUnit,
                  service: DebtUnit, disturbance: DebtUnit,
                  budget: DebtUnit) -> tuple[GateDecision, str | None]:
    """
    Apply CK-0 Law:
    
    Accept iff: D_post ≤ D_pre - S(D_pre, B) + E
    
    Otherwise reject.
    """
    # Compute allowed maximum debt
    allowed_max = debt_pre - service + disturbance
    
    # Check inequality
    if debt_post.int_value <= allowed_max.int_value:
        return GateDecision.ACCEPT, None
    else:
        return GateDecision.REJECT, f"law_violation:debt_exceeded"
```

---

## Complete Gate Process

```python
def measured_gate(input: GateInput) -> GateOutput:
    """
    Execute the complete measured gate process.
    """
    # Step 1: Decode + canonicalize action
    action = decode_action(input.action)
    
    # Step 2: Check invariant preconditions
    invariants_pass, invariant_failure = check_invariants(input.state)
    if not invariants_pass:
        return create_failure_receipt(
            input, 
            "invariant_violation", 
            invariant_failure
        )
    
    # Step 3: Compute D_pre
    debt_pre = compute_debt_pre(input.contract_set, input.state)
    
    # Step 4: Apply candidate transition
    try:
        state_post = apply_transition(input.state, action)
    except Exception as e:
        return create_failure_receipt(input, "transition_error", str(e))
    
    # Step 5: Compute D_post
    debt_post = compute_debt_post(input.contract_set, state_post)
    
    # Step 6: Compute ΔV
    delta_v = compute_delta_v(debt_post, debt_pre)
    
    # Step 7: Compute service
    service = compute_service(
        debt_pre, 
        input.budget, 
        input.service_policy_id,
        input.service_instance_id
    )
    
    # Step 8: Verify disturbance policy
    disturbance_ok, disturbance_failure = verify_disturbance(
        input.disturbance,
        input.disturbance_policy_id,
        input.policy_header  # Contains E_bar, event types, etc.
    )
    if not disturbance_ok:
        return create_failure_receipt(input, "disturbance_violation", disturbance_failure)
    
    # Step 9: Gate decision
    decision, failure_code = gate_decision(
        debt_pre, debt_post, service, input.disturbance, input.budget
    )
    
    # Step 10: Emit receipt
    receipt = create_receipt(
        input=input,
        state_post=state_post,
        debt_pre=debt_pre,
        debt_post=debt_post,
        delta_v=delta_v,
        service=service,
        decision=decision,
        failure_code=failure_code,
        invariants_pass=True,
        law_check_pass=(decision == GateDecision.ACCEPT)
    )
    
    return GateOutput(decision=decision, failure_code=failure_code, receipt=receipt)
```

---

## Service Law Specifications

### Default: Linear Capped

```
S_lin(D, B) = min(D, μ * B)
```

| Property | Value |
|----------|-------|
| `S(D, 0)` | 0 |
| `S(0, B)` | 0 |
| `S(D, B) ≤ D` | Yes |
| Monotone | Yes |

### Service Instance IDs

| Instance ID | Formula |
|-------------|---------|
| `linear_capped.mu:1.0` | min(D, 1.0 * B) |
| `linear_capped.mu:0.5` | min(D, 0.5 * B) |
| `linear_capped.mu:0` | 0 (no service) |

---

## Disturbance Policies (DP0-DP3)

### DP0: Zero Disturbance

```python
def verify_dp0(disturbance: DebtUnit) -> tuple[bool, str | None]:
    """E_k must be 0."""
    if disturbance.int_value != 0:
        return False, "dp0_violation:nonzero_disturbance"
    return True, None
```

### DP1: Bounded Disturbance

```python
def verify_dp1(disturbance: DebtUnit, e_bar: DebtUnit) -> tuple[bool, str | None]:
    """0 ≤ E_k ≤ Ē."""
    if disturbance.int_value < 0:
        return False, "dp1_violation:negative"
    if disturbance.int_value > e_bar.int_value:
        return False, "dp1_violation:exceeds_bound"
    return True, None
```

### DP2: Event-Typed Disturbance

```python
def verify_dp2(disturbance: DebtUnit, event_type: str | None,
               beta: dict[str, DebtUnit]) -> tuple[bool, str | None]:
    """E_k ≤ β(event_type), β(∅) = 0."""
    bound = beta.get(event_type, DebtUnit(0))
    if disturbance.int_value > bound.int_value:
        return False, "dp2_violation:exceeds_event_bound"
    return True, None
```

### DP3: Model-Based Disturbance

```python
def verify_dp3(disturbance: DebtUnit, computed_disturbance: DebtUnit) -> tuple[bool, str | None]:
    """E_k must match model computation exactly."""
    if disturbance.int_value != computed_disturbance.int_value:
        return False, "dp3_violation:mismatch"
    return True, None
```

---

## Receipt Emission

The gate always emits a receipt, whether accepted or rejected:

```python
def create_receipt(
    input: GateInput,
    state_post: State,
    debt_pre: DebtUnit,
    debt_post: DebtUnit,
    delta_v: DebtUnit,
    service: DebtUnit,
    decision: GateDecision,
    failure_code: str | None,
    invariants_pass: bool,
    law_check_pass: bool
) -> Receipt:
    """Create and hash-chain receipt."""
    
    # Compute hashes
    state_hash_pre = hash(input.state.to_canonical_bytes())
    state_hash_post = hash(state_post.to_canonical_bytes())
    action_hash = hash(input.action.to_canonical_bytes())
    
    # Build receipt
    receipt = Receipt(
        # Chain
        prev_receipt_hash=input.prev_receipt_hash,
        receipt_hash=None,  # Computed after full receipt
        state_hash_pre=state_hash_pre,
        state_hash_post=state_hash_post,
        action_descriptor_hash=action_hash,
        
        # Policy
        contract_set_id=input.contract_set.contract_set_id,
        v_policy_id="CK0.v1",
        service_policy_id=input.service_policy_id,
        service_instance_id=input.service_instance_id,
        disturbance_policy_id=input.disturbance_policy_id,
        
        # Measurements
        debt_pre=debt_pre,
        debt_post=debt_post,
        delta_v=delta_v,
        budget=input.budget,
        disturbance=input.disturbance,
        service_applied=service,
        
        # Decision
        gate_decision=decision.value,
        failure_code=failure_code,
        invariants_pass=invariants_pass,
        law_check_pass=law_check_pass,
    )
    
    # Compute receipt hash
    receipt.receipt_hash = hash(receipt.to_canonical_bytes())
    
    return receipt
```

---

## Failure Receipts

When gate rejects due to preconditions:

```python
def create_failure_receipt(
    input: GateInput,
    failure_type: str,
    failure_detail: str | None
) -> GateOutput:
    """Create receipt for gate failure."""
    
    # Compute pre-state hash
    state_hash_pre = hash(input.state.to_canonical_bytes())
    
    # Create failure receipt (no state transition)
    receipt = Receipt(
        prev_receipt_hash=input.prev_receipt_hash,
        receipt_hash=None,
        state_hash_pre=state_hash_pre,
        state_hash_post=state_hash_pre,  # No change
        action_descriptor_hash=hash(input.action.to_canonical_bytes()),
        
        contract_set_id=input.contract_set.contract_set_id,
        v_policy_id="CK0.v1",
        service_policy_id=input.service_policy_id,
        service_instance_id=input.service_instance_id,
        disturbance_policy_id=input.disturbance_policy_id,
        
        debt_pre=compute_debt_pre(input.contract_set, input.state),
        debt_post=compute_debt_pre(input.contract_set, input.state),  # No change
        delta_v=DebtUnit(0),
        budget=input.budget,
        disturbance=input.disturbance,
        service_applied=DebtUnit(0),
        
        gate_decision=GateDecision.REJECT.value,
        failure_code=f"{failure_type}:{failure_detail}" if failure_detail else failure_type,
        invariants_pass=False,
        law_check_pass=False,
    )
    
    receipt.receipt_hash = hash(receipt.to_canonical_bytes())
    
    return GateOutput(
        decision=GateDecision.REJECT,
        failure_code=failure_type,
        receipt=receipt
    )
```

---

*See also: [`5_curvature.md`](5_curvature.md), [`7_receipts.md`](7_receipts.md), [`../ck0/4_budget_debt_law.md`](../ck0/4_budget_debt_law.md)*
