# NK-3 KernelRegistry Interface v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`1_canon_inputs.md`](1_canon_inputs.md)

---

## Overview

This document defines the KernelRegistry interface that NK-3 must assume. The KernelRegistry provides kernel specifications needed for lowering.

---

## 1. KernelSpec (Static)

### 1.1 Definition

Each kernel entry provides:

| Field | Type | Description |
|-------|------|-------------|
| `kernel_id` | KernelID | Unique kernel identifier |
| `kernel_hash` | Hash256 | Hash of kernel implementation |
| `glb_mode` | bool | Whether kernel can read ledger (false = cannot) |
| `footprint_mode` | FootprintMode | Static or param-decidable |
| `block_index` | bool | Whether kernel uses block indexing |
| `float_touch` | bool | Whether kernel touches floating-point values |
| `delta_bound_mode` | DeltaBoundMode | How delta bounds are computed |

### 1.2 Footprint Mode

| Mode | Description |
|------|-------------|
| `static_footprints` | Fixed R, W sets |
| `param_decidable` | Footprint computed via allowlisted function |

---

## 2. Static Footprints

### 2.1 Definition

When `footprint_mode = static_footprints`:

| Field | Type | Description |
|-------|------|-------------|
| `R` | set[FieldID] | Read set (sorted, deduped) |
| `W` | set[FieldID] | Write set (sorted, deduped) |

### 2.2 Requirements

- R and W must be sorted arrays
- R and W must be deduplicated
- No overlap between R and W (enforced by schema)

---

## 3. Param-Decidable Footprints

### 3.1 Definition

When `footprint_mode = param_decidable`:

```
footprint(params) → (R, W, block_index, float_touch, delta_bound_mode, requires_modeD)
```

### 3.2 Requirements

| Requirement | Description |
|-------------|-------------|
| Total | Function defined for all valid params |
| Terminating | Always terminates |
| Canonical output | R, W are sorted + deduped sets |
| Code hash | Function hash must be allowlisted |

### 3.3 Footprint Function Hash

| Field | Type | Description |
|-------|------|-------------|
| `footprint_fn_hash` | Hash256 | Hash of footprint function code |
| `allowlisted` | bool | Must be in NK-3 allowlist |

---

## 4. KernelRegistry Loader

### 4.1 Loader Interface

```python
class KernelRegistryLoader:
    """Loads and verifies KernelRegistry."""
    
    def load(registry_bytes: bytes) -> KernelRegistry:
        """Load registry from canonical bytes."""
    
    def verify_digest(registry: KernelRegistry, expected_digest: Hash256) -> bool:
        """Verify registry matches expected digest."""
    
    def get_kernel(registry: KernelRegistry, kernel_id: KernelID) -> KernelSpec:
        """Get kernel spec by ID."""
    
    def verify_footprint_fn(registry: KernelRegistry, fn_hash: Hash256) -> bool:
        """Verify footprint function is allowlisted."""
```

### 4.2 Allowlist Verification

NK-3 must verify:
- KernelRegistry digest matches allowlist
- All kernel IDs referenced in NSC are in registry
- All kernel hashes match registry
- All footprint function hashes are allowlisted

---

## 5. Kernel Validation Rules

### 5.1 Static Checks

| Check | Description |
|-------|-------------|
| Kernel ID exists | kernel_id in registry |
| Kernel hash match | kernel_hash matches registry entry |
| Footprint mode valid | Mode is `static_footprints` or `param_decidable` |
| Param-decidable verify | footprint_fn_hash is allowlisted |
| GLB mode consistent | glb_mode consistent with policy |

### 5.2 Rejection Criteria

NK-3 must reject if:
- Unknown kernel_id
- kernel_hash mismatch
- footprint_fn_hash not allowlisted
- Footprint function fails to terminate

---

## 6. Example KernelSpec

### 6.1 Static Footprint Example

```json
{
  "kernel_id": "add.v1",
  "kernel_hash": "sha256:abc123...",
  "glb_mode": false,
  "footprint_mode": "static_footprints",
  "static_footprints": {
    "R": ["field.a", "field.b"],
    "W": ["field.c"]
  },
  "block_index": false,
  "float_touch": false,
  "delta_bound_mode": "additive"
}
```

### 6.2 Param-Decidable Example

```json
{
  "kernel_id": "slice.v1",
  "kernel_hash": "sha256:def456...",
  "glb_mode": false,
  "footprint_mode": "param_decidable",
  "footprint_fn_hash": "sha256:func789...",
  "block_index": true,
  "float_touch": false,
  "delta_bound_mode": "parametric"
}
```
