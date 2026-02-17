# NK-2 ExecPlan + OpSpec per docs/nk2/1_exec_plan.md

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class OpStatus(Enum):
    """Operation status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class OpSpec:
    """
    Operation specification per docs/nk2/1_exec_plan.md.
    
    Defines a single operation to be executed.
    """
    op_id: str
    kernel_id: str
    
    # Read/write sets
    read_fields: Set[str] = field(default_factory=set)
    write_fields: Set[str] = field(default_factory=set)
    
    # Contracts
    contracts: List[str] = field(default_factory=list)  # Contract IDs
    
    # Footprint info
    footprint_r: Set[str] = field(default_factory=set)  # Read footprint
    footprint_w: Set[str] = field(default_factory=set)  # Write footprint
    footprint_block: bool = False
    float_touch: bool = False
    delta_bound_mode: str = "exact"
    
    # Execution
    args: Dict[str, Any] = field(default_factory=dict)
    status: OpStatus = OpStatus.PENDING
    
    # Dependencies (explicit)
    depends_on: Set[str] = field(default_factory=set)
    
    def __hash__(self):
        return hash(self.op_id)
    
    def __eq__(self, other):
        if not isinstance(other, OpSpec):
            return NotImplemented
        return self.op_id == other.op_id


@dataclass
class ExecPlan:
    """
    Execution plan per docs/nk2/1_exec_plan.md.
    
    Contains all operations to execute and scheduler configuration.
    """
    plan_id: str
    
    # Operations (sorted by op_id for deterministic ordering)
    operations: List[OpSpec] = field(default_factory=list)
    
    # Scheduler configuration
    scheduler_config: Dict[str, Any] = field(default_factory=dict)
    
    # Policy binding
    policy_digest: str = ""
    
    # Metadata
    version: str = "execplan_v1"
    
    def __post_init__(self):
        # Sort operations by op_id for canonical ordering
        self.operations.sort(key=lambda op: op.op_id.encode('utf-8'))
    
    def get_op(self, op_id: str) -> Optional[OpSpec]:
        """Get operation by ID."""
        for op in self.operations:
            if op.op_id == op_id:
                return op
        return None
    
    def get_ready_ops(self) -> List[OpSpec]:
        """Get operations that are ready to execute (dependencies met)."""
        ready = []
        for op in self.operations:
            if op.status != OpStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_met = True
            for dep_id in op.depends_on:
                dep = self.get_op(dep_id)
                if dep is None or dep.status != OpStatus.COMPLETED:
                    deps_met = False
                    break
            
            if deps_met:
                ready.append(op)
        
        return ready
    
    def mark_completed(self, op_id: str) -> None:
        """Mark operation as completed."""
        op = self.get_op(op_id)
        if op:
            op.status = OpStatus.COMPLETED
    
    def mark_failed(self, op_id: str) -> None:
        """Mark operation as failed."""
        op = self.get_op(op_id)
        if op:
            op.status = OpStatus.FAILED
    
    def is_complete(self) -> bool:
        """Check if all operations are complete."""
        for op in self.operations:
            if op.status not in (OpStatus.COMPLETED, OpStatus.SKIPPED):
                return False
        return True
    
    def has_failures(self) -> bool:
        """Check if any operation failed."""
        for op in self.operations:
            if op.status == OpStatus.FAILED:
                return True
        return False


def create_example_exec_plan() -> ExecPlan:
    """Create example execution plan."""
    plan = ExecPlan(plan_id="plan:example")
    
    # Add example operations
    op1 = OpSpec(
        op_id="op:001",
        kernel_id="example.add",
        read_fields=set(),
        write_fields={"f:00000000000000000000000000000001"}
    )
    
    op2 = OpSpec(
        op_id="op:002",
        kernel_id="example.mul",
        read_fields={"f:00000000000000000000000000000001"},
        write_fields={"f:00000000000000000000000000000002"},
        depends_on={"op:001"}
    )
    
    plan.operations = [op1, op2]
    return plan
