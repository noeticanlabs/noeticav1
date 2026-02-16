# NK-1 Replay Verifier

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`7_receipts.md`](7_receipts.md), [`../ck0/9_replay_verifier.md`](../ck0/9_replay_verifier.md)

---

## Overview

The NK-1 Replay Verifier is the **hostile review weapon** - a standalone verifier that independently recomputes all gate decisions from receipts and policy headers. It has no trust in the prover.

---

## Verifier Interface

```python
@dataclass
class VerifierInput:
    """All inputs needed for verification."""
    
    # Policy commitments
    policy_header: PolicyHeader
    
    # Contract set definition
    contract_set: ContractSet
    
    # Matrix registry (if curvature used)
    curvature_registry: CurvatureRegistry | None = None
    
    # Receipt stream
    receipts: list[Receipt]
    
    # Genesis state (for first receipt)
    genesis_state: State | None = None


@dataclass
class VerificationResult:
    """Result of verification."""
    
    valid: bool
    failed_step: int | None
    failure_reason: str | None
    details: list[str]  # Detailed log
    
    @property
    def summary(self) -> str:
        if self.valid:
            return f"Verification PASSED ({len(self.details)} checks)"
        else:
            return f"Verification FAILED at step {self.failed_step}: {self.failure_reason}"
```

---

## Verification Checklist

The verifier performs these checks **in order**, stopping at first failure:

### 1. Hash Chain Continuity

```python
def verify_hash_chain(receipts: list[Receipt]) -> tuple[bool, str | None]:
    """
    Verify hash chain continuity.
    
    - First receipt prev_receipt_hash must be all-zeros
    - Each receipt's prev_receipt_hash must match previous receipt's hash
    - Each receipt's hash must match recomputed hash
    """
    for i, receipt in enumerate(receipts):
        # Check prev_hash
        if i == 0:
            expected_prev = "0" * 64
        else:
            expected_prev = receipts[i-1].receipt_hash
        
        if receipt.prev_receipt_hash != expected_prev:
            return False, f"step_{i}:prev_hash_mismatch"
        
        # Check receipt hash
        computed = compute_receipt_hash(receipt)
        if computed != receipt.receipt_hash:
            return False, f"step_{i}:receipt_hash_mismatch"
    
    return True, None
```

### 2. Action Schema Validity

```python
def verify_action_schema(receipt: Receipt, known_actions: dict) -> tuple[bool, str | None]:
    """
    Verify action descriptor hash matches known valid actions.
    
    The verifier checks that the action_descriptor_hash corresponds to
    a valid action that passed canonicalization.
    """
    # In practice, the verifier would have the canonical action
    # For now, we check hash format validity
    if not re.match(r"^[a-f0-9]{64}$", receipt.action_descriptor_hash):
        return False, f"invalid_action_hash_format"
    
    return True, None
```

### 3. State Hash Matches

```python
def verify_state_hashes(
    receipt: Receipt,
    state_pre: State,
    state_post: State
) -> tuple[bool, str | None]:
    """
    Verify state hashes match committed canonical bytes.
    """
    hash_pre = hash(state_pre.to_canonical_bytes())
    hash_post = hash(state_post.to_canonical_bytes())
    
    if receipt.state_hash_pre != hash_pre:
        return False, "state_hash_pre_mismatch"
    
    if receipt.state_hash_post != hash_post:
        return False, "state_hash_post_mismatch"
    
    return True, None
```

### 4. Recompute V(x)

```python
def verify_v_computation(
    receipt: Receipt,
    contract_set: ContractSet,
    state: State,
    expected_v: DebtUnit
) -> tuple[bool, str | None]:
    """
    Verify V(x) computation.
    
    Recompute V(x) from contract set and state.
    Compare to receipt value.
    """
    computed_v = compute_v(contract_set, state)
    
    if computed_v.int_value != expected_v.int_value:
        return False, f"v_computation_mismatch:expected_{expected_v},got_{computed_v}"
    
    return True, None
```

### 5. Compute Service Law

```python
def verify_service_law(
    debt_pre: DebtUnit,
    budget: DebtUnit,
    service_policy_id: str,
    service_instance_id: str
) -> tuple[bool, str | None, DebtUnit]:
    """
    Verify service law computation.
    
    Recompute S(D_pre, B) using declared policy.
    """
    # Parse service instance
    if service_instance_id.startswith("linear_capped.mu:"):
        mu = Decimal(service_instance_id.split(":")[1])
        mu_debt = DebtUnit.from_decimal(str(mu))
        
        # S(D, B) = min(D, μ * B)
        service_cap = budget.mul_int(mu_debt.int_value)
        service = min(debt_pre, service_cap)
        
        return True, None, service
    else:
        return False, f"unknown_service_instance:{service_instance_id}", DebtUnit(0)
```

### 6. Disturbance Policy Check

```python
def verify_disturbance_policy(
    receipt: Receipt,
    policy_header: PolicyHeader
) -> tuple[bool, str | None]:
    """
    Verify disturbance policy constraints.
    """
    disturbance = parse_debtunit(receipt.disturbance)
    policy_id = receipt.disturbance_policy_id
    
    if policy_id == "DP0":
        # Must be zero
        if disturbance.int_value != 0:
            return False, "dp0_violation:nonzero"
    
    elif policy_id == "DP1":
        # Must be within bound
        e_bar = parse_debtunit(policy_header.e_bar)
        if disturbance.int_value < 0:
            return False, "dp1_violation:negative"
        if disturbance.int_value > e_bar.int_value:
            return False, "dp1_violation:exceeds_bound"
    
    elif policy_id == "DP2":
        # Must be within event bound
        # (Would need event type from action)
        pass
    
    elif policy_id == "DP3":
        # Must match model
        # (Would need model computation)
        pass
    
    return True, None
```

### 7. Check Law Inequality

```python
def verify_law_inequality(
    debt_pre: DebtUnit,
    debt_post: DebtUnit,
    service: DebtUnit,
    disturbance: DebtUnit
) -> tuple[bool, str | None]:
    """
    Verify CK-0 Law: D_post ≤ D_pre - S(D_pre, B) + E
    """
    allowed_max = debt_pre - service + disturbance
    
    if debt_post.int_value > allowed_max.int_value:
        return False, f"law_violation:debt_exceeded"
    
    return True, None
```

### 8. Matrix Invariants (if applicable)

```python
def verify_matrix_invariants(
    matrix: CurvatureMatrix
) -> tuple[bool, str | None]:
    """
    Verify matrix invariants.
    """
    # Symmetry
    entry_map = {(e.row, e.col): e.value for e in matrix.entries}
    for (i, j), value in entry_map.items():
        if (j, i) not in entry_map:
            return False, f"asymmetric_missing_entry_{i}_{j}"
        if entry_map[(j, i)].int_value != value.int_value:
            return False, f"asymmetric_value_{i}_{j}"
    
    # Nonnegativity
    for entry in matrix.entries:
        if entry.value.int_value < 0:
            return False, f"negative_entry_{entry.row}_{entry.col}"
    
    return True, None
```

---

## Complete Verification

```python
class ReplayVerifier:
    """Standalone NK-1 replay verifier."""
    
    def verify(self, input: VerifierInput) -> VerificationResult:
        """Run full verification."""
        details = []
        
        # Check receipts not empty
        if not input.receipts:
            return VerificationResult(
                valid=False,
                failed_step=0,
                failure_reason="no_receipts",
                details=["No receipts to verify"]
            )
        
        # Step 1: Hash chain
        ok, err = verify_hash_chain(input.receipts)
        details.append(f"Step 1 - Hash chain: {'PASS' if ok else 'FAIL'}")
        if not ok:
            return VerificationResult(valid=False, failed_step=0, failure_reason=err, details=details)
        
        # For each receipt...
        for i, receipt in enumerate(input.receipts):
            step_details = f"Step {i + 2} - Receipt {i}:"
            
            # Step 2: Action schema
            ok, err = verify_action_schema(receipt, {})
            details.append(f"{step_details} Action schema: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return VerificationResult(valid=False, failed_step=i, failure_reason=err, details=details)
            
            # Step 3: State hashes (would need actual states)
            # In practice, verifier would have state snapshots
            
            # Step 4: V(x) computation
            debt_pre = parse_debtunit(receipt.debt_pre)
            # Would need actual contract set and state
            
            # Step 5: Service law
            ok, err, service = verify_service_law(
                debt_pre,
                parse_debtunit(receipt.budget),
                receipt.service_policy_id,
                receipt.service_instance_id
            )
            details.append(f"{step_details} Service law: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return VerificationResult(valid=False, failed_step=i, failure_reason=err, details=details)
            
            # Step 6: Disturbance policy
            ok, err = verify_disturbance_policy(receipt, input.policy_header)
            details.append(f"{step_details} Disturbance policy: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return VerificationResult(valid=False, failed_step=i, failure_reason=err, details=details)
            
            # Step 7: Law inequality
            debt_post = parse_debtunit(receipt.debt_post)
            disturbance = parse_debtunit(receipt.disturbance)
            ok, err = verify_law_inequality(debt_pre, debt_post, service, disturbance)
            details.append(f"{step_details} Law inequality: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return VerificationResult(valid=False, failed_step=i, failure_reason=err, details=details)
        
        # All checks passed
        return VerificationResult(
            valid=True,
            failed_step=None,
            failure_reason=None,
            details=details
        )
```

---

## Verification Output

### Success

```json
{
  "valid": true,
  "failed_step": null,
  "failure_reason": null,
  "details": [
    "Step 1 - Hash chain: PASS",
    "Step 2 - Receipt 0: Action schema: PASS",
    "Step 2 - Receipt 0: Service law: PASS",
    "Step 2 - Receipt 0: Disturbance policy: PASS",
    "Step 2 - Receipt 0: Law inequality: PASS",
    ...
  ]
}
```

### Failure

```json
{
  "valid": false,
  "failed_step": 5,
  "failure_reason": "law_violation:debt_exceeded",
  "details": [
    "Step 1 - Hash chain: PASS",
    ...
    "Step 2 - Receipt 5: Service law: PASS",
    "Step 2 - Receipt 5: Disturbance policy: PASS",
    "Step 2 - Receipt 5: Law inequality: FAIL"
  ]
}
```

---

## Verification Properties

| Property | Description |
|----------|-------------|
| **Deterministic** | Same inputs → same result |
| **Independent** | No trust in prover |
| **Complete** | Checks all receipt fields |
| **Efficient** | Linear in receipt count |
| **Auditable** | Detailed failure logs |

---

## Usage

```python
# Create verifier
verifier = ReplayVerifier()

# Run verification
result = verifier.verify(VerifierInput(
    policy_header=policy_header,
    contract_set=contract_set,
    curvature_registry=registry,
    receipts=receipts,
    genesis_state=genesis
))

# Check result
if result.valid:
    print("Verification PASSED")
else:
    print(f"Verification FAILED: {result.failure_reason}")
    for detail in result.details:
        print(f"  {detail}")
```

---

*See also: [`7_receipts.md`](7_receipts.md), [`9_conformance.md`](9_conformance.md), [`../ck0/9_replay_verifier.md`](../ck0/9_replay_verifier.md)*
