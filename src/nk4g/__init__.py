# NK-4G - Governance Certificate Verification

"""
NK-4G is the audit protocol layer that consumes ASG spectral certificates
and verifies consistency with policy thresholds.

Core responsibilities:
- Verify NK-4G receipt fields
- Check spectral certificate consistency
- Enforce policy thresholds (κ₀, margin)
"""

from .receipt_fields import NK4GReceiptExtension, NK4GReceiptSchema
from .verifier import NK4GVerifier, VerificationResult
from .policy import NK4GPolicyKeys, NK4GPolicyBundle

__all__ = [
    "NK4GReceiptExtension",
    "NK4GReceiptSchema", 
    "NK4GVerifier",
    "VerificationResult",
    "NK4GPolicyKeys",
    "NK4GPolicyBundle",
]
