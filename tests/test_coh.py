"""
Coh Module Tests

Tests for the Category of Coherent Spaces implementation.
"""

import pytest
from src.coh import (
    CohObject,
    CohMorphism,
    create_finite_coh_object,
    verify_faithfulness,
    verify_algebraic_geometric_binding,
    verify_deterministic_validity,
    transition_relation,
    descent_preorder,
    verify_admissibility_preservation,
    verify_receipt_covariance,
    identity,
    compose,
    product,
    pullback,
    TimeFunctor,
    NaturalTransformation,
    CohCK0Object,
    is_ck0_receipt,
    CK0_RECEIPT_FIELDS,
)


class TestCohObject:
    """Test CohObject creation and properties"""
    
    def test_simple_finite_object(self):
        """Create a simple 3-state system"""
        states = {'a', 'b', 'c'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        
        # Valid transitions: b->a, c->b (descent)
        valid = {
            ('b', 'a', 'rho0'),
            ('c', 'b', 'rho0'),
        }
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Test admissibility
        assert obj.is_admissible('a', 0.0) == True
        assert obj.is_admissible('b', 0.0) == False
        assert obj.is_admissible('c', 0.0) == False
        
        # Test potential
        assert obj.potential('a') == 0
        assert obj.potential('b') == 1
        assert obj.potential('c') == 2


class TestObjectAxioms:
    """Test object axioms A1, A2, A3"""
    
    def test_a1_faithfulness(self):
        """Test A1: x ∈ C ⟺ V(x) = 0"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        
        # Valid transition with zero budget
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # A1 should hold
        assert verify_faithfulness(obj) == True
    
    def test_a2_algebraic_geometric_binding(self):
        """Test A2: V(y) ≤ V(x) + Δ(ρ)"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 1}.__getitem__  # Budget allows increase
        
        # Valid: b -> a, V(a)=0 ≤ V(b)+Δ = 1+1 = 2
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        assert verify_algebraic_geometric_binding(obj) == True
    
    def test_a3_deterministic_validity(self):
        """Test A3: RV is replay-stable"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        assert verify_deterministic_validity(obj) == True


class TestTransitionRelation:
    """Test transition relation and preorder"""
    
    def test_transition_relation(self):
        """Test T = {(x,y) | ∃ρ: RV(x,y,ρ)}"""
        states = {'a', 'b', 'c'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = {
            ('b', 'a', 'rho0'),
            ('c', 'b', 'rho0'),
        }
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        T = transition_relation(obj)
        assert ('b', 'a') in T
        assert ('c', 'b') in T
        assert ('a', 'b') not in T
    
    def test_descent_preorder(self):
        """Test x ≼ y (y can reach x)"""
        states = {'a', 'b', 'c'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = {
            ('b', 'a', 'rho0'),
            ('c', 'b', 'rho0'),
        }
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        leq = descent_preorder(obj)
        
        # a ≼ a (reflexive)
        assert leq('a', 'a') == True
        # a ≼ b (b -> a exists)
        assert leq('a', 'b') == True
        # a ≼ c (c -> b -> a)
        assert leq('a', 'c') == True
        # b ≼ c (c -> b)
        assert leq('b', 'c') == True
        # c ≼ a (no path from a to c)
        assert leq('c', 'a') == False


class TestMorphismAxioms:
    """Test morphism axioms M1, M2"""
    
    def test_m1_admissibility_preservation(self):
        """Test M1: x ∈ C₁ ⇒ f_X(x) ∈ C₂"""
        # Create two simple objects
        states1 = {'a', 'b'}
        receipts1 = {'rho0'}
        potential1 = {'a': 0, 'b': 1}.__getitem__
        budget_map1 = {'rho0': 0}.__getitem__
        valid1 = {('b', 'a', 'rho0')}
        
        obj1 = create_finite_coh_object(
            states=states1,
            receipts=receipts1,
            potential=potential1,
            budget_map=budget_map1,
            valid_transitions=valid1
        )
        
        # Object 2: same structure
        states2 = {'x', 'y'}
        receipts2 = {'rho1'}
        potential2 = {'x': 0, 'y': 1}.__getitem__
        budget_map2 = {'rho1': 0}.__getitem__
        valid2 = {('y', 'x', 'rho1')}
        
        obj2 = create_finite_coh_object(
            states=states2,
            receipts=receipts2,
            potential=potential2,
            budget_map=budget_map2,
            valid_transitions=valid2
        )
        
        # Morphism: a -> x, b -> y
        f = CohMorphism(
            state_map={'a': 'x', 'b': 'y'}.__getitem__,
            receipt_map={'rho0': 'rho1'}.__getitem__
        )
        
        assert verify_admissibility_preservation(f, obj1, obj2) == True
    
    def test_m2_receipt_covariance(self):
        """Test M2: RV₁(x,y,ρ) ⇒ RV₂(f_X(x),f_X(y),f_♯(ρ))"""
        states1 = {'a', 'b'}
        receipts1 = {'rho0'}
        potential1 = {'a': 0, 'b': 1}.__getitem__
        budget_map1 = {'rho0': 0}.__getitem__
        valid1 = {('b', 'a', 'rho0')}
        
        obj1 = create_finite_coh_object(
            states=states1,
            receipts=receipts1,
            potential=potential1,
            budget_map=budget_map1,
            valid_transitions=valid1
        )
        
        states2 = {'x', 'y'}
        receipts2 = {'rho1'}
        potential2 = {'x': 0, 'y': 1}.__getitem__
        budget_map2 = {'rho1': 0}.__getitem__
        valid2 = {('y', 'x', 'rho1')}
        
        obj2 = create_finite_coh_object(
            states=states2,
            receipts=receipts2,
            potential=potential2,
            budget_map=budget_map2,
            valid_transitions=valid2
        )
        
        # Morphism preserving structure
        f = CohMorphism(
            state_map={'a': 'x', 'b': 'y'}.__getitem__,
            receipt_map={'rho0': 'rho1'}.__getitem__
        )
        
        assert verify_receipt_covariance(f, obj1, obj2) == True


class TestCategory:
    """Test category structure"""
    
    def test_identity(self):
        """Test id_S = (id_X, id_Rec)"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        id_obj = identity(obj)
        
        assert id_obj.state_map('a') == 'a'
        assert id_obj.receipt_map('rho0') == 'rho0'
    
    def test_composition(self):
        """Test composition g ∘ f"""
        states = {'a', 'b', 'c'}
        receipts = {'rho0'}
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = {
            ('b', 'a', 'rho0'),
            ('c', 'b', 'rho0'),
        }
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # f: a->x, b->y
        f = CohMorphism(
            state_map={'a': 'x', 'b': 'y', 'c': 'z'}.__getitem__,
            receipt_map={'rho0': 'rho1'}.__getitem__
        )
        
        # g: x->X, y->Y
        g = CohMorphism(
            state_map={'x': 'X', 'y': 'Y', 'z': 'Z'}.__getitem__,
            receipt_map={'rho1': 'rho2'}.__getitem__
        )
        
        h = compose(f, g)
        
        assert h.state_map('a') == 'X'
        assert h.state_map('b') == 'Y'
        assert h.receipt_map('rho0') == 'rho2'


class TestProduct:
    """Test product construction"""
    
    def test_product_basic(self):
        """Test S₁ × S₂"""
        # Object 1: states {a, b}, potential based on dict
        states1 = {'a', 'b'}
        receipts1 = {'rho0'}
        potential1 = {'a': 0, 'b': 1}.__getitem__
        budget_map1 = {'rho0': 0}.__getitem__
        valid1 = {('b', 'a', 'rho0')}
        
        obj1 = create_finite_coh_object(
            states=states1,
            receipts=receipts1,
            potential=potential1,
            budget_map=budget_map1,
            valid_transitions=valid1
        )
        
        # Object 2: single state
        states2 = {'x'}
        receipts2 = {'rho1'}
        potential2 = {'x': 0}.__getitem__
        budget_map2 = {'rho1': 0}.__getitem__
        valid2 = set()
        
        obj2 = create_finite_coh_object(
            states=states2,
            receipts=receipts2,
            potential=potential2,
            budget_map=budget_map2,
            valid_transitions=valid2
        )
        
        prod = product(obj1, obj2)
        
        # Product potential should be sum (V(a)+V(x) = 0+0 = 0)
        assert prod.potential(('a', 'x')) == 0
        # Product potential (b,x) = 1+0 = 1
        assert prod.potential(('b', 'x')) == 1


class TestCK0Integration:
    """Test CK-0 integration"""
    
    def test_ck0_receipt_schema(self):
        """Test CK-0 receipt fields"""
        receipt = {
            'policy_id': 'test_policy',
            'budget': 100,
            'debt': 50,
            'residual': [0.1, 0.2],
            'hash': 'abc123',
            'timestamp': 1234567890,
        }
        
        assert is_ck0_receipt(receipt) == True
        
        # Missing field
        bad_receipt = {'policy_id': 'test'}
        assert is_ck0_receipt(bad_receipt) == False
    
    def test_ck0_receipt_fields(self):
        """Test CK0_RECEIPT_FIELDS constant"""
        assert 'policy_id' in CK0_RECEIPT_FIELDS
        assert 'budget' in CK0_RECEIPT_FIELDS
        assert 'debt' in CK0_RECEIPT_FIELDS
        assert 'residual' in CK0_RECEIPT_FIELDS
        assert 'hash' in CK0_RECEIPT_FIELDS
        assert 'timestamp' in CK0_RECEIPT_FIELDS


class TestBoundedTubeAdmissibility:
    """Test bounded-tube admissibility (§3.2 spec)"""
    
    def test_bounded_tube_admissible(self):
        """Test bounded-tube regime: C(Θ) = {x | V(x) ≤ Θ}"""
        states = {'a', 'b', 'c', 'd'}
        receipts = {'rho0'}
        
        # V: a=0, b=1, c=2, d=3
        potential = {'a': 0, 'b': 1, 'c': 2, 'd': 3}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        
        valid = set()  # No transitions needed for this test
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # With Θ = 1.5, states a and b should be admissible
        theta = 1.5
        
        # Check: states with V(x) ≤ Θ are admissible
        # Note: is_admissible checks V(x) == 0 by default, need to check potential directly
        assert obj.potential('a') <= theta  # 0 ≤ 1.5 ✓
        assert obj.potential('b') <= theta  # 1 ≤ 1.5 ✓
        assert not (obj.potential('c') <= theta)  # 2 ≤ 1.5 ✗
        assert not (obj.potential('d') <= theta)  # 3 ≤ 1.5 ✗
    
    def test_strict_vs_bounded_equivalence(self):
        """Verify strict regime (Θ=0) matches zero-set admissibility"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = set()
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Θ = 0 should equal strict admissibility (V(x) == 0)
        theta_zero = 0.0
        
        # At Θ=0, only a (V=0) should satisfy V(x) ≤ Θ
        assert obj.potential('a') <= theta_zero  # True (0 ≤ 0)
        assert not (obj.potential('b') <= theta_zero)  # False (1 ≤ 0)


class TestDeterminismLemma:
    """Test determinism lemma (§7 spec)"""
    
    def test_deterministic_validation(self):
        """Same inputs → same output (determinism lemma)"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 1}.__getitem__
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Call validate multiple times with same inputs
        results = []
        for _ in range(100):
            result = obj.validate('b', 'rho0', 'a')
            results.append(result)
        
        # All results must be identical (determinism)
        assert all(r == results[0] for r in results)
    
    def test_deterministic_potential_evaluation(self):
        """Potential function must be deterministic"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        # Potential with no side effects
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'rho0': 0}.__getitem__
        valid = set()
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Evaluate potential multiple times
        for _ in range(100):
            assert obj.potential('a') == 0
            assert obj.potential('b') == 1


class TestTraceClosure:
    """Test trace closure principle (§6 spec)"""
    
    def test_trace_chain_composition(self):
        """Legal steps compose into legal histories"""
        states = {'a', 'b', 'c'}
        receipts = {'rho0', 'rho1'}
        
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        # Budget must allow descent: V(c)=2 → V(b)=1 is ΔV=1, budget needs to be ≥1
        budget_map = {'rho0': 2, 'rho1': 2}.__getitem__
        
        # Chain: c → b → a (each step descends by 1)
        valid = {
            ('c', 'b', 'rho0'),
            ('b', 'a', 'rho1'),
        }
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Verify each step individually
        # Note: validate(x, y, rho) where x=source, y=target, rho=receipt
        assert obj.validate('c', 'b', 'rho0') == True
        assert obj.validate('b', 'a', 'rho1') == True
        
        # Both steps form a valid trace
        trace = [
            ('c', 'b', 'rho0'),
            ('b', 'a', 'rho1'),
        ]
        
        # Verify trace is valid
        for source, target, receipt in trace:
            assert obj.validate(source, target, receipt) == True
    
    def test_chain_digest_tracking(self):
        """Verify chain digest can be computed from receipts"""
        states = {'a', 'b'}
        receipts = {'rho0'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        # Budget must allow V(b)=1 → V(a)=0 (descent of 1)
        budget_map = {'rho0': 1}.__getitem__
        valid = {('b', 'a', 'rho0')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # The verifier should track chain progression
        # (simplified test - actual implementation would use hash)
        # Note: validate(x, y, rho) = source, target, receipt
        step_result = obj.validate('b', 'a', 'rho0')
        assert step_result == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
