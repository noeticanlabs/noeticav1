# Full Integration Test Plan

## Overview
Comprehensive integration test covering ALL modules: NK-1, NK-2, NK-3, NK-4G, NEC, ASG, CK0, PhaseLoom, COH.

## Module Summary

| Module | Purpose | Key Types |
|--------|---------|-----------|
| **CK-0** | Mathematical substrate (exact arithmetic) | `DebtUnit`, `State`, `ViolationFunctional`, `CurvatureMatrix` |
| **COH** | Category of Coherent Spaces | `CohObject`, `CohMorphism`, `TimeFunctor` |
| **NK-1** | Runtime kernel (gating/policy) | `PolicyBundle`, `StateCanon`, `ReceiptCanon`, `MeasuredGate` |
| **NK-2** | Execution + scheduler | `ExecPlan`, `GreedyCurvScheduler`, `Batch` |
| **NK-3** | Lowering core | `NSCProgram`, `OpSet`, `DAG` |
| **NK-4G** | Governance certificate verification | `NK4GReceiptExtension`, `NK4GVerifier` |
| **ASG** | Spectral governance | `ASGStateLayout`, `ASGParams`, `ProxWatchdog` |
| **PhaseLoom** | Geometric memory | `PLState`, `PLParams`, `PhaseLoomFunctor` |

## Data Flow

```
NSC Input (NK-3)
    ↓
OpSet → DAG (NK-3)
    ↓
ExecPlan (NK-2)
    ↓
State + Receipts (CK-0)
    ↓
[Optional: PhaseLoom Functor → PLState]
    ↓
Coh Object (COH) - optional categorical view
    ↓
ASG Spectral Analysis (κ₀, margin)
    ↓
NK-4G Receipt Extension (certificate)
    ↓
NK-1 Policy Gates (PASS/WARN/HALT)
```

## Test Scenarios

### 1. CK-0 Core Tests
- [ ] DebtUnit arithmetic operations
- [ ] State field definitions and validation
- [ ] Invariant checking
- [ ] Violation functional V(x) computation
- [ ] Budget law S(D,B) computation
- [ ] Curvature matrix NEC closure

### 2. CK0 → COH Bridge
- [ ] Convert CK-0 State to CohObject
- [ ] Verify CK-0 receipts as valid CohMorphism
- [ ] TimeFunctor applied to CK-0 trajectory
- [ ] Natural transformation between CK-0 and COH views

### 3. NK-3 → NK-2 Pipeline
- [ ] NSCProgram → OpSet conversion
- [ ] OpSet → DAG construction with hazard edges
- [ ] DAG → ExecPlan scheduling
- [ ] Batch execution with AppendLog

### 4. NK-2 → CK-0 Integration
- [ ] ExecPlan results stored in CK-0 State
- [ ] Receipt generation from Batch results
- [ ] Failure handling produces terminal receipts

### 5. CK-0 → ASG Bridge
- [ ] Extract curvature matrix from CK-0
- [ ] Build ASGStateLayout from CK-0 state dimensions
- [ ] ASG parameters from CK-0 curvature

### 6. ASG Spectral Analysis
- [ ] Jacobian assembly for 1D ring topology
- [ ] Hessian model computation
- [ ] κ₀ estimation with policy identification
- [ ] Semantic direction computation
- [ ] Semantic margin computation
- [ ] Watchdog receipt generation

### 7. ASG → NK-4G Integration
- [ ] ASGCertificate → NK4GReceiptExtension
- [ ] NK4GVerifier checks certificate fields
- [ ] Policy threshold enforcement (κ₀, margin)

### 8. NK-4G → NK-1 Integration
- [ ] PolicyBundle gates PASS when thresholds met
- [ ] PolicyBundle gates WARN on margin violation
- [ ] PolicyBundle gates HALT on κ₀ violation

### 9. PhaseLoom Integration
- [ ] CK-0 State → PLState conversion
- [ ] PhaseLoomFunctor applied to trajectory
- [ ] PLState → CK-0 State round-trip
- [ ] PhaseLoom receipt verification

### 10. End-to-End Pipeline
- [ ] Full flow: NSC → NK-3 → NK-2 → CK-0 → ASG → NK-4G → NK-1
- [ ] Full flow with PhaseLoom
- [ ] Full flow with COH categorical verification

## Test File Structure

Create `tests/test_full_integration.py`:

```python
# Full Integration Tests
# Covers: NK-1, NK-2, NK-3, NK-4G, NEC, ASG, CK0, PhaseLoom, COH

class TestCK0Core: ...
class TestCK0ToCOHBridge: ...
class TestNK3ToNK2Pipeline: ...
class TestNK2ToCK0Integration: ...
class TestCK0ToASGBridge: ...
class TestASGSpectralAnalysis: ...
class TestASGToNK4GIntegration: ...
class TestNK4GToNK1Integration: ...
class TestPhaseLoomIntegration: ...
class TestEndToEndPipeline: ...
```

## Execution

```bash
# Run all integration tests
pytest tests/test_full_integration.py -v

# Run with coverage
pytest tests/test_full_integration.py --cov=src --cov-report=html
```

## Gap Analysis

Existing test coverage:
- ✅ `test_pipeline_integration.py` - NK-3 → NK-2 → ASG → NK-4G → NK-1
- ✅ `test_coh.py` - COH module
- ✅ `test_curvature.py` - CK-0 curvature
- ✅ `test_budget_law.py` - CK-0 budget law
- ✅ Various unit tests per module

Missing integration points to add:
1. CK-0 ↔ COH bridge tests
2. NK-2 → CK-0 receipt flow
3. PhaseLoom full integration
4. End-to-end with all options
