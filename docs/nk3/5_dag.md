# NK-3 DAG v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`2_canon_outputs.md`](2_canon_outputs.md), [`8_hazard_control.md`](8_hazard_control.md)

---

## Overview

This document defines the DAG v1 artifact. The DAG is a deterministic directed acyclic graph over OpIDs with hazard and control edges.

---

## 1. DAG Schema

### 1.1 Definition

```python
@dataclass(frozen=True)
class DAG:
    """Directed acyclic graph for NK-2."""
    
    nodes: tuple[OpID, ...]    # In canonical lex-toposort order
    edges: tuple[DAGEdge, ...] # Sorted by (src, dst, kind)
    dag_digest: Hash256
    
    @staticmethod
    def from_edges(nodes: list[OpID], edges: list[DAGEdge]) -> DAG:
        """Create DAG from nodes and edges."""
        sorted_nodes = tuple(sorted(nodes))
        sorted_edges = tuple(sorted(edges, key=lambda e: (e.src, e.dst, e.kind)))
        return DAG(
            nodes=sorted_nodes,
            edges=sorted_edges,
            dag_digest=Hash256(sha256(DAG._canonical_bytes(sorted_nodes, sorted_edges)))
        )
    
    @staticmethod
    def _canonical_bytes(nodes: tuple[OpID, ...], edges: tuple[DAGEdge, ...]) -> bytes:
        """Produce canonical byte representation."""
        node_bytes = b''.join(n.encode('utf-8') for n in nodes)
        edge_bytes = b''.join(e.canonical_bytes() for e in edges)
        return node_bytes + edge_bytes
```

### 1.2 Node Ordering

Nodes must be in **canonical lex-toposort order**:
1. Lexicographic sort by op_id
2. Topological sort respecting dependencies
3. Result is deterministic

---

## 2. DAG Edge

### 2.1 Edge Schema

```python
@dataclass(frozen=True)
class DAGEdge:
    """Directed edge in the DAG."""
    
    src: OpID   # Source operation
    dst: OpID   # Destination operation
    kind: EdgeKind  # Edge kind
    
    def canonical_bytes(self) -> bytes:
        """Produce canonical byte representation."""
        return self.src.encode('utf-8') + b':' + self.dst.encode('utf-8') + b':' + self.kind.value.encode('utf-8')
```

### 2.2 Edge Kinds

| Kind | Description | v1.0 Allowed |
|------|-------------|---------------|
| `hazard.WAW` | Write-after-write | ✅ Yes |
| `hazard.WAR` | Write-after-read | ✅ Yes |
| `control.explicit` | Explicit control dependency | ✅ Yes |
| `hazard.RAW` | Read-after-write | ❌ No (forbidden in v1.0) |

---

## 3. Edge Canonicalization

### 3.1 Edge Sorting

Edges must be sorted by `(src, dst, kind)`:
1. Primary: src (lexicographic)
2. Secondary: dst (lexicographic)
3. Tertiary: kind (lexicographic)

### 3.2 Canonical Form

Edge bytes must be:
```
src + ":" + dst + ":" + kind
```

---

## 4. DAG Validation

### 4.1 Static Checks

| Check | Description |
|-------|-------------|
| Acyclic | No cycles in graph |
| Nodes match OpSet | All nodes in OpSet |
| Edges valid | src, dst in nodes |
| Edge kinds | Only WAW, WAR, control.explicit |
| Node order | Lex-toposort order |
| Edge order | Canonical (src, dst, kind) |

### 4.2 Cycle Detection

NK-3 must verify the DAG is acyclic:

```python
def verify_acyclic(dag: DAG) -> bool:
    """Verify DAG has no cycles using DFS."""
    visited = set()
    rec_stack = set()
    
    def dfs(node: OpID) -> bool:
        visited.add(node)
        rec_stack.add(node)
        
        for edge in dag.edges:
            if edge.src == node:
                if edge.dst in rec_stack:
                    return False  # Cycle detected
                if edge.dst not in visited:
                    if not dfs(edge.dst):
                        return False
        
        rec_stack.remove(node)
        return True
    
    return all(dfs(n) for n in dag.nodes)
```

### 4.3 Rejection Criteria

| Reason | Description |
|--------|-------------|
| Cycle detected | DAG contains a cycle |
| Unknown node | src or dst not in OpSet |
| Invalid edge kind | RAW or unknown kind |
| Node order invalid | Not in lex-toposort |
| Edge order invalid | Not canonical |

---

## 5. Graph Properties

### 5.1 Required Properties

| Property | Description |
|----------|-------------|
| Acyclic | No directed cycles |
| Connected to OpSet | All nodes in OpSet |
| Deterministic | Same NSC → same DAG |
| Explicit | Only WAW/WAR/control edges |

### 5.2 Optional Properties

| Property | Description | v1.0 |
|----------|-------------|------|
| Connected | All nodes reachable | ❌ Not required |
| Dense | Many edges | ❌ Not required |

---

## 6. Example DAG

### 6.1 Example NSC Program

```
SEQ(
  a = add(field.x, field.y),
  b = mul(a, field.z)
)
```

### 6.2 Resulting DAG

```json
{
  "nodes": [
    "op:abc123...",
    "op:def456..."
  ],
  "edges": [
    {
      "src": "op:abc123...",
      "dst": "op:def456...",
      "kind": "hazard.WAW"
    },
    {
      "src": "op:abc123...",
      "dst": "op:def456...",
      "kind": "control.explicit"
    }
  ]
}
```

Note: Both WAW (since b writes to output that a also writes to conceptually) and control edge from SEQ.
