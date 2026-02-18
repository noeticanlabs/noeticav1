
# Tests for NK-1 ReceiptCanon and MerkleTree

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.receipt_canon import ReceiptCanon, MerkleTree, CANON_RECEIPT_ID, ReceiptType


class TestReceiptCanon(unittest.TestCase):
    """Tests for ReceiptCanon canon_receipt_bytes.v1."""
    
    def test_canon_receipt_id(self):
        """Test canonical receipt ID."""
        self.assertEqual(CANON_RECEIPT_ID, "canon_receipt_bytes.v1")
    
    def test_receipt_type_constants(self):
        """Test receipt type constants."""
        self.assertEqual(ReceiptType.OP_LOCAL, "op.local.v1")
        self.assertEqual(ReceiptType.OP_COMMIT, "op.commit.v1")
    
    def test_canon_receipt_format(self):
        """Test canonical receipt format is array."""
        canon = ReceiptCanon()
        
        fields = {
            "receipt_type": "op.local.v1",
            "state_hash_before": "h:abc123",
            "debt_before": 100,
        }
        
        canon_bytes = canon.canon_receipt("op.local.v1", fields)
        
        # Should be valid JSON
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        
        # Should be array format: [canon_id, receipt_type, fields]
        self.assertEqual(parsed[0], CANON_RECEIPT_ID)
        self.assertEqual(parsed[1], "op.local.v1")
        self.assertIsInstance(parsed[2], list)
    
    def test_keys_sorted(self):
        """Test keys are sorted lexicographically."""
        canon = ReceiptCanon(strict_mode=False)
        
        fields = {
            "zebra": 1,
            "apple": 2,
            "mango": 3,
        }
        
        canon_bytes = canon.canon_receipt("op.local.v1", fields, strict=False)
        
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        keys = [pair[0] for pair in parsed[2]]
        
        # Should be sorted
        self.assertEqual(keys, ["apple", "mango", "zebra"])
    
    def test_strict_mode_rejects_unknown_keys(self):
        """Test strict mode rejects unknown keys."""
        canon = ReceiptCanon(strict_mode=True)
        
        fields = {
            "known_key": "value",
            "unknown_key": "value",  # Not in known_keys
        }
        
        with self.assertRaises(ValueError) as ctx:
            canon.canon_receipt("op.local.v1", fields, strict=True)
        
        self.assertIn("Unknown keys", str(ctx.exception))
    
    def test_non_strict_mode_allows_unknown(self):
        """Test non-strict mode allows unknown keys."""
        canon = ReceiptCanon(strict_mode=False)
        
        fields = {
            "known_key": "value",
            "unknown_key": "value",
        }
        
        # Should not raise
        canon_bytes = canon.canon_receipt("op.local.v1", fields, strict=False)
        self.assertIsNotNone(canon_bytes)
    
    def test_receipt_hash_format(self):
        """Test receipt hash is in h:<hex> format."""
        canon = ReceiptCanon()
        
        fields = {
            "receipt_type": "op.local.v1",
            "state_hash_before": "h:abc123",
        }
        
        receipt_hash = canon.receipt_hash("op.local.v1", fields)
        
        self.assertTrue(receipt_hash.startswith("h:"))
        self.assertEqual(len(receipt_hash), 2 + 64)  # h: + 64 hex chars
    
    def test_value_canon_in_receipt(self):
        """Test ValueCanon is applied to values."""
        canon = ReceiptCanon()
        
        fields = {
            "receipt_type": "op.local.v1",
            "debt_before": 100,  # Should become i:100
        }
        
        canon_bytes = canon.canon_receipt("op.local.v1", fields)
        
        # The value should be canonized
        self.assertIn(b"i:100", canon_bytes)


class TestMerkleTree(unittest.TestCase):
    """Tests for MerkleTree."""
    
    def test_decode_hash(self):
        """Test hash decoding."""
        hash_str = "h:0000000000000000000000000000000000000000000000000000000000000001"
        decoded = MerkleTree.decode_hash(hash_str)
        
        self.assertEqual(len(decoded), 32)
    
    def test_encode_hash(self):
        """Test hash encoding."""
        hash_bytes = b'\x00' * 31 + b'\x01'
        encoded = MerkleTree.encode_hash(hash_bytes)
        
        self.assertEqual(encoded, "h:" + "0" * 62 + "01")
    
    def test_hash_node(self):
        """Test node hashing."""
        left = b'\x00' * 32
        right = b'\x01' * 32
        
        parent = MerkleTree.hash_node(left, right)
        
        self.assertEqual(len(parent), 32)
    
    def test_compute_root_empty(self):
        """Test empty tree root."""
        root = MerkleTree.compute_root([])
        
        # Should be hash of 32 zero bytes
        self.assertTrue(root.startswith("h:"))
    
    def test_compute_root_single_leaf(self):
        """Test single leaf tree."""
        leaves = ["h:0000000000000000000000000000000000000000000000000000000000000001"]
        
        root = MerkleTree.compute_root(leaves)
        
        # Single leaf = leaf itself
        self.assertEqual(root, leaves[0])
    
    def test_compute_root_two_leaves(self):
        """Test two leaf tree."""
        leaves = [
            "h:0000000000000000000000000000000000000000000000000000000000000001",
            "h:0000000000000000000000000000000000000000000000000000000000000002",
        ]
        
        root = MerkleTree.compute_root(leaves)
        
        self.assertTrue(root.startswith("h:"))
        self.assertNotEqual(root, leaves[0])
        self.assertNotEqual(root, leaves[1])
    
    def test_compute_root_odd_leaves(self):
        """Test odd leaf count - last node duplicated."""
        leaves = [
            "h:0000000000000000000000000000000000000000000000000000000000000001",
            "h:0000000000000000000000000000000000000000000000000000000000000002",
            "h:0000000000000000000000000000000000000000000000000000000000000003",
        ]
        
        root = MerkleTree.compute_root(leaves)
        
        self.assertTrue(root.startswith("h:"))
    
    def test_compute_proof(self):
        """Test Merkle proof generation."""
        leaves = [
            "h:0000000000000000000000000000000000000000000000000000000000000001",
            "h:0000000000000000000000000000000000000000000000000000000000000002",
            "h:0000000000000000000000000000000000000000000000000000000000000003",
        ]
        
        proof = MerkleTree.compute_proof(leaves, 0)
        
        # Should have proof elements
        self.assertIsInstance(proof, list)
    
    def test_verify_proof(self):
        """Test Merkle proof verification."""
        leaves = [
            "h:0000000000000000000000000000000000000000000000000000000000000001",
            "h:0000000000000000000000000000000000000000000000000000000000000002",
        ]
        
        root = MerkleTree.compute_root(leaves)
        proof = MerkleTree.compute_proof(leaves, 0)
        
        # Verify proof for leaf 0
        verified = MerkleTree.verify_proof(leaves[0], proof, root)
        self.assertTrue(verified)
    
    def test_verify_proof_fails_wrong_leaf(self):
        """Test proof verification fails with wrong leaf."""
        leaves = [
            "h:0000000000000000000000000000000000000000000000000000000000000001",
            "h:0000000000000000000000000000000000000000000000000000000000000002",
        ]
        
        root = MerkleTree.compute_root(leaves)
        proof = MerkleTree.compute_proof(leaves, 0)
        
        # Try to verify leaf 1 with proof for leaf 0
        verified = MerkleTree.verify_proof(leaves[1], proof, root)
        self.assertFalse(verified)


if __name__ == "__main__":
    unittest.main(verbosity=2)
