# NK-4G Policy - Governance Threshold Definitions

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class NK4GPolicyKeys:
    """Policy keys for NK-4G/ASG governance.
    
    These keys are used in PolicyBundle to specify spectral
    certificate requirements.
    """
    
    # Spectral thresholds
    NK4G_KAPPA_MIN = "nk4g_kappa_min"           # Minimum κ₀ threshold
    NK4G_MARGIN_MIN = "nk4g_margin_min"         # Minimum semantic margin
    
    # Operator configuration
    NK4G_PROJECTOR_ID = "nk4g_projector_id"      # Required projector type
    NK4G_ESTIMATION_METHOD = "nk4g_estimation_method"  # κ₀ estimation method
    
    # ASG model configuration
    ASG_MODEL_ID = "asg_model_id"                # Residual architecture version
    ASG_TOPOLOGY = "asg_topology"               # 1d_ring or 2d_torus
    
    # Alpha parameters
    ASG_ALPHA_L = "asg_alpha_l"                 # Linguistic coupling strength
    ASG_ALPHA_G = "asg_alpha_g"                 # Gradient coupling strength
    ASG_W_THETA = "asg_w_theta"                 # Theta penalty weight
    
    # State configuration
    ASG_STATE_DIM = "asg_state_dim"              # System size N
    
    # Verification settings
    NK4G_STRICT_MODE = "nk4g_strict_mode"       # Treat warnings as errors
    NK4G_VERIFY_PROX = "nk4g_verify_prox"       # Verify prox witness
    
    @classmethod
    def all_keys(cls) -> List[str]:
        """Return all policy keys"""
        return [
            cls.NK4G_KAPPA_MIN,
            cls.NK4G_MARGIN_MIN,
            cls.NK4G_PROJECTOR_ID,
            cls.NK4G_ESTIMATION_METHOD,
            cls.ASG_MODEL_ID,
            cls.ASG_TOPOLOGY,
            cls.ASG_ALPHA_L,
            cls.ASG_ALPHA_G,
            cls.ASG_W_THETA,
            cls.ASG_STATE_DIM,
            cls.NK4G_STRICT_MODE,
            cls.NK4G_VERIFY_PROX,
        ]


class ProjectorType(Enum):
    """Supported projector types"""
    MEAN_ZERO_THETA = "mean_zero_theta"
    CUSTOM = "custom"


class EstimationMethod(Enum):
    """Supported κ₀ estimation methods"""
    EIGSH = "eigsh"
    LOBPCG = "lobpcg"
    POWER = "power"
    EXACT = "exact"


@dataclass
class NK4GPolicyBundle:
    """NK-4G policy bundle with spectral governance settings.
    
    This extends the base PolicyBundle with NK-4G specific settings.
    """
    # Spectral thresholds
    kappa_min: float = 1e-6
    margin_min: float = 1.0
    
    # Operator settings
    projector_id: str = "mean_zero_theta_v1"
    estimation_method: str = "eigsh"
    
    # ASG model
    model_id: str = "asg_v1"
    topology: str = "1d_ring"
    
    # ASG parameters
    alpha_l: float = 1.0
    alpha_g: float = 1.0
    w_theta: float = 1.0
    state_dim: int = 32
    
    # Verification
    strict_mode: bool = False
    verify_prox: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to policy dictionary"""
        return {
            NK4GPolicyKeys.NK4G_KAPPA_MIN: self.kappa_min,
            NK4GPolicyKeys.NK4G_MARGIN_MIN: self.margin_min,
            NK4GPolicyKeys.NK4G_PROJECTOR_ID: self.projector_id,
            NK4GPolicyKeys.NK4G_ESTIMATION_METHOD: self.estimation_method,
            NK4GPolicyKeys.ASG_MODEL_ID: self.model_id,
            NK4GPolicyKeys.ASG_TOPOLOGY: self.topology,
            NK4GPolicyKeys.ASG_ALPHA_L: self.alpha_l,
            NK4GPolicyKeys.ASG_ALPHA_G: self.alpha_g,
            NK4GPolicyKeys.ASG_W_THETA: self.w_theta,
            NK4GPolicyKeys.ASG_STATE_DIM: self.state_dim,
            NK4GPolicyKeys.NK4G_STRICT_MODE: self.strict_mode,
            NK4GPolicyKeys.NK4G_VERIFY_PROX: self.verify_prox,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NK4GPolicyBundle":
        """Create from policy dictionary"""
        return cls(
            kappa_min=data.get(NK4GPolicyKeys.NK4G_KAPPA_MIN, 1e-6),
            margin_min=data.get(NK4GPolicyKeys.NK4G_MARGIN_MIN, 1.0),
            projector_id=data.get(NK4GPolicyKeys.NK4G_PROJECTOR_ID, "mean_zero_theta_v1"),
            estimation_method=data.get(NK4GPolicyKeys.NK4G_ESTIMATION_METHOD, "eigsh"),
            model_id=data.get(NK4GPolicyKeys.ASG_MODEL_ID, "asg_v1"),
            topology=data.get(NK4GPolicyKeys.ASG_TOPOLOGY, "1d_ring"),
            alpha_l=data.get(NK4GPolicyKeys.ASG_ALPHA_L, 1.0),
            alpha_g=data.get(NK4GPolicyKeys.ASG_ALPHA_G, 1.0),
            w_theta=data.get(NK4GPolicyKeys.ASG_W_THETA, 1.0),
            state_dim=data.get(NK4GPolicyKeys.ASG_STATE_DIM, 32),
            strict_mode=data.get(NK4GPolicyKeys.NK4G_STRICT_MODE, False),
            verify_prox=data.get(NK4GPolicyKeys.NK4G_VERIFY_PROX, True),
        )
    
    def validate(self) -> List[str]:
        """Validate policy values.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check thresholds
        if self.kappa_min < 0:
            errors.append(f"kappa_min must be non-negative, got {self.kappa_min}")
        
        if self.margin_min < 0:
            errors.append(f"margin_min must be non-negative, got {self.margin_min}")
        
        # Check ASG parameters
        if self.alpha_l < 0:
            errors.append(f"alpha_l must be non-negative, got {self.alpha_l}")
        
        if self.alpha_g < 0:
            errors.append(f"alpha_g must be non-negative, got {self.alpha_g}")
        
        if self.w_theta < 0:
            errors.append(f"w_theta must be non-negative, got {self.w_theta}")
        
        if self.state_dim <= 0:
            errors.append(f"state_dim must be positive, got {self.state_dim}")
        
        # Check topology
        if self.topology not in ["1d_ring", "2d_torus"]:
            errors.append(f"topology must be '1d_ring' or '2d_torus', got {self.topology}")
        
        # Check estimation method
        valid_methods = [e.value for e in EstimationMethod]
        if self.estimation_method not in valid_methods:
            errors.append(f"estimation_method must be one of {valid_methods}")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if policy is valid"""
        return len(self.validate()) == 0
    
    def get_hash(self) -> str:
        """Compute deterministic hash of policy.
        
        Returns:
            SHA-256 hex digest
        """
        import hashlib
        
        # Create deterministic string
        parts = [
            f"kappa_min={self.kappa_min}",
            f"margin_min={self.margin_min}",
            f"projector={self.projector_id}",
            f"method={self.estimation_method}",
            f"model={self.model_id}",
            f"topology={self.topology}",
            f"alpha_l={self.alpha_l}",
            f"alpha_g={self.alpha_g}",
            f"w_theta={self.w_theta}",
            f"dim={self.state_dim}",
        ]
        
        policy_str = "|".join(parts)
        return hashlib.sha256(policy_str.encode()).hexdigest()


def create_default_nk4g_policy() -> NK4GPolicyBundle:
    """Create default NK-4G policy.
    
    Returns:
        Default policy bundle
    """
    return NK4GPolicyBundle()


def create_strict_nk4g_policy() -> NK4GPolicyBundle:
    """Create strict NK-4G policy (warnings = errors).
    
    Returns:
        Strict policy bundle
    """
    return NK4GPolicyBundle(
        kappa_min=1e-4,  # Stricter κ₀ requirement
        margin_min=10.0,  # Stricter margin requirement
        strict_mode=True,
    )


def create_relaxed_nk4g_policy() -> NK4GPolicyBundle:
    """Create relaxed NK-4G policy for testing.
    
    Returns:
        Relaxed policy bundle
    """
    return NK4GPolicyBundle(
        kappa_min=1e-10,  # Very low threshold
        margin_min=0.01,  # Very low margin
        strict_mode=False,
    )


# Default values
DEFAULT_KAPPA_MIN = 1e-6
DEFAULT_MARGIN_MIN = 1.0
DEFAULT_ESTIMATION_METHOD = "eigsh"
DEFAULT_PROJECTOR_ID = "mean_zero_theta_v1"
