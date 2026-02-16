# NK-2 Runtime State + Dependency Bookkeeping

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_exec_plan.md`](1_exec_plan.md)

---

## Overview

This document defines the core runtime state that NK-2 maintains during execution. The runtime state is designed for immutability (each state is hashable) and deterministic progression through the DAG.

---

## 1. Runtime State Structure

### 1.1 Core State Components

```python
@dataclass(frozen=True)
class RuntimeState:
    """Immutable runtime state for NK-2 execution."""
    
    # State (immutable, hashable from NK-1)
    x: State                           # Current state (hashable)
    
    # Ledger anchor (commit chain)
    ledger_prev_hash: Hash256         # Previous commit hash
    
    # Execution tracking
    committed: frozenset[OpID]        # Successfully committed ops
    pending: frozenset[OpID]          # Not yet committed
    
    def hash(self) -> Hash256:
        """Hash of runtime state for deterministic commit."""
        return Hash256(sha256(self.canonical_bytes()))
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation."""
        return b'||'.join([
            self.x.hash().bytes,
            self.ledger_prev_hash,
            b'committed:' + b','.join(sorted(op.encode('utf-8') for op in self.committed)),
            b'pending:' + b','.join(sorted(op.encode('utf-8') for op in self.pending)),
        ])
```

### 1.2 State Properties

| Component | Type | Description |
|-----------|------|-------------|
| `x` | State | Current state (immutable, hashable) |
| `ledger_prev_hash` | Hash256 | Commit-chain anchor |
| `committed` | set[OpID] | Successfully committed operations |
| `pending` | set[OpID] | Not yet committed |

### 1.3 Invariants

```
1. committed ∪ pending = all_ops (partition)
2. committed ∩ pending = ∅
3. ledger_prev_hash is hash of previous commit (or genesis)
```

---

## 2. Dependency Bookkeeping

### 2.1 In-Degree Tracking

```python
class DependencyTracker:
    """Tracks DAG dependencies for Ready set computation."""
    
    def __init__(self, ops: list[OpSpec], dag_edges: list[tuple[OpID, OpID]]):
        # Build in-degree map
        self._in_degree: dict[OpID, int] = {op.op_id: 0 for op in ops}
        self._successors: dict[OpID, list[OpID]] = {op.op_id: [] for op in ops}
        
        # Process edges (a, b) means a ≺ b (a before b)
        for predecessor, successor in dag_edges:
            self._in_degree[successor] += 1
            self._successors[predecessor].append(successor)
        
        # Immutable snapshot
        self._initial_in_degree = dict(self._in_degree)
    
    def get_in_degree(self, op_id: OpID) -> int:
        """Get current in-degree of an operation."""
        return self._in_degree.get(op_id, 0)
    
    def is_ready(self, op_id: OpID, committed: frozenset[OpID]) -> bool:
        """Check if op is ready (in_degree 0 and not committed)."""
        return self._in_degree.get(op_id, 0) == 0 and op_id not in committed
    
    def mark_committed(self, op_id: OpID) -> None:
        """Mark op as committed and update successors."""
        if op_id not in self._in_degree:
            return
        
        for successor in self._successors.get(op_id, []):
            self._in_degree[successor] -= 1
    
    def get_ready_set(self, committed: frozenset[OpID]) -> list[OpID]:
        """Get sorted list of ready operations (canonical ordering)."""
        ready = [
            op_id for op_id, degree in self._in_degree.items()
            if degree == 0 and op_id not in committed
        ]
        # Canonical ordering: sort by op_id bytes
        return sorted(ready, key=lambda op: op.encode('utf-8'))
    
    def reset(self) -> None:
        """Reset to initial state (for testing)."""
        self._in_degree = dict(self._initial_in_degree)
```

### 2.2 Ready Set Computation

```python
def compute_ready(
    ops: list[OpSpec],
    dag_edges: list[tuple[OpID, OpID]],
    committed: frozenset[OpID]
) -> list[OpID]:
    """
    Compute the Ready set from DAG + committed ops.
    
    Returns sorted list (canonical ordering) of ops where:
    - in_degree = 0
    - not in committed
    
    Determinism pin: all sets become sorted lists by op_id bytes.
    """
    tracker = DependencyTracker(ops, dag_edges)
    return tracker.get_ready_set(committed)
```

---

## 3. Ledger Anchor

### 3.1 Commit Chain

The ledger anchor connects each batch commit to the previous commit, forming a hash chain:

```
genesis_hash → commit_1 → commit_2 → ... → commit_n
```

```python
class LedgerAnchor:
    """Manages commit chain anchor."""
    
    def __init__(self, genesis_hash: Hash256):
        self._current_hash = genesis_hash
    
    @property
    def prev_hash(self) -> Hash256:
        """Get current anchor hash."""
        return self._current_hash
    
    def advance(self, commit_hash: Hash256) -> None:
        """Advance to next commit (immutable update)."""
        self._current_hash = commit_hash
    
    def reset(self, genesis_hash: Hash256) -> None:
        """Reset to genesis (for testing)."""
        self._current_hash = genesis_hash
```

### 3.2 Genesis Hash

```python
def compute_genesis_hash(exec_plan: ExecPlan) -> Hash256:
    """Compute genesis hash for a given ExecPlan."""
    return Hash256(sha256(
        exec_plan.plan_id.encode('utf-8') +
        exec_plan.initial_state_hash.bytes +
        b'genesis'
    ))
```

---

## 4. Batch Construction Context

### 4.1 Batch Context

```python
@dataclass
class BatchContext:
    """Context for batch construction and execution."""
    
    # Execution plan
    exec_plan: ExecPlan
    
    # Runtime state
    state: RuntimeState
    
    # Dependency tracking
    tracker: DependencyTracker
    
    # Current ready set (canonical ordering)
    ready: list[OpID]
    
    # Append log (for determinism)
    append_log: list[OpID]
    
    def get_op_spec(self, op_id: OpID) -> OpSpec:
        """Get OpSpec by ID."""
        for op in self.exec_plan.ops:
            if op.op_id == op_id:
                return op
        raise ValueError(f"Unknown op_id: {op_id}")
    
    def get_ready_ops_not_in_batch(self, batch: list[OpID]) -> list[OpID]:
        """Get ready ops not already in batch (canonical ordering)."""
        batch_set = frozenset(batch)
        return [op for op in self.ready if op not in batch_set]
```

---

## 5. State Transitions

### 5.1 Commit Transition

```python
def commit_batch(
    state: RuntimeState,
    batch: list[OpID],
    batch_context: BatchContext,
    commit_receipt: 'CommitReceipt'
) -> RuntimeState:
    """
    Create new runtime state after successful batch commit.
    
    Args:
        state: Current runtime state
        batch: Committed batch (sorted)
        batch_context: Execution context
        commit_receipt: Commit receipt
    
    Returns:
        New runtime state with updated committed set
    """
    # Update committed set
    new_committed = state.committed | frozenset(batch)
    
    # Update pending set
    new_pending = state.pending - frozenset(batch)
    
    # Create new state
    return RuntimeState(
        x=batch_context.state.x,  # Updated state
        ledger_prev_hash=commit_receipt.hash(),
        committed=new_committed,
        pending=new_pending,
    )
```

### 5.2 Rescheduling Transition

```python
def reschedule_ops(
    batch: list[OpID],
    returned_ops: list[OpID],
    tracker: DependencyTracker,
    committed: frozenset[OpID]
) -> list[OpID]:
    """
    Return ops to Ready set after failed batch.
    
    Args:
        batch: Failed batch
        returned_ops: Ops to return to Ready
        tracker: Dependency tracker
        committed: Currently committed ops
    
    Returns:
        New ready set (canonical ordering)
    """
    # Reset in-degrees for returned ops
    for op_id in batch:
        tracker._in_degree[op_id] = 0
    
    return tracker.get_ready_set(committed)
```

---

## 6. Determinism Guarantees

### 6.1 Canonical Ordering Rules

1. **Ready set**: Sorted by op_id bytes ascending
2. **Batch order**: Append sequence (append_log) is canonical
3. **Edge processing**: Sorted by (predecessor, successor) bytes
4. **Patch order**: Sorted by op_id bytes for state updates

### 6.2 Determinism Theorem

```
Given:
  - Same ExecPlan
  - Same initial state
  
Then:
  - Same Ready set sequence at each step
  - Same batch append sequence
  - Same commit chain hashes
  - Same final state hash
```

### 6.3 Verification

```python
def verify_determinism(
    plan: ExecPlan,
    initial_state: State,
    num_runs: int = 10
) -> bool:
    """
    Verify deterministic execution across multiple runs.
    
    Returns True if all runs produce identical results.
    """
    results = []
    
    for _ in range(num_runs):
        # Execute (would need full runtime)
        result = execute_plan(plan, initial_state)
        results.append(result.final_state_hash)
    
    # All hashes must be identical
    return len(set(results)) == 1
```

---

## 7. Example Usage

```python
# Initialize
initial_state = State(...)
genesis_hash = compute_genesis_hash(exec_plan)

# Create runtime state
state = RuntimeState(
    x=initial_state,
    ledger_prev_hash=genesis_hash,
    committed=frozenset(),
    pending=frozenset(op.op_id for op in exec_plan.ops),
)

# Create dependency tracker
tracker = DependencyTracker(exec_plan.ops, exec_plan.dag_edges)

# Get initial ready set
ready = tracker.get_ready_set(state.committed)
# ready = ["id:op.a.001", "id:op.b.001", ...] (sorted)

# After committing batch
tracker.mark_committed("id:op.a.001")
new_ready = tracker.get_ready_set(state.committed | {"id:op.a.001"})
```
