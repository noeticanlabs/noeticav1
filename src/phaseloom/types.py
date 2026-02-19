# PhaseLoom Types
#
# Core type definitions for PhaseLoom Potential

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from fractions import Fraction


# =============================================================================
# Fixed-Point Arithmetic
# =============================================================================

class FixedPoint:
    """Fixed-point number with deterministic truncation toward zero.
    
    All consensus-critical arithmetic uses fixed-point to ensure determinism.
    Scale is fixed at 6 decimal places (10^6) for v1.
    """
    
    SCALE = 6
    SCALE_FACTOR = 10 ** SCALE
    
    def __init__(self, value: int):
        """Create fixed-point from integer value (already scaled)."""
        self.value = value
    
    @classmethod
    def from_float(cls, f: float) -> FixedPoint:
        """Convert float to fixed-point (truncates toward zero)."""
        scaled = int(f * cls.SCALE_FACTOR)
        return cls(scaled)
    
    @classmethod
    def from_int(cls, i: int) -> FixedPoint:
        """Create from integer."""
        return cls(i * cls.SCALE_FACTOR)
    
    @classmethod
    def zero(cls) -> FixedPoint:
        """Create zero."""
        return cls(0)
    
    @classmethod
    def one(cls) -> FixedPoint:
        """Create one."""
        return cls(cls.SCALE_FACTOR)
    
    def to_float(self) -> float:
        """Convert to float (for display only, not for consensus)."""
        return self.value / self.SCALE_FACTOR
    
    def __repr__(self) -> str:
        return f"FixedPoint({self.value})"
    
    def __add__(self, other: FixedPoint) -> FixedPoint:
        return FixedPoint(self.value + other.value)
    
    def __sub__(self, other: FixedPoint) -> FixedPoint:
        return FixedPoint(self.value - other.value)
    
    def __mul__(self, other: FixedPoint) -> FixedPoint:
        """Multiply with truncation toward zero."""
        result = self.value * other.value
        # Truncate: shift right by scale
        scaled = result // self.SCALE_FACTOR
        return FixedPoint(scaled)
    
    def __truediv__(self, other: FixedPoint) -> FixedPoint:
        """Divide with truncation toward zero."""
        if other.value == 0:
            raise ZeroDivisionError("Division by zero in fixed-point")
        # Scale up before dividing
        scaled = self.value * self.SCALE_FACTOR
        result = scaled // other.value
        return FixedPoint(result)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FixedPoint):
            return False
        return self.value == other.value
    
    def __lt__(self, other: FixedPoint) -> bool:
        return self.value < other.value
    
    def __le__(self, other: FixedPoint) -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: FixedPoint) -> bool:
        return self.value > other.value
    
    def __ge__(self, other: FixedPoint) -> bool:
        return self.value >= other.value
    
    def __abs__(self) -> FixedPoint:
        return FixedPoint(abs(self.value))
    
    def __neg__(self) -> FixedPoint:
        return FixedPoint(-self.value)


# =============================================================================
# Enums
# =============================================================================

class StepType(Enum):
    """Step types in PhaseLoom execution."""
    SOLVE = "SOLVE"
    REPAIR = "REPAIR"
    RESOLVE = "RESOLVE"
    AUTH_INJECT = "AUTH_INJECT"


class InterlockReason(Enum):
    """Reasons for interlock activation."""
    NONE = "none"
    BUDGET_EXHAUSTED = "budget_exhausted"
    POTENTIAL_EXCEEDED = "potential_exceeded"


# =============================================================================
# Core Types
# =============================================================================

@dataclass
class MemoryState:
    """Geometric memory fiber state (M).
    
    M = R≥0 × R≥0 × R≥0 × R≥0
    Coordinates: (C, T, b, a)
    """
    C: FixedPoint = field(default_factory=FixedPoint.zero)  # Curvature
    T: FixedPoint = field(default_factory=FixedPoint.zero)  # Tension
    b: FixedPoint = field(default_factory=FixedPoint.zero)  # Budget
    a: FixedPoint = field(default_factory=FixedPoint.zero)  # Authority
    
    def to_tuple(self) -> Tuple[FixedPoint, FixedPoint, FixedPoint, FixedPoint]:
        return (self.C, self.T, self.b, self.a)
    
    @classmethod
    def from_tuple(cls, t: Tuple) -> MemoryState:
        return cls(C=t[0], T=t[1], b=t[2], a=t[3])
    
    @classmethod
    def zeros(cls) -> MemoryState:
        return cls(
            C=FixedPoint.zero(),
            T=FixedPoint.zero(),
            b=FixedPoint.zero(),
            a=FixedPoint.zero()
        )


@dataclass
class PLState:
    """PhaseLoom extended state.
    
    Extended state space: X × M
    Where X is base state space, M is geometric memory
    """
    x: Any                                           # Base state (from CK-0)
    C: FixedPoint = field(default_factory=FixedPoint.zero)  # Curvature
    T: FixedPoint = field(default_factory=FixedPoint.zero)  # Tension
    b: FixedPoint = field(default_factory=FixedPoint.zero)  # Budget
    a: FixedPoint = field(default_factory=FixedPoint.zero)  # Authority
    
    @property
    def memory(self) -> MemoryState:
        """Get memory component."""
        return MemoryState(C=self.C, T=self.T, b=self.b, a=self.a)
    
    def with_memory(self, memory: MemoryState) -> PLState:
        """Create new state with updated memory."""
        return PLState(
            x=self.x,
            C=memory.C,
            T=memory.T,
            b=memory.b,
            a=memory.a
        )


@dataclass 
class Weights:
    """Weights for PhaseLoom Potential V_PL."""
    w0: FixedPoint  # Base violation weight
    wC: FixedPoint  # Curvature weight  
    wT: FixedPoint  # Tension weight
    wb: FixedPoint  # Barrier weight
    wa: FixedPoint  # Authority weight
    
    @classmethod
    def default(cls) -> Weights:
        """Default weights for v1."""
        return cls(
            w0=FixedPoint.from_float(1.0),
            wC=FixedPoint.from_float(0.1),
            wT=FixedPoint.from_float(0.05),
            wb=FixedPoint.from_float(0.01),
            wa=FixedPoint.from_float(0.001)
        )


@dataclass
class PLParams:
    """PhaseLoom governance parameters.
    
    All parameters are fixed-point for deterministic execution.
    """
    # Decay factors (in [0, 1))
    rho_C: FixedPoint  # Curvature decay
    rho_T: FixedPoint  # Tension decay
    
    # Cost parameters
    kappa_A: FixedPoint  # Amplification budget price (> 0)
    kappa_T: FixedPoint  # Tension increment budget price (> 0)
    
    # Interlock
    b_min: FixedPoint  # Budget floor for interlock
    
    # Weights
    weights: Weights
    
    # Barrier constant
    epsilon: FixedPoint  # (> 0) for barrier function
    
    # Strong mode (optional)
    Theta: Optional[FixedPoint] = None  # Potential threshold
    strong_mode: bool = False
    
    @classmethod
    def default(cls) -> PLParams:
        """Default parameters for v1 (consensus safe)."""
        return cls(
            rho_C=FixedPoint.from_float(0.9),
            rho_T=FixedPoint.from_float(0.9),
            kappa_A=FixedPoint.from_float(1.0),
            kappa_T=FixedPoint.from_float(1.0),
            b_min=FixedPoint.zero(),
            weights=Weights.default(),
            epsilon=FixedPoint.from_float(0.0001),
            Theta=None,
            strong_mode=False
        )


@dataclass
class InterlockResult:
    """Result of interlock check."""
    allowed: bool
    reason: InterlockReason = InterlockReason.NONE
    
    @classmethod
    def allowed(cls) -> InterlockResult:
        return cls(allowed=True, reason=InterlockReason.NONE)
    
    @classmethod
    def rejected(cls, reason: InterlockReason) -> InterlockResult:
        return cls(allowed=False, reason=reason)


@dataclass
class STFResult:
    """State transition function result."""
    accepted: bool
    next_state: Optional[PLState] = None
    reject_code: Optional[str] = None
    message: str = ""
    
    @classmethod
    def accepted(cls, next_state: PLState) -> STFResult:
        return cls(accepted=True, next_state=next_state, message="Accepted")
    
    @classmethod
    def rejected(cls, reject_code: str, message: str) -> STFResult:
        return cls(accepted=False, next_state=None, reject_code=reject_code, message=message)


# =============================================================================
# CK-0 Integration Bridge
# =============================================================================
# These functions provide bridge to CK-0 DebtUnit for integration.
# PhaseLoom uses FixedPoint internally for performance, but can convert
# to DebtUnit for NK verification boundary when needed.

def fixedpoint_to_debtunit_value(fp: FixedPoint) -> int:
    """Convert FixedPoint to DebtUnit value (integer).
    
    Note: FixedPoint uses scale=10^6, DebtUnit typically uses scale=1000.
    This converts the scaled value directly.
    
    Args:
        fp: FixedPoint value
        
    Returns:
        Integer value suitable for DebtUnit
    """
    # FixedPoint is already scaled, return the raw value
    return fp.value


def debtunit_value_to_fixedpoint(value: int) -> FixedPoint:
    """Convert DebtUnit value to FixedPoint.
    
    Args:
        value: Integer value from DebtUnit
        
    Returns:
        FixedPoint representation
    """
    return FixedPoint(value)


def convert_to_ck0_format(fp: FixedPoint) -> dict:
    """Convert FixedPoint to CK-0 compatible format.
    
    Args:
        fp: FixedPoint value
        
    Returns:
        Dictionary with value and scale
    """
    return {
        "value": fp.value,
        "scale": FixedPoint.SCALE,
        "type": "FixedPoint"
    }


def convert_from_ck0_format(data: dict) -> FixedPoint:
    """Convert from CK-0 format to FixedPoint.
    
    Args:
        data: Dictionary with value and scale
        
    Returns:
        FixedPoint value
    """
    if data.get("type") == "FixedPoint":
        return FixedPoint(data["value"])
    elif data.get("type") == "DebtUnit":
        # DebtUnit value directly
        return FixedPoint(data["value"])
    else:
        raise ValueError(f"Unknown format: {data}")


# =============================================================================
# Coh Category Integration
# =============================================================================
# PhaseLoom state can be viewed as a CohObject for categorical operations.

def make_coh_object(pl_state: PLState, v_threshold: float = 0.0):
    """Create a CohObject from PhaseLoom state.
    
    This enables PhaseLoom to participate in categorical operations
    defined in the Coh module.
    
    Args:
        pl_state: PhaseLoom state
        v_threshold: Admissibility threshold
        
    Returns:
        CohObject adapter
    """
    # Import here to avoid circular dependencies
    from coh.types import CohObject
    
    def is_state(x: Any) -> bool:
        return isinstance(x, PLState)
    
    def is_receipt(x: Any) -> bool:
        return isinstance(x, Receipt)
    
    def potential(x: Any) -> float:
        if isinstance(x, PLState):
            # Use the potential value if available
            if hasattr(x, 'potential') and x.potential is not None:
                return x.potential.to_float()
            return 0.0
        return float('inf')
    
    def budget_map(x: Any) -> float:
        # Budget mapping - PhaseLoom doesn't have explicit receipts for budget
        return 0.0
    
    def validate(x: Any, y: Any, rho: Any) -> bool:
        # Validation - check state transition is valid
        if not isinstance(x, PLState) or not isinstance(y, PLState):
            return False
        # Basic validation: same phase transition
        return True
    
    return CohObject(
        is_state=is_state,
        is_receipt=is_receipt,
        potential=potential,
        budget_map=budget_map,
        validate=validate
    )


# =============================================================================
# NK-4G Receipt Bridge
# =============================================================================
# Functions to convert PhaseLoom state/receipts to NK-4G compatible format.

def convert_plstate_to_nk4g_format(pl_state: PLState) -> dict:
    """Convert PhaseLoom state to NK-4G compatible format.
    
    Args:
        pl_state: PhaseLoom state
        
    Returns:
        Dictionary with NK-4G compatible fields
    """
    result = {
        "type": "phaseloom_state",
        "version": "v1",
    }
    
    # Add curvature if available
    if hasattr(pl_state, 'curvature') and pl_state.curvature is not None:
        result["curvature"] = convert_to_ck0_format(pl_state.curvature)
    
    # Add tension if available
    if hasattr(pl_state, 'tension') and pl_state.tension is not None:
        result["tension"] = convert_to_ck0_format(pl_state.tension)
    
    # Add phase
    if hasattr(pl_state, 'phase'):
        result["phase"] = pl_state.phase.value if hasattr(pl_state.phase, 'value') else str(pl_state.phase)
    
    return result


def convert_plreceipt_to_nk4g_format(receipt: Any) -> dict:
    """Convert PhaseLoom receipt to NK-4G compatible format.
    
    Args:
        receipt: PhaseLoom receipt
        
    Returns:
        Dictionary with NK-4G compatible fields
    """
    result = {
        "type": "phaseloom_receipt",
        "version": "v1",
    }
    
    # Extract common receipt fields if available
    if hasattr(receipt, 'digest'):
        result["receipt_digest"] = receipt.digest
    
    if hasattr(receipt, 'state_hash'):
        result["state_hash"] = receipt.state_hash
    
    if hasattr(receipt, 'step_type'):
        result["step_type"] = receipt.step_type.value if hasattr(receipt.step_type, 'value') else str(receipt.step_type)
    
    return result


# =============================================================================
# NK-1 Gate Integration
# =============================================================================
# Functions to check PhaseLoom operations against NK-1 Measured Gate.

def convert_to_nk1_gate_format(
    pl_state: PLState,
    budget: int
) -> dict:
    """Convert PhaseLoom state for NK-1 gate check.
    
    Args:
        pl_state: PhaseLoom state
        budget: Proposed budget for operation
        
    Returns:
        Dictionary with NK-1 gate compatible fields
    """
    result = {
        "type": "phaseloom_nk1_gate_check",
        "version": "v1",
        "budget": budget,
    }
    
    # Add curvature as epsilon bound
    if hasattr(pl_state, 'curvature') and pl_state.curvature is not None:
        result["epsilon_hat"] = fixedpoint_to_debtunit_value(pl_state.curvature)
    else:
        result["epsilon_hat"] = 0
    
    # Add potential as V(x)
    if hasattr(pl_state, 'potential') and pl_state.potential is not None:
        result["v_x"] = fixedpoint_to_debtunit_value(pl_state.potential)
    else:
        result["v_x"] = 0
    
    return result


def check_phaseloom_gate(
    pl_state: PLState,
    budget: int,
    epsilon_hat: int,
    epsilon_measured: int
) -> dict:
    """Check if PhaseLoom operation passes NK-1 gate.
    
    Args:
        pl_state: PhaseLoom state before operation
        budget: Proposed budget
        epsilon_hat: Maximum allowed delta-V (from curvature matrix)
        epsilon_measured: Actual measured delta-V
        
    Returns:
        Gate decision dict with:
        - approved: bool
        - epsilon_measured: int
        - epsilon_hat: int
        - reason: str
    """
    # NK-1 gate rule: epsilon_measured <= epsilon_hat
    if epsilon_measured <= epsilon_hat:
        return {
            "approved": True,
            "epsilon_measured": epsilon_measured,
            "epsilon_hat": epsilon_hat,
            "reason": "gate_passed",
            "budget": budget
        }
    else:
        return {
            "approved": False,
            "epsilon_measured": epsilon_measured,
            "epsilon_hat": epsilon_hat,
            "reason": f"epsilon_measured ({epsilon_measured}) > epsilon_hat ({epsilon_hat})",
            "budget": budget
        }
