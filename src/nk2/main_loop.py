# NK-2 Main Loop Implementation
# Per docs/nk2/8_main_loop.md

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .exec_plan import ExecPlan, OpSpec, OpStatus
from .scheduler import GreedyCurvScheduler, SchedulerMode
from .failure_handling import FailureHandler, FailureType


class RuntimeStatus(Enum):
    """Runtime execution status."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    HALTED = "halted"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionResult:
    """Result of NK-2 execution."""
    status: RuntimeStatus
    final_state_hash: str
    commit_hash: str
    receipt_chain: List[str]
    batches_executed: int
    operations_completed: int
    failures: List[Dict[str, Any]]


class NK2Runtime:
    """
    NK-2 Runtime Executor.
    
    Per docs/nk2/8_main_loop.md:
    - Validates inputs
    - Initializes DAG and ready set
    - Executes batches via greedy.curv.v1 scheduler
    - Handles failures with rescheduling transforms
    - Outputs final state and receipt chain
    """
    
    def __init__(
        self,
        exec_plan: ExecPlan,
        initial_state: 'State',
        policy_bundle: 'PolicyBundle',
        kernel_registry: 'KernelRegistry',
        curvature_matrix: 'CurvatureMatrix',
    ):
        """Initialize NK-2 Runtime."""
        self.exec_plan = exec_plan
        self.initial_state = initial_state
        self.current_state = initial_state
        self.policy_bundle = policy_bundle
        self.kernel_registry = kernel_registry
        self.curvature_matrix = curvature_matrix
        
        # Initialize scheduler
        self.scheduler = GreedyCurvScheduler(SchedulerMode.GREEDY_CURV_V1)
        
        # Initialize failure handler
        self.failure_handler = FailureHandler()
        
        # Runtime state
        self.status = RuntimeStatus.INITIALIZING
        self.receipt_chain: List[str] = []
        self.batch_count = 0
        self.failures: List[Dict[str, Any]] = []
        
        # Validate inputs
        self._validate_inputs()
        
        # Build initial ready set
        self._initialize_dag()
    
    def _validate_inputs(self) -> None:
        """Validate all inputs before execution."""
        # Validate policy bundle
        if not self.policy_bundle:
            raise ValueError("PolicyBundle is required")
        
        # Validate initial state
        if not self.initial_state:
            raise ValueError("Initial state is required")
        
        # Validate exec plan
        if not self.exec_plan or not self.exec_plan.operations:
            raise ValueError("ExecPlan with operations is required")
        
        self.status = RuntimeStatus.INITIALIZING
    
    def _initialize_dag(self) -> None:
        """Build DAG indegrees and compute initial ready set."""
        # Compute in-degrees for DAG
        self.in_degree: Dict[str, int] = {}
        for op in self.exec_plan.operations:
            self.in_degree[op.op_id] = len(op.depends_on)
        
        # Initial ready set (operations with no dependencies)
        self.ready_ops: List[OpSpec] = [
            op for op in self.exec_plan.operations
            if self.in_degree[op.op_id] == 0 and op.status == OpStatus.PENDING
        ]
        
        # Sort for deterministic order
        self.ready_ops.sort(key=lambda op: op.op_id.encode('utf-8'))
    
    def run(self) -> ExecutionResult:
        """
        Execute the main loop.
        
        Algorithm per docs/nk2/8_main_loop.md:
        1. VALIDATE - Verify policy and initial state
        2. INITIALIZE - Build DAG, compute ready set
        3. WHILE PENDING ≠ ∅:
           - BUILD BATCH (Greedy.curv.v1)
           - ATTEMPT BATCH
           - IF SUCCESS: emit receipts, update state
           - IF FAIL: classify, reschedule or halt
        4. OUTPUT - Final state, commit hash, receipt chain
        """
        self.status = RuntimeStatus.RUNNING
        
        while self._has_pending_ops():
            # Build batch using scheduler
            batch = self._build_batch()
            
            if not batch:
                break
            
            # Attempt batch execution
            success, batch_result = self._attempt_batch(batch)
            
            if success:
                self._handle_success(batch_result)
            else:
                self._handle_failure(batch_result)
                
                # Check for terminal failure
                if batch_result.get('terminal'):
                    self.status = RuntimeStatus.FAILED
                    break
        
        # Complete
        if self.status == RuntimeStatus.RUNNING:
            self.status = RuntimeStatus.COMPLETED
        
        return self._produce_result()
    
    def _has_pending_ops(self) -> bool:
        """Check if there are pending operations."""
        return any(
            op.status == OpStatus.PENDING 
            for op in self.exec_plan.operations
        )
    
    def _build_batch(self) -> List[OpSpec]:
        """Build next batch using scheduler."""
        if not self.ready_ops:
            return []
        
        # Get curvature map for scheduler
        curvature_map = {}
        for op_id in self.curvature_matrix.interactions:
            curvature_map[op_id] = self.curvature_matrix.interactions[op_id]
        
        # Schedule using greedy.curv.v1
        batch = self.scheduler.schedule(
            self.exec_plan,
            curvature_map,
            max_batch_size=10  # Configurable
        )
        
        return batch
    
    def _attempt_batch(self, batch: List[OpSpec]) -> tuple[bool, Dict[str, Any]]:
        """Attempt to execute a batch."""
        # Placeholder: actual kernel execution would happen here
        # For now, simulate successful execution
        
        result = {
            'operations': [op.op_id for op in batch],
            'state_delta': {},
            'receipts': [],
        }
        
        # Mark operations as completed
        for op in batch:
            op.status = OpStatus.COMPLETED
            
            # Update in-degrees for dependents
            for dependent_op in self.exec_plan.operations:
                if op.op_id in dependent_op.depends_on:
                    self.in_degree[dependent_op.op_id] -= 1
                    if self.in_degree[dependent_op.op_id] == 0:
                        self.ready_ops.append(dependent_op)
        
        # Sort ready ops for deterministic order
        self.ready_ops.sort(key=lambda op: op.op_id.encode('utf-8'))
        
        return True, result
    
    def _handle_success(self, batch_result: Dict[str, Any]) -> None:
        """Handle successful batch execution."""
        self.batch_count += 1
        
        # Emit receipts
        for receipt in batch_result.get('receipts', []):
            self.receipt_chain.append(receipt)
        
        # Update state
        # (Actual state update would happen here)
    
    def _handle_failure(self, failure_result: Dict[str, Any]) -> None:
        """Handle batch failure."""
        # Classify failure
        failure_type = self.failure_handler.classify(failure_result)
        
        # Record failure
        self.failures.append({
            'type': failure_type.value,
            'result': failure_result,
        })
        
        # Apply rescheduling transform
        self.failure_handler.apply_transform(failure_result, self.exec_plan)
    
    def _produce_result(self) -> ExecutionResult:
        """Produce final execution result."""
        # Compute final state hash (placeholder)
        final_state_hash = f"sha256:{hash(str(self.current_state)) % (2**64):016x}"
        
        # Compute commit hash
        commit_hash = f"commit:{self.batch_count}:{final_state_hash}"
        
        return ExecutionResult(
            status=self.status,
            final_state_hash=final_state_hash,
            commit_hash=commit_hash,
            receipt_chain=self.receipt_chain,
            batches_executed=self.batch_count,
            operations_completed=sum(
                1 for op in self.exec_plan.operations 
                if op.status == OpStatus.COMPLETED
            ),
            failures=self.failures,
        )


def create_runtime(
    exec_plan: ExecPlan,
    initial_state: 'State',
    policy_bundle: 'PolicyBundle',
    kernel_registry: 'KernelRegistry',
    curvature_matrix: 'CurvatureMatrix',
) -> NK2Runtime:
    """Create NK-2 Runtime instance."""
    return NK2Runtime(
        exec_plan=exec_plan,
        initial_state=initial_state,
        policy_bundle=policy_bundle,
        kernel_registry=kernel_registry,
        curvature_matrix=curvature_matrix,
    )
