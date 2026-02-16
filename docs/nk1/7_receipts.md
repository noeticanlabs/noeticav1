# NK-1 Receipts

**Version:** 1.0 (canon_receipt_bytes.v1)  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_measured_gate.md`](4_measured_gate.md), [`6_actions.md`](6_actions.md), [`8_verifier.md`](8_verifier.md)

---

## Overview

NK-1 receipts are the **replay fuel** for the verifier. Every gate step produces a receipt that contains all information needed to independently verify the decision. Receipts are hash-chained for continuity verification.

---

## Receipt Schema

### Tagged Atoms Format (canon_receipt_bytes.v1)

All receipt fields use tagged atom prefixes for type safety and strict parsing:

| Prefix | Type | Description |
|--------|------|-------------|
| `id:` | Identifier | UUIDs, policy IDs, contract IDs |
| `h:` | Hash | 32-byte SHA3-256 hashes (hex-encoded) |
| `q:` | Quantity | Integers, DebtUnit canonical strings |
| `i:` | Index | Step indices, array indices |

### Full Receipt Structure

```python
@dataclass
class Receipt:
    """
    Complete NK-1 receipt for a gate step.
    All fields are canonical and hash-chained.
    Uses canon_receipt_bytes.v1 format with tagged atoms.
    """
    
    # === Identity + Chain (h: prefix for hashes) ===
    h:prev_receipt_hash: str          # SHA3-256 of previous receipt
    h:receipt_hash: str              # SHA3-256 of this receipt (computed)
    h:state_hash_pre: str            # SHA3-256 of state before
    h:state_hash_post: str           # SHA3-256 of state after
    h:action_descriptor_hash: str    # SHA3-256 of action descriptor
    
    # === Policy Commitments (id: prefix for identifiers) ===
    id:contract_set_id: str           # Hash of contract set
    id:v_policy_id: str = "id:CK0.v1"   # Violation policy
    id:service_policy_id: str         # Service policy ID
    id:service_instance_id: str       # Service instance ID
    id:disturbance_policy_id: str     # DP0/DP1/DP2/DP3
    id:matrix_registry_id: str | None = None  # If curvature used
    
    # === Measurements (q: prefix for DebtUnit quantities) ===
    q:debt_pre: str                  # DebtUnit canonical string
    q:debt_post: str                 # DebtUnit canonical string
    q:delta_v: str                   # DebtUnit canonical string
    q:budget: str                    # DebtUnit canonical string
    q:disturbance: str               # DebtUnit canonical string
    q:service_applied: str | None = None  # Optional: S(D_pre, B)
    
    # === Per-Contract Summaries ===
    contract_results: list[ContractResultReceipt] = field(default_factory=list)
    
    # === Decision + Codes ===
    gate_decision: str             # accept / reject / repair
    failure_code: str | None = None
    invariants_pass: bool
    law_check_pass: bool
    
    # === Metadata ===
    timestamp: str | None = None   # ISO 8601 (optional, for logging)
    i:step_index: int | None = None # Step number (optional)


@dataclass
class ContractResultReceipt:
    """Per-contract result in receipt."""
    id:contract_id: str
    active: bool
    q:r2_k: str                    # DebtUnit canonical string
    h:r_hash_k: str | None = None  # Optional commitment hash
```

---

## Canonical JSON Format (canon_receipt_bytes.v1)

All keys must be in **lexicographic order** and use **tagged atom prefixes**:

```json
{
  "h:action_descriptor_hash": "h:jkl012...",
  "contract_results": [
    {
      "active": true,
      "h:r_hash_k": null,
      "id:contract_id": "position_limit",
      "q:r2_k": "q:6:0"
    },
    {
      "active": true,
      "h:r_hash_k": "h:commitment_hash_abc",
      "id:contract_id": "velocity_bound",
      "q:r2_k": "q:6:100000"
    }
  ],
  "gate_decision": "accept",
  "h:prev_receipt_hash": "h:0000000000000000000000000000000000000000000000000000000000000000",
  "h:receipt_hash": "h:abc123...",
  "h:state_hash_post": "h:ghi789...",
  "h:state_hash_pre": "h:def456...",
  "id:contract_set_id": "id:contract_set_v1_abc123",
  "id:disturbance_policy_id": "id:DP1",
  "id:matrix_registry_id": null,
  "id:service_instance_id": "id:linear_capped.mu:1.0",
  "id:service_policy_id": "id:CK0.service.v1",
  "id:v_policy_id": "id:CK0.v1",
  "invariants_pass": true,
  "law_check_pass": true,
  "q:budget": "q:6:500000",
  "q:debt_post": "q:6:800000",
  "q:debt_pre": "q:6:1000000",
  "q:delta_v": "q:6:-200000",
  "q:disturbance": "q:6:0",
  "q:service_applied": "q:6:200000",
  "failure_code": null,
  "timestamp": "2026-02-16T12:00:00Z",
  "i:step_index": 0
}
```

---

## Hash Chain

### Chain Structure

```
receipt[0] → receipt[1] → receipt[2] → ...
     ↑              ↑              ↑
  prev_hash      prev_hash      prev_hash
```

### Hash Computation (canon_receipt_bytes.v1)

```python
def compute_receipt_hash(receipt: Receipt) -> str:
    """Compute SHA3-256 hash of receipt."""
    return hash(receipt.to_canonical_bytes())

def to_canonical_bytes(self) -> bytes:
    """Serialize receipt to canonical bytes for hashing."""
    data = {
        # Chain (h: prefix for hashes - sorted lexicographically)
        "h:action_descriptor_hash": self.h:action_descriptor_hash,
        "h:prev_receipt_hash": self.h:prev_receipt_hash,
        "h:state_hash_post": self.h:state_hash_post,
        "h:state_hash_pre": self.h:state_hash_pre,
        
        # Policy (id: prefix for identifiers - sorted lexicographically)
        "id:contract_set_id": self.id:contract_set_id,
        "id:disturbance_policy_id": self.id:disturbance_policy_id,
        "id:matrix_registry_id": self.id:matrix_registry_id,
        "id:service_instance_id": self.id:service_instance_id,
        "id:service_policy_id": self.id:service_policy_id,
        "id:v_policy_id": self.id:v_policy_id,
        
        # Measurements (q: prefix for quantities - sorted lexicographically)
        "q:budget": self.q:budget,
        "q:debt_post": self.q:debt_post,
        "q:debt_pre": self.q:debt_pre,
        "q:delta_v": self.q:delta_v,
        "q:disturbance": self.q:disturbance,
        
        # Decision
        "gate_decision": self.gate_decision,
        "failure_code": self.failure_code,
        "invariants_pass": self.invariants_pass,
        "law_check_pass": self.law_check_pass,
    }
    
    # Optional fields
    if self.q:service_applied:
        data["q:service_applied"] = self.q:service_applied
    
    if self.contract_results:
        data["contract_results"] = sorted([
            {
                "id:contract_id": cr.id:contract_id,
                "active": cr.active,
                "q:r2_k": cr.q:r2_k,
            }
            for cr in self.contract_results
        ], key=lambda x: x["id:contract_id"])
    
    # Lexicographic sort for deterministic serialization
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode("utf-8")
```

### Merkle Hashing (Raw 32-Byte Hashes)

For merkle node hashing, use **decoded raw 32-byte hashes** (not hex-encoded strings):

```python
def hash_for_merkle(hex_hash: str) -> bytes:
    """Convert hex-encoded hash to raw 32 bytes for merkle operations."""
    # Remove 'h:' prefix if present
    if hex_hash.startswith('h:'):
        hex_hash = hex_hash[2:]
    # Decode from hex to raw 32 bytes
    return bytes.fromhex(hex_hash)

def compute_merkle_root(hashes: list[str]) -> str:
    """Compute merkle root from list of hex hashes."""
    if not hashes:
        return 'h:' + '00' * 32
    
    # Convert to raw bytes
    nodes = [hash_for_merkle(h) for h in hashes]
    
    # Build merkle tree (pairwise hashing)
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])  # Duplicate last node
        nodes = [sha3_256(nodes[i] + nodes[i+1]) for i in range(0, len(nodes), 2)]
    
    # Return as hex with h: prefix
    return 'h:' + nodes[0].hex()
```

---

## Strict Unknown-Field Rejection (canon_receipt_bytes.v1)

**Any receipt with unknown fields must be rejected**, not silently ignored. This ensures cryptographic integrity and prevents version-skew attacks.

### Parser Rules

```python
class ReceiptParser:
    """Strict receipt parser with unknown-field rejection."""
    
    # All known fields in canon_receipt_bytes.v1 format
    KNOWN_FIELDS = frozenset([
        # Chain hashes
        "h:action_descriptor_hash",
        "h:prev_receipt_hash",
        "h:receipt_hash",
        "h:state_hash_post",
        "h:state_hash_pre",
        
        # Policy identifiers
        "id:contract_set_id",
        "id:disturbance_policy_id",
        "id:matrix_registry_id",
        "id:service_instance_id",
        "id:service_policy_id",
        "id:v_policy_id",
        
        # Measurements
        "q:budget",
        "q:debt_post",
        "q:debt_pre",
        "q:delta_v",
        "q:disturbance",
        "q:service_applied",
        
        # Decision
        "contract_results",
        "failure_code",
        "gate_decision",
        "invariants_pass",
        "law_check_pass",
        
        # Metadata
        "timestamp",
        "i:step_index",
    ])
    
    # Contract result fields
    KNOWN_CONTRACT_RESULT_FIELDS = frozenset([
        "active",
        "h:r_hash_k",
        "id:contract_id",
        "q:r2_k",
    ])
    
    def parse(self, json_data: dict) -> Receipt:
        """Parse receipt with strict field validation."""
        
        # Check for unknown top-level fields
        unknown_fields = set(json_data.keys()) - self.KNOWN_FIELDS
        if unknown_fields:
            raise ReceiptParseError(
                f"Unknown receipt fields: {sorted(unknown_fields)}"
            )
        
        # Parse contract results with field validation
        if "contract_results" in json_data:
            for i, cr in enumerate(json_data["contract_results"]):
                unknown_cr_fields = set(cr.keys()) - self.KNOWN_CONTRACT_RESULT_FIELDS
                if unknown_cr_fields:
                    raise ReceiptParseError(
                        f"Unknown contract_result[{i}] fields: {sorted(unknown_cr_fields)}"
                    )
        
        # All fields valid - proceed with parsing
        return self._build_receipt(json_data)
```

### Rejection Behavior

| Scenario | Action |
|----------|--------|
| Unknown top-level field | **REJECT** with `ReceiptParseError` |
| Unknown field in contract_results | **REJECT** with `ReceiptParseError` |
| Missing required field | **REJECT** with `ReceiptParseError` |
| Invalid tag prefix | **REJECT** with `ReceiptParseError` |

### Tag Validation

```python
def validate_tag_prefix(key: str, value: str) -> bool:
    """Validate that value matches the tag prefix of the key."""
    tag_prefix = key.split(':')[0] + ':'
    
    # Fields without prefix (metadata)
    if tag_prefix == ':':
        return True
    
    # Check value has correct prefix
    if not value.startswith(tag_prefix):
        raise ReceiptParseError(
            f"Field '{key}' has prefix '{tag_prefix}' but value starts with '{value[:2]}'"
        )
    return True
```

---

## Receipt Pipeline

### Creation Flow

```
┌─────────────────┐
│   Gate Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Compute V(x)   │  ← Contract measurement
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apply Action   │  ← State transition
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Compute V(x')  │  ← Contract measurement
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gate Decision  │  ← Accept/Reject
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Receipt  │  ← Collect all fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chain Hash     │  ← Link to previous
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Emit Receipt   │  ← Output
└─────────────────┘
```

### Receipt Emitter

```python
class ReceiptEmitter:
    """Emits and stores receipts."""
    
    def __init__(self):
        self.receipts: list[Receipt] = []
        self.last_hash: str | None = None
    
    def emit(self, receipt: Receipt) -> Receipt:
        """Emit a receipt, chaining to previous."""
        # Set previous hash with h: prefix
        receipt.h:prev_receipt_hash = (
            self.last_hash if self.last_hash 
            else "h:" + "00" * 32
        )
        
        # Compute and set receipt hash
        receipt.h:receipt_hash = compute_receipt_hash(receipt)
        
        # Store
        self.receipts.append(receipt)
        self.last_hash = receipt.h:receipt_hash
        
        return receipt
    
    def get_receipt_chain(self) -> list[Receipt]:
        """Get full receipt chain."""
        return self.receipts
    
    def verify_chain(self) -> bool:
        """Verify hash chain continuity."""
        for i, receipt in enumerate(self.receipts):
            expected_prev = (
                "h:" + "00" * 32 if i == 0 
                else self.receipts[i-1].h:receipt_hash
            )
            if receipt.h:prev_receipt_hash != expected_prev:
                return False
        return True
```

---

## Receipt Fields by Category (canon_receipt_bytes.v1)

All fields use tagged atom prefixes. Fields are sorted lexicographically.

### Identity + Chain (Required)

| Field | Type | Description |
|-------|------|-------------|
| `h:action_descriptor_hash` | string | SHA3-256 of action (with `h:` prefix) |
| `h:prev_receipt_hash` | string | SHA3-256 of previous receipt (with `h:` prefix) |
| `h:receipt_hash` | string | SHA3-256 of this receipt (with `h:` prefix) |
| `h:state_hash_post` | string | SHA3-256 of post-state (with `h:` prefix) |
| `h:state_hash_pre` | string | SHA3-256 of pre-state (with `h:` prefix) |

### Policy Commitments (Required)

| Field | Type | Description |
|-------|------|-------------|
| `id:contract_set_id` | string | Hash of contract set (with `id:` prefix) |
| `id:disturbance_policy_id` | string | DP0/DP1/DP2/DP3 (with `id:` prefix) |
| `id:matrix_registry_id` | string \| null | Matrix registry ID (with `id:` prefix) |
| `id:service_instance_id` | string | Service instance ID (with `id:` prefix) |
| `id:service_policy_id` | string | Service policy ID (with `id:` prefix) |
| `id:v_policy_id` | string | "id:CK0.v1" (with `id:` prefix) |

### Measurements (Required)

| Field | Type | Description |
|-------|------|-------------|
| `q:budget` | string | B_k as DebtUnit (with `q:` prefix) |
| `q:debt_post` | string | D_post as DebtUnit (with `q:` prefix) |
| `q:debt_pre` | string | D_pre as DebtUnit (with `q:` prefix) |
| `q:delta_v` | string | ΔV as DebtUnit (with `q:` prefix) |
| `q:disturbance` | string | E_k as DebtUnit (with `q:` prefix) |
| `q:service_applied` | string \| null | S(D_pre, B_k) (with `q:` prefix) |

### Per-Contract Results (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `contract_results` | array | List of ContractResultReceipt (sorted by contract_id) |

### ContractResultReceipt Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Whether contract was active |
| `h:r_hash_k` | string \| null | Commitment hash (with `h:` prefix) |
| `id:contract_id` | string | Contract identifier (with `id:` prefix) |
| `q:r2_k` | string | DebtUnit value (with `q:` prefix) |

### Decision (Required)

| Field | Type | Description |
|-------|------|-------------|
| `failure_code` | string \| null | Failure reason |
| `gate_decision` | string | accept/reject/repair |
| `invariants_pass` | boolean | Invariant check result |
| `law_check_pass` | boolean | Law inequality result |

### Metadata (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `i:step_index` | int \| null | Step number (with `i:` prefix) |
| `timestamp` | string \| null | ISO 8601 timestamp |

---

## Serialization

### To JSON

```python
def to_json(receipt: Receipt) -> str:
    """Serialize receipt to JSON."""
    data = receipt_to_dict(receipt)
    return json.dumps(data, sort_keys=True, indent=2)
```

### From JSON

```python
def from_json(json_str: str) -> Receipt:
    """Parse receipt from JSON."""
    data = json.loads(json_str)
    return dict_to_receipt(data)
```

## Failure Receipts

When gate rejects before transition:

```python
def create_failure_receipt(
    prev_hash: str,
    state: State,
    action: ActionDescriptor,
    contract_set: ContractSet,
    failure_type: str,
    failure_detail: str | None,
    debt_pre: DebtUnit
) -> Receipt:
    """Create receipt for gate failure."""
    
    state_hash = "h:" + hash(state.to_canonical_bytes()).hex()
    action_hash = "h:" + hash(action.to_canonical_bytes()).hex()
    
    receipt = Receipt(
        h:prev_receipt_hash=prev_hash,
        h:receipt_hash=None,  # Computed after
        h:state_hash_pre=state_hash,
        h:state_hash_post=state_hash,  # No change
        h:action_descriptor_hash=action_hash,
        
        id:contract_set_id=contract_set.contract_set_id,
        id:v_policy_id="id:CK0.v1",
        id:service_policy_id=action.service_policy_id,
        id:service_instance_id=action.service_instance_id,
        id:disturbance_policy_id=action.disturbance_policy_id,
        
        q:debt_pre=debt_pre.canonical(),
        q:debt_post=debt_pre.canonical(),  # No change
        q:delta_v="q:6:0",  # No change
        q:budget=action.budget,
        q:disturbance=action.disturbance,
        
        gate_decision="reject",
        failure_code=f"{failure_type}:{failure_detail}" if failure_detail else failure_type,
        invariants_pass=False,
        law_check_pass=False,
    )
    
    receipt.h:receipt_hash = compute_receipt_hash(receipt)
    return receipt
```

---

## Verification Input (canon_receipt_bytes.v1)

Receipts are designed to be verified independently. The verifier **must** reject any receipt with unknown fields per the strict rejection rule.

```
Verifier Input:
├── Policy header (hashed)
├── Contract set definition
├── Matrix registry allowlist
└── Receipt stream

Verifier Checks:
├── Hash chain continuity
├── Action schema validity
├── State hash matches
├── V(x) recomputation
├── Service law computation
├── Disturbance policy check
├── Law inequality check
├── Matrix invariants
└── Unknown field rejection (STRICT)
```

---

*See also: [`8_verifier.md`](8_verifier.md), [`../ck0/8_receipts_omega_ledger.md`](../ck0/8_receipts_omega_ledger.md)*
