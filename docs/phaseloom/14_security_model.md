# PhaseLoom Security Model

**Canon Doc Spine v1.0.0** — Section 15

---

## 1. Threat Model

### 1.1 Adversarial Capabilities

| Capability | Description |
|------------|-------------|
| Network control | May intercept/modify messages |
| Computational power | May attempt brute force |
| Collusion | May coordinate multiple actors |
| Insider | May have access to partial state |

### 1.2 Non-Goals

The system does not protect against:
- Quantum adversaries (post-quantum not implemented)
- Social engineering of authorized signers
- Physical compromise of hardware

---

## 2. Attack Surfaces

### 2.1 Enumerated Surfaces

| Surface | Risk | Mitigation |
|---------|------|------------|
| Float nondeterminism | HIGH | Fixed-point arithmetic |
| Serialization inconsistency | HIGH | Canonical JSON |
| Authority forgery | CRITICAL | Multisig verification |
| Tension gaming | MEDIUM | Deterministic formulas |
| Budget manipulation | CRITICAL | STF checks |
| Receipt replay | MEDIUM | Chain verification |
| Hash collision | LOW | SHA3-256 |

---

## 3. Countermeasures

### 3.1 Float Elimination

**Threat:** Floating-point arithmetic introduces non-determinism

**Countermeasure:** Fixed-point arithmetic only
```python
# All arithmetic uses fixed-point
value = FixedPoint(1000000)  # = 1.0 with scale 6
result = mul_fix(value, other)
```

### 3.2 Serialization

**Threat:** Inconsistent JSON serialization enables hash malleability

**Countermeasure:** Canonical JSON
- Sorted keys
- No whitespace
- Numbers as strings (fixed-point)
- UTF-8 encoding

### 3.3 Authority Forgery

**Threat:** Attacker forges authority injection

**Countermeasure:** Multi-signature verification
```python
def verify_multisig(request: AuthInjectRequest, signers: Set[str]) -> bool:
    """Verify multi-sig."""
    required = threshold
    verified = sum(1 for sig in request.signatures 
                  if verify_signature(request.message, sig, signers))
    return verified >= required
```

### 3.4 Tension Gaming

**Threat:** Attacker manipulates tension for advantage

**Countermeasure:** Deterministic computation
- Use canonical on-chain formula
- Audit proofs for off-chain computation

### 3.5 Budget Manipulation

**Threat:** Attacker inflates budget or avoids charges

**Countermeasure:** STF enforcement
```python
def verify_budget_charge(receipt, params):
    required = params.kappa_A * receipt.A + params.kappa_T * receipt.delta_T_inc
    return receipt.delta_b >= required
```

---

## 4. Failure Modes

### 4.1 Safety-First Halt

When interlock activates:
- SOLVE steps with A > 0 are rejected
- Only REPAIR, RESOLVE, AUTH_INJECT allowed

**Response:**
```python
if state.b <= params.b_min:
    # Safety halt - reject risky operations
    reject_solve_steps()
```

### 4.2 Liveness Restoration

When deadlock occurs:
- Authority injection escape hatch available
- Requires multi-sig authorization

### 4.3 Unknown Policy

**Threat:** Unknown policy label in receipt

**Response:** Reclassify or halt
```python
if policy_label not in known_policies:
    if strict_mode:
        reject_receipt()
    else:
        log_warning("Unknown policy")
        assign_default_classification()
```

---

## 5. Consensus Security

### 5.1 Determinism Requirements

All consensus-critical operations must be deterministic:
- State transitions
- Receipt verification
- Hash computation
- Fixed-point arithmetic

### 5.2 Verification

```python
def verify_determinism():
    """Verify consensus-critical code is deterministic."""
    # No random imports
    # No time-dependent operations
    # No float arithmetic
    # All operations use fixed-point
```

---

## 6. Governance Security

### 6.1 Parameter Changes

Parameters are governance-controlled:
- Changes require DAO approval
- Cannot change during execution epoch
- Must be part of parameter bundle

### 6.2 Authority Limits

Authority injection is bounded:
```python
@dataclass
class InjectionLimits:
    max_delta_b: FixedPoint    # Per-step limit
    max_delta_a: FixedPoint    # Per-step limit
    max_total_a: FixedPoint     # Cumulative limit
    min_interval: int          # Steps between injections
```

---

## 7. Cryptographic Assumptions

### 7.1 Hash Function

- **Algorithm:** SHA3-256
- **Security:** 128-bit collision resistance
- **Prefix:** 'h:' for hash identifiers

### 7.2 Signatures

- **Algorithm:** ECDSA (secp256k1) or Ed25519
- **Security:** Assuming discrete log hardness

### 7.3 Merkle Trees

- **Security:** Reduced from hash function
- **Proof:** Logarithmic size

---

## 8. Security Properties

### 8.1 Safety

**Claim:** The system never accepts unsafe transitions when interlock is active.

**Proof:** Interlock rejects SOLVE with A > 0 when b ≤ b_min.

### 8.2 Liveness

**Claim:** If budget is available, valid transitions can proceed.

**Proof:** SOLVE, REPAIR, RESOLVE steps admitted when b > b_min.

### 8.3 Boundedness

**Claim:** V_PL cannot diverge without exhausting budget.

**Proof:** Budget charge law limits amplification.

### 8.4 Verifiability

**Claim:** All state transitions are cryptographically verifiable.

**Proof:** Receipt chain with Merkle proofs.

---

## 9. Incident Response

### 9.1 Detection

Monitor for:
- Reject rate spikes
- Unusual authority injections
- Budget exhaustion
- Interlock activation frequency

### 9.2 Mitigation

| Incident | Response |
|----------|----------|
| Attack detected | Freeze affected contracts |
| Bug found | Parameter adjustment via DAO |
| Key compromise | Key rotation procedure |

---

## 10. Status

- [x] Threat model defined
- [x] Attack surfaces enumerated
- [x] Countermeasures specified
- [x] Failure modes documented
- [x] Security properties stated

---

*The security model identifies all known attack surfaces and specifies countermeasures. Safety-first design ensures the system halts gracefully under adverse conditions.*
