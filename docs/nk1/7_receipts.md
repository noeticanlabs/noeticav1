# NK-1 Receipts

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_measured_gate.md`](4_measured_gate.md), [`6_actions.md`](6_actions.md), [`8_verifier.md`](8_verifier.md)

---

## Overview

NK-1 receipts are the **replay fuel** for the verifier. Every gate step produces a receipt that contains all information needed to independently verify the decision. Receipts are hash-chained for continuity verification.

---

## Receipt Schema

### Full Receipt Structure

```python
@dataclass
class Receipt:
    """
    Complete NK-1 receipt for a gate step.
    All fields are canonical and hash-chained.
    """
    
    # === Identity + Chain ===
    prev_receipt_hash: str          # SHA3-256 of previous receipt
    receipt_hash: str              # SHA3-256 of this receipt (computed)
    state_hash_pre: str            # SHA3-256 of state before
    state_hash_post: str           # SHA3-256 of state after
    action_descriptor_hash: str    # SHA3-256 of action descriptor
    
    # === Policy Commitments ===
    contract_set_id: str           # Hash of contract set
    v_policy_id: str = "CK0.v1"   # Violation policy
    service_policy_id: str         # Service policy ID
    service_instance_id: str       # Service instance ID
    disturbance_policy_id: str     # DP0/DP1/DP2/DP3
    matrix_registry_id: str | None = None  # If curvature used
    
    # === Measurements ===
    debt_pre: str                  # DebtUnit canonical string
    debt_post: str                 # DebtUnit canonical string
    delta_v: str                   # DebtUnit canonical string
    budget: str                    # DebtUnit canonical string
    disturbance: str               # DebtUnit canonical string
    service_applied: str | None = None  # Optional: S(D_pre, B)
    
    # === Per-Contract Summaries ===
    contract_results: list[ContractResultReceipt] = field(default_factory=list)
    
    # === Decision + Codes ===
    gate_decision: str             # accept / reject / repair
    failure_code: str | None = None
    invariants_pass: bool
    law_check_pass: bool
    
    # === Metadata ===
    timestamp: str | None = None   # ISO 8601 (optional, for logging)
    step_index: int | None = None # Step number (optional)


@dataclass
class ContractResultReceipt:
    """Per-contract result in receipt."""
    contract_id: str
    active: bool
    r2_k: str                    # DebtUnit canonical string
    r_hash_k: str | None = None  # Optional commitment
```

---

## Canonical JSON Format

```json
{
  "prev_receipt_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "receipt_hash": "abc123...",
  "state_hash_pre": "def456...",
  "state_hash_post": "ghi789...",
  "action_descriptor_hash": "jkl012...",
  
  "contract_set_id": "contract_set_v1_abc123",
  "v_policy_id": "CK0.v1",
  "service_policy_id": "CK0.service.v1",
  "service_instance_id": "linear_capped.mu:1.0",
  "disturbance_policy_id": "DP1",
  "matrix_registry_id": null,
  
  "debt_pre": "q:6:1000000",
  "debt_post": "q:6:800000",
  "delta_v": "q:6:-200000",
  "budget": "q:6:500000",
  "disturbance": "q:6:0",
  "service_applied": "q:6:200000",
  
  "contract_results": [
    {
      "contract_id": "position_limit",
      "active": true,
      "r2_k": "q:6:0",
      "r_hash_k": null
    },
    {
      "contract_id": "velocity_bound",
      "active": true,
      "r2_k": "q:6:100000",
      "r_hash_k": "commitment_hash_abc"
    }
  ],
  
  "gate_decision": "accept",
  "failure_code": null,
  "invariants_pass": true,
  "law_check_pass": true,
  
  "timestamp": "2026-02-16T12:00:00Z",
  "step_index": 0
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

### Hash Computation

```python
def compute_receipt_hash(receipt: Receipt) -> str:
    """Compute SHA3-256 hash of receipt."""
    return hash(receipt.to_canonical_bytes())

def to_canonical_bytes(self) -> bytes:
    """Serialize receipt to canonical bytes for hashing."""
    data = {
        # Chain
        "prev_receipt_hash": self.prev_receipt_hash,
        "state_hash_pre": self.state_hash_pre,
        "state_hash_post": self.state_hash_post,
        "action_descriptor_hash": self.action_descriptor_hash,
        
        # Policy
        "contract_set_id": self.contract_set_id,
        "v_policy_id": self.v_policy_id,
        "service_policy_id": self.service_policy_id,
        "service_instance_id": self.service_instance_id,
        "disturbance_policy_id": self.disturbance_policy_id,
        
        # Measurements
        "debt_pre": self.debt_pre,
        "debt_post": self.debt_post,
        "delta_v": self.delta_v,
        "budget": self.budget,
        "disturbance": self.disturbance,
        
        # Decision
        "gate_decision": self.gate_decision,
        "failure_code": self.failure_code,
        "invariants_pass": self.invariants_pass,
        "law_check_pass": self.law_check_pass,
    }
    
    # Optional fields
    if self.service_applied:
        data["service_applied"] = self.service_applied
    
    if self.contract_results:
        data["contract_results"] = [
            {
                "contract_id": cr.contract_id,
                "active": cr.active,
                "r2_k": cr.r2_k,
            }
            for cr in self.contract_results
        ]
    
    # Lexicographic sort for deterministic serialization
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode("utf-8")
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
        # Set previous hash
        receipt.prev_receipt_hash = self.last_hash if self.last_hash else "0" * 64
        
        # Compute and set receipt hash
        receipt.receipt_hash = compute_receipt_hash(receipt)
        
        # Store
        self.receipts.append(receipt)
        self.last_hash = receipt.receipt_hash
        
        return receipt
    
    def get_receipt_chain(self) -> list[Receipt]:
        """Get full receipt chain."""
        return self.receipts
    
    def verify_chain(self) -> bool:
        """Verify hash chain continuity."""
        for i, receipt in enumerate(self.receipts):
            expected_prev = "0" * 64 if i == 0 else self.receipts[i-1].receipt_hash
            if receipt.prev_receipt_hash != expected_prev:
                return False
        return True
```

---

## Receipt Fields by Category

### Identity + Chain (Required)

| Field | Type | Description |
|-------|------|-------------|
| `prev_receipt_hash` | string | SHA3-256 of previous receipt |
| `receipt_hash` | string | SHA3-256 of this receipt |
| `state_hash_pre` | string | SHA3-256 of pre-state |
| `state_hash_post` | string | SHA3-256 of post-state |
| `action_descriptor_hash` | string | SHA3-256 of action |

### Policy Commitments (Required)

| Field | Type | Description |
|-------|------|-------------|
| `contract_set_id` | string | Hash of contract set |
| `v_policy_id` | string | "CK0.v1" |
| `service_policy_id` | string | Service policy ID |
| `service_instance_id` | string | Service instance ID |
| `disturbance_policy_id` | string | DP0/DP1/DP2/DP3 |
| `matrix_registry_id` | string \| null | Matrix registry ID |

### Measurements (Required)

| Field | Type | Description |
|-------|------|-------------|
| `debt_pre` | string | D_pre as DebtUnit |
| `debt_post` | string | D_post as DebtUnit |
| `delta_v` | string | ΔV as DebtUnit |
| `budget` | string | B_k as DebtUnit |
| `disturbance` | string | E_k as DebtUnit |
| `service_applied` | string \| null | S(D_pre, B_k) |

### Per-Contract Results (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `contract_results` | array | List of ContractResultReceipt |

### Decision (Required)

| Field | Type | Description |
|-------|------|-------------|
| `gate_decision` | string | accept/reject/repair |
| `failure_code` | string \| null | Failure reason |
| `invariants_pass` | boolean | Invariant check result |
| `law_check_pass` | boolean | Law inequality result |

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

---

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
    
    state_hash = hash(state.to_canonical_bytes())
    action_hash = hash(action.to_canonical_bytes())
    
    receipt = Receipt(
        prev_receipt_hash=prev_hash,
        receipt_hash=None,  # Computed after
        state_hash_pre=state_hash,
        state_hash_post=state_hash,  # No change
        action_descriptor_hash=action_hash,
        
        contract_set_id=contract_set.contract_set_id,
        v_policy_id="CK0.v1",
        service_policy_id=action.service_policy_id,
        service_instance_id=action.service_instance_id,
        disturbance_policy_id=action.disturbance_policy_id,
        
        debt_pre=debt_pre.canonical(),
        debt_post=debt_pre.canonical(),  # No change
        delta_v="q:6:0",  # No change
        budget=action.budget,
        disturbance=action.disturbance,
        
        gate_decision="reject",
        failure_code=f"{failure_type}:{failure_detail}" if failure_detail else failure_type,
        invariants_pass=False,
        law_check_pass=False,
    )
    
    receipt.receipt_hash = compute_receipt_hash(receipt)
    return receipt
```

---

## Verification Input

Receipts are designed to be verified independently:

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
└── Matrix invariants
```

---

*See also: [`8_verifier.md`](8_verifier.md), [`../ck0/8_receipts_omega_ledger.md`](../ck0/8_receipts_omega_ledger.md)*
