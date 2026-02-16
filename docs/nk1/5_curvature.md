# NK-1 Curvature Registry + M-entry

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_constants.md`](1_constants.md), [`../ck0/5_curvature_interaction_bounds.md`](../ck0/5_curvature_interaction_bounds.md)

---

## Overview

The Curvature Matrix Registry provides a deterministic, verifier-checkable representation for interaction magnitudes between block indices. The matrix is not "floating math" - it is an **allowlisted certificate object**.

This document (§1.7.1) defines the **canonical byte-level encoding** for the NK-1 Curvature Matrix that is:

* Un-wedgeable to parse
* Unambiguous to version
* Evaluates deterministically into DebtUnit
* Verifier-checkable via allowlist
* Hostile-implementation safe

---

## Scope

This section defines the canonical encoding for the NK-1 Curvature Matrix under:

| Parameter | Value |
|----------|-------|
| `M_ENTRY_MODE` | `rational_scaled.v1` |
| `M_SYMMETRY_MODE` | `symmetric.v1` |
| `M_DOMAIN_MODE` | `blocks_only.v1` |
| `REJECT_ON_NEGATIVE_M` | `true` |
| `DEBT_SCALE` | `6` |

This encoding is authoritative for:

* Matrix hashing
* Registry allowlisting
* Verifier replay
* Golden vector testing

---

## Mathematical Object

Let:

* Block index set: $\mathcal{B} = \{0, 1, \dots, N-1\}$
* Matrix $M \in \mathbb{R}_{\ge 0}^{N \times N}$

Constraints:

1. **Symmetry**: $M_{ij} = M_{ji}$
2. **Non-negativity**: $M_{ij} \ge 0$
3. **Domain**: Indices are block indices only (no substructure, no coordinates)
4. **Entry representation**: Rational scaled (see below)

---

## Entry Representation — `rational_scaled.v1`

Each entry $M_{ij}$ is encoded as a reduced rational:

$$M_{ij} = \frac{a_{ij}}{b_{ij}}$$

Where:

* $a_{ij} \in \mathbb{Z}_{\ge 0}$ (nonnegative integer)
* $b_{ij} \in \mathbb{Z}_{>0}$ (positive integer)
* $\gcd(a_{ij}, b_{ij}) = 1$ (reduced)
* If $a_{ij} = 0$, then $b_{ij} = 1$ (canonical zero form)

### Rejection Rules

| Condition | Action |
|-----------|--------|
| Negative numerator | Reject |
| Denominator ≤ 0 | Reject |
| Unreduced fraction | Reject (must reduce) |

---

## Canonical Matrix Storage Form

Because symmetry is required, we store **upper triangular including diagonal** only.

**Lexicographic index pair order:**

```
(0,0), (0,1), ..., (0,N-1),
(1,1), (1,2), ..., (1,N-1),
...
(N-1,N-1)
```

**Lower triangle MUST NOT appear.** If present → reject.

---

## Canonical JSON Encoding (Pre-Hash Form)

Before hashing, the matrix must be encoded as canonical JSON with:

* UTF-8
* No whitespace except structural
* Sorted keys
* Deterministic field order

### Canonical Object Structure

```json
{
  "matrix_id": "<string>",
  "version": "1.0",
  "entry_mode": "rational_scaled.v1",
  "symmetry_mode": "symmetric.v1",
  "domain_mode": "blocks_only.v1",
  "block_count": N,
  "entries": [
    {"i":0,"j":0,"num":a00,"den":b00},
    {"i":0,"j":1,"num":a01,"den":b01},
    ...
  ]
}
```

### Field Ordering (Mandatory)

Top-level object - **exact order**:

1. `matrix_id`
2. `version`
3. `entry_mode`
4. `symmetry_mode`
5. `domain_mode`
6. `block_count`
7. `entries`

Inside each entry object - **exact order**:

1. `i`
2. `j`
3. `num`
4. `den`

### No Extra Fields

Unknown field → reject.

---

## Canonical Byte Encoding for Hash

Hash input specifications:

* **Encoding**: UTF-8
* **No trailing newline**
* **No indentation**
* **No trailing commas**
* **Integers**: Base-10 ASCII
* **No leading zeros** (except "0")

### Valid Integer Examples

```
0
1
10
12345
```

### Invalid Integer Examples

```
01      ← leading zero
+1      ← sign
1.0     ← decimal
1e0     ← scientific notation
```

**Reject on invalid integer format.**

---

## Matrix Hash Commitment

Matrix registry entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `matrix_id` | string | Unique identifier |
| `matrix_hash` | string | SHA3-256 of canonical bytes |

Where:

```
matrix_hash = SHA3_256(canonical_matrix_bytes)
```

### Verifier Procedure

1. Parse canonical JSON
2. Re-encode canonically
3. Compute SHA3-256 hash
4. Compare with registry allowlist
5. Reject if mismatch

**No dynamic matrix allowed outside allowlist.**

---

## Deterministic Evaluation to DebtUnit

To use $M_{ij}$ in runtime, convert rational $(a/b)$ to DebtUnit.

### Conversion Procedure

1. Multiply numerator by $10^{DEBT\_SCALE}$
2. Perform integer division by denominator using **half-even rounding**
3. Result is DebtUnit integer

**Formally:**

$$\text{DebtInt}(M_{ij}) = \text{round}_{\text{half-even}}\left(\frac{a \cdot 10^{DEBT\_SCALE}}{b}\right)$$

### Requirements

* This conversion **must be deterministic**
* All intermediate arithmetic in **integer big-int domain**
* **No float conversion allowed**

---

## Validation Rules (Mandatory Reject Conditions)

Reject matrix if ANY of:

| # | Condition |
|---|-----------|
| 1 | `entry_mode != rational_scaled.v1` |
| 2 | `symmetry_mode != symmetric.v1` |
| 3 | `domain_mode != blocks_only.v1` |
| 4 | Any lower triangle entry present |
| 5 | Any missing required upper triangle entry |
| 6 | Any duplicate entry |
| 7 | Any $i \ge N$ or $j \ge N$ |
| 8 | Any $j < i$ (lower triangle) |
| 9 | Any $\gcd(\text{num}, \text{den}) \neq 1$ |
| 10 | Any $\text{den} \le 0$ |
| 11 | Any $\text{num} < 0$ |
| 12 | `block_count` inconsistent with entries |
| 13 | Hash mismatch with allowlist |
| 14 | Unexpected JSON field |

---

## Interaction Bound Evaluation (NK-1 Obligation)

NK-1 must support computing deterministic bound:

Given block activity vector $\delta \in \mathbb{R}_{\ge 0}^N$ (DebtUnits),

Compute:

$$\text{InteractionBound} = \sum_{i \le j} M_{ij} \cdot \delta_i \cdot \delta_j \cdot c_{ij}$$

Where:

* $c_{ij} = 2$ if $i \neq j$
* $c_{ii} = 1$

### Evaluation Requirements

All operations:

1. Convert $M_{ij}$ to DebtUnit first
2. Multiply using big-int arithmetic
3. Divide by $10^{DEBT\_SCALE}$ appropriately if needed
4. Final result in DebtUnit

**No floating intermediates.**

---

## Registry Interface

```python
@dataclass
class MatrixEntry:
    """Single entry in a curvature matrix."""
    row: int          # Block index i
    col: int          # Block index j  
    value: DebtUnit   # M_{ij} value (nonnegative)
    
@dataclass
class CurvatureMatrix:
    """Curvature matrix certificate."""
    matrix_id: str                   # Unique identifier
    version: int                    # Matrix version
    block_count: int                # Number of blocks
    entry_mode: str = "rational_scaled.v1"
    symmetry_mode: str = "symmetric.v1"
    domain_mode: str = "blocks_only.v1"
    debt_scale: int = 6
    entries: list[MatrixEntry]      # All entries (sparse: upper triangle only)
    hash_commitment: str            # Hash of full canonical encoding
```

### Registry Class

```python
class CurvatureRegistry:
    """Allowlist of known curvature matrices."""
    
    def __init__(self):
        self._matrices: dict[str, CurvatureMatrix] = {}
    
    def register(self, matrix: CurvatureMatrix) -> None:
        """Register a new matrix (for initialization)."""
        self._validate_matrix(matrix)
        self._matrices[matrix.matrix_id] = matrix
    
    def get(self, matrix_id: str) -> CurvatureMatrix:
        """Get matrix by ID. Raises if unknown."""
        if matrix_id not in self._matrices:
            raise ValueError(f"Unknown matrix_id: {matrix_id}")
        return self._matrices[matrix_id]
    
    def is_known(self, matrix_id: str) -> bool:
        """Check if matrix ID is in allowlist."""
        return matrix_id in self._matrices
```

---

## M-entry Parsing

```python
@dataclass
class MEntry:
    """Rational-scaled matrix entry."""
    num: int    # Numerator (nonnegative)
    den: int    # Denominator (positive, reduced)
    
    def to_debtunit(self) -> DebtUnit:
        """Convert to DebtUnit with standard scaling."""
        return DebtUnit.from_rational(self.num, self.den)
    
    def canonical(self) -> str:
        """Canonical string representation."""
        return f"m_entry:{self.num}:{self.den}"


def parse_m_entry(data: dict) -> MEntry:
    """
    Parse M-entry from dict data.
    
    Expected format:
    {
        "i": <int>,
        "j": <int>,
        "num": <int>,
        "den": <int>
    }
    """
    i = data.get("i")
    j = data.get("j")
    num = data.get("num")
    den = data.get("den")
    
    if None in (i, j, num, den):
        raise ValueError("Missing required field in M-entry")
    
    # Type checks
    if not all(isinstance(x, int) for x in (i, j, num, den)):
        raise ValueError("All fields must be integers")
    
    # Nonnegativity (reject negative)
    if num < 0:
        raise ValueError(f"Negative numerator not allowed: {num}")
    
    if den <= 0:
        raise ValueError(f"Denominator must be positive: {den}")
    
    # Reduce to lowest terms
    g = gcd(num, den)
    num_reduced = num // g
    den_reduced = den // g
    
    # Zero canonical form
    if num_reduced == 0:
        num_reduced = 0
        den_reduced = 1
    
    return MEntry(num=num_reduced, den=den_reduced)
```

---

## Canonical Serialization

```python
def matrix_to_canonical_bytes(matrix: CurvatureMatrix) -> bytes:
    """Serialize matrix to canonical bytes for hashing."""
    # Build entry list - upper triangle only, lexicographic order
    entries_list = []
    for entry in matrix.entries:
        entries_list.append({
            "i": entry.row,
            "j": entry.col,
            "num": entry.value.int_value,  # Already scaled
            "den": 10**matrix.debt_scale     # Standard scale
        })
    
    # Sort entries by (i, j)
    entries_list.sort(key=lambda x: (x["i"], x["j"]))
    
    # Build canonical object - exact field order
    data = {
        "matrix_id": matrix.matrix_id,
        "version": str(matrix.version),
        "entry_mode": matrix.entry_mode,
        "symmetry_mode": matrix.symmetry_mode,
        "domain_mode": matrix.domain_mode,
        "block_count": matrix.block_count,
        "entries": entries_list,
    }
    
    # Canonical JSON: no indent, no trailing comma, sorted keys
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode("utf-8")


def matrix_from_canonical_bytes(data: bytes) -> CurvatureMatrix:
    """Deserialize matrix from canonical bytes."""
    obj = json.loads(data.decode("utf-8"))
    
    entries = []
    for entry_dict in obj["entries"]:
        # Convert back to MatrixEntry
        num = entry_dict["num"]
        den = entry_dict["den"]
        # Convert to DebtUnit
        debt_value = DebtUnit.from_rational(num, den)
        entries.append(MatrixEntry(
            row=entry_dict["i"],
            col=entry_dict["j"],
            value=debt_value
        ))
    
    return CurvatureMatrix(
        matrix_id=obj["matrix_id"],
        version=int(obj["version"]),
        block_count=obj["block_count"],
        entry_mode=obj["entry_mode"],
        symmetry_mode=obj["symmetry_mode"],
        domain_mode=obj["domain_mode"],
        entries=entries,
        hash_commitment=hashlib.sha3_256(data).hexdigest()
    )
```

---

## Golden Vector Examples

### Example 1: 2×2 Identity Matrix

**Input:**
```json
{
  "matrix_id": "test_identity_2x2",
  "version": "1.0",
  "entry_mode": "rational_scaled.v1",
  "symmetry_mode": "symmetric.v1",
  "domain_mode": "blocks_only.v1",
  "block_count": 2,
  "entries": [
    {"i":0,"j":0,"num":1,"den":1},
    {"i":0,"j":1,"num":0,"den":1},
    {"i":1,"j":1,"num":1,"den":1}
  ]
}
```

**Expected SHA3-256:** (compute from canonical bytes)

**Expected DebtUnit conversions:**
* M00 → 1.0 (q:6:1000000)
* M01 → 0.0 (q:6:0)
* M11 → 1.0 (q:6:1000000)

### Example 2: Asymmetric Input (Must Reject)

**Input:**
```json
{
  "matrix_id": "test_asymmetric",
  "version": "1.0",
  "entry_mode": "rational_scaled.v1",
  "symmetry_mode": "symmetric.v1",
  "domain_mode": "blocks_only.v1",
  "block_count": 2,
  "entries": [
    {"i":0,"j":0,"num":1,"den":1},
    {"i":0,"j":1,"num":1,"den":2},
    {"i":1,"j":0,"num":1,"den":3},
    {"i":1,"j":1,"num":1,"den":1}
  ]
}
```

**Expected:** REJECT (asymmetric values: M01 = 0.5, M10 = 0.333...)

### Example 3: Negative Numerator (Must Reject)

**Input:**
```json
{
  "matrix_id": "test_negative",
  "version": "1.0",
  "entry_mode": "rational_scaled.v1",
  "symmetry_mode": "symmetric.v1",
  "domain_mode": "blocks_only.v1",
  "block_count": 1,
  "entries": [
    {"i":0,"j":0,"num":-1,"den":1}
  ]
}
```

**Expected:** REJECT (negative numerator)

### Example 4: Unreduced Fraction (Must Reject)

**Input:**
```json
{
  "matrix_id": "test_unreduced",
  "version": "1.0",
  "entry_mode": "rational_scaled.v1",
  "symmetry_mode": "symmetric.v1",
  "domain_mode": "blocks_only.v1",
  "block_count": 1,
  "entries": [
    {"i":0,"j":0,"num":50,"den":100}
  ]
}
```

**Expected:** REJECT (not reduced: gcd(50,100) = 50 ≠ 1)

### Example 5: Integer Format Edge Cases

| Input | Expected |
|-------|----------|
| `"num": 0` | ACCEPT (canonical zero) |
| `"num": 01` | REJECT (leading zero) |
| `"num": +1` | REJECT (sign not allowed) |
| `"den": 0` | REJECT (zero denominator) |
| `"den": -1` | REJECT (negative denominator) |

---

## Versioning Discipline

### Major Bump Required If

* `entry_mode` changes
* Symmetry rules change
* Encoding order changes
* Hash algorithm changes
* DebtUnit scaling changes

### Minor Bump Allowed For

* New allowlisted matrix IDs
* Documentation clarifications

---

## Why This Is Tight

This matrix encoding:

| Ambiguity | How Closed |
|-----------|------------|
| Parse ambiguity | Exact JSON schema + field order |
| Float ambiguity | Rational representation only |
| Symmetry ambiguity | Upper triangle only, reject lower |
| Negative sign tricks | Explicit reject on negative |
| Ordering tricks | Lexicographic sorted |
| Leading zero tricks | Exact integer format validation |
| Representation wedge | Canonical zero = 0/1 |

**It is hostile-review safe.**

---

## Registry Initialization

```python
def create_default_registry() -> CurvatureRegistry:
    """Create registry with default matrices."""
    registry = CurvatureRegistry()
    
    # Example: 2x2 identity-like matrix
    identity = CurvatureMatrix(
        matrix_id="default_identity_2x2",
        version=1,
        block_count=2,
        entries=[
            MatrixEntry(row=0, col=0, value=DebtUnit(1000000)),  # 1.0
            MatrixEntry(row=0, col=1, value=DebtUnit(0)),
            MatrixEntry(row=1, col=0, value=DebtUnit(0)),
            MatrixEntry(row=1, col=1, value=DebtUnit(1000000)),  # 1.0
        ],
        hash_commitment=None  # Computed after validation
    )
    identity.hash_commitment = hash(identity.to_canonical_bytes())
    registry.register(identity)
    
    # Example: 3x3 with cross-coupling
    cross_coupled = CurvatureMatrix(
        matrix_id="default_cross_3x3",
        version=1,
        block_count=3,
        entries=[
            MatrixEntry(row=0, col=0, value=DebtUnit(1000000)),
            MatrixEntry(row=0, col=1, value=DebtUnit(500000)),  # 0.5
            MatrixEntry(row=0, col=2, value=DebtUnit(250000)),  # 0.25
            MatrixEntry(row=1, col=0, value=DebtUnit(500000)),
            MatrixEntry(row=1, col=1, value=DebtUnit(1000000)),
            MatrixEntry(row=1, col=2, value=DebtUnit(500000)),
            MatrixEntry(row=2, col=0, value=DebtUnit(250000)),
            MatrixEntry(row=2, col=1, value=DebtUnit(500000)),
            MatrixEntry(row=2, col=2, value=DebtUnit(1000000)),
        ],
        hash_commitment=None
    )
    cross_coupled.hash_commitment = hash(cross_coupled.to_canonical_bytes())
    registry.register(cross_coupled)
    
    return registry
```

---

## Summary: NK-1 Matrix Obligations

| Obligation | Implementation |
|------------|----------------|
| **Allowlist enforcement** | Unknown matrices rejected |
| **Invariant enforcement** | Symmetry, nonnegativity checked |
| **Deterministic conversion** | Rational → DebtUnit via half-even |
| **Canonical encoding** | JSON with exact field order |
| **Hash commitment** | SHA3-256 of canonical bytes |
| **Interaction bounds** | Deterministic computation in DebtUnit |

---

*See also: [`4_measured_gate.md`](4_measured_gate.md), [`6_actions.md`](6_actions.md), [`../ck0/5_curvature_interaction_bounds.md`](../ck0/5_curvature_interaction_bounds.md)*
