# NK-1 Action Parsing + Canonicalization

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_measured_gate.md`](4_measured_gate.md), [`7_receipts.md`](7_receipts.md)

---

## Overview

NK-1 defines a strict action schema and canonicalization rules that make actions **un-wedgeable by construction**. The parser rejects any ambiguous, floating-point, or non-deterministic representations.

---

## Action Schema

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "NK-1 Action Descriptor",
  "required": ["action_type", "target_blocks", "payload", "budget", "policy_header_hash"],
  "properties": {
    "action_type": {
      "type": "string",
      "enum": ["state_update", "contract_activate", "contract_deactivate", "parameter_update", "boundary_enforce"]
    },
    "target_blocks": {
      "type": "array",
      "items": {"type": "integer"},
      "uniqueItems": true,
      "minItems": 1
    },
    "payload": {
      "type": "object"
    },
    "budget": {
      "type": "string",
      "pattern": "^q:6:-?[0-9]+$"
    },
    "disturbance_event": {
      "type": "string",
      "nullable": true
    },
    "policy_header_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    }
  },
  "additionalProperties": false
}
```

---

## Action Descriptor Class

```python
@dataclass
class ActionDescriptor:
    """Canonical action descriptor."""
    
    action_type: str                    # Enum: state_update, etc.
    target_blocks: list[int]           # Sorted unique block indices
    payload: dict                      # Type-specific payload
    budget: str                        # DebtUnit as canonical string
    disturbance_event: str | None      # Optional: DP2 event type
    policy_header_hash: str            # SHA3-256 hash (64 hex chars)
    
    # Computed
    action_descriptor_hash: str | None = None
    
    def canonicalize(self) -> 'ActionDescriptor':
        """Return canonically ordered version of self."""
        # Sort target_blocks
        self.target_blocks = sorted(set(self.target_blocks))
        
        # Ensure budget is canonical string
        if not self.budget.startswith("q:6:"):
            raise ValueError(f"Invalid budget format: {self.budget}")
        
        # Validate policy_header_hash is valid hex
        if not re.match(r"^[a-f0-9]{64}$", self.policy_header_hash):
            raise ValueError(f"Invalid policy_header_hash: {self.policy_header_hash}")
        
        return self
```

---

## Canonicalization Rules

### Rule 1: Reject Unknown Fields

```python
def validate_no_unknown_fields(action: dict, schema: dict) -> None:
    """Reject any fields not in schema."""
    allowed = set(schema.get("properties", {}).keys())
    provided = set(action.keys())
    
    unknown = provided - allowed
    if unknown:
        raise ValueError(f"Unknown fields: {unknown}")
```

### Rule 2: Reject NaN/Float

```python
def validate_no_floats(action: dict) -> None:
    """Recursively reject float values."""
    for key, value in action.items():
        if isinstance(value, float):
            raise ValueError(f"Float not allowed in field '{key}': {value}")
        elif isinstance(value, dict):
            validate_no_floats(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    validate_no_floats(item)
                elif isinstance(item, float):
                    raise ValueError(f"Float not allowed in list: {item}")
```

### Rule 3: Stable Ordering

```python
def canonicalize_dict(data: dict) -> dict:
    """Return dict with keys in lexicographic order."""
    return dict(sorted(data.items()))

def canonicalize_list(items: list) -> list:
    """Return list with stable ordering."""
    # For list of dicts, sort by first key
    if items and isinstance(items[0], dict):
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True))
    return items
```

### Rule 4: Stable Numeric Encoding

```python
def canonicalize_numeric(value: int | str | dict) -> str:
    """
    Convert numeric values to canonical DebtUnit string.
    
    - Integers: interpret as already scaled
    - Strings: must be q:6: format
    - Dicts: parse as rational and convert
    """
    if isinstance(value, int):
        return f"q:6:{value}"
    elif isinstance(value, str):
        if not value.startswith("q:6:"):
            raise ValueError(f"Invalid numeric format: {value}")
        return value
    elif isinstance(value, dict):
        # Parse as rational
        if "num" in value and "den" in value:
            num = value["num"]
            den = value["den"]
            du = DebtUnit.from_rational(num, den)
            return du.canonical()
        else:
            raise ValueError(f"Unknown numeric dict: {value}")
    else:
        raise ValueError(f"Unsupported numeric type: {type(value)}")
```

### Rule 5: Stable String Encoding

```python
def canonicalize_string(value: str) -> str:
    """
    Canonicalize string encoding.
    
    - UTF-8 encoding
    - NFC normalization
    """
    import unicodedata
    return unicodedata.normalize("NFC", value)
```

---

## Parsing Interface

```python
def parse_action(action_data: dict) -> ActionDescriptor:
    """
    Parse and validate action data.
    
    Applies all canonicalization rules.
    Raises ValueError for any issues.
    """
    # Validate against schema
    validate_schema(action_data)
    
    # Reject floats
    validate_no_floats(action_data)
    
    # Build ActionDescriptor
    action = ActionDescriptor(
        action_type=action_data["action_type"],
        target_blocks=list(action_data["target_blocks"]),
        payload=canonicalize_dict(action_data["payload"]),
        budget=action_data["budget"],
        disturbance_event=action_data.get("disturbance_event"),
        policy_header_hash=action_data["policy_header_hash"]
    )
    
    # Canonicalize
    action.canonicalize()
    
    # Compute hash
    action.action_descriptor_hash = hash(action.to_canonical_bytes())
    
    return action
```

---

## Action Type Payloads

### state_update

```json
{
  "action_type": "state_update",
  "target_blocks": [0, 1],
  "payload": {
    "transition_fn_id": "linear_step",
    "parameters": {
      "delta": "q:6:100000"
    }
  },
  "budget": "q:6:1000000",
  "policy_header_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

### contract_activate

```json
{
  "action_type": "contract_activate",
  "target_blocks": [2],
  "payload": {
    "contract_id": "position_limit_v1"
  },
  "budget": "q:6:500000",
  "policy_header_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

### contract_deactivate

```json
{
  "action_type": "contract_deactivate",
  "target_blocks": [2],
  "payload": {
    "contract_id": "position_limit_v1"
  },
  "budget": "q:6:0",
  "policy_header_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

### parameter_update

```json
{
  "action_type": "parameter_update",
  "target_blocks": [0],
  "payload": {
    "parameter_id": "Kp",
    "new_value": "q:6:1500000"
  },
  "budget": "q:6:100000",
  "policy_header_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

### boundary_enforce

```json
{
  "action_type": "boundary_enforce",
  "target_blocks": [0, 1, 2],
  "payload": {
    "boundary_id": "safe_operating_region",
    "enforcement_mode": "hard"
  },
  "budget": "q:6:2000000",
  "policy_header_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

---

## Policy Header

### Structure

```python
@dataclass
class PolicyHeader:
    """Commits to service and disturbance policies."""
    
    service_policy_id: str           # e.g., "CK0.service.v1"
    service_instance_id: str         # e.g., "linear_capped.mu:1.0"
    disturbance_policy_id: str      # DP0/DP1/DP2/DP3
    disturbance_params: dict        # Policy-specific parameters
    
    # For DP1
    e_bar: str | None = None        # Maximum disturbance bound
    
    # For DP2
    event_types: list[str] | None = None
    beta: dict[str, str] | None = None  # event -> bound mapping
    
    # For DP3
    e_model_id: str | None = None
    
    def hash(self) -> str:
        """Compute policy header hash."""
        return hash(self.to_canonical_bytes())
    
    def to_canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes."""
        data = {
            "service_policy_id": self.service_policy_id,
            "service_instance_id": self.service_instance_id,
            "disturbance_policy_id": self.disturbance_policy_id,
            "disturbance_params": self.disturbance_params,
        }
        if self.e_bar:
            data["e_bar"] = self.e_bar
        if self.event_types:
            data["event_types"] = sorted(self.event_types)
        if self.beta:
            data["beta"] = {k: v for k, v in sorted(self.beta.items())}
        if self.e_model_id:
            data["e_model_id"] = self.e_model_id
        
        return json.dumps(data, sort_keys=True).encode("utf-8")
```

---

## Rejection Examples

| Input | Why Rejected |
|-------|--------------|
| `{"value": 1.5}` | Float not allowed |
| `{"value": NaN}` | NaN not allowed |
| `{"value": 1e6}` | Scientific notation not allowed |
| `{"unknown_field": 1}` | Unknown field |
| `{"target_blocks": [1, 1]}` | Duplicate blocks |
| `{"budget": "1.0"}` | Not canonical format |
| `{"policy_header_hash": "abc"} | Invalid hash length |

---

*See also: [`4_measured_gate.md`](4_measured_gate.md), [`7_receipts.md`](7_receipts.md)*
