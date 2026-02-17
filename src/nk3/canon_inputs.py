# NK-3 Lowering: NSC Canonicalization per docs/nk3/1_canon_inputs.md

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json


class NSCVersion(Enum):
    """NSC version identifiers."""
    V1 = "nsc.v1"


@dataclass
class NSCProgram:
    """
    NSC program per docs/nk3/1_canon_inputs.md.
    
    Canonical NSC.v1 program structure.
    """
    nsc_id: str = "id:nsc.v1"
    canon_profile_id: str = "id:nk1.valuecanon.v1"
    schema_id: str = ""
    kernel_registry_digest: str = ""
    policy_digest: str = ""
    decls: List[Dict[str, Any]] = field(default_factory=list)
    entry: str = ""
    
    def to_canonical_bytes(self) -> bytes:
        """
        Convert to canonical NSC bytes.
        
        Per docs/nk3/1_canon_inputs.md:
        - Decl list sorted by decl_id bytes
        - JSON with deterministic key ordering
        - UTF-8 encoding
        """
        data = self._to_dict()
        
        # Sort decls by decl_id
        data['decls'] = sorted(data['decls'], key=lambda d: d.get('decl_id', '').encode('utf-8'))
        
        # Canonical JSON
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            'nsc_id': self.nsc_id,
            'canon_profile_id': self.canon_profile_id,
            'schema_id': self.schema_id,
            'kernel_registry_digest': self.kernel_registry_digest,
            'policy_digest': self.policy_digest,
            'decls': self.decls,
            'entry': self.entry
        }
    
    def compute_digest(self) -> str:
        """Compute program digest: H_R(P_nsc_bytes)."""
        canonical_bytes = self.to_canonical_bytes()
        return 'h:' + hashlib.sha3_256(canonical_bytes).hexdigest()


@dataclass
class PolicyBundleRef:
    """Reference to PolicyBundle."""
    policy_bundle_id: str
    policy_digest: str


@dataclass
class KernelRegistryRef:
    """Reference to KernelRegistry."""
    kernel_registry_digest: str


@dataclass
class InputBundle:
    """
    InputBundle per docs/nk3/1_canon_inputs.md.
    
    The complete input to NK-3 lowering.
    """
    program_nsc: NSCProgram
    policy_bundle: PolicyBundleRef
    kernel_registry: KernelRegistryRef
    toolchain_ids: List[str] = field(default_factory=list)
    schemas_digest_set: Optional[List[str]] = None
    
    def validate(self) -> bool:
        """Validate input bundle."""
        if not self.program_nsc.entry:
            return False
        if not self.program_nsc.policy_digest:
            return False
        if not self.program_nsc.kernel_registry_digest:
            return False
        return True


def create_example_nsc_program() -> NSCProgram:
    """Create example NSC program."""
    return NSCProgram(
        schema_id="id:schema.example",
        kernel_registry_digest="h:abc123",
        policy_digest="h:def456",
        entry="main",
        decls=[
            {
                'decl_id': 'main',
                'params': [],
                'body': {
                    'type': 'SEQ',
                    'stmts': []
                }
            }
        ]
    )


def parse_nsc_bytes(bytes_data: bytes) -> NSCProgram:
    """
    Parse NSC bytes to NSCProgram.
    
    This is the inverse of to_canonical_bytes.
    """
    data = json.loads(bytes_data.decode('utf-8'))
    return NSCProgram(
        nsc_id=data.get('nsc_id', 'id:nsc.v1'),
        canon_profile_id=data.get('canon_profile_id', 'id:nk1.valuecanon.v1'),
        schema_id=data.get('schema_id', ''),
        kernel_registry_digest=data.get('kernel_registry_digest', ''),
        policy_digest=data.get('policy_digest', ''),
        decls=data.get('decls', []),
        entry=data.get('entry', '')
    )
