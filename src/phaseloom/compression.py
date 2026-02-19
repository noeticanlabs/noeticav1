# PhaseLoom Compression Protocol
#
# Implements slab compression as per canon spine Section 14

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import hashlib
import json

from .types import FixedPoint
from .receipt import Receipt, compute_digest


# =============================================================================
# Merkle Tree
# =============================================================================

class MerkleTree:
    """Merkle tree for receipt compression."""
    
    def __init__(self, receipts: List[Receipt]):
        """Build Merkle tree from receipts.
        
        Args:
            receipts: List of receipts
        """
        self.leaves = [r.digest() for r in receipts]
        self.tree = self._build_tree(self.leaves)
        self.receipts = receipts
    
    def _build_tree(self, leaves: List[str]) -> List[str]:
        """Build Merkle tree bottom-up.
        
        Args:
            leaves: Leaf hashes
            
        Returns:
            Tree levels (root at index 0)
        """
        if not leaves:
            return ['h:' + '0' * 64]
        
        tree = list(leaves)
        while len(tree) > 1:
            # Pad to even length
            if len(tree) % 2 == 1:
                tree.append(tree[-1])
            
            next_level = []
            for i in range(0, len(tree), 2):
                combined = tree[i] + tree[i+1]
                next_level.append('h:' + hashlib.sha3_256(combined.encode()).hexdigest())
            tree = next_level
        
        return tree
    
    @property
    def root(self) -> str:
        """Get Merkle root."""
        return self.tree[0] if self.tree else 'h:' + '0' * 64
    
    def get_proof(self, index: int) -> 'MerkleProof':
        """Get Merkle proof for receipt at index.
        
        Args:
            index: Receipt index
            
        Returns:
            Merkle proof
        """
        return MerkleProof.build(self.leaves, index)


@dataclass
class MerkleProof:
    """Merkle proof for a receipt."""
    leaf_hash: str
    path: List[str]
    positions: List[int]  # 0 = left, 1 = right
    
    @classmethod
    def build(cls, leaves: List[str], index: int) -> 'MerkleProof':
        """Build proof from leaves.
        
        Args:
            leaves: Leaf hashes
            index: Index of leaf
            
        Returns:
            Merkle proof
        """
        if index >= len(leaves):
            raise IndexError("Index out of range")
        
        path = []
        positions = []
        current_idx = index
        
        # Build tree
        tree = list(leaves)
        while len(tree) > 1:
            if len(tree) % 2 == 1:
                tree.append(tree[-1])
            
            # Determine sibling
            sibling_idx = current_idx + 1 if current_idx % 2 == 0 else current_idx - 1
            sibling_idx = min(sibling_idx, len(tree) - 1)
            
            if current_idx % 2 == 0:
                positions.append(1)  # We are left, sibling is right
                path.append(tree[sibling_idx])
            else:
                positions.append(0)  # We are right, sibling is left
                path.append(tree[sibling_idx])
            
            # Move up
            current_idx = current_idx // 2
            tree = [tree[i] + tree[i+1] for i in range(0, len(tree), 2)]
            current_idx = 0
        
        return cls(
            leaf_hash=leaves[index],
            path=path,
            positions=positions
        )
    
    def verify(self, root: str) -> bool:
        """Verify proof against root.
        
        Args:
            root: Expected root
            
        Returns:
            True if proof is valid
        """
        current = self.leaf_hash
        
        for sibling, pos in zip(self.path, self.positions):
            if pos == 0:  # Left
                combined = current + sibling
            else:  # Right
                combined = sibling + current
            current = 'h:' + hashlib.sha3_256(combined.encode()).hexdigest()
        
        return current == root


# =============================================================================
# Slab Summary
# =============================================================================

@dataclass
class SlabSummary:
    """Summary vector for a slab."""
    # Violation
    sup_v: FixedPoint
    
    # Budget deltas
    sum_delta_b: FixedPoint
    sum_delta_a: FixedPoint
    
    # Amp/Diss
    sum_A: FixedPoint
    sum_D: FixedPoint
    
    # Policy histogram (stored as dict)
    policy_histogram: Dict[str, int] = field(default_factory=dict)
    
    # Max values
    max_C_plus: FixedPoint = field(default_factory=FixedPoint.zero)
    max_T: FixedPoint = field(default_factory=FixedPoint.zero)
    
    # Receipt count
    receipt_count: int = 0
    
    @classmethod
    def compute(cls, receipts: List[Receipt]) -> 'SlabSummary':
        """Compute summary from receipts.
        
        Args:
            receipts: List of receipts
            
        Returns:
            SlabSummary
        """
        if not receipts:
            return cls(
                sup_v=FixedPoint.zero(),
                sum_delta_b=FixedPoint.zero(),
                sum_delta_a=FixedPoint.zero(),
                sum_A=FixedPoint.zero(),
                sum_D=FixedPoint.zero(),
                receipt_count=0
            )
        
        sup_v = max(r.v_next for r in receipts)
        
        sum_delta_b = sum(r.b_next - r.b_prev for r in receipts)
        sum_delta_a = sum(r.a_next - r.a_prev for r in receipts)
        
        sum_A = sum(r.A for r in receipts)
        sum_D = sum(r.D for r in receipts)
        
        max_C_plus = FixedPoint(max(
            max(r.C_prev.value, r.C_next.value) for r in receipts
        ))
        max_T = FixedPoint(max(
            max(r.T_prev.value, r.T_next.value) for r in receipts
        ))
        
        return cls(
            sup_v=sup_v,
            sum_delta_b=sum_delta_b,
            sum_delta_a=sum_delta_a,
            sum_A=sum_A,
            sum_D=sum_D,
            max_C_plus=max_C_plus,
            max_T=max_T,
            receipt_count=len(receipts)
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "sup_v": str(self.sup_v.value),
            "sum_delta_b": str(self.sum_delta_b.value),
            "sum_delta_a": str(self.sum_delta_a.value),
            "sum_A": str(self.sum_A.value),
            "sum_D": str(self.sum_D.value),
            "max_C_plus": str(self.max_C_plus.value),
            "max_T": str(self.max_T.value),
            "receipt_count": self.receipt_count,
        }


# =============================================================================
# Slab
# =============================================================================

@dataclass
class Slab:
    """Compressed slab of receipts."""
    root: str
    summary: SlabSummary
    merkle_tree: MerkleTree
    
    @classmethod
    def create(cls, receipts: List[Receipt]) -> 'Slab':
        """Create slab from receipts.
        
        Args:
            receipts: List of receipts
            
        Returns:
            Slab
        """
        tree = MerkleTree(receipts)
        summary = SlabSummary.compute(receipts)
        
        return cls(
            root=tree.root,
            summary=summary,
            merkle_tree=tree
        )
    
    def verify_receipt(self, receipt: Receipt, proof: MerkleProof) -> bool:
        """Verify receipt is in slab.
        
        Args:
            receipt: Receipt to verify
            proof: Merkle proof
            
        Returns:
            True if receipt is in slab
        """
        return proof.verify(self.root)


# =============================================================================
# Tier Configuration
# =============================================================================

@dataclass
class TierConfig:
    """Configuration for storage tiers."""
    hot_window_size: int = 1000      # Keep last 1000 receipts in memory
    slab_size: int = 10000          # 10000 receipts per slab
    archival_enabled: bool = True


# =============================================================================
# Compression Manager
# =============================================================================

class CompressionManager:
    """Manages receipt compression across tiers."""
    
    def __init__(self, config: TierConfig):
        """Initialize compression manager.
        
        Args:
            config: Tier configuration
        """
        self.config = config
        self.hot_receipts: List[Receipt] = []
        self.slabs: List[Slab] = []
    
    def add_receipt(self, receipt: Receipt) -> Optional[Slab]:
        """Add receipt to hot window.
        
        Args:
            receipt: Receipt to add
            
        Returns:
            Slab if one was formed, None otherwise
        """
        self.hot_receipts.append(receipt)
        
        # Check for slab formation
        if len(self.hot_receipts) >= self.config.slab_size:
            return self._form_slab()
        return None
    
    def _form_slab(self) -> Slab:
        """Form slab from hot receipts.
        
        Returns:
            Created slab
        """
        receipts = self.hot_receipts[:self.config.slab_size]
        
        slab = Slab.create(receipts)
        self.slabs.append(slab)
        self.hot_receipts = self.hot_receipts[self.config.slab_size:]
        
        return slab
    
    def get_receipt_proof(self, receipt: Receipt) -> Optional[MerkleProof]:
        """Get Merkle proof for receipt.
        
        Args:
            receipt: Receipt
            
        Returns:
            Merkle proof if receipt is in a slab
        """
        # Check hot window
        try:
            idx = self.hot_receipts.index(receipt)
            # Can't prove from hot (need slab)
            return None
        except ValueError:
            pass
        
        # Check slabs
        for slab in self.slabs:
            try:
                idx = slab.merkle_tree.receipts.index(receipt)
                return slab.merkle_tree.get_proof(idx)
            except ValueError:
                continue
        
        return None
    
    def verify_receipt_in_slab(self, receipt: Receipt, proof: MerkleProof) -> bool:
        """Verify receipt is in any slab.
        
        Args:
            receipt: Receipt
            proof: Merkle proof
            
        Returns:
            True if verified
        """
        for slab in self.slabs:
            if slab.verify_receipt(receipt, proof):
                return True
        return False


# =============================================================================
# Archival
# =============================================================================

@dataclass
class ArchivalObligation:
    """Obligation record for archival."""
    receipt_digest: str
    slab_root: str
    proof: MerkleProof
    timestamp: int
    
    def verify(self) -> bool:
        """Verify obligation.
        
        Returns:
            True if valid
        """
        return self.proof.verify(self.slab_root)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "receipt_digest": self.receipt_digest,
            "slab_root": self.slab_root,
            "timestamp": self.timestamp,
        }
