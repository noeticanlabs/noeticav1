# NK-3 Conformance Tests v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md)

---

## Overview

This document defines the conformance test requirements for NK-3 v1.0. All tests must be deterministic and produce verifiable results.

---

## 1. Test Categories

### 1.1 Test Types

| Category | Description |
|----------|-------------|
| Determinism golden vectors | Verify same input → same output |
| Negative tests | Verify rejection of invalid inputs |
| End-to-end replay | Verify NK-3 → NK-2 execution |

---

## 2. Determinism Golden Vectors

### 2.1 Test Corpus

Minimum required programs:

| # | Program | Purpose |
|---|---------|---------|
| 1 | Straight-line disjoint ops | No hazards |
| 2 | WAW hazard | Two writes to same field |
| 3 | WAR hazard | Write then later read |
| 4 | IF with join | Conditional + join insertion |
| 5 | Param-decidable footprint | Dynamic footprint kernel |

### 2.2 Golden Vector Contents

For each test program, ship:

| Artifact | Description |
|----------|-------------|
| `program_nsc_bytes` | Input NSC program |
| `program_nsc_digest` | Expected digest |
| `OpSet.bytes` | Emitted OpSet |
| `OpSet.digest` | Expected digest |
| `DAG.bytes` | Emitted DAG |
| `DAG.digest` | Expected digest |
| `ExecPlan.bytes` | Emitted ExecPlan |
| `ExecPlan.digest` | Expected digest |
| `ModuleReceipt.bytes` | Emitted receipt |
| `ModuleReceipt.digest` | Expected digest |

### 2.3 Test Format

```python
# Example golden vector
GOLDEN_VECTORS = {
    "disjoint_ops": {
        "input": {
            "program_nsc_bytes": b"...",
            "program_nsc_digest": "sha256:...",
            "policy_digest": "sha256:...",
            "kernel_registry_digest": "sha256:...",
        },
        "expected": {
            "opset_digest": "sha256:...",
            "dag_digest": "sha256:...",
            "execplan_digest": "sha256:...",
            "module_receipt_digest": "sha256:...",
        }
    },
    # ... more vectors
}
```

---

## 3. Negative Tests

### 3.1 Required Negative Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| Unknown kernel | kernel_id not in registry | Reject |
| Kernel hash mismatch | kernel_hash != registry | Reject |
| Footprint fn not allowlisted | footprint_fn_hash not in allowlist | Reject |
| Disallowed edge kind | DAG contains RAW or safety edge | Reject |
| ExecPlan mode conflict | requires_modeD conflicts with mode | Reject |
| Schema digest mismatch | Schema digest doesn't match | Reject (if bound) |

### 3.2 Rejection Test Format

```python
NEGATIVE_TESTS = [
    {
        "name": "unknown_kernel",
        "input": {
            "program_nsc_bytes": b"...",
            "policy_digest": "sha256:...",
            "kernel_registry_digest": "sha256:...",
            "nsc_uses_kernel": "unknown.kernel.v1",
        },
        "expected_error": "UNKNOWN_KERNEL",
    },
    # ... more tests
]
```

---

## 4. End-to-End Replay Tests

### 4.1 Replay Stability

Lower NK-3 → execute NK-2 under different thread counts:

| Property | Must Hold |
|----------|-----------|
| Final state hash | Same across all thread counts |
| Receipt chain | Verifies under NK-1/NK-2 |
| Module digest | Same module_receipt_digest |

### 4.2 Test Configuration

```python
REPLAY_TESTS = [
    {
        "name": "replay_stability",
        "program": "program_nsc_bytes",
        "thread_counts": [1, 2, 4, 8],
        "verify": {
            "final_state_hash_equality": True,
            "receipt_chain_verifies": True,
            "module_digest_unchanged": True,
        }
    },
    # ... more tests
]
```

---

## 5. Verification Checklist

### 5.1 Static Verification

For each artifact:

| Check | OpSet | DAG | ExecPlan | ModuleReceipt |
|-------|-------|-----|----------|---------------|
| Schema valid | ✅ | ✅ | ✅ | ✅ |
| Digest matches | ✅ | ✅ | ✅ | ✅ |
| Sorted arrays | ✅ | ✅ | ✅ | ✅ |
| Deduped sets | ✅ | ✅ | - | - |
| Hash format | ✅ | ✅ | ✅ | ✅ |
| Unknown fields | reject | reject | reject | reject |

### 5.2 Cross-Artifact Verification

| Check | Description |
|-------|-------------|
| OpSet DAG match | All DAG nodes in OpSet |
| ExecPlan refs | opset_digest, dag_digest match |
| Receipt binds | All digests match |

---

## 6. Test Execution

### 6.1 Running Tests

```bash
# Run all NK-3 tests
pytest tests/nk3/ -v

# Run specific test category
pytest tests/nk3/test_golden_vectors.py -v
pytest tests/nk3/test_negative.py -v
pytest tests/nk3/test_replay.py -v
```

### 6.2 Expected Output

```
tests/nk3/
├── test_golden_vectors.py
│   ├── test_disjoint_ops
│   ├── test_waw_hazard
│   ├── test_war_hazard
│   ├── test_if_join
│   └── test_param_footprint
├── test_negative.py
│   ├── test_unknown_kernel
│   ├── test_hash_mismatch
│   ├── test_fn_not_allowlisted
│   ├── test_disallowed_edge
│   ├── test_mode_conflict
│   └── test_schema_mismatch
└── test_replay.py
    ├── test_replay_stability_1_thread
    ├── test_replay_stability_2_threads
    ├── test_replay_stability_4_threads
    └── test_replay_stability_8_threads
```

---

## 7. Success Criteria

### 7.1 Golden Vector Success

All golden vectors must:
- Produce identical output bytes
- Match expected digests exactly
- Complete within timeout

### 7.2 Negative Test Success

All negative tests must:
- Reject with correct error code
- Provide meaningful error message
- Not crash or hang

### 7.3 Replay Test Success

All replay tests must:
- Final state hash identical across thread counts
- Receipt chain verifies under NK-1/NK-2
- Module receipt digest unchanged

---

## 8. Test Vectors (Reference)

### 8.1 Disjoint Ops (Minimal)

```nsc
// NSC: Two operations, no overlap
SEQ(
  a = add(field.x, field.y),
  b = mul(field.z, field.w)
)
```

Expected: No hazard edges, parallel execution possible.

### 8.2 WAW Hazard

```nsc
// NSC: Two writes to same field
SEQ(
  a = set(field.result, 1),
  b = set(field.result, 2)
)
```

Expected: WAW edge from a → b.

### 8.3 WAR Hazard

```nsc
// NSC: Write then read
SEQ(
  a = set(field.temp, 10),
  b = add(field.temp, field.x)
)
```

Expected: WAR edge from a → b.

### 8.4 IF with Join

```nsc
// NSC: Conditional with join
IF(field.cond,
  set(field.result, 1),
  set(field.result, 2)
)
```

Expected: Join node inserted, control edges from both branches to join.

### 8.5 Param-Decidable Footprint

```nsc
// NSC: Dynamic footprint operation
slice(field.input, field.start, field.end)
```

Expected: Footprint computed via allowlisted function.
