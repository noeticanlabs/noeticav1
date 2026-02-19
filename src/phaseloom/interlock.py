# PhaseLoom Scheduler Interlock
#
# Implements multi-clock interlock as per canon spine

from __future__ import annotations
from typing import List, Optional

from .types import (
    PLState,
    PLParams,
    FixedPoint,
    StepType,
    InterlockReason,
    InterlockResult,
)
from .potential import compute_potential_from_state


def check_interlock(
    state: PLState,
    step_type: StepType,
    A: FixedPoint,
    params: PLParams,
    strong_mode: Optional[bool] = None
) -> InterlockResult:
    """Check if step is admissible under interlock.
    
    Interlock rules:
    - If b ≤ b_min: reject SOLVE steps with A > 0
    - If strong_mode and V_PL ≥ Θ: reject SOLVE steps with A > 0
    
    Args:
        state: Current state
        step_type: Type of step being attempted
        A: Amplification (Δv)+ 
        params: Governance parameters
        strong_mode: Override for strong mode
        
    Returns:
        InterlockResult indicating if step is allowed
    """
    # Use provided strong_mode or fall back to params
    use_strong = strong_mode if strong_mode is not None else params.strong_mode
    
    # Check budget floor
    budget_ok = state.b > params.b_min
    
    # Check potential threshold (strong mode)
    if use_strong and params.Theta is not None:
        V_PL = compute_potential_from_state(state, params)
        potential_ok = V_PL < params.Theta
    else:
        potential_ok = True
    
    # Determine if interlock is active
    interlock_active = not budget_ok or not potential_ok
    
    # Check step type
    if step_type == StepType.SOLVE:
        # SOLVE steps with A > 0 are rejected when interlock is active
        if interlock_active and A.value > 0:
            if not budget_ok:
                return InterlockResult.rejected(InterlockReason.BUDGET_EXHAUSTED)
            else:
                return InterlockResult.rejected(InterlockReason.POTENTIAL_EXCEEDED)
    
    return InterlockResult.allowed()


def admissible_steps(
    state: PLState,
    params: PLParams,
    strong_mode: Optional[bool] = None
) -> List[StepType]:
    """Get list of admissible step types.
    
    Args:
        state: Current state
        params: Governance parameters
        strong_mode: Override for strong mode
        
    Returns:
        List of admissible step types
    """
    # Use provided strong_mode or fall back to params
    use_strong = strong_mode if strong_mode is not None else params.strong_mode
    
    # Check budget floor
    budget_ok = state.b > params.b_min
    
    # Check potential threshold (strong mode)
    if use_strong and params.Theta is not None:
        V_PL = compute_potential_from_state(state, params)
        potential_ok = V_PL < params.Theta
    else:
        potential_ok = True
    
    # Determine if interlock is active
    interlock_active = not budget_ok or not potential_ok
    
    if interlock_active:
        # Only repair/resolve/inject allowed
        return [
            StepType.REPAIR,
            StepType.RESOLVE,
            StepType.AUTH_INJECT
        ]
    
    # All steps allowed
    return [
        StepType.SOLVE,
        StepType.REPAIR,
        StepType.RESOLVE,
        StepType.AUTH_INJECT
    ]


def select_delta_t(
    solver_delta: FixedPoint,
    governance_delta: FixedPoint,
    spectral_delta: FixedPoint,
    hardware_delta: FixedPoint,
    state: PLState,
    params: PLParams
) -> FixedPoint:
    """Select minimum clock delta with interlock check.
    
    The scheduler chooses Δt = min(Δt_s, Δt_g, Δt_λ, Δt_h)
    but interlock may reduce the delta.
    
    Args:
        solver_delta: Solver clock delta
        governance_delta: Governance clock delta
        spectral_delta: Spectral clock delta
        hardware_delta: Hardware clock delta
        state: Current state
        params: Governance parameters
        
    Returns:
        Selected delta t
    """
    # Base selection
    base_delta = min(solver_delta, governance_delta, spectral_delta, hardware_delta)
    
    # Interlock may reduce delta
    if state.b <= params.b_min:
        # Return minimum safe delta
        return FixedPoint.from_int(1)
    
    return base_delta


def is_interlock_active(
    state: PLState,
    params: PLParams,
    strong_mode: Optional[bool] = None
) -> bool:
    """Check if interlock is currently active.
    
    Args:
        state: Current state
        params: Governance parameters
        strong_mode: Override for strong mode
        
    Returns:
        True if interlock is active
    """
    # Use provided strong_mode or fall back to params
    use_strong = strong_mode if strong_mode is not None else params.strong_mode
    
    # Check budget floor
    budget_ok = state.b > params.b_min
    
    # Check potential threshold (strong mode)
    if use_strong and params.Theta is not None:
        V_PL = compute_potential_from_state(state, params)
        potential_ok = V_PL < params.Theta
    else:
        potential_ok = True
    
    return not budget_ok or not potential_ok


def get_interlock_reason(
    state: PLState,
    params: PLParams,
    strong_mode: Optional[bool] = None
) -> InterlockReason:
    """Get the reason for interlock activation.
    
    Args:
        state: Current state
        params: Governance parameters
        strong_mode: Override for strong mode
        
    Returns:
        InterlockReason if active, NONE otherwise
    """
    # Use provided strong_mode or fall back to params
    use_strong = strong_mode if strong_mode is not None else params.strong_mode
    
    # Check budget floor first (most common)
    if state.b <= params.b_min:
        return InterlockReason.BUDGET_EXHAUSTED
    
    # Check potential threshold (strong mode)
    if use_strong and params.Theta is not None:
        V_PL = compute_potential_from_state(state, params)
        if V_PL >= params.Theta:
            return InterlockReason.POTENTIAL_EXCEEDED
    
    return InterlockReason.NONE
