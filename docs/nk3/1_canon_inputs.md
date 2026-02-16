# NK-3 Canon Inputs v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`../nk2/1_exec_plan.md`](../nk2/1_exec_plan.md)

---

## Overview

This document defines the canonical inputs that NK-3 consumes. All inputs must be deterministic and hashable.

---

## 1. NSC.v1 Program Bytes

### 1.1 Canonical Input Definition

**Canonical input** is the canonical byte encoding of NSC.v1:

| Field | Type | Description |
|-------|------|-------------|
| `program_nsc_bytes` | bytes | Canonical NSC.v1 byte encoding |
| `program_nsc_digest` | Hash256 | H_R(program_nsc_bytes) |

### 1.2 No Frontend Degrees of Freedom

No front-end degrees of freedom are permitted inside NK-3. Any token/text frontend must first produce **canonical NSC bytes**.

### 1.3 NSC.v1 Requirements

NSC.v1 must be:
- **Typed**: All operations have explicit type signatures
- **Normalized**: All values in canonical form (no NaN, no ±Inf)
- **Deterministic**: Same meaning → same bytes

---

## 2. PolicyBundle

### 2.1 Definition

NK-3 is instantiated under a **fixed PolicyBundle digest**:

| Field | Type | Description |
|-------|------|-------------|
| `policy_bundle_id` | PolicyID | Policy bundle identifier |
| `policy_digest` | Hash256 | Hash of policy bundle (chain-locked) |

### 2.2 Allowlist Verification

The policy digest must match the allowlist in the NK-3 configuration.

---

## 3. KernelRegistry

### 3.1 Definition

NK-3 is instantiated under a **fixed KernelRegistry digest**:

| Field | Type | Description |
|-------|------|-------------|
| `kernel_registry_digest` | Hash256 | Hash of kernel registry |

### 3.2 Kernel Spec Requirements

Kernel specs include:
- Footprints and bounds (static or param-decidable via allowlisted footprint function hash)
- Block index information
- Float touch flags

---

## 4. Toolchain IDs

### 4.1 Required Toolchain Identifiers

NK-3 must record the toolchain versions used:

| Field | Type | Description |
|-------|------|-------------|
| `parser_id` | str | Parser identifier and version |
| `typechecker_id` | str | Type checker identifier and version |
| `lowerer_id` | str | Lowerer identifier and version |

---

## 5. Lowering Purity Axiom

### 5.1 Forbidden Inputs

`LowerNK3` is a pure function and must NOT depend on:

- Time
- Host info
- Filesystem
- Environment variables
- Thread count
- Hash-map iteration order
- Randomness
- Ledger contents

### 5.2 Allowed Inputs

`LowerNK3` may only depend on:

- `program_nsc_bytes`
- `policy_digest`
- `kernel_registry_digest`
- Toolchain IDs
- Allowlisted footprint function hashes (when used)

---

## 6. Input Validation

### 6.1 Static Checks

NK-3 must verify:

| Check | Description |
|-------|-------------|
| NSC bytes schema | Valid NSC.v1 encoding |
| Policy digest | Matches allowlist |
| Kernel registry digest | Matches allowlist |
| Toolchain IDs | Valid format |

### 6.2 Rejection Criteria

NK-3 must reject inputs if:

- NSC bytes fail schema validation
- Policy digest not in allowlist
- Kernel registry digest not in allowlist
- Unknown toolchain IDs
