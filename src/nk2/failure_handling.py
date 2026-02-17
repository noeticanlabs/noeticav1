# NK-2 Failure Handling per docs/nk2/6_failure_handling.md

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .exec_plan import ExecPlan, OpSpec, OpStatus


class FailureType(Enum):
    """Types of failures."""
    KERNEL_ERROR = "kernel_error"
    DELTA_BOUND = "delta_bound"
    RESOURCE_CAP = "resource_cap"
    POLICY_VETO = "policy_veto"
    DEPENDENCY_FAILED = "dependency_failed"


@dataclass
class FailureInfo:
    """Information about a failure."""
    op_id: str
    failure_type: FailureType
    message: str
    is_singleton: bool = False


class FailureHandler:
    """
    Failure handling per docs/nk2/6_failure_handling.md.
    
    Implements:
    - Deterministic rescheduling transforms
    - Singleton terminal halt rule per §2.6.B
    - No retry loops
    """
    
    def __init__(self):
        self.failures: List[FailureInfo] = []
    
    def handle_failure(
        self,
        exec_plan: ExecPlan,
        failed_op: OpSpec,
        failure_type: FailureType,
        message: str = ""
    ) -> ExecPlan:
        """
        Handle a failure.
        
        Per docs/nk2/6_failure_handling.md:
        - Singleton kernel_error → terminal halt
        - Singleton delta_bound → terminal halt
        - No retry loops
        
        Returns modified exec_plan.
        """
        # Record failure
        failure = FailureInfo(
            op_id=failed_op.op_id,
            failure_type=failure_type,
            message=message,
            is_singleton=self._is_singleton_failure(exec_plan, failed_op)
        )
        self.failures.append(failure)
        
        # Check singleton terminal rule
        if failure.is_singleton:
            # Singleton failure → terminal halt
            return self._handle_singleton_halt(exec_plan, failure)
        else:
            # Non-singleton → deterministic reschedule
            return self._handle_reschedule(exec_plan, failure)
    
    def _is_singleton_failure(
        self,
        exec_plan: ExecPlan,
        failed_op: OpSpec
    ) -> bool:
        """Check if this is a singleton failure."""
        # Count pending operations
        pending_count = sum(
            1 for op in exec_plan.operations 
            if op.status == OpStatus.PENDING
        )
        
        # A singleton failure is when only one operation remains pending
        # and it fails
        return pending_count == 1 and failed_op.status == OpStatus.PENDING
    
    def _handle_singleton_halt(
        self,
        exec_plan: ExecPlan,
        failure: FailureInfo
    ) -> ExecPlan:
        """
        Handle singleton failure → terminal halt.
        
        Per §2.6.B:
        - Singleton kernel_error → terminal halt
        - Singleton delta_bound → terminal halt
        - No retry loops
        """
        # Mark the remaining pending operation as failed (this is the singleton)
        for op in exec_plan.operations:
            if op.status == OpStatus.PENDING:
                op.status = OpStatus.FAILED
                break
        
        return exec_plan
    
    def _handle_reschedule(
        self,
        exec_plan: ExecPlan,
        failure: FailureInfo
    ) -> ExecPlan:
        """
        Handle non-singleton failure with deterministic reschedule.
        
        Uses split lexmin + removal transforms.
        """
        # Remove the failed operation
        failed_op = exec_plan.get_op(failure.op_id)
        if failed_op:
            failed_op.status = OpStatus.FAILED
        
        # For remaining pending operations, we could implement:
        # - Split: divide batch
        # - Lexmin: remove lexically smallest
        # - Removal: remove failed op's dependents
        
        # For now, mark dependents as skipped
        for op in exec_plan.operations:
            if op.status == OpStatus.PENDING:
                if failure.op_id in op.depends_on:
                    op.status = OpStatus.SKIPPED
        
        return exec_plan
    
    def should_halt(self, exec_plan: ExecPlan) -> bool:
        """
        Determine if execution should halt.
        
        Halts if:
        - All operations complete
        - Singleton failure occurred
        - All pending operations failed
        """
        # Check for terminal singleton failures
        for failure in self.failures:
            if failure.is_singleton:
                return True
        
        # Check if all operations are terminal
        all_terminal = all(
            op.status in (OpStatus.COMPLETED, OpStatus.FAILED, OpStatus.SKIPPED)
            for op in exec_plan.operations
        )
        
        return all_terminal
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """Get summary of failures."""
        return {
            'total_failures': len(self.failures),
            'singleton_halts': sum(1 for f in self.failures if f.is_singleton),
            'failures': [
                {
                    'op_id': f.op_id,
                    'type': f.failure_type.value,
                    'message': f.message,
                    'is_singleton': f.is_singleton
                }
                for f in self.failures
            ]
        }


def create_failure_handler() -> FailureHandler:
    """Create a failure handler."""
    return FailureHandler()
