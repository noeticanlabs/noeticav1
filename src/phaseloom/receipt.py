# PhaseLoom Receipt Contract
#
# Implements coh.receipt.pl.v1 as per canon spine Section 12

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json
import hashlib

from .types import FixedPoint, StepType


# Schema constants
RECEIPT_SCHEMA = "coh.receipt.pl.v1"
RECEIPT_VERSION = "1.0.0"


def canon_json(data: Dict) -> bytes:
    """Serialize to canonical JSON.
    
    - Keys sorted lexicographically
    - No whitespace
    - UTF-8 encoding
    - Numbers as strings (fixed-point)
    
    Args:
        data: Dictionary to serialize
        
    Returns:
        Canonical JSON bytes
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_digest(data: Dict) -> str:
    """Compute canonical digest.
    
    Args:
        data: Data to hash
        
    Returns:
        Hash with 'h:' prefix
    """
    canon = canon_json(data)
    return 'h:' + hashlib.sha3_256(canon).hexdigest()


@dataclass
class Receipt:
    """PhaseLoom receipt for state transitions.
    
    Schema: coh.receipt.pl.v1
    """
    # Schema
    schema: str = RECEIPT_SCHEMA
    version: str = RECEIPT_VERSION
    
    # Context IDs
    coh_object_id: str = ""
    ck0_contract_id: str = ""
    nk1_policy_id: str = ""
    nk2_scheduler_id: str = ""
    params_id: str = ""
    
    # Clocks
    timestamp: int = 0
    step: int = 0
    
    # Boundary values
    state_hash_prev: str = ""
    state_hash_next: str = ""
    v_prev: FixedPoint = field(default_factory=FixedPoint.zero)
    v_next: FixedPoint = field(default_factory=FixedPoint.zero)
    C_prev: FixedPoint = field(default_factory=FixedPoint.zero)
    C_next: FixedPoint = field(default_factory=FixedPoint.zero)
    T_prev: FixedPoint = field(default_factory=FixedPoint.zero)
    T_next: FixedPoint = field(default_factory=FixedPoint.zero)
    b_prev: FixedPoint = field(default_factory=FixedPoint.zero)
    b_next: FixedPoint = field(default_factory=FixedPoint.zero)
    a_prev: FixedPoint = field(default_factory=FixedPoint.zero)
    a_next: FixedPoint = field(default_factory=FixedPoint.zero)
    
    # Derived deltas
    delta_T_inc: FixedPoint = field(default_factory=FixedPoint.zero)
    delta_T_res: FixedPoint = field(default_factory=FixedPoint.zero)
    delta_v: FixedPoint = field(default_factory=FixedPoint.zero)
    A: FixedPoint = field(default_factory=FixedPoint.zero)  # Amplification
    D: FixedPoint = field(default_factory=FixedPoint.zero)  # Dissipation
    
    # Step type
    step_type: StepType = StepType.SOLVE
    
    # Authorization (for AUTH_INJECT)
    multisig_valid: bool = False
    
    # Metadata
    receipt_id: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "schema": self.schema,
            "version": self.version,
            "context": {
                "coh_object_id": self.coh_object_id,
                "ck0_contract_id": self.ck0_contract_id,
                "nk1_policy_id": self.nk1_policy_id,
                "nk2_scheduler_id": self.nk2_scheduler_id,
                "params_id": self.params_id,
            },
            "clocks": {
                "timestamp": self.timestamp,
                "step": self.step,
            },
            "boundary": {
                "state_hash_prev": self.state_hash_prev,
                "state_hash_next": self.state_hash_next,
                "v_prev": str(self.v_prev.value),
                "v_next": str(self.v_next.value),
                "C_prev": str(self.C_prev.value),
                "C_next": str(self.C_next.value),
                "T_prev": str(self.T_prev.value),
                "T_next": str(self.T_next.value),
                "b_prev": str(self.b_prev.value),
                "b_next": str(self.b_next.value),
                "a_prev": str(self.a_prev.value),
                "a_next": str(self.a_next.value),
            },
            "derived": {
                "delta_T_inc": str(self.delta_T_inc.value),
                "delta_T_res": str(self.delta_T_res.value),
                "delta_v": str(self.delta_v.value),
                "A": str(self.A.value),
                "D": str(self.D.value),
            },
            "step_type": self.step_type.value,
            "multisig_valid": self.multisig_valid,
            "metadata": {
                "receipt_id": self.receipt_id,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> Receipt:
        """Create from dictionary."""
        ctx = data.get("context", {})
        clocks = data.get("clocks", {})
        boundary = data.get("boundary", {})
        derived = data.get("derived", {})
        metadata = data.get("metadata", {})
        
        return cls(
            schema=data.get("schema", RECEIPT_SCHEMA),
            version=data.get("version", RECEIPT_VERSION),
            coh_object_id=ctx.get("coh_object_id", ""),
            ck0_contract_id=ctx.get("ck0_contract_id", ""),
            nk1_policy_id=ctx.get("nk1_policy_id", ""),
            nk2_scheduler_id=ctx.get("nk2_scheduler_id", ""),
            params_id=ctx.get("params_id", ""),
            timestamp=clocks.get("timestamp", 0),
            step=clocks.get("step", 0),
            state_hash_prev=boundary.get("state_hash_prev", ""),
            state_hash_next=boundary.get("state_hash_next", ""),
            v_prev=FixedPoint(int(boundary.get("v_prev", "0"))),
            v_next=FixedPoint(int(boundary.get("v_next", "0"))),
            C_prev=FixedPoint(int(boundary.get("C_prev", "0"))),
            C_next=FixedPoint(int(boundary.get("C_next", "0"))),
            T_prev=FixedPoint(int(boundary.get("T_prev", "0"))),
            T_next=FixedPoint(int(boundary.get("T_next", "0"))),
            b_prev=FixedPoint(int(boundary.get("b_prev", "0"))),
            b_next=FixedPoint(int(boundary.get("b_next", "0"))),
            a_prev=FixedPoint(int(boundary.get("a_prev", "0"))),
            a_next=FixedPoint(int(boundary.get("a_next", "0"))),
            delta_T_inc=FixedPoint(int(derived.get("delta_T_inc", "0"))),
            delta_T_res=FixedPoint(int(derived.get("delta_T_res", "0"))),
            delta_v=FixedPoint(int(derived.get("delta_v", "0"))),
            A=FixedPoint(int(derived.get("A", "0"))),
            D=FixedPoint(int(derived.get("D", "0"))),
            step_type=StepType(data.get("step_type", "SOLVE")),
            multisig_valid=data.get("multisig_valid", False),
            receipt_id=metadata.get("receipt_id", ""),
        )
    
    def digest(self) -> str:
        """Compute receipt digest."""
        return compute_digest(self.to_dict())
    
    def canonical_bytes(self) -> bytes:
        """Get canonical JSON bytes."""
        return canon_json(self.to_dict())


@dataclass
class ReceiptChain:
    """Chain of receipts forming a linked list."""
    receipts: List[Receipt] = field(default_factory=list)
    
    def append(self, receipt: Receipt) -> None:
        """Append receipt to chain."""
        # Verify chain continuity
        if self.receipts:
            prev = self.receipts[-1]
            if receipt.state_hash_prev != prev.state_hash_next:
                raise ValueError("Receipt chain break")
        self.receipts.append(receipt)
    
    def verify_continuity(self) -> bool:
        """Verify chain continuity."""
        for i in range(1, len(self.receipts)):
            if self.receipts[i].state_hash_prev != self.receipts[i-1].state_hash_next:
                return False
        return True
    
    def get_root(self) -> Optional[str]:
        """Get latest state hash."""
        if not self.receipts:
            return None
        return self.receipts[-1].state_hash_next
    
    def get_digests(self) -> List[str]:
        """Get all receipt digests."""
        return [r.digest() for r in self.receipts]


def create_receipt(
    prev_state_hash: str,
    v_prev: FixedPoint,
    v_next: FixedPoint,
    C_prev: FixedPoint,
    C_next: FixedPoint,
    T_prev: FixedPoint,
    T_next: FixedPoint,
    b_prev: FixedPoint,
    b_next: FixedPoint,
    a_prev: FixedPoint,
    a_next: FixedPoint,
    step_type: StepType,
    params_id: str = ""
) -> Receipt:
    """Create a receipt from state transition.
    
    Args:
        prev_state_hash: Previous state hash
        v_prev: Violation before
        v_next: Violation after
        C_prev: Curvature before
        C_next: Curvature after
        T_prev: Tension before
        T_next: Tension after
        b_prev: Budget before
        b_next: Budget after
        a_prev: Authority before
        a_next: Authority after
        step_type: Step type
        params_id: Parameter bundle ID
        
    Returns:
        Receipt
    """
    # Compute deltas
    delta_v = v_next - v_prev
    A = FixedPoint(max(delta_v.value, 0))
    D = FixedPoint(max(-delta_v.value, 0))
    
    # Generate next state hash (simplified)
    next_state_data = {
        "v": str(v_next.value),
        "C": str(C_next.value),
        "T": str(T_next.value),
        "b": str(b_next.value),
        "a": str(a_next.value),
    }
    next_state_hash = compute_digest(next_state_data)
    
    return Receipt(
        state_hash_prev=prev_state_hash,
        state_hash_next=next_state_hash,
        v_prev=v_prev,
        v_next=v_next,
        C_prev=C_prev,
        C_next=C_next,
        T_prev=T_prev,
        T_next=T_next,
        b_prev=b_prev,
        b_next=b_next,
        a_prev=a_prev,
        a_next=a_next,
        delta_v=delta_v,
        A=A,
        D=D,
        step_type=step_type,
        params_id=params_id,
    )
