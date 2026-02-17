# CK-0 Receipt Schema
# Receipt generation per docs/ck0/8_receipts_omega_ledger.md

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib
import json

from .debtunit import DebtUnit
from .state_space import State


@dataclass
class PerContractReceiptData:
    """Per-contract receipt data."""
    contract_id: str
    active: bool
    m_k: int  # Dimension
    sigma_spec_id: str
    weight_spec_id: str
    r2_k: int  # ||r_k(x)||^2 in DebtUnit
    r_hash_k: Optional[str] = None


@dataclass
class StepReceipt:
    """
    A step receipt per docs/ck0/8_receipts_omega_ledger.md.
    
    Contains all information needed for replay verification.
    """
    # Required fields per spec
    step_index: int
    receipt_hash: str  # h:<hex> of this receipt
    prev_receipt_hash: str  # h:<hex> of previous receipt
    
    # State
    state_hash_before: str  # h:<hex>
    state_hash_after: str  # h:<hex>
    
    # Violation functional
    debt_before: int  # DebtUnit value
    debt_after: int  # DebtUnit value
    
    # Service law
    service_policy_id: str  # e.g., "CK0.service.v1.linear_capped"
    service_instance_id: str  # e.g., "linear_capped.mu:1"
    service_provided: int  # DebtUnit
    
    # Disturbance
    disturbance_policy_id: str  # DP0, DP1, DP2, DP3
    E_k: int  # Disturbance value (DebtUnit)
    
    # Transition
    transition_id: str
    transition_success: bool
    
    # Invariants
    invariant_status: bool  # True if all invariants hold
    law_satisfied: bool  # True if CK-0 law satisfied
    
    # Per-contract data
    contracts: List[PerContractReceiptData] = field(default_factory=list)
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    version: str = "receipt_v1"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert contracts
        data['contracts'] = [asdict(c) for c in self.contracts]
        return data
    
    def canonical_json(self) -> bytes:
        """
        Return canonical JSON representation.
        
        Per docs/ck0/7_rounding_canonicalization.md.
        """
        data = self.to_dict()
        
        # Sort keys for canonical ordering
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    def compute_hash(self) -> str:
        """Compute receipt hash."""
        canonical = self.canonical_json()
        return 'h:' + hashlib.sha3_256(canonical).hexdigest()
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'StepReceipt':
        """Create from dictionary."""
        # Handle contracts
        contracts = []
        for c in data.get('contracts', []):
            contracts.append(PerContractReceiptData(**c))
        data['contracts'] = contracts
        
        return StepReceipt(**data)


@dataclass
class ModuleReceipt:
    """
    Module receipt per docs/nk3/7_module_receipt.md.
    
    Binds program digest to all artifact digests.
    """
    module_id: str
    program_nsc_digest: str  # h:<hex>
    opset_digest: str  # h:<hex>
    dag_digest: str  # h:<hex>
    execplan_digest: str  # h:<hex>
    kernel_registry_digest: str  # h:<hex>
    policy_digest: str  # h:<hex>
    toolchain_ids: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    
    def compute_hash(self) -> str:
        """Compute module receipt hash."""
        data = asdict(self)
        canonical = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        return 'h:' + hashlib.sha3_256(canonical).hexdigest()


@dataclass
class CommitReceipt:
    """
    Commit receipt per docs/nk2/5_commit_receipts.md.
    
    Created when a batch commits successfully.
    """
    commit_index: int
    commit_hash: str  # h:<hex>
    prev_commit_hash: str  # h:<hex>
    
    # State
    state_hash: str  # h:<hex>
    
    # Module
    module_receipt_digest: str  # h:<hex>
    
    # Step receipts (hashes only, not full receipts)
    step_receipt_hashes: List[str] = field(default_factory=list)
    
    # Child error (if any halt occurred)
    child_error_hash: Optional[str] = None
    child_error_code: Optional[str] = None
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    version: str = "commit_v1"
    
    def canonical_json(self) -> bytes:
        """Return canonical JSON."""
        data = asdict(self)
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    def compute_hash(self) -> str:
        """Compute commit hash."""
        return 'h:' + hashlib.sha3_256(self.canonical_json()).hexdigest()


# Receipt chain management

class ReceiptChain:
    """
    Manages the receipt chain for replay verification.
    """
    
    def __init__(self):
        self.step_receipts: List[StepReceipt] = []
        self.commit_receipts: List[CommitReceipt] = []
        self._last_step_hash: Optional[str] = None
        self._last_commit_hash: Optional[str] = None
    
    def add_step_receipt(self, receipt: StepReceipt) -> None:
        """Add a step receipt to the chain."""
        # Verify hash
        computed_hash = receipt.compute_hash()
        if computed_hash != receipt.receipt_hash:
            raise ValueError(f"Receipt hash mismatch: expected {receipt.receipt_hash}, got {computed_hash}")
        
        # Verify chain
        if self._last_step_hash is not None:
            if receipt.prev_receipt_hash != self._last_step_hash:
                raise ValueError(f"Chain broken: expected prev {self._last_step_hash}, got {receipt.prev_receipt_hash}")
        
        self.step_receipts.append(receipt)
        self._last_step_hash = receipt.receipt_hash
    
    def add_commit_receipt(self, receipt: CommitReceipt) -> None:
        """Add a commit receipt to the chain."""
        computed_hash = receipt.compute_hash()
        if computed_hash != receipt.commit_hash:
            raise ValueError(f"Commit hash mismatch")
        
        if self._last_commit_hash is not None:
            if receipt.prev_commit_hash != self._last_commit_hash:
                raise ValueError(f"Commit chain broken")
        
        self.commit_receipts.append(receipt)
        self._last_commit_hash = receipt.commit_hash
    
    def get_last_step_hash(self) -> Optional[str]:
        """Get last step receipt hash."""
        return self._last_step_hash
    
    def get_last_commit_hash(self) -> Optional[str]:
        """Get last commit receipt hash."""
        return self._last_commit_hash


# Helper functions for receipt creation

def create_step_receipt(
    step_index: int,
    prev_hash: str,
    state_before: State,
    state_after: State,
    debt_before: DebtUnit,
    debt_after: DebtUnit,
    service_law_id: str,
    service_law_instance: str,
    service_provided: DebtUnit,
    disturbance_policy_id: str,
    disturbance: DebtUnit,
    transition_id: str,
    transition_success: bool,
    invariant_status: bool,
    law_satisfied: bool,
    contracts: List[PerContractReceiptData] = None
) -> StepReceipt:
    """Helper to create a step receipt."""
    
    receipt = StepReceipt(
        step_index=step_index,
        receipt_hash="",  # Will be computed
        prev_receipt_hash=prev_hash,
        state_hash_before=state_before.state_hash(),
        state_hash_after=state_after.state_hash(),
        debt_before=debt_before.value,
        debt_after=debt_after.value,
        service_policy_id=service_law_id,
        service_instance_id=service_law_instance,
        service_provided=service_provided.value,
        disturbance_policy_id=disturbance_policy_id,
        E_k=disturbance.value,
        transition_id=transition_id,
        transition_success=transition_success,
        invariant_status=invariant_status,
        law_satisfied=law_satisfied,
        contracts=contracts or []
    )
    
    # Compute hash
    receipt.receipt_hash = receipt.compute_hash()
    
    return receipt
