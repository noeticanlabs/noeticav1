# CK-0 DebtUnit: Exact Integer Arithmetic
# No floats, no rationals, no mixed units - deterministic exact integer quanta

from typing import Union
from fractions import Fraction
import math

class DebtUnit:
    """
    DebtUnit: Exact integer arithmetic for CK-0 coherence computation.
    
    INVARIANTS:
    - All values are non-negative integers (ℤ_{≥0})
    - No floats, no rationals, no NaN, no ±Inf
    - Arithmetic operations return exact integers
    - Rounding (if needed) is half-even and happens exactly once at boundary
    """
    
    def __init__(self, value: Union[int, 'DebtUnit']):
        if isinstance(value, DebtUnit):
            self._value = value._value
        else:
            if not isinstance(value, int):
                raise TypeError(f"DebtUnit requires int, got {type(value).__name__}")
            if value < 0:
                raise ValueError(f"DebtUnit requires non-negative, got {value}")
            self._value = value
    
    @staticmethod
    def from_fraction(frac: Fraction, scale: int) -> 'DebtUnit':
        """
        Convert rational to DebtUnit via half-even rounding.
        
        This is the ONLY place rounding happens - at the boundary
        when converting from rational space to integer DebtUnit.
        """
        if not isinstance(frac, Fraction):
            raise TypeError(f"Fraction required, got {type(frac).__name__}")
        
        scaled = frac * scale
        # Half-even rounding
        rounded = scaled.numerator // scaled.denominator
        remainder = scaled.numerator % scaled.denominator
        
        # Half-even adjustment
        if remainder * 2 == scaled.denominator:
            # Exactly half - round to even
            if rounded % 2 == 0:
                pass  # Keep even
            else:
                rounded += 1
        elif remainder * 2 > scaled.denominator:
            rounded += 1
            
        return DebtUnit(max(0, rounded))
    
    @staticmethod
    def from_decimal(value: Union[int, float], scale: int = 1) -> 'DebtUnit':
        """Convert decimal to DebtUnit - only for testing, not production."""
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                raise ValueError("DebtUnit cannot represent NaN or Inf")
            # Convert float to fraction, then to DebtUnit
            frac = Fraction(value).limit_denominator(10**12)
            return DebtUnit.from_fraction(frac, scale)
        return DebtUnit(int(value) * scale)
    
    @property
    def value(self) -> int:
        """Return the raw integer value."""
        return self._value
    
    def __repr__(self) -> str:
        return f"DebtUnit({self._value})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DebtUnit):
            return NotImplemented
        return self._value == other._value
    
    def __lt__(self, other: 'DebtUnit') -> bool:
        if not isinstance(other, DebtUnit):
            return NotImplemented
        return self._value < other._value
    
    def __le__(self, other: 'DebtUnit') -> bool:
        return self == other or self < other
    
    def __gt__(self, other: 'DebtUnit') -> bool:
        return not self <= other
    
    def __ge__(self, other: 'DebtUnit') -> bool:
        return not self < other
    
    def __add__(self, other: 'DebtUnit') -> 'DebtUnit':
        if not isinstance(other, DebtUnit):
            return NotImplemented
        return DebtUnit(self._value + other._value)
    
    def __sub__(self, other: 'DebtUnit') -> 'DebtUnit':
        if not isinstance(other, DebtUnit):
            return NotImplemented
        result = self._value - other._value
        if result < 0:
            raise ValueError("DebtUnit subtraction would result in negative")
        return DebtUnit(result)
    
    def __mul__(self, other: 'DebtUnit') -> 'DebtUnit':
        if not isinstance(other, DebtUnit):
            return NotImplemented
        return DebtUnit(self._value * other._value)
    
    def __truediv__(self, other: 'DebtUnit') -> Fraction:
        """Division returns Fraction for intermediate computation."""
        if not isinstance(other, DebtUnit):
            return NotImplemented
        if other._value == 0:
            raise ZeroDivisionError("DebtUnit division by zero")
        return Fraction(self._value, other._value)
    
    def __pow__(self, exp: int) -> 'DebtUnit':
        """Integer power."""
        if not isinstance(exp, int):
            return NotImplemented
        if exp < 0:
            raise ValueError("DebtUnit power must be non-negative")
        return DebtUnit(self._value ** exp)
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    # Comparison with int
    def __radd__(self, other: int) -> 'DebtUnit':
        return DebtUnit(other) + self
    
    # Canonical form
    def canonical_bytes(self) -> bytes:
        """Return canonical byte representation."""
        return self._value.to_bytes((self._value.bit_length() + 8) // 8, 'big')
    
    @staticmethod
    def from_canonical_bytes(data: bytes) -> 'DebtUnit':
        """Reconstruct from canonical bytes."""
        return DebtUnit(int.from_bytes(data, 'big'))
    
    def __bool__(self) -> bool:
        """Truth value: True if non-zero."""
        return self._value != 0


# Module-level constants

ZERO = DebtUnit(0)
ONE = DebtUnit(1)


def debtunit_add(a: DebtUnit, b: DebtUnit) -> DebtUnit:
    """Deterministic addition."""
    return a + b


def debtunit_sub(a: DebtUnit, b: DebtUnit) -> DebtUnit:
    """Deterministic subtraction (with non-negativity check)."""
    return a - b


def debtunit_mul(a: DebtUnit, b: DebtUnit) -> DebtUnit:
    """Deterministic multiplication."""
    return a * b


def debtunit_div(a: DebtUnit, b: DebtUnit) -> Fraction:
    """Division returns Fraction (for intermediate computation)."""
    return a / b


def debtunit_scale(frac: Fraction, scale: int) -> DebtUnit:
    """Scale a rational to DebtUnit via half-even rounding."""
    return DebtUnit.from_fraction(frac, scale)


def debtunit_eq(a: DebtUnit, b: DebtUnit) -> bool:
    """Exact equality check."""
    return a == b


def debtunit_lt(a: DebtUnit, b: DebtUnit) -> bool:
    """Less-than check."""
    return a < b
