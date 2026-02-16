# NK-2 Conformance Tests

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`3_scheduler.md`](3_scheduler.md), [`6_failure_handling.md`](6_failure_handling.md), [`7_resource_caps.md`](7_resource_caps.md)

---

## Overview

This document defines the required conformance tests that must pass for NK-2 v1.0. These tests verify deterministic behavior, correct rescheduling, and proper resource handling.

---

## 1. Test Categories

### 1.1 Test Categories Overview

| Category | Description | Count |
|----------|-------------|-------|
| Determinism | Same inputs → same outputs | 5 |
| Rescheduling | Correct failure transforms | 4 |
| No-Attempt Receipts | Failed attempts emit nothing | 2 |
| Resource Caps | Cap boundary enforcement | 5 |
| Precedence | DAG constraints preserved | 3 |

---

## 2. Determinism Tests

### 2.1 Test: Same ExecPlan + Same State → Identical Commit Chain

```python
def test_determinism_identical_inputs():
    """
    Test: Same ExecPlan + Same initial state → identical commit chain.
    
    Verifies deterministic execution across multiple runs.
    """
    
    # Create test inputs
    exec_plan = create_test_exec_plan()
    initial_state = create_test_state()
    
    # Run multiple times
    results = []
    for _ in range(10):
        result = run_nk2(
            exec_plan=exec_plan,
            initial_state=initial_state,
            policy_bundle=policy_bundle,
            kernel_registry=kernel_registry,
            curvature_matrix=curvature_matrix,
        )
        results.append((
            result.final_state_hash,
            result.final_commit_hash,
            len(result.receipt_chain),
        ))
    
    # All results must be identical
    assert len(set(results)) == 1, "Results must be identical"


def test_determinism_shuffled_ready():
    """
    Test: Shuffled input ops still yield same schedule.
    
    Verifies canonical ordering is enforced.
    """
    
    exec_plan = create_test_exec_plan()
    initial_state = create_test_state()
    
    # Shuffle ops order in ExecPlan
    shuffled_plan = shuffle_ops(exec_plan)
    
    # Run
    result = run_nk2(
        exec_plan=shuffled_plan,
        initial_state=initial_state,
        ...
    )
    
    # Compare with canonical order result
    canonical_result = run_nk2(
        exec_plan=exec_plan,
        initial_state=initial_state,
        ...
    )
    
    assert result.final_state_hash == canonical_result.final_state_hash
    assert result.final_commit_hash == canonical_result.final_commit_hash
```

### 2.2 Test: Ready Ordering Invariance

```python
def test_ready_ordering_invariance():
    """
    Test: Ready set ordering doesn't affect final result.
    
    The scheduler must produce same batch regardless of Ready ordering.
    """
    
    # Create scenario with multiple ready ops
    exec_plan = create_exec_plan_with_ready_ops(4)
    initial_state = create_test_state()
    
    # Run with different Ready orderings
    results = []
    for ready_order in [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2]]:
        result = run_with_ready_order(exec_plan, initial_state, ready_order)
        results.append((result.final_state_hash, result.final_commit_hash))
    
    # All must be identical
    assert len(set(results)) == 1
```

### 2.3 Test: Append Sequence Determinism

```python
def test_append_sequence_determinism():
    """
    Test: Append log is deterministic.
    
    The append_log must be same for same inputs.
    """
    
    exec_plan = create_test_exec_plan()
    initial_state = create_test_state()
    
    results = []
    for _ in range(5):
        result = run_nk2(...)
        # Extract append logs from receipt chain
        append_logs = extract_append_logs(result.receipt_chain)
        results.append(tuple(append_logs))
    
    assert len(set(results)) == 1
```

---

## 3. Rescheduling Tests

### 3.1 Test: Gate Fail → Split Lexmin

```python
def test_gate_fail_split_lexmin():
    """
    Test: Gate failure on wide batch → split lexmin always same op peeled.
    
    When a batch fails gate_eps, the lexmin (lexicographically smallest)
    op must be peeled off first, deterministically.
    """
    
    # Create batch that will fail gate
    batch = [
        OpSpec(op_id="id:op.z.001", ...),
        OpSpec(op_id="id:op.a.001", ...),
        OpSpec(op_id="id:op.m.001", ...),
    ]
    
    # Simulate gate failure
    failure = FailureCode.GATE_EPS
    result = handle_execution_failure(batch, failure)
    
    # Lexmin must be "id:op.a.001"
    assert result.split_op_id == "id:op.a.001"
    
    # Same failure always produces same split
    for _ in range(10):
        result2 = handle_execution_failure(batch, failure)
        assert result2.split_op_id == "id:op.a.001"
```

### 3.2 Test: Planning-Time Conflict → Last-Added Removal

```python
def test_planning_removes_last_added():
    """
    Test: Planning-time failure removes last-added op from append_log.
    
    When fail.independence or fail.policy_veto occurs,
    the last op in append_log must be removed.
    """
    
    batch_result = BatchResult(
        batch=[op_a, op_b, op_c],
        append_log=["id:op.a", "id:op.b", "id:op.c"],
        ...
    )
    
    failure = FailureCode.POLICY_VETO
    result = handle_planning_failure(batch_result, failure)
    
    # Must remove last-added (op_c)
    assert result.append_log == ["id:op.a", "id:op.b"]
    assert len(result.batch) == 2
```

### 3.3 Test: Execution-Time Split Returns to Ready

```python
def test_execution_split_returns_to_ready():
    """
    Test: After split, returned ops respect DAG constraints.
    
    Ops returned to Ready after split must still satisfy precedence.
    """
    
    # Create DAG: A → B, A → C, B → D, C → D
    dag_edges = [
        ("id:op.a", "id:op.b"),
        ("id:op.a", "id:op.c"),
        ("id:op.b", "id:op.d"),
        ("id:op.c", "id:op.d"),
    ]
    
    # Batch = [B, C] fails, split removes B (lexmin)
    batch = [op_b, op_c]
    failure = FailureCode.GATE_EPS
    
    result = handle_execution_failure(batch, failure)
    
    # Returned: [C]
    assert result.returned_ops == ["id:op.c"]
    
    # Verify C's dependencies are satisfied (A is already committed)
    # This must be true for the test to pass
    assert verify_precedence_after_split(plan, "id:op.b", result.returned_ops)
```

### 3.4 Test: Split Reduces Batch Width

```python
def test_split_reduces_width():
    """
    Test: Split always reduces future batch width.
    
    Each split peels exactly one op, reducing potential batch size.
    """
    
    for width in [2, 3, 4, 5, 8, 16]:
        batch = create_batch_of_width(width)
        failure = FailureCode.GATE_EPS
        
        result = handle_execution_failure(batch, failure)
        
        # Singleton batch created
        assert len(result.singleton_batch) == 1
        
        # Rest returned to Ready
        assert len(result.returned_ops) == width - 1
```

---

## 4. No-Attempt Receipts Tests

### 4.1 Test: Failed Attempts Produce No Receipts

```python
def test_no_receipts_for_failures():
    """
    Test: Failed attempts produce zero ledger entries.
    
    v1.0 rule: only successful commits emit receipts.
    """
    
    # Create scenario that will fail
    exec_plan = create_exec_plan_that_fails()
    initial_state = create_test_state()
    
    result = run_nk2(...)
    
    # Should have terminal error
    assert not result.success
    
    # Ledger should be empty (no commits)
    assert len(result.receipt_chain) == 0
    
    # Or if partial commits exist, verify no gaps
    # (would need more complex test)
```

### 4.2 Test: Only Successful Commits in Chain

```python
def test_only_successful_commits():
    """
    Test: Receipt chain contains only successful commits.
    
    Each commit in the ledger must have passed the gate.
    """
    
    result = run_nk2(...)
    
    for receipt in result.receipt_chain:
        # Verify epsilon_measured <= epsilon_hat
        assert receipt.epsilon_measured <= receipt.epsilon_hat
        
        # Verify all local receipts exist
        assert receipt.batch_size > 0
```

---

## 5. Resource Caps Tests

### 5.1 Test: BigInt Bits Cap

```python
def test_cap_bigint_bits_reject():
    """
    Test: BigInt bits cap rejects deterministically.
    
    When max_bigint_bits is exceeded, execution halts immediately.
    """
    
    caps = ResourceCaps(
        max_bigint_bits=4096,
        ...
    )
    tracker = ResourceTracker(caps)
    
    # At cap: should pass
    assert tracker.check_bigint_bits(4096) == True
    
    # Over cap: should fail
    assert tracker.check_bigint_bits(4097) == False


def test_cap_bigint_bits_execution():
    """
    Test: Execution halts when BigInt cap exceeded.
    """
    
    # Create exec with small cap
    exec_plan = create_exec_plan(resource_caps=ResourceCaps(
        max_bigint_bits=1024,
        ...
    ))
    
    # Run with inputs that would exceed
    result = run_nk2(exec_plan=exec_plan, ...)
    
    # Should halt with terminal error
    assert not result.success
    assert result.terminal_error.error_code == "err.cap.bigint_bits_exceeded"
```

### 5.2 Test: Matrix Terms Cap

```python
def test_cap_matrix_terms():
    """
    Test: Matrix accumulation terms cap enforced.
    """
    
    caps = ResourceCaps(
        max_matrix_accum_terms=10000,
        ...
    )
    tracker = ResourceTracker(caps)
    
    assert tracker.check_matrix_terms(10000) == True
    assert tracker.check_matrix_terms(10001) == False
```

### 5.3 Test: Fields Touched Cap

```python
def test_cap_fields_touched():
    """
    Test: Fields touched per op cap enforced.
    """
    
    caps = ResourceCaps(
        max_fields_touched_per_op=100,
        ...
    )
    tracker = ResourceTracker(caps)
    
    fields_99 = set(f"field_{i}" for i in range(99))
    fields_100 = set(f"field_{i}" for i in range(100))
    fields_101 = set(f"field_{i}" for i in range(101))
    
    assert tracker.check_fields_touched(fields_99) == True
    assert tracker.check_fields_touched(fields_100) == True
    assert tracker.check_fields_touched(fields_101) == False
```

### 5.4 Test: V Eval Cost Cap

```python
def test_cap_v_eval_cost():
    """
    Test: V(x) evaluation cost cap enforced.
    """
    
    caps = ResourceCaps(
        max_v_eval_cost=1000000,
        ...
    )
    tracker = ResourceTracker(caps)
    
    assert tracker.check_v_eval_cost(1000000) == True
    assert tracker.check_v_eval_cost(1000001) == False
```

### 5.5 Test: No Reschedule on Cap

```python
def test_no_reschedule_on_cap():
    """
    Test: Resource cap errors never trigger rescheduling.
    
    Unlike other failures, cap errors are always terminal.
    """
    
    # Simulate cap error during batch attempt
    resource_error = ResourceError(
        error_code=ResourceErrorCode.BIGINT_BITS_EXCEEDED,
        ...
    )
    
    result = handle_failure_with_caps(
        failure_code=FailureCode.CAP_EXCEEDED,
        batch=[op_a, op_b],
        resource_error=resource_error,
    )
    
    # Must halt
    assert result.action == ContinueAction.HALT
    assert result.terminal_error is not None
```

---

## 6. Precedence Tests

### 6.1 Test: Precedence After Split

```python
def test_precedence_after_split():
    """
    Test: After split, returned ops still respect DAG constraints.
    """
    
    # Create DAG where split could violate precedence
    dag = {
        "a": [],
        "b": ["a"],
        "c": ["a"],
        "d": ["b", "c"],
    }
    
    # If batch [b, c] splits and returns c to Ready,
    # c must not depend on b (which was peeled)
    # Since both depend on a (already done), this is valid
    
    exec_plan = create_exec_plan_with_dag(dag)
    result = run_nk2(exec_plan, ...)
    
    # Final state should include all ops
    assert len(result.receipt_chain) == expected_commits
```

### 6.2 Test: No Precedence Violation

```python
def test_no_precedence_violation():
    """
    Test: Committed ops never violate DAG ordering.
    """
    
    result = run_nk2(...)
    
    # Build precedence map from DAG
    dag_edges = exec_plan.dag_edges
    
    # For each commit, verify all predecessors are committed
    committed = set()
    for receipt in result.receipt_chain:
        # Get ops in this commit
        ops_in_commit = get_ops_from_receipt(receipt)
        
        for op_id in ops_in_commit:
            # Check all predecessors are committed
            predecessors = get_predecessors(op_id, dag_edges)
            for pred in predecessors:
                assert pred in committed
        
        # Add to committed
        committed.update(ops_in_commit)
```

### 6.3 Test: DAG Cycles Rejected

```python
def test_dag_cycles_rejected():
    """
    Test: ExecPlan with cycles is rejected at validation.
    """
    
    # Create ExecPlan with cycle: A → B → C → A
    exec_plan = create_exec_plan_with_cycle()
    
    # Validation should fail
    result = validate_exec_plan(exec_plan, policy_bundle)
    
    assert not result.valid
    assert "dag_has_cycles" in result.errors
```

---

## 7. Running Tests

### 7.1 Test Runner

```python
def run_conformance_tests():
    """Run all conformance tests."""
    
    test_suite = [
        # Determinism
        test_determinism_identical_inputs,
        test_determinism_shuffled_ready,
        test_ready_ordering_invariance,
        test_append_sequence_determinism,
        
        # Rescheduling
        test_gate_fail_split_lexmin,
        test_planning_removes_last_added,
        test_execution_split_returns_to_ready,
        test_split_reduces_width,
        
        # No-Attempt Receipts
        test_no_receipts_for_failures,
        test_only_successful_commits,
        
        # Resource Caps
        test_cap_bigint_bits_reject,
        test_cap_bigint_bits_execution,
        test_cap_matrix_terms,
        test_cap_fields_touched,
        test_cap_v_eval_cost,
        test_no_reschedule_on_cap,
        
        # Precedence
        test_precedence_after_split,
        test_no_precedence_violation,
        test_dag_cycles_rejected,
    ]
    
    passed = 0
    failed = 0
    
    for test in test_suite:
        try:
            test()
            passed += 1
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__}: {e}")
    
    print(f"\n{passed}/{passed+failed} tests passed")
    return failed == 0
```

---

## 8. Summary

| Test Category | Tests | Required Pass Rate |
|---------------|-------|-------------------|
| Determinism | 4 | 100% |
| Rescheduling | 4 | 100% |
| No-Attempt Receipts | 2 | 100% |
| Resource Caps | 5 | 100% |
| Precedence | 3 | 100% |

All conformance tests must pass for NK-2 v1.0 to be considered complete.
