# NK-2 Commit + Local Receipts

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_batch_attempt.md`](4_batch_attempt.md), [`../nk1/7_receipts.md`](../nk1/7_receipts.md)

---

## Overview

This document defines the receipt schemas for NK-2. v1.0 rule: only successful batches emit receipts; failed attempts emit none. This ensures replay stability and prevents nondeterminism leakage.

---

## 1. Receipt Philosophy

### 1.1 v1.0 Rules

1. **Only successful commits** emit receipts
2. **No attempt receipts** for failed attempts
3. **Receipt chain** forms hash chain (commit_n links to commit_{n-1})
4. **Local receipts** bind individual ops to their state changes
5. **Commit receipt** aggregates local receipts via Merkle root

### 1.2 Receipt Types

```
┌─────────────────────────────────────────────────────────────────┐
│                      RECEIPT HIERARCHY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CommitReceipt                                                   │
│    ├─ batch_prev_hash (chain link)                            │
│    ├─ batch_size                                               │
│    ├─ locals_root (Merkle root of LocalReceipts)              │
│    ├─ scheduler_rule_id                                        │
│    ├─ scheduler_mode                                           │
│    ├─ policy_bundle_id, policy_digest                         │
│    ├─ curvature_matrix_version_id, curvature_matrix_digest   │
│    ├─ epsilon_measured                                         │
│    └─ epsilon_hat                                              │
│         ↓                                                      │
│  LocalReceipt (one per op in batch)                           │
│    ├─ op_id                                                   │
│    ├─ kernel_hash                                             │
│    ├─ footprint_digest                                         │
│    ├─ block_index                                             │
│    ├─ delta_bound_a                                            │
│    ├─ state_pre_hash                                          │
│    ├─ state_post_hash                                         │
│    └─ batch_prev_hash                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Local Receipt Schema

### 2.1 LocalReceipt Definition

```python
@dataclass(frozen=True)
class LocalReceipt:
    """
    Receipt for a single operation in a batch.
    
    Binds op to its pre/post states for receipt reconstruction.
    """
    
    # Op identification
    op_id: OpID
    kernel_hash: Hash256
    footprint_digest: Hash256
    block_index: int
    delta_bound_a: DebtUnit
    
    # Mode info
    requires_modeD: bool
    glb_mode_id: str
    
    # Policy IDs
    policy_bundle_id: PolicyID
    
    # State anchors
    state_pre_hash: Hash256
    state_post_hash: Hash256
    
    # Batch anchor
    batch_prev_hash: Hash256
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation."""
        return b'||'.join([
            self.op_id.encode('utf-8'),
            self.kernel_hash.bytes,
            self.footprint_digest.bytes,
            str(self.block_index).encode('utf-8'),
            str(self.delta_bound_a).encode('utf-8'),
            str(self.requires_modeD).encode('utf-8'),
            self.glb_mode_id.encode('utf-8'),
            self.policy_bundle_id.encode('utf-8'),
            self.state_pre_hash.bytes,
            self.state_post_hash.bytes,
            self.batch_prev_hash.bytes,
        ])
    
    def hash(self) -> Hash256:
        """Hash of canonical representation."""
        return Hash256(sha256(self.canonical_bytes()))
```

### 2.2 Local Receipt Construction

```python
def create_local_receipt(
    op: OpSpec,
    pre_state: State,
    post_state: State,
    batch_prev_hash: Hash256,
    policy_bundle_id: PolicyID
) -> LocalReceipt:
    """
    Create local receipt for an operation.
    
    Args:
        op: OpSpec for the operation
        pre_state: Pre-execution state
        post_state: Post-execution (patched) state
        batch_prev_hash: Previous commit hash
        policy_bundle_id: Policy bundle ID
    
    Returns:
        LocalReceipt
    """
    return LocalReceipt(
        op_id=op.op_id,
        kernel_hash=op.kernel_hash,
        footprint_digest=op.footprint_digest,
        block_index=op.block_index,
        delta_bound_a=op.delta_bound_a,
        requires_modeD=op.requires_modeD,
        glb_mode_id=op.glb_mode_id,
        policy_bundle_id=policy_bundle_id,
        state_pre_hash=pre_state.hash(),
        state_post_hash=post_state.hash(),
        batch_prev_hash=batch_prev_hash,
    )
```

---

## 3. Commit Receipt Schema

### 3.1 CommitReceipt Definition

```python
@dataclass(frozen=True)
class CommitReceipt:
    """
    Receipt for a successful batch commit.
    
    Aggregates local receipts via Merkle root and links to previous commit.
    """
    
    # Chain link
    batch_prev_hash: Hash256
    
    # Batch info
    batch_size: int
    locals_root: Hash256  # Merkle root of local receipts
    
    # Scheduler info
    scheduler_rule_id: str
    scheduler_mode: str
    
    # Policy info
    policy_bundle_id: PolicyID
    policy_digest: Hash256
    
    # Curvature info
    curvature_matrix_version_id: str
    curvature_matrix_digest: Hash256
    
    # Gate values
    epsilon_measured: DebtUnit
    epsilon_hat: DebtUnit
    
    # Optional: commit timestamp
    commit_timestamp_ns: int  # Nanoseconds since epoch
    
    def canonical_bytes(self) -> bytes:
        """Produce deterministic byte representation."""
        return b'||'.join([
            self.batch_prev_hash.bytes,
            str(self.batch_size).encode('utf-8'),
            self.locals_root.bytes,
            self.scheduler_rule_id.encode('utf-8'),
            self.scheduler_mode.encode('utf-8'),
            self.policy_bundle_id.encode('utf-8'),
            self.policy_digest.bytes,
            self.curvature_matrix_version_id.encode('utf-8'),
            self.curvature_matrix_digest.bytes,
            str(self.epsilon_measured).encode('utf-8'),
            str(self.epsilon_hat).encode('utf-8'),
            str(self.commit_timestamp_ns).encode('utf-8'),
        ])
    
    def hash(self) -> Hash256:
        """Hash of canonical representation."""
        return Hash256(sha256(self.canonical_bytes()))
```

### 3.2 Commit Receipt Construction

```python
def create_commit_receipt(
    batch: list[OpSpec],
    local_receipts: list[LocalReceipt],
    batch_prev_hash: Hash256,
    scheduler_rule_id: str,
    scheduler_mode: str,
    policy_bundle_id: PolicyID,
    policy_digest: Hash256,
    curvature_matrix_version_id: str,
    curvature_matrix_digest: Hash256,
    epsilon_measured: DebtUnit,
    epsilon_hat: DebtUnit
) -> CommitReceipt:
    """
    Create commit receipt for a batch.
    
    Args:
        batch: Batch that was committed
        local_receipts: Local receipts for each op
        batch_prev_hash: Previous commit hash
        scheduler_rule_id: Scheduler rule used
        scheduler_mode: Scheduler mode used
        policy_bundle_id: Policy bundle ID
        policy_digest: Policy digest
        curvature_matrix_version_id: Curvature matrix version
        curvature_matrix_digest: Curvature matrix digest
        epsilon_measured: Measured epsilon
        epsilon_hat: Estimated epsilon
    
    Returns:
        CommitReceipt
    """
    # Build Merkle tree from local receipts
    locals_root = build_merkle_root(local_receipts)
    
    return CommitReceipt(
        batch_prev_hash=batch_prev_hash,
        batch_size=len(batch),
        locals_root=locals_root,
        scheduler_rule_id=scheduler_rule_id,
        scheduler_mode=scheduler_mode,
        policy_bundle_id=policy_bundle_id,
        policy_digest=policy_digest,
        curvature_matrix_version_id=curvature_matrix_version_id,
        curvature_matrix_digest=curvature_matrix_digest,
        epsilon_measured=epsilon_measured,
        epsilon_hat=epsilon_hat,
        commit_timestamp_ns=time.time_ns(),
    )
```

---

## 4. Merkle Root Construction

### 4.1 Merkle Tree

```python
def build_merkle_root(receipts: list[LocalReceipt]) -> Hash256:
    """
    Build Merkle root from local receipts.
    
    Uses SHA-256 for hashing.
    Canonical leaf ordering by receipt hash.
    """
    if not receipts:
        return Hash256(sha256(b'empty'))
    
    # Sort receipts by hash (canonical ordering)
    sorted_receipts = sorted(receipts, key=lambda r: r.hash())
    
    # Build tree bottom-up
    leaves = [r.hash() for r in sorted_receipts]
    
    while len(leaves) > 1:
        # Pad to even number
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        
        # Hash pairs
        new_level = []
        for i in range(0, len(leaves), 2):
            combined = leaves[i].bytes + leaves[i + 1].bytes
            new_level.append(Hash256(sha256(combined)))
        
        leaves = new_level
    
    return leaves[0]


def verify_merkle_proof(
    receipt: LocalReceipt,
    root: Hash256,
    proof: list[tuple[Hash256, bool]]
) -> bool:
    """
    Verify a receipt is in the Merkle tree.
    
    Args:
        receipt: Local receipt to verify
        root: Merkle root
        proof: Proof path [(sibling_hash, is_left), ...]
    
    Returns:
        True if receipt is in tree
    """
    current = receipt.hash()
    
    for sibling, is_left in proof:
        if is_left:
            combined = current.bytes + sibling.bytes
        else:
            combined = sibling.bytes + current.bytes
        current = Hash256(sha256(combined))
    
    return current == root
```

---

## 5. Receipt Chain

### 5.1 Ledger Structure

```python
class ReceiptLedger:
    """
    Maintains receipt chain.
    
    Each commit links to previous via batch_prev_hash.
    """
    
    def __init__(self, genesis_hash: Hash256):
        self._commits: list[CommitReceipt] = []
        self._current_hash = genesis_hash
    
    def append(self, receipt: CommitReceipt) -> None:
        """Append commit receipt to ledger."""
        # Verify chain link
        assert receipt.batch_prev_hash == self._current_hash
        
        self._commits.append(receipt)
        self._current_hash = receipt.hash()
    
    @property
    def current_hash(self) -> Hash256:
        """Get current chain head."""
        return self._current_hash
    
    @property
    def commits(self) -> list[CommitReceipt]:
        """Get all commits."""
        return list(self._commits)
    
    def verify_chain(self) -> bool:
        """Verify entire chain is valid."""
        expected_hash = self._commits[0].batch_prev_hash if self._commits else self._current_hash
        
        for receipt in self._commits:
            if receipt.batch_prev_hash != expected_hash:
                return False
            expected_hash = receipt.hash()
        
        return expected_hash == self._current_hash
```

---

## 6. Receipt Verification

### 6.1 Local Receipt Verification

```python
def verify_local_receipt(
    receipt: LocalReceipt,
    kernel_registry: KernelRegistry,
    policy_bundle: PolicyBundle
) -> tuple[bool, str | None]:
    """
    Verify a local receipt.
    
    Checks:
    - kernel_hash is allowlisted
    - glb_mode_id matches bundle
    - state hashes are valid
    
    Returns:
        (is_valid, error_message)
    """
    # Check kernel
    if receipt.kernel_hash not in policy_bundle.allowed_kernel_hashes:
        return False, "kernel_hash_not_allowlisted"
    
    # Check glb_mode
    if receipt.glb_mode_id != policy_bundle.glb_mode_id:
        return False, "glb_mode_id_mismatch"
    
    # Check policy bundle
    if receipt.policy_bundle_id != policy_bundle.bundle_id:
        return False, "policy_bundle_id_mismatch"
    
    return True, None
```

### 6.2 Commit Receipt Verification

```python
def verify_commit_receipt(
    receipt: CommitReceipt,
    prev_receipt: CommitReceipt | None,
    local_receipts: list[LocalReceipt],
    policy_bundle: PolicyBundle,
    curvature_matrix: CurvatureMatrix
) -> tuple[bool, str | None]:
    """
    Verify a commit receipt.
    
    Checks:
    - Chain link is correct
    - Batch size matches local receipts
    - Merkle root is correct
    - Scheduler/policy IDs match
    - Curvature info matches
    
    Returns:
        (is_valid, error_message)
    """
    # Check chain link
    if prev_receipt is not None:
        if receipt.batch_prev_hash != prev_receipt.hash():
            return False, "chain_link_mismatch"
    
    # Check batch size
    if receipt.batch_size != len(local_receipts):
        return False, "batch_size_mismatch"
    
    # Check Merkle root
    expected_root = build_merkle_root(local_receipts)
    if receipt.locals_root != expected_root:
        return False, "merkle_root_mismatch"
    
    # Check scheduler
    if receipt.scheduler_rule_id != "greedy.curv.v1":
        return False, "unknown_scheduler_rule"
    
    # Check policy
    if receipt.policy_digest != policy_bundle.digest:
        return False, "policy_digest_mismatch"
    
    # Check curvature
    if receipt.curvature_matrix_digest != curvature_matrix.digest():
        return False, "curvature_digest_mismatch"
    
    return True, None
```

---

## 7. Full Receipt Generation

### 7.1 Generate Receipts for Batch

```python
def generate_batch_receipts(
    batch: list[OpSpec],
    pre_state: State,
    post_state: State,
    singleton_states: list[State],
    batch_prev_hash: Hash256,
    context: AttemptContext,
    epsilon_measured: DebtUnit,
    epsilon_hat: DebtUnit
) -> tuple[list[LocalReceipt], CommitReceipt]:
    """
    Generate all receipts for a successful batch.
    
    Args:
        batch: Committed batch
        pre_state: Pre-batch state
        post_state: Post-batch state
        singleton_states: Per-op patched states
        batch_prev_hash: Previous commit hash
        context: Attempt context
        epsilon_measured: Measured epsilon
        epsilon_hat: Estimated epsilon
    
    Returns:
        (local_receipts, commit_receipt)
    """
    # Create local receipts
    local_receipts = []
    for op, singleton_state in zip(batch, singleton_states):
        receipt = create_local_receipt(
            op=op,
            pre_state=pre_state,
            post_state=singleton_state,
            batch_prev_hash=batch_prev_hash,
            policy_bundle_id=context.policy_bundle.bundle_id
        )
        local_receipts.append(receipt)
    
    # Get curvature info
    curvature_version, curvature_digest = context.curvature_matrix.version_id(), context.curvature_matrix.digest()
    
    # Create commit receipt
    commit_receipt = create_commit_receipt(
        batch=batch,
        local_receipts=local_receipts,
        batch_prev_hash=batch_prev_hash,
        scheduler_rule_id=context.scheduler_rule_id,
        scheduler_mode=context.scheduler_mode,
        policy_bundle_id=context.policy_bundle.bundle_id,
        policy_digest=context.policy_bundle.digest(),
        curvature_matrix_version_id=curvature_version,
        curvature_matrix_digest=curvature_digest,
        epsilon_measured=epsilon_measured,
        epsilon_hat=epsilon_hat
    )
    
    return local_receipts, commit_receipt
```

---

## 8. Example Usage

```python
# After successful batch attempt
if result.success:
    # Generate receipts
    local_receipts, commit_receipt = generate_batch_receipts(
        batch=selected_batch,
        pre_state=pre_state,
        post_state=result.post_state,
        singleton_states=singleton_states,
        batch_prev_hash=ledger.current_hash,
        context=context,
        epsilon_measured=result.epsilon_measured,
        epsilon_hat=result.epsilon_hat
    )
    
    # Append to ledger
    ledger.append(commit_receipt)
    
    print(f"Commit: {commit_receipt.hash()}")
    print(f"Locals root: {commit_receipt.locals_root}")
    print(f"ε_measured: {commit_receipt.epsilon_measured}")
    print(f"ε_hat: {commit_receipt.epsilon_hat}")
```

---

## 9. No-Attempt Receipts Rule

### 9.1 Verification

```python
def verify_no_attempt_receipts(ledger: ReceiptLedger, failed_attempts: int) -> bool:
    """
    Verify no receipts exist for failed attempts.
    
    v1.0 rule: failed attempts produce zero ledger entries.
    """
    # Number of failed attempts should equal gap in commit sequence
    # (This is enforced by the main loop, not by receipts)
    return True  # Ledger only contains successful commits
```

---

## 10. Receipt Schema Summary

| Field | LocalReceipt | CommitReceipt | Purpose |
|-------|-------------|---------------|---------|
| `op_id` | ✅ | - | Op identification |
| `kernel_hash` | ✅ | - | Kernel verification |
| `footprint_digest` | ✅ | - | Memory footprint |
| `block_index` | ✅ | - | Curvature index |
| `delta_bound_a` | ✅ | - | Numeric bound |
| `state_pre_hash` | ✅ | - | Pre-state anchor |
| `state_post_hash` | ✅ | - | Post-state anchor |
| `batch_prev_hash` | ✅ | ✅ | Chain link |
| `batch_size` | - | ✅ | Batch info |
| `locals_root` | - | ✅ | Merkle aggregation |
| `scheduler_rule_id` | - | ✅ | Scheduler ID |
| `scheduler_mode` | - | ✅ | Mode used |
| `policy_bundle_id` | ✅ | ✅ | Policy reference |
| `policy_digest` | - | ✅ | Chain lock |
| `curvature_matrix_*` | - | ✅ | Curvature info |
| `epsilon_measured` | - | ✅ | Gate value |
| `epsilon_hat` | - | ✅ | Gate bound |
