# Coh Module Interface Contract v1.0.0

**Canonical ID:** `coh.module_contract.v1`  
**Version:** `1.0.0`  
**Status:** Canon (implementation-binding)  
**Scope:** Defines the required *module surface area* for any system claiming to be an object in \(\mathbf{Coh}\).

---

## 0. Purpose

This document freezes the **implementation contract** for a Coh object so that:

- every Coh-based system has the same structural interface,
- verifiers remain deterministic,
- receipts remain canonical,
- cross-system tooling (NK-2/NK-4G validators, slab compressors, auditors) can be reused,
- drift becomes mechanically visible (hash changes).

This is the "compiler physics" boundary for Coh.

---

## 1. Coh Object Implementation Artifact

Any Coh object must ship a **Coh Object Artifact**:

\[
\mathsf{ObjArtifact}(\mathcal S)
\]

as canonical bytes, hashed and optionally signed.

### 1.1 Required metadata

| Field | Type | Description |
|-------|------|-------------|
| `schema_id` | string | `"coh.object.v1"` |
| `version` | string | `"1.0.0"` |
| `object_id` | string | Stable identifier |
| `canon_profile_id` | string | `"coh.canon_profile.v1"` |
| `canon_profile_hash` | string | `sha256:...` |
| `policy_hash` | string | `sha256:...` |
| `receipt_schema_id` | string | e.g. `"coh.receipt.micro.v1"` |
| `slab_schema_id` | string | e.g. `"coh.receipt.slab.v1"` |
| `verifier_id` | string | Stable identifier |
| `verifier_hash` | string | `sha256:...` |

### 1.2 Required declared structure

| Field | Description |
|-------|-------------|
| `state_space_decl` | Description of \(X\) |
| `potential_decl` | Description of \(V\) (or receipt-bound surrogate) |
| `admissibility_decl` | Either `zero_set` or `tube` with threshold \(\Theta\) |
| `transition_decl` | Description of step types and what RV checks |

---

## 2. Canonical Profiles (Non-Negotiable)

Every Coh module must bind itself to a **canon profile** that fixes:

### 2.1 Serialization

| Requirement | Description |
|-------------|-------------|
| Format | Canonical JSON: RFC 8785 JCS |
| Text | UTF-8 NFC normalization |
| Keys | Deterministic key ordering (implied by JCS) |

### 2.2 Hash

| Requirement | Description |
|-------------|-------------|
| Algorithm | `SHA-256` |
| Domain tag | `COH_V1` (bytes fixed by canon profile) |

Chain digest update rule:

\[
H_{n+1} = \mathrm{SHA256}(\mathrm{tag}\ \|\ H_n\ \|\ \mathrm{JCS}(r_n))
\]

### 2.3 Numeric domain (Verifier-side)

**Verifier MUST NOT use IEEE-754 float.**

Allowed v1 numeric domains:

| Domain | Description |
|--------|-------------|
| `QFixed(p)` | Scaled integers with frozen `p` |
| Rational | `(num, den)` bigints (optional) |
| Intervals | Over `QFixed(p)` (recommended) |

All numeric fields in receipts are encoded as **strings**.

### 2.4 Overflow and rounding

Canon must specify:

- Integer width (int128 or int256)
- Intermediate widening rules
- Outward rounding for interval ops
- Overflow policy: **reject**

---

## 3. Coh Module Interface: Required Functions

A Coh implementation must provide **exactly** these callable units (language-neutral interface):

### 3.1 Canonical encoders/decoders

| # | Function | Description |
|---|----------|-------------|
| 1 | `encode_receipt_micro(receipt) -> bytes` | Encode micro receipt |
| 2 | `decode_receipt_micro(bytes) -> receipt` | Decode micro receipt |
| 3 | `encode_receipt_slab(receipt) -> bytes` | Encode slab receipt |
| 4 | `decode_receipt_slab(bytes) -> receipt` | Decode slab receipt |
| 5 | `hash_bytes(bytes) -> digest` | SHA-256 with domain separation |
| 6 | `jcs_canonicalize(json) -> bytes` | Canonical JSON (if using JSON) |

### 3.2 State hashing (boundary only)

| # | Function | Description |
|---|----------|-------------|
| 7 | `state_hash(state_boundary_view) -> digest` | Hash of state boundary |

**Constraint:** verifiers MUST be able to validate the hash relation using only receipt bytes + prior digest. Verifiers should not need full internal state to check RV; only the boundary hash.

### 3.3 Violation evaluation (optional, depends on module class)

| # | Function | Description |
|---|----------|-------------|
| 8a | `eval_V(state) -> QFixed` | If verifier computes V |
| **OR** | | |
| 8b | `verify_V_bounds(receipt) -> ACCEPT/REJECT` | If V is receipt-reported interval |

### 3.4 Core verifier predicate (mandatory)

| # | Function | Description |
|---|----------|-------------|
| 9 | `RV(prev_state_hash, receipt, next_state_hash, prev_chain_digest) -> Decision` | Core verifier |

Decision is:
- `ACCEPT` or
- `REJECT(code)`

Codes are an enumerated set frozen per module, but must include Coh-required codes (§5).

### 3.5 Slab compressor/expander (mandatory)

| # | Function | Description |
|---|----------|-------------|
| 10 | `build_slab(micro_receipts[]) -> slab_receipt` | Build slab |
| 11 | `verify_slab(slab_receipt) -> Decision` | Verify slab |
| 12 | `open_challenge(slab_receipt, index) -> (micro_receipt, merkle_path)` | Challenge opening (optional) |

---

## 4. Receipt Contracts (Schemas)

Coh defines two receipt layers:
- **Micro receipts**: one step
- **Slab receipts**: aggregation/compression over a range

### 4.1 Micro receipt: `coh.receipt.micro.v1` (required fields)

#### Identity
| Field | Description |
|-------|-------------|
| `schema_id`, `version` | Schema identification |
| `object_id` | Object identifier |
| `canon_profile_hash` | Canon profile reference |
| `policy_hash` | Policy reference |
| `step_type` | Module-defined enum |
| `step_index` | Nonnegative integer |

#### Chain binding
| Field | Description |
|-------|-------------|
| `chain_digest_prev` | Previous chain digest |
| `chain_digest_next` | Must equal hash update rule |
| `state_hash_prev` | Previous state hash |
| `state_hash_next` | Next state hash |

#### Boundary metrics
| Field | Description |
|-------|-------------|
| `metrics` | Module's risk variables as QFixed or interval strings |
| | Governance/accounting variables (e.g., budgets) |

#### Signatures (optional)
| Field | Description |
|-------|-------------|
| `signatures` | Ed25519 or multisig proofs |

### 4.2 Slab receipt: `coh.receipt.slab.v1` (required fields)

| Field | Description |
|-------|-------------|
| `schema_id`, `version` | Schema identification |
| `object_id` | Object identifier |
| `canon_profile_hash`, `policy_hash` | References |
| `range: {start, end}` | Range with `start < end` |
| `merkle_root` | Committing to micro receipts |
| `chain_digest_prev`, `chain_digest_next` | Chain binding |
| `summary` | Aggregate invariants |
| `signatures` | Optional |

---

## 5. Verifier Decision Codes (Coh-Required Set)

Every module's `RV` MUST support these reject codes at minimum:

| Code | Description |
|------|-------------|
| `REJECT_SCHEMA` | Invalid schema |
| `REJECT_CANON_PROFILE` | Invalid canon profile |
| `REJECT_CHAIN_DIGEST` | Invalid chain digest |
| `REJECT_STATE_HASH_LINK` | Invalid state hash link |
| `REJECT_NUMERIC_PARSE` | Numeric parse failure |
| `REJECT_INTERVAL_INVALID` | Invalid interval |
| `REJECT_OVERFLOW` | Arithmetic overflow |
| `REJECT_POLICY_VIOLATION` | Policy violation |
| `REJECT_SLAB_MERKLE` | Merkle verification failure |
| `REJECT_SLAB_SUMMARY` | Summary mismatch |

Modules may add domain-specific codes, but these must exist.

---

## 6. Determinism Laws (Must Hold)

A Coh module is invalid if any of the following fail.

### 6.1 Deterministic parsing
Same receipt bytes must decode to the same values.

### 6.2 Deterministic RV
Given the same `prev_state_hash`, `receipt`, `next_state_hash`, `prev_chain_digest`, `RV` must return the same decision on all platforms.

### 6.3 No hidden inputs
`RV` must not read:
- Wall clock time
- RNG
- Local filesystem
- Network state
- CPU floating point flags
- Environment variables

Only receipt bytes and explicit canonical constants are permitted.

---

## 7. Minimal Coh Test Vectors (Mandatory)

Every module must publish a `tests/vectors/` set with canonical receipts and expected outcomes.

### 7.1 Vector format

Each vector includes:
- `prev_chain_digest`
- `receipt_bytes` (hex or base64 of canonical bytes)
- `expected_chain_digest_next`
- `expected_decision` (`ACCEPT` or `REJECT(code)`)

### 7.2 Required vectors (minimum)

| Vector | Description |
|--------|-------------|
| `vector_001_accept_minimal_step` | Valid minimal step |
| `vector_002_reject_bad_schema` | Invalid schema rejection |
| `vector_002_reject_bad_schema` | Invalid chain digest rejection |
| `vector_004_reject_interval_invalid` | Invalid interval rejection |
| `vector_005_reject_overflow` | Overflow rejection |
| `vector_006_slab_accept_valid_merkle` | Valid slab acceptance |
| `vector_007_slab_reject_wrong_summary` | Wrong summary rejection |

These vectors are non-negotiable: they define consensus behavior.

---

## 8. CK-0 Compatibility Extension (Optional but Standard)

If the module is CK-0 subclassed, it must additionally provide:

| Field | Description |
|-------|-------------|
| `residual_schema` | Names/types of residual components |
| `weight_dictionary` hash | Weight dictionary hash |
| Scalarization | \(V(x)=\sum_i w_i r_i(x)^2\) |

Receipts must include:
- Residual norm bounds
- Budget law fields if amplification is budgeted

---

## 9. PhaseLoom Compatibility Extension (Optional)

If the module uses PhaseLoom (geometric memory), it must define:

### Extended state boundary metrics
| Variable | Description |
|----------|-------------|
| \(V\) | Base risk |
| \(C\) | Curvature, clamped at 0 |
| \(T\) | Tension |
| \(B\) | Budget |
| \(A\) | Authority injected |

### RV checks required
- Clamped recurrence updates: \(C_{n+1}=\max(\rho C_n + \Delta,0)\)
- Interlock rules at low budget
- Monotone descent bounds under repair-only regimes

---

## 10. Acceptance Checklist (Mechanical)

A Coh module is "canon-admissible" iff:

1. All required functions exist (§3).
2. Receipts validate under frozen schema (§4).
3. RV is deterministic and total (§6).
4. All required test vectors pass (§7).
5. Canon profile is pinned and hashed (§2).
6. Slab receipts verify and challenge-openings work (§4.2, §3.5).

---

## 11. End State

This contract turns Coh from a mathematical abstraction into a **repeatable engineering standard**.

Any future system—Coh-NSE, Coh-GR, Noetica runtime, robotics controllers, economic engines—must satisfy this interface to be recognized as a Coh object and participate in the same validator/compression/governance pipeline.

---

**End of Coh Module Interface Contract v1.0.0**
