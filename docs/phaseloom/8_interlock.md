# PhaseLoom Scheduler Interlock

**Canon Doc Spine v1.0.0** — Section 9

---

## 1. Interlock Rule

### 1.1 Canon Statement

If either:
- (b ≤ b_min), or
- (optional strong mode) (V_PL ≥ Θ),

then:
- **Solver steps producing (A > 0) are rejected**
- Only `REPAIR`, `RESOLVE`, and `AUTH_INJECT` are admissible

### 1.2 Rationale

The interlock provides a "brake" on the system when:
- Budget is exhausted (safety-critical)
- Potential exceeds threshold (optional strong mode)

This guarantees safety via a curvature-bounded viability tube.

---

## 2. Multi-Clock Admissibility

### 2.1 Clock Selection

The scheduler chooses:

Δt = min(Δt_s, Δt_g, Δt_λ, Δt_h)

Where:
- Δt_s: Solver clock
- Δt_g: Governance clock
- Δt_λ: Spectral clock
- Δt_h: Hardware clock

### 2.2 Additional Constraints

The selected Δt must additionally satisfy:
- Interlock constraints
- Budget charge constraints

---

## 3. Implementation

### 3.1 Interlock Check

```python
def check_interlock(
    state: PLState,
    step: Step,
    params: PLParams,
    strong_mode: bool = False
) -> InterlockResult:
    """Check if step is admissible under interlock."""
    
    # Condition 1: Budget floor
    budget_ok = state.b > params.b_min
    
    # Condition 2: Strong mode - potential threshold
    if strong_mode:
        V_PL = compute_potential(
            step.v_next, step.C_next, step.T_next,
            step.b_next, step.a_next,
            params.weights, params.epsilon
        )
        potential_ok = V_PL < params.Theta
    else:
        potential_ok = True
    
    # Step type check
    if step.step_type == StepType.SOLVE:
        # SOLVE requires A = 0 when interlock active
        if not budget_ok or not potential_ok:
            if step.A > 0:
                return InterlockResult(
                    allowed=False,
                    reason=InterlockReason.BUDGET_EXHAUSTED if not budget_ok 
                           else InterlockReason.POTENTIAL_EXCEEDED
                )
    
    return InterlockResult(allowed=True, reason=None)
```

### 3.2 Step Type Filtering

```python
def admissible_steps(
    state: PLState,
    params: PLParams,
    strong_mode: bool = False
) -> List[StepType]:
    """Get list of admissible step types."""
    
    budget_ok = state.b > params.b_min
    
    if strong_mode:
        V_PL = compute_potential(state, params)
        potential_ok = V_PL < params.Theta
    else:
        potential_ok = True
    
    if not budget_ok or not potential_ok:
        # Only repair/resolve/inject allowed
        return [StepType.REPAIR, StepType.RESOLVE, StepType.AUTH_INJECT]
    
    return [StepType.SOLVE, StepType.REPAIR, StepType.RESOLVE, StepType.AUTH_INJECT]
```

---

## 4. Interlock Reasons

### 4.1 Reason Codes

| Reason | Description |
|--------|-------------|
| BUDGET_EXHAUSTED | b ≤ b_min |
| POTENTIAL_EXCEEDED | V_PL ≥ Θ (strong mode) |
| NONE | No interlock active |

### 4.2 Rejection Response

When a step is rejected:
```python
class RejectCode(Enum):
    SCHEMA_HASH_MISMATCH = "schema"
    RECURRENCE_VIOLATION = "recurrence"
    BUDGET_CHARGE_VIOLATION = "budget_charge"
    INTERLOCK_VIOLATION = "interlock"  # <-- Interlock rejection
    UNAUTHORIZED_INJECTION = "auth"
    OVERFLOW = "overflow"
```

---

## 5. Scheduler Integration

### 5.1 NK-2 Scheduler Hook

The NK-2 scheduler calls interlock check before executing steps:

```python
def schedule_batch(batch: Batch, state: PLState, params: PLParams) -> Batch:
    """Schedule batch with interlock enforcement."""
    
    admissible = admissible_steps(state, params)
    filtered_ops = []
    
    for op in batch.operations:
        if op.step_type in admissible:
            filtered_ops.append(op)
        else:
            # Log rejection
            log_rejection(op, InterlockReason.BUDGET_EXHAUSTED)
    
    return Batch(operations=filtered_ops)
```

### 5.2 Multi-Clock Coordination

```python
def select_delta_t(
    clocks: Clocks,
    state: PLState,
    params: PLParams
) -> FixedPoint:
    """Select minimum clock delta with interlock check."""
    
    base_delta = min(
        clocks.solver_delta,
        clocks.governance_delta,
        clocks.spectral_delta,
        clocks.hardware_delta
    )
    
    # Interlock may reduce delta
    if state.b <= params.b_min:
        # Reduce to minimum safe delta
        return params.min_safe_delta
    
    return base_delta
```

---

## 6. Safety Guarantees

### 6.1 Viability Tube

The interlock defines a viability tube:
- Upper bound: b_min
- (Strong mode) Upper bound: V_PL = Θ

### 6.2 Invariant

Once interlock activates:
- No new amplification (A > 0) can occur
- Only repair/resolve/inject proceed
- System cannot diverge while in interlock

---

## 7. Liveness Interaction

### 7.1 Escape Hatch

The interlock can be escaped via:
- Authority injection (AUTH_INJECT): increases b
- Repair steps (REPAIR): reduces V

### 7.2 Deadlock Condition

A deadlock occurs when:
- Interlock forbids solve steps with A > 0
- Repair/resolve cannot reduce V further
- Budget b cannot pay for exploration

This is resolved by Authority Injection (Section 9).

---

## 8. Configuration

### 8.1 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| b_min | FixedPoint ≥ 0 | Budget floor |
| Theta | FixedPoint | Potential threshold (strong mode) |
| strong_mode | bool | Enable potential threshold |
| min_safe_delta | FixedPoint | Minimum delta under interlock |

### 8.2 Recommended v1

```python
DEFAULT_PARAMS = Params(
    b_min=FixedPoint(0),          # Allow zero budget in v1
    Theta=FixedPoint(1000),      # High threshold
    strong_mode=False,            # Disabled in v1
    min_safe_delta=FixedPoint(1)  # Minimum step
)
```

---

## 9. Status

- [x] Interlock rule defined
- [x] Multi-clock admissibility specified
- [x] Implementation skeleton provided
- [x] Scheduler integration defined
- [ ] Implementation in src/phaseloom/interlock.py

---

*The interlock provides the safety-critical brake that prevents amplification when budget is exhausted, guaranteeing curvature-bounded viability.*
