# NK-4G Verifier Consistency

**Related:** [`6_regularization_policy.md`](6_regularization_policy.md), [`8_limits_and_nonclaims.md`](8_limits_and_nonclaims.md)

---

## 7.1 No New Verification Rules

NK-4G is an **interpretive layer**. It does not introduce new verification requirements.

### Verification Scope

All quantities used by NK-4G derive from existing NK-1/NK-2:

| Quantity | Source | Verification |
|----------|--------|-------------|
| V(x) | NK-1 V(x) | Already verified by NK-1 verifier |
| δ_g(x) | NK-1 transition | Already verified by NK-1 verifier |
| ε_B | NK-1 batch residual | Already verified by NK-1 verifier |
| CTD rule | PolicyBundle | Verified via policy_digest |
| L_max | PolicyBundle | Verified via policy_digest |
| ε̂_B | PolicyBundle | Verified via policy_digest |

---

## 7.2 Receipt Compatibility

### Removing NK-4G Does Not Invalidate Receipts

Since NK-4G does not:
- Modify V computation
- Modify transition semantics
- Add state variables
- Change receipt schema

**Receipts remain valid** with or without NK-4G interpretation.

### Receipt Fields Required

The verifier requires:

```
receipt_data = {
    "step_index": ...,
    "state_hash_before": ...,
    "state_hash_after": ...,
    "V_before": ...,
    "V_after": ...,
    "service_policy_id": ...,
    "service_instance_id": ...,
    "law_satisfied": ...,
    "invariant_status": ...,
    "receipt_hash": ...
}
```

No NK-4G-specific fields required.

---

## 7.3 Optional NK-4G Analysis

### Analysis Output (Not Required)

NK-4G can produce analysis for governance:

```
nk4g_analysis = {
    "spectral_gap_estimate": ...,
    "regularization_applied": ...,
    "epsilon_value": ...,
    "stability_margin": ...,
    "center_dimension": ...
}
```

This is **supplementary** - not part of core verification.

### Governance Clock

NK-4G analysis can feed governance tooling:

- Monitoring spectral gap over time
- Detecting metastability trends
- Triggering policy updates

But this is **external** to the verifier.

---

## 7.4 Verification Checklist

### Core Verification (Required)

```
verify(receipt):
    1. Check receipt_hash chain integrity
    2. Verify state_hash transitions
    3. Verify V(x) computation
    4. Verify service law satisfaction
    5. Verify invariant hold
    6. Verify policy_digest match
```

### NK-4G Analysis (Optional)

```
analyze_nk4g(receipt):
    1. Compute eigenvalue estimate from M
    2. Check spectral gap
    3. Report stability margin
    4. Flag if regularization was used
```

---

## 7.5 Consistency Guarantees

### Theorem 7.1: Interpretation Consistency

For any execution trace:

```
NK-1 verifier accepts
    ⇔
NK-4G analysis can be performed
    ⇔
All quantities are within NK-4G assumptions
```

### Proof Sketch

NK-4G assumptions:
1. V(x) is computed by NK-1 (verified)
2. δ bounds are enforced by NK-1 (verified)
3. ε_B bounds are enforced by NK-1 (verified)
4. PolicyBundle constants are hash-locked (verified)

If all NK-1 verifications pass, NK-4G analysis is valid.

---

## 7.6 Summary

| Aspect | Status |
|--------|--------|
| New verification rules | None |
| Receipt modification | None |
| Required fields | None (uses existing) |
| Optional analysis | Available for governance |
| Removal impact | None on core verification |

NK-4G is **purely additive** - it enhances understanding without changing contracts.
