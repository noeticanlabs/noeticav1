# NK-2: Runtime Execution + Scheduler
#
# This module implements the NK-2 runtime execution and scheduler.
#
# Core Components:
# - exec_plan.py: ExecPlan + OpSpec
# - scheduler.py: Greedy.curv.v1 scheduler with append_log
# - failure_handling.py: Deterministic failure handling with singleton terminal rule

from .exec_plan import ExecPlan, OpSpec, OpStatus
from .scheduler import GreedyCurvScheduler, SchedulerMode, Batch, AppendLog
from .failure_handling import FailureHandler, FailureType, FailureInfo

__version__ = "1.0.0"

__all__ = [
    # Exec Plan
    'ExecPlan',
    'OpSpec',
    'OpStatus',
    
    # Scheduler
    'GreedyCurvScheduler',
    'SchedulerMode',
    'Batch',
    'AppendLog',
    
    # Failure Handling
    'FailureHandler',
    'FailureType',
    'FailureInfo',
]
