# CK-0 Unit Tests: Budget Law

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ck0.budget_law import (
    ServiceLaw, ServicePolicyID, linear_capped_service, 
    identity_service, quadratic_service, LINEAR_CAPPED_MU_1,
    DisturbancePolicy, DisturbancePolicyID, ZERO_DISTURBANCE,
    compute_budget_law
)
from ck0.debtunit import DebtUnit
from fractions import Fraction


class TestLinearCappedService(unittest.TestCase):
    """Test linear_capped_service."""
    
    def test_simple_case(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        result = linear_capped_service(debt, budget, Fraction(1))
        self.assertEqual(result.value, 50)
    
    def test_budget_exceeds_debt(self):
        debt = DebtUnit(30)
        budget = DebtUnit(50)
        result = linear_capped_service(debt, budget, Fraction(1))
        self.assertEqual(result.value, 30)  # Can only service what's owed
    
    def test_zero_budget(self):
        debt = DebtUnit(100)
        budget = DebtUnit(0)
        result = linear_capped_service(debt, budget, Fraction(1))
        self.assertEqual(result.value, 0)
    
    def test_zero_debt(self):
        debt = DebtUnit(0)
        budget = DebtUnit(50)
        result = linear_capped_service(debt, budget, Fraction(1))
        self.assertEqual(result.value, 0)
    
    def test_mu_scaling(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        result = linear_capped_service(debt, budget, Fraction(2))
        self.assertEqual(result.value, 100)  # 2*50 = 100, but capped at debt


class TestIdentityService(unittest.TestCase):
    """Test identity_service."""
    
    def test_pays_all_if_budget_sufficient(self):
        debt = DebtUnit(30)
        budget = DebtUnit(50)
        result = identity_service(debt, budget)
        self.assertEqual(result.value, 30)


class TestQuadraticService(unittest.TestCase):
    """Test quadratic_service."""
    
    def test_quadratic_scaling(self):
        debt = DebtUnit(1000)
        budget = DebtUnit(100)
        result = quadratic_service(debt, budget, Fraction(1, 10))
        # S = min(1000, 0.1 * 10000 / 1000) = min(1000, 1) = 1
        self.assertEqual(result.value, 1)


class TestComputeBudgetLaw(unittest.TestCase):
    """Test compute_budget_law."""
    
    def test_simple_law(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        disturbance = DebtUnit(0)
        
        result = compute_budget_law(
            debt, budget, disturbance,
            LINEAR_CAPPED_MU_1,
            ZERO_DISTURBANCE
        )
        
        self.assertEqual(result.service.value, 50)
        self.assertEqual(result.debt_next.value, 50)  # 100 - 50 + 0
        self.assertTrue(result.law_satisfied)
    
    def test_with_disturbance(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        disturbance = DebtUnit(10)
        
        result = compute_budget_law(
            debt, budget, disturbance,
            LINEAR_CAPPED_MU_1,
            ZERO_DISTURBANCE
        )
        
        self.assertEqual(result.debt_next.value, 60)  # 100 - 50 + 10


class TestDisturbancePolicy(unittest.TestCase):
    """Test DisturbancePolicy."""
    
    def test_dp0_zero_valid(self):
        policy = ZERO_DISTURBANCE
        self.assertTrue(policy.validate_e(DebtUnit(0)))
        self.assertFalse(policy.validate_e(DebtUnit(1)))


class TestPredefinedServiceLaws(unittest.TestCase):
    """Test predefined service laws."""
    
    def test_linear_capped_mu_1(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        result = LINEAR_CAPPED_MU_1.compute(debt, budget)
        self.assertEqual(result.value, 50)
    
    def test_service_law_callable(self):
        debt = DebtUnit(100)
        budget = DebtUnit(50)
        result = LINEAR_CAPPED_MU_1(debt, budget)
        self.assertEqual(result.value, 50)


if __name__ == '__main__':
    unittest.main()
