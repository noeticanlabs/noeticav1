# PhaseLoom Authority Injection
#
# Implements liveness escape hatch as per canon spine Section 10

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum

from .types import FixedPoint, StepType


class InjectionError(Exception):
    """Error during authority injection."""
    pass


class UnauthorizedInjectionError(InjectionError):
    """Authorization verification failed."""
    pass


class InvalidInjectionAmountError(InjectionError):
    """Invalid injection amounts."""
    pass


@dataclass
class MultiSig:
    """Multi-signature authorization for authority injection."""
    signers: List[str]  # Authorized signer addresses
    threshold: int     # Required signatures
    signatures: List[bytes] = field(default_factory=list)
    message_hash: str = ""
    
    def is_valid(self) -> bool:
        """Verify multi-sig validity."""
        # Check threshold
        if len(self.signatures) < self.threshold:
            return False
        
        # In production, verify each signature
        # For now, assume signatures are validated externally
        return len(self.signatures) >= self.threshold


@dataclass
class InjectionLimits:
    """Limits on authority injection."""
    max_delta_b: FixedPoint   # Max budget increase per step
    max_delta_a: FixedPoint   # Max authority increase per step
    max_total_a: FixedPoint   # Max cumulative authority
    min_interval: int          # Min steps between injections
    
    @classmethod
    def default(cls) -> 'InjectionLimits':
        """Default limits."""
        return cls(
            max_delta_b=FixedPoint.from_int(10000),
            max_delta_a=FixedPoint.from_int(1000),
            max_total_a=FixedPoint.from_int(100000),
            min_interval=10
        )


@dataclass
class AuthInjectRequest:
    """Authority injection request."""
    delta_b: FixedPoint      # Budget increase (> 0)
    delta_a: FixedPoint      # Authority increase (> 0)
    multisig: MultiSig       # Authorization proof
    policy_bundle_id: str     # Policy binding
    v_prev: FixedPoint       # Violation before (should equal v_next)
    v_next: FixedPoint       # Violation after (should equal v_prev)
    
    def validate(self) -> bool:
        """Validate injection constraints."""
        return (
            self.delta_b.value > 0 and
            self.delta_a.value > 0 and
            self.multisig.is_valid()
        )


def update_budget(b: FixedPoint, delta_b: FixedPoint) -> FixedPoint:
    """Update budget: b+ = b - Δb
    
    Args:
        b: Current budget
        delta_b: Budget expenditure (positive value)
        
    Returns:
        Next budget
        
    Raises:
        InvalidInjectionAmountError: If delta_b > b
    """
    if delta_b.value > b.value:
        raise InvalidInjectionAmountError("Budget expenditure exceeds available")
    return b - delta_b


def update_authority(a: FixedPoint, delta_a: FixedPoint) -> FixedPoint:
    """Update authority: a+ = a + Δa
    
    Args:
        a: Current authority
        delta_a: Authority injection (positive value)
        
    Returns:
        Next authority
    """
    return a + delta_a


def apply_authority_injection(
    b: FixedPoint,
    a: FixedPoint,
    request: AuthInjectRequest
) -> tuple[FixedPoint, FixedPoint]:
    """Apply authority injection.
    
    Args:
        b: Current budget
        a: Current authority
        request: Injection request
        
    Returns:
        Tuple of (new_b, new_a)
        
    Raises:
        UnauthorizedInjectionError: If authorization invalid
        InvalidInjectionAmountError: If amounts invalid
    """
    # Validate request
    if not request.validate():
        raise UnauthorizedInjectionError("Invalid injection request")
    
    # Apply injection
    new_b = b + request.delta_b
    new_a = a + request.delta_a
    
    return (new_b, new_a)


def check_injection_limits(
    state_a: FixedPoint,
    request: AuthInjectRequest,
    steps_since_last_injection: int,
    limits: InjectionLimits
) -> bool:
    """Check if injection stays within limits.
    
    Args:
        state_a: Current authority
        request: Injection request
        steps_since_last_injection: Steps since last injection
        limits: Injection limits
        
    Returns:
        True if within limits
    """
    # Check amounts
    if request.delta_b > limits.max_delta_b:
        return False
    if request.delta_a > limits.max_delta_a:
        return False
    if state_a + request.delta_a > limits.max_total_a:
        return False
    
    # Check interval
    if steps_since_last_injection < limits.min_interval:
        return False
    
    return True


def detect_deadlock(
    b: FixedPoint,
    b_min: FixedPoint,
    can_repair: bool
) -> bool:
    """Detect if system is in deadlock.
    
    A deadlock occurs when:
    - Interlock is active (b <= b_min)
    - Cannot repair (no tension or curvature to resolve)
    
    Args:
        b: Current budget
        b_min: Budget floor
        can_repair: Whether repair can progress
        
    Returns:
        True if in deadlock
    """
    # Interlock must be active
    if b.value > b_min.value:
        return False
    
    # Check if repair can progress
    return not can_repair


def create_injection_request(
    delta_b: FixedPoint,
    delta_a: FixedPoint,
    policy_bundle_id: str,
    signers: List[str],
    threshold: int
) -> AuthInjectRequest:
    """Create authority injection request.
    
    Args:
        delta_b: Budget increase
        delta_a: Authority increase
        policy_bundle_id: Policy binding
        signers: Authorized signers
        threshold: Required signatures
        
    Returns:
        AuthInjectRequest (unsigned)
    """
    # Create multisig placeholder
    multisig = MultiSig(
        signers=signers,
        threshold=threshold,
        signatures=[],
        message_hash=""
    )
    
    return AuthInjectRequest(
        delta_b=delta_b,
        delta_a=delta_a,
        multisig=multisig,
        policy_bundle_id=policy_bundle_id,
        v_prev=FixedPoint.zero(),  # Would be set from state
        v_next=FixedPoint.zero()   # Would be set from state
    )


@dataclass
class AuthorityState:
    """Authority injection state."""
    a: FixedPoint              # Cumulative authority
    last_injection_step: int   # Step number of last injection
    injection_count: int       # Number of injections
    
    @classmethod
    def zero(cls) -> 'AuthorityState':
        return cls(
            a=FixedPoint.zero(),
            last_injection_step=-1,
            injection_count=0
        )


class AuthorityInjector:
    """Authority injection handler."""
    
    def __init__(self, limits: InjectionLimits):
        """Initialize with limits."""
        self.limits = limits
    
    def inject(
        self,
        state: AuthorityState,
        request: AuthInjectRequest,
        current_step: int
    ) -> AuthorityState:
        """Process authority injection.
        
        Args:
            state: Current authority state
            request: Injection request
            current_step: Current step number
            
        Returns:
            Updated authority state
            
        Raises:
            UnauthorizedInjectionError: If unauthorized
            InvalidInjectionAmountError: If invalid amounts
        """
        # Check limits
        steps_since = current_step - state.last_injection_step
        if not check_injection_limits(state.a, request, steps_since, self.limits):
            raise InvalidInjectionAmountError("Injection exceeds limits")
        
        # Validate request
        if not request.validate():
            raise UnauthorizedInjectionError("Invalid injection")
        
        # Update state
        return AuthorityState(
            a=state.a + request.delta_a,
            last_injection_step=current_step,
            injection_count=state.injection_count + 1
        )
