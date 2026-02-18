# NK-1 Curvature Matrix Registry per docs/nk1/5_curvature.md

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import hashlib
from fractions import Fraction
from math import gcd


CANON_MATRIX_ID = "curvature_matrix.v1"


def reduce_fraction(num: int, denom: int) -> Tuple[int, int]:
    """Reduce a fraction to simplest form."""
    if denom == 0:
        raise ValueError("Denominator cannot be zero")
    if num == 0:
        return (0, 1)
    
    g = gcd(abs(num), abs(denom))
    num //= g
    denom //= g
    
    # Ensure denominator is positive
    if denom < 0:
        num = -num
        denom = -denom
    
    return (num, denom)


@dataclass
class CurvatureMatrix:
    """
    Curvature matrix M per NK-1 §5.
    
    Per spec:
    - Store entries for i≤j only (upper triangle)
    - Symmetry fill: M_ij = M_ji
    - Missing entry defaults to 0
    - Reduced rationals enforced
    - Digest binds matrix bytes exactly
    """
    dimension: int
    entries: Dict[Tuple[int, int], Tuple[int, int]] = field(default_factory=dict)
    _digest: Optional[str] = field(default=None, repr=False)
    
    def set_entry(self, i: int, j: int, numerator: int, denominator: int = 1) -> None:
        """
        Set matrix entry at (i, j).
        
        Per NK-1 §5.1: Store for i≤j only (upper triangle).
        """
        if i < 0 or j < 0:
            raise ValueError("Indices must be non-negative")
        if i >= self.dimension or j >= self.dimension:
            raise ValueError(f"Index out of bounds: dimension={self.dimension}")
        
        # Store upper triangle only
        ri, rj = min(i, j), max(i, j)
        
        # Reduce fraction
        num, denom = reduce_fraction(numerator, denominator)
        self.entries[(ri, rj)] = (num, denom)
        
        # Invalidate digest
        self._digest = None
    
    def get_entry(self, i: int, j: int) -> Tuple[int, int]:
        """
        Get matrix entry at (i, j).
        
        Per NK-1 §5.1: Missing entry defaults to 0.
        """
        ri, rj = min(i, j), max(i, j)
        return self.entries.get((ri, rj), (0, 1))
    
    def to_canonical_bytes(self) -> bytes:
        """
        Serialize matrix to canonical bytes.
        
        Per NK-1 §5.1:
        - Entries sorted by (i, j) key
        - Compact JSON, sorted keys
        """
        # Build canonical structure
        data = {
            "canon_id": CANON_MATRIX_ID,
            "dimension": self.dimension,
            "entries": []
        }
        
        # Sort entries by (i, j)
        sorted_keys = sorted(self.entries.keys(), key=lambda x: (x[0], x[1]))
        
        for (i, j) in sorted_keys:
            num, denom = self.entries[(i, j)]
            data["entries"].append({
                "i": i,
                "j": j,
                "n": num,
                "d": denom
            })
        
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    def compute_digest(self) -> str:
        """
        Compute matrix digest.
        
        Per NK-1 §5.1: Digest binds matrix bytes exactly.
        """
        if self._digest is not None:
            return self._digest
        
        canon_bytes = self.to_canonical_bytes()
        self._digest = 'h:' + hashlib.sha3_256(canon_bytes).hexdigest()
        return self._digest
    
    @staticmethod
    def from_canonical_bytes(data: bytes) -> 'CurvatureMatrix':
        """Deserialize from canonical bytes."""
        parsed = json.loads(data.decode('utf-8'))
        
        matrix = CurvatureMatrix(dimension=parsed["dimension"])
        
        for entry in parsed.get("entries", []):
            i = entry["i"]
            j = entry["j"]
            n = entry["n"]
            d = entry["d"]
            matrix.set_entry(i, j, n, d)
        
        return matrix
    
    def to_rational_matrix(self) -> List[List[float]]:
        """Convert to rational matrix (for computation)."""
        result = []
        for i in range(self.dimension):
            row = []
            for j in range(self.dimension):
                num, denom = self.get_entry(i, j)
                row.append(num / denom if denom != 0 else 0)
            result.append(row)
        return result


class CurvatureMatrixRegistry:
    """
    Registry for curvature matrices per NK-1 §5.
    
    Manages multiple matrix versions with digests.
    """
    
    def __init__(self):
        self.matrices: Dict[str, CurvatureMatrix] = {}
        self._latest_digest: Optional[str] = None
    
    def register(self, matrix_id: str, matrix: CurvatureMatrix) -> str:
        """Register a matrix and return its digest."""
        digest = matrix.compute_digest()
        self.matrices[matrix_id] = matrix
        self._latest_digest = digest
        return digest
    
    def get(self, matrix_id: str) -> Optional[CurvatureMatrix]:
        """Get matrix by ID."""
        return self.matrices.get(matrix_id)
    
    def get_by_digest(self, digest: str) -> Optional[CurvatureMatrix]:
        """Get matrix by digest."""
        for matrix in self.matrices.values():
            if matrix.compute_digest() == digest:
                return matrix
        return None
    
    def latest_digest(self) -> Optional[str]:
        """Get latest registered matrix digest."""
        return self._latest_digest


# Test implementations
if __name__ == "__main__":
    # Test reduce fraction
    assert reduce_fraction(2, 4) == (1, 2)
    assert reduce_fraction(-2, 4) == (-1, 2)
    assert reduce_fraction(0, 5) == (0, 1)
    print("Fraction reduction OK")
    
    # Test matrix
    matrix = CurvatureMatrix(dimension=3)
    matrix.set_entry(0, 0, 1)  # M[0,0] = 1
    matrix.set_entry(0, 1, 1, 2)  # M[0,1] = 0.5
    matrix.set_entry(1, 2, 3)  # M[1,2] = 3
    
    # Test symmetry fill
    assert matrix.get_entry(1, 0) == matrix.get_entry(0, 1)  # Same as (0,1)
    assert matrix.get_entry(2, 1) == matrix.get_entry(1, 2)  # Same as (1,2)
    print("Symmetry fill OK")
    
    # Test missing entry defaults to 0
    assert matrix.get_entry(2, 0) == (0, 1)
    print("Missing entry default OK")
    
    # Test canonical bytes
    canon_bytes = matrix.to_canonical_bytes()
    print(f"Canonical bytes: {canon_bytes}")
    
    # Test digest
    digest = matrix.compute_digest()
    print(f"Matrix digest: {digest}")
    
    # Test registry
    registry = CurvatureMatrixRegistry()
    registry.register("matrix_001", matrix)
    assert registry.latest_digest() == digest
    print("Registry OK")
    
    print("\nAll curvature matrix tests passed!")
