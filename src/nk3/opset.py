# NK-3 OpSet Generation per docs/nk3/4_opset.md

from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class OpSpecNK3:
    """
    Operation specification for NK-3 per docs/nk3/4_opset.md.
    
    Defines an operation with:
    - op_id: unique identifier
    - kernel_id: which kernel to call
    - read/write field sets
    - contracts
    """
    op_id: str
    kernel_id: str
    read_fields: Set[str] = field(default_factory=set)
    write_fields: Set[str] = field(default_factory=set)
    contracts: List[str] = field(default_factory=list)
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpSet:
    """
    OpSet per docs/nk3/4_opset.md.
    
    Deterministic list of OpSpecs sorted by op_id.
    """
    ops: List[OpSpecNK3] = field(default_factory=list)
    version: str = "opset_v1"
    
    def __post_init__(self):
        # Sort by op_id bytes for deterministic ordering
        self.ops.sort(key=lambda op: op.op_id.encode('utf-8'))
    
    def get_op(self, op_id: str) -> Optional[OpSpecNK3]:
        """Get operation by ID."""
        for op in self.ops:
            if op.op_id == op_id:
                return op
        return None
    
    def compute_digest(self) -> str:
        """Compute OpSet digest."""
        data = []
        for op in self.ops:
            data.append({
                'op_id': op.op_id,
                'kernel_id': op.kernel_id,
                'read_fields': sorted(op.read_fields),
                'write_fields': sorted(op.write_fields),
                'contracts': op.contracts,
                'args': op.args
            })
        
        canonical = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        return 'h:' + hashlib.sha3_256(canonical).hexdigest()


def lower_nsc_to_opset(nsc_program) -> OpSet:
    """
    Lower NSC program to OpSet.
    
    Per docs/nk3/4_opset.md:
    - Extract operations from NSC declarations
    - Generate OpSpecs with kernel_id, read/write sets
    - Sort by op_id for deterministic ordering
    """
    opset = OpSet()
    
    # This is a placeholder - actual lowering depends on NSC structure
    # In a real implementation, this would parse NSC and generate ops
    
    return opset
