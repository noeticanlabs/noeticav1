# NK-3 Hazard and Control Edge Construction v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`5_dag.md`](5_dag.md)

---

## Overview

This document defines how NK-3 constructs hazard edges (WAW, WAR) and control edges from NSC programs. v1.0 has strict rules: no hidden quantifiers, no safety edges, explicit constructs only.

---

## 1. Data Hazards

### 1.1 WAW Hazard (Write-After-Write)

**Definition:** Two operations write to overlapping fields.

**Rule:**
```
if (W_a ∩ W_b ≠ ∅) then add WAW edge
```

**Algorithm:**
```python
def compute_waw_edges(ops: list[OpSpec]) -> list[DAGEdge]:
    """Compute WAW hazard edges."""
    edges = []
    for i, op_a in enumerate(ops):
        for op_b in ops[i+1:]:
            if set(op_a.W) & set(op_b.W):
                edges.append(DAGEdge(
                    src=op_a.op_id,
                    dst=op_b.op_id,
                    kind="hazard.WAW"
                ))
    return edges
```

### 1.2 WAR Hazard (Write-After-Read)

**Definition:** Second operation writes to a field that the first operation reads.

**Rule:**
```
if (W_a ∩ R_b ≠ ∅) then add WAR edge
```

**Algorithm:**
```python
def compute_war_edges(ops: list[OpSpec]) -> list[DAGEdge]:
    """Compute WAR hazard edges."""
    edges = []
    for i, op_a in enumerate(ops):
        for op_b in ops[i+1:]:
            if set(op_a.W) & set(op_b.R):
                edges.append(DAGEdge(
                    src=op_a.op_id,
                    dst=op_b.op_id,
                    kind="hazard.WAR"
                ))
    return edges
```

### 1.3 RAW Hazard (Read-After-Write)

**v1.0 Rule:** RAW edges are **forbidden** in v1.0.

RAW edges are not required for determinism if reads do not constrain order. Adding RAW would complicate the DAG unnecessarily.

---

## 2. Control Dependencies

### 2.1 Explicit Control Constructs

Only these NSC constructs may create control edges:

| Construct | Description | Control Edge |
|-----------|-------------|--------------|
| `SEQ(a, b)` | Sequential | a → b |
| `IF(cond, then, else)` | Conditional | cond → then, cond → else, then → join, else → join |
| `JOIN` | Explicit join | All predecessors → join |

### 2.2 SEQ Construction

```python
def compute_seq_edges(nodes: list[NSCNode]) -> list[DAGEdge]:
    """Compute control edges from SEQ nodes."""
    edges = []
    for node in nodes:
        if isinstance(node, SEQ):
            # a → b for each consecutive pair
            for i in range(len(node.ops) - 1):
                edges.append(DAGEdge(
                    src=node.ops[i].op_id,
                    dst=node.ops[i+1].op_id,
                    kind="control.explicit"
                ))
    return edges
```

### 2.3 IF Construction

```python
def compute_if_edges(node: IfNode) -> list[DAGEdge]:
    """Compute control edges from IF node."""
    edges = []
    
    # Condition must execute before branches
    edges.append(DAGEdge(
        src=node.condition.op_id,
        dst=node.then_branch.op_id,
        kind="control.explicit"
    ))
    edges.append(DAGEdge(
        src=node.condition.op_id,
        dst=node.else_branch.op_id,
        kind="control.explicit"
    ))
    
    # Both branches must complete before join
    edges.append(DAGEdge(
        src=node.then_branch.op_id,
        dst=node.join.op_id,
        kind="control.explicit"
    ))
    edges.append(DAGEdge(
        src=node.else_branch.op_id,
        dst=node.join.op_id,
        kind="control.explicit"
    ))
    
    return edges
```

---

## 3. Join Node Insertion

### 3.1 When to Insert

When NSC contains control-flow joins, NK-3 must insert explicit `op.join.v1` nodes:

| NSC Construct | Join Required |
|---------------|---------------|
| `IF(cond, then, else)` | Yes |
| `SEQ` with branches | Yes |
| Nested conditionals | Yes |

### 3.2 Join Node Properties

```python
@dataclass(frozen=True)
class JoinNode:
    """Explicit join barrier node."""
    
    op_id: str          # "join:" + hash
    R: tuple = ()       # Empty read set
    W: tuple = ()       # Empty write set
    block_index: bool = False
    float_touch: bool = False
    delta_bound: None = None
    requires_modeD: bool = False
```

### 3.3 Join Insertion Algorithm

```python
def insert_join_nodes(dag: DAG, if_nodes: list[IfNode]) -> DAG:
    """Insert explicit join nodes for IF constructs."""
    join_ops = []
    join_edges = []
    
    for if_node in if_nodes:
        # Create join op
        join_op = JoinNode(op_id=f"join:{hash(if_node)}")
        join_ops.append(join_op)
        
        # Add edges to join
        join_edges.append(DAGEdge(
            src=if_node.then_branch.op_id,
            dst=join_op.op_id,
            kind="control.explicit"
        ))
        join_edges.append(DAGEdge(
            src=if_node.else_branch.op_id,
            dst=join_op.op_id,
            kind="control.explicit"
        ))
    
    # Return new DAG with join nodes
    return DAG(
        nodes=dag.nodes + tuple(j.op_id for j in join_ops),
        edges=dag.edges + tuple(join_edges)
    )
```

---

## 4. No Hidden Quantifiers

### 4.1 v1.0 Rule

All edges must be **explicitly constructed** from NSC constructs. No implicit edges from:

- Data flow analysis
- Alias analysis
- "Safety" edges
- Optimizer hints

### 4.2 Edge Kind Restrictions

| Kind | v1.0 Allowed |
|------|--------------|
| `hazard.WAW` | ✅ Yes |
| `hazard.WAR` | ✅ Yes |
| `control.explicit` | ✅ Yes |
| `hazard.RAW` | ❌ No |
| `safety.*` | ❌ No |
| `implicit.*` | ❌ No |

---

## 5. Lex-Toposort Ordering

### 5.1 Node Ordering

Nodes must be sorted in **lex-toposort order**:
1. Topological sort (respect dependencies)
2. Lexicographic tie-break (by op_id bytes)

### 5.2 Algorithm

```python
def lex_toposort(nodes: list[OpID], edges: list[DAGEdge]) -> list[OpID]:
    """Compute lex-toposort order."""
    # Build adjacency and in-degree
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    all_nodes = set(nodes)
    
    for edge in edges:
        adj[edge.src].append(edge.dst)
        in_degree[edge.dst] += 1
    
    # Start with nodes that have no incoming edges
    queue = sorted([n for n in all_nodes if in_degree[n] == 0])
    result = []
    
    while queue:
        # Pop lexicographically smallest
        current = queue.pop(0)
        result.append(current)
        
        # Update neighbors
        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                # Insert in sorted position
                queue.append(neighbor)
                queue.sort()
    
    return result
```

---

## 6. Edge Sorting

### 6.1 Canonical Edge Order

Edges must be sorted by `(src, dst, kind)`:
1. Primary: src (lexicographic)
2. Secondary: dst (lexicographic)
3. Tertiary: kind (lexicographic)

### 6.2 Sorting Algorithm

```python
def canonicalize_edges(edges: list[DAGEdge]) -> tuple[DAGEdge, ...]:
    """Sort edges canonically."""
    return tuple(sorted(edges, key=lambda e: (e.src, e.dst, e.kind)))
```

---

## 7. Validation

### 7.1 Edge Validation

| Check | Description |
|-------|-------------|
| No RAW edges | RAW kind forbidden |
| No safety edges | Safety kinds forbidden |
| No implicit edges | Implicit kinds forbidden |
| Edges sorted | Canonical (src, dst, kind) order |
| Nodes in order | Lex-toposort |

### 7.2 Rejection Criteria

| Reason | Description |
|--------|-------------|
| RAW edge found | RAW kind in edges |
| Safety edge found | Safety kind in edges |
| Implicit edge found | Implicit kind in edges |
| Edge order invalid | Not sorted canonically |
| Node order invalid | Not lex-toposort |
