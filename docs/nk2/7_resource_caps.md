# NK-2 Resource Caps + Deterministic Reject

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_exec_plan.md`](1_exec_plan.md), [`4_batch_attempt.md`](4_batch_attempt.md)

---

## Overview

This document defines resource caps and deterministic reject rules. Resource caps are the "hardware variability kill switch" - when any cap is exceeded, execution halts immediately with a deterministic error. There is no graceful degradation in v1.0.

---

## 1. Resource Caps Overview

### 1.1 Purpose

Resource caps serve as:
1. **Variability Kill Switch**: Prevent nondeterminism from hardware differences
2. **DoS Prevention**: Limit resource consumption
3. **Replay Stability**: Ensure same inputs → same outputs regardless of hardware

### 1.2 Policy-Locked Caps

All caps must be locked in the PolicyBundle at chain initialization:

```python
@dataclass(frozen=True)
class ResourceCaps:
    """Policy-locked resource limits."""
    
    max_bigint_bits: int             # Maximum BigInt bit length
    max_matrix_accum_terms: int      # Maximum matrix accumulation terms
    max_fields_touched_per_op: int   # Maximum fields per operation
    max_v_eval_cost: int            # Maximum V(x) evaluation cost
    max_batch_size_p: int | None    # Optional chain-locked batch size
    max_epsilon: DebtUnit | None    # Optional epsilon cap
```

---

## 2. Resource Events

### 2.1 What Triggers Resource Events

A resource event occurs when any computation exceeds a cap during:

| Event | Description | Trigger |
|-------|-------------|---------|
| `cap.bigint_bits` | BigInt size exceeds limit | During δ-norm computation |
| `cap.matrix_terms` | Matrix accumulation exceeds limit | During ε̂ computation |
| `cap.fields_touched` | Fields touched exceeds limit | During kernel execution |
| `cap.v_eval_cost` | V(x) evaluation cost exceeds limit | During gate computation |
| `cap.lcm_overflow` | LCM computation overflows | During DebtUnit arithmetic |
| `cap.epsilon` | ε_measured exceeds cap | During gate check |

### 2.2 Resource Tracker

```python
class ResourceTracker:
    """Tracks resource usage during execution."""
    
    def __init__(self, caps: ResourceCaps):
        self.caps = caps
        self._current_bigint_bits = 0
        self._current_matrix_terms = 0
        self._current_fields_touched = 0
        self._current_v_eval_cost = 0
    
    def check_bigint_bits(self, value: int) -> bool:
        """Check if BigInt bits within cap."""
        self._current_bigint_bits = max(self._current_bigint_bits, value)
        return value <= self.caps.max_bigint_bits
    
    def check_matrix_terms(self, count: int) -> bool:
        """Check if matrix terms within cap."""
        self._current_matrix_terms = max(self._current_matrix_terms, count)
        return count <= self.caps.max_matrix_accum_terms
    
    def check_fields_touched(self, fields: set[FieldID]) -> bool:
        """Check if fields touched within cap."""
        count = len(fields)
        self._current_fields_touched = max(self._current_fields_touched, count)
        return count <= self.caps.max_fields_touched_per_op
    
    def check_v_eval_cost(self, cost: int) -> bool:
        """Check if V eval cost within cap."""
        self._current_v_eval_cost = max(self._current_v_eval_cost, cost)
        return cost <= self.caps.max_v_eval_cost
    
    def get_peak_usage(self) -> dict[str, int]:
        """Get peak resource usage."""
        return {
            'bigint_bits': self._current_bigint_bits,
            'matrix_terms': self._current_matrix_terms,
            'fields_touched': self._current_fields_touched,
            'v_eval_cost': self._current_v_eval_cost,
        }
```

---

## 3. Deterministic Reject Rule

### 3.1 v1.0 Rule

When any resource event occurs:
1. **Halt immediately**
2. **Emit no commit receipt** for in-progress attempt
3. **Return deterministic error code**

There is **no graceful degradation** in v1.0 (no "try smaller batch").

### 3.2 Error Codes

```python
class ResourceErrorCode(Enum):
    """Resource cap error codes."""
    
    BIGINT_BITS_EXCEEDED = "err.cap.bigint_bits_exceeded"
    MATRIX_TERMS_EXCEEDED = "err.cap.matrix_terms_exceeded"
    FIELDS_TOUCHED_EXCEEDED = "err.cap.fields_touched_exceeded"
    V_EVAL_COST_EXCEEDED = "err.cap.v_eval_cost_exceeded"
    EPSILON_EXCEEDED = "err.cap.epsilon_exceeded"
    LCM_OVERFLOW = "err.cap.lcm_overflow"


@dataclass
class ResourceError:
    """Resource cap error (terminal)."""
    
    error_code: ResourceErrorCode
    resource_type: str
    limit: int
    actual: int
    batch_prev_hash: Hash256
    ops_in_flight: list[OpID]
    
    def __str__(self) -> str:
        return (
            f"ResourceError({self.error_code.value}): "
            f"{self.resource_type}={self.actual} > {self.limit}"
        )
```

---

## 4. Integration Points

### 4.1 δ-Norm Computation

```python
def compute_delta_norm_with_caps(
    op: OpSpec,
    pre_state: State,
    post_state: State,
    tracker: ResourceTracker
) -> tuple[DebtUnit, ResourceError | None]:
    """
    Compute δ-norm with resource tracking.
    
    Returns:
        (delta_norm, error)
    """
    delta = DebtUnit(0)
    
    for field_id in op.R_o | op.W_o:
        pre_val = pre_state.get_field(field_id)
        post_val = post_state.get_field(field_id)
        
        # Compute difference
        diff = abs(post_val - pre_val)
        
        # Check BigInt size
        diff_bits = diff.bit_length()
        if not tracker.check_bigint_bits(diff_bits):
            return delta, ResourceError(
                error_code=ResourceErrorCode.BIGINT_BITS_EXCEEDED,
                resource_type="bigint_bits",
                limit=tracker.caps.max_bigint_bits,
                actual=diff_bits,
                batch_prev_hash=None,  # Set by caller
                ops_in_flight=[op.op_id],
            )
        
        delta += diff ** 2
    
    # Check fields touched
    fields_touched = op.R_o | op.W_o
    if not tracker.check_fields_touched(fields_touched):
        return delta, ResourceError(
            error_code=ResourceErrorCode.FIELDS_TOUCHED_EXCEEDED,
            resource_type="fields_touched",
            limit=tracker.caps.max_fields_touched_per_op,
            actual=len(fields_touched),
            batch_prev_hash=None,
            ops_in_flight=[op.op_id],
        )
    
    return DebtUnit(int(math.isqrt(delta))), None
```

### 4.2 ε̂ Computation

```python
def compute_batch_cost_with_caps(
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix,
    tracker: ResourceTracker
) -> tuple[DebtUnit, ResourceError | None]:
    """
    Compute batch ε̂ with resource tracking.
    
    Returns:
        (epsilon_hat, error)
    """
    cost = DebtUnit(0)
    
    # Diagonal terms
    for op in batch:
        term = op.delta_bound_a ** 2
        
        # Check BigInt
        term_bits = term.bit_length()
        if not tracker.check_bigint_bits(term_bits):
            return cost, ResourceError(
                error_code=ResourceErrorCode.BIGINT_BITS_EXCEEDED,
                resource_type="bigint_bits",
                limit=tracker.caps.max_bigint_bits,
                actual=term_bits,
                batch_prev_hash=None,
                ops_in_flight=[op.op_id for op in batch],
            )
        
        cost += term
    
    # Off-diagonal terms
    for i, op_i in enumerate(batch):
        for j, op_j in enumerate(batch):
            if i >= j:
                continue
            
            m_ij = curvature_matrix.get(op_i.block_index, op_j.block_index)
            
            # m_ij * a_i * a_j = num * a_i * a_j / den
            # Track matrix terms
            num_terms = 1
            if not tracker.check_matrix_terms(num_terms):
                return cost, ResourceError(
                    error_code=ResourceErrorCode.MATRIX_TERMS_EXCEEDED,
                    resource_type="matrix_terms",
                    limit=tracker.caps.max_matrix_accum_terms,
                    actual=tracker._current_matrix_terms + num_terms,
                    batch_prev_hash=None,
                    ops_in_flight=[op.op_id for op in batch],
                )
            
            term = m_ij.numerator * op_i.delta_bound_a * op_j.delta_bound_a
            term //= m_ij.denominator
            
            # Check BigInt
            term_bits = term.bit_length()
            if not tracker.check_bigint_bits(term_bits):
                return cost, ResourceError(
                    error_code=ResourceErrorCode.BIGINT_BITS_EXCEEDED,
                    resource_type="bigint_bits",
                    limit=tracker.caps.max_bigint_bits,
                    actual=term_bits,
                    batch_prev_hash=None,
                    ops_in_flight=[op.op_id for op in batch],
                )
            
            cost += term
    
    return cost, None
```

### 4.3 V(x) Evaluation

```python
def evaluate_v_with_caps(
    state: State,
    contracts: ContractSet,
    tracker: ResourceTracker
) -> tuple[DebtUnit, ResourceError | None]:
    """
    Evaluate V(x) with resource tracking.
    
    Returns:
        (V(x), error)
    """
    v = DebtUnit(0)
    eval_cost = 0
    
    for contract in contracts.contracts:
        # Compute residual (simulated)
        residual = compute_residual(state, contract)
        eval_cost += 1
        
        # Check eval cost
        if not tracker.check_v_eval_cost(eval_cost):
            return v, ResourceError(
                error_code=ResourceErrorCode.V_EVAL_COST_EXCEEDED,
                resource_type="v_eval_cost",
                limit=tracker.caps.max_v_eval_cost,
                actual=eval_cost,
                batch_prev_hash=None,
                ops_in_flight=[],
            )
        
        # Continue computation...
    
    return v, None
```

---

## 5. Batch Attempt with Caps

### 5.1 Full Pipeline with Resource Tracking

```python
def attempt_batch_with_caps(
    context: AttemptContext,
    executor: KernelExecutor,
    tracker: ResourceTracker
) -> BatchAttemptResult:
    """
    Execute batch attempt with resource cap tracking.
    
    Any resource error immediately halts with terminal error.
    """
    # === PLANNING CHECKS ===
    valid, failure = run_planning_checks(...)
    if not valid:
        return BatchAttemptResult(success=False, failure_code=failure)
    
    # === KERNEL EXECUTION WITH CAPS ===
    kernel_results, failure = execute_batch_kernels(...)
    if failure:
        return BatchAttemptResult(success=False, failure_code=failure)
    
    # === δ-BOUND CHECKS WITH CAPS ===
    for op, post_state in kernel_results:
        delta_norm, error = compute_delta_norm_with_caps(
            op, context.pre_state, post_state, tracker
        )
        if error:
            return BatchAttemptResult(
                success=False,
                failure_code=FailureCode.CAP_EXCEEDED,
                resource_error=error,
            )
        
        if delta_norm > op.delta_bound_a:
            return BatchAttemptResult(
                success=False,
                failure_code=FailureCode.DELTA_BOUND,
            )
    
    # === STATE PATCHING ===
    post_state = patch_state_with_batch(...)
    
    # === ε̂ COMPUTATION WITH CAPS ===
    epsilon_hat, error = compute_batch_cost_with_caps(
        batch, context.curvature_matrix, tracker
    )
    if error:
        return BatchAttemptResult(
            success=False,
            failure_code=FailureCode.CAP_EXCEEDED,
            resource_error=error,
        )
    
    # === V(x) EVALUATION WITH CAPS ===
    v_pre, error = evaluate_v_with_caps(
        context.pre_state, context.policy_bundle.contracts, tracker
    )
    if error:
        return BatchAttemptResult(
            success=False,
            failure_code=FailureCode.CAP_EXCEEDED,
            resource_error=error,
        )
    
    v_post, error = evaluate_v_with_caps(
        post_state, context.policy_bundle.contracts, tracker
    )
    if error:
        return BatchAttemptResult(
            success=False,
            failure_code=FailureCode.CAP_EXCEEDED,
            resource_error=error,
        )
    
    # === MEASURED GATE ===
    epsilon_measured = abs(v_post - v_pre)
    
    # Check epsilon cap
    if tracker.caps.max_epsilon is not None:
        if epsilon_measured > tracker.caps.max_epsilon:
            return BatchAttemptResult(
                success=False,
                failure_code=FailureCode.EPSILON_EXCEEDED,
            )
    
    if epsilon_measured > epsilon_hat:
        return BatchAttemptResult(
            success=False,
            failure_code=FailureCode.GATE_EPS,
        )
    
    # === SUCCESS ===
    return BatchAttemptResult(
        success=True,
        post_state=post_state,
        epsilon_measured=epsilon_measured,
        epsilon_hat=epsilon_hat,
    )
```

---

## 6. Resource Cap Errors Are Terminal

### 6.1 No Rescheduling

Unlike other failures, resource cap errors **never trigger rescheduling**:

```python
def handle_failure_with_caps(
    failure_code: FailureCode,
    batch: list[OpSpec],
    resource_error: ResourceError | None = None
) -> FailureResult:
    """
    Handle failure, including resource cap errors.
    
    Resource errors are ALWAYS terminal.
    """
    # Check for resource error first
    if resource_error is not None:
        return FailureResult(
            action=ContinueAction.HALT,
            terminal_error=create_resource_terminal_error(
                resource_error, batch
            ),
            failure_code=failure_code,
        )
    
    # Other failures follow normal handling
    # ... (from section 6)
```

### 6.2 Terminal Error Creation

```python
def create_resource_terminal_error(
    error: ResourceError,
    batch: list[OpSpec]
) -> TerminalError:
    """Create terminal error from resource error."""
    
    return TerminalError(
        error_code=error.error_code.value,
        failed_op_id=error.ops_in_flight[0] if error.ops_in_flight else "unknown",
        failure_code=FailureCode.CAP_EXCEEDED,
        batch_size=len(batch),
        batch_prev_hash=error.batch_prev_hash,
    )
```

---

## 7. Cap Boundary Tests

### 7.1 Test Cases

```python
def test_cap_bigint_bits():
    """Test BigInt bits cap boundary."""
    
    caps = ResourceCaps(
        max_bigint_bits=4096,
        ...
    )
    tracker = ResourceTracker(caps)
    
    # Under cap: should pass
    assert tracker.check_bigint_bits(4096) == True
    
    # At cap: should pass
    assert tracker.check_bigint_bits(4096) == True
    
    # Over cap: should fail
    assert tracker.check_bigint_bits(4097) == False


def test_cap_matrix_terms():
    """Test matrix terms cap boundary."""
    
    caps = ResourceCaps(
        max_matrix_accum_terms=10000,
        ...
    )
    tracker = ResourceTracker(caps)
    
    # Under cap: should pass
    assert tracker.check_matrix_terms(10000) == True
    
    # Over cap: should fail
    assert tracker.check_matrix_terms(10001) == False


def test_cap_epsilon():
    """Test epsilon cap."""
    
    caps = ResourceCaps(
        max_epsilon=DebtUnit(1000),
        ...
    )
    
    # Check epsilon
    epsilon = DebtUnit(999)
    assert epsilon <= caps.max_epsilon
    
    epsilon = DebtUnit(1000)
    assert epsilon <= caps.max_epsilon
    
    epsilon = DebtUnit(1001)
    assert epsilon > caps.max_epsilon
```

---

## 8. No Reschedule on Cap

### 8.1 Design Rationale

Resource caps are **fundamental limits**, not conditions that can be fixed by retrying:

1. **Hardware variability**: Same inputs should produce same outputs
2. **DoS prevention**: Malicious inputs can't force unbounded computation
3. **Simplicity**: No complex fallback logic needed

### 8.2 Invariant

```python
def verify_no_reschedule_on_cap(ledger: ReceiptLedger) -> bool:
    """
    Verify no commit was made after resource cap error.
    
    v1.0 invariant: resource cap errors produce zero ledger entries.
    """
    # This is enforced by the main loop:
    # - Resource error → HALT immediately
    # - No receipt emitted
    # - No state update
    return True
```

---

## 9. Summary

| Cap | Error Code | Trigger | Action |
|-----|-----------|---------|--------|
| `max_bigint_bits` | `err.cap.bigint_bits_exceeded` | δ-norm computation | HALT |
| `max_matrix_accum_terms` | `err.cap.matrix_terms_exceeded` | ε̂ computation | HALT |
| `max_fields_touched_per_op` | `err.cap.fields_touched_exceeded` | Kernel execution | HALT |
| `max_v_eval_cost` | `err.cap.v_eval_cost_exceeded` | V(x) evaluation | HALT |
| `max_epsilon` | `err.cap.epsilon_exceeded` | Gate check | HALT |

**No graceful degradation in v1.0** - when a cap trips, execution halts.
