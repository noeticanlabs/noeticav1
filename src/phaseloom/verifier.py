# PhaseLoom Verifier — LoomVerifier STF
#
# Deterministic fixed-point state transition function

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from .types import (
    PLState,
    PLParams,
    FixedPoint,
    StepType,
    STFResult,
    InterlockReason,
)
from .interlock import check_interlock
from .potential import compute_potential_from_state


class RejectCode(Enum):
    """STF reject codes."""
    SCHEMA_HASH_MISMATCH = "schema"
    INVALID_STATE = "state"
    STATE_HASH_MISMATCH = "state_hash"
    CURVATURE_VIOLATION = "curvature"
    TENSION_VIOLATION = "tension"
    BUDGET_VIOLATION = "budget"
    AUTHORITY_VIOLATION = "authority"
    BUDGET_CHARGE_VIOLATION = "budget_charge"
    INTERLOCK_VIOLATION = "interlock"
    UNAUTHORIZED_INJECTION = "auth"
    MULTISIG_INVALID = "multisig"
    SIGNATURE_INVALID = "signature"
    OVERFLOW = "overflow"
    DIVISION_BY_ZERO = "div_zero"
    RECEIPT_CHAIN_BREAK = "chain"
    DUPLICATE_RECEIPT = "duplicate"


@dataclass
class Receipt:
    """PhaseLoom receipt for state transitions."""
    # Schema
    schema: str = "coh.receipt.pl.v1"
    version: str = "1.0.0"
    
    # Context IDs
    coh_object_id: str = ""
    ck0_contract_id: str = ""
    nk1_policy_id: str = ""
    nk2_scheduler_id: str = ""
    params_id: str = ""
    
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
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for hashing."""
        return {
            "schema": self.schema,
            "version": self.version,
            "coh_object_id": self.coh_object_id,
            "ck0_contract_id": self.ck0_contract_id,
            "nk1_policy_id": self.nk1_policy_id,
            "nk2_scheduler_id": self.nk2_scheduler_id,
            "params_id": self.params_id,
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
            "delta_T_inc": str(self.delta_T_inc.value),
            "delta_T_res": str(self.delta_T_res.value),
            "delta_v": str(self.delta_v.value),
            "A": str(self.A.value),
            "D": str(self.D.value),
            "step_type": self.step_type.value,
        }
    
    def digest(self) -> str:
        """Compute receipt digest."""
        data = json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
        return 'h:' + hashlib.sha3_256(data.encode()).hexdigest()


class LoomVerifier:
    """Deterministic fixed-point state transition function.
    
    Verifies receipt validity and computes next state.
    """
    
    def __init__(self, params: PLParams):
        """Initialize verifier with governance parameters."""
        self.params = params
    
    def verify_transition(
        self,
        prev_state: PLState,
        receipt: Receipt,
        auth_valid: bool = True
    ) -> STFResult:
        """Verify complete state transition.
        
        Args:
            prev_state: Previous extended state
            receipt: Receipt for transition
            auth_valid: Whether authorization is valid (for AUTH_INJECT)
            
        Returns:
            STFResult with acceptance decision
        """
        # 1. Schema check
        if receipt.schema != "coh.receipt.pl.v1":
            return STFResult.rejected(
                RejectCode.SCHEMA_HASH_MISMATCH.value,
                "Invalid schema"
            )
        
        # 2. Boundary matching
        if not self._verify_boundary(prev_state, receipt):
            return STFResult.rejected(
                RejectCode.STATE_HASH_MISMATCH.value,
                "Boundary mismatch"
            )
        
        # 3. Verify recurrences
        if not self._verify_curvature(receipt):
            return STFResult.rejected(
                RejectCode.CURVATURE_VIOLATION.value,
                "Curvature recurrence violation"
            )
        
        if not self._verify_tension(receipt):
            return STFResult.rejected(
                RejectCode.TENSION_VIOLATION.value,
                "Tension recurrence violation"
            )
        
        # 4. Verify budget law
        if not self._verify_budget_charge(receipt):
            return STFResult.rejected(
                RejectCode.BUDGET_CHARGE_VIOLATION.value,
                "Budget charge law violation"
            )
        
        # 5. Verify interlock
        if not self._verify_interlock(receipt):
            return STFResult.rejected(
                RejectCode.INTERLOCK_VIOLATION.value,
                "Interlock violation"
            )
        
        # 6. Verify authorization (if AUTH_INJECT)
        if receipt.step_type == StepType.AUTH_INJECT:
            if not self._verify_auth_inject(receipt, auth_valid):
                return STFResult.rejected(
                    RejectCode.UNAUTHORIZED_INJECTION.value,
                    "Unauthorized injection"
                )
        
        # 7. Compute next state
        next_state = self._compute_next_state(prev_state, receipt)
        
        return STFResult.accepted(next_state)
    
    def _verify_boundary(self, prev_state: PLState, receipt: Receipt) -> bool:
        """Verify boundary values match."""
        return (
            receipt.C_prev == prev_state.C and
            receipt.T_prev == prev_state.T and
            receipt.b_prev == prev_state.b and
            receipt.a_prev == prev_state.a
        )
    
    def _verify_curvature(self, receipt: Receipt) -> bool:
        """Verify C^+ = rho_C * C + (A - D)"""
        expected_C = self.params.rho_C * receipt.C_prev + (receipt.A - receipt.D)
        return receipt.C_next == expected_C
    
    def _verify_tension(self, receipt: Receipt) -> bool:
        """Verify T^+ = rho_T * T + delta_T_inc - delta_T_res"""
        expected_T = self.params.rho_T * receipt.T_prev + receipt.delta_T_inc - receipt.delta_T_res
        return receipt.T_next == expected_T
    
    def _verify_budget_charge(self, receipt: Receipt) -> bool:
        """Verify delta_b >= kappa_A * A + kappa_T * delta_T_inc"""
        required = self.params.kappa_A * receipt.A + self.params.kappa_T * receipt.delta_T_inc
        delta_b = receipt.b_prev - receipt.b_next
        return delta_b >= required
    
    def _verify_interlock(self, receipt: Receipt) -> bool:
        """Verify interlock constraints."""
        if receipt.step_type == StepType.SOLVE and receipt.A.value > 0:
            # SOLVE with A > 0 requires b > b_min
            return receipt.b_prev > self.params.b_min
        return True
    
    def _verify_auth_inject(self, receipt: Receipt, auth_valid: bool) -> bool:
        """Verify AUTH_INJECT constraints."""
        if receipt.step_type != StepType.AUTH_INJECT:
            return True
        
        # Check authorization
        if not auth_valid or not receipt.multisig_valid:
            return False
        
        # Check b increases
        if not (receipt.b_next > receipt.b_prev):
            return False
        
        # Check a increases
        if not (receipt.a_next > receipt.a_prev):
            return False
        
        # Check V unchanged (v1 safe choice)
        if receipt.v_next != receipt.v_prev:
            return False
        
        return True
    
    def _compute_next_state(self, prev_state: PLState, receipt: Receipt) -> PLState:
        """Compute next extended state."""
        return PLState(
            x=prev_state.x,  # Base state would come from CK-0
            C=receipt.C_next,
            T=receipt.T_next,
            b=receipt.b_next,
            a=receipt.a_next
        )
    
    def verify_batch(
        self,
        initial_state: PLState,
        receipts: List[Receipt],
        auth_valids: Optional[List[bool]] = None
    ) -> STFResult:
        """Verify a batch of receipts.
        
        Args:
            initial_state: Initial state
            receipts: List of receipts
            auth_valids: List of auth validity flags (default all True)
            
        Returns:
            STFResult with final state or rejection
        """
        if auth_valids is None:
            auth_valids = [True] * len(receipts)
        
        current_state = initial_state
        
        for i, (receipt, auth_valid) in enumerate(zip(receipts, auth_valids)):
            result = self.verify_transition(current_state, receipt, auth_valid)
            
            if not result.accepted:
                return STFResult.rejected(
                    result.reject_code,
                    f"Batch rejected at receipt {i}: {result.message}"
                )
            
            current_state = result.next_state
        
        return STFResult.accepted(current_state)
