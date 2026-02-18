# NK-1 ReceiptCanon: canon_receipt_bytes.v1 per docs/nk1/7_receipts.md

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import json
import hashlib
import binascii

from .value_canon import ValueCanon


CANON_RECEIPT_ID = "canon_receipt_bytes.v1"


class ReceiptType:
    """Receipt type identifiers."""
    OP_LOCAL = "op.local.v1"
    OP_COMMIT = "op.commit.v1"


@dataclass
class ReceiptCanon:
    """
    Canonical receipt serialization per NK-1 §2.1.
    
    Format:
    ["canon_receipt_bytes.v1", "<receipt_type>", [["key1", ValueCanon],...]]
    
    - Keys sorted lexicographically
    - Unknown keys rejected in v1.0 strict mode
    """
    
    strict_mode: bool = True
    known_keys: Optional[set] = None
    
    def __post_init__(self):
        if self.known_keys is None:
            # Default known keys for v1.0
            self.known_keys = {
                "receipt_type",
                "state_hash_before",
                "state_hash_after",
                "debt_before",
                "debt_after",
                "operations",
                "batch_id",
                "timestamp",
                "policy_digest",
            }
    
    def canon_receipt(
        self,
        receipt_type: str,
        fields: Dict[str, Any],
        strict: bool = True
    ) -> bytes:
        """
        Generate canonical receipt bytes.
        
        Args:
            receipt_type: Type of receipt (op.local.v1, op.commit.v1)
            fields: Receipt fields
            strict: If True, reject unknown keys
        
        Returns:
            Canonical bytes
        """
        # Validate keys in strict mode
        if strict:
            unknown_keys = set(fields.keys()) - self.known_keys
            if unknown_keys:
                raise ValueError(f"Unknown keys in strict mode: {unknown_keys}")
        
        # Build canonical structure: [canon_id, receipt_type, sorted_key_value_pairs]
        sorted_fields = sorted(fields.items(), key=lambda kv: kv[0].encode('utf-8'))
        
        canon_fields = []
        for key, value in sorted_fields:
            canon_value = self._canon_value(value)
            canon_fields.append([key, canon_value])
        
        # Build the array format
        canon_array = [
            CANON_RECEIPT_ID,
            receipt_type,
            canon_fields
        ]
        
        # Serialize as compact JSON
        return json.dumps(canon_array, separators=(',', ':')).encode('utf-8')
    
    def _canon_value(self, value: Any) -> Any:
        """Canon a value using ValueCanon."""
        if isinstance(value, dict):
            # Maps become sorted [key, value] arrays
            sorted_items = sorted(value.items(), key=lambda kv: kv[0].encode('utf-8'))
            return [[k, self._canon_value(v)] for k, v in sorted_items]
        elif isinstance(value, list):
            return [self._canon_value(item) for item in value]
        elif isinstance(value, str):
            # Check if it's a hash
            if value.startswith("h:"):
                # Keep as-is for hashes
                return value
            return ValueCanon.canon(value)
        elif isinstance(value, int):
            return ValueCanon.canon(value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        return value
    
    def receipt_hash(self, receipt_type: str, fields: Dict[str, Any]) -> str:
        """
        Compute receipt hash.
        
        Returns h:<hex> format.
        """
        canon_bytes = self.canon_receipt(receipt_type, fields)
        return 'h:' + hashlib.sha3_256(canon_bytes).hexdigest()
    
    def verify_receipt(
        self,
        receipt_type: str,
        fields: Dict[str, Any],
        expected_bytes: bytes
    ) -> Tuple[bool, str]:
        """Verify receipt bytes match expected."""
        actual = self.canon_receipt(receipt_type, fields)
        if actual == expected_bytes:
            return True, ""
        return False, f"Receipt bytes mismatch"


class MerkleTree:
    """
    Merkle tree implementation per NK-1 §2.2.
    
    - Leaf = raw 32 bytes from decoded receipt hash
    - Node = SHA256(L||R)
    - Odd nodes duplicated
    - Root encoded as h:<hex>
    """
    
    @staticmethod
    def decode_hash(hash_str: str) -> bytes:
        """
        Decode h:<hex> to 32 bytes.
        
        Args:
            hash_str: Hash string in h:<hex> format
        
        Returns:
            32 bytes
        """
        if not hash_str.startswith("h:"):
            raise ValueError(f"Invalid hash format: {hash_str}")
        
        hex_str = hash_str[2:]  # Remove 'h:' prefix
        return binascii.unhexlify(hex_str)
    
    @staticmethod
    def encode_hash(hash_bytes: bytes) -> str:
        """Encode 32 bytes to h:<hex> format."""
        return 'h:' + binascii.hexlify(hash_bytes).decode('ascii')
    
    @staticmethod
    def hash_node(left: bytes, right: bytes) -> bytes:
        """Compute SHA256(L||R) for a node."""
        return hashlib.sha256(left + right).digest()
    
    @staticmethod
    def compute_root(leaf_hashes: List[str]) -> str:
        """
        Compute Merkle root from list of leaf hashes.
        
        Args:
            leaf_hashes: List of h:<hex> hash strings
        
        Returns:
            Root hash in h:<hex> format
        """
        if not leaf_hashes:
            # Empty tree has empty root
            return MerkleTree.encode_hash(b'\x00' * 32)
        
        # Decode all hashes to bytes
        nodes = [MerkleTree.decode_hash(h) for h in leaf_hashes]
        
        # Build tree bottom-up
        while len(nodes) > 1:
            new_level = []
            
            # Process pairs
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                if i + 1 < len(nodes):
                    right = nodes[i + 1]
                else:
                    # Odd node: duplicate the last node
                    right = left
                
                # Compute parent
                parent = MerkleTree.hash_node(left, right)
                new_level.append(parent)
            
            nodes = new_level
        
        return MerkleTree.encode_hash(nodes[0])
    
    @staticmethod
    def compute_proof(leaf_hashes: List[str], leaf_index: int) -> List[Tuple[bool, str]]:
        """
        Compute Merkle proof for a leaf.
        
        Args:
            leaf_hashes: List of leaf hashes
            leaf_index: Index of the leaf to prove
        
        Returns:
            List of (is_left_sibling, hash) tuples
        """
        if leaf_index < 0 or leaf_index >= len(leaf_hashes):
            raise ValueError(f"Invalid leaf index: {leaf_index}")
        
        # Start with leaf hashes
        nodes = [MerkleTree.decode_hash(h) for h in leaf_hashes]
        proof = []
        
        # Build tree and collect siblings
        level_index = leaf_index
        current_level = nodes
        
        while len(current_level) > 1:
            new_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    # Odd node: duplicate
                    right = left
                
                # Add sibling to proof if this is our path
                if i == level_index or i + 1 == level_index:
                    if i == level_index:
                        proof.append((False, MerkleTree.encode_hash(right)))  # Right sibling
                    else:
                        proof.append((True, MerkleTree.encode_hash(left)))  # Left sibling
                
                # Compute parent
                parent = MerkleTree.hash_node(left, right)
                new_level.append(parent)
            
            # Update for next level
            current_level = new_level
            level_index //= 2
        
        return proof
    
    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[Tuple[bool, str]], root: str) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            leaf_hash: Leaf hash to verify
            proof: List of (is_left_sibling, hash) tuples
            root: Expected root hash
        
        Returns:
            True if proof is valid
        """
        current = MerkleTree.decode_hash(leaf_hash)
        
        for is_left, sibling_hash in proof:
            sibling = MerkleTree.decode_hash(sibling_hash)
            if is_left:
                # Sibling is on the left: hash(sibling || current)
                current = MerkleTree.hash_node(sibling, current)
            else:
                # Sibling is on the right: hash(current || sibling)
                current = MerkleTree.hash_node(current, sibling)
        
        return MerkleTree.encode_hash(current) == root


# Test the implementations
if __name__ == "__main__":
    # Test ReceiptCanon
    canon = ReceiptCanon()
    
    fields = {
        "receipt_type": "op.local.v1",
        "state_hash_before": "h:abc123",
        "state_hash_after": "h:def456",
        "debt_before": 100,
        "debt_after": 150,
    }
    
    canon_bytes = canon.canon_receipt("op.local.v1", fields)
    print(f"Canon receipt bytes: {canon_bytes}")
    
    receipt_hash = canon.receipt_hash("op.local.v1", fields)
    print(f"Receipt hash: {receipt_hash}")
    
    # Test MerkleTree
    leaves = [
        "h:0000000000000000000000000000000000000000000000000000000000000001",
        "h:0000000000000000000000000000000000000000000000000000000000000002",
        "h:0000000000000000000000000000000000000000000000000000000000000003",
    ]
    
    root = MerkleTree.compute_root(leaves)
    print(f"Merkle root: {root}")
    
    proof = MerkleTree.compute_proof(leaves, 0)
    print(f"Merkle proof for leaf 0: {proof}")
    
    verified = MerkleTree.verify_proof(leaves[0], proof, root)
    print(f"Proof verified: {verified}")
    
    print("\nAll ReceiptCanon and MerkleTree tests passed!")
