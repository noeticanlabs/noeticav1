# NK-2 Batch Attempt Semantics

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`3_scheduler.md`](3_scheduler.md), [`../nk1/4_measured_gate.md`](../nk1/4_measured_gate.md)

---

## Overview

This document defines how batches are attempted - the execution pipeline from candidate batch to either successful commit or deterministic failure. A batch attempt proceeds through: planning checks, kernel execution, δ-bound verification, state patching, and measured gate verification.

---

## 1. Batch Attempt Pipeline

### 1.1 Attempt Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                    BATCH ATTEMPT PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PLANNING CHECKS                                             │
│     ├─ Independence verification                                 │
│     └─ Policy veto check                                        │
│           ↓                                                     │
│  2. KERNEL EXECUTION                                            │
│     ├─ Run all kernels on pre-state x                           │
│     ├─ Extract writes from kernel output                        │
│     └─ Patch singleton states                                  │
│           ↓                                                     │
│  3. δ-BOUND CHECKS                                              │
│     ├─ Compute δ-norm for each op                               │
│     └─ Verify ||δ_o|| ≤ a_o                                    │
│           ↓                                                     │
│  4. STATE PATCHING                                               │
│     ├─ Apply all writes in deterministic order                  │
│     └─ Produce x'                                              │
│           ↓                                                     │
│  5. MEASURED GATE                                               │
│     ├─ Compute ε_meas = |ε_B|                                  │
│     ├─ Compute ε_hat = ε̂(B)                                    │
│     └─ Verify ε_meas ≤ ε_hat                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Batch Attempt Result

```python
from dataclasses import dataclass
from enum import Enum, auto


class FailureCode(Enum):
    """Failure classification codes."""
    # Planning-time failures
    INDEPENDENCE = "fail.independence"
    POLICY_VETO = "fail.policy_veto"
    
    # Execution-time failures
    KERNEL_ERROR = "fail.kernel_error"
    DELTA_BOUND = "fail.delta_bound"
    GATE_EPS = "fail.gate_eps"
    
    # Terminal (singleton)
    KERNEL_ERROR_SINGLETON = "err.kernel_error.singleton"
    DELTA_BOUND_SINGLETON = "err.delta_bound.singleton"
    POLICY_VETO_SINGLETON = "err.policy_veto.singleton"


@dataclass
class BatchAttemptResult:
    """Result of a batch attempt."""
    
    success: bool
    failure_code: FailureCode | None = None
    
    # Only populated on success
    post_state: State | None = None
    local_receipts: tuple['LocalReceipt', ...] | None = None
    commit_receipt: 'CommitReceipt' | None = None
    
    # Execution info
    epsilon_measured: DebtUnit | None = None
    epsilon_hat: DebtUnit | None = None
    execution_time_ms: float | None = None


@dataclass
class AttemptContext:
    """Context for batch attempt."""
    
    pre_state: State
    batch: list[OpSpec]
    append_log: list[OpID]
    ledger_prev_hash: Hash256
    scheduler_rule_id: str
    scheduler_mode: str
    policy_bundle: PolicyBundle
    curvature_matrix: CurvatureMatrix
```

---

## 2. Planning-Time Checks

### 2.1 Independence Verification

```python
def check_planning_independence(batch: list[OpSpec]) -> tuple[bool, FailureCode | None]:
    """
    Verify all ops in batch are mutually independent.
    
    This should not happen if scheduler is correct, but we verify anyway.
    
    Returns:
        (is_valid, failure_code)
    """
    for i, op1 in enumerate(batch):
        for op2 in batch[i+1:]:
            if not check_independence(op1, op2):
                return False, FailureCode.INDEPENDENCE
    
    return True, None
```

### 2.2 Policy Veto Check

```python
def check_policy_veto(
    batch: list[OpSpec],
    scheduler_mode: str,
    policy_bundle: PolicyBundle
) -> tuple[bool, FailureCode | None]:
    """
    Check if batch violates any policy constraints.
    
    Returns:
        (is_valid, failure_code)
    """
    # Check mode constraints
    requires_modeD = any(op.requires_modeD for op in batch)
    if requires_modeD and scheduler_mode != "id:mode.D":
        return False, FailureCode.POLICY_VETO
    
    # Check float policy
    float_restricts = not policy_bundle.float_policy_allows_tensor
    has_float = any(op.float_touch for op in batch)
    if float_restricts and has_float:
        return False, FailureCode.POLICY_VETO
    
    return True, None
```

### 2.3 Combined Planning Checks

```python
def run_planning_checks(
    batch: list[OpSpec],
    scheduler_mode: str,
    policy_bundle: PolicyBundle
) -> tuple[bool, FailureCode | None]:
    """
    Run all planning-time checks.
    
    Returns:
        (all_passed, failure_code)
    """
    # Independence check
    valid, failure = check_planning_independence(batch)
    if not valid:
        return False, failure
    
    # Policy veto check
    valid, failure = check_policy_veto(batch, scheduler_mode, policy_bundle)
    if not valid:
        return False, failure
    
    return True, None
```

---

## 3. Kernel Execution

### 3.1 Kernel Execution Interface

```python
class KernelExecutor:
    """Executes kernels on states."""
    
    def __init__(self, kernel_registry: KernelRegistry):
        self.kernel_registry = kernel_registry
    
    def execute(
        self,
        kernel_hash: Hash256,
        pre_state: State
    ) -> tuple[State, bool]:
        """
        Execute kernel on pre-state.
        
        Returns:
            (post_state, is_error)
        """
        kernel = self.kernel_registry.get(kernel_hash)
        
        try:
            post_state = kernel.execute(pre_state)
            return post_state, False
        except KernelError:
            return pre_state, True
```

### 3.2 Batch Kernel Execution

```python
def execute_batch_kernels(
    batch: list[OpSpec],
    pre_state: State,
    executor: KernelExecutor,
    abort_on_error: bool = True
) -> tuple[list[tuple[OpSpec, State, bool]], FailureCode | None]:
    """
    Execute all kernels in batch on same pre-state.
    
    All kernels see the same pre-state x.
    
    Returns:
        (results: list[(op, post_state, is_error)], failure_code)
    """
    results = []
    
    for op in batch:
        post_state, is_error = executor.execute(op.kernel_hash, pre_state)
        results.append((op, post_state, is_error))
        
        if is_error and abort_on_error:
            return results, FailureCode.KERNEL_ERROR
    
    return results, None
```

### 3.3 Singleton State Extraction

```python
def extract_singleton_state(
    op: OpSpec,
    kernel_output: State,
    pre_state: State
) -> State:
    """
    Extract patched singleton state for an op.
    
    1. Extract writes Δ_o from kernel_output restricted to W_o
    2. Patch pre_state with Δ_o to get x̃_o
    
    This is what epsilon uses, never raw kernel output.
    """
    # Extract writes
    writes = {}
    for field_id in op.W_o:
        if field_id in kernel_output.fields:
            writes[field_id] = kernel_output.fields[field_id]
    
    # Patch pre-state
    patched = pre_state.patch(writes)
    
    return patched
```

---

## 4. δ-Bound Checks

### 4.1 δ-Norm Computation

```python
def compute_delta_norm(
    op: OpSpec,
    pre_state: State,
    post_state: State
) -> DebtUnit:
    """
    Compute exact δ-norm for an operation.
    
    From NK-1 §1.5: ||δ_o|| = ||x̃_o - x|| (in DebtUnit)
    
    Uses exact integer arithmetic.
    """
    # Get field values
    delta = DebtUnit(0)
    
    for field_id in op.R_o | op.W_o:
        pre_val = pre_state.get_field(field_id)
        post_val = post_state.get_field(field_id)
        
        # Compute difference in DebtUnit
        diff = abs(post_val - pre_val)
        delta += diff ** 2
    
    # Square root (in DebtUnit space)
    return DebtUnit(int(math.isqrt(delta)))
```

### 4.2 δ-Bound Verification

```python
def verify_delta_bounds(
    batch_results: list[tuple[OpSpec, State]],
    exec_plan: ExecPlan
) -> tuple[list[tuple[OpSpec, bool]], FailureCode | None]:
    """
    Verify δ-norm ≤ delta_bound_a for each op.
    
    Returns:
        (results: list[(op, is_valid)], failure_code)
    """
    results = []
    
    for op, post_state in batch_results:
        # Need pre-state (would be passed in)
        # Compute delta norm
        delta_norm = compute_delta_norm(op, pre_state, post_state)
        
        if delta_norm > op.delta_bound_a:
            # Check if singleton (terminal)
            if len(batch_results) == 1:
                return results, FailureCode.DELTA_BOUND_SINGLETON
            return results, FailureCode.DELTA_BOUND
        
        results.append((op, True))
    
    return results, None
```

---

## 5. State Patching

### 5.1 Disjoint Patching

```python
def patch_state_with_batch(
    pre_state: State,
    batch: list[OpSpec],
    kernel_outputs: list[State]
) -> State:
    """
    Apply all writes from batch to produce post-state.
    
    Order: deterministic by op_id bytes (sorted).
    Under independence, order doesn't change meaning.
    """
    # Sort by op_id bytes
    sorted_batch = sorted(
        zip(batch, kernel_outputs),
        key=lambda x: x[0].op_id.encode('utf-8')
    )
    
    # Apply patches in order
    current_state = pre_state
    
    for op, kernel_output in sorted_batch:
        # Extract writes for this op
        writes = {f: kernel_output.fields[f] for f in op.W_o if f in kernel_output.fields}
        
        # Patch
        current_state = current_state.patch(writes)
    
    return current_state
```

---

## 6. Measured Gate

### 6.1 Gate Computation

```python
def compute_batch_gate(
    batch: list[OpSpec],
    pre_state: State,
    post_state: State,
    curvature_matrix: CurvatureMatrix
) -> tuple[DebtUnit, DebtUnit]:
    """
    Compute measured gate values.
    
    Returns:
        (epsilon_measured, epsilon_hat)
    """
    # ε_measured = |ε_B| from NK-1 §1.6
    epsilon_measured = epsilon_measured_batch(pre_state, post_state, batch)
    
    # ε_hat = ε̂(B) from NK-1 §1.7
    epsilon_hat = compute_batch_cost(batch, curvature_matrix)
    
    return epsilon_measured, epsilon_hat
```

### 6.2 Gate Verification

```python
def verify_gate(
    epsilon_measured: DebtUnit,
    epsilon_hat: DebtUnit,
    policy_bundle: PolicyBundle
) -> tuple[bool, FailureCode | None]:
    """
    Verify measured gate condition.
    
    Accept iff ε_meas ≤ ε_hat (and optional ≤ ε_max_policy)
    """
    # Primary check
    if epsilon_measured > epsilon_hat:
        return False, FailureCode.GATE_EPS
    
    # Optional policy cap
    if policy_bundle.max_epsilon is not None:
        if epsilon_measured > policy_bundle.max_epsilon:
            return False, FailureCode.GATE_EPS
    
    return True, None
```

---

## 7. Full Batch Attempt

### 7.1 Complete Attempt Pipeline

```python
def attempt_batch(
    context: AttemptContext,
    executor: KernelExecutor
) -> BatchAttemptResult:
    """
    Execute full batch attempt pipeline.
    
    Stages:
    1. Planning checks
    2. Kernel execution
    3. δ-bound checks
    4. State patching
    5. Measured gate
    """
    import time
    start_time = time.time()
    
    batch = context.batch
    
    # === STAGE 1: Planning Checks ===
    valid, failure = run_planning_checks(
        batch,
        context.scheduler_mode,
        context.policy_bundle
    )
    if not valid:
        return BatchAttemptResult(
            success=False,
            failure_code=failure,
        )
    
    # === STAGE 2: Kernel Execution ===
    kernel_results, failure = execute_batch_kernels(
        batch,
        context.pre_state,
        executor,
        context.policy_bundle.abort_on_kernel_error
    )
    if failure:
        # Check for singleton terminal
        if len(batch) == 1 and failure == FailureCode.KERNEL_ERROR:
            return BatchAttemptResult(
                success=False,
                failure_code=FailureCode.KERNEL_ERROR_SINGLETON,
            )
        return BatchAttemptResult(
            success=False,
            failure_code=failure,
        )
    
    # Extract singleton states
    singleton_states = []
    for op, kernel_output, _ in kernel_results:
        singleton = extract_singleton_state(op, kernel_output, context.pre_state)
        singleton_states.append((op, singleton))
    
    # === STAGE 3: δ-Bound Checks ===
    # (Requires pre_state - would need to pass in)
    # Skip for now - would use delta_norm_check from NK-1
    
    # === STAGE 4: State Patching ===
    post_state = patch_state_with_batch(
        context.pre_state,
        batch,
        [s for _, s in kernel_results]
    )
    
    # === STAGE 5: Measured Gate ===
    epsilon_measured, epsilon_hat = compute_batch_gate(
        batch,
        context.pre_state,
        post_state,
        context.curvature_matrix
    )
    
    valid, failure = verify_gate(
        epsilon_measured,
        epsilon_hat,
        context.policy_bundle
    )
    
    if not valid:
        return BatchAttemptResult(
            success=False,
            failure_code=failure,
            epsilon_measured=epsilon_measured,
            epsilon_hat=epsilon_hat,
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    
    # === SUCCESS ===
    execution_time = (time.time() - start_time) * 1000
    
    return BatchAttemptResult(
        success=True,
        post_state=post_state,
        epsilon_measured=epsilon_measured,
        epsilon_hat=epsilon_hat,
        execution_time_ms=execution_time,
    )
```

---

## 8. Failure Classification Priority

When multiple failures could occur, use this priority:

```python
FAILURE_PRIORITY = [
    FailureCode.INDEPENDENCE,      # 1. Planning-time
    FailureCode.POLICY_VETO,      # 2. Planning-time
    FailureCode.KERNEL_ERROR,     # 3. Execution-time
    FailureCode.DELTA_BOUND,      # 4. Execution-time
    FailureCode.GATE_EPS,          # 5. Execution-time
]


def classify_failure(failures: list[FailureCode]) -> FailureCode:
    """Classify single failure using priority."""
    for code in FAILURE_PRIORITY:
        if code in failures:
            return code
    return FailureCode.KERNEL_ERROR  # Default
```

---

## 9. Example Usage

```python
# Setup context
context = AttemptContext(
    pre_state=initial_state,
    batch=selected_batch,
    append_log=append_log,
    ledger_prev_hash=prev_commit_hash,
    scheduler_rule_id="greedy.curv.v1",
    scheduler_mode="id:mode.S",
    policy_bundle=policy_bundle,
    curvature_matrix=curvature_matrix,
)

# Execute attempt
executor = KernelExecutor(kernel_registry)
result = attempt_batch(context, executor)

if result.success:
    print(f"Batch committed: {result.post_state.hash()}")
    print(f"ε_measured={result.epsilon_measured}, ε_hat={result.epsilon_hat}")
else:
    print(f"Failed: {result.failure_code}")
```
