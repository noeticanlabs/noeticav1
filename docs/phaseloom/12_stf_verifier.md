# PhaseLoom State Transition Function — LoomVerifier

**Canon Doc Spine v1.0.0** — Section 13

---

## 1. Overview

### 1.1 Module Name

`LoomVerifier`

### 1.2 Purpose

Deterministic fixed-point state transition function that:
- Verifies receipt validity
- Enforces all PhaseLoom constraints
- Computes next state

---

## 2. Inputs

### 2.1 Required Inputs

| Input | Type | Description |
|-------|------|-------------|
| prev_state | PLState | Previous extended state |
| receipt | Receipt | Receipt payload |
| params | Params | Parameter bundle |
| auth_ctx | AuthContext | Authorization context |

### 2.2 Auth Context

```python
@dataclass
class AuthContext:
    """Authorization context for STF."""
    signer_set: Set[str]       # Authorized signers
    dao_rules: Optional[Dict]  # DAO governance rules
    timestamp: uint64          # Execution timestamp
```

---

## 3. Deterministic Arithmetic

### 3.1 Fix Type

```python
@dataclass
class FixedPoint:
    """Fixed-point number with truncation toward zero."""
    value: int    # Scaled integer
    scale: int    # Decimal places (default 6)
    
    @staticmethod
    def from_float(f: float, scale: int = 6) -> 'FixedPoint':
        """Convert float to fixed-point."""
        return FixedPoint(int(f * 10**scale), scale)
    
    def to_float(self) -> float:
        """Convert to float."""
        return self.value / 10**self.scale
```

### 3.2 Operations

```python
def mul_fix(a: FixedPoint, b: FixedPoint) -> FixedPoint:
    """Multiply with truncation toward zero."""
    result = a.value * b.value
    # Truncate: shift right by scale
    scaled = result // 10**a.scale
    return FixedPoint(scaled, a.scale)

def div_fix(a: FixedPoint, b: FixedPoint) -> FixedPoint:
    """Divide with truncation toward zero."""
    if b.value == 0:
        raise DivisionByZero()
    # Scale up before dividing
    scaled = a.value * 10**a.scale
    result = scaled // b.value
    return FixedPoint(result, a.scale)
```

### 3.3 Overflow Handling

```python
MAX_INT = 2**63 - 1

def check_overflow(value: int) -> None:
    """Check for overflow."""
    if abs(value) > MAX_INT:
        raise OverflowError("Consensus reject")
```

---

## 4. Step Type Semantics

### 4.1 SOLVE

**Requirements:**
- Must satisfy interlock (if b ≤ b_min, then A = 0)
- Must satisfy budget charge law
- Recurrences must hold

**Reject codes:**
- INTERLOCK_VIOLATION
- BUDGET_CHARGE_VIOLATION

### 4.2 REPAIR

**Requirements:**
- Allowed under interlock
- Must satisfy budget charge law
- Recurrences must hold
- Should reduce V

### 4.3 RESOLVE

**Requirements:**
- Must reduce tension (T_next < T_prev)
- Allowed under interlock

### 4.4 AUTH_INJECT

**Requirements:**
- Must have valid multisig
- Must increase b: b_next > b_prev
- Must increase a: a_next > a_prev
- Must not change V: v_next = v_prev (v1)
- Budget increase must match declaration

**Reject codes:**
- UNAUTHORIZED_INJECTION
- INVALID_INJECTION_AMOUNT
- MULTISIG_INVALID

---

## 5. Reject Codes

### 5.1 Complete Enum

```python
class RejectCode(Enum):
    """STF reject codes."""
    
    # Schema/Hash
    SCHEMA_HASH_MISMATCH = "schema"
    
    # State
    INVALID_STATE = "state"
    STATE_HASH_MISMATCH = "state_hash"
    
    # Recurrences
    CURVATURE_VIOLATION = "curvature"
    TENSION_VIOLATION = "tension"
    BUDGET_VIOLATION = "budget"
    AUTHORITY_VIOLATION = "authority"
    
    # Constraints
    BUDGET_CHARGE_VIOLATION = "budget_charge"
    INTERLOCK_VIOLATION = "interlock"
    
    # Authorization
    UNAUTHORIZED_INJECTION = "auth"
    MULTISIG_INVALID = "multisig"
    SIGNATURE_INVALID = "signature"
    
    # Arithmetic
    OVERFLOW = "overflow"
    DIVISION_BY_ZERO = "div_zero"
    INVALID_FIXED_POINT = "fix_invalid"
    
    # Chain
    RECEIPT_CHAIN_BREAK = "chain"
    DUPLICATE_RECEIPT = "duplicate"
```

### 5.2 Error Response

```python
@dataclass
class STFResult:
    """State transition result."""
    accepted: bool
    next_state: Optional[PLState]
    reject_code: Optional[RejectCode]
    message: str
```

---

## 6. Transition Verification

### 6.1 Full Verification Pipeline

```python
def verify_transition(
    prev_state: PLState,
    receipt: Receipt,
    params: Params,
    auth_ctx: AuthContext
) -> STFResult:
    """Verify complete state transition."""
    
    # 1. Schema check
    if receipt.schema != "coh.receipt.pl.v1":
        return STFResult(False, None, RejectCode.SCHEMA_HASH_MISMATCH, "Invalid schema")
    
    # 2. Boundary matching
    if not verify_boundary(prev_state, receipt):
        return STFResult(False, None, RejectCode.STATE_HASH_MISMATCH, "Boundary mismatch")
    
    # 3. Compute derived values
    delta_v = receipt.v_next - receipt.v_prev
    A = max(delta_v, 0)
    D = max(-delta_v, 0)
    
    # 4. Verify recurrences
    if not verify_curvature(receipt, params):
        return STFResult(False, None, RejectCode.CURVATURE_VIOLATION, "Curvature violation")
    
    if not verify_tension(receipt, params):
        return STFResult(False, None, RejectCode.TENSION_VIOLATION, "Tension violation")
    
    # 5. Verify budget law
    if not verify_budget_charge(receipt, params):
        return STFResult(False, None, RejectCode.BUDGET_CHARGE_VIOLATION, "Budget charge violation")
    
    # 6. Verify interlock
    if not verify_interlock(receipt, params):
        return STFResult(False, None, RejectCode.INTERLOCK_VIOLATION, "Interlock violation")
    
    # 7. Verify authorization (if AUTH_INJECT)
    if receipt.step_type == StepType.AUTH_INJECT:
        if not verify_auth_inject(receipt, auth_ctx):
            return STFResult(False, None, RejectCode.UNAUTHORIZED_INJECTION, "Unauthorized")
    
    # 8. Compute next state
    next_state = compute_next_state(prev_state, receipt)
    
    return STFResult(True, next_state, None, "Accepted")
```

### 6.2 Compute Next State

```python
def compute_next_state(prev: PLState, receipt: Receipt) -> PLState:
    """Compute next extended state."""
    return PLState(
        x=receipt.x_next,
        C=receipt.C_next,
        T=receipt.T_next,
        b=receipt.b_next,
        a=receipt.a_next
    )
```

---

## 7. Determinism Guarantees

### 7.1 Sources of Non-Determinism

| Source | Mitigation |
|--------|------------|
| Float arithmetic | Fixed-point only |
| Random numbers | None allowed |
| System time | Use receipt timestamp |
| Hash order | Canonical JSON |
| Set iteration | Sorted order |

### 7.2 Verification

```python
def verify_determinism(receipts: List[Receipt]) -> bool:
    """Verify deterministic execution."""
    for r in receipts:
        # Check no floats
        assert all(isinstance(v, (int, str)) for v in r.values())
        # Check canonical JSON
        canon = canon_json(r)
        digest = sha3_256(canon)
    return True
```

---

## 8. Integration Points

### 8.1 NK-2 Scheduler

```python
class LoomVerifierSTF:
    """Integration with NK-2 scheduler."""
    
    def __init__(self, params: Params):
        self.params = params
        self.verifier = LoomVerifier()
    
    def execute_batch(self, batch: Batch, state: PLState) -> BatchResult:
        """Execute batch through STF."""
        results = []
        current_state = state
        
        for receipt in batch.receipts:
            result = self.verifier.verify_transition(
                current_state, receipt, self.params, batch.auth_ctx
            )
            
            if not result.accepted:
                return BatchResult(
                    accepted=False,
                    failed_at=len(results),
                    reject_code=result.reject_code
                )
            
            results.append(result.next_state)
            current_state = result.next_state
        
        return BatchResult(accepted=True, final_state=current_state)
```

---

## 9. Status

- [x] Inputs defined
- [x] Arithmetic library specified
- [x] Step semantics defined
- [x] Reject codes enumerated
- [x] Verification pipeline described
- [ ] Implementation in src/phaseloom/verifier.py

---

*The LoomVerifier STF provides deterministic, verifiable state transitions that enforce all PhaseLoom contracts.*
