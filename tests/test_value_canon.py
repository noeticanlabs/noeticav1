# Tests for NK-1 ValueCanon and StateCanon

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.value_canon import ValueCanon, canon_field_value
from nk1.state_canon import StateCanon, StateMeta, CANON_ID
from ck0.state_space import State, FieldBlock, FieldDef, FieldType


class TestValueCanon(unittest.TestCase):
    """Tests for ValueCanon type tagging."""
    
    def test_integer_tag(self):
        """Test i: tag for integers."""
        assert ValueCanon.canon(42) == "i:42"
        assert ValueCanon.canon(0) == "i:0"
        assert ValueCanon.canon(-100) == "i:-100"
    
    def test_type_confusion_prevention(self):
        """Test that i:1 ≠ s:1 ≠ q:0:1 per spec."""
        assert ValueCanon.canon(1) == "i:1"
        assert ValueCanon.canon("1") == "s:1"
        assert ValueCanon.canon((1, 1)) == "q:1:1"  # rational 1/1 = 1
        # These must be different!
        assert ValueCanon.canon(1) != ValueCanon.canon("1")
    
    def test_string_nfc_normalization(self):
        """Test NFC normalization for strings."""
        # NFC composed form
        assert ValueCanon.canon("café") == "s:café"
        
        # Different Unicode forms should produce same canonical form
        # NFC vs NFD for 'e' + combining acute
        composed = "café"  # é as single codepoint
        decomposed = "cafe\u0301"  # e + combining acute
        
        assert ValueCanon.canon(composed) == ValueCanon.canon(decomposed)
    
    def test_bytes_b64_encoding(self):
        """Test b64: tag for bytes."""
        result = ValueCanon.canon(b"hello")
        assert result.startswith("b64:")
        
        # Round-trip
        parsed = ValueCanon.parse(result)
        assert parsed == b"hello"
    
    def test_bool_not_int(self):
        """Test that bool is distinguished from int."""
        result = ValueCanon.canon(True)
        # Should be tagged differently than int
        assert result != "i:1"
        
        result = ValueCanon.canon(False)
        assert result != "i:0"
    
    def test_rational_fixed_point(self):
        """Test q: scale:int format for rationals."""
        # 1/2 = 0.5
        result = ValueCanon.canon((1, 2))
        assert result.startswith("q:2:1")  # scale:num = 2:1
        
        # 3/4 = 0.75
        result = ValueCanon.canon((3, 4))
        assert result.startswith("q:4:3")
    
    def test_list_preserves_order(self):
        """Test that lists preserve order."""
        result = ValueCanon.canon([1, 2, 3])
        assert result == ["i:1", "i:2", "i:3"]
    
    def test_parse_roundtrip(self):
        """Test parse round-trip for all types."""
        # Integer
        assert ValueCanon.parse("i:42") == 42
        
        # String
        assert ValueCanon.parse("s:hello") == "hello"
        
        # Bytes
        result = ValueCanon.parse("b64:aGVsbG8")
        assert result == b"hello"


class TestCanonFieldValue(unittest.TestCase):
    """Tests for canon_field_value helper."""
    
    def test_integer_type(self):
        assert canon_field_value("integer", 42) == "i:42"
    
    def test_nonneg_type(self):
        assert canon_field_value("nonneg", 100) == "i:100"
    
    def test_rational_type(self):
        result = canon_field_value("rational", (3, 4))
        assert result == "q:4:3"
    
    def test_bool_type(self):
        assert canon_field_value("bool", True) == "true"
        assert canon_field_value("bool", False) == "false"
    
    def test_string_type(self):
        result = canon_field_value("string", "test")
        assert result == "s:test"
        # NFC normalization
        result = canon_field_value("string", "café")
        assert "café" in result


class TestStateCanon(unittest.TestCase):
    """Tests for StateCanon sorted_json_bytes.v1."""
    
    def test_canon_id(self):
        """Test canonical ID is correct."""
        assert CANON_ID == "sorted_json_bytes.v1"
    
    def test_fields_sorted_by_fieldid(self):
        """Test fields are sorted by FieldID bytes."""
        field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000002", FieldType.NONNEG_INT),
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
        
        state = State(
            field_blocks=field_blocks,
            _field_values={
                "f:00000000000000000000000000000001": 100,
                "f:00000000000000000000000000000002": 200,
            }
        )
        
        canon = StateCanon(schema_id="id:schema.test")
        canon_bytes = canon.canon_state(state)
        
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        
        # Fields should be sorted
        fields = parsed["fields"]
        assert len(fields) == 2
        assert fields[0][0] < fields[1][0]  # First FieldID < second FieldID
    
    def test_meta_excluded_from_bytes(self):
        """Test that meta is excluded from canonical bytes."""
        field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
        
        state = State(
            field_blocks=field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        
        # With meta
        meta = StateMeta(timestamp="2024-01-01T00:00:00Z", provenance="test")
        
        canon = StateCanon(schema_id="id:schema.test")
        
        # Both should produce same bytes (meta excluded)
        bytes_with_meta = canon.canon_state(state, meta)
        bytes_without_meta = canon.canon_state(state, None)
        
        assert bytes_with_meta == bytes_without_meta
    
    def test_schema_id_in_canon(self):
        """Test schema_id is included in canonical bytes."""
        field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
        
        state = State(
            field_blocks=field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        
        canon = StateCanon(schema_id="id:schema.myapp")
        canon_bytes = canon.canon_state(state)
        
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        
        assert parsed["schema_id"] == "id:schema.myapp"
        assert parsed["canon_id"] == "sorted_json_bytes.v1"
    
    def test_hash_format(self):
        """Test hash is in h:<hex> format."""
        field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
        
        state = State(
            field_blocks=field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        
        canon = StateCanon(schema_id="id:schema.test")
        state_hash = canon.state_hash(state)
        
        assert state_hash.startswith("h:")
        assert len(state_hash) == 2 + 64  # h: + 64 hex chars
    
    def test_different_ordering_same_hash(self):
        """Test that different insertion order produces same hash."""
        field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000002", FieldType.NONNEG_INT),
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
        
        # Order 1: insert first=1, then first=2
        state1 = State(
            field_blocks=field_blocks,
            _field_values={
                "f:00000000000000000000000000000001": 100,
                "f:00000000000000000000000000000002": 200,
            }
        )
        
        # Order 2: insert first=2, then first=1
        state2 = State(
            field_blocks=field_blocks,
            _field_values={
                "f:00000000000000000000000000000002": 200,
                "f:00000000000000000000000000000001": 100,
            }
        )
        
        canon = StateCanon(schema_id="id:schema.test")
        
        bytes1 = canon.canon_state(state1)
        bytes2 = canon.canon_state(state2)
        
        # Should be identical
        assert bytes1 == bytes2
        
        hash1 = canon.state_hash(state1)
        hash2 = canon.state_hash(state2)
        
        assert hash1 == hash2


if __name__ == "__main__":
    unittest.main(verbosity=2)
