# Noetica WASM ABI v1

**Version:** 1.0  
**Status:** Draft  
**Related:** [`6_ir_and_lowering.md`](6_ir_and_lowering.md), [`9_security_model.md`](9_security_model.md)

---

## 8.1 Host Boundary

Noetica WASM modules operate in a **hosted environment**. All consensus-critical operations (mint, burn, thaw, measure, emit) must cross the WASM/host boundary.

### Boundary Principle

> All state-modifying operations must be performed by the host. The WASM module only performs arithmetic, memory operations, and control flow.

### Allowed Host Calls

| Host Function | Called From | Purpose |
|---------------|-------------|---------|
| `host.mint` | mint construct | Create new budget |
| `host.burn` | burn construct | Destroy budget |
| `host.thaw` | thaw construct | Unlock budget |
| `host.measure` | measure construct | Read V(x) |
| `host.emit_checkpoint` | emit construct | Produce receipt |

---

## 8.2 Function Signatures

### Import Section

```wasm
(import "host" "mint" (func $host_mint
    (param i32)        ;; amount
    (param i32)        ;; mint_cap_ptr
    (result i32)))     ;; budget_ptr

(import "host" "burn" (func $host_burn
    (param i32)        ;; amount
    (param i32)        ;; budget_ptr
    (result i32)))     ;; receipt_ptr

(import "host" "thaw" (func $host_thaw
    (param i32)        ;; locked_budget_ptr
    (result i32)))     ;; budget_ptr

(import "host" "measure" (func $host_measure
    (param i32)        ;; state_ptr
    (result i32)))     ;; measurement_ptr

(import "host" "emit_checkpoint" (func $host_emit
    (result i32)))     ;; receipt_ptr
```

### Export Section

```wasm
(func $run (export "run")
    (param i32)        ;; input_ptr
    (result i32))      ;; output_ptr
```

---

## 8.3 Data Encoding

### Endianness

All multi-byte values are **big-endian** (network byte order).

### Fixed-Point Encoding

Values are encoded as scaled integers:

```
encoded = round_toward_zero(value × scale)
```

Where `scale = 1000` (configurable in profile).

### Canonical Byte Layout

```
┌─────────────────────────────────────────────┐
│ Field Header (4 bytes)                      │
│   - field_id: u16                          │
│   - encoding: u8                           │
│   - flags: u8                              │
├─────────────────────────────────────────────┤
│ Length (4 bytes)                            │
│   - payload_length: u32                    │
├─────────────────────────────────────────────┤
│ Payload (variable)                          │
│   - encoded value(s)                       │
└─────────────────────────────────────────────┘
```

---

## 8.4 Domain Separation

### Hash Domains

Each hash type uses a domain separator to prevent cross-domain attacks:

| Domain | Separator | Purpose |
|--------|-----------|---------|
| State | "noetica_state_v1" | State hash |
| Receipt | "noetica_receipt_v1" | Receipt hash |
| Program | "noetica_program_v1" | Program hash |
| Profile | "noetica_profile_v1" | Profile hash |

### Encoding

```
hash = SHA256(domain_separator || payload)
```

---

## 8.5 Memory Model

### Linear Memory

```
┌─────────────────────────────────────────────┐
│ 0x0000: Header                              │
│   - magic: 0x6E6F6574 ("noet")             │
│   - version: u16                           │
│   - state_ptr: u32                          │
│   - budget_ptr: u32                        │
├─────────────────────────────────────────────┤
│ 0x0100: State Region                       │
│   - NK-1 state (DebtUnit)                  │
│   - PhaseLoom state                        │
├─────────────────────────────────────────────┤
│ 0x1000: Budget Region                      │
│   - Current budget                         │
│   - Locked budget                          │
├─────────────────────────────────────────────┤
│ 0x2000: Receipt Region                     │
│   - Receipt buffer                         │
│   - Max 64KB                               │
├─────────────────────────────────────────────┤
│ 0x10000: Scratch Region                    │
│   - Working memory                         │
└─────────────────────────────────────────────┘
```

### Memory Safety

- No arbitrary reads/writes outside declared regions
- Bounds checking on all memory operations
- Maximum memory: 1GB (configurable)

---

## 8.6 Call Sequence

### Typical Execution Flow

```
1. WASM module loaded
2. Host populates input_ptr with initial state
3. Host calls $run
4. WASM executes local computation (solve/repair)
5. If host call needed:
   a. WASM encodes arguments
   b. WASM calls host function
   c. Host executes consensus-critical operation
   d. Host returns result
   e. WASM validates result
6. WASM returns output_ptr
7. Host reads output and receipts
```

### Error Handling

| Error | WASM Result | Host Action |
|-------|-------------|-------------|
| Invalid phase | trap | Revert state |
| Budget insufficient | trap | Revert state |
| Measure failure | return -1 | Check error code |
| Emit failure | return -1 | Check error code |

---

## 8.7 Receipt Format

### Receipt Structure

```json
{
  "version": "noetica_receipt_v1",
  "type": "burn" | "mint" | "checkpoint",
  "timestamp": 1234567890,
  "data": {
    // Type-specific fields
  },
  "hash": "sha256..."
}
```

### Burn Receipt

```json
{
  "type": "burn",
  "amount": 1000,
  "budget_before": 5000,
  "budget_after": 4000,
  "state_hash": "abc123...",
  "signature": "host_sig_..."
}
```

### Checkpoint Receipt

```json
{
  "type": "checkpoint",
  "state_hash": "abc123...",
  "v_x": 100,
  "phase": "Loom",
  "curvature": 500,
  "tension": 300,
  "receipt_chain": ["prev_hash_1", "prev_hash_2"]
}
```

---

## 8.8 Security Considerations

### Input Validation

The WASM module must validate all host call results:
- Check return codes
- Verify receipt hashes
- Validate state transitions

### Replay Prevention

- Each receipt includes timestamp and sequence number
- Host maintains receipt log
- Duplicate receipts rejected

### Timing Attacks

- No timing-dependent branches in consensus paths
- Fixed-time arithmetic operations
- No secret-dependent loops

---

## 8.9 References

- IR and lowering: [`6_ir_and_lowering.md`](6_ir_and_lowering.md)
- Security model: [`9_security_model.md`](9_security_model.md)
- Zero-cost coherence: [`10_zero_cost_coherence.md`](10_zero_cost_coherence.md)
