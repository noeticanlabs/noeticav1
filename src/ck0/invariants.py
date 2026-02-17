# CK-0 Invariants: Hard Constraint Checking

from typing import List, Callable, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from .state_space import State, FieldBlock, FieldDef, FieldType


class InvariantCategory(Enum):
    """Categories of invariants per docs/ck0/2_invariants.md."""
    STATE_STRUCTURE = "state_structure"      # Schema conformance
    FIELD_RANGE = "field_range"               # Value bounds
    CROSS_FIELD = "cross_field"               # Multi-field constraints
    TEMPORAL = "temporal"                     # Time-series constraints
    SECURITY = "security"                     # Access control


@dataclass
class Invariant:
    """
    A hard invariant that must hold at all times.
    
    Per docs/ck0/2_invariants.md:
    - Hard invariants I(x) are non-negotiable
    - Violation means system is incoherent
    - No "soft" fallback - either holds or doesn't
    """
    invariant_id: str
    name: str
    category: InvariantCategory
    description: str
    check_fn: Callable[[State], Tuple[bool, str]]  # (passes, message)
    
    def evaluate(self, state: State) -> Tuple[bool, str]:
        """Evaluate invariant on state."""
        try:
            return self.check_fn(state)
        except Exception as e:
            return False, f"Invariant check raised exception: {e}"


@dataclass
class InvariantSet:
    """
    Collection of invariants that must all hold.
    """
    invariants: List[Invariant] = field(default_factory=list)
    
    def add(self, invariant: Invariant) -> 'InvariantSet':
        """Add invariant to set."""
        self.invariants.append(invariant)
        return self
    
    def evaluate_all(self, state: State) -> Tuple[bool, Dict[str, str]]:
        """
        Evaluate all invariants.
        
        Returns (all_pass, {invariant_id: failure_message})
        """
        failures = {}
        for inv in self.invariants:
            passed, msg = inv.evaluate(state)
            if not passed:
                failures[inv.invariant_id] = msg
        
        return len(failures) == 0, failures
    
    def check_strict(self, state: State) -> None:
        """
        Strict check - raises if any invariant fails.
        
        Per CK-0: hard invariants are non-negotiable.
        """
        all_pass, failures = self.evaluate_all(state)
        if not all_pass:
            failure_msgs = "; ".join(f"{k}: {v}" for k, v in failures.items())
            raise InvariantViolationError(f"Hard invariant violation: {failure_msgs}")


class InvariantViolationError(Exception):
    """Raised when a hard invariant is violated."""
    pass


# Standard invariant constructors

def field_range_invariant(
    field_id: str,
    min_val: int = None,
    max_val: int = None,
    name: str = None
) -> Invariant:
    """Create a field range invariant."""
    inv_id = f"inv:range:{field_id}"
    
    def check(state: State) -> Tuple[bool, str]:
        val = state.get_field(field_id)
        if val is None:
            return False, f"Field {field_id} not set"
        
        if min_val is not None and val < min_val:
            return False, f"Field {field_id} = {val} < minimum {min_val}"
        
        if max_val is not None and val > max_val:
            return False, f"Field {field_id} = {val} > maximum {max_val}"
        
        return True, "OK"
    
    return Invariant(
        invariant_id=inv_id,
        name=name or f"Range check for {field_id}",
        category=InvariantCategory.FIELD_RANGE,
        description=f"Ensure {field_id} is in range [{min_val}, {max_val}]",
        check_fn=check
    )


def non_negative_invariant(field_id: str) -> Invariant:
    """Create a non-negativity invariant."""
    return field_range_invariant(field_id, min_val=0, name=f"Non-negative: {field_id}")


def state_schema_invariant(field_blocks: List[FieldBlock]) -> Invariant:
    """Create a state schema conformance invariant."""
    inv_id = "inv:schema:conformance"
    required_fields = set()
    for block in field_blocks:
        for field in block.fields:
            required_fields.add(field.field_id)
    
    def check(state: State) -> Tuple[bool, str]:
        # Check all required fields present
        for field_id in required_fields:
            if state.get_field(field_id) is None:
                return False, f"Missing required field: {field_id}"
        return True, "OK"
    
    return Invariant(
        invariant_id=inv_id,
        name="State schema conformance",
        category=InvariantCategory.STATE_STRUCTURE,
        description="All required fields must be present",
        check_fn=check
    )


def cross_field_invariant(
    name: str,
    fields: List[str],
    check_fn: Callable[[Dict[str, Any]], Tuple[bool, str]]
) -> Invariant:
    """Create a cross-field invariant."""
    import hashlib
    inv_id = f"inv:cross:{hashlib.sha256(name.encode()).hexdigest()[:16]}"
    
    def check(state: State) -> Tuple[bool, str]:
        field_values = {}
        for field_id in fields:
            val = state.get_field(field_id)
            if val is None:
                return False, f"Field {field_id} not set"
            field_values[field_id] = val
        
        return check_fn(field_values)
    
    return Invariant(
        invariant_id=inv_id,
        name=name,
        category=InvariantCategory.CROSS_FIELD,
        description=f"Cross-field constraint: {name}",
        check_fn=check
    )


# Example: Balance invariant
def balance_invariant(
    total_field: str,
    available_field: str,
    reserved_field: str
) -> Invariant:
    """Total = Available + Reserved"""
    return cross_field_invariant(
        f"Balance: {total_field} = {available_field} + {reserved_field}",
        [total_field, available_field, reserved_field],
        lambda vals: (
            vals[total_field] == vals[available_field] + vals[reserved_field],
            f"Balance violated: {vals[total_field]} != {vals[available_field]} + {vals[reserved_field]}"
        )
    )


def create_core_invariants(field_blocks: List[FieldBlock]) -> InvariantSet:
    """Create the standard set of core invariants."""
    invariant_set = InvariantSet()
    
    # Always add schema conformance
    invariant_set.add(state_schema_invariant(field_blocks))
    
    # Add non-negativity for all non-negative integer fields
    for block in field_blocks:
        for field in block.fields:
            if field.field_type == FieldType.NONNEG_INT:
                invariant_set.add(non_negative_invariant(field.field_id))
    
    return invariant_set
