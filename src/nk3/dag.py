# NK-3 DAG Construction per docs/nk3/5_dag.md

from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json


class EdgeKind(Enum):
    """DAG edge kinds per docs/nk3/5_dag.md."""
    HAZARD_WAR = "id:hazard.WAR.v1"
    HAZARD_WAW = "id:hazard.WAW.v1"
    CONTROL_EXPLICIT = "id:control.explicit.v1"


@dataclass
class DAGEdge:
    """A directed edge in the DAG."""
    src: str  # Source op_id
    dst: str  # Destination op_id
    kind: EdgeKind


@dataclass
class DAGNode:
    """A node in the DAG (represents an operation)."""
    op_id: str
    is_join: bool = False  # True if this is an op.join.v1 node


@dataclass
class DAG:
    """
    DAG per docs/nk3/5_dag.md.
    
    Contains:
    - Nodes: operations (including op.join.v1)
    - Edges: hazard (WAR, WAW) and explicit control edges
    - Lex-toposort ordering
    """
    nodes: List[DAGNode] = field(default_factory=list)
    edges: List[DAGEdge] = field(default_factory=list)
    version: str = "dag_v1"
    
    def add_node(self, op_id: str, is_join: bool = False) -> None:
        """Add a node."""
        # Check if exists
        for node in self.nodes:
            if node.op_id == op_id:
                return
        self.nodes.append(DAGNode(op_id=op_id, is_join=is_join))
    
    def add_edge(self, src: str, dst: str, kind: EdgeKind) -> None:
        """Add an edge."""
        # Verify nodes exist
        node_ids = {n.op_id for n in self.nodes}
        if src not in node_ids:
            self.add_node(src)
        if dst not in node_ids:
            self.add_node(dst)
        
        self.edges.append(DAGEdge(src=src, dst=dst, kind=kind))
    
    def compute_digest(self) -> str:
        """Compute DAG digest."""
        # Sort nodes by op_id bytes
        node_list = sorted(self.nodes, key=lambda n: n.op_id.encode('utf-8'))
        
        # Sort edges by (src, dst, kind)
        edge_list = sorted(
            self.edges, 
            key=lambda e: (e.src.encode('utf-8'), e.dst.encode('utf-8'), e.kind.value.encode('utf-8'))
        )
        
        data = {
            'nodes': [{'op_id': n.op_id, 'is_join': n.is_join} for n in node_list],
            'edges': [{'src': e.src, 'dst': e.dst, 'kind': e.kind.value} for e in edge_list]
        }
        
        canonical = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
        return 'h:' + hashlib.sha3_256(canonical).hexdigest()
    
    def get_successors(self, op_id: str) -> List[str]:
        """Get all successor op_ids."""
        return [e.dst for e in self.edges if e.src == op_id]
    
    def get_predecessors(self, op_id: str) -> List[str]:
        """Get all predecessor op_ids."""
        return [e.src for e in self.edges if e.dst == op_id]


def insert_join_nodes(ops: List[Any]) -> DAG:
    """
    Insert op.join.v1 nodes for IF merges.
    
    Per docs/nk3/5_dag.md:
    - NK-3 must insert explicit join barrier op.join.v1 after branches
    - Join nodes participate in scheduling DAG
    - Join nodes have no state effect (W=∅)
    """
    dag = DAG()
    
    # Add all operations as nodes
    for op in ops:
        dag.add_node(op.op_id)
    
    # For IF constructs, add join nodes
    # This is a placeholder - actual implementation depends on NSC structure
    
    return dag


def compute_hazard_edges(opset) -> List[DAGEdge]:
    """
    Compute hazard edges (WAR, WAW) from OpSet.
    
    Per docs/nk3/8_hazard_control.md:
    - WAR: Write-After-Read
    - WAW: Write-After-Write
    """
    edges = []
    
    ops = opset.ops
    
    for i, op1 in enumerate(ops):
        for j, op2 in enumerate(ops):
            if i >= j:
                continue
            
            # Check WAR: op1 reads, op2 writes same field
            for field in op1.read_fields:
                if field in op2.write_fields:
                    edges.append(DAGEdge(
                        src=op1.op_id,
                        dst=op2.op_id,
                        kind=EdgeKind.HAZARD_WAR
                    ))
            
            # Check WAW: op1 writes, op2 writes same field
            for field in op1.write_fields:
                if field in op2.write_fields:
                    edges.append(DAGEdge(
                        src=op1.op_id,
                        dst=op2.op_id,
                        kind=EdgeKind.HAZARD_WAW
                    ))
    
    return edges
