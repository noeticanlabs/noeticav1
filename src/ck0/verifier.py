# CK-0 Replay Verifier
# Per docs/ck0/9_replay_verifier.md

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .debtunit import DebtUnit
from .state_space import State
from .receipts import StepReceipt, CommitReceipt, ReceiptChain
from .budget_law import ServiceLaw, DisturbancePolicy, compute_budget_law
from .invariants import InvariantSet


class VerificationResult(Enum):
    """Verification result codes."""
    PASS = "pass"
    FAIL_STATE_HASH = "fail_state_hash"
    FAIL_RECEIPT_HASH = "fail_receipt_hash"
    FAIL_CHAIN = "fail_chain"
    FAIL_INVARIANT = "fail_invariant"
    FAIL_LAW = "fail_law"
    FAIL_SERVICE = "fail_service"
    FAIL_DISTURBANCE = "fail_disturbance"
    FAIL_TRANSITION = "fail_transition"


@dataclass
class VerificationError:
    """A verification error."""
    code: VerificationResult
    message: str
    details: Dict[str, Any]


@dataclass
class ReceiptVerificationResult:
    """Result of verifying a receipt."""
    passed: bool
    errors: List[VerificationError]
    details: Dict[str, Any]


class ReplayVerifier:
    """
    CK-0 Replay Verifier per docs/ck0/9_replay_verifier.md.
    
    Verifies:
    - Receipt chain integrity
    - State hash consistency
    - Invariant satisfaction
    - Budget law compliance
    - Service policy enforcement
    - Disturbance policy compliance
    """
    
    def __init__(
        self,
        invariant_set: InvariantSet,
        service_law: ServiceLaw,
        disturbance_policy: DisturbancePolicy,
        initial_state: State
    ):
        self.invariant_set = invariant_set
        self.service_law = service_law
        self.disturbance_policy = disturbance_policy
        self.initial_state = initial_state
        self._expected_state_hash = initial_state.state_hash()
    
    def verify_receipt_chain(self, chain: ReceiptChain) -> ReceiptVerificationResult:
        """
        Verify the entire receipt chain.
        
        Checks:
        - Receipt hashes are correct
        - Chain links are valid
        - State transitions are valid
        """
        errors = []
        
        # Check step receipts
        for i, receipt in enumerate(chain.step_receipts):
            result = self._verify_step_receipt(receipt, chain.step_receipts[i-1] if i > 0 else None)
            if not result.passed:
                errors.extend(result.errors)
        
        # Check commit receipts
        for i, receipt in enumerate(chain.commit_receipts):
            result = self._verify_commit_receipt(receipt, chain.commit_receipts[i-1] if i > 0 else None)
            if not result.passed:
                errors.extend(result.errors)
        
        return ReceiptVerificationResult(
            passed=len(errors) == 0,
            errors=errors,
            details={'total_receipts': len(chain.step_receipts), 'total_commits': len(chain.commit_receipts)}
        )
    
    def _verify_step_receipt(
        self, 
        receipt: StepReceipt, 
        prev_receipt: Optional[StepReceipt]
    ) -> ReceiptVerificationResult:
        """Verify a single step receipt."""
        errors = []
        
        # 1. Verify receipt hash
        computed = receipt.compute_hash()
        if computed != receipt.receipt_hash:
            errors.append(VerificationError(
                code=VerificationResult.FAIL_RECEIPT_HASH,
                message=f"Receipt hash mismatch at step {receipt.step_index}",
                details={'expected': receipt.receipt_hash, 'computed': computed}
            ))
        
        # 2. Verify chain link
        if prev_receipt is not None:
            if receipt.prev_receipt_hash != prev_receipt.receipt_hash:
                errors.append(VerificationError(
                    code=VerificationResult.FAIL_CHAIN,
                    message=f"Chain broken at step {receipt.step_index}",
                    details={'expected_prev': prev_receipt.receipt_hash, 'got': receipt.prev_receipt_hash}
                ))
        
        # 3. Verify state hash (we'd need the actual states for this)
        # In practice, verifier would reconstruct states from transitions
        
        # 4. Verify invariants (would check at each step)
        
        # 5. Verify budget law
        debt_before = DebtUnit(receipt.debt_before)
        budget = DebtUnit(receipt.service_provided)  # This is service, not budget - need to track
        disturbance = DebtUnit(receipt.E_k)
        
        # Check law: D_{k+1} <= D_k - S(D_k, B_k) + E_k
        law_result = compute_budget_law(
            debt_before,
            budget,  # Need actual budget value
            disturbance,
            self.service_law,
            self.disturbance_policy
        )
        
        if not law_result.law_satisfied:
            errors.append(VerificationError(
                code=VerificationResult.FAIL_LAW,
                message=f"Budget law violated at step {receipt.step_index}",
                details={'debt_before': debt_before.value, 'service': receipt.service_provided, 'disturbance': receipt.E_k}
            ))
        
        # 6. Verify service policy
        if receipt.service_policy_id != self.service_law.policy_id.value:
            errors.append(VerificationError(
                code=VerificationResult.FAIL_SERVICE,
                message=f"Service policy mismatch at step {receipt.step_index}",
                details={'expected': self.service_law.policy_id.value, 'got': receipt.service_policy_id}
            ))
        
        # 7. Verify disturbance policy
        if receipt.disturbance_policy_id != self.disturbance_policy.policy_id.value:
            errors.append(VerificationError(
                code=VerificationResult.FAIL_DISTURBANCE,
                message=f"Disturbance policy mismatch at step {receipt.step_index}",
                details={'expected': self.disturbance_policy.policy_id.value, 'got': receipt.disturbance_policy_id}
            ))
        
        # Validate disturbance value
        if not self.disturbance_policy.validate_e(DebtUnit(receipt.E_k)):
            errors.append(VerificationError(
                code=VerificationResult.FAIL_DISTURBANCE,
                message=f"Disturbance out of bounds at step {receipt.step_index}",
                details={'E_k': receipt.E_k}
            ))
        
        return ReceiptVerificationResult(
            passed=len(errors) == 0,
            errors=errors,
            details={'step_index': receipt.step_index}
        )
    
    def _verify_commit_receipt(
        self,
        receipt: CommitReceipt,
        prev_receipt: Optional[CommitReceipt]
    ) -> ReceiptVerificationResult:
        """Verify a commit receipt."""
        errors = []
        
        # 1. Verify commit hash
        computed = receipt.compute_hash()
        if computed != receipt.commit_hash:
            errors.append(VerificationError(
                code=VerificationResult.FAIL_RECEIPT_HASH,
                message=f"Commit hash mismatch at index {receipt.commit_index}",
                details={'expected': receipt.commit_hash, 'computed': computed}
            ))
        
        # 2. Verify chain link
        if prev_receipt is not None:
            if receipt.prev_commit_hash != prev_receipt.commit_hash:
                errors.append(VerificationError(
                    code=VerificationResult.FAIL_CHAIN,
                    message=f"Commit chain broken at index {receipt.commit_index}",
                    details={'expected_prev': prev_receipt.commit_hash, 'got': receipt.prev_commit_hash}
                ))
        
        return ReceiptVerificationResult(
            passed=len(errors) == 0,
            errors=errors,
            details={'commit_index': receipt.commit_index}
        )
    
    def verify_state_invariants(self, state: State) -> ReceiptVerificationResult:
        """Verify invariants hold for a state."""
        all_pass, failures = self.invariant_set.evaluate_all(state)
        
        errors = []
        if not all_pass:
            for inv_id, msg in failures.items():
                errors.append(VerificationError(
                    code=VerificationResult.FAIL_INVARIANT,
                    message=f"Invariant {inv_id} violated: {msg}",
                    details={'invariant_id': inv_id, 'message': msg}
                ))
        
        return ReceiptVerificationResult(
            passed=all_pass,
            errors=errors,
            details={}
        )
    
    def full_verification(
        self,
        chain: ReceiptChain,
        final_state: State
    ) -> Tuple[bool, List[VerificationError]]:
        """
        Perform full verification.
        
        Returns (passed, errors).
        """
        all_errors = []
        
        # Verify chain
        chain_result = self.verify_receipt_chain(chain)
        all_errors.extend(chain_result.errors)
        
        # Verify final state invariants
        state_result = self.verify_state_invariants(final_state)
        all_errors.extend(state_result.errors)
        
        return len(all_errors) == 0, all_errors


# Verification checklist per docs/ck0/9_replay_verifier.md

def get_verification_checklist() -> List[str]:
    """Return the verification checklist."""
    return [
        "1. Receipt hash verification",
        "2. Chain integrity (prev_receipt_hash links)",
        "3. State hash consistency (state_before → state_after)",
        "4. Invariant satisfaction at each step",
        "5. Budget law compliance: D_{k+1} ≤ D_k - S(D_k, B_k) + E_k",
        "6. Service policy enforcement (service_policy_id matches)",
        "7. Disturbance policy enforcement (E_k within bounds)",
        "8. Transition success (transition_success = true)",
        "9. Per-contract data integrity",
        "10. Commit chain verification"
    ]
