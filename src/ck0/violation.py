# CK-0 Violation Functional V(x)
# V(x) = sum_k w_k * ||r_k(x)/sigma_k(x)||^2
# Computes in rational space, converts exactly once to DebtUnit via half-even rounding

from typing import Dict, List, Tuple, Any, Callable, Optional
from dataclasses import dataclass, field
from fractions import Fraction
import math

from .state_space import State
from .debtunit import DebtUnit


@dataclass
class Contract:
    """
    A single contract (constraint) in V(x).
    
    Each contract defines:
    - A residual function r_k(x)
    - A weight w_k
    - A scale sigma_k(x) for normalization
    """
    contract_id: str
    name: str
    residual_fn: Callable[[State], Fraction]  # r_k(x)
    weight: Fraction  # w_k
    sigma_fn: Callable[[State], Fraction]   # sigma_k(x), must be > 0
    m_k: int = 1  # Dimension of residual vector
    
    def __post_init__(self):
        if self.weight < 0:
            raise ValueError(f"Contract weight must be non-negative: {self.weight}")
    
    def compute_residual(self, state: State) -> Fraction:
        """Compute r_k(x)."""
        return self.residual_fn(state)
    
    def compute_sigma(self, state: State) -> Fraction:
        """Compute sigma_k(x)."""
        sigma = self.sigma_fn(state)
        if sigma <= 0:
            raise ValueError(f"Sigma must be positive, got {sigma}")
        return sigma
    
    def compute_normalized_residual_squared(self, state: State) -> Fraction:
        """
        Compute ||r_k(x)/sigma_k(x)||^2
        
        For m_k = 1: (r/sigma)^2
        For m_k > 1: sum of squares
        """
        r = self.compute_residual(state)
        sigma = self.compute_sigma(state)
        
        if self.m_k == 1:
            return (r * r) / (sigma * sigma)
        else:
            # Sum of squares - for now assuming residual is tuple
            if not isinstance(r, tuple):
                raise ValueError(f"Multi-dimensional contract requires tuple residual")
            return sum((r_i * r_i) for r_i in r) / (sigma * sigma)


@dataclass
class ViolationFunctional:
    """
    V(x) = sum_k w_k * ||r_k(x)/sigma_k(x)||^2
    
    Per docs/ck0/3_violation_functional.md:
    - V: X → ℝ_{≥0}
    - Deterministic
    - Computed in rational space
    - Converted to DebtUnit via half-even rounding under DEBT_SCALE
    """
    contracts: List[Contract] = field(default_factory=list)
    debt_scale: int = 1  # DEBT_SCALE from PolicyBundle
    
    def add_contract(self, contract: Contract) -> 'ViolationFunctional':
        """Add a contract to V(x)."""
        self.contracts.append(contract)
        return self
    
    def compute_rational(self, state: State) -> Fraction:
        """
        Compute V(x) in rational space.
        
        Returns Fraction for intermediate computation.
        """
        total = Fraction(0)
        for contract in self.contracts:
            residual_squared = contract.compute_normalized_residual_squared(state)
            weighted = residual_squared * contract.weight
            total += weighted
        return total
    
    def compute_debtunit(self, state: State) -> DebtUnit:
        """
        Compute V(x) as DebtUnit.
        
        This is the boundary conversion:
        - Compute in rational space
        - Convert exactly once to DebtUnit via half-even rounding
        - Under DEBT_SCALE from PolicyBundle
        """
        rational_v = self.compute_rational(state)
        return DebtUnit.from_fraction(rational_v, self.debt_scale)
    
    def compute_with_details(self, state: State) -> Dict[str, Any]:
        """
        Compute V(x) with detailed breakdown for receipts.
        
        Returns dict with:
        - total: DebtUnit value
        - rational_total: Fraction (for verification)
        - per_contract: list of (contract_id, residual_squared, weighted)
        """
        rational_total = self.compute_rational(self.state)
        
        per_contract = []
        for contract in self.contracts:
            residual_sq = contract.compute_normalized_residual_squared(state)
            weighted = residual_sq * contract.weight
            per_contract.append({
                'contract_id': contract.contract_id,
                'residual_squared': residual_sq,
                'weight': contract.weight,
                'weighted_residual': weighted
            })
        
        total = DebtUnit.from_fraction(rational_total, self.debt_scale)
        
        return {
            'total': total,
            'rational_total': rational_total,
            'per_contract': per_contract
        }
    
    def __call__(self, state: State) -> DebtUnit:
        """Convenience: V(state) returns DebtUnit."""
        return self.compute_debtunit(state)


# Standard contract factories

def residual_from_field(
    field_id: str,
    target: int
) -> Callable[[State], Fraction]:
    """Create residual function: r = actual - target"""
    def residual(state: State) -> Fraction:
        actual = state.get_field(field_id)
        if actual is None:
            raise ValueError(f"Field {field_id} not set")
        return Fraction(actual - target)
    return residual


def sigma_constant(value: Fraction) -> Callable[[State], Fraction]:
    """Create constant sigma function."""
    def sigma(state: State) -> Fraction:
        return value
    return sigma


def create_budget_contract(
    contract_id: str,
    budget_field: str,
    debt_field: str,
    weight: Fraction = Fraction(1)
) -> Contract:
    """
    Create a budget constraint contract.
    
    r(x) = budget - debt
    sigma = budget + 1 (avoid division by zero)
    """
    def residual(state: State) -> Fraction:
        budget = state.get_field(budget_field)
        debt = state.get_field(debt_field)
        if budget is None or debt is None:
            raise ValueError(f"Missing budget/debt field")
        return Fraction(budget - debt)
    
    def sigma(state: State) -> Fraction:
        budget = state.get_field(budget_field)
        return Fraction(max(budget, 1))
    
    return Contract(
        contract_id=contract_id,
        name=f"Budget constraint: {budget_field} >= {debt_field}",
        residual_fn=residual,
        weight=weight,
        sigma_fn=sigma,
        m_k=1
    )


def create_delta_bound_contract(
    contract_id: str,
    field_id: str,
    delta_bound: int,
    weight: Fraction = Fraction(1)
) -> Contract:
    """
    Create a delta-bound contract.
    
    Ensures |x - x_prev| <= delta_bound
    """
    def residual(state: State) -> Fraction:
        # This needs previous state - will be passed differently
        # For now, placeholder
        current = state.get_field(field_id)
        return Fraction(0)  # Placeholder
    
    def sigma(state: State) -> Fraction:
        return Fraction(delta_bound)
    
    return Contract(
        contract_id=contract_id,
        name=f"Delta bound: {field_id}",
        residual_fn=residual,
        weight=weight,
        sigma_fn=sigma,
        m_k=1
    )


def create_example_vfunctional() -> ViolationFunctional:
    """Create an example violation functional for testing."""
    vf = ViolationFunctional(debt_scale=1000)
    
    # Add a simple budget contract
    vf.add_contract(create_budget_contract(
        "contract:budget",
        "f:00000000000000000000000000000001",
        "f:00000000000000000000000000000002",
        weight=Fraction(1)
    ))
    
    return vf
