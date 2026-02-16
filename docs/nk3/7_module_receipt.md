# NK-3 ModuleReceipt v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`2_canon_outputs.md`](2_canon_outputs.md), [`../nk1/7_receipts.md`](../nk1/7_receipts.md)

---

## Overview

This document defines the ModuleReceipt v1 artifact. The ModuleReceipt binds the program digest with all artifact digests for verification.

---

## 1. ModuleReceipt Schema

### 1.1 Definition

```python
@dataclass(frozen=True)
class ModuleReceipt:
    """Binds program and artifact digests for verification."""
    
    # Program binding
    program_nsc_digest: Hash256
    
    # Chain bindings
    policy_digest: Hash256
    kernel_registry_digest: Hash256
    
    # Artifact bindings
    opset_digest: Hash256
    dag_digest: Hash256
    execplan_digest: Hash256
    
    # Toolchain
    parser_id: str
    typechecker_id: str
    lowerer_id: str
    
    # Configuration
    no_optimization_clause: bool
    
    # Optional schema digests (recommended hardening)
    opset_schema_digest: Hash256 | None = None
    dag_schema_digest: Hash256 | None = None
    execplan_schema_digest: Hash256 | None = None
    module_receipt_schema_digest: Hash256 | None = None
    
    # Digest
    module_receipt_digest: Hash256
    
    @staticmethod
    def create(...) -> ModuleReceipt:
        """Create ModuleReceipt with all required fields."""
        # ... implementation
```

### 1.2 Required Fields

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| `program_nsc_digest` | Hash256 | NSC program digest | Required |
| `policy_digest` | Hash256 | Policy bundle digest | Chain-locked |
| `kernel_registry_digest` | Hash256 | Kernel registry digest | Chain-locked |
| `opset_digest` | Hash256 | OpSet artifact digest | Must match OpSet |
| `dag_digest` | Hash256 | DAG artifact digest | Must match DAG |
| `execplan_digest` | Hash256 | ExecPlan artifact digest | Must match ExecPlan |
| `parser_id` | str | Parser identifier | Toolchain |
| `typechecker_id` | str | Type checker identifier | Toolchain |
| `lowerer_id` | str | Lowerer identifier | Toolchain |
| `no_optimization_clause` | bool | No optimization flag | Must be true |

### 1.3 Optional Fields

| Field | Type | Description | Recommendation |
|-------|------|-------------|----------------|
| `opset_schema_digest` | Hash256 | OpSet schema digest | Recommended |
| `dag_schema_digest` | Hash256 | DAG schema digest | Recommended |
| `execplan_schema_digest` | Hash256 | ExecPlan schema digest | Recommended |
| `module_receipt_schema_digest` | Hash256 | ModuleReceipt schema digest | Recommended |

---

## 2. Digest Binding

### 2.1 Binding Rules

ModuleReceipt must bind all digests:

```
module_receipt_digest = H_R(module_receipt_bytes)
```

Where `module_receipt_bytes` includes all bound digests.

### 2.2 Digest Verification

NK-2 and NK-1 verifiers must be able to check:
1. All artifact digests match the actual artifacts
2. Program digest matches the original NSC program
3. Policy/registry digests match chain state

---

## 3. Toolchain Identification

### 3.1 Toolchain IDs

| ID | Description | Format |
|----|-------------|--------|
| `parser_id` | Parser version | `"parser:major.minor"` |
| `typechecker_id` | Type checker version | `"typechecker:major.minor"` |
| `lower_id` | Lowerer version | `"lowerer:major.minor"` |

### 3.2 Version Locking

Toolchain IDs must be locked at lowering time and recorded in the receipt.

---

## 4. No Optimization Clause

### 4.1 Flag Value

| Field | Value | Meaning |
|-------|-------|---------|
| `no_optimization_clause` | `true` | No optimization performed during lowering |

### 4.2 Verification

Verifiers can check that `no_optimization_clause = true` to confirm no transformations beyond lowering.

---

## 5. Schema Digest Binding

### 5.1 Recommended Binding

For hardening, ModuleReceipt may bind schema digests:

```
opset_schema_digest = H_R(opset_schema_json)
dag_schema_digest = H_R(dag_schema_json)
execplan_schema_digest = H_R(execplan_schema_json)
module_receipt_schema_digest = H_R(module_receipt_schema_json)
```

### 5.2 Schema IDs

NK-3 v1.0 defines these canonical schemas:

| Schema | ID |
|--------|-----|
| KernelRegistry | `nk3.kernel_registry.schema.json` |
| OpSet | `nk3.opset.schema.json` |
| DAG | `nk3.dag.schema.json` |
| ExecPlan | `nk3.execplan.schema.json` |
| ModuleReceipt | `nk3.module_receipt.schema.json` |

---

## 6. Validation Rules

### 6.1 Static Checks

| Check | Description |
|-------|-------------|
| Program digest valid | Non-empty hash |
| Policy digest valid | Matches allowlist |
| Registry digest valid | Matches allowlist |
| Artifact digests match | All four match actual artifacts |
| Toolchain IDs valid | Non-empty strings |
| No optimization flag | Must be true |
| Schema digests valid | If provided, match schemas |

### 6.2 Rejection Criteria

| Reason | Description |
|--------|-------------|
| Missing digest | Any required digest missing |
| Digest mismatch | Artifact digest doesn't match |
| Policy digest unknown | Not in allowlist |
| Invalid toolchain | Empty or malformed ID |
| No optimization violated | Flag is false |

---

## 7. Chain Binding

### 7.1 v1.0 Rule

NK-2 must bind `module_receipt_digest` into the first commit (or a pre-commit receipt if allowed).

### 7.2 Simplest Binding

v1.0: "first commit includes module_receipt_digest"

---

## 8. Example ModuleReceipt

### 8.1 Example

```json
{
  "program_nsc_digest": "sha256:program123...",
  "policy_digest": "sha256:policy456...",
  "kernel_registry_digest": "sha256:registry789...",
  "opset_digest": "sha256:opsetabc...",
  "dag_digest": "sha256:dagdef...",
  "execplan_digest": "sha256:execplanghi...",
  "parser_id": "parser:1.0.0",
  "typechecker_id": "typechecker:1.0.0",
  "lowerer_id": "lowerer:1.0.0",
  "no_optimization_clause": true,
  "opset_schema_digest": "sha256:schema_opset...",
  "dag_schema_digest": "sha256:schema_dag...",
  "execplan_schema_digest": "sha256:schema_execplan...",
  "module_receipt_schema_digest": "sha256:schema_receipt..."
}
```
