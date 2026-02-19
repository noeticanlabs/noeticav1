# PhaseLoom Authority Injection — Liveness Morphism

**Canon Doc Spine v1.0.0** — Section 10

---

## 1. Deadlock Condition

### 1.1 Formal Definition

A deadlock is a state where:

1. **Interlock active:** b ≤ b_min (or V_PL ≥ Θ in strong mode)
2. **Cannot solve:** SOLVE steps with A > 0 are rejected
3. **Cannot repair:** REPAIR/RESOLVE cannot reduce V further without temporary amplification
4. **Budget exhausted:** b cannot pay for needed exploration

### 1.2 Detection

```python
def detect_deadlock(state: PLState, params: PLParams) -> bool:
    """Detect if system is in deadlock."""
    
    # Interlock must be active
    if state.b > params.b_min:
        return False
    
    # Check if repair can progress
    can_repair = state.T > 0 or state.C > 0
    
    return not can_repair
```

---

## 2. Authority Injection Step Type

### 2.1 Definition

Define a transition type:

**STEP_AUTH_INJECT**

### 2.2 Constraints

| Constraint | Formula | Description |
|-----------|---------|-------------|
| Budget increase | b^+ > b | Budget must increase |
| Authority increase | a^+ > a | Authority must increase |
| Violation unchanged | Δv = 0 | No change in V (v1 safe choice) |

### 2.3 Implementation

```python
@dataclass
class AuthInjectStep:
    """Authority injection step."""
    delta_b: FixedPoint  # Budget increase (> 0)
    delta_a: FixedPoint  # Authority increase (> 0)
    multisig: MultiSig   # Authorization proof
    policy_bundle_id: str  # Policy binding
    
    def validate(self) -> bool:
        """Validate injection constraints."""
        return (
            self.delta_b > FixedPoint(0) and
            self.delta_a > FixedPoint(0) and
            self.multisig.is_valid()
        )
```

---

## 3. Authorization Contract

### 3.1 Requirements

Authority injection must include:

1. **Multi-signature proof** from human/DAO signers
2. **Policy bundle ID** binding authorization rules
3. **Explicit declared increase** (Δb_inj, Δa_inj)

### 3.2 Multi-Sig Structure

```python
@dataclass
class MultiSig:
    """Multi-signature authorization."""
    signers: List[str]           # Authorized signer addresses
    threshold: int               # Required signatures
    signatures: List[bytes]      # Actual signatures
    message_hash: str           # Hash of injection request
    
    def is_valid(self) -> bool:
        """Verify multi-sig validity."""
        # Check threshold
        if len(self.signatures) < self.threshold:
            return False
        
        # Verify each signature
        for sig in self.signatures[:self.threshold]:
            if not verify_signature(self.message_hash, sig):
                return False
        
        return True
```

---

## 4. Injection Effects

### 4.1 State Changes

| Field | Before | After |
|-------|--------|-------|
| b | b | b + Δb_inj |
| a | a | a + Δa_inj |
| V | V | V (unchanged in v1) |
| C | C | C (unchanged) |
| T | T | T (unchanged) |

### 4.2 Liveness Restoration

After injection:
- Budget increases: b > b_min
- Interlock deactivates
- SOLVE steps become admissible again

---

## 5. Authorization Flow

### 5.1 Request Creation

```python
def create_injection_request(
    delta_b: FixedPoint,
    delta_a: FixedPoint,
    policy_bundle_id: str,
    signers: List[str],
    threshold: int
) -> InjectionRequest:
    """Create authority injection request."""
    
    request = InjectionRequest(
        delta_b=delta_b,
        delta_a=delta_a,
        policy_bundle_id=policy_bundle_id,
        signers=signers,
        threshold=threshold
    )
    
    # Hash for signing
    request.message_hash = sha3_256(request.serialize())
    
    return request
```

### 5.2 Signing

```python
def sign_request(request: InjectionRequest, private_key: bytes) -> bytes:
    """Sign injection request."""
    return sign(request.message_hash, private_key)
```

### 5.3 Execution

```python
def execute_injection(
    state: PLState,
    request: InjectionRequest
) -> PLState:
    """Execute authority injection."""
    
    if not request.validate():
        raise UnauthorizedInjectionError("Invalid injection")
    
    # Apply injection
    return PLState(
        x=state.x,
        C=state.C,
        T=state.T,
        b=state.b + request.delta_b,
        a=state.a + request.delta_a
    )
```

---

## 6. Receipt Integration

### 6.1 Required Fields

| Field | Description |
|-------|-------------|
| step_type | AUTH_INJECT |
| delta_b_inj | Budget increase |
| delta_a_inj | Authority increase |
| multisig | Multi-signature proof |
| policy_bundle_id | Policy binding |
| v_prev | V before (equals v_next) |
| v_next | V after (equals v_prev) |

### 6.2 Verification

The verifier checks:
1. step_type == AUTH_INJECT
2. delta_b_inj > 0
3. delta_a_inj > 0
4. v_prev == v_next (no violation change)
5. multisig is valid
6. b_next = b_prev + delta_b_inj
7. a_next = a_prev + delta_a_inj

---

## 7. Security Considerations

### 7.1 Attack Surface

- **Forged authorization:** Prevented by multisig
- **Excessive injection:** Limited by threshold and policy
- **Repeated injection:** Tracked via cumulative authority a

### 7.2 Governance Limits

```python
@dataclass
class InjectionLimits:
    """Limits on authority injection."""
    max_delta_b: FixedPoint   # Max budget increase per step
    max_delta_a: FixedPoint   # Max authority increase per step
    max_total_a: FixedPoint   # Max cumulative authority
    min_interval: int         # Min steps between injections
    
    def check_limits(self, state: PLState, request: InjectionRequest) -> bool:
        """Verify injection stays within limits."""
        return (
            request.delta_b <= self.max_delta_b and
            request.delta_a <= self.max_delta_a and
            state.a + request.delta_a <= self.max_total_a
        )
```

---

## 8. Status

- [x] Deadlock condition defined
- [x] Authority injection step type specified
- [x] Authorization contract defined
- [x] Injection effects documented
- [ ] Implementation in src/phaseloom/authority.py

---

*Authority Injection is the liveness escape hatch that allows the system to recover from deadlock through explicit multi-sig authorization, restoring budget and enabling continued execution.*
