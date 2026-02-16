# NK-2 Reference Implementation

**Version:** 1.0  
**Status:** Reference  
**Related:** [`0_overview.md`](0_overview.md), [`1_exec_plan.md`](1_exec_plan.md), [`2_runtime_state.md`](2_runtime_state.md), [`3_scheduler.md`](3_scheduler.md)

---

## Overview

This document provides a reference implementation of NK-2 in Python. The implementation is intended to be a reference for implementers and is not optimized for production use.

---

## 1. Core Data Structures

### 1.1 Type Definitions

```python
# type_defs.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import hashlib
import math


# Type aliases
OpID = str
PolicyID = str
FieldID = str
Hash256 = bytes
DebtUnit = int


class SchedulerMode(Enum):
    """Scheduler mode identifiers."""
    SINGLE = "id:mode.S"
    DOUBLE = "id:mode.D"


class SchedulerRule(Enum):
    """Scheduler rule identifiers."""
    GREEDY_CURV_V1 = "greedy.curv.v1"


class FailureCode(Enum):
    """Failure classification codes."""
    # Planning-time
    INDEPENDENCE = "fail.independence"
    POLICY_VETO = "fail.policy_veto"
    
    # Execution-time
    KERNEL_ERROR = "fail.kernel_error"
    DELTA_BOUND = "fail.delta_bound"
    GATE_EPS = "fail.gate_eps"
    
    # Terminal (singleton)
    KERNEL_ERROR_SINGLETON = "err.kernel_error.singleton"
    DELTA_BOUND_SINGLETON = "err.delta_bound.singleton"
    POLICY_VETO_SINGLETON = "err.policy_veto.singleton"


class ResourceErrorCode(Enum):
    """Resource cap error codes."""
    BIGINT_BITS_EXCEEDED = "err.cap.bigint_bits_exceeded"
    MATRIX_TERMS_EXCEEDED = "err.cap.matrix_terms_exceeded"
    FIELDS_TOUCHED_EXCEEDED = "err.cap.fields_touched_exceeded"
    V_EVAL_COST_EXCEEDED = "err.cap.v_eval_cost_exceeded"
    EPSILON_EXCEEDED = "err.cap.epsilon_exceeded"


def sha256(data: bytes) -> bytes:
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()
```

### 1.2 ExecPlan and OpSpec

```python
# exec_plan.py

from type_defs import *

@dataclass(frozen=True)
class ResourceCaps:
    """Policy-locked resource limits."""
    max_bigint_bits: int = 4096
    max_matrix_accum_terms: int = 10000
    max_fields_touched_per_op: int = 100
    max_v_eval_cost: int = 1000000
    max_batch_size_p: Optional[int] = None
    max_epsilon: Optional[DebtUnit] = None
    
    def canonical_bytes(self) -> bytes:
        return b'||'.join([
            f"max_bigint_bits:{self.max_bigint_bits}".encode(),
            f"max_matrix_accum_terms:{self.max_matrix_accum_terms}".encode(),
            f"max_fields_touched_per_op:{self.max_fields_touched_per_op}".encode(),
            f"max_v_eval_cost:{self.max_v_eval_cost}".encode(),
            f"max_batch_size_p:{self.max_batch_size_p or 'unlimited'}".encode(),
        ])


@dataclass(frozen=True)
class OpSpec:
    """Per-operation specification."""
    op_id: OpID
    kernel_hash: Hash256
    footprint_digest: Hash256
    R_o: frozenset[FieldID]
    W_o: frozenset[FieldID]
    block_index: int
    delta_bound_a: DebtUnit
    requires_modeD: bool
    float_touch: bool
    glb_mode_id: str
    
    def canonical_bytes(self) -> bytes:
        return b'||'.join([
            self.op_id.encode('utf-8'),
            self.kernel_hash,
            self.footprint_digest,
            b','.join(sorted(f.encode('utf-8') for f in self.R_o)),
            b','.join(sorted(f.encode('utf-8') for f in self.W_o)),
            str(self.block_index).encode('utf-8'),
            str(self.delta_bound_a).encode('utf-8'),
            str(self.requires_modeD).encode('utf-8'),
            str(self.float_touch).encode('utf-8'),
            self.glb_mode_id.encode('utf-8'),
        ])


@dataclass(frozen=True)
class ExecPlan:
    """Deterministic job spec for NK-2."""
    plan_id: OpID
    policy_bundle_id: PolicyID
    policy_digest: Hash256
    initial_state_hash: Hash256
    ops: tuple[OpSpec, ...]
    dag_edges: tuple[tuple[OpID, OpID], ...]
    max_parallel_width_P: int
    scheduler_rule_id: str
    scheduler_mode: str
    resource_caps: ResourceCaps
    abort_on_kernel_error: bool = True
    
    def canonical_bytes(self) -> bytes:
        parts = [
            self.plan_id.encode('utf-8'),
            self.policy_bundle_id.encode('utf-8'),
            self.policy_digest,
            self.initial_state_hash,
            b''.join(op.canonical_bytes() for op in sorted(self.ops, key=lambda o: o.op_id)),
            b''.join(a.encode('utf-8') + b.encode('utf-8') for a, b in sorted(self.dag_edges)),
            str(self.max_parallel_width_P).encode('utf-8'),
            self.scheduler_rule_id.encode('utf-8'),
            self.scheduler_mode.encode('utf-8'),
            self.resource_caps.canonical_bytes(),
        ]
        return b'||'.join(parts)
    
    def hash(self) -> Hash256:
        return sha256(self.canonical_bytes())
```

---

## 2. Runtime State

### 2.1 State and Dependencies

```python
# runtime_state.py

from type_defs import *
from exec_plan import *


@dataclass(frozen=True)
class RuntimeState:
    """Immutable runtime state."""
    x: 'State'  # Forward reference
    ledger_prev_hash: Hash256
    committed: frozenset[OpID]
    pending: frozenset[OpID]


class DependencyTracker:
    """Tracks DAG dependencies."""
    
    def __init__(self, ops: list[OpSpec], dag_edges: list[tuple[OpID, OpID]]):
        self._in_degree: dict[OpID, int] = {op.op_id: 0 for op in ops}
        self._successors: dict[OpID, list[OpID]] = {op.op_id: [] for op in ops}
        
        for predecessor, successor in dag_edges:
            self._in_degree[successor] = self._in_degree.get(successor, 0) + 1
            self._successors[predecessor].append(successor)
        
        self._initial_in_degree = dict(self._in_degree)
    
    def get_in_degree(self, op_id: OpID) -> int:
        return self._in_degree.get(op_id, 0)
    
    def mark_committed(self, op_id: OpID) -> None:
        for successor in self._successors.get(op_id, []):
            self._in_degree[successor] -= 1
    
    def get_ready_set(self, committed: frozenset[OpID]) -> list[OpID]:
        ready = [
            op_id for op_id, degree in self._in_degree.items()
            if degree == 0 and op_id not in committed
        ]
        return sorted(ready, key=lambda op: op.encode('utf-8'))
    
    def reset_op_degree(self, op_id: OpID) -> None:
        """Reset in-degree for returned op."""
        self._in_degree[op_id] = 0
```

---

## 3. Scheduler

### 3.1 Curvature and Scheduling

```python
# scheduler.py

from type_defs import *
from exec_plan import *


class Rational:
    """Rational number for curvature entries."""
    
    def __init__(self, numerator: int, denominator: int = 1):
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        # Reduce
        g = math.gcd(abs(numerator), denominator)
        self.numerator = numerator // g
        self.denominator = denominator // g
    
    def __repr__(self):
        return f"Rational({self.numerator}, {self.denominator})"


class CurvatureMatrix:
    """Curvature matrix with rational_scaled.v1 encoding."""
    
    def __init__(self, entries: dict[tuple[int, int], Rational]):
        self._entries = entries
        self._size = max(max(i, j) for i, j in entries.keys()) + 1
    
    def get(self, i: int, j: int) -> Rational:
        if i > j:
            i, j = j, i
        return self._entries.get((i, j), Rational(0, 1))
    
    def digest(self) -> Hash256:
        entries = []
        for i in range(self._size):
            for j in range(i, self._size):
                r = self.get(i, j)
                entries.append(f"{i},{j},{r.numerator},{r.denominator}")
        return sha256(b'|'.join(e.encode('utf-8') for e in sorted(entries)))


@dataclass
class BatchResult:
    batch: list[OpSpec]
    append_log: list[OpID]
    total_cost: DebtUnit
    is_full: bool


def check_independence(op1: OpSpec, op2: OpSpec) -> bool:
    """Check if two ops are independent."""
    if op1.W_o & op2.W_o:
        return False
    if op1.W_o & op2.R_o:
        return False
    if op1.R_o & op2.W_o:
        return False
    return True


def compute_marginal_cost(
    candidate: OpSpec,
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix
) -> DebtUnit:
    """Compute Δε̂(o|B) for adding candidate to batch."""
    if not batch:
        return DebtUnit(0)
    
    cost = DebtUnit(0)
    i_candidate = candidate.block_index
    a_candidate = candidate.delta_bound_a
    
    for op in batch:
        m_ij = curvature_matrix.get(i_candidate, op.block_index)
        term = m_ij.numerator * a_candidate * op.delta_bound_a // m_ij.denominator
        cost += term
    
    return DebtUnit(cost)


def compute_batch_cost(
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix
) -> DebtUnit:
    """Compute total ε̂(B) for a batch."""
    cost = sum(op.delta_bound_a ** 2 for op in batch)
    
    for i, op_i in enumerate(batch):
        for j, op_j in enumerate(batch):
            if i < j:
                m_ij = curvature_matrix.get(op_i.block_index, op_j.block_index)
                term = m_ij.numerator * op_i.delta_bound_a * op_j.delta_bound_a // m_ij.denominator
                cost += term
    
    return DebtUnit(cost)


class GreedyCurvScheduler:
    """Greedy curvature-aware scheduler."""
    
    def __init__(
        self,
        max_parallel_width: int,
        scheduler_rule_id: str,
        scheduler_mode: str,
        curvature_matrix: CurvatureMatrix,
    ):
        self.max_parallel_width = max_parallel_width
        self.scheduler_rule_id = scheduler_rule_id
        self.scheduler_mode = scheduler_mode
        self.curvature_matrix = curvature_matrix
    
    def build_batch(self, ready_ops: list[OpSpec]) -> BatchResult:
        batch: list[OpSpec] = []
        append_log: list[OpID] = []
        
        ops_by_id = {op.op_id: op for op in ready_ops}
        
        while len(batch) < self.max_parallel_width:
            candidates = []
            for op in ready_ops:
                if op.op_id in append_log:
                    continue
                
                # Check independence
                feasible = all(check_independence(op, b) for b in batch)
                if not feasible:
                    continue
                
                candidates.append(op)
            
            if not candidates:
                break
            
            # Select best candidate
            best = None
            best_cost = None
            for candidate in candidates:
                cost = compute_marginal_cost(candidate, batch, self.curvature_matrix)
                
                if best_cost is None or cost < best_cost:
                    best = candidate
                    best_cost = cost
                elif cost == best_cost:
                    if candidate.op_id.encode('utf-8') < best.op_id.encode('utf-8'):
                        best = candidate
            
            if best:
                batch.append(best)
                append_log.append(best.op_id)
        
        total_cost = compute_batch_cost(batch, self.curvature_matrix)
        
        return BatchResult(
            batch=batch,
            append_log=append_log,
            total_cost=total_cost,
            is_full=len(batch) >= self.max_parallel_width,
        )
```

---

## 4. Main Loop

### 4.1 Runtime Execution

```python
# main.py

from type_defs import *
from exec_plan import *
from runtime_state import *
from scheduler import *


class State:
    """Simple state representation."""
    
    def __init__(self, fields: dict[FieldID, DebtUnit]):
        self.fields = fields
    
    def hash(self) -> Hash256:
        items = sorted(self.fields.items())
        data = b'&'.join(f"{k}={v}".encode('utf-8') for k, v in items)
        return sha256(data)
    
    def get_field(self, field_id: FieldID) -> DebtUnit:
        return self.fields.get(field_id, DebtUnit(0))
    
    def patch(self, writes: dict[FieldID, DebtUnit]) -> 'State':
        new_fields = dict(self.fields)
        new_fields.update(writes)
        return State(new_fields)


@dataclass
class ExecutionStats:
    batches_built: int = 0
    attempts: int = 0
    commits: int = 0
    failures: int = 0


@dataclass
class ExecutionResult:
    success: bool
    final_state_hash: Optional[Hash256] = None
    final_commit_hash: Optional[Hash256] = None
    stats: Optional[ExecutionStats] = None
    error: Optional[str] = None


class NK2Runtime:
    """NK-2 Runtime Executor."""
    
    def __init__(
        self,
        exec_plan: ExecPlan,
        initial_state: State,
        curvature_matrix: CurvatureMatrix,
    ):
        self.exec_plan = exec_plan
        self.initial_state = initial_state
        self.curvature_matrix = curvature_matrix
        
        # Compute genesis hash
        self.genesis_hash = sha256(
            exec_plan.plan_id.encode('utf-8') +
            exec_plan.initial_state_hash +
            b'genesis'
        )
        
        # Initialize runtime state
        self.state = RuntimeState(
            x=initial_state,
            ledger_prev_hash=self.genesis_hash,
            committed=frozenset(),
            pending=frozenset(op.op_id for op in exec_plan.ops),
        )
        
        # Initialize dependency tracker
        self.tracker = DependencyTracker(
            list(exec_plan.ops),
            list(exec_plan.dag_edges),
        )
        
        # Initialize scheduler
        self.scheduler = GreedyCurvScheduler(
            max_parallel_width=exec_plan.max_parallel_width_P,
            scheduler_rule_id=exec_plan.scheduler_rule_id,
            scheduler_mode=exec_plan.scheduler_mode,
            curvature_matrix=curvature_matrix,
        )
        
        self.stats = ExecutionStats()
    
    def run(self) -> ExecutionResult:
        """Execute the main loop."""
        
        while self.state.pending:
            # Build batch
            ready = self.tracker.get_ready_set(self.state.committed)
            ready_ops = [op for op in self.exec_plan.ops if op.op_id in ready]
            
            if not ready_ops:
                break
            
            batch_result = self.scheduler.build_batch(ready_ops)
            self.stats.batches_built += 1
            
            if not batch_result.batch:
                break
            
            # Simulate successful commit (simplified)
            self.stats.attempts += 1
            
            # Update state
            self.state = RuntimeState(
                x=self.state.x,  # Would update with patched state
                ledger_prev_hash=sha256(self.state.ledger_prev_hash + b'commit'),
                committed=self.state.committed | frozenset(op.op_id for op in batch_result.batch),
                pending=self.state.pending - frozenset(op.op_id for op in batch_result.batch),
            )
            
            # Update tracker
            for op in batch_result.batch:
                self.tracker.mark_committed(op.op_id)
            
            self.stats.commits += 1
        
        return ExecutionResult(
            success=True,
            final_state_hash=self.state.x.hash(),
            final_commit_hash=self.state.ledger_prev_hash,
            stats=self.stats,
        )
```

---

## 5. Usage Example

```python
# example.py

from exec_plan import *
from scheduler import *
from main import *


def main():
    # Create sample ops
    ops = (
        OpSpec(
            op_id="id:op.a.001",
            kernel_hash=sha256(b"kernel_a"),
            footprint_digest=sha256(b"footprint_a"),
            R_o=frozenset({"id:field.balance"}),
            W_o=frozenset({"id:field.balance"}),
            block_index=0,
            delta_bound_a=DebtUnit(100),
            requires_modeD=False,
            float_touch=False,
            glb_mode_id="id:kernel_type_erasure.v1",
        ),
        OpSpec(
            op_id="id:op.b.001",
            kernel_hash=sha256(b"kernel_b"),
            footprint_digest=sha256(b"footprint_b"),
            R_o=frozenset({"id:field.balance"}),
            W_o=frozenset({"id:field.status"}),
            block_index=1,
            delta_bound_a=DebtUnit(50),
            requires_modeD=False,
            float_touch=False,
            glb_mode_id="id:kernel_type_erasure.v1",
        ),
    )
    
    # Create DAG edges
    dag_edges = (("id:op.a.001", "id:op.b.001"),)
    
    # Create curvature matrix
    curvature_matrix = CurvatureMatrix({
        (0, 0): Rational(1, 1),
        (0, 1): Rational(1, 2),
        (1, 1): Rational(1, 1),
    })
    
    # Create initial state
    initial_state = State({"id:field.balance": DebtUnit(1000)})
    initial_state_hash = initial_state.hash()
    
    # Create ExecPlan
    exec_plan = ExecPlan(
        plan_id="id:plan.example.001",
        policy_bundle_id="id:policy.standard.v1",
        policy_digest=sha256(b"policy"),
        initial_state_hash=initial_state_hash,
        ops=ops,
        dag_edges=dag_edges,
        max_parallel_width_P=4,
        scheduler_rule_id="greedy.curv.v1",
        scheduler_mode="id:mode.S",
        resource_caps=ResourceCaps(),
        abort_on_kernel_error=True,
    )
    
    # Run
    runtime = NK2Runtime(
        exec_plan=exec_plan,
        initial_state=initial_state,
        curvature_matrix=curvature_matrix,
    )
    
    result = runtime.run()
    
    print(f"Success: {result.success}")
    print(f"Final state: {result.final_state_hash.hex()}")
    print(f"Final commit: {result.final_commit_hash.hex()}")
    print(f"Stats: {result.stats}")


if __name__ == "__main__":
    main()
```

---

## 6. Implementation Notes

### 6.1 Design Decisions

1. **Immutable data structures**: Use frozen dataclasses for ExecPlan, OpSpec, RuntimeState
2. **Canonical ordering**: All lists sorted by op_id bytes for determinism
3. **Separation of concerns**: Scheduler, executor, and state management are separate
4. **Forward references**: Use string annotations for circular dependencies

### 6.2 Testing

Run the conformance tests in `9_conformance.md` to verify the implementation.

### 6.3 Performance Considerations

This is a reference implementation. Production implementations should consider:
- Object pooling for reduce GC pressure
- Lazy evaluation of curvature matrix
- Parallel kernel execution where appropriate
- Caching of intermediate results
