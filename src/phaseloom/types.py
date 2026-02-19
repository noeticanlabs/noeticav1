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
