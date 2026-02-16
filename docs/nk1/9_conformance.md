# NK-1 Conformance Suite

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`2_debtunit.md`](2_debtunit.md), [`3_contracts.md`](3_contracts.md), [`4_measured_gate.md`](4_measured_gate.md), [`5_curvature.md`](5_curvature.md), [`8_verifier.md`](8_verifier.md)

---

## Overview

The NK-1 Conformance Suite provides **golden vectors** for verifying that implementations produce deterministic, byte-for-byte identical results. This is the **hostile review defense** - any deviation from canonical behavior is detected.

---

## Test Categories

### 1. DebtUnit Arithmetic

| Test | Description |
|------|-------------|
| `debtunit_from_int` | Integer construction |
| `debtunit_from_rational` | Rational construction with reduction |
| `debtunit_from_decimal` | Decimal string parsing |
| `debtunit_add` | Addition |
| `debtunit_sub` | Subtraction |
| `debtunit_mul_int` | Multiplication by integer |
| `debtunit_div_int` | Division by integer |
| `debtunit_compare` | Comparison operations |
| `debtunit_min_max` | min/max operations |
| `debtunit_negation` | Unary negation |
| `debtunit_abs` | Absolute value |

#### Rounding Edge Cases

```python
# Half-even rounding tests
TEST_CASES = [
    # (input_rational, expected_int_value)
    # 0.5 rounds to 0 (even)
    ((1, 2), 0),
    # 1.5 rounds to 2 (even)
    ((3, 2), 2),
    # 2.5 rounds to 2 (even)
    ((5, 2), 2),
    # 3.5 rounds to 4 (even)
    ((7, 2), 4),
]
```

#### Golden Vector Example

```json
{
  "test_name": "debtunit_from_rational_half_even",
  "input": {
    "p": 3,
    "q": 2
  },
  "expected": {
    "int_value": 2,
    "canonical": "q:6:2",
    "decimal": "0.000002"
  }
}
```

---

### 2. V(x) Determinism

| Test | Description |
|------|-------------|
| `vx_contract_ordering` | Contract ordering must not affect result |
| `vx_weight_reduction` | Same fraction via different representations |
| `vx_sigma_computation` | Sigma computation determinism |
| `vx_applicability` | Applicability predicate handling |
| `vx_empty_contract_set` | Empty contract set returns 0 |

#### Contract Ordering Test

```json
{
  "test_name": "vx_contract_ordering",
  "description": "Reordering contracts must not change V(x)",
  "contract_set_1": [
    {"contract_id": "A", "weight": "p_q:1_1", "residual": [100000]},
    {"contract_id": "B", "weight": "p_q:1_1", "residual": [200000]}
  ],
  "contract_set_2": [
    {"contract_id": "B", "weight": "p_q:1_1", "residual": [200000]},
    {"contract_id": "A", "weight": "p_q:1_1", "residual": [100000]}
  ],
  "expected_v": "q:6:500000",  // Same for both
  "must_be_equal": true
}
```

#### Weight Reduction Test

```json
{
  "test_name": "vx_weight_reduction",
  "description": "Different representations of same weight must produce identical results",
  "weight_1": "p_q:1_2",        // 0.5
  "weight_2": "p_q:2_4",        // 0.5
  "weight_3": "p_q:50_100",    // 0.5
  "expected": "q:6:500000",
  "all_equal": true
}
```

---

### 3. Gate Accept/Reject

| Test | Description |
|------|-------------|
| `gate_accept_at_boundary` | Accept when inequality holds at boundary |
| `gate_accept_under_budget` | Accept when well under budget |
| `gate_reject_by_1_tick` | Reject when violated by 1 DebtUnit |
| `gate_reject_invariant_failure` | Reject on invariant failure |
| `gate_reject_policy_mismatch` | Reject on policy mismatch |
| `gate_zero_budget` | Zero budget preserves debt |
| `gate_zero_disturbance` | Zero disturbance |

#### Boundary Tests

```json
{
  "test_name": "gate_accept_at_boundary",
  "description": "Accept when D_post equals D_pre - S(D_pre, B) + E",
  "input": {
    "debt_pre": "q:6:1000000",
    "budget": "q:6:500000",
    "mu": "1.0",
    "disturbance": "q:6:0"
  },
  "expected": {
    "service": "q:6:500000",
    "allowed_max": "q:6:500000",
    "decision": "accept"
  }
}
```

```json
{
  "test_name": "gate_reject_by_1_tick",
  "description": "Reject when debt exceeds allowed by 1 DebtUnit",
  "input": {
    "debt_pre": "q:6:1000000",
    "debt_post": "q:6:500001",
    "budget": "q:6:500000",
    "mu": "1.0",
    "disturbance": "q:6:0"
  },
  "expected": {
    "service": "q:6:500000",
    "allowed_max": "q:6:500000",
    "decision": "reject"
  }
}
```

---

### 4. M-entry + Matrix

| Test | Description |
|------|-------------|
| `mentry_parse` | Parse rational_scaled.v1 |
| `mentry_reduce` | Fraction reduction |
| `mentry_reject_negative` | Reject negative entries |
| `matrix_symmetry` | Symmetry enforcement |
| `matrix_block_indices` | Block-only index domain |
| `registry_allowlist` | Unknown matrix_id rejection |
| `matrix_sparse` | Sparse matrix handling |

#### M-entry Parse Test

```json
{
  "test_name": "mentry_parse",
  "input": {
    "num": 3,
    "den": 4
  },
  "expected": {
    "num_reduced": 3,
    "den_reduced": 4,
    "debtunit": "q:6:750000"
  }
}
```

```json
{
  "test_name": "mentry_reduce",
  "description": "Ensure reduction to lowest terms",
  "input": {
    "num": 50,
    "den": 100
  },
  "expected": {
    "num_reduced": 1,
    "den_reduced": 2
  }
}
```

```json
{
  "test_name": "mentry_reject_negative",
  "description": "Negative entries must be rejected",
  "input": {
    "num": -1,
    "den": 2
  },
  "expected_error": "negative_not_allowed"
}
```

#### Matrix Symmetry Test

```json
{
  "test_name": "matrix_symmetry",
  "description": "Asymmetric matrices must be rejected",
  "input": {
    "matrix_id": "test_asymmetric",
    "entries": [
      {"row": 0, "col": 1, "value": "q:6:500000"},
      {"row": 1, "col": 0, "value": "q:6:400000"}
    ]
  },
  "expected_error": "asymmetric_values"
}
```

---

### 5. Replay Verification

| Test | Description |
|------|-------------|
| `replay_10k_steps` | 10,000-step chain reproduces identical hashes |
| `replay_hash_continuity` | Hash chain continuity |
| `replay_action_schema` | Action validation |
| `replay_law_check` | Law inequality verification |
| `replay_service_compute` | Service computation |

#### Long Chain Test

```json
{
  "test_name": "replay_10k_steps",
  "description": "10,000-step chain must reproduce identical receipt hashes",
  "step_count": 10000,
  "expected": {
    "all_hashes_match": true,
    "final_hash": "abc123...",
    "chain_valid": true
  }
}
```

---

## Test Runner

```python
class ConformanceTestRunner:
    """Runs conformance tests and reports results."""
    
    def run_all(self) -> TestReport:
        """Run all conformance tests."""
        results = []
        
        # Run each test category
        for category in TEST_CATEGORIES:
            for test in category.tests:
                result = self.run_test(test)
                results.append(result)
        
        return TestReport(results)
    
    def run_test(self, test: TestCase) -> TestResult:
        """Run a single test case."""
        try:
            # Execute test
            actual = test.execute()
            
            # Compare to expected
            if test.is_valid(actual):
                return TestResult(test=test.name, passed=True)
            else:
                return TestResult(
                    test=test.name,
                    passed=False,
                    expected=test.expected,
                    actual=actual
                )
        except Exception as e:
            return TestResult(
                test=test.name,
                passed=False,
                error=str(e)
            )
```

---

## Golden Vector Storage

```
nk1/
  conformance/
    vectors/
      debtunit/
        from_int.json
        from_rational.json
        add.json
        ...
      vx/
        contract_ordering.json
        weight_reduction.json
        ...
      gate/
        accept_at_boundary.json
        reject_by_1_tick.json
        ...
      matrix/
        symmetry.json
        allowlist.json
        ...
      replay/
        10k_steps.json
        hash_continuity.json
        ...
```

---

## Test Execution

```bash
# Run all tests
python -m nk1.conformance.run_all

# Run specific category
python -m nk1.conformance.run_debtunit
python -m nk1.conformance.run_vx
python -m nk1.conformance.run_gate
python -m nk1.conformance.run_matrix
python -m nk1.conformance.run_replay

# Run single test
python -m nk1.conformance.run_test debtunit_from_rational_half_even
```

---

## Acceptance Criteria

All tests MUST pass for NK-1 v1.0 to be considered complete:

| Category | Required Pass Rate |
|----------|------------------|
| DebtUnit Arithmetic | 100% |
| V(x) Determinism | 100% |
| Gate Accept/Reject | 100% |
| M-entry + Matrix | 100% |
| Replay Verification | 100% |

---

## Continuous Verification

The conformance suite should be run:

1. **On every commit** - automated CI
2. **Before release** - manual verification
3. **On verifier update** - regression testing

---

*See also: [`../ck0/10_conformance_tests.md`](../ck0/10_conformance_tests.md)*
