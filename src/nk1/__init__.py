# NK-1: Runtime Kernel
#
# This module implements the NK-1 runtime kernel for deterministic gating.
#
# Core Components:
# - policy_bundle.py: PolicyBundle canonicalization + digest
# - contracts.py: V(x) measurement engine
# - measured_gate.py: Gate decision logic
# - resource_guard.py: deterministic_reject.v1

from .policy_bundle import PolicyBundle, PolicyID, GLBMode, FloatPolicy, HashMode, StateEqMode
from .contracts import ContractMeasurementEngine, ContractMeasurement
from .measured_gate import MeasuredGate, GateDecision, DisturbancePolicies
from .resource_guard import ResourceGuard, ResourceLimit, ResourceCapError, create_standard_resource_guard

__version__ = "1.0.0"

__all__ = [
    # Policy Bundle
    'PolicyBundle',
    'PolicyID',
    'GLBMode',
    'FloatPolicy',
    'HashMode',
    'StateEqMode',
    
    # Contracts
    'ContractMeasurementEngine',
    'ContractMeasurement',
    
    # Measured Gate
    'MeasuredGate',
    'GateDecision',
    'DisturbancePolicies',
    
    # Resource Guard
    'ResourceGuard',
    'ResourceLimit',
    'ResourceCapError',
    'create_standard_resource_guard',
]
