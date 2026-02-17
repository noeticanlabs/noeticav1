# NK-1 Measured Gate: Gate decision logic per docs/nk1/4_measured_gate.md

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from fractions import Fraction

# Import from ck0
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ck0'))

from debtunit import DebtUnit
from state_space import State
from budget_law import ServiceLaw, DisturbancePolicy, compute_budget_law


@dataclass
class GateDecision:
    """Result of gate decision."""
    approved: bool
    epsilon_measured: int  # Measured epsilon in DebtUnit
    epsilon_hat: int       # Bound from matrix in DebtUnit
    reason: str
    details: Dict[str, Any]


class MeasuredGate:
    """
    NK-1 Measured Gate per docs/nk1/4_measured_gate.md.
    
    Enforces: epsilon_measured <= epsilon_hat
    
    The gate approves operations only when:
    - Measured delta-V (epsilon_measured) is within bounds (epsilon_hat)
    - Budget law is satisfied
    """
    
    def __init__(
        self,
        service_law: ServiceLaw,
        disturbance_policy: DisturbancePolicy,
        epsilon_hat: int = 0  # Default: zero tolerance
    ):
        self.service_law = service_law
        self.disturbance_policy = disturbance_policy
        self.epsilon_hat = epsilon_hat
    
    def check(
        self,
        state: State,
        debt_before: DebtUnit,
        budget: DebtUnit,
        disturbance: DebtUnit,
        new_state: State,
        debt_after: DebtUnit
    ) -> GateDecision:
        """
        Check if operation passes the measured gate.
        
        Returns gate decision with epsilon_measured and epsilon_hat.
        """
        # Compute epsilon_measured = |V(x') - V(x)|
        epsilon_measured = abs(debt_after.value - debt_before.value)
        
        # Check against epsilon_hat
        approved = epsilon_measured <= self.epsilon_hat
        
        reason = "APPROVED" if approved else "REJECTED"
        
        return GateDecision(
            approved=approved,
            epsilon_measured=epsilon_measured,
            epsilon_hat=self.epsilon_hat,
            reason=reason,
            details={
                'debt_before': debt_before.value,
                'debt_after': debt_after.value,
                'budget': budget.value,
                'disturbance': disturbance.value,
                'delta': epsilon_measured
            }
        )
    
    def check_with_budget_law(
        self,
        debt_before: DebtUnit,
        budget: DebtUnit,
        disturbance: DebtUnit,
        debt_after: DebtUnit
    ) -> GateDecision:
        """
        Check gate with budget law computation.
        
        Validates both:
        1. epsilon_measured <= epsilon_hat
        2. Budget law: D_{k+1} <= D_k - S(D_k, B_k) + E_k
        """
        # Compute budget law
        law_result = compute_budget_law(
            debt_before,
            budget,
            disturbance,
            self.service_law,
            self.disturbance_policy
        )
        
        # Compute epsilon_measured
        epsilon_measured = abs(debt_after.value - debt_before.value)
        
        # Both must pass
        gate_passed = epsilon_measured <= self.epsilon_hat
        law_passed = law_result.law_satisfied
        
        approved = gate_passed and law_passed
        
        reasons = []
        if not gate_passed:
            reasons.append(f"epsilon_measured({epsilon_measured}) > epsilon_hat({self.epsilon_hat})")
        if not law_passed:
            reasons.append(f"budget_law_violated")
        
        return GateDecision(
            approved=approved,
            epsilon_measured=epsilon_measured,
            epsilon_hat=self.epsilon_hat,
            reason="; ".join(reasons) if reasons else "APPROVED",
            details={
                'debt_before': debt_before.value,
                'debt_after': debt_after.value,
                'service': law_result.service.value,
                'disturbance': law_result.disturbance.value,
                'law_satisfied': law_passed
            }
        )
    
    def __call__(
        self,
        debt_before: DebtUnit,
        budget: DebtUnit,
        disturbance: DebtUnit,
        debt_after: DebtUnit
    ) -> GateDecision:
        """Convenience: gate(debt_before, budget, disturbance, debt_after)."""
        return self.check_with_budget_law(debt_before, budget, disturbance, debt_after)


# Disturbance policies per docs/nk1/4_measured_gate.md

class DisturbancePolicies:
    """Disturbance policy handlers."""
    
    @staticmethod
    def dp0_zero() -> DisturbancePolicy:
        """DP0: Zero disturbance - E_k = 0 always."""
        from budget_law import DisturbancePolicyID
        return DisturbancePolicy(
            policy_id=DisturbancePolicyID.DP0_ZERO
        )
    
    @staticmethod
    def dp1_uniform_bounded(e_bar: int) -> DisturbancePolicy:
        """DP1: Uniform bounded - 0 <= E_k <= e_bar."""
        from budget_law import DisturbancePolicyID
        return DisturbancePolicy(
            policy_id=DisturbancePolicyID.DP1_UNIFORM_BOUNDED,
            e_bar=DebtUnit(e_bar)
        )
    
    @staticmethod
    def dp2_event_typed(bounds: Dict[str, int]) -> DisturbancePolicy:
        """DP2: Event-typed bounds."""
        from budget_law import DisturbancePolicyID
        return DisturbancePolicy(
            policy_id=DisturbancePolicyID.DP2_EVENT_TYPED,
            event_bounds={k: DebtUnit(v) for k, v in bounds.items()}
        )


# Example gate

def create_example_gate() -> MeasuredGate:
    """Create example measured gate."""
    from budget_law import LINEAR_CAPPED_MU_1, DisturbancePolicyID
    from budget_law import DisturbancePolicy
    
    return MeasuredGate(
        service_law=LINEAR_CAPPED_MU_1,
        disturbance_policy=DisturbancePolicy(policy_id=DisturbancePolicyID.DP0_ZERO),
        epsilon_hat=100  # Allow up to 100 delta
    )
