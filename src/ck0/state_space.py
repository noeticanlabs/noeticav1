# CK-0 State Space: Typed State Representation

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# Type definitions following docs/ck0/1_state_space.md

class FieldType(Enum):
    """Field types in CK-0 state space."""
    INTEGER = "integer"      # ℤ - arbitrary precision integer
    NONNEG_INT = "nonneg"   # ℤ_{≥0} - non-negative integer
    RATIONAL = "rational"   # ℚ - rational number
    BOOLEAN = "bool"        # Boolean
    STRING = "string"       # Unicode string
    BYTES = "bytes"         # Byte array
    FIELD_REF = "field_ref" # Reference to another field


@dataclass
class FieldDef:
    """Definition of a field in the state space."""
    field_id: str           # f:<hex_fixedlen> per docs/ck0/C_canonical_ids.md
    field_type: FieldType
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Validate field_id format
        if not self.field_id.startswith("f:"):
            raise ValueError(f"FieldID must start with 'f:', got {self.field_id}")
        hex_part = self.field_id[2:]
        if len(hex_part) != 32:  # 16 bytes = 32 hex chars
            raise ValueError(f"FieldID must be 32 hex chars, got {len(hex_part)}")


@dataclass
class FieldBlock:
    """A collection of fields with same access policy."""
    block_id: str
    fields: List[FieldDef]
    access_policy: str  # e.g., "public", "private", "kernel_only"
    
    def __post_init__(self):
        # Sort fields by FieldID for canonical ordering (per docs/ck0/D_sorting_rules.md)
        self.fields = sorted(self.fields, key=lambda f: f.field_id)


@dataclass 
class State:
    """
    CK-0 state representation.
    
    INVARIANTS:
    - All field values must match their field type constraints
    - Field IDs must be valid per canonical ID rules
    - State is immutable after construction
    """
    field_blocks: List[FieldBlock] = field(default_factory=list)
    _field_values: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False)
    
    def get_field(self, field_id: str) -> Any:
        """Get field value by FieldID."""
        return self._field_values.get(field_id)
    
    def set_field(self, field_id: str, value: Any) -> 'State':
        """Return new State with updated field (immutable)."""
        if field_id not in self._field_values:
            raise KeyError(f"Unknown field: {field_id}")
        
        new_state = State(
            field_blocks=self.field_blocks,
            _field_values=dict(self._field_values),
            _hash=None  # Invalidate cache
        )
        new_state._field_values[field_id] = value
        return new_state
    
    def with_fields(self, updates: Dict[str, Any]) -> 'State':
        """Return new State with multiple updated fields (immutable)."""
        new_state = State(
            field_blocks=self.field_blocks,
            _field_values=dict(self._field_values),
            _hash=None
        )
        for field_id, value in updates.items():
            if field_id not in new_state._field_values:
                raise KeyError(f"Unknown field: {field_id}")
            new_state._field_values[field_id] = value
        return new_state
    
    def state_hash(self) -> str:
        """
        Compute canonical state hash.
        
        Uses hash_canon.v1 per NK-1 spec.
        """
        if self._hash is not None:
            return self._hash
        
        # Canonical serialization: sorted fields by ID
        canonical_fields = []
        for block in self.field_blocks:
            for field in block.fields:
                value = self._field_values.get(field.field_id)
                if value is not None:
                    canonical_fields.append((field.field_id, value))
        
        # Sort by field_id bytes (deterministic)
        canonical_fields.sort(key=lambda x: x[0].encode('utf-8'))
        
        # Serialize
        serialized = b'state_v1:'
        for field_id, value in canonical_fields:
            serialized += field_id.encode('utf-8') + b':' + repr(value).encode('utf-8') + b';'
        
        self._hash = 'h:' + hashlib.sha3_256(serialized).hexdigest()
        return self._hash
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate state against field definitions.
        
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Check all required fields have values
        for block in self.field_blocks:
            for field in block.fields:
                if field.field_id not in self._field_values:
                    errors.append(f"Missing required field: {field.field_id}")
        
        # Validate field types
        for field_id, value in self._field_values.items():
            # Find field definition
            field_def = None
            for block in self.field_blocks:
                for f in block.fields:
                    if f.field_id == field_id:
                        field_def = f
                        break
            
            if field_def is None:
                errors.append(f"Unknown field in state: {field_id}")
                continue
            
            # Type checking
            if not self._check_type(value, field_def.field_type):
                errors.append(f"Field {field_id} has wrong type: expected {field_def.field_type.value}")
        
        return len(errors) == 0, errors
    
    def _check_type(self, value: Any, field_type: FieldType) -> bool:
        """Check if value matches field type."""
        if field_type == FieldType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        elif field_type == FieldType.NONNEG_INT:
            return isinstance(value, int) and not isinstance(value, bool) and value >= 0
        elif field_type == FieldType.RATIONAL:
            return isinstance(value, tuple) and len(value) == 2  # (num, denom)
        elif field_type == FieldType.BOOLEAN:
            return isinstance(value, bool)
        elif field_type == FieldType.STRING:
            return isinstance(value, str)
        elif field_type == FieldType.BYTES:
            return isinstance(value, bytes)
        elif field_type == FieldType.FIELD_REF:
            return isinstance(value, str) and value.startswith('f:')
        return False
    
    @staticmethod
    def canonical_sort(items: List[str]) -> List[str]:
        """
        Sort items by raw UTF-8 bytes per docs/ck0/D_sorting_rules.md.
        
        This is the canonical sorting algorithm for all ordered collections.
        """
        return sorted(items, key=lambda x: x.encode('utf-8'))
    
    @staticmethod
    def from_dict(data: Dict[str, Any], field_blocks: List[FieldBlock]) -> 'State':
        """Construct State from dictionary."""
        state = State(field_blocks=field_blocks, _field_values=data)
        return state


def create_example_state() -> State:
    """Create an example state for testing."""
    field_blocks = [
        FieldBlock(
            block_id="block:public",
            fields=[
                FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                FieldDef("f:00000000000000000000000000000002", FieldType.NONNEG_INT),
            ],
            access_policy="public"
        )
    ]
    
    return State(
        field_blocks=field_blocks,
        _field_values={
            "f:00000000000000000000000000000001": 100,
            "f:00000000000000000000000000000002": 200,
        }
    )
