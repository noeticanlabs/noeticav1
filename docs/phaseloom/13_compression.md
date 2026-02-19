# PhaseLoom Compression Protocol

**Canon Doc Spine v1.0.0** — Section 14

---

## 1. Tiering Strategy

### 1.1 Storage Tiers

| Tier | Retention | Storage Type | Receipt Detail |
|------|-----------|--------------|----------------|
| Hot | Recent N steps | Memory/SSD | Full receipts |
| Slab | Compressed window | Disk | Merkle root + summary |
| Archival | Full history | Cold storage | Obligations only |

### 1.2 Tier Boundaries

```python
class TierConfig:
    """Configuration for storage tiers."""
    hot_window_size: int = 1000      # Keep last 1000 receipts in memory
    slab_size: int = 10000           # 10000 receipts per slab
    archival_enabled: bool = True
```

---

## 2. Slab Structure

### 2.1 Slab Definition

A slab is a collection of receipts compressed into:
- Merkle root
- Summary vector

### 2.2 Merkle Tree

```python
class MerkleTree:
    """Merkle tree for receipt compression."""
    
    def __init__(self, receipts: List[Receipt]):
        self.leaves = [receipt.digest() for receipt in receipts]
        self.tree = self._build_tree(self.leaves)
    
    @property
    def root(self) -> str:
        """Get Merkle root."""
        return self.tree[0] if self.tree else 'h:' + '0' * 64
    
    def _build_tree(self, leaves: List[str]) -> List[str]:
        """Build Merkle tree bottom-up."""
        if not leaves:
            return ['h:' + '0' * 64]
        
        tree = list(leaves)
        while len(tree) > 1:
            if len(tree) % 2 == 1:
                tree.append(tree[-1])  # Duplicate last for odd
            
            next_level = []
            for i in range(0, len(tree), 2):
                combined = tree[i] + tree[i+1]
                next_level.append(sha3_256(combined.encode()).hexdigest())
            tree = next_level
        
        return tree
```

---

## 3. Slab Summary Vector

### 3.1 Definition

S^sharp (slab summary) contains aggregated statistics:

### 3.2 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| sup_v | fixed | Maximum violation in slab |
| sum_delta_b | fixed | Sum of budget deltas |
| sum_delta_a | fixed | Sum of authority deltas |
| sum_A | fixed | Sum of amplifications |
| sum_D | fixed | Sum of dissipations |
| policy_histogram | dict | Count by policy label |
| max_C_plus | fixed | Maximum positive curvature |
| max_T | fixed | Maximum tension |

### 3.3 Computation

```python
def compute_slab_summary(receipts: List[Receipt]) -> SlabSummary:
    """Compute summary vector for slab."""
    
    return SlabSummary(
        sup_v=max(r.v_next for r in receipts),
        sum_delta_b=sum(r.delta_b for r in receipts),
        sum_delta_a=sum(r.delta_a for r in receipts),
        sum_A=sum(r.A for r in receipts),
        sum_D=sum(r.D for r in receipts),
        policy_histogram=compute_policy_histogram(receipts),
        max_C_plus=max(max(r.C_prev, r.C_next) for r in receipts),
        max_T=max(max(r.T_prev, r.T_next) for r in receipts)
    )
```

---

## 4. Membership Verification

### 4.1 Merkle Proof

```python
@dataclass
class MerkleProof:
    """Merkle proof for a receipt."""
    leaf_hash: str
    path: List[str]  # Sibling hashes
    position: int    # Left (0) or Right (1)
    
    def verify(self, root: str, leaf_index: int) -> bool:
        """Verify proof against root."""
        current = self.leaf_hash
        
        for i, (sibling, pos) in enumerate(zip(self.path, self.positions)):
            if pos == 0:  # Left
                combined = current + sibling
            else:  # Right
                combined = sibling + current
            
            current = sha3_256(combined.encode()).hexdigest()
        
        return current == root
```

### 4.2 Verification Protocol

```python
def verify_receipt_in_slab(
    receipt: Receipt,
    proof: MerkleProof,
    root: str
) -> bool:
    """Verify receipt is in slab."""
    return proof.verify(root, receipt.index)
```

---

## 5. Stability Evidence

### 5.1 From Summary to Bounds

From slab summary, we can derive stability bounds:

- **Violation bound:** sup_v in slab
- **Budget bound:** sum_delta_b over slab
- **Curvature bound:** max_C_plus

### 5.2 Recurrence Verification

```python
def verify_slab_stability(
    prev_slab: SlabSummary,
    next_slab: SlabSummary,
    params: Params
) -> bool:
    """Verify stability across slabs."""
    
    # Budget cannot go negative
    if next_slab.sum_delta_b < -prev_slab.budget:
        return False
    
    # Curvature bounded by amplification
    if next_slab.max_C_plus > params.C_max:
        return False
    
    return True
```

---

## 6. Archival Protocol

### 6.1 Obligations

When moving to archival:
- Store only receipt digests (not full receipts)
- Keep summary vectors
- Maintain Merkle roots for proof

### 6.2 Proof Obligations

```python
@dataclass
class ArchivalObligation:
    """Obligation record for archival."""
    receipt_digest: str
    merkle_proof: MerkleProof
    slab_root: str
    timestamp: uint64
    
    def verify(self) -> bool:
        """Verify obligation."""
        return self.merkle_proof.verify(
            self.slab_root,
            self.receipt_index
        )
```

---

## 7. Full Proof vs Receipt Access

### 7.1 Scenario 1: Full Receipt Available

When receipt is in hot window:
- Direct access
- No proof needed

### 7.2 Scenario 2: Slab Access

When receipt is in slab:
- Use Merkle proof to verify inclusion
- Use summary for aggregated stats

### 7.3 Scenario 3: Archival

When receipt is archived:
- Need full proof chain:
  1. Archival obligation
  2. Merkle proof
  3. Slab summary

---

## 8. Implementation

### 8.1 Compression Manager

```python
class CompressionManager:
    """Manages receipt compression."""
    
    def __init__(self, config: TierConfig):
        self.config = config
        self.hot_receipts: List[Receipt] = []
        self.slabs: List[Slab] = []
    
    def add_receipt(self, receipt: Receipt) -> None:
        """Add receipt to hot window."""
        self.hot_receipts.append(receipt)
        
        # Check for slab formation
        if len(self.hot_receipts) >= self.config.slab_size:
            self._form_slab()
    
    def _form_slab(self) -> None:
        """Form slab from hot receipts."""
        receipts = self.hot_receipts[:self.config.slab_size]
        
        # Build Merkle tree
        tree = MerkleTree(receipts)
        
        # Compute summary
        summary = compute_slab_summary(receipts)
        
        slab = Slab(
            root=tree.root,
            summary=summary,
            receipts=receipts
        )
        
        self.slabs.append(slab)
        self.hot_receipts = self.hot_receipts[self.config.slab_size:]
```

---

## 9. Status

- [x] Tiering strategy defined
- [x] Slab structure specified
- [x] Summary vector defined
- [x] Membership verification described
- [ ] Implementation in src/phaseloom/compression.py

---

*The compression protocol enables long-horizon auditability without unbounded receipt growth, using Merkle trees and summary vectors for efficient verification.*
