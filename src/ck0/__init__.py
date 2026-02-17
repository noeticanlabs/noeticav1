# CK-0: Mathematical Substrate
# 
# This module implements the CK-0 mathematical substrate for coherence enforcement.
# 
# Core Components:
# - debtunit.py: Exact integer arithmetic (no floats)
# - state_space.py: Typed state representation
# - invariants.py: Hard constraint checking
# - violation.py: V(x) coherence functional
# - budget_law.py: Service map S(D,B)
# - curvature.py: NEC closure matrix
# - transition.py: Deterministic evolution T(x,u)
# - receipts.py: Receipt schema
# - verifier.py: Replay verifier

from .debtunit import DebtUnit, ZERO, ONE
from .state_space import State, FieldBlock, FieldDef, FieldType
from .invariants import Invariant, InvariantSet, InvariantViolationError
from .violation import ViolationFunctional, Contract
from .budget_law import ServiceLaw, DisturbancePolicy, compute_budget_law
from .curvature import CurvatureMatrix
from .transition import TransitionContract, TransitionDescriptor, TransitionType
from .receipts import StepReceipt, CommitReceipt, ModuleReceipt, ReceiptChain
from .verifier import ReplayVerifier, VerificationResult, VerificationError

__version__ = "1.0.0"

__all__ = [
    # DebtUnit
    'DebtUnit',
    'ZERO',
    'ONE',
    
    # State Space
    'State',
    'FieldBlock', 
    'FieldDef',
    'FieldType',
    
    # Invariants
    'Invariant',
    'InvariantSet',
    'InvariantViolationError',
    
    # Violation Functional
    'ViolationFunctional',
    'Contract',
    
    # Budget Law
    'ServiceLaw',
    'DisturbancePolicy',
    'compute_budget_law',
    
    # Curvature
    'CurvatureMatrix',
    
    # Transition
    'TransitionContract',
    'TransitionDescriptor',
    'TransitionType',
    
    # Receipts
    'StepReceipt',
    'CommitReceipt', 
    'ModuleReceipt',
    'ReceiptChain',
    
    # Verifier
    'ReplayVerifier',
    'VerificationResult',
    'VerificationError',
]
