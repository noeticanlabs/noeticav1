# NK-1 Unit Tests: Policy Bundle

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.policy_bundle import (
    PolicyBundle, GLBMode, FloatPolicy, HashMode, StateEqMode,
    DEFAULT_POLICY, policy_digest_constant_check, validate_policy_chain
)


class TestPolicyBundle(unittest.TestCase):
    """Test PolicyBundle."""
    
    def test_default_policy(self):
        self.assertEqual(DEFAULT_POLICY.glb_mode, GLBMode.STATIC_PLUS_TRAP)
        self.assertEqual(DEFAULT_POLICY.float_policy, FloatPolicy.REJECT)
        self.assertEqual(DEFAULT_POLICY.hash_mode, HashMode.SHA3_256)
        self.assertEqual(DEFAULT_POLICY.debt_scale, 1000)
    
    def test_compute_digest(self):
        digest = DEFAULT_POLICY.compute_digest()
        self.assertTrue(digest.startswith("h:"))
        self.assertEqual(len(digest), 66)
    
    def test_digest_cached(self):
        d1 = DEFAULT_POLICY.compute_digest()
        d2 = DEFAULT_POLICY.compute_digest()
        self.assertEqual(d1, d2)
    
    def test_bind_to_receipt(self):
        binding = DEFAULT_POLICY.bind_to_receipt()
        self.assertIn('policy_digest', binding)
        self.assertIn('glb_mode_id', binding)
        self.assertIn('debt_scale', binding)
    
    def test_validate(self):
        self.assertTrue(DEFAULT_POLICY.validate())
    
    def test_invalid_debt_scale(self):
        pb = PolicyBundle(debt_scale=0)
        self.assertFalse(pb.validate())


class TestPolicyBundleFromDict(unittest.TestCase):
    """Test PolicyBundle from_dict."""
    
    def test_from_dict(self):
        data = {
            'glb_mode': 'static',
            'float_policy': 'reject',
            'hash_mode': 'sha3_256',
            'state_eq_mode': 'hash_canon.v1',
            'debt_scale': 1000
        }
        pb = PolicyBundle.from_dict(data)
        self.assertEqual(pb.glb_mode, GLBMode.STATIC)
        self.assertEqual(pb.float_policy, FloatPolicy.REJECT)


class TestPolicyDigestConstantCheck(unittest.TestCase):
    """Test policy digest constant check."""
    
    def test_same_digest(self):
        self.assertTrue(policy_digest_constant_check("h:abc123", "h:abc123"))
    
    def test_different_digest(self):
        self.assertFalse(policy_digest_constant_check("h:abc123", "h:def456"))


class TestValidatePolicyChain(unittest.TestCase):
    """Test policy chain validation."""
    
    def test_empty_chain(self):
        self.assertTrue(validate_policy_chain([]))
    
    def test_single_policy(self):
        self.assertTrue(validate_policy_chain([DEFAULT_POLICY]))
    
    def test_identical_policies(self):
        pb1 = PolicyBundle()
        pb2 = PolicyBundle()
        self.assertTrue(validate_policy_chain([pb1, pb2]))
    
    def test_different_policies(self):
        pb1 = PolicyBundle(debt_scale=1000)
        pb2 = PolicyBundle(debt_scale=2000)
        self.assertFalse(validate_policy_chain([pb1, pb2]))


if __name__ == '__main__':
    unittest.main()
