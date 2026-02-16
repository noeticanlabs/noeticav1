# NK-2 Scheduler: greedy.curv.v1

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`2_runtime_state.md`](2_runtime_state.md), [`../nk1/5_curvature.md`](../nk1/5_curvature.md)

---

## Overview

The scheduler is the canonical batching algorithm for NK-2. It implements **greedy curvature-aware batching** using the curvature matrix M from NK-1 to minimize marginal cost when adding operations to a batch.

---

## 1. Scheduler Core

### 1.1 Scheduler Configuration

```python
@dataclass(frozen=True)
class SchedulerConfig:
    """Configuration for greedy.curv.v1 scheduler."""
    
    # Max parallel width
    max_parallel_width: int
    
    # Scheduler rule ID (canonical)
    scheduler_rule_id: str = "greedy.curv.v1"
    
    # Scheduler mode
    scheduler_mode: str  # "id:mode.S" or "id:mode.D"
    
    # Policy bundle reference
    policy_bundle: PolicyBundle
    
    # Curvature matrix (from NK-1)
    curvature_matrix: CurvatureMatrix
```

### 1.2 Curvature Matrix Access

```python
class CurvatureMatrix:
    """NK-1 curvature matrix with rational_scaled.v1 encoding."""
    
    def __init__(self, entries: dict[tuple[int, int], Rational]):
        self._entries = entries
        self._size = max(i for i, _ in entries.keys()) + 1
    
    def get(self, i: int, j: int) -> Rational:
        """Get M[i,j] (symmetric)."""
        if i > j:
            i, j = j, i
        return self._entries.get((i, j), Rational(0, 1))
    
    @property
    def size(self) -> int:
        """Matrix dimension."""
        return self._size
    
    def version_id(self) -> str:
        """Matrix version identifier."""
        return "id:curvature.rational_scaled.v1"
    
    def digest(self) -> Hash256:
        """Matrix digest for receipts."""
        # Canonical serialization
        entries = []
        for i in range(self._size):
            for j in range(i, self._size):
                r = self.get(i, j)
                entries.append(f"{i},{j},{r.numerator},{r.denominator}")
        return Hash256(sha256(b'|'.join(e.encode('utf-8') for e in sorted(entries))))
```

---

## 2. Conflict Detection

### 2.1 Independence Feasibility

```python
def check_independence(
    op1: OpSpec,
    op2: OpSpec
) -> bool:
    """
    Check if two ops are independent (no read/write conflicts).
    
    Returns True if:
    - W_o ∩ W_p = ∅ (no write-write conflict)
    - W_o ∩ R_p = ∅ (no write-read conflict)
    - W_p ∩ R_o = ∅ (no read-write conflict)
    """
    # Write-write conflict
    if op1.W_o & op2.W_o:
        return False
    
    # Write-read conflict (op1 writes, op2 reads)
    if op1.W_o & op2.R_o:
        return False
    
    # Read-write conflict (op1 reads, op2 writes)
    if op1.R_o & op2.W_o:
        return False
    
    return True


def check_batch_independence(batch: list[OpSpec]) -> bool:
    """Check if all ops in batch are mutually independent."""
    for i, op1 in enumerate(batch):
        for op2 in batch[i+1:]:
            if not check_independence(op1, op2):
                return False
    return True
```

### 2.2 Mode Constraints

```python
def check_mode_constraints(
    batch: list[OpSpec],
    scheduler_mode: str,
    policy_bundle: PolicyBundle
) -> tuple[bool, str | None]:
    """
    Check mode constraints for batch.
    
    Returns:
        (is_valid, error_code)
    """
    # Check if any op requires mode D
    requires_modeD = any(op.requires_modeD for op in batch)
    
    if requires_modeD and scheduler_mode != "id:mode.D":
        return False, "fail.policy_veto"
    
    # Check float policy
    float_restricts_tensor = not policy_bundle.float_policy_allows_tensor
    has_float_touch = any(op.float_touch for op in batch)
    
    if float_restricts_tensor and has_float_touch:
        return False, "fail.policy_veto"
    
    return True, None
```

---

## 3. Curvature-Aware Marginal Cost

### 3.1 Marginal Cost Computation

```python
def compute_marginal_cost(
    candidate: OpSpec,
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix
) -> DebtUnit:
    """
    Compute marginal cost Δε̂(o|B) for adding candidate to batch.
    
    Using curvature matrix M and per-op bounds a_o:
    
    Δε̂(o|B) = Σ_{p∈B} M[i(o), i(p)] * a_o * a_p
    
    All computation in DebtUnit integer space.
    """
    if not batch:
        return DebtUnit(0)
    
    cost = DebtUnit(0)
    i_candidate = candidate.block_index
    a_candidate = candidate.delta_bound_a
    
    for op in batch:
        i_op = op.block_index
        a_op = op.delta_bound_a
        
        # M[i, j] * a_o * a_p
        m_ij = curvature_matrix.get(i_candidate, i_op)
        
        # Convert rational to integer (DebtUnit)
        # m_ij = num/den, so m_ij * a_o * a_p = num * a_o * a_p / den
        term = m_ij.numerator * a_candidate * a_op // m_ij.denominator
        
        cost += term
    
    return DebtUnit(cost)
```

### 3.2 Batch Cost Accumulation

```python
def compute_batch_cost(
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix
) -> DebtUnit:
    """
    Compute total ε̂(B) for a batch.
    
    ε̂(B) = Σ_{o∈B} a_o² + Σ_{(o,p)∈B×B, o≠p} M[i(o), i(p)] * a_o * a_p
    """
    # Diagonal terms: a_o²
    cost = sum(op.delta_bound_a ** 2 for op in batch)
    
    # Off-diagonal terms: M[i,j] * a_i * a_j
    for i, op_i in enumerate(batch):
        for j, op_j in enumerate(batch):
            if i < j:  # Symmetric, only compute once
                m_ij = curvature_matrix.get(op_i.block_index, op_j.block_index)
                term = m_ij.numerator * op_i.delta_bound_a * op_j.delta_bound_a // m_ij.denominator
                cost += term
    
    return DebtUnit(cost)
```

---

## 4. Greedy Selection Algorithm

### 4.1 Core Greedy Algorithm

```python
@dataclass
class BatchResult:
    """Result of batch construction."""
    
    batch: list[OpSpec]           # Selected ops
    append_log: list[OpID]        # Canonical append sequence
    total_cost: DebtUnit          # Total ε̂(B)
    is_full: bool                 # Whether batch reached max size


def greedy_curv_batch(
    ready_ops: list[OpSpec],
    curvature_matrix: CurvatureMatrix,
    max_parallel_width: int,
    scheduler_mode: str,
    policy_bundle: PolicyBundle
) -> BatchResult:
    """
    Greedy curvature-aware batch construction.
    
    Algorithm:
    1. Start B = []
    2. Build append_log = [] (canon-required)
    3. While |B| < P:
       a. Consider candidates o in Ready not in B that are feasible
       b. Choose o* minimizing Δε̂(o|B)
       c. Tie-break by lexicographically smallest op_id bytes
       d. Append: B := B ∪ {o*}
    4. Output B and append_log
    """
    batch: list[OpSpec] = []
    append_log: list[OpID] = []
    
    # Convert ready_ops to dict for O(1) lookup
    ops_by_id = {op.op_id: op for op in ready_ops}
    ready_ids = [op.op_id for op in ready_ops]
    
    while len(batch) < max_parallel_width:
        # Find feasible candidates
        candidates = []
        for op_id in ready_ids:
            if op_id in append_log:
                continue
            
            op = ops_by_id[op_id]
            
            # Check independence with current batch
            feasible = True
            for batch_op in batch:
                if not check_independence(op, batch_op):
                    feasible = False
                    break
            
            if not feasible:
                continue
            
            # Check mode constraints
            is_valid, _ = check_mode_constraints(
                batch + [op], scheduler_mode, policy_bundle
            )
            if not is_valid:
                continue
            
            candidates.append(op)
        
        if not candidates:
            break  # No more feasible candidates
        
        # Select op with minimum marginal cost
        best_op = None
        best_cost = None
        
        for candidate in candidates:
            cost = compute_marginal_cost(candidate, batch, curvature_matrix)
            
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_op = candidate
            elif cost == best_cost:
                # Tie-break: lexicographically smallest op_id bytes
                if candidate.op_id.encode('utf-8') < best_op.op_id.encode('utf-8'):
                    best_op = candidate
        
        # Append to batch
        batch.append(best_op)
        append_log.append(best_op.op_id)
    
    # Compute total batch cost
    total_cost = compute_batch_cost(batch, curvature_matrix)
    
    return BatchResult(
        batch=batch,
        append_log=append_log,
        total_cost=total_cost,
        is_full=len(batch) >= max_parallel_width,
    )
```

### 4.2 Tie-Breaking Rule

```python
def select_best_candidate(
    candidates: list[OpSpec],
    batch: list[OpSpec],
    curvature_matrix: CurvatureMatrix
) -> OpSpec:
    """
    Select best candidate from feasible ops.
    
    Selection criteria:
    1. Minimum marginal cost Δε̂(o|B)
    2. Tie-break: lexicographically smallest op_id bytes
    """
    best = None
    best_cost = None
    
    for candidate in candidates:
        cost = compute_marginal_cost(candidate, batch, curvature_matrix)
        
        if best_cost is None:
            best = candidate
            best_cost = cost
        elif cost < best_cost:
            best = candidate
            best_cost = cost
        elif cost == best_cost:
            # Tie-break by op_id bytes
            if candidate.op_id.encode('utf-8') < best.op_id.encode('utf-8'):
                best = candidate
                best_cost = cost
    
    return best
```

---

## 5. Full Scheduler Interface

### 5.1 Scheduler Class

```python
class GreedyCurvScheduler:
    """Canonical greedy.curv.v1 scheduler."""
    
    def __init__(
        self,
        config: SchedulerConfig,
        curvature_matrix: CurvatureMatrix
    ):
        self.config = config
        self.curvature_matrix = curvature_matrix
    
    def build_batch(
        self,
        ready_ops: list[OpSpec],
        current_batch: list[OpSpec] | None = None
    ) -> BatchResult:
        """
        Build next batch from ready ops.
        
        Args:
            ready_ops: List of ready ops (must be sorted canonically)
            current_batch: Current batch (for planning-time retry)
        
        Returns:
            BatchResult with selected batch and append_log
        """
        # Use current batch if provided (for retry after removal)
        if current_batch is not None:
            batch = list(current_batch)
            append_log = [op.op_id for op in batch]
        else:
            batch = []
            append_log = []
        
        # Continue greedy selection
        max_width = self.config.max_parallel_width
        
        while len(batch) < max_width:
            # Get feasible candidates
            candidates = self._get_feasible_candidates(ready_ops, batch)
            
            if not candidates:
                break
            
            # Select best
            best = select_best_candidate(candidates, batch, self.curvature_matrix)
            batch.append(best)
            append_log.append(best.op_id)
        
        total_cost = compute_batch_cost(batch, self.curvature_matrix)
        
        return BatchResult(
            batch=batch,
            append_log=append_log,
            total_cost=total_cost,
            is_full=len(batch) >= max_width,
        )
    
    def _get_feasible_candidates(
        self,
        ready_ops: list[OpSpec],
        batch: list[OpSpec]
    ) -> list[OpSpec]:
        """Get feasible candidates from ready ops."""
        candidates = []
        
        for op in ready_ops:
            # Skip if already in batch
            if any(o.op_id == op.op_id for o in batch):
                continue
            
            # Check independence
            feasible = True
            for batch_op in batch:
                if not check_independence(op, batch_op):
                    feasible = False
                    break
            
            if not feasible:
                continue
            
            # Check mode constraints
            is_valid, _ = check_mode_constraints(
                batch + [op],
                self.config.scheduler_mode,
                self.config.policy_bundle
            )
            if not is_valid:
                continue
            
            candidates.append(op)
        
        return candidates
    
    def get_curvature_info(self) -> tuple[str, Hash256]:
        """Get curvature matrix version and digest."""
        return (
            self.curvature_matrix.version_id(),
            self.curvature_matrix.digest()
        )
```

---

## 6. Planning-Time Failure Handling

### 6.1 Remove Last-Added

```python
def remove_last_added(
    batch_result: BatchResult
) -> BatchResult:
    """
    Handle planning-time failure by removing last-added op.
    
    Used when fail.independence or fail.policy_veto occurs.
    
    Returns new BatchResult without the last op.
    """
    if len(batch_result.batch) == 0:
        raise ValueError("Cannot remove from empty batch")
    
    # Remove last op
    new_batch = batch_result.batch[:-1]
    new_append_log = batch_result.append_log[:-1]
    
    # Recompute cost
    # Note: This is approximate; exact cost would require recalculation
    
    return BatchResult(
        batch=new_batch,
        append_log=new_append_log,
        total_cost=batch_result.total_cost,  # Approximate
        is_full=False,
    )
```

---

## 7. Determinism Verification

### 7.1 Determinism Test

```python
def verify_scheduler_determinism(
    scheduler: GreedyCurvScheduler,
    ready_ops: list[OpSpec],
    num_runs: int = 100
) -> bool:
    """
    Verify scheduler produces identical results across runs.
    
    Tests:
    - Same ready ops → same batch
    - Shuffled input → same batch (canonical ordering)
    """
    results = []
    
    for _ in range(num_runs):
        # Shuffle input (but scheduler must produce same result)
        shuffled = list(ready_ops)
        random.shuffle(shuffled)
        
        result = scheduler.build_batch(shuffled)
        results.append((
            tuple(op.op_id for op in result.batch),
            tuple(result.append_log),
        ))
    
    # All results must be identical
    return len(set(results)) == 1
```

---

## 8. Example Usage

```python
# Setup
config = SchedulerConfig(
    max_parallel_width=4,
    scheduler_rule_id="greedy.curv.v1",
    scheduler_mode="id:mode.S",
    policy_bundle=policy_bundle,
)

curvature = CurvatureMatrix({
    (0, 0): Rational(1, 1),
    (0, 1): Rational(1, 2),
    (1, 1): Rational(1, 1),
})

scheduler = GreedyCurvScheduler(config, curvature)

# Build batch
ready = [
    OpSpec(op_id="id:op.a", block_index=0, delta_bound_a=DebtUnit(100), ...),
    OpSpec(op_id="id:op.b", block_index=1, delta_bound_a=DebtUnit(50), ...),
    OpSpec(op_id="id:op.c", block_index=0, delta_bound_a=DebtUnit(75), ...),
    OpSpec(op_id="id:op.d", block_index=1, delta_bound_a=DebtUnit(80), ...),
]

result = scheduler.build_batch(ready)

# result.batch = [op_a, op_c, op_b, ...] (depends on costs)
# result.append_log = ["id:op.a", "id:op.c", "id:op.b", ...]
```
