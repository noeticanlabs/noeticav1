# Noetica IR and Lowering

**Version:** 1.0  
**Status:** Draft  
**Related:** [`5_concrete_syntax.md`](5_concrete_syntax.md), [`8_wasm_abi_v1.md`](8_wasm_abi_v1.md)

---

## 6.1 Core IR

The Noetica Intermediate Representation (IR) is a **Static Single Assignment (SSA)** form with explicit resource management.

### IR Design Principles

1. **SSA**: Each variable assigned exactly once
2. **Explicit moves**: No implicit resource transfer
3. **Explicit consumption**: All resource uses are visible
4. **No implicit drop**: Unused resources must be explicitly moved to discard

### IR Instructions

```
Instr ::= "mint" dst, amount
        | "burn" src, dst
        | "solve" budget, src1, src2, dst1, dst2
        | "repair" budget, src1, src2, dst1, dst2
        | "freeze" src1, src2, dst
        | "thaw" src, dst
        | "measure" src, dst
        | "emit" dst
        | "move" src, dst
        | "branch" cond, then, else
        | "phi" dst, (cond1, val1), (cond2, val2)
```

### Basic Block Structure

```
Block:
  label: Label
  instrs: [Instr]
  terminator: Terminator

Terminator ::= "jump" Label
             | "branch" Value, Label, Label
             | "ret" Value
```

### Control Flow Graph

```
CFG:
  entry: Block
  blocks: Map[Label, Block]
  exit: Block
```

---

## 6.2 Lowering Pipeline

### Pipeline Stages

```
Source → Parser → AST → Type Checker → IR Builder → SSA Conversion
                                                      ↓
                                            Refinement Checker
                                                      ↓
                                            WASM Emitter → WASM
```

### Stage Details

| Stage | Input | Output | Checks |
|-------|-------|--------|--------|
| Parser | Source text | AST | Syntax errors |
| Type Checker | AST | Typed AST | Linear typing, phase rules |
| IR Builder | Typed AST | IR | None |
| SSA Conversion | IR | SSA form | None |
| Refinement Checker | SSA | SSA | QF-LRA-FP predicates |
| WASM Emitter | SSA | WASM | None |

---

## 6.3 Determinism Theorem

### Theorem

Given:
- Source program P
- Compiler profile hash H_compiler
- Canonical profile hash H_canonical

`Lower(P, H_compiler, H_canonical)` produces a unique byte sequence B.

### Proof Outline

1. **Parser determinism**: Parser is a total function on source text
2. **Type checking determinism**: Type rules are syntax-directed, single outcome
3. **IR construction determinism**: Single translation from typed AST to IR
4. **Refinement checking**: Either accepts (unique) or rejects (compile error)
5. **WASM emission**: Deterministic encoding given IR

Therefore, same (P, H_compiler, H_canonical) → same B. ∎

---

## 6.4 No Dead Code Elimination (v1)

**Design Decision**: No dead code elimination in v1.

Rationale:
- Simpler verification: what you write is what executes
- Easier receipt tracing: every instruction produces verifiable output
- Security: prevents hidden code paths

### Future Consideration

Dead code elimination may be added in v2 with:
- Explicit annotation for removable code
- Receipt preservation requirements

---

## 6.5 Resource Tracking in IR

### Resource Liveness

Each SSA value carries a resource flag:

```
Value:
  id: Name
  type: Type
  resource: ResourceFlag

ResourceFlag ::= Linear | Nonlinear | Discarded
```

### Consumption Tracking

| Operation | Producer | Consumer |
|-----------|----------|----------|
| `mint` | dst | - |
| `burn` | src | dst (receipt) |
| `solve` | dst1, dst2 | budget |
| `repair` | dst1, dst2 | budget |
| `freeze` | dst | src1, src2 |
| `thaw` | dst | src |
| `measure` | dst | src |
| `emit` | dst | - |
| `move` | dst | src |

---

## 6.6 WASM Target

### WASM Version

WebAssembly 1.0 (MVP) with extensions:
- Reference types
- Bulk memory operations

### Module Structure

```wasm
(module
  (type $func_type (func (param i32) (result i32)))
  (import "host" "mint" (func $host_mint (param i32) (result i32)))
  (import "host" "burn" (func $host_burn (param i32) (result i32)))
  (import "host" "thaw" (func $host_thaw (param i32) (result i32)))
  (import "host" "measure" (func $host_measure (param i32) (result i32)))
  (import "host" "emit" (func $host_emit (result i32)))
  (func $program (export "run") ...)
)
```

### Memory Model

- Linear memory for state vectors
- No garbage collection (manual resource management)
- Maximum memory: 1GB (configurable in profile)

---

## 6.7 Canonical Encoding

### IR Canonical Form

For deterministic lowering, IR must be in canonical form:

1. **Block ordering**: Ascending label order
2. **Instruction ordering**: Within block, program order
3. **Name allocation**: Sequential from 0
4. **No unreachable blocks**: Eliminated before emission

### Canonical Bytes

```
canonical_bytes = JSON.stringify(canonical_ir)
hash = SHA256(canonical_bytes)
```

---

## 6.8 References

- Syntax: [`5_concrete_syntax.md`](5_concrete_syntax.md)
- WASM ABI: [`8_wasm_abi_v1.md`](8_wasm_abi_v1.md)
- Security model: [`9_security_model.md`](9_security_model.md)
