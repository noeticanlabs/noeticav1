# NK-1 StateCanon: sorted_json_bytes.v1 per docs/nk1/1_canon.md

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import hashlib
import unicodedata

from ck0.state_space import State, FieldBlock, FieldDef, FieldType
from .value_canon import ValueCanon, canon_field_value


CANON_ID = "sorted_json_bytes.v1"


@dataclass
class StateMeta:
    """
    State metadata - EXCLUDED from canonical bytes and hash.
    
    Per NK-1 §1.1:
    - meta is excluded from canon_bytes and state_hash
    - Used for timestamps, provenance, debugging info
    """
    timestamp: Optional[str] = None
    provenance: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class StateCanon:
    """
    Canonical state serialization per NK-1 §1.2.
    
    Root layout:
    {
        "canon_id": "sorted_json_bytes.v1",
        "schema_id": "...",
        "float_policy": "...",
        "fields": [["<FieldID>", <ValueCanon>], ...]
    }
    
    - fields is an ARRAY OF PAIRS, sorted lexicographically by FieldID byte encoding
    - UTF-8, no whitespace, stable numeric formatting
    - Strings NFC normalized
    """
    
    def __init__(
        self,
        schema_id: str = "",
        float_policy: str = "reject"
    ):
        self.schema_id = schema_id
        self.float_policy = float_policy
    
    def canon_state(self, state: State, meta: Optional[StateMeta] = None) -> bytes:
        """
        Generate canonical bytes for a state.
        
        Per NK-1 §1.2:
        - meta is EXCLUDED from canonical bytes
        - fields sorted by FieldID bytes
        - UTF-8, no whitespace
        """
        # Build canonical structure
        # Sort fields by FieldID bytes
        sorted_fields = []
        
        for block in state.field_blocks:
            for field_def in block.fields:
                field_id = field_def.field_id
                value = state._field_values.get(field_id)
                
                if value is not None:
                    # Canon the value based on field type
                    canon_value = canon_field_value(field_def.field_type.value, value)
                    sorted_fields.append([field_id, canon_value])
        
        # Sort by FieldID bytes
        sorted_fields.sort(key=lambda x: x[0].encode('utf-8'))
        
        # Build canonical JSON
        canonical = {
            "canon_id": CANON_ID,
            "schema_id": self.schema_id,
            "float_policy": self.float_policy,
            "fields": sorted_fields
        }
        
        # Compact JSON with sorted keys - no whitespace
        return json.dumps(canonical, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    def state_hash(self, state: State, meta: Optional[StateMeta] = None) -> str:
        """
        Compute canonical state hash.
        
        Returns h:<hex> format.
        """
        canon_bytes = self.canon_state(state, meta)
        return 'h:' + hashlib.sha3_256(canon_bytes).hexdigest()
    
    def verify_canon_bytes(
        self,
        state: State,
        expected_canon_bytes: bytes,
        meta: Optional[StateMeta] = None
    ) -> Tuple[bool, str]:
        """
        Verify canon_bytes match expected.
        
        Returns (is_valid, error_message).
        """
        actual = self.canon_state(state, meta)
        
        if actual == expected_canon_bytes:
            return True, ""
        
        # Provide detailed error
        return False, f"Canon bytes mismatch: expected {expected_canon_bytes!r}, got {actual!r}"
    
    def verify_hash(
        self,
        state: State,
        expected_hash: str,
        meta: Optional[StateMeta] = None
    ) -> Tuple[bool, str]:
        """
        Verify state_hash matches expected.
        
        Returns (is_valid, error_message).
        """
        actual_hash = self.state_hash(state, meta)
        
        if actual_hash == expected_hash:
            return True, ""
        
        return False, f"Hash mismatch: expected {expected_hash}, got {actual_hash}"


def create_state_with_meta(
    schema_id: str,
    field_blocks: List[FieldBlock],
    field_values: Dict[str, Any],
    meta: Optional[StateMeta] = None
) -> Tuple[State, str, str]:
    """
    Create a state and return (state, canon_bytes, state_hash).
    
    This is the main entry point for creating canonically hashed states.
    """
    state = State(
        field_blocks=field_blocks,
        _field_values=field_values
    )
    
    canon = StateCanon(schema_id=schema_id)
    canon_bytes = canon.canon_state(state, meta)
    state_hash = canon.state_hash(state, meta)
    
    return state, canon_bytes, state_hash


# Test the StateCanon implementation
if __name__ == "__main__":
    from ck0.state_space import FieldBlock, FieldDef, FieldType
    
    # Create test fields
    field_blocks = [
        FieldBlock(
            block_id="block:public",
            fields=[
                FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                FieldDef("f:00000000000000000000000000000002", FieldType.STRING),
            ],
            access_policy="public"
        )
    ]
    
    state = State(
        field_blocks=field_blocks,
        _field_values={
            "f:00000000000000000000000000000001": 100,
            "f:00000000000000000000000000000002": "hello",
        }
    )
    
    canon = StateCanon(schema_id="id:schema.test")
    canon_bytes = canon.canon_state(state)
    state_hash = canon.state_hash(state)
    
    print(f"Canon ID: {CANON_ID}")
    print(f"Canon bytes: {canon_bytes}")
    print(f"State hash: {state_hash}")
    
    # Verify fields are sorted
    parsed = json.loads(canon_bytes.decode('utf-8'))
    assert parsed["canon_id"] == CANON_ID
    assert len(parsed["fields"]) == 2
    # First field ID should be less than second
    assert parsed["fields"][0][0] < parsed["fields"][1][0]
    
    print("All StateCanon tests passed!")
