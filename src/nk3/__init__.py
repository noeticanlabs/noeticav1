# NK-3: Lowering Core
#
# This module implements the NK-3 lowering layer.
#
# Core Components:
# - canon_inputs.py: NSC canonicalization
# - opset.py: OpSet generation
# - dag.py: DAG construction with hazard edges and join nodes

from .canon_inputs import NSCProgram, InputBundle, NSCVersion, create_example_nsc_program, parse_nsc_bytes
from .opset import OpSet, OpSpecNK3
from .dag import DAG, DAGEdge, EdgeKind, insert_join_nodes, compute_hazard_edges

__version__ = "1.0.0"

__all__ = [
    # Canon Inputs
    'NSCProgram',
    'InputBundle',
    'NSCVersion',
    'create_example_nsc_program',
    'parse_nsc_bytes',
    
    # OpSet
    'OpSet',
    'OpSpecNK3',
    
    # DAG
    'DAG',
    'DAGEdge',
    'EdgeKind',
    'insert_join_nodes',
    'compute_hazard_edges',
]
