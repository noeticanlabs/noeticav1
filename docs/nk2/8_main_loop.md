# NK-2 Canonical Main Loop

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`2_runtime_state.md`](2_runtime_state.md), [`3_scheduler.md`](3_scheduler.md), [`4_batch_attempt.md`](4_batch_attempt.md)

---

## Overview

This document defines the canonical main loop algorithm that orchestrates all NK-2 execution. The main loop combines scheduling, batch attempt, failure handling, and state management into a deterministic execution engine.

---

## 1. Main Loop Algorithm

### 1.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      NK-2 MAIN LOOP                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. VALIDATE                                                     │
│     ├─ Verify PolicyBundle allowlist                            │
│     └─ Verify initial state hash                                │
│           ↓                                                      │
│  2. INITIALIZE                                                  │
│     ├─ Build DAG indegrees                                      │
│     ├─ Compute initial Ready set                                │
│     └─ Initialize ledger anchor                                 │
│           ↓                                                      │
│  3. WHILE PENDING ≠ ∅                                          │
│     │                                                            │
│     ├─→ BUILD BATCH                                            │
│     │     └─ Greedy.curv.v1 scheduler                         │
│     │           ↓                                               │
│     ├─→ ATTEMPT BATCH                                          │
│     │     ├─ Planning checks                                   │
│     │     ├─ Kernel execution                                  │
│     │     ├─ δ-bound checks                                   │
│     │     ├─ State patching                                   │
│     │     └─ Measured gate                                    │
│     │           ↓                                               │
│     ├─→ IF SUCCESS                                             │
│     │     ├─ Emit local receipts                              │
│     │     ├─ Emit commit receipt                              │
│     │     ├─ Update state + ledger                            │
│     │     ├─ Update DAG + Ready                               │
│     │     └─ Continue                                         │
│     │                                                           │
│     └─→ IF FAIL                                                │
│           ├─ Classify failure                                   │
│           ├─ Apply rescheduling transform                       │
│           ├─ If terminal → HALT                                │
│           └─ Continue                                          │
│                                                                  │
│  4. OUTPUT                                                      │
│     └─ Final state hash, commit hash, receipt chain              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Main Loop Class

```python
class NK2Runtime:
    """NK-2 Runtime Executor."""
    
    def __init__(
        self,
        exec_plan: ExecPlan,
        initial_state: State,
        policy_bundle: PolicyBundle,
        kernel_registry: KernelRegistry,
        curvature_matrix: CurvatureMatrix,
    ):
        # Validate inputs
        self._validate_inputs(exec_plan, initial_state, policy_bundle)
        
        # Store components
        self.exec_plan = exec_plan
        self.initial_state = initial_state
        self.policy_bundle = policy_bundle
        self.kernel_registry = kernel_registry
        self.curvature_matrix = curvature_matrix
        
        # Initialize runtime state
        self._initialize()
        
        # Create scheduler
        self.scheduler = GreedyCurvScheduler(
            config=SchedulerConfig(
                max_parallel_width=exec_plan.max_parallel_width_P,
                scheduler_rule_id=exec_plan.scheduler_rule_id,
                scheduler_mode=exec_plan.scheduler_mode,
                policy_bundle=policy_bundle,
            ),
            curvature_matrix=curvature_matrix,
        )
        
        # Create executor
        self.executor = KernelExecutor(kernel_registry)
        
        # Create resource tracker
        self.resource_tracker = ResourceTracker(exec_plan.resource_caps)
    
    def _validate_inputs(
        self,
        exec_plan: ExecPlan,
        initial_state: State,
        policy_bundle: PolicyBundle
    ) -> None:
        """Validate inputs before execution."""
        
        # Check policy digest matches
        if exec_plan.policy_digest != policy_bundle.digest:
            raise ValueError("policy_digest_mismatch")
        
        # Check initial state hash
        if initial_state.hash() != exec_plan.initial_state_hash:
            raise ValueError("initial_state_hash_mismatch")
        
        # Check scheduler rule is allowlisted
        if exec_plan.scheduler_rule_id not in policy_bundle.allowed_scheduler_rules:
            raise ValueError("scheduler_rule_not_allowlisted")
    
    def _initialize(self) -> None:
        """Initialize runtime state."""
        
        # Compute genesis hash
        self.genesis_hash = self._compute_genesis_hash()
        
        # Initialize ledger
        self.ledger = ReceiptLedger(self.genesis_hash)
        
        # Initialize runtime state
        self.state = RuntimeState(
            x=self.initial_state,
            ledger_prev_hash=self.genesis_hash,
            committed=frozenset(),
            pending=frozenset(op.op_id for op in self.exec_plan.ops),
        )
        
        # Initialize dependency tracker
        self.tracker = DependencyTracker(
            self.exec_plan.ops,
            self.exec_plan.dag_edges,
        )
        
        # Compute initial ready set
        self.ready = self.tracker.get_ready_set(self.state.committed)
        
        # Execution statistics
        self.stats = ExecutionStats()
    
    def _compute_genesis_hash(self) -> Hash256:
        """Compute genesis hash for this execution."""
        return Hash256(sha256(
            self.exec_plan.plan_id.encode('utf-8') +
            self.exec_plan.initial_state_hash.bytes +
            b'genesis'
        ))
    
    def execute(self) -> ExecutionResult:
        """Execute the main loop."""
        
        iteration = 0
        max_iterations = 10000  # Safety limit
        
        while self.state.pending:
            iteration += 1
            if iteration > max_iterations:
                raise RuntimeError("max_iterations_exceeded")
            
            # === BUILD BATCH ===
            ready_ops = [self.tracker._in_degree  # Get OpSpec for ready ops
            batch_result = self._build_batch()
            
            # === ATTEMPT BATCH ===
            attempt_result = self._attempt_batch(batch_result)
            
            if attempt_result.success:
                # === SUCCESS ===
                self._handle_success(attempt_result, batch_result)
            else:
                # === FAILURE ===
                should_continue, should_halt = self._handle_failure(
                    attempt_result, batch_result
                )
                
                if should_halt:
                    return ExecutionResult(
                        success=False,
                        terminal_error=attempt_result.terminal_error,
                        final_state_hash=self.state.x.hash(),
                        final_commit_hash=self.ledger.current_hash,
                        stats=self.stats,
                    )
                # Continue (possibly with modified batch)
        
        # === COMPLETE ===
        return ExecutionResult(
            success=True,
            final_state_hash=self.state.x.hash(),
            final_commit_hash=self.ledger.current_hash,
            receipt_chain=self.ledger.commits,
            stats=self.stats,
        )
```

---

## 2. Batch Building

### 2.1 Build Batch Step

```python
def _build_batch(self) -> BatchResult:
    """Build next batch using scheduler."""
    
    # Get OpSpecs for ready ops
    ready_ops = []
    for op_id in self.ready:
        op_spec = self._get_op_spec(op_id)
        ready_ops.append(op_spec)
    
    # Build batch using greedy.curv.v1
    batch_result = self.scheduler.build_batch(ready_ops)
    
    self.stats.batches_built += 1
    
    return batch_result
```

### 2.2 Get OpSpec

```python
def _get_op_spec(self, op_id: OpID) -> OpSpec:
    """Get OpSpec by ID."""
    for op in self.exec_plan.ops:
        if op.op_id == op_id:
            return op
    raise ValueError(f"Unknown op_id: {op_id}")
```

---

## 3. Batch Attempt

### 3.1 Attempt Batch Step

```python
def _attempt_batch(self, batch_result: BatchResult) -> BatchAttemptResult:
    """Attempt to execute batch."""
    
    # Get OpSpecs for batch
    batch = batch_result.batch
    append_log = batch_result.append_log
    
    # Create context
    context = AttemptContext(
        pre_state=self.state.x,
        batch=batch,
        append_log=append_log,
        ledger_prev_hash=self.state.ledger_prev_hash,
        scheduler_rule_id=self.exec_plan.scheduler_rule_id,
        scheduler_mode=self.exec_plan.scheduler_mode,
        policy_bundle=self.policy_bundle,
        curvature_matrix=self.curvature_matrix,
    )
    
    # Attempt with resource tracking
    result = attempt_batch_with_caps(
        context=context,
        executor=self.executor,
        tracker=self.resource_tracker,
    )
    
    self.stats.attempts += 1
    
    return result
```

---

## 4. Success Handling

### 4.1 Handle Success

```python
def _handle_success(
    self,
    attempt_result: BatchAttemptResult,
    batch_result: BatchResult
) -> None:
    """Handle successful batch commit."""
    
    batch = batch_result.batch
    append_log = batch_result.append_log
    
    # Generate receipts
    local_receipts, commit_receipt = generate_batch_receipts(
        batch=batch,
        pre_state=self.state.x,
        post_state=attempt_result.post_state,
        singleton_states=[],  # Would need to track these
        batch_prev_hash=self.state.ledger_prev_hash,
        context=AttemptContext(
            pre_state=self.state.x,
            batch=batch,
            append_log=append_log,
            ledger_prev_hash=self.state.ledger_prev_hash,
            scheduler_rule_id=self.exec_plan.scheduler_rule_id,
            scheduler_mode=self.exec_plan.scheduler_mode,
            policy_bundle=self.policy_bundle,
            curvature_matrix=self.curvature_matrix,
        ),
        epsilon_measured=attempt_result.epsilon_measured,
        epsilon_hat=attempt_result.epsilon_hat,
    )
    
    # Append to ledger
    self.ledger.append(commit_receipt)
    
    # Update state
    self.state = RuntimeState(
        x=attempt_result.post_state,
        ledger_prev_hash=commit_receipt.hash(),
        committed=self.state.committed | frozenset(op.op_id for op in batch),
        pending=self.state.pending - frozenset(op.op_id for op in batch),
    )
    
    # Update DAG and Ready
    for op in batch:
        self.tracker.mark_committed(op.op_id)
    
    self.ready = self.tracker.get_ready_set(self.state.committed)
    
    # Update stats
    self.stats.commits += 1
    self.stats.total_ops_committed += len(batch)
```

---

## 5. Failure Handling

### 5.1 Handle Failure

```python
def _handle_failure(
    self,
    attempt_result: BatchAttemptResult,
    batch_result: BatchResult
) -> tuple[bool, bool]:
    """
    Handle failed batch attempt.
    
    Returns:
        (should_continue, should_halt)
    """
    
    # Classify failure
    failure_code = attempt_result.failure_code
    
    # Check for resource error (always terminal)
    if attempt_result.resource_error is not None:
        self.stats.failures += 1
        return False, True  # HALT
    
    # Check for terminal (singleton) failure
    if is_terminal_failure(failure_code, len(batch_result.batch)):
        self.stats.failures += 1
        return False, True  # HALT
    
    # Planning-time failures: retry with modification
    if failure_code in [FailureCode.INDEPENDENCE, FailureCode.POLICY_VETO]:
        # Remove last-added and retry
        new_result = handle_planning_failure(batch_result, failure_code)
        
        # Update batch result for retry
        batch_result.batch = new_result.batch
        batch_result.append_log = new_result.append_log
        
        self.stats.planning_retries += 1
        return True, False  # CONTINUE with retry
    
    # Execution-time failures: split lexmin
    if failure_code in [
        FailureCode.KERNEL_ERROR,
        FailureCode.DELTA_BOUND,
        FailureCode.GATE_EPS,
    ]:
        # Split: schedule singleton, return rest to Ready
        split_result = handle_execution_failure(
            batch_result.batch, failure_code
        )
        
        # Schedule singleton
        batch_result.batch = split_result.singleton_batch
        batch_result.append_log = [op.op_id for op in split_result.singleton_batch]
        
        # Return rest to Ready (via tracker)
        for op_id in split_result.returned_ops:
            self.tracker.reset_op_degree(op_id)
        
        self.ready = self.tracker.get_ready_set(self.state.committed)
        
        self.stats.execution_splits += 1
        return True, False  # CONTINUE with singleton
    
    # Unknown failure
    raise ValueError(f"Unknown failure: {failure_code}")
```

---

## 6. Complete Main Loop

### 6.1 Full Implementation

```python
def run_nk2(
    exec_plan: ExecPlan,
    initial_state: State,
    policy_bundle: PolicyBundle,
    kernel_registry: KernelRegistry,
    curvature_matrix: CurvatureMatrix,
) -> ExecutionResult:
    """
    Run NK-2 execution.
    
    Canonical main loop algorithm:
    1. Validate PolicyBundle allowlist and chain lock
    2. Load initial state and verify hash
    3. Initialize DAG indegrees; Ready = sorted ops with indegree 0
    4. While Pending nonempty:
       a. Build candidate batch using greedy.curv.v1
       b. Attempt batch (planning, kernels, δ, gate)
       c. If success: emit receipts, update state
       d. If fail: classify, apply transform, halt if terminal
       e. If singleton terminal failure or cap: halt
    5. Output: final state hash, final commit hash, receipt chain
    """
    
    # === STEP 1: VALIDATE ===
    if policy_bundle.digest != exec_plan.policy_digest:
        raise ValueError("policy_digest_mismatch")
    
    if initial_state.hash() != exec_plan.initial_state_hash:
        raise ValueError("initial_state_hash_mismatch")
    
    # === STEP 2: INITIALIZE ===
    runtime = NK2Runtime(
        exec_plan=exec_plan,
        initial_state=initial_state,
        policy_bundle=policy_bundle,
        kernel_registry=kernel_registry,
        curvature_matrix=curvature_matrix,
    )
    
    # === STEP 3: MAIN LOOP ===
    result = runtime.execute()
    
    # === STEP 4: OUTPUT ===
    return result
```

---

## 7. Execution Statistics

### 7.1 Stats Tracking

```python
@dataclass
class ExecutionStats:
    """Runtime execution statistics."""
    
    batches_built: int = 0
    attempts: int = 0
    commits: int = 0
    failures: int = 0
    planning_retries: int = 0
    execution_splits: int = 0
    total_ops_committed: int = 0
    
    def __str__(self) -> str:
        return (
            f"ExecutionStats(\n"
            f"  batches_built={self.batches_built},\n"
            f"  attempts={self.attempts},\n"
            f"  commits={self.commits},\n"
            f"  failures={self.failures},\n"
            f"  planning_retries={self.planning_retries},\n"
            f"  execution_splits={self.execution_splits},\n"
            f"  total_ops_committed={self.total_ops_committed}\n"
            f")"
        )


@dataclass
class ExecutionResult:
    """Result of NK-2 execution."""
    
    success: bool
    terminal_error: TerminalError | None = None
    final_state_hash: Hash256 | None = None
    final_commit_hash: Hash256 | None = None
    receipt_chain: list[CommitReceipt] | None = None
    stats: ExecutionStats | None = None
```

---

## 8. Termination Guarantees

### 8.1 Progress Theorem

The main loop is guaranteed to terminate because:

1. **Planning-time failures**: Remove last-added → batch strictly shrinks
2. **Execution-time failures**: Split lexmin → width reduces, lexmin peeled
3. **Singleton failures**: Terminal → halt
4. **Resource caps**: Always terminal → halt

### 8.2 Worst Case

In worst case (all batches fail), execution converges to serialized execution:

```
P = 4: [A,B,C,D] → fail → [A] + return [B,C,D]
       [B] → fail → return [C,D]
       [C] → fail → return [D]
       [D] → commit
```

This is deterministic - no improvisation.

---

## 9. Example Usage

```python
# Setup
exec_plan = load_exec_plan(...)
initial_state = load_initial_state(...)
policy_bundle = load_policy_bundle(...)
kernel_registry = load_kernel_registry(...)
curvature_matrix = load_curvature_matrix(...)

# Execute
result = run_nk2(
    exec_plan=exec_plan,
    initial_state=initial_state,
    policy_bundle=policy_bundle,
    kernel_registry=kernel_registry,
    curvature_matrix=curvature_matrix,
)

# Check result
if result.success:
    print(f"Final state: {result.final_state_hash}")
    print(f"Final commit: {result.final_commit_hash}")
    print(f"Stats: {result.stats}")
else:
    print(f"Terminal error: {result.terminal_error}")
```

---

## 10. Summary

| Step | Description |
|------|-------------|
| 1. Validate | PolicyBundle + initial state |
| 2. Initialize | DAG + Ready + ledger |
| 3. Build Batch | Greedy.curv.v1 scheduler |
| 4. Attempt | Planning → Kernel → δ → Gate |
| 5. Success | Emit receipts, update state |
| 6. Failure | Classify → Transform → Halt/Retry |
| 7. Loop | Until Pending = ∅ |
| 8. Output | Final hashes + receipt chain |
