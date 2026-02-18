# NK-4G Receipt Fields - Spectral Certificate Schema

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ProjectorType(Enum):
    """Projector type identifiers"""
    MEAN_ZERO_THETA_V1 = "mean_zero_theta_v1"
    MEAN_ZERO_THETA_V2 = "mean_zero_theta_v2"
    ASG_THETA_MEAN_ZERO_V1 = "asg.projector.theta_mean_zero.v1"
    CUSTOM = "custom"


class EstimationMethod(Enum):
    """κ₀ estimation method identifiers"""
    EIGSH = "eigsh"
    LOBPCG = "lobpcg"
    POWER = "power"
    EXACT = "exact"
    EIGSH_SMALLEST_SA_V1 = "eigsh_smallest_sa.v1"


@dataclass
class ASGCertificate:
    """ASG certificate fields for NK-4G receipts.
    
    This is the first-class ASG integration that NK-4G consumes.
    """
    # Model identification
    model_id: str = "asg.zeta-theta-rho-G.v1"
    
    # Operator identification
    operator_digest: str = ""
    projector_id: str = "asg.projector.4n_state_perp.v1"
    
    # Spectral certificates
    kappa_est: float = 0.0
    kappa_method_id: str = "eigsh_smallest_sa.v1"
    kappa_tol: float = 1e-6
    kappa_maxiter: int = 1000
    
    # Semantic certificate
    gamma_sem: float = 0.0
    semantic_dir_id: str = "asg.semantic.thetaG_rotation.v1"
    semantic_margin: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "model_id": self.model_id,
            "operator_digest": self.operator_digest,
            "projector_id": self.projector_id,
            "kappa_est": self.kappa_est,
            "kappa_method_id": self.kappa_method_id,
            "kappa_tol": self.kappa_tol,
            "kappa_maxiter": self.kappa_maxiter,
            "gamma_sem": self.gamma_sem,
            "semantic_dir_id": self.semantic_dir_id,
            "semantic_margin": self.semantic_margin,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ASGCertificate":
        """Create from dictionary"""
        return cls(
            model_id=data.get("model_id", "asg.zeta-theta-rho-G.v1"),
            operator_digest=data.get("operator_digest", ""),
            projector_id=data.get("projector_id", "asg.projector.theta_mean_zero.v1"),
            kappa_est=data.get("kappa_est", 0.0),
            kappa_method_id=data.get("kappa_method_id", "eigsh_smallest_sa.v1"),
            kappa_tol=data.get("kappa_tol", 1e-6),
            kappa_maxiter=data.get("kappa_maxiter", 1000),
            gamma_sem=data.get("gamma_sem", 0.0),
            semantic_dir_id=data.get("semantic_dir_id", "asg.semantic.thetaG_rotation.v1"),
            semantic_margin=data.get("semantic_margin", 0.0),
        )


@dataclass
class NK4GReceiptExtension:
    """NK-4G specific receipt fields for spectral certificates.
    
    These fields are added to the base receipt to provide spectral
    governance certificates from ASG.
    """
    # Spectral quantities
    kappa_est: float              # κ₀ = λ_min(H_⊥) estimate
    gamma_sem: float             # Γ_sem: semantic Rayleigh quotient
    semantic_margin: float        # M = Γ_sem / κ₀
    
    # Operator identification
    projector_id: str             # e.g., "mean_zero_theta_v1"
    operator_digest: str         # SHA-256 of operator structure
    
    # Estimation metadata
    estimation_method: str        # "eigsh", "lobpcg", "exact"
    
    # Gate results
    spectral_gate_passed: bool    # Whether κ₀ ≥ NK4G_KAPPA_MIN
    margin_warned: bool          # Whether margin < NK4G_MARGIN_MIN
    
    # Provenance
    state_hash: str              # Hash of input state
    params_hash: str             # Hash of ASG parameters
    
    # Optional extended fields
    condition_number: Optional[float] = None    # κ(H_⊥)
    eigenvalue_spectrum: Optional[List[float]] = None  # Full spectrum (if small)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "kappa_est": self.kappa_est,
            "gamma_sem": self.gamma_sem,
            "semantic_margin": self.semantic_margin,
            "projector_id": self.projector_id,
            "operator_digest": self.operator_digest,
            "estimation_method": self.estimation_method,
            "spectral_gate_passed": self.spectral_gate_passed,
            "margin_warned": self.margin_warned,
            "state_hash": self.state_hash,
            "params_hash": self.params_hash,
        }
        
        if self.condition_number is not None:
            result["condition_number"] = self.condition_number
            
        if self.eigenvalue_spectrum is not None:
            result["eigenvalue_spectrum"] = self.eigenvalue_spectrum
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NK4GReceiptExtension":
        """Create from dictionary"""
        return cls(
            kappa_est=data["kappa_est"],
            gamma_sem=data["gamma_sem"],
            semantic_margin=data["semantic_margin"],
            projector_id=data["projector_id"],
            operator_digest=data["operator_digest"],
            estimation_method=data["estimation_method"],
            spectral_gate_passed=data["spectral_gate_passed"],
            margin_warned=data["margin_warned"],
            state_hash=data["state_hash"],
            params_hash=data["params_hash"],
            condition_number=data.get("condition_number"),
            eigenvalue_spectrum=data.get("eigenvalue_spectrum"),
        )
    
    def validate(self) -> List[str]:
        """Validate receipt fields.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check κ₀ is non-negative
        if self.kappa_est < 0:
            errors.append(f"kappa_est must be non-negative, got {self.kappa_est}")
        
        # Check Γ_sem is non-negative
        if self.gamma_sem < 0:
            errors.append(f"gamma_sem must be non-negative, got {self.gamma_sem}")
        
        # Check margin is non-negative
        if self.semantic_margin < 0:
            errors.append(f"semantic_margin must be non-negative, got {self.semantic_margin}")
        
        # Check projector_id is not empty
        if not self.projector_id:
            errors.append("projector_id cannot be empty")
        
        # Check operator_digest is valid hex
        if len(self.operator_digest) != 64:
            errors.append(f"operator_digest must be 64 hex chars, got {len(self.operator_digest)}")
        
        # Check estimation_method is valid
        valid_methods = [e.value for e in EstimationMethod]
        if self.estimation_method not in valid_methods:
            errors.append(f"estimation_method must be one of {valid_methods}")
        
        # Check hashes are valid hex
        if len(self.state_hash) != 64:
            errors.append(f"state_hash must be 64 hex chars, got {len(self.state_hash)}")
        if len(self.params_hash) != 64:
            errors.append(f"params_hash must be 64 hex chars, got {len(self.params_hash)}")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if receipt is valid"""
        return len(self.validate()) == 0


@dataclass
class NK4GReceiptSchema:
    """Complete NK-4G receipt schema.
    
    This combines the base receipt with NK-4G extensions.
    """
    # Step identification
    step_index: int
    module_id: str
    
    # Base NEC fields
    v_before: float
    v_after: float
    v_drift: float              # V(z_k) - drift point violation
    x_before_hash: str
    x_after_hash: str
    z_k_hash: str               # Drift point hash
    lambda_k: float             # Prox parameter
    
    # NK-4G spectral extension
    spectral: NK4GReceiptExtension
    
    # Metadata
    timestamp: str
    chain_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to full receipt dictionary"""
        return {
            "step_index": self.step_index,
            "module_id": self.module_id,
            "v_before": self.v_before,
            "v_after": self.v_after,
            "v_drift": self.v_drift,
            "x_before_hash": self.x_before_hash,
            "x_after_hash": self.x_after_hash,
            "z_k_hash": self.z_k_hash,
            "lambda_k": self.lambda_k,
            "spectral": self.spectral.to_dict(),
            "timestamp": self.timestamp,
            "chain_id": self.chain_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NK4GReceiptSchema":
        """Create from dictionary"""
        spectral = NK4GReceiptExtension.from_dict(data["spectral"])
        return cls(
            step_index=data["step_index"],
            module_id=data["module_id"],
            v_before=data["v_before"],
            v_after=data["v_after"],
            v_drift=data["v_drift"],
            x_before_hash=data["x_before_hash"],
            x_after_hash=data["x_after_hash"],
            z_k_hash=data["z_k_hash"],
            lambda_k=data["lambda_k"],
            spectral=spectral,
            timestamp=data["timestamp"],
            chain_id=data["chain_id"],
        )


# Default threshold values
DEFAULT_KAPPA_MIN = 1e-6
DEFAULT_MARGIN_MIN = 1.0


def create_default_receipt_extension(
    kappa_est: float,
    gamma_sem: float,
    margin: float,
    projector_id: str,
    operator_digest: str,
    estimation_method: str,
    state_hash: str,
    params_hash: str,
    kappa_min: float = DEFAULT_KAPPA_MIN,
    margin_min: float = DEFAULT_MARGIN_MIN
) -> NK4GReceiptExtension:
    """Factory to create NK4GReceiptExtension with default gate decisions.
    
    Args:
        kappa_est: κ₀ estimate
        gamma_sem: Γ_sem
        margin: M = Γ_sem / κ₀
        projector_id: Projector identifier
        operator_digest: Operator digest
        estimation_method: Estimation method
        state_hash: State hash
        params_hash: Parameters hash
        kappa_min: Minimum κ₀ threshold
        margin_min: Minimum margin threshold
        
    Returns:
        NK4GReceiptExtension with gate decisions
    """
    spectral_gate_passed = kappa_est >= kappa_min
    margin_warned = margin < margin_min
    
    return NK4GReceiptExtension(
        kappa_est=kappa_est,
        gamma_sem=gamma_sem,
        semantic_margin=margin,
        projector_id=projector_id,
        operator_digest=operator_digest,
        estimation_method=estimation_method,
        spectral_gate_passed=spectral_gate_passed,
        margin_warned=margin_warned,
        state_hash=state_hash,
        params_hash=params_hash,
    )
