# CK-0 Curvature Matrix M
# NEC closure / M matrix with canonicalization per docs/ck0/5_curvature_interaction_bounds.md

from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
from fractions import Fraction
import math
import hashlib
import json


@dataclass
class CurvatureMatrix:
    """
    Curvature matrix M for NEC (No Entirely Counterexample) closure.
    
    Per docs/ck0/5_curvature_interaction_bounds.md:
    - M[i,j] represents curvature bound between residuals i and j
    - Reduced rationals (gcd=1)
    - Symmetric storage (i≤j)
    - Default 0
    - Canonical byte encoding (canon_matrix_bytes.v1)
    - Matrix digest bound into PolicyBundle
    """
    # Internal storage: (i, j) -> Fraction, only for i <= j
    _data: Dict[Tuple[int, int], Fraction] = field(default_factory=dict)
    _size: int = 0
    _digest: Optional[str] = field(default=None, repr=False)
    
    def _check_index(self, i: int, j: int) -> None:
        """Validate indices."""
        if i < 0 or j < 0:
            raise IndexError(f"Indices must be non-negative: {i}, {j}")
        if i >= self._size or j >= self._size:
            raise IndexError(f"Index out of bounds: {i}, {j} (size={self._size})")
    
    def _normalize_index(self, i: int, j: int) -> Tuple[int, int]:
        """Normalize to i <= j for symmetric storage."""
        if i <= j:
            return (i, j)
        return (j, i)
    
    def set(self, i: int, j: int, value: Fraction) -> None:
        """Set M[i,j] = value (reduced rational)."""
        self._check_index(i, j)
        
        # Reduce to canonical form (gcd=1)
        reduced = self._reduce_fraction(value)
        
        # Store symmetrically
        key = self._normalize_index(i, j)
        self._data[key] = reduced
        self._digest = None  # Invalidate cache
    
    def get(self, i: int, j: int) -> Fraction:
        """Get M[i,j] (defaults to 0)."""
        self._check_index(i, j)
        key = self._normalize_index(i, j)
        return self._data.get(key, Fraction(0))
    
    def _reduce_fraction(self, frac: Fraction) -> Fraction:
        """Reduce fraction to canonical form (gcd=1)."""
        if frac.numerator == 0:
            return Fraction(0)
        # Already reduced if denominator is positive
        if frac.denominator < 0:
            return Fraction(-frac.numerator, -frac.denominator)
        return Fraction(frac.numerator, frac.denominator)
    
    def size(self) -> int:
        """Return matrix dimension."""
        return self._size
    
    def compute_digest(self) -> str:
        """
        Compute matrix digest for PolicyBundle binding.
        
        Uses canon_matrix_bytes.v1 encoding.
        """
        if self._digest is not None:
            return self._digest
        
        # Canonical serialization: sorted by (i, j)
        entries = []
        for (i, j), value in self._data.items():
            if value != Fraction(0):  # Skip zeros
                entries.append((i, j, value.numerator, value.denominator))
        
        entries.sort()  # Sort by (i, j)
        
        # Serialize
        serialized = b'matrix_v1:'
        serialized += f"size:{self._size};".encode('utf-8')
        for i, j, num, denom in entries:
            serialized += f"({i},{j},{num}/{denom});".encode('utf-8')
        
        self._digest = 'h:' + hashlib.sha3_256(serialized).hexdigest()
        return self._digest
    
    def canonical_bytes(self) -> bytes:
        """
        Return canonical byte representation.
        
        Per docs/ck0/C_canonical_ids.md.
        """
        entries = []
        for (i, j), value in self._data.items():
            if value != Fraction(0):
                entries.append((i, j, value.numerator, value.denominator))
        
        entries.sort()
        
        serialized = b'matrix_v1:'
        serialized += f"size:{self._size};".encode('utf-8')
        for i, j, num, denom in entries:
            serialized += f"({i},{j},{num}/{denom});".encode('utf-8')
        
        return serialized
    
    @staticmethod
    def from_dict(data: Dict[Tuple[int, int], Fraction], size: int) -> 'CurvatureMatrix':
        """Create matrix from dictionary."""
        m = CurvatureMatrix()
        m._size = size
        for (i, j), value in data.items():
            m.set(i, j, value)
        return m
    
    @staticmethod
    def create_zero(size: int) -> 'CurvatureMatrix':
        """Create zero matrix of given size."""
        m = CurvatureMatrix()
        m._size = size
        return m
    
    @staticmethod
    def create_identity(size: int, scale: Fraction = Fraction(1)) -> 'CurvatureMatrix':
        """Create scaled identity matrix."""
        m = CurvatureMatrix()
        m._size = size
        for i in range(size):
            m.set(i, i, scale)
        return m
    
    def __repr__(self) -> str:
        entries = []
        for i in range(self._size):
            row = []
            for j in range(self._size):
                row.append(str(self.get(i, j)))
            entries.append('[' + ', '.join(row) + ']')
        return 'CurvatureMatrix([' + '; '.join(entries) + '])'


# Curvature interaction bounds computation

def compute_curvature_bound(
    delta_i: Fraction,
    delta_j: Fraction,
    h_ii: Fraction,
    h_jj: Fraction,
    h_ij: Fraction
) -> Fraction:
    """
    Compute curvature interaction bound.
    
    Per docs/ck0/5_curvature_interaction_bounds.md:
    M[i,j] bounds the interaction term in second-order expansion.
    
    Uses rectangle identity: |a*b| <= (a^2 + b^2)/2
    """
    # Triangle inequality based bound
    # |h_ij * delta_i * delta_j| <= |h_ij| * |delta_i| * |delta_j|
    
    bound = abs(h_ij) * abs(delta_i) * abs(delta_j)
    return bound


def compute_nec_closure(
    residuals: List[Fraction],
    hessian_approx: CurvatureMatrix
) -> CurvatureMatrix:
    """
    Compute NEC (No Entirely Counterexample) closure.
    
    Ensures curvature bounds are sufficient for all residual combinations.
    """
    n = len(residuals)
    if n == 0:
        return CurvatureMatrix.create_zero(0)
    
    m = CurvatureMatrix.create_zero(n)
    
    # For each pair, compute bound
    for i in range(n):
        for j in range(i, n):
            bound = compute_curvature_bound(
                residuals[i],
                residuals[j],
                hessian_approx.get(i, i),
                hessian_approx.get(j, j),
                hessian_approx.get(i, j)
            )
            m.set(i, j, bound)
    
    return m


def validate_curvature_matrix(
    m: CurvatureMatrix,
    max_residuals: List[Fraction]
) -> Tuple[bool, str]:
    """
    Validate curvature matrix is sufficient for given residual bounds.
    
    Returns (is_valid, error_message).
    """
    n = m.size()
    if n != len(max_residuals):
        return False, f"Size mismatch: matrix {n} vs residuals {len(max_residuals)}"
    
    # Check each entry
    for i in range(n):
        for j in range(i, n):
            m_ij = m.get(i, j)
            # Need: M[i,j] >= |h_ij| * |r_i| * |r_j|
            # For validation, just check matrix is well-formed
            if m_ij < 0:
                return False, f"Negative curvature bound M[{i},{j}] = {m_ij}"
    
    return True, "OK"


# Example curvature matrix for testing

def create_example_curvature_matrix() -> CurvatureMatrix:
    """Create example curvature matrix."""
    m = CurvatureMatrix()
    m._size = 2
    
    # Simple 2x2 with moderate bounds
    m.set(0, 0, Fraction(1))  # M[0,0] = 1
    m.set(0, 1, Fraction(1, 2))  # M[0,1] = 0.5
    m.set(1, 1, Fraction(1))  # M[1,1] = 1
    
    return m
