# CK-0 Unit Tests: State Space

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ck0.state_space import State, FieldBlock, FieldDef, FieldType


class TestFieldDef(unittest.TestCase):
    """Test FieldDef."""
    
    def test_create_field_def(self):
        fd = FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT)
        self.assertEqual(fd.field_id, "f:00000000000000000000000000000001")
        self.assertEqual(fd.field_type, FieldType.NONNEG_INT)
    
    def test_invalid_field_id_raises(self):
        with self.assertRaises(ValueError):
            FieldDef("invalid", FieldType.INTEGER)
    
    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            FieldDef("f:001", FieldType.INTEGER)


class TestFieldBlock(unittest.TestCase):
    """Test FieldBlock."""
    
    def test_create_field_block(self):
        fields = [
            FieldDef("f:00000000000000000000000000000002", FieldType.NONNEG_INT),
            FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
        ]
        fb = FieldBlock("block:test", fields, "public")
        # Fields should be sorted
        self.assertEqual(fb.fields[0].field_id, "f:00000000000000000000000000000001")


class TestState(unittest.TestCase):
    """Test State."""
    
    def setUp(self):
        self.field_blocks = [
            FieldBlock(
                block_id="block:public",
                fields=[
                    FieldDef("f:00000000000000000000000000000001", FieldType.NONNEG_INT),
                    FieldDef("f:00000000000000000000000000000002", FieldType.NONNEG_INT),
                ],
                access_policy="public"
            )
        ]
    
    def test_create_state(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={
                "f:00000000000000000000000000000001": 100,
                "f:00000000000000000000000000000002": 200,
            }
        )
        self.assertEqual(state.get_field("f:00000000000000000000000000000001"), 100)
        self.assertEqual(state.get_field("f:00000000000000000000000000000002"), 200)
    
    def test_set_field(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        new_state = state.set_field("f:00000000000000000000000000000001", 200)
        # Original unchanged
        self.assertEqual(state.get_field("f:00000000000000000000000000000001"), 100)
        # New state has new value
        self.assertEqual(new_state.get_field("f:00000000000000000000000000000001"), 200)
    
    def test_with_fields(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        new_state = state.with_fields({
            "f:00000000000000000000000000000001": 200,
        })
        self.assertEqual(new_state.get_field("f:00000000000000000000000000000001"), 200)
    
    def test_state_hash(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        h1 = state.state_hash()
        h2 = state.state_hash()  # Should be cached
        self.assertEqual(h1, h2)
        self.assertTrue(h1.startswith("h:"))
    
    def test_validate_valid(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={
                "f:00000000000000000000000000000001": 100,
                "f:00000000000000000000000000000002": 200,
            }
        )
        is_valid, errors = state.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_missing_field(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={"f:00000000000000000000000000000001": 100}
        )
        is_valid, errors = state.validate()
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
    
    def test_validate_wrong_type(self):
        state = State(
            field_blocks=self.field_blocks,
            _field_values={
                "f:00000000000000000000000000000001": "not an int",
            }
        )
        is_valid, errors = state.validate()
        self.assertFalse(is_valid)


class TestCanonicalSort(unittest.TestCase):
    """Test canonical sorting."""
    
    def test_canonical_sort(self):
        items = ["z", "a", "m", "b"]
        sorted_items = State.canonical_sort(items)
        self.assertEqual(sorted_items, ["a", "b", "m", "z"])


if __name__ == '__main__':
    unittest.main()
