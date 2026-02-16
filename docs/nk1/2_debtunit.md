# NK-1 DebtUnit Arithmetic Library

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_constants.md`](1_constants.md), [`../ck0/7_rounding_canonicalization.md`](../ck0/7_rounding_canonicalization.md)

---

## Overview

DebtUnit is the **only authoritative scalar type** in NK-1. All numeric computations in the authoritative path MUST use DebtUnit - no floats, no doubles, no floating-point arithmetic.

---

## DebtUnit Representation

### Internal Structure

```python
class DebtUnit:
    scale: int = 6          # Fixed decimal scale
    int_value: int          # Scaled integer value
    
    def __init__(self, int_value: int, scale: int = 6):
        self.int_value = int_value
        self.scale = scale
```

### Canonical Encoding

```
DebtUnit := "q:6:<signed_int>"
```

Examples:
- `DebtUnit(0)` → `"q:6:0"`
- `DebtUnit(1000000)` → `"q:6:1000000"` (represents 1.0)
- `DebtUnit(-500000)` → `"q:6:-500000"` (represents -0.5)

---

## Construction Methods

### From Integer

```python
def from_int(value: int) -> DebtUnit:
    """Create DebtUnit from integer (assumed to be already scaled)."""
    return DebtUnit(int_value=value)
```

### From Rational (p/q)

```python
def from_rational(p: int, q: int) -> DebtUnit:
    """
    Create DebtUnit from rational p/q.
    Reduces fraction first, then computes scaled int_value.
    """
    # Reduce to lowest terms
    g = gcd(abs(p), abs(q))
    p_reduced = p // g
    q_reduced = q // g
    
    # Compute scaled value with half-even rounding
    scaled_value = (p_reduced * 10**6) // q_reduced
    remainder = (p_reduced * 10**6) % q_reduced
    
    # Half-even rounding
    if remainder * 2 > q_reduced:
        scaled_value += 1
    elif remainder * 2 == q_reduced:
        # Round to even
        if scaled_value % 2 == 1:
            scaled_value += 1
    
    return DebtUnit(int_value=scaled_value)
```

### From Decimal String

```python
def from_decimal(decimal_str: str) -> DebtUnit:
    """
    Parse decimal string to DebtUnit.
    Rejects floats, scientific notation, NaN, Inf.
    """
    # Reject scientific notation
    if 'e' in decimal_str.lower():
        raise ValueError("Scientific notation not allowed")
    
    # Parse sign, integer, fractional parts
    s = decimal_str.strip()
    if s.startswith('-'):
        sign = -1
        s = s[1:]
    else:
        sign = 1
    
    if '.' in s:
        integer_part, fractional_part = s.split('.')
    else:
        integer_part = s
        fractional_part = ''
    
    # Pad or truncate fractional to 6 digits
    fractional_part = (fractional_part + '0'*6)[:6]
    
    # Combine
    int_val = sign * (int(integer_part) * 10**6 + int(fractional_part))
    return DebtUnit(int_value=int_val)
```

### From Float (Discouraged)

```python
def from_float(value: float) -> DebtUnit:
    """
    Create DebtUnit from float (discouraged - prefer rational).
    Uses half-even rounding.
    """
    if math.isnan(value) or math.isinf(value):
        raise ValueError("NaN and Inf not allowed")
    
    scaled = round_half_even(value * 10**6)
    return DebtUnit(int_value=scaled)
```

---

## Arithmetic Operations

### Addition

```python
def __add__(self, other: DebtUnit) -> DebtUnit:
    """Add two DebtUnits (must have same scale)."""
    if self.scale != other.scale:
        raise ValueError("Scale mismatch")
    return DebtUnit(int_value=self.int_value + other.int_value)

def __radd__(self, other: DebtUnit) -> DebtUnit:
    return self.__add__(other)
```

### Subtraction

```python
def __sub__(self, other: DebtUnit) -> DebtUnit:
    """Subtract two DebtUnits."""
    if self.scale != other.scale:
        raise ValueError("Scale mismatch")
    return DebtUnit(int_value=self.int_value - other.int_value)

def __rsub__(self, other: DebtUnit) -> DebtUnit:
    return DebtUnit(int_value=other.int_value - self.int_value)
```

### Multiplication by Integer

```python
def mul_int(self, multiplier: int) -> DebtUnit:
    """Multiply DebtUnit by integer."""
    return DebtUnit(int_value=self.int_value * multiplier)
```

### Division by Positive Integer

```python
def div_int(self, divisor: int) -> DebtUnit:
    """
    Divide DebtUnit by positive integer.
    Uses half-even rounding.
    """
    if divisor <= 0:
        raise ValueError("Divisor must be positive")
    
    # Compute quotient with rounding
    quotient = self.int_value // divisor
    remainder = self.int_value % divisor
    
    # Half-even rounding
    twice_remainder = remainder * 2
    if twice_remainder > divisor:
        quotient += 1
    elif twice_remainder == divisor:
        # Round to even
        if quotient % 2 == 1:
            quotient += 1
    
    return DebtUnit(int_value=quotient)
```

---

## Comparison Operations

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, DebtUnit):
        return False
    return self.int_value == other.int_value

def __lt__(self, other: DebtUnit) -> bool:
    return self.int_value < other.int_value

def __le__(self, other: DebtUnit) -> bool:
    return self.int_value <= other.int_value

def __gt__(self, other: DebtUnit) -> bool:
    return self.int_value > other.int_value

def __ge__(self, other: DebtUnit) -> bool:
    return self.int_value >= other.int_value
```

---

## Utility Functions

### Minimum/Maximum

```python
def min(a: DebtUnit, b: DebtUnit) -> DebtUnit:
    return a if a.int_value <= b.int_value else b

def max(a: DebtUnit, b: DebtUnit) -> DebtUnit:
    return a if a.int_value >= b.int_value else b
```

### Absolute Value

```python
def abs(self) -> DebtUnit:
    return DebtUnit(int_value=abs(self.int_value))
```

### Negation

```python
def __neg__(self) -> DebtUnit:
    return DebtUnit(int_value=-self.int_value)
```

---

## Nonnegativity Enforcement

NK-1 rejects negative values for required-nonnegative fields:

```python
def require_nonnegative(self, field_name: str = "value") -> None:
    """Raise ValueError if negative."""
    if self.int_value < 0:
        raise ValueError(f"{field_name} must be nonnegative, got {self}")
```

---

## Conversion Methods

### To Rational (p/q)

```python
def to_rational(self) -> tuple[int, int]:
    """Return (numerator, denominator) for exact rational representation."""
    return (self.int_value, 10**self.scale)
```

### To Decimal String

```python
def to_decimal(self) -> str:
    """Return canonical decimal string representation."""
    sign = '-' if self.int_value < 0 else ''
    abs_val = abs(self.int_value)
    
    integer_part = abs_val // 10**self.scale
    fractional_part = abs_val % 10**self.scale
    
    return f"{sign}{integer_part}.{fractional_part:06d}"
```

### To Float (For Display Only)

```python
def to_float(self) -> float:
    """Convert to float (for display/logging only, not for computation)."""
    return self.int_value / (10**self.scale)
```

---

## Canonical String Representation

```python
def canonical(self) -> str:
    """Return canonical string encoding."""
    return f"q:{self.scale}:{self.int_value}"
```

---

## Half-Even Rounding (Internal)

```python
def round_half_even(value: float) -> int:
    """Round float to nearest integer, ties to even."""
    rounded = int(value)
    frac = value - rounded
    
    if frac > 0.5:
        return rounded + 1
    elif frac < -0.5:
        return rounded - 1
    elif frac == 0.5 or frac == -0.5:
        # Round to even
        return rounded if rounded % 2 == 0 else rounded + 1
    else:
        return rounded
```

---

## Rejection Rules

The following are **rejected** by DebtUnit:

| Input | Action |
|-------|--------|
| NaN | Raise ValueError |
| ±Infinity | Raise ValueError |
| Scientific notation | Raise ValueError |
| Negative (when nonnegative required) | Raise ValueError |
| Different scales in operation | Raise ValueError |

---

## Implementation Notes

1. **No floats in authoritative path**: All V(x) computations, gate decisions, and receipt values use DebtUnit
2. **Deterministic**: Same inputs → same outputs, guaranteed
3. **Overflow**: Use Python's arbitrary-precision integers (no overflow in practice)
4. **Serialization**: Always canonical string form for hashes

---

*See also: [`3_contracts.md`](3_contracts.md), [`../ck0/7_rounding_canonicalization.md`](../ck0/7_rounding_canonicalization.md)*
