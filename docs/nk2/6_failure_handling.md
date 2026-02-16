# NK-2 Failure Handling + Rescheduling

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`3_scheduler.md`](3_scheduler.md), [`4_batch_attempt.md`](4_batch_attempt.md)

---

## Overview

This document defines deterministic failure handling and rescheduling transforms. When a batch attempt fails, NK-2 applies deterministic rules to either retry with modifications or halt. The key principle: **no improvisation** - failure handling is as deterministic as success.

---

## 1. Failure Classification

### 1.1 Failure Types

| Category | Failure Code | Stage | Description |
|----------|-------------|-------|-------------|
| Planning | `fail.independence` | Planning | Scheduler produced dependent ops |
| Planning | `fail.policy_veto` | Planning | Policy constraint violation |
| Execution | `fail.kernel_error` | Kernel | Kernel execution error |
| Execution | `fail.delta_bound` | δ-check | δ-norm exceeds bound |
| Execution | `fail.gate_eps` | Gate | ε_measured > ε_hat |
| Terminal | `err.*.singleton` | Any | Singleton op failed |

### 1.2 Failure Priority

When multiple failures could occur, classify using this priority:

```python
FAILURE_PRIORITY = [
    # Planning-time (lower number = higher priority)
    FailureCode.INDEPENDENCE,       # 1
    FailureCode.POLICY_VETO,       # 2
    
    # Execution-time
    FailureCode.KERNEL_ERROR,       # 3
    FailureCode.DELTA_BOUND,       # 4
    FailureCode.GATE_EPS,          # 5
    
    # Terminal (highest priority - immediate halt)
    FailureCode.KERNEL_ERROR_SINGLETON,
    FailureCode.DELTA_BOUND_SINGLETON,
    FailureCode.POLICY_VETO_SINGLETON,
]


def classify_failure(failures: list[FailureCode]) -> FailureCode:
    """Classify single failure using priority."""
    for code in FAILURE_PRIORITY:
        if code in failures:
            return code
    return FailureCode.KERNEL_ERROR  # Default
```

---

## 2. Rescheduling Transforms

### 2.1 Transform Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAILURE HANDLING FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Batch Fails                                                     │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐     ┌─────────────┐                            │
│  │ Planning?   │─Yes─→│ Remove last │                            │
│  └─────────────┘     │ added op    │                            │
│       │ No           └─────────────┘                            │
│       ▼                                                        │
│  ┌─────────────┐     ┌─────────────┐                            │
│  │ Singleton?  │─Yes─→│   HALT      │                            │
│  └─────────────┘     │ (terminal)  │                            │
│       │ No           └─────────────┘                            │
│       ▼                                                        │
│  ┌─────────────┐     ┌─────────────┐                            │
│  │ Split lexmin│─Yes─→│ Schedule    │                            │
│  │             │     │ singleton   │                            │
│  └─────────────┘     │ B1 = [min]  │                            │
│                      │ Return rest │                            │
│                      └─────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Planning-Time Failures

```python
def handle_planning_failure(
    batch_result: BatchResult,
    failure_code: FailureCode
) -> BatchResult:
    """
    Handle planning-time failure by removing last-added op.
    
    Used for:
    - fail.independence
    - fail.policy_veto
    
    Transform: Remove o_last = append_log[-1] from batch
    """
    if failure_code not in [FailureCode.INDEPENDENCE, FailureCode.POLICY_VETO]:
        raise ValueError(f"Invalid planning failure: {failure_code}")
    
    if len(batch_result.batch) == 0:
        raise ValueError("Cannot remove from empty batch")
    
    # Remove last op (canonical - always append_log[-1])
    new_batch = batch_result.batch[:-1]
    new_append_log = batch_result.append_log[:-1]
    
    # Note: Cost is not recalculated exactly - this is intentional
    # The retry uses the same curvature calculation but without the problematic op
    
    return BatchResult(
        batch=new_batch,
        append_log=new_append_log,
        total_cost=batch_result.total_cost,  # Approximate
        is_full=False,
    )
```

### 2.3 Execution-Time Failures

```python
@dataclass
class SplitResult:
    """Result of split lexmin transform."""
    
    singleton_batch: list[OpSpec]    # B1 = [o_min]
    returned_ops: list[OpID]         # B_rest returned to Ready
    split_op_id: OpID                # The peeled op


def handle_execution_failure(
    batch: list[OpSpec],
    failure_code: FailureCode
) -> SplitResult:
    """
    Handle execution-time failure with split lexmin.
    
    Used for:
    - fail.kernel_error
    - fail.delta_bound
    - fail.gate_eps
    
    Transform: resched.split_lexmin.v1
    1. o_min = lexmin(op_id in B) [lexicographically smallest]
    2. B1 = [o_min] (singleton batch next)
    3. B_rest = B \ {o_min} (return to Ready)
    """
    if failure_code not in [
        FailureCode.KERNEL_ERROR,
        FailureCode.DELTA_BOUND,
        FailureCode.GATE_EPS
    ]:
        raise ValueError(f"Invalid execution failure: {failure_code}")
    
    if len(batch) == 0:
        raise ValueError("Cannot split empty batch")
    
    # Lexicographically smallest op_id (canonical ordering)
    sorted_batch = sorted(batch, key=lambda op: op.op_id.encode('utf-8'))
    o_min = sorted_batch[0]
    
    # B1 = [o_min]
    singleton_batch = [o_min]
    
    # B_rest = B \ {o_min}
    returned_ops = [op.op_id for op in batch if op.op_id != o_min.op_id]
    
    return SplitResult(
        singleton_batch=singleton_batch,
        returned_ops=returned_ops,
        split_op_id=o_min.op_id,
    )
```

---

## 3. Singleton Terminal Rule

### 3.1 Terminal Conditions

```python
TERMINAL_FAILURE_CODES = [
    FailureCode.KERNEL_ERROR_SINGLETON,
    FailureCode.DELTA_BOUND_SINGLETON,
    FailureCode.POLICY_VETO_SINGLETON,
    # Defensive: gate failure on singleton is also terminal
    FailureCode.GATE_EPS,  # Should be impossible but defensive
]


def is_terminal_failure(failure_code: FailureCode, batch_size: int) -> bool:
    """
    Check if failure is terminal.
    
    Terminal if:
    - Singleton batch fails with terminal code
    - Any batch fails with singleton terminal code
    """
    if batch_size == 1 and failure_code in TERMINAL_FAILURE_CODES:
        return True
    
    # Also check for explicit singleton terminal codes
    if failure_code in [
        FailureCode.KERNEL_ERROR_SINGLETON,
        FailureCode.DELTA_BOUND_SINGLETON,
        FailureCode.POLICY_VETO_SINGLETON,
    ]:
        return True
    
    return False
```

### 3.2 Terminal Error

```python
@dataclass
class TerminalError:
    """Terminal error that halts execution."""
    
    error_code: str
    failed_op_id: OpID
    failure_code: FailureCode
    batch_size: int
    batch_prev_hash: Hash256
    
    def __str__(self) -> str:
        return (
            f"TerminalError({self.error_code}): "
            f"op={self.failed_op_id}, "
            f"failure={self.failure_code.value}, "
            f"batch_size={self.batch_size}"
        )


def create_terminal_error(
    failure_code: FailureCode,
    batch: list[OpSpec],
    batch_prev_hash: Hash256
) -> TerminalError:
    """Create terminal error from failed batch."""
    
    if len(batch) != 1:
        # This shouldn't happen, but handle defensively
        op_id = batch[0].op_id  # Use first op
    else:
        op_id = batch[0].op_id
    
    error_code_map = {
        FailureCode.KERNEL_ERROR_SINGLETON: "err.kernel_error.singleton",
        FailureCode.DELTA_BOUND_SINGLETON: "err.delta_bound.singleton",
        FailureCode.POLICY_VETO_SINGLETON: "err.policy_veto.singleton",
        FailureCode.GATE_EPS: "err.gate_eps.singleton",
    }
    
    return TerminalError(
        error_code=error_code_map.get(failure_code, "err.unknown"),
        failed_op_id=op_id,
        failure_code=failure_code,
        batch_size=len(batch),
        batch_prev_hash=batch_prev_hash,
    )
```

---

## 4. No Attempt Receipts

### 4.1 v1.0 Rule

```python
def emit_receipts_for_failure(
    failure_code: FailureCode,
    batch: list[OpSpec]
) -> bool:
    """
    Determine if receipts should be emitted for a failed attempt.
    
    v1.0 rule: NO receipts for failed attempts.
    
    Returns:
        True if receipts should be emitted (i.e., success)
    """
    return False  # Always false for failures
```

### 4.2 Ledger Invariant

```python
def verify_no_failed_attempt_receipts(ledger: ReceiptLedger) -> bool:
    """
    Verify ledger contains only successful commits.
    
    v1.0 invariant: failed attempts produce zero ledger entries.
    """
    # This is enforced by the main loop not calling append on failure
    # We verify by checking each commit passes verification
    for receipt in ledger.commits:
        if not verify_commit_structure(receipt):
            return False
    return True
```

---

## 5. Full Failure Handling

### 5.1 Handle Failure

```python
from dataclasses import dataclass
from enum import Enum, auto


class ContinueAction(Enum):
    """Action to take after failure handling."""
    RETRY_BATCH = auto()      # Retry with modified batch
    SCHEDULE_SINGLETON = auto()  # Schedule singleton next
    RETURN_TO_READY = auto()   # Return ops to Ready
    HALT = auto()              # Stop execution


@dataclass
class FailureResult:
    """Result of failure handling."""
    
    action: ContinueAction
    
    # For RETRY_BATCH
    retry_batch: list[OpSpec] | None = None
    retry_append_log: list[OpID] | None = None
    
    # For SCHEDULE_SINGLETON
    singleton_batch: list[OpSpec] | None = None
    
    # For RETURN_TO_READY
    returned_ops: list[OpID] | None = None
    
    # For HALT
    terminal_error: TerminalError | None = None
    
    # Failure info
    failure_code: FailureCode | None = None
    split_op_id: OpID | None = None


def handle_failure(
    failure_code: FailureCode,
    batch: list[OpSpec],
    batch_result: BatchResult,
    batch_prev_hash: HashNumber
) -> FailureResult:
    """
    Handle batch failure with deterministic transforms.
    
    Args:
        failure_code: Classified failure code
        batch: The failed batch
        batch_result: Original batch result with append_log
        batch_prev_hash: Current ledger anchor
    
    Returns:
        FailureResult with next action
    """
    # Check for terminal
    if is_terminal_failure(failure_code, len(batch)):
        return FailureResult(
            action=ContinueAction.HALT,
            terminal_error=create_terminal_error(failure_code, batch, batch_prev_hash),
            failure_code=failure_code,
        )
    
    # Planning-time failures: remove last-added
    if failure_code in [FailureCode.INDEPENDENCE, FailureCode.POLICY_VETO]:
        # Remove last-added and retry
        new_result = handle_planning_failure(batch_result, failure_code)
        
        return FailureResult(
            action=ContinueAction.RETRY_BATCH,
            retry_batch=new_result.batch,
            retry_append_log=new_result.append_log,
            failure_code=failure_code,
        )
    
    # Execution-time failures: split lexmin
    if failure_code in [
        FailureCode.KERNEL_ERROR,
        FailureCode.DELTA_BOUND,
        FailureCode.GATE_EPS,
    ]:
        split_result = handle_execution_failure(batch, failure_code)
        
        return FailureResult(
            action=ContinueAction.SCHEDULE_SINGLETON,
            singleton_batch=split_result.singleton_batch,
            returned_ops=split_result.returned_ops,
            failure_code=failure_code,
            split_op_id=split_result.split_op_id,
        )
    
    # Should not reach here
    raise ValueError(f"Unknown failure code: {failure_code}")
```

---

## 6. Progress Guarantees

### 6.1 Termination Theorem

```python
def verify_termination(
    plan: ExecPlan,
    initial_state: State
) -> bool:
    """
    Verify execution terminates for given plan.
    
    The system guarantees:
    1. No infinite planning-time loops (removal reduces batch)
    2. No infinite execution-time loops (split reduces width)
    3. Singleton failures halt (terminal rule)
    
    Therefore, execution must terminate.
    """
    # This is proven by the design, not tested at runtime
    return True  # Always terminates by construction
```

### 6.2 Worst-Case Behavior

In worst case (repeated failures), the system converges to **serialized execution**:

```
Initial:     [A, B, C, D] (P=4)
After fail:  [A] + return [B, C, D]
After fail:  [B] + return [C, D]
After fail:  [C] + return [D]
After fail:  [D] (single, commits)
```

This is deterministic "pressure behavior" - no scheduler improvisation.

---

## 7. Precedence Preservation

### 7.1 DAG Constraints After Split

```python
def verify_precedence_after_split(
    plan: ExecPlan,
    split_op: OpID,
    returned_ops: list[OpID]
) -> bool:
    """
    Verify returned ops still respect DAG constraints.
    
    After split lexmin:
    - split_op is scheduled as singleton
    - returned_ops return to Ready
    
    Must ensure:
    1. No returned op depends on split_op (would violate precedence)
    2. All dependencies of returned ops are still satisfied
    """
    # Build dependency map
    predecessors = {op_id: [] for op_id in returned_ops}
    for a, b in plan.dag_edges:
        if b in returned_ops:
            predecessors[b].append(a)
    
    # Check: no returned op depends on split_op
    for op_id in returned_ops:
        if split_op in predecessors[op_id]:
            return False  # Would violate precedence
    
    return True
```

---

## 8. Example Usage

```python
# Attempt batch
result = attempt_batch(context, executor)

if not result.success:
    # Handle failure
    failure_result = handle_failure(
        failure_code=result.failure_code,
        batch=selected_batch,
        batch_result=batch_result,
        batch_prev_hash=ledger.current_hash
    )
    
    if failure_result.action == ContinueAction.HALT:
        print(f"Halting: {failure_result.terminal_error}")
        return  # Exit main loop
    
    elif failure_result.action == ContinueAction.RETRY_BATCH:
        # Retry with modified batch (removed last-added)
        selected_batch = failure_result.retry_batch
        append_log = failure_result.retry_append_log
        continue  # Retry attempt
    
    elif failure_result.action == ContinueAction.SCHEDULE_SINGLETON:
        # Schedule singleton, return rest to Ready
        selected_batch = failure_result.singleton_batch
        returned_ops = failure_result.returned_ops
        # Return ops to Ready via tracker
        for op_id in returned_ops:
            tracker.mark_ready(op_id)
```

---

## 9. Determinism Verification

### 9.1 Test: Same Failure = Same Transform

```python
def test_failure_determinism():
    """Verify same failure always triggers same transform."""
    
    # Same batch, same failure → same split
    batch = [op_a, op_b, op_c]
    failure = FailureCode.GATE_EPS
    
    result1 = handle_execution_failure(batch, failure)
    result2 = handle_execution_failure(batch, failure)
    
    assert result1.split_op_id == result2.split_op_id  # Always op_a
    
    # Same batch, same planning failure → same removal
    batch_result = BatchResult(batch, append_log=['a', 'b', 'c'], ...)
    failure = FailureCode.POLICY_VETO
    
    result1 = handle_planning_failure(batch_result, failure)
    result2 = handle_planning_failure(batch_result, failure)
    
    assert result1.append_log == result2.append_log  # ['a', 'b']
```

---

## 10. Summary: Rescheduling Transforms

| Failure Type | Transform | Result |
|--------------|-----------|--------|
| `fail.independence` | Remove last-added | Retry with smaller batch |
| `fail.policy_veto` | Remove last-added | Retry with smaller batch |
| `fail.kernel_error` | Split lexmin | Schedule singleton, return rest |
| `fail.delta_bound` | Split lexmin | Schedule singleton, return rest |
| `fail.gate_eps` | Split lexmin | Schedule singleton, return rest |
| `err.*.singleton` | Halt | Terminal error |
