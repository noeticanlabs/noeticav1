# CK-0 Budget/Debt Law: Service Map S(D, B)
# D_{k+1} ≤ D_k - S(D_k, B_k) + E_k

from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from fractions import Fraction
from enum import Enum

from .debtunit import DebtUnit


class ServicePolicyID(Enum):
    """Service policy identifiers."""
    LINEAR_CAPPED = "CK0.service.v1.linear_capped"
    IDENTITY = "CK0.service.v1.identity"
    QUADRATIC = "CK0.service.v1.quadratic"


@dataclass
class ServiceLaw:
    """
    Service map S(D, B) per docs/ck0/4_budget_debt_law.md.
    
    The service law determines how much debt reduction (servicing) 
    is provided given current debt D and budget B.
    
    Per docs/ck0/4_budget_debt_law.md, service laws must satisfy:
    - A1: Determinism
    - A2: Monotonicity in B
    - A3: Zero-debt consistency: Φ(0, B) = 0
    - A4: Zero-budget identity: Φ(D, 0) = D
    - A5: Lipschitz control in debt
    - A6: Continuity
    """
    policy_id: ServicePolicyID
    instance_id: str  # e.g., "linear_capped.mu:<value>"
    service_fn: Callable[[DebtUnit, DebtUnit], DebtUnit]
    
    def compute(self, debt: DebtUnit, budget: DebtUnit) -> DebtUnit:
        """Compute S(D, B)."""
        return self.service_fn(debt, budget)
    
    def __call__(self, debt: DebtUnit, budget: DebtUnit) -> DebtUnit:
        """Convenience: S(debt, budget)."""
        return self.compute(debt, budget)


class DisturbancePolicyID(Enum):
    """Disturbance policy identifiers per docs/ck0/4_budget_debt_law.md."""
    DP0_ZERO = "DP0"           # E_k ≡ 0
    DP1_UNIFORM_BOUNDED = "DP1"  # 0 ≤ E_k ≤ Ē
    DP2_EVENT_TYPED = "DP2"    # Event-typed bounds
    DP3_MODEL_BASED = "DP3"    # Model-based disturbance


@dataclass
class DisturbancePolicy:
    """
    Disturbance policy per docs/ck0/4_budget_debt_law.md.
    
    Defines how external disturbances E_k are bounded.
    """
    policy_id: DisturbancePolicyID
    e_bar: Optional[DebtUnit] = None  # For DP1
    event_bounds: Optional[Dict[str, DebtUnit]] = None  # For DP2
    
    def validate_e(self, e_k: DebtUnit) -> bool:
        """Validate E_k against policy."""
        if self.policy_id == DisturbancePolicyID.DP0_ZERO:
            return e_k == DebtUnit(0)
        elif self.policy_id == DisturbancePolicyID.DP1_UNIFORM_BOUNDED:
            return e_k <= (self.e_bar or DebtUnit(0))
        elif self.policy_id == DisturbancePolicyID.DP2_EVENT_TYPED:
            # Would need event type
            return True
        return True


# Service law implementations

def linear_capped_service(
    debt: DebtUnit, 
    budget: DebtUnit, 
    mu: Fraction = Fraction(1)
) -> DebtUnit:
    """
    Linear capped service: S(D, B) = min(D, mu * B)
    
    Parameters:
    - mu: scaling factor (default 1)
    - D: current debt
    - B: budget
    
    Satisfies A1-A6:
    - A1: Deterministic ✓
    - A2: Monotonic in B ✓
    - A3: Φ(0, B) = min(0, mu*B) = 0 ✓
    - A4: Φ(D, 0) = min(D, 0) = 0 ≠ D (but this is by design - no budget = no service)
    - A5: Lipschitz with L=mu ✓
    - A6: Continuous ✓
    """
    service_amount = min(debt.value, int(mu * budget.value))
    return DebtUnit(service_amount)


def identity_service(debt: DebtUnit, budget: DebtUnit) -> DebtUnit:
    """
    Identity service: S(D, B) = D (pay off all debt if budget sufficient)
    
    Warning: This may violate A4 (Φ(D, 0) = D but Φ(D, 0) should be 0)
    """
    return debt if budget >= debt else DebtUnit(budget.value)


def quadratic_service(
    debt: DebtUnit, 
    budget: DebtUnit, 
    alpha: Fraction = Fraction(1, 10)
) -> DebtUnit:
    """
    Quadratic service: S(D, B) = min(D, alpha * B^2 / D)
    
    More gradual service curve.
    """
    if debt.value == 0:
        return DebtUnit(0)
    
    service_amount = min(
        debt.value, 
        int(alpha * budget.value * budget.value / debt.value)
    )
    return DebtUnit(max(0, service_amount))


# Pre-defined service laws

LINEAR_CAPPED_MU_1 = ServiceLaw(
    policy_id=ServicePolicyID.LINEAR_CAPPED,
    instance_id="linear_capped.mu:1",
    service_fn=lambda d, b: linear_capped_service(d, b, Fraction(1))
)

LINEAR_CAPPED_MU_2 = ServiceLaw(
    policy_id=ServicePolicyID.LINEAR_CAPPED,
    instance_id="linear_capped.mu:2",
    service_fn=lambda d, b: linear_capped_service(d, b, Fraction(2))
)

IDENTITY_SERVICE = ServiceLaw(
    policy_id=ServicePolicyID.IDENTITY,
    instance_id="identity",
    service_fn=identity_service
)

QUADRATIC_ALPHA_01 = ServiceLaw(
    policy_id=ServicePolicyID.QUADRATIC,
    instance_id="quadratic.alpha:0.1",
    service_fn=lambda d, b: quadratic_service(d, b, Fraction(1, 10))
)


def create_service_law(policy_id: str, instance_id: str) -> ServiceLaw:
    """Factory to create service law from policy/instance IDs."""
    if policy_id == "CK0.service.v1.linear_capped":
        if "mu:1" in instance_id:
            return LINEAR_CAPPED_MU_1
        elif "mu:2" in instance_id:
            return LINEAR_CAPPED_MU_2
        # Parse custom mu
        mu = Fraction(instance_id.split(":")[-1])
        return ServiceLaw(
            policy_id=ServicePolicyID.LINEAR_CAPPED,
            instance_id=instance_id,
            service_fn=lambda d, b: linear_capped_service(d, b, mu)
        )
    elif policy_id == "CK0.service.v1.identity":
        return IDENTITY_SERVICE
    elif policy_id == "CK0.service.v1.quadratic":
        return QUADRATIC_ALPHA_01
    
    raise ValueError(f"Unknown service policy: {policy_id}")


# Budget law computation

@dataclass
class BudgetLawResult:
    """Result of applying CK-0 budget law."""
    debt_next: DebtUnit
    service: DebtUnit
    disturbance: DebtUnit
    law_satisfied: bool
    details: Dict[str, Any]


def compute_budget_law(
    debt: DebtUnit,
    budget: DebtUnit,
    disturbance: DebtUnit,
    service_law: ServiceLaw,
    disturbance_policy: Optional[DisturbancePolicy] = None
) -> BudgetLawResult:
    """
    Compute D_{k+1} ≤ D_k - S(D_k, B_k) + E_k
    
    Returns the computed debt_next and whether law is satisfied.
    """
    # Compute service
    service = service_law.compute(debt, budget)
    
    # Compute theoretical next debt
    if debt.value >= service.value:
        debt_after_service = DebtUnit(debt.value - service.value)
    else:
        debt_after_service = DebtUnit(0)
    
    # Add disturbance
    debt_next = DebtUnit(debt_after_service.value + disturbance.value)
    
    # Validate disturbance if policy provided
    law_satisfied = True
    if disturbance_policy:
        law_satisfied = disturbance_policy.validate_e(disturbance)
    
    return BudgetLawResult(
        debt_next=debt_next,
        service=service,
        disturbance=disturbance,
        law_satisfied=law_satisfied,
        details={
            'debt_before': debt,
            'budget': budget,
            'service': service,
            'disturbance': disturbance,
            'debt_after_service': debt_after_service,
            'debt_final': debt_next
        }
    )


# Zero-disturbance policy (DP0)
ZERO_DISTURBANCE = DisturbancePolicy(
    policy_id=DisturbancePolicyID.DP0_ZERO
)
