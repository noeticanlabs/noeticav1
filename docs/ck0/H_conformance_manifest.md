# CK-0 Conformance Manifest

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`10_conformance_tests.md`](10_conformance_tests.md), [`9_replay_verifier.md`](9_replay_verifier.md)

---

## Overview

This document defines the conformance pack manifest format for CK-0 golden vector artifacts. The manifest provides a single source of truth listing all required artifacts for conformance verification, enabling deterministic byte-level validation of canonical encodings and computational outputs.

---

## Manifest Format

The conformance manifest is a JSON file that enumerates all golden vector artifacts with their associated file paths and cryptographic hashes for integrity verification.

### Schema

```json
{
  "version": "v1.0",
  "description": "CK-0 Conformance Pack Manifest",
  "artifacts": [
    {
      "name": "<artifact_name>",
      "file": "<filename>",
      "hash": "<sha256_hex>"
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Manifest version identifier |
| `description` | string | Human-readable description |
| `artifacts` | array | Array of artifact entries |
| `artifacts[].name` | string | Unique artifact identifier |
| `artifacts[].file` | string | Relative path to artifact file |
| `artifacts[].hash` | string | SHA-256 hash of artifact contents (64 hex characters) |

---

## Required Artifacts

### Core Canonical Encoding Artifacts

| Name | File | Description |
|------|------|-------------|
| `state_canon_bytes` | `state_canon.json` | Golden vector for state canonical encoding (byte-exact) |
| `receipt_canon_bytes` | `receipt_canon.json` | Golden vector for receipt canonical encoding |
| `matrix_canon_bytes` | `matrix_canon.json` | Golden vector for transition matrix canonical encoding |

### Structural Artifacts

| Name | File | Description |
|------|------|-------------|
| `merkle_root` | `merkle_golden.json` | Golden Merkle tree root for receipt chain verification |
| `policy_bundle_bytes` | `policy_golden.json` | Golden policy bundle for authorization verification |

### Computational Example Artifacts

| Name | File | Description |
|------|------|-------------|
| `epsilon_hat_examples` | `eps_hat_golden.json` | Golden vectors for curvature upper bound (ε̂) computations |
| `epsilon_measured_examples` | `eps_measured_golden.json` | Golden vectors for measured curvature (ε) computations |
| `dag_ordering_examples` | `dag_order_golden.json` | Golden vectors for DAG topological ordering verification |

---

## Complete Manifest Example

```json
{
  "version": "v1.0",
  "description": "CK-0 Conformance Pack Manifest",
  "artifacts": [
    {
      "name": "state_canon_bytes",
      "file": "state_canon.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "receipt_canon_bytes",
      "file": "receipt_canon.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "merkle_root",
      "file": "merkle_golden.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "matrix_canon_bytes",
      "file": "matrix_canon.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "policy_bundle_bytes",
      "file": "policy_golden.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "epsilon_hat_examples",
      "file": "eps_hat_golden.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "epsilon_measured_examples",
      "file": "eps_measured_golden.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "name": "dag_ordering_examples",
      "file": "dag_order_golden.json",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

> **Note:** The hash values shown above are examples (SHA-256 of empty input). Actual artifacts require computed golden hashes.

---

## Verification Command

### CLI Interface

The conformance check command verifies all artifacts against the manifest:

```bash
noetica conformance-check --manifest <path_to_manifest>
```

### Command Options

| Option | Description |
|--------|-------------|
| `--manifest` | Path to the conformance manifest JSON file (required) |
| `--verbose` | Enable detailed output for each artifact verification |
| `--strict` | Fail on any hash mismatch (default: report only) |

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | All artifacts verified successfully |
| 1 | One or more artifacts failed verification |
| 2 | Invalid manifest format or missing files |

### Example Usage

```bash
# Basic conformance check
noetica conformance-check --manifest conformance_manifest.json

# Verbose output
noetica conformance-check --manifest conformance_manifest.json --verbose

# Strict mode (fail on any mismatch)
noetica conformance-check --manifest conformance_manifest.json --strict
```

---

## Artifact Storage Requirements

### Directory Structure

```
artifacts/
├── state_canon.json
├── receipt_canon.json
├── merkle_golden.json
├── matrix_canon.json
├── policy_golden.json
├── eps_hat_golden.json
├── eps_measured_golden.json
└── dag_order_golden.json
```

### Hash Algorithm

All artifact hashes use **SHA-256** (64 hexadecimal characters, lowercase). This ensures:
- Deterministic verification across toolchains
- Compatibility with standard cryptographic libraries
- Sufficient collision resistance for golden vector integrity

### Encoding Requirements

- All JSON artifact files: UTF-8 encoded
- All hashes: lowercase hexadecimal (base16)
- All paths: relative to manifest location

---

## Integration with Build Pipeline

The conformance manifest should be integrated into the pre-build tightening phase:

1. **Phase 0**: Generate all golden vector artifacts with computed hashes
2. **Phase 0**: Create/update `conformance_manifest.json` with actual hashes
3. **Pre-build**: Run `noetica conformance-check --manifest` to verify integrity
4. **Build**: Proceed only after all artifacts verify successfully

---

## Related Documents

- [`10_conformance_tests.md`](10_conformance_tests.md) - Test vector definitions
- [`9_replay_verifier.md`](9_replay_verifier.md) - Replay verification protocol
- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Canonical encoding rules
- [`C_canonical_ids.md`](C_canonical_ids.md) - ID canonicalization
- [`D_sorting_rules.md`](D_sorting_rules.md) - Bytewise sorting rules
