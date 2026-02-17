# NK-1 PolicyBundle: PolicyBundle canonicalization + digest per docs/nk1/1_constants.md

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json


class PolicyID(Enum):
    """Policy identifiers."""
    GLB_MODE = "id:nk1.glb_mode.v1"
    DEBT_UNIT = "id:nk1.debtunit.v1"
    FLOAT_POLICY = "id:nk1.float_policy.v1"
    HASH_MODE = "id:nk1.hash_mode.v1"
    STATE_EQ_MODE = "id:nk1.state_eq_mode.v1"


class GLBMode(Enum):
    """Global Ledger Behavior modes."""
    STATIC = "static"
    STATIC_PLUS_TRAP = "static_plus_trap"
    DYNAMIC = "dynamic"


class FloatPolicy(Enum):
    """Float handling policy."""
    REJECT = "reject"
    ROUND = "round"
    SATURATE = "saturate"


class HashMode(Enum):
    """Hash algorithm mode."""
    SHA3_256 = "sha3_256"
    BLAKE2B = "blake2b"


class StateEqMode(Enum):
    """State equality mode."""
    HASH_CANON_V1 = "hash_canon.v1"
    BYTES_EQUAL = "bytes_equal"


@dataclass
class PolicyBundle:
    """
    PolicyBundle per docs/nk1/1_constants.md.
    
    Contains all policy settings that must be constant across the chain.
    Policy digest is bound to receipts for chain-wide locking.
    """
    # Core policies
    glb_mode: GLBMode = GLBMode.STATIC_PLUS_TRAP
    float_policy: FloatPolicy = FloatPolicy.REJECT
    hash_mode: HashMode = HashMode.SHA3_256
    state_eq_mode: StateEqMode = StateEqMode.HASH_CANON_V1
    
    # DebtUnit configuration
    debt_scale: int = 1000  # DEBT_SCALE from PolicyBundle
    
    # Additional policies
    extra: Dict[str, Any] = field(default_factory=dict)
    
    # Computed
    _digest: Optional[str] = field(default=None, repr=False)
    
    def compute_digest(self) -> str:
        """
        Compute policy digest for chain-wide locking.
        
        Per docs/ck0/E_capability_ban.md:
        policy_digest must be constant across entire chain.
        """
        if self._digest is not None:
            return self._digest
        
        # Canonical serialization
        data = self._to_canonical_dict()
        canonical = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        
        self._digest = 'h:' + hashlib.sha3_256(canonical).hexdigest()
        return self._digest
    
    def _to_canonical_dict(self) -> Dict[str, Any]:
        """Convert to canonical dict for hashing."""
        return {
            'glb_mode': self.glb_mode.value,
            'float_policy': self.float_policy.value,
            'hash_mode': self.hash_mode.value,
            'state_eq_mode': self.state_eq_mode.value,
            'debt_scale': self.debt_scale,
            'extra': self.extra
        }
    
    def bind_to_receipt(self) -> Dict[str, str]:
        """Get policy binding for receipts."""
        return {
            'policy_digest': self.compute_digest(),
            'glb_mode_id': self.glb_mode.value,
            'float_policy_id': self.float_policy.value,
            'hash_mode_id': self.hash_mode.value,
            'state_eq_mode_id': self.state_eq_mode.value,
            'debt_scale': str(self.debt_scale)
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PolicyBundle':
        """Create from dictionary."""
        return PolicyBundle(
            glb_mode=GLBMode(data.get('glb_mode', 'static_plus_trap')),
            float_policy=FloatPolicy(data.get('float_policy', 'reject')),
            hash_mode=HashMode(data.get('hash_mode', 'sha3_256')),
            state_eq_mode=StateEqMode(data.get('state_eq_mode', 'hash_canon.v1')),
            debt_scale=data.get('debt_scale', 1000),
            extra=data.get('extra', {})
        )
    
    def validate(self) -> bool:
        """Validate policy bundle."""
        # Check required fields
        if self.debt_scale <= 0:
            return False
        return True


# Default policy bundle
DEFAULT_POLICY = PolicyBundle()


def policy_digest_constant_check(
    prev_digest: str,
    current_digest: str
) -> bool:
    """
    Verify policy digest is constant across chain.
    
    Per docs/nk1/1_constants.md:
    policy_digest must be constant across chain.
    """
    return prev_digest == current_digest


def validate_policy_chain(policy_bundles: List[PolicyBundle]) -> bool:
    """
    Validate all policy bundles in chain have same digest.
    """
    if not policy_bundles:
        return True
    
    digests = [pb.compute_digest() for pb in policy_bundles]
    return len(set(digests)) == 1
