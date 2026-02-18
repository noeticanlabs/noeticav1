# ASG Operator Digest - Deterministic Hash Computation

import hashlib
import json
from typing import List, Dict, Any, Optional


def compute_operator_digest(
    topology: str,
    N: int,
    operator_type_ids: List[str],
    weights: List[float],
    projector_id: str,
    alpha_l: Optional[float] = None,
    alpha_g: Optional[float] = None,
    w_theta: Optional[float] = None
) -> str:
    """Compute canonical digest over ASG configuration.
    
    This digest is deterministic and auditable, allowing verification
    that the same ASG configuration was used across runs/machines.
    
    Args:
        topology: Grid topology - "1d_ring" or "2d_torus"
        N: System size (number of nodes, or M*N for torus)
        operator_type_ids: List of operator type identifiers
            e.g., ["gradient.forward_diff.v1", "laplacian.central_diff.v1"]
        weights: Node weights/couplings (length N)
        projector_id: Projector identifier
            e.g., "asg.projector.theta_mean_zero.v1"
        alpha_l: Linguistic coupling strength (optional)
        alpha_g: Gradient coupling strength (optional)
        w_theta: Theta penalty weight (optional)
        
    Returns:
        16-character hex digest string
        
    Example:
        >>> digest = compute_operator_digest(
        ...     topology="1d_ring",
        ...     N=32,
        ...     operator_type_ids=["gradient.forward_diff.v1"],
        ...     weights=[1.0] * 32,
        ...     projector_id="asg.projector.theta_mean_zero.v1"
        ... )
        >>> len(digest)
        16
    """
    # Build canonical dictionary with sorted keys for determinism
    canonical: Dict[str, Any] = {
        "topology": topology,
        "N": N,
        "operator_type_ids": sorted(operator_type_ids),
        "weights": weights,
        "projector_id": projector_id,
    }
    
    # Add optional parameters if provided
    if alpha_l is not None:
        canonical["alpha_l"] = alpha_l
    if alpha_g is not None:
        canonical["alpha_g"] = alpha_g
    if w_theta is not None:
        canonical["w_theta"] = w_theta
    
    # Stable JSON serialization with sorted keys
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    
    # SHA-256 hash, truncated to 16 characters for readability
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


def compute_topology_digest(topology: str, dimensions: List[int]) -> str:
    """Compute digest for topology configuration.
    
    Args:
        topology: "1d_ring" or "2d_torus"
        dimensions: [N] for ring, [M, N] for torus
        
    Returns:
        16-character hex digest
    """
    canonical = {
        "topology": topology,
        "dimensions": dimensions
    }
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()[:16]


def verify_digest_match(digest1: str, digest2: str) -> bool:
    """Verify two digests match.
    
    Args:
        digest1: First digest
        digest2: Second digest
        
    Returns:
        True if digests match
    """
    return digest1 == digest2


# Known operator type IDs
OPERATOR_IDS = {
    "gradient": [
        "gradient.forward_diff.v1",
        "gradient.central_diff.v1",
    ],
    "laplacian": [
        "laplacian.central_diff.v1",
        "laplacian.standard.v1",
    ],
    "projector": [
        "asg.projector.theta_mean_zero.v1",
        "asg.projector.full_mean_zero.v1",
    ]
}


# Version constants
ASG_MODEL_ID = "asg.zeta-theta-rho-G.v1"
DIGEST_VERSION = "v1.0"


def get_asg_model_info() -> Dict[str, str]:
    """Get ASG model identification information.
    
    Returns:
        Dictionary with model_id, digest_version, etc.
    """
    return {
        "model_id": ASG_MODEL_ID,
        "digest_version": DIGEST_VERSION,
        "description": "ASG with ζ-θ-ρ-G state blocks"
    }
