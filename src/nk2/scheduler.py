# NK-2 Scheduler: Greedy.curv.v1 per docs/nk2/3_scheduler.md

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from .exec_plan import ExecPlan, OpSpec, OpStatus


class SchedulerMode(Enum):
    """Scheduler modes."""
    GREEDY_CURV_V1 = "greedy.curv.v1"
    PRIORITY = "priority"
    FIFO = "fifo"


@dataclass
class AppendLog:
    """
    Append log per docs/nk2/3_scheduler.md.
    
    Maintains canonical append order during batch construction.
    last-added op is defined from append_log for replay stability.
    """
    entries: List[str] = field(default_factory=list)  # List of op_ids in order
    
    def append(self, op_id: str) -> None:
        """Append an operation to the log."""
        self.entries.append(op_id)
    
    def get_last(self) -> Optional[str]:
        """Get last added operation."""
        return self.entries[-1] if self.entries else None
    
    def get_order(self) -> List[str]:
        """Get the full append order."""
        return list(self.entries)
    
    def compute_digest(self) -> str:
        """Compute digest of append order for receipts."""
        if not self.entries:
            return 'h:' + '0' * 64
        
        data = b'append_log_v1:'
        for op_id in self.entries:
            data += op_id.encode('utf-8') + b';'
        
        return 'h:' + hashlib.sha3_256(data).hexdigest()


@dataclass
class Batch:
    """A batch of operations to execute together."""
    batch_id: str
    operations: List[OpSpec] = field(default_factory=list)
    append_log: AppendLog = field(default_factory=AppendLog)
    total_cost: float = 0.0
    
    def add_operation(self, op: OpSpec) -> None:
        """Add operation to batch."""
        self.operations.append(op)
        self.append_log.append(op.op_id)
    
    def compute_cost(self, curvature_map: Dict[str, float]) -> float:
        """Compute total curvature cost of batch."""
        total = 0.0
        for op in self.operations:
            total += curvature_map.get(op.op_id, 0.0)
        self.total_cost = total
        return total


class GreedyCurvScheduler:
    """
    Greedy.curv.v1 scheduler per docs/nk2/3_scheduler.md.
    
    Curvature-aware marginal cost batching with deterministic ordering.
    Maintains append_log during batch construction.
    """
    
    def __init__(self, scheduler_mode: SchedulerMode = SchedulerMode.GREEDY_CURV_V1):
        self.scheduler_mode = scheduler_mode
        self.append_log = AppendLog()
    
    def schedule(
        self,
        exec_plan: ExecPlan,
        curvature_map: Dict[str, float],
        max_batch_size: int = 100
    ) -> List[Batch]:
        """
        Schedule operations into batches.
        
        Returns list of batches in execution order.
        Maintains append_log for replay stability.
        """
        batches = []
        current_batch = None
        
        # Get ready operations
        ready_ops = exec_plan.get_ready_ops()
        
        # Sort by op_id for deterministic ordering (per docs/ck0/D_sorting_rules.md)
        ready_ops.sort(key=lambda op: op.op_id.encode('utf-8'))
        
        while ready_ops:
            # Select operation (greedy: pick highest curvature first)
            selected_op = self._select_op(ready_ops, curvature_map)
            
            # Try to add to current batch
            if current_batch is None:
                current_batch = Batch(batch_id=f"batch:{len(batches)}")
            
            # Check if we should start new batch
            if len(current_batch.operations) >= max_batch_size:
                batches.append(current_batch)
                current_batch = Batch(batch_id=f"batch:{len(batches)}")
            
            # Add operation to batch
            current_batch.add_operation(selected_op)
            current_batch.compute_cost(curvature_map)
            
            # Remove from ready list
            ready_ops.remove(selected_op)
            
            # Update dependencies
            for op in exec_plan.operations:
                if op.status == OpStatus.PENDING:
                    # Check if dependencies are now met
                    deps_met = True
                    for dep_id in op.depends_on:
                        dep = exec_plan.get_op(dep_id)
                        if dep is None or dep.status != OpStatus.COMPLETED:
                            deps_met = False
                            break
                    
                    if deps_met and op not in ready_ops:
                        ready_ops.append(op)
                        ready_ops.sort(key=lambda o: o.op_id.encode('utf-8'))
        
        # Add final batch
        if current_batch and current_batch.operations:
            batches.append(current_batch)
        
        return batches
    
    def _select_op(
        self,
        ready_ops: List[OpSpec],
        curvature_map: Dict[str, float]
    ) -> OpSpec:
        """
        Select next operation to execute.
        
        Greedy: select highest marginal cost operation.
        Tie-break by op_id bytes (deterministic).
        """
        if not ready_ops:
            raise ValueError("No operations to select")
        
        if len(ready_ops) == 1:
            return ready_ops[0]
        
        # Find max curvature
        max_curv = -1
        candidates = []
        
        for op in ready_ops:
            curv = curvature_map.get(op.op_id, 0.0)
            if curv > max_curv:
                max_curv = curv
                candidates = [op]
            elif curv == max_curv:
                candidates.append(op)
        
        # Tie-break by op_id bytes
        candidates.sort(key=lambda o: o.op_id.encode('utf-8'))
        return candidates[0]
    
    def get_append_log(self) -> AppendLog:
        """Get the append log."""
        return self.append_log


def create_scheduler(scheduler_mode: SchedulerMode = SchedulerMode.GREEDY_CURV_V1) -> GreedyCurvScheduler:
    """Create a scheduler."""
    return GreedyCurvScheduler(scheduler_mode)
