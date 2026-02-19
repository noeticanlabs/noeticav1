# PhaseLoom Braiding Tension
#
# Implements T recurrence as per canon spine Section 6

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
import hashlib

from .types import FixedPoint


def compute_tension_increment_deterministic(
    expected_policy: str,
    observed_policy: str,
    expected_budget_delta: FixedPoint,
    observed_budget_delta: FixedPoint,
    expected_authority_delta: FixedPoint,
    observed_authority_delta: FixedPoint
) -> FixedPoint:
    """Compute tension increment deterministically.
    
    This is the v1 recommended formula that avoids off-chain computation.
    
    Args:
        expected_policy: Expected policy label
        observed_policy: Observed policy label
        expected_budget_delta: Expected budget change
        observed_budget_delta: Observed budget change
        expected_authority_delta: Expected authority change
        observed_authority_delta: Observed authority change
        
    Returns:
        Tension increment (non-negative)
    """
    # Policy distance: 0 if match, 1 if different
    policy_dist = FixedPoint.zero() if expected_policy == observed_policy else FixedPoint.one()
    
    # Budget distance
    budget_dist = (expected_budget_delta - observed_budget_delta).__abs__()
    
    # Authority distance  
    auth_dist = (expected_authority_delta - observed_authority_delta).__abs__()
    
    # Weighted sum (weights are governance parameters in full implementation)
    return policy_dist + budget_dist + auth_dist


def compute_tension_resolution(
    T: FixedPoint,
    resolution_efficacy: FixedPoint
) -> FixedPoint:
    """Compute tension resolution.
    
    Args:
        T: Current tension
        resolution_efficacy: How much tension can be resolved
        
    Returns:
        Tension resolution (non-negative, at most T)
    """
    # Resolution is bounded by current tension
    if resolution_efficacy.value >= T.value:
        return T
    return resolution_efficacy


def compute_tension_next(
    T: FixedPoint,
    delta_T_inc: FixedPoint,
    delta_T_res: FixedPoint,
    rho_T: FixedPoint
) -> FixedPoint:
    """Compute next tension: T+ = ρ_T * T + ΔT_inc - ΔT_res
    
    Then clamp to non-negative: T+ = max(T+, 0)
    
    Args:
        T: Current tension
        delta_T_inc: Tension increment
        delta_T_res: Tension resolution
        rho_T: Decay factor in [0, 1)
        
    Returns:
        Next tension (non-negative)
    """
    # Compute raw tension
    raw = rho_T * T + delta_T_inc - delta_T_res
    
    # Clamp to non-negative
    return FixedPoint(max(raw.value, 0))


def thread_assignment(
    step_index: int,
    policy_label: str,
    op_class: str,
    spectral_label: Optional[str] = None,
    module_id: Optional[str] = None
) -> str:
    """Deterministic thread assignment.
    
    Maps each step to a thread ID based on policy and operation.
    
    Args:
        step_index: Step number
        policy_label: Policy label
        op_class: Operation class (solve/repair/resolve)
        spectral_label: Optional spectral regime
        module_id: Optional module ID
        
    Returns:
        16-character thread ID
    """
    # Build deterministic string
    data = f"{step_index}:{policy_label}:{op_class}"
    if spectral_label:
        data += f":{spectral_label}"
    if module_id:
        data += f":{module_id}"
    
    # Hash to get thread ID
    thread_hash = hashlib.sha3_256(data.encode()).hexdigest()
    return thread_hash[:16]


@dataclass
class TensionState:
    """Tension accumulator state."""
    T: FixedPoint
    delta_T_inc: FixedPoint  # Last increment
    delta_T_res: FixedPoint  # Last resolution
    
    @classmethod
    def zero(cls) -> 'TensionState':
        return cls(
            T=FixedPoint.zero(),
            delta_T_inc=FixedPoint.zero(),
            delta_T_res=FixedPoint.zero()
        )


class TensionAccumulator:
    """Tension accumulator for PhaseLoom.
    
    Tracks cross-thread inconsistency using exponential decay.
    """
    
    def __init__(self, rho_T: FixedPoint):
        """Initialize with decay factor.
        
        Args:
            rho_T: Decay factor in [0, 1)
        """
        self.rho_T = rho_T
    
    def update(
        self,
        state: TensionState,
        delta_T_inc: FixedPoint,
        delta_T_res: FixedPoint
    ) -> TensionState:
        """Update tension.
        
        Args:
            state: Current tension state
            delta_T_inc: Tension increment
            delta_T_res: Tension resolution
            
        Returns:
            Updated tension state
        """
        # Compute next tension
        T_next = compute_tension_next(
            state.T, delta_T_inc, delta_T_res, self.rho_T
        )
        
        return TensionState(
            T=T_next,
            delta_T_inc=delta_T_inc,
            delta_T_res=delta_T_res
        )
    
    def verify_recurrence(
        self,
        T_prev: FixedPoint,
        T_next: FixedPoint,
        delta_T_inc: FixedPoint,
        delta_T_res: FixedPoint
    ) -> bool:
        """Verify tension recurrence holds.
        
        Args:
            T_prev: Previous tension
            T_next: Next tension
            delta_T_inc: Tension increment
            delta_T_res: Tension resolution
            
        Returns:
            True if recurrence holds
        """
        expected = compute_tension_next(T_prev, delta_T_inc, delta_T_res, self.rho_T)
        return T_next == expected


def compute_policy_histogram(
    thread_assignments: Dict[str, int]
) -> Dict[str, int]:
    """Compute histogram of thread assignments by policy.
    
    Args:
        thread_assignments: Map of thread_id -> count
        
    Returns:
        Histogram dict
    """
    return dict(thread_assignments)
