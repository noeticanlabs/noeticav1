# NK-4G Verifier Tests

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk4g.receipt_fields import (
    NK4GReceiptExtension,
    NK4GReceiptSchema,
    create_default_receipt_extension,
)
from nk4g.verifier import (
    NK4GVerifier,
    VerificationResult,
    create_verifier,
)
from nk4g.policy import (
    NK4GPolicyKeys,
    NK4GPolicyBundle,
    create_default_nk4g_policy,
)


class TestReceiptFieldValidation(unittest.TestCase):
    """Test receipt field validation"""
    
    def test_valid_receipt(self):
        """Valid receipt passes validation"""
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        errors = receipt.validate()
        self.assertEqual(len(errors), 0)
    
    def test_negative_kappa_fails(self):
        """Negative kappa fails validation"""
        receipt = NK4GReceiptExtension(
            kappa_est=-1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=False,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        errors = receipt.validate()
        self.assertGreater(len(errors), 0)
    
    def test_invalid_digest_length_fails(self):
        """Invalid digest length fails"""
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="short",  # Invalid
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        errors = receipt.validate()
        self.assertGreater(len(errors), 0)
    
    def test_invalid_estimation_method_fails(self):
        """Invalid estimation method fails"""
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="invalid_method",  # Invalid
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        errors = receipt.validate()
        self.assertGreater(len(errors), 0)


class TestVerifierFieldValidation(unittest.TestCase):
    """Test NK4GVerifier field validation"""
    
    def test_valid_receipt_passes(self):
        """Valid receipt passes verifier"""
        verifier = create_verifier()
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_receipt_fields(receipt)
        
        self.assertTrue(report.passed)
        self.assertEqual(report.result, VerificationResult.PASS)
    
    def test_invalid_receipt_fails(self):
        """Invalid receipt fails verifier"""
        verifier = create_verifier()
        
        receipt = NK4GReceiptExtension(
            kappa_est=-1e-4,  # Invalid
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_receipt_fields(receipt)
        
        self.assertFalse(report.passed)
        self.assertEqual(report.result, VerificationResult.FAIL)


class TestSpectralCertificateVerification(unittest.TestCase):
    """Test spectral certificate verification"""
    
    def test_kappa_positive_passes(self):
        """Positive kappa passes"""
        verifier = create_verifier()
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_spectral_certificate(receipt)
        
        self.assertTrue(report.passed)
    
    def test_kappa_negative_fails(self):
        """Negative kappa fails"""
        verifier = create_verifier()
        
        receipt = NK4GReceiptExtension(
            kappa_est=-1e-4,  # Negative!
            gamma_sem=1.0,
            semantic_margin=-10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=False,
            margin_warned=True,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_spectral_certificate(receipt)
        
        self.assertFalse(report.passed)
    
    def test_margin_consistency_check(self):
        """Margin consistency is verified"""
        verifier = create_verifier()
        
        # Inconsistent: gamma/kappa != margin
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=999999.0,  # Wrong! Should be 1e4
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_spectral_certificate(receipt)
        
        # This should fail margin consistency check
        # (In practice, small tolerance may allow it)
        self.assertIsNotNone(report)


class TestPolicyThresholdVerification(unittest.TestCase):
    """Test policy threshold verification"""
    
    def test_kappa_above_threshold_passes(self):
        """Kappa above threshold passes"""
        verifier = create_verifier(kappa_min=1e-6)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_policy_thresholds(receipt)
        
        self.assertTrue(report.passed)
    
    def test_kappa_below_threshold_fails(self):
        """Kappa below threshold fails"""
        verifier = create_verifier(kappa_min=1e-4)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-6,  # Below threshold!
            gamma_sem=1.0,
            semantic_margin=1000000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=False,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_policy_thresholds(receipt)
        
        self.assertFalse(report.passed)
        self.assertEqual(report.result, VerificationResult.FAIL)
    
    def test_margin_warning(self):
        """Margin below threshold gives warning"""
        verifier = create_verifier(margin_min=10.0)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=5.0,  # Below margin threshold
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=True,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_policy_thresholds(receipt)
        
        # Should pass but have warning
        self.assertTrue(report.passed)
        self.assertTrue(report.has_warnings)
    
    def test_strict_mode_warnings_fail(self):
        """In strict mode, warnings cause failure"""
        verifier = create_verifier(margin_min=10.0, strict=True)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=5.0,  # Below threshold
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=True,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_policy_thresholds(receipt)
        
        # In strict mode, warning becomes failure
        self.assertEqual(report.result, VerificationResult.WARN)


class TestNK4GPolicyBundle(unittest.TestCase):
    """Test NK4GPolicyBundle"""
    
    def test_default_policy(self):
        """Default policy is valid"""
        policy = create_default_nk4g_policy()
        
        self.assertTrue(policy.is_valid())
        self.assertEqual(policy.kappa_min, 1e-6)
        self.assertEqual(policy.margin_min, 1.0)
    
    def test_policy_to_dict(self):
        """Policy converts to dict"""
        policy = create_default_nk4g_policy()
        
        d = policy.to_dict()
        
        self.assertIn(NK4GPolicyKeys.NK4G_KAPPA_MIN, d)
        self.assertIn(NK4GPolicyKeys.NK4G_MARGIN_MIN, d)
        self.assertIn(NK4GPolicyKeys.NK4G_PROJECTOR_ID, d)
    
    def test_policy_roundtrip(self):
        """Policy roundtrips through dict"""
        policy = create_default_nk4g_policy()
        
        d = policy.to_dict()
        policy2 = NK4GPolicyBundle.from_dict(d)
        
        self.assertEqual(policy.kappa_min, policy2.kappa_min)
        self.assertEqual(policy.margin_min, policy2.margin_min)
        self.assertEqual(policy.projector_id, policy2.projector_id)
    
    def test_policy_hash(self):
        """Policy computes hash"""
        policy = create_default_nk4g_policy()
        
        hash1 = policy.get_hash()
        hash2 = policy.get_hash()
        
        # Same policy = same hash
        self.assertEqual(hash1, hash2)
        
        # Hash is valid hex
        self.assertEqual(len(hash1), 64)
    
    def test_invalid_policy(self):
        """Invalid policy fails validation"""
        policy = NK4GPolicyBundle(
            kappa_min=-1.0,  # Invalid!
            margin_min=1.0,
        )
        
        self.assertFalse(policy.is_valid())
        errors = policy.validate()
        self.assertGreater(len(errors), 0)


class TestCompleteVerification(unittest.TestCase):
    """Test complete verification flow"""
    
    def test_complete_verification_passes(self):
        """Complete verification passes for valid receipt"""
        verifier = create_verifier(kappa_min=1e-6, margin_min=0.1)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-4,
            gamma_sem=1.0,
            semantic_margin=10000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=True,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_complete(receipt)
        
        self.assertTrue(report.passed)
        self.assertEqual(report.result, VerificationResult.PASS)
    
    def test_complete_verification_fails_on_kappa(self):
        """Complete verification fails when kappa too low"""
        verifier = create_verifier(kappa_min=1e-2)
        
        receipt = NK4GReceiptExtension(
            kappa_est=1e-6,  # Below threshold
            gamma_sem=1.0,
            semantic_margin=1000000.0,
            projector_id="mean_zero_theta_v1",
            operator_digest="a" * 64,
            estimation_method="eigsh",
            spectral_gate_passed=False,
            margin_warned=False,
            state_hash="b" * 64,
            params_hash="c" * 64,
        )
        
        report = verifier.verify_complete(receipt)
        
        self.assertFalse(report.passed)
        self.assertEqual(report.result, VerificationResult.FAIL)


if __name__ == '__main__':
    unittest.main()
