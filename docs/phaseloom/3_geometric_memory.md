# PhaseLoom Geometric Memory Fiber

**Canon Doc Spine v1.0.0** — Section 4

---

## 1. Memory Fiber Definition

### 1.1 Mathematical Definition

M := \mathbb R_{\ge 0} \times \mathbb R_{\ge 0} \times \mathbb R_{\ge 0} \times \mathbb R_{\ge 0}

The geometric memory fiber M is a 4-dimensional non-negative real space with coordinates:

| Coordinate | Symbol | Description |
|------------|--------|-------------|
| 1 | (C) | Curvature accumulator |
| 2 | (T) | Tension accumulator |
| 3 | (b) | Remaining budget |
| 4 | (a) | Cumulative authority injected |

### 1.2 Extended State Space

\tilde X = X \times M

For any base state (x \in X), the extended state is:

\tilde x = (x, C, T, b, a) \in \tilde X

---

## 2. Memory Coordinate Semantics

### 2.1 Curvature (C)

- **Purpose:** Track net amplification over dissipation
- **Range:** \mathbb R_{\ge 0}
- **Interpretation:**
  - (C > 0): Net amplification dominating
  - (C = 0): Balanced or no history
- **Update:** C^+ = \rho_C \cdot C + (A - D)

### 2.2 Tension (T)

- **Purpose:** Track cross-thread inconsistency (braid)
- **Range:** \mathbb R_{\ge 0}
- **Interpretation:**
  - (T > 0): Threads are inconsistent
  - (T = 0): All threads aligned
- **Update:** T^+ = \rho_T \cdot T + \Delta T_{inc} - \Delta T_{res}

### 2.3 Budget (b)

- **Purpose:** Governable exploration budget
- **Range:** \mathbb R_{\ge 0}
- **Interpretation:**
  - (b > 0): Budget available
  - (b = 0): Exhausted (triggers interlock)
- **Update:** b^+ = b - \Delta b

### 2.4 Authority (a)

- **Purpose:** Cumulative authorized injection for liveness
- **Range:** \mathbb R_{\ge 0}
- **Interpretation:**
  - (a = 0): No external authority
  - (a > 0): Authority injected via multisig
- **Update:** a^+ = a + \Delta a

---

## 3. Markov Recovery

### 3.1 Problem Statement

The base system (X, V) is not Markov for long-horizon coherence because:
1. Future violation dynamics depend on historical amplification/dissipation
2. Cross-thread consistency affects feasibility
3. Budget exhaustion determines available actions

### 3.2 Solution

By extending to \tilde X = X \times M, the extended system is Markov:

**Theorem (Markov Recovery):**

Given update recurrences for C and T (Sections 5-6), the next memory state depends only on:
- Current extended state: ((x, C, T, b, a))
- Current accepted transition

Therefore the extended system is Markov on \tilde X.

**Status:** [PROVED] - By definition of recurrence.

### 3.3 Formal Proof Sketch

1. **Memory Sufficiency:** The tuple (C, T, b, a) contains all historical information needed to compute future dynamics
2. **Recurrence Closure:** All memory updates are functions of:
   - Current memory values
   - Current step's (A, D, \Delta T_{inc}, \Delta T_{res}, \Delta b, \Delta a)
3. **No Hidden State:** No external variables affect the dynamics

---

## 4. Memory Initialization

### 4.1 Default Initial Memory

For a new PhaseLoom session:

| Coordinate | Initial Value |
|------------|---------------|
| C | 0 |
| T | 0 |
| b | b_{init} (> 0) |
| a | 0 |

### 4.2 Checkpoint Restoration

When restoring from a checkpoint:

```python
def restore_memory(checkpoint_data):
    C = checkpoint_data['C']
    T = checkpoint_data['T']
    b = checkpoint_data['b']
    a = checkpoint_data['a']
    return MemoryState(C, T, b, a)
```

---

## 5. Memory State Operations

### 5.1 State Representation

```python
@dataclass
class MemoryState:
    """Geometric memory fiber state."""
    C: FixedPoint  # Curvature
    T: FixedPoint  # Tension
    b: FixedPoint  # Budget
    a: FixedPoint  # Authority
    
    def to_tuple(self) -> Tuple[FixedPoint, FixedPoint, FixedPoint, FixedPoint]:
        return (self.C, self.T, self.b, self.a)
    
    @classmethod
    def from_tuple(cls, t: Tuple) -> 'MemoryState':
        return cls(C=t[0], T=t[1], b=t[2], a=t[3])
    
    @classmethod
    def zeros(cls) -> 'MemoryState':
        return cls(C=FixedPoint(0), T=FixedPoint(0), 
                   b=FixedPoint(0), a=FixedPoint(0))
```

### 5.2 Update Operations

```python
def update_curvature(C: FixedPoint, A: FixedPoint, D: FixedPoint, 
                     rho_C: FixedPoint) -> FixedPoint:
    """C^+ = rho_C * C + (A - D)"""
    return rho_C * C + (A - D)

def update_tension(T: FixedPoint, delta_T_inc: FixedPoint, 
                    delta_T_res: FixedPoint, rho_T: FixedPoint) -> FixedPoint:
    """T^+ = rho_T * T + delta_T_inc - delta_T_res"""
    return rho_T * T + delta_T_inc - delta_T_res

def update_budget(b: FixedPoint, delta_b: FixedPoint) -> FixedPoint:
    """b^+ = b - delta_b"""
    return b - delta_b

def update_authority(a: FixedPoint, delta_a: FixedPoint) -> FixedPoint:
    """a^+ = a + delta_a"""
    return a + delta_a
```

---

## 6. Serialization

### 6.1 Canonical JSON

Memory states serialize to canonical JSON:

```json
{
  "C": "1000000",
  "T": "0",
  "b": "5000000",
  "a": "0"
}
```

All values are fixed-point integers (scaled by 10^6).

### 6.2 Hash Integration

Memory state contributes to state hash:

```python
def memory_hash(mem: MemoryState) -> str:
    """Compute memory component of state hash."""
    data = json.dumps({
        "C": str(mem.C),
        "T": str(mem.T),
        "b": str(mem.b),
        "a": str(mem.a)
    }, sort_keys=True)
    return 'h:' + sha3_256(data.encode()).hexdigest()
```

---

## 7. Status

- [x] Memory fiber defined as M = R^4_≥0
- [x] Markov recovery theorem stated
- [x] Update operations specified
- [ ] Serialization implementation
- [ ] Checkpoint/restore implementation

---

*The geometric memory fiber M provides the sufficient statistics for Markovian dynamics. All implementations must maintain these four coordinates.*
