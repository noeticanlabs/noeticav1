# NK-1 Contract Measurement Engine: V(x) in DebtUnit

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from fractions import Fraction

# Re-export from ck0 for NK-1 usage
from ck0.debtunit import DebtUnit
from ck0.state_space import State
from ck0.violation import ViolationFunctional, Contract


@dataclass
class ContractMeasurement:
    """Result of measuring a single contract."""
    contract_id: str
    r2_k: int  # ||r_k(x)||^2 in DebtUnit
    m_k: int  # Dimension
    sigma_spec_id: str
    weight_spec_id: str
    active: bool


class ContractMeasurementEngine:
    """
    NK-1 Contract Measurement Engine per docs/nk1/3_contracts.md.
    
    Computes V(x) in DebtUnit (exact integer).
    """
    
    def __init__(self, vfunctional: ViolationFunctional, debt_scale: int = 1000):
        self.vfunctional = vfunctional
        self.debt_scale = debt_scale
    
    def measure(self, state: State) -> Tuple[DebtUnit, List[ContractMeasurement]]:
        """
        Compute V(x) as DebtUnit.
        
        Returns (V_DU, per_contract_measurements).
        """
        # Compute rational V(x)
        rational_v = self.vfunctional.compute_rational(state)
        
        # Convert to DebtUnit via half-even rounding
        v_du = DebtUnit.from_fraction(rational_v, self.debt_scale)
        
        # Compute per-contract measurements for receipts
        measurements = []
        for contract in self.vfunctional.contracts:
            r2 = contract.compute_normalized_residual_squared(state)
            r2_du = DebtUnit.from_fraction(r2, self.debt_scale)
            
            measurements.append(ContractMeasurement(
                contract_id=contract.contract_id,
                r2_k=r2_du.value,
                m_k=contract.m_k,
                sigma_spec_id="sigma:default",  # Would come from contract
                weight_spec_id="weight:default",
                active=True
            ))
        
        return v_du, measurements
    
    def __call__(self, state: State) -> DebtUnit:
        """Convenience: measure(state) returns DebtUnit."""
        v, _ = self.measure(state)
        return v
