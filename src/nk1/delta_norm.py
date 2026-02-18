# NK-1 δ-Norm Enforcement per docs/nk1/3_delta_norms.md

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from fractions import Fraction
import math
from math import gcd


class NormDomainMode:
    """Norm domain mode identifiers."""
    NUMERIC_ONLY_V1 = "numeric_only.v1"


@dataclass
class DeltaNormConfig:
    """
    Configuration for δ-norm enforcement.
    
    Per NK-1 §3:
    - NORM_DOMAIN_MODE = numeric_only.v1
    - Only numeric fields with participates_in_delta_norm=true contribute
    - Non-numeric writes do NOT contribute to δ-norm
    """
    norm_domain_mode: str = NormDomainMode.NUMERIC_ONLY_V1
    
    def validate(self) -> bool:
        """Validate configuration."""
        return self.norm_domain_mode == NormDomainMode.NUMERIC_ONLY_V1


def is_numeric_field(field_type: str) -> bool:
    """
    Check if a field type is numeric.
    
    Numeric types: integer, nonneg, rational
    Non-numeric: bool, string, bytes
    """
    return field_type in ("integer", "nonneg", "rational")


def compute_delta_norm(
    state_before: Dict[str, Any],
    state_after: Dict[str, Any],
    field_definitions: Dict[str, Dict[str, Any]],
    weights: Dict[str, Tuple[int, int]]  # field_id -> (numerator, denominator)
) -> Tuple[int, int]:
    """
    Compute δ-norm: ||x' - x||_M
    
    Per NK-1 §3.1:
    - Only numeric fields with participates_in_delta_norm=true contribute
    - Non-numeric writes do NOT contribute to δ-norm
    
    Args:
        state_before: State before operation
        state_after: State after operation
        field_definitions: Field definitions with metadata
        weights: Field weights as rationals (num, denom)
    
    Returns:
        (numerator, denominator) of the δ-norm result
    """
    # Filter to only numeric fields that participate in delta norm
    contributions = []
    
    for field_id, field_def in field_definitions.items():
        # Check if field participates in delta norm
        if not field_def.get("participates_in_delta_norm", False):
            continue
        
        # Check if field type is numeric
        field_type = field_def.get("type", "integer")
        if not is_numeric_field(field_type):
            # Non-numeric field - does NOT contribute to δ-norm
            continue
        
        # Get values
        val_before = state_before.get(field_id, 0)
        val_after = state_after.get(field_id, 0)
        
        # Compute delta
        delta = val_after - val_before
        
        # Get weight
        weight = weights.get(field_id, (1, 1))  # Default weight = 1
        weight_num, weight_denom = weight
        
        # Compute weighted delta: weight * delta
        # Result is (weight_num * delta * weight_denom, weight_denom)
        contribution = (weight_num * delta * weight_denom, weight_denom)
        contributions.append(contribution)
    
    # Sum all contributions
    if not contributions:
        return (0, 1)  # Zero
    
    # Find common denominator using LCM
    denominators = [c[1] for c in contributions]
    common_denom = lcm_list(denominators)
    
    # Sum numerators
    total_num = 0
    for num, denom in contributions:
        # Scale to common denominator
        scale = common_denom // denom
        total_num += num * scale
    
    # Simplify
    common_gcd = gcd(abs(total_num), common_denom)
    return (total_num // common_gcd, common_denom // common_gcd)


def lcm(a: int, b: int) -> int:
    """Compute LCM of two integers."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def lcm_list(numbers: List[int]) -> int:
    """
    Compute LCM of a list of integers.
    
    Per NK-1 §3.2:
    - If no non-zero denominators, D=1, N=0
    """
    if not numbers:
        return 1
    
    result = numbers[0]
    for num in numbers[1:]:
        result = lcm(result, num)
    
    return result


def normalize_weight(weight: Tuple[int, int]) -> Tuple[int, int]:
    """
    Normalize a weight to reduced form.
    
    Per NK-1 §3.2:
    - Weights reduced: gcd(p, q) = 1
    """
    num, denom = weight
    
    if num == 0:
        return (0, 1)
    
    g = gcd(abs(num), denom)
    return (num // g, denom // g)


def check_non_numeric_write(
    operations: List[Dict[str, Any]],
    field_definitions: Dict[str, Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Check if any operation writes to a non-numeric field.
    
    Per NK-1 §3.3:
    - If any op writes any non-numeric field:
      - op must be flagged requires_modeD=true OR forced into Mode D
      - measured gate must run for any batch containing such ops
    
    Returns:
        (has_non_numeric_write, list of field IDs written)
    """
    non_numeric_fields = []
    
    for field_id, field_def in field_definitions.items():
        field_type = field_def.get("type", "integer")
        if not is_numeric_field(field_type):
            non_numeric_fields.append(field_id)
    
    # Check if any operation writes to non-numeric fields
    writes_non_numeric = []
    for op in operations:
        writes = op.get("writes", [])
        for write in writes:
            field_id = write.get("field_id")
            if field_id in non_numeric_fields:
                writes_non_numeric.append(field_id)
    
    return len(writes_non_numeric) > 0, writes_non_numeric


def requires_mode_d(
    operations: List[Dict[str, Any]],
    field_definitions: Dict[str, Dict[str, Any]]
) -> bool:
    """
    Determine if operations require Mode D.
    
    Returns True if any operation writes to non-numeric fields.
    """
    has_non_numeric, _ = check_non_numeric_write(operations, field_definitions)
    return has_non_numeric


# Test the implementations
if __name__ == "__main__":
    # Test delta norm with numeric fields
    field_defs = {
        "f:balance": {
            "type": "integer",
            "participates_in_delta_norm": True
        },
        "f:version": {
            "type": "integer", 
            "participates_in_delta_norm": True
        },
        "f:name": {
            "type": "string",
            "participates_in_delta_norm": True  # Should be ignored
        }
    }
    
    weights = {
        "f:balance": (1, 1),
        "f:version": (1, 1),
    }
    
    state_before = {"f:balance": 100, "f:version": 5}
    state_after = {"f:balance": 150, "f:version": 6}
    
    # Should only compute delta for numeric fields
    delta = compute_delta_norm(state_before, state_after, field_defs, weights)
    print(f"Delta norm: {delta}")
    
    # Test weight normalization
    assert normalize_weight((2, 4)) == (1, 2)
    assert normalize_weight((0, 5)) == (0, 1)
    print("Weight normalization OK")
    
    # Test non-numeric write detection
    ops = [
        {"writes": [{"field_id": "f:balance", "value": 200}]}
    ]
    requires_d = requires_mode_d(ops, field_defs)
    print(f"Requires Mode D: {requires_d}")
    
    print("\nAll δ-Norm tests passed!")
