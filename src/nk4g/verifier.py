# NK-4G Verifier - Receipt Verification

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from .receipt_fields import (
    NK4GReceiptExtension, 
    NK4GReceiptSchema,
    DEFAULT_KAPPA_MIN,
    DEFAULT_MARGIN_MIN,
)


class VerificationResult(Enum):
    """Verification result codes"""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class VerificationError:
    """Verification error details"""
    code: str
    message: str
    field: Optional[str] = None
    
    def __str__(self):
        if self.field:
            return f"{self.code}: {self.field} - {self.message}"
        return f"{self.code}: {self.message}"


@dataclass
class VerificationReport:
    """Complete verification report"""
    result: VerificationResult
    errors: List[VerificationError]
    warnings: List[str]
    details: Dict[str, Any]
    
    @property
    def passed(self) -> bool:
        return self.result == VerificationResult.PASS
    
    @property
    def failed(self) -> bool:
        return self.result == VerificationResult.FAIL
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def summary(self) -> str:
        """Generate human-readable summary"""
        lines = [f"Verification: {self.result.value}"]
        
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  - {e}")
        
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")
        
        return "\n".join(lines)


class NK4GVerifier:
    """Verify NK-4G receipt consistency.
    
    The verifier checks:
    1. Receipt field validity (schema compliance)
    2. Spectral certificate consistency
    3. Policy threshold enforcement
    4. Prox witness inequality fields
    """
    
    def __init__(
        self,
        kappa_min: float = DEFAULT_KAPPA_MIN,
        margin_min: float = DEFAULT_MARGIN_MIN,
        strict: bool = False
    ):
        """Initialize verifier.
        
        Args:
            kappa_min: Minimum κ₀ threshold
            margin_min: Minimum semantic margin threshold
            strict: If True, warnings are treated as failures
        """
        self.kappa_min = kappa_min
        self.margin_min = margin_min
        self.strict = strict
    
    def verify_receipt_fields(self, receipt: NK4GReceiptExtension) -> VerificationReport:
        """Verify receipt field validity (schema compliance).
        
        Args:
            receipt: Receipt to verify
            
        Returns:
            VerificationReport
        """
        errors = []
        warnings = []
        
        # Use the receipt's built-in validation
        field_errors = receipt.validate()
        for err in field_errors:
            errors.append(VerificationError(
                code="SCHEMA_ERROR",
                message=err
            ))
        
        # Additional checks
        # Check κ₀ is reasonable
        if receipt.kappa_est > 1e10:
            warnings.append("kappa_est unusually large (>1e10)")
        
        if receipt.kappa_est < 1e-10 and receipt.kappa_est > 0:
            warnings.append("kappa_est very small but positive")
        
        # Check Γ_sem vs κ₀ relationship
        if receipt.semantic_margin > 0 and receipt.kappa_est < 1e-10:
            warnings.append("positive margin with near-zero kappa - verify computation")
        
        result = VerificationResult.PASS if not errors else VerificationResult.FAIL
        if self.strict and warnings:
            result = VerificationResult.WARN
        
        return VerificationReport(
            result=result,
            errors=errors,
            warnings=warnings,
            details={"field_validation": True}
        )
    
    def verify_spectral_certificate(self, receipt: NK4GReceiptExtension) -> VerificationReport:
        """Verify spectral certificate consistency.
        
        Args:
            receipt: Receipt to verify
            
        Returns:
            VerificationReport
        """
        errors = []
        warnings = []
        
        # Check κ₀ ≥ 0
        if receipt.kappa_est < 0:
            errors.append(VerificationError(
                code="NEGATIVE_KAPPA",
                message="kappa_est must be non-negative",
                field="kappa_est"
            ))
        
        # Check Γ_sem ≥ 0
        if receipt.gamma_sem < 0:
            errors.append(VerificationError(
                code="NEGATIVE_GAMMA",
                message="gamma_sem must be non-negative",
                field="gamma_sem"
            ))
        
        # Check margin is consistent: M = Γ/κ
        if receipt.kappa_est > 1e-10:
            expected_margin = receipt.gamma_sem / receipt.kappa_est
            margin_error = abs(receipt.semantic_margin - expected_margin)
            if margin_error > 1e-6:
                errors.append(VerificationError(
                    code="MARGIN_MISMATCH",
                    message=f"margin inconsistency: expected {expected_margin}, got {receipt.semantic_margin}",
                    field="semantic_margin"
                ))
        
        # Check operator digest format
        if len(receipt.operator_digest) != 64:
            errors.append(VerificationError(
                code="INVALID_DIGEST",
                message="operator_digest must be 64 hex characters",
                field="operator_digest"
            ))
        
        result = VerificationResult.PASS if not errors else VerificationResult.FAIL
        
        return VerificationReport(
            result=result,
            errors=errors,
            warnings=warnings,
            details={
                "kappa_est": receipt.kappa_est,
                "gamma_sem": receipt.gamma_sem,
                "margin": receipt.semantic_margin,
            }
        )
    
    def verify_policy_thresholds(
        self,
        receipt: NK4GReceiptExtension,
        kappa_min: Optional[float] = None,
        margin_min: Optional[float] = None
    ) -> VerificationReport:
        """Verify policy threshold enforcement.
        
        Args:
            receipt: Receipt to verify
            kappa_min: Override minimum κ₀ threshold
            margin_min: Override minimum margin threshold
            
        Returns:
            VerificationReport
        """
        errors = []
        warnings = []
        
        kappa = kappa_min if kappa_min is not None else self.kappa_min
        margin = margin_min if margin_min is not None else self.margin_min
        
        # Check κ₀ threshold
        if receipt.kappa_est < kappa:
            errors.append(VerificationError(
                code="KAPPA_BELOW_THRESHOLD",
                message=f"kappa_est {receipt.kappa_est} < minimum {kappa}",
                field="kappa_est"
            ))
        
        # Check margin threshold (warning only, not fatal)
        if receipt.semantic_margin < margin:
            warnings.append(
                f"semantic_margin {receipt.semantic_margin} < recommended {margin}"
            )
        
        # Check estimation method is recognized
        valid_methods = ["eigsh", "lobpcg", "power", "exact"]
        if receipt.estimation_method not in valid_methods:
            warnings.append(
                f"unrecognized estimation_method: {receipt.estimation_method}"
            )
        
        result = VerificationResult.PASS
        if errors:
            result = VerificationResult.FAIL
        elif warnings and self.strict:
            result = VerificationResult.WARN
        
        return VerificationReport(
            result=result,
            errors=errors,
            warnings=warnings,
            details={
                "kappa_min": kappa,
                "margin_min": margin,
                "kappa_passed": receipt.kappa_est >= kappa,
                "margin_passed": receipt.semantic_margin >= margin,
            }
        )
    
    def verify_prox_witness(self, receipt: NK4GReceiptSchema) -> VerificationReport:
        """Verify prox witness inequality fields are consistent.
        
        Args:
            receipt: Full receipt with NEC fields
            
        Returns:
            VerificationReport
        """
        errors = []
        warnings = []
        
        # Check that V values are consistent
        if receipt.v_drift < receipt.v_before:
            warnings.append(
                f"V(drift) < V(before): drift increased violation "
                f"({receipt.v_drift} < {receipt.v_before})"
            )
        
        if receipt.v_after > receipt.v_drift:
            errors.append(VerificationError(
                code="VIOLATION_INCREASED",
                message=f"V(after) > V(drift): correction failed to reduce violation",
                field="v_after"
            ))
        
        # Check λ_k is positive
        if receipt.lambda_k <= 0:
            errors.append(VerificationError(
                code="INVALID_LAMBDA",
                message="lambda_k must be positive",
                field="lambda_k"
            ))
        
        # Check hashes are present
        if not receipt.z_k_hash:
            errors.append(VerificationError(
                code="MISSING_Z_HASH",
                message="z_k_hash is required for drift point verification",
                field="z_k_hash"
            ))
        
        result = VerificationResult.PASS if not errors else VerificationResult.FAIL
        
        return VerificationReport(
            result=result,
            errors=errors,
            warnings=warnings,
            details={
                "v_before": receipt.v_before,
                "v_drift": receipt.v_drift,
                "v_after": receipt.v_after,
                "lambda_k": receipt.lambda_k,
            }
        )
    
    def verify_complete(
        self,
        receipt: NK4GReceiptExtension,
        full_receipt: Optional[NK4GReceiptSchema] = None,
        kappa_min: Optional[float] = None,
        margin_min: Optional[float] = None
    ) -> VerificationReport:
        """Run all verification checks.
        
        Args:
            receipt: NK-4G receipt extension
            full_receipt: Optional full receipt with NEC fields
            kappa_min: Optional κ₀ threshold override
            margin_min: Optional margin threshold override
            
        Returns:
            Combined VerificationReport
        """
        all_errors = []
        all_warnings = []
        all_details = {}
        
        # Field validation
        field_report = self.verify_receipt_fields(receipt)
        all_errors.extend(field_report.errors)
        all_warnings.extend(field_report.warnings)
        all_details["field_validation"] = field_report.passed
        
        # Spectral certificate
        spectral_report = self.verify_spectral_certificate(receipt)
        all_errors.extend(spectral_report.errors)
        all_warnings.extend(spectral_report.warnings)
        all_details["spectral_certificate"] = spectral_report.passed
        
        # Policy thresholds
        policy_report = self.verify_policy_thresholds(
            receipt, kappa_min, margin_min
        )
        all_errors.extend(policy_report.errors)
        all_warnings.extend(policy_report.warnings)
        all_details["policy_thresholds"] = policy_report.passed
        
        # Prox witness (if full receipt provided)
        if full_receipt is not None:
            prox_report = self.verify_prox_witness(full_receipt)
            all_errors.extend(prox_report.errors)
            all_warnings.extend(prox_report.warnings)
            all_details["prox_witness"] = prox_report.passed
        
        # Determine final result
        if all_errors:
            result = VerificationResult.FAIL
        elif all_warnings and self.strict:
            result = VerificationResult.WARN
        else:
            result = VerificationResult.PASS
        
        return VerificationReport(
            result=result,
            errors=all_errors,
            warnings=all_warnings,
            details=all_details
        )


def create_verifier(
    kappa_min: float = DEFAULT_KAPPA_MIN,
    margin_min: float = DEFAULT_MARGIN_MIN,
    strict: bool = False
) -> NK4GVerifier:
    """Factory to create NK4GVerifier.
    
    Args:
        kappa_min: Minimum κ₀ threshold
        margin_min: Minimum semantic margin
        strict: Strict mode (warnings = failures)
        
    Returns:
        Configured verifier
    """
    return NK4GVerifier(
        kappa_min=kappa_min,
        margin_min=margin_min,
        strict=strict,
    )
