# NEC v1.0 + NK-1 + NK-2 + NK-3 Compliance Implementation Plan

**Version:** 1.0  
**Scope:** NEC v1.0, NK-1 Runtime Core v1.0, NK-2 Scheduler v1.0, NK-3 Lowering v1.0  
**Goal:** Deterministic replay + GLB + receipt-verifiable gating + chain-stable policy universe

---

## Executive Summary

This plan implements the compliance checklist for Noetica v1.0, covering:
- NK-1 State Engine (§1.1-1.8)
- NK-1 Receipt Engine (§1.3-1.4)
- NK-1 δ-Norm Enforcement (§1.5)
- NK-1 Measured Gate (§1.6)
- NK-1 Curvature Matrix Registry (§1.7)
- NK-1 Policy Registry (§1.8)
- NK-2 Scheduler Compliance
- NK-2 Resource Caps
- NK-3 Lowering Compliance
- GLB Enforcement
- Golden Vectors Generation
- Cross-Platform Verification

---

## Phase 1: NK-1 State Engine Compliance (§1.1-1.3)

### 1.1 State Structure

#### 1.1.1 Implement State with schema_id, fields, meta separation
**Current Status:** PARTIAL - State exists but meta handling incomplete
**Required Actions:**
- Add `schema_id` field to State dataclass
- Add `meta` field excluded from canonical bytes
- Ensure field identity uses FieldID (not names)
- Add unit tests verifying meta exclusion from hash

#### 1.1.2 Add canonical serialization (sorted_json_bytes.v1)
**Current Status:** PARTIAL - Basic serialization exists
**Required Actions:**
- Implement root layout: `{"canon_id":"sorted_json_bytes.v1","schema_id":"...","float_policy":"...","fields":[["<FieldID>",<ValueCanon>],...]}`
- Use array of pairs for fields (not JSON object)
- Sort fields lexicographically by FieldID byte encoding

#### 1.1.3 Implement ValueCanon tagging (i:, q:, b64:, s:)
**Required Actions:**
- Create ValueCanon encoder with tags:
  - `i:<decimal>` for integers
  - `q:<scale>:<int>` for fixed-point
  - `b64:<base64url_no_padding>` for bytes
  - `s:<NFC>` for strings
- Add type confusion tests

### 1.2 Canonical Serialization Details

#### 1.2.1 Create sorted fields array with FieldID ordering
**Required Actions:**
- Implement `sorted_json_bytes.v1` format
- Ensure fields is array of pairs sorted by FieldID bytes

#### 1.2.2 Implement UTF-8, NFC normalization, no whitespace
**Required Actions:**
- Add Unicode NFC normalization for strings
- Use compact JSON (no whitespace)
- Ensure consistent numeric formatting

### 1.3 ValueCanon Implementation

#### 1.3.1 Add type-tagged atoms for all scalar values
**Required Actions:**
- Implement all ValueCanon tags
- Add type confusion tests: `i:1` ≠ `s:1` ≠ `q:0:1`

#### 1.3.2 Implement maps as sorted [key,value] arrays
**Required Actions:**
- Replace dict with sorted arrays for maps
- Add Unicode normalization tests

---

## Phase 2: NK-1 Receipt Engine Compliance (§1.3-1.4)

### 2.1 Receipt Canonicalization

#### 2.1.1 Implement canon_receipt_bytes.v1 format
**Current Status:** PARTIAL - StepReceipt exists
**Required Actions:**
- Implement format: `["canon_receipt_bytes.v1","<receipt_type>",[["key1",ValueCanon],...]]`
- Support `op.local.v1` and `op.commit.v1`

#### 2.1.2 Add unknown key rejection in strict mode
**Required Actions:**
- Add strict mode validation
- Reject unknown keys in v1.0 strict mode

### 2.2 Merkle Rules

#### 2.2.1 Implement Merkle tree (leaf=32bytes, node=SHA256)
**Required Actions:**
- Implement leaf = raw 32 bytes from decoded hash
- Implement node = SHA256(L||R)

#### 2.2.2 Handle odd nodes with duplication
**Required Actions:**
- Implement odd node duplication rule
- Root encoded as `h:<hex>`

---

## Phase 3: NK-1 δ-Norm Enforcement (§1.5)

### 3.1 Norm Domain Restriction

#### 3.1.1 Implement NORM_DOMAIN_MODE = numeric_only.v1
**Required Actions:**
- Add config for `NORM_DOMAIN_MODE`
- Filter only numeric fields

#### 3.1.2 Filter non-numeric fields from δ-norm
**Required Actions:**
- Check `participates_in_delta_norm=true` flag
- Ensure non-numeric writes don't contribute

### 3.2 Weight Rational Normalization

#### 3.2.1 Implement weight rational normalization (gcd)
**Required Actions:**
- Reduce weights: `gcd(p,q)=1`
- Add unit tests

#### 3.2.2 Add lcm rule for denominator normalization
**Required Actions:**
- Implement `Q = lcm(q_k)` rule
- Handle empty set: D=1, N=0

### 3.3 Non-numeric Write Policy

#### 3.3.1 Implement non-numeric write policy (requires_modeD)
**Required Actions:**
- Flag ops with `requires_modeD=true` for non-numeric writes
- Force Mode D for batches with non-numeric writes

---

## Phase 4: NK-1 Measured Gate (§1.6)

### 4.1 V_DU Definition

#### 4.1.1 Implement V_DU with DebtUnit integer output
**Current Status:** PARTIAL - MeasuredGate exists
**Required Actions:**
- Output in DebtUnit integer quanta
- No floats in V_DU evaluation

#### 4.1.2 Add StateCtx-only evaluation (GLB enforced)
**Required Actions:**
- V can only read StateCtx
- No ledger, time, randomness, IO, meta

### 4.2 ε_B Exact Definition

#### 4.2.1 Implement ε_B computation with patch rule
**Required Actions:**
- Compute `x_o = f_o(x)` on same pre-state
- Use `tilde{x}_o = patch(x, W_o, Δ_o)` (not raw kernel output)

#### 4.2.2 Use W_o outputs only for isolated delta states
**Required Actions:**
- Ignore kernel outputs outside W_o via patch rule

### 4.3 ε̂(B) Certificate Computation

#### 4.3.1 Implement ε̂ certificate with half-even rounding
**Required Actions:**
- One rounding only, half-even
- Output in DebtUnit integer quanta

#### 4.3.2 Bind M_ENTRY_MODE to matrix digest
**Required Actions:**
- Matrix digest must match for verifier acceptance

---

## Phase 5: NK-1 Curvature Matrix Registry (§1.7)

### 5.1 Representation and Parsing

#### 5.1.1 Store entries for i≤j only with symmetry fill
**Required Actions:**
- Only store upper triangle
- Add symmetry fill for i>j

#### 5.1.2 Implement missing entry default 0
**Required Actions:**
- Return 0 for missing entries

#### 5.1.3 Add reduced rationals enforcement
**Required Actions:**
- Enforce reduced form for all rationals

---

## Phase 6: NK-1 Policy Registry (§1.8)

### 6.1 PolicyBundle

#### 6.1.1 Implement PolicyBundle with all required mode IDs
**Current Status:** PARTIAL - PolicyBundle exists
**Required Actions:**
- Include all mode IDs required by NK-1/NK-2

#### 6.1.2 Add canonical bytes with sorted keys, tagged atoms
**Required Actions:**
- Sorted keys, tagged atoms, no whitespace

#### 6.1.3 Implement policy_digest chain locking
**Required Actions:**
- `policy_digest = SHA256(policy_bytes)`
- Reject mid-chain drift in v1.0

---

## Phase 7: NK-2 Scheduler Compliance

### 7.1 Ready Set + Deterministic Ordering

#### 7.1.1 Implement deterministic ready set ordering by op_id bytes
**Current Status:** PARTIAL - Scheduler exists
**Required Actions:**
- Order by op_id bytes for tie-breaking

#### 7.1.2 Maintain append_log throughout batch construction
**Required Actions:**
- AppendLog already exists, verify correctness

### 7.2 Failure Classes + Priority

#### 7.2.1 Implement failure priority
**Required Actions:**
- Priority: independence > policy_veto > kernel_error > delta_bound > gate_eps

### 7.3 Split Law and Termination

#### 7.3.1 Implement split law with lexmin(op_id)
**Required Actions:**
- Split by lexmin(op_id)
- Failed wide batch never reattempted

#### 7.3.2 Add termination for singleton kernel_error/delta_bound/policy_veto
**Required Actions:**
- Singleton failure halts execution

---

## Phase 8: NK-2 Resource Caps (§3.7)

### 8.1 Cap Event Semantics

#### 8.1.1 Implement cap event deterministic halt
**Required Actions:**
- Immediate deterministic halt on cap event

#### 8.1.2 Add matrix_terms cap threshold
**Required Actions:**
- Batch size threshold triggers cap

#### 8.1.3 Implement BigInt bitlen cap
**Required Actions:**
- Deterministic error on cap crossing

---

## Phase 9: NK-3 Lowering Compliance

### 9.1 Purity Axiom

#### 9.1.1 Verify purity axiom in lowering output
**Current Status:** PARTIAL - Canon inputs exist
**Required Actions:**
- Output depends only on: NSC.v1 bytes, toolchain IDs, policy_digest, kernel_registry_digest

#### 9.1.2 Add toolchain IDs to canonical output
**Required Actions:**
- Include toolchain IDs in canonical form

### 9.2 Hazards and Control Edges

#### 9.2.1 Implement hazard control edges (WAR/WAW/control.explicit)
**Required Actions:**
- Only allowed edge kinds exist

#### 9.2.2 Add join nodes for explicit control constructs
**Required Actions:**
- Join nodes have empty R/W
- Non-eliminable

### 9.3 Kernel Registry Enforcement

#### 9.3.1 Implement kernel_registry_digest binding
**Required Actions:**
- Each OpSpec carries kernel_id + kernel_hash
- Verify against KernelRegistry

---

## Phase 10: GLB Enforcement

### 10.1 Compile-Time Prohibition

#### 10.1.1 Add compile-time capability erasure verification
**Required Actions:**
- Kernel/V can only call StateCtx read

### 10.2 Runtime Trap Backstop

#### 10.2.1 Implement runtime trap for forbidden capabilities
**Required Actions:**
- Deterministic trap with error code

### 10.3 Verifier Requirement

#### 10.3.1 Bind kernel_hash/v_function_hash to receipts
**Required Actions:**
- Receipts bind hashes
- Verifier accepts only allowlisted hashes

---

## Phase 11: Golden Vectors

### 11.1 Minimum Set Requirements

#### 11.1.1 Generate ≥20 state canon bytes + hashes
**Required Actions:**
- Create golden state_canon.json with ≥20 examples
- Include various field types

#### 11.1.2 Generate ≥20 receipt canon bytes + hashes
**Required Actions:**
- Create golden receipt_canon.json with ≥20 examples

#### 11.1.3 Generate ≥10 Merkle root vectors
**Required Actions:**
- Create merkle_golden.json with ≥10 examples

#### 11.1.4 Generate ≥10 δ-norm enforcement vectors
**Required Actions:**
- Create delta_norm_golden.json with ≥10 examples

#### 11.1.5 Generate ≥10 ε_B/ε̂ vectors
**Required Actions:**
- Expand eps_measured_golden.json (≥10)
- Expand eps_hat_golden.json (≥10)

#### 11.1.6 Generate ≥5 PolicyBundle bytes + digest
**Required Actions:**
- Expand policy_golden.json (≥5)

#### 11.1.7 Generate ≥5 KernelRegistry bytes + digest
**Required Actions:**
- Create kernel_registry_golden.json with ≥5 examples

#### 11.1.8 Generate ≥5 Matrix bytes + digest
**Required Actions:**
- Expand matrix_canon.json (≥5)

---

## Phase 12: Cross-Platform Verification

### 12.1 Platform Requirements

#### 12.1.1 Add Linux/Windows test cases
**Required Actions:**
- Verify byte-for-byte match on Linux
- Add Windows compatibility tests

#### 12.1.2 Add x86_64/ARM64 test cases
**Required Actions:**
- Verify on x86_64
- Add ARM64 compatibility tests where possible

#### 12.1.3 Verify single-thread vs multi-thread determinism
**Required Actions:**
- Test with 1 thread
- Test with N threads
- Verify identical results

---

## File Structure

### New Files to Create

```
conformance/
├── kernel_registry_golden.json    # NEW: ≥5 kernel registry examples
├── delta_norm_golden.json         # NEW: ≥10 δ-norm examples
├── merkle_golden.json             # NEW: ≥10 Merkle root examples
├── state_canon.json               # UPDATE: ≥20 examples
├── receipt_canon.json             # UPDATE: ≥20 examples
├── eps_measured_golden.json       # UPDATE: ≥10 examples
├── eps_hat_golden.json            # UPDATE: ≥10 examples
├── policy_golden.json             # UPDATE: ≥5 examples
└── matrix_canon.json              # UPDATE: ≥5 examples

src/
├── nk1/
│   ├── state_canon.py             # NEW: sorted_json_bytes.v1 implementation
│   ├── value_canon.py             # NEW: ValueCanon tagging
│   ├── delta_norm.py              # NEW: δ-norm enforcement
│   ├── curvature_matrix.py       # UPDATE: Matrix registry
│   └── measured_gate.py          # UPDATE: Full ε_B/ε̂ computation
├── nk2/
│   ├── scheduler.py              # UPDATE: Failure priority, split law
│   └── resource_caps.py           # NEW: Cap event handling
├── nk3/
│   ├── lowering.py               # NEW: Full lowering implementation
│   └── hazard_control.py         # NEW: Edge enforcement
└── glb/
    ├── compile_check.py           # NEW: Compile-time verification
    └── runtime_trap.py            # NEW: Runtime trap handling
```

### Documentation Files to Create

```
docs/compliance/
├── NEC_NK123_Compliance_Checklist_v1_0.md
├── state_canonization_spec.md
├── receipt_canonicalization_spec.md
├── delta_norm_spec.md
├── measured_gate_spec.md
└── glb_enforcement_spec.md
```

---

## Implementation Dependencies

```
Phase 1 (State Engine)
    │
    ├─► Phase 2 (Receipt Engine)
    │       │
    │       └─► Phase 4 (Measured Gate ε_B)
    │
    ├─► Phase 3 (δ-Norm)
    │       │
    │       └─► Phase 4 (Measured Gate ε̂)
    │
    ├─► Phase 5 (Matrix Registry)
    │       │
    │       └─► Phase 4 (Measured Gate ε̂)
    │
    ├─► Phase 6 (Policy Registry)
    │       │
    │       └─► Phase 7 (Scheduler)
    │               │
    │               └─► Phase 8 (Resource Caps)
    │
    └─► Phase 9 (NK-3 Lowering)
            │
            └─► Phase 10 (GLB Enforcement)

Phase 11 (Golden Vectors) - Runs parallel to all phases
Phase 12 (Cross-Platform) - Final verification
```

---

## Testing Strategy

### Unit Tests
- Each component has dedicated unit tests
- Test against golden vectors where applicable
- Type confusion tests for ValueCanon

### Integration Tests
- End-to-end state → receipt → verification flow
- Scheduler batch construction tests
- Gate approval/rejection tests

### Conformance Tests
- Run against all golden vectors
- Verify byte-for-byte exact match
- Cross-platform verification

---

## Acceptance Criteria

1. **Deterministic Serialization**
   - Same state → identical canon_bytes across runs
   - Same inputs → identical output across platforms

2. **Receipt Verification**
   - All receipts pass verifier
   - Policy digest chain locked

3. **Measured Gate**
   - ε_measured ≤ ε̂ for all approved batches
   - Budget law satisfied

4. **Scheduler**
   - Deterministic batch ordering
   - Failure priority correctly applied

5. **GLB Enforcement**
   - No forbidden capability access at runtime
   - Traps are deterministic

6. **Golden Vectors**
   - All ≥N examples present
   - Hashes match golden values

---

## Notes

- Focus on **byte-for-byte** exact match, not just logical equivalence
- Explicit rounding rules (half-even) at every quantization point
- No attempt receipts in v1.0
- Join nodes are non-eliminable
