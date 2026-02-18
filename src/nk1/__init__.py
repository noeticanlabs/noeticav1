# NK-1: Runtime Kernel
#
# This module implements the NK-1 runtime kernel for deterministic gating.
#
# Core Components:
# - policy_bundle.py: PolicyBundle canonicalization + digest
# - state_canon.py: sorted_json_bytes.v1 canonicalization
# - value_canon.py: ValueCanon type tagging (i:, q:, b64:, s:)
# - receipt_canon.py: canon_receipt_bytes.v1 + Merkle tree
# - delta_norm.py: δ-norm enforcement
# - batch_epsilon.py: ε_B/ε̂ computation
# - contracts.py: V(x) measurement engine
# - measured_gate.py: Gate decision logic
# - resource_guard.py: deterministic_reject.v1

from .policy_bundle import PolicyBundle, PolicyID, GLBMode, FloatPolicy, HashMode, StateEqMode
from .state_canon import StateCanon, StateMeta, CANON_ID, create_state_with_meta
from .value_canon import ValueCanon, canon_field_value
from .receipt_canon import ReceiptCanon, MerkleTree, CANON_RECEIPT_ID, ReceiptType
from .delta_norm import DeltaNormConfig, NormDomainMode, compute_delta_norm, requires_mode_d
from .batch_epsilon import BatchEpsilonConfig, VFunctional, Operation, compute_epsilon_B, compute_epsilon_hat, verify_gate
from .contracts import ContractMeasurementEngine, ContractMeasurement
from .measured_gate import MeasuredGate, GateDecision, DisturbancePolicies
from .resource_guard import ResourceGuard, ResourceLimit, ResourceCapError, create_standard_resource_guard
from .curvature_matrix import CurvatureMatrix, CurvatureMatrixRegistry, CANON_MATRIX_ID

__version__ = "1.0.0"

__all__ = [
    # Policy Bundle
    'PolicyBundle',
    'PolicyID',
    'GLBMode',
    'FloatPolicy',
    'HashMode',
    'StateEqMode',
    
    # State Canon
    'StateCanon',
    'StateMeta',
    'CANON_ID',
    'create_state_with_meta',
    
    # Value Canon
    'ValueCanon',
    'canon_field_value',
    
    # Receipt Canon
    'ReceiptCanon',
    'MerkleTree',
    'CANON_RECEIPT_ID',
    'ReceiptType',
    
    # Delta Norm
    'DeltaNormConfig',
    'NormDomainMode',
    'compute_delta_norm',
    'requires_mode_d',
    
    # Batch Epsilon
    'BatchEpsilonConfig',
    'VFunctional',
    'Operation',
    'compute_epsilon_B',
    'compute_epsilon_hat',
    'verify_gate',
    
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
    
    # Curvature Matrix
    'CurvatureMatrix',
    'CurvatureMatrixRegistry',
    'CANON_MATRIX_ID',
]
