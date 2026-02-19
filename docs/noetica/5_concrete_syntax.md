# Noetica Concrete Syntax

**Version:** 1.0  
**Status:** Draft  
**Related:** [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md), [`6_ir_and_lowering.md`](6_ir_and_lowering.md)

---

## 5.1 EBNF Grammar

The complete grammar for Noetica Core v1:

```ebnf
program     ::= stmt*

stmt        ::= expr ";"

expr        ::= mint
              | burn
              | solve
              | repair
              | freeze
              | thaw
              | measure
              | emit
              | move
              | phase_match
              | let
              | seq

(* Boundary Operations *)
mint        ::= "mint" amount "from" ident "->" ident
burn        ::= "burn" amount "->" ident
thaw        ::= "thaw" ident "->" ident
measure     ::= "measure" ident "->" ident
emit        ::= "emit" "->" ident

(* Geometry Operations *)
solve       ::= "solve" "<" amount ">" ident ident "->" ident ident
repair      ::= "repair" "<" amount ">" ident ident "->" ident ident

(* Phase Control *)
freeze      ::= "freeze" ident ident "->" ident
phase_match ::= "phase_match" ident "{" branch* "}"

(* Linear Memory *)
move        ::= "move" ident "->" ident

(* Let Binding *)
let         ::= "let" ident "=" expr "in" expr

(* Sequencing *)
seq         ::= expr ";" expr

(* Branch *)
branch      ::= "Loom" "->" expr
              | "Frozen" "->" expr

(* Lexical *)
amount      ::= DECIMAL
ident       ::= ALPHA (ALPHA | DIGIT)*
DECIMAL     ::= [0-9]+ ("." [0-9]+)?
ALPHA       ::= [a-zA-Z_]
DIGIT       ::= [0-9]

(* Comments *)
COMMENT     ::= "//" [^\n]* "\n"
              | "/*" [^*] "*" ([^*/] [^*] "*")* "/"
```

---

## 5.2 Tokenization Rules

### Reserved Words

```
mint, burn, thaw, measure, emit,
solve, repair, freeze, thaw,
phase_match, let, in,
Loom, Frozen
```

### Identifiers

- Must start with letter or underscore
- May contain letters, digits, underscores
- Case-sensitive
- Maximum length: 64 characters

### Decimal Literals

All decimal literals must be valid fixed-point values:

```
Valid:  "100", "100.0", "0.001", "1000.500"
Invalid: ".001", "100.", "+100", "1e3"
```

---

## 5.3 Pretty-Printed Examples

### Mint Operation

```
mint 1000 from mint_cap -> budget;
```

### Burn Operation

```
burn 500 -> burn_receipt;
```

### Solve Operation

```
solve <100> state_gradients -> new_state new_gradients;
```

### Repair Operation

```
repair <50> state_gradients -> restored_state restored_gradients;
```

### Freeze Operation

```
freeze loom_state frozen_state -> locked_budget;
```

### Thaw Operation

```
thaw locked_budget -> budget;
```

### Measure Operation

```
measure current_state -> measurement;
```

### Emit Checkpoint

```
emit -> checkpoint_receipt;
```

### Move Operation

```
move input_resource -> output_resource;
```

### Phase Match

```
phase_match current_phase {
    Loom -> solve <10> s g -> s' g';
    Frozen -> emit -> rc;
};
```

---

## 5.4 AST Representation

### Node Types

```
Program : [Stmt]
Stmt    : Expr
Expr    : Mint | Burn | Solve | Repair | Freeze | Thaw
        | Measure | Emit | Move | PhaseMatch | Let | Seq

Mint      : { amount: Decimal, source: Ident, target: Ident }
Burn      : { amount: Decimal, target: Ident }
Solve     : { budget: Decimal, input1: Ident, input2: Ident,
              output1: Ident, output2: Ident }
Repair    : { budget: Decimal, input1: Ident, input2: Ident,
              output1: Ident, output2: Ident }
Freeze    : { input1: Ident, input2: Ident, target: Ident }
Thaw      : { source: Ident, target: Ident }
Measure   : { source: Ident, target: Ident }
Emit      : { target: Ident }
Move      : { source: Ident, target: Ident }
PhaseMatch : { scrutinee: Ident, branches: [Branch] }
Branch    : { phase: Phase, body: Expr }
Let       : { binder: Ident, value: Expr, body: Expr }
Seq       : { head: Expr, tail: Expr }
```

---

## 5.5 Canonical Serialization

### JSON Encoding

Programs are canonically serialized as JSON:

```json
{
  "version": "noetica_v1",
  "program": [
    {
      "op": "mint",
      "amount": "1000",
      "source": "mint_cap",
      "target": "budget"
    },
    {
      "op": "solve",
      "budget": "100",
      "inputs": ["state", "gradients"],
      "outputs": ["new_state", "new_gradients"]
    }
  ]
}
```

### Canonical Hash

The program hash is computed over the canonical JSON bytes:

```
program_hash = SHA256(canonical_json(program))
```

---

## 5.6 Error Messages

| Error | Example | Message |
|-------|---------|---------|
| Unexpected token | `m int 100` | "Expected 'mint', found 'int'" |
| Invalid decimal | `.5` | "Invalid decimal literal" |
| Undefined identifier | `mint x -> y` | "Unknown identifier 'x'" |
| Missing semicolon | `mint 1 -> x` | "Expected ';'" |
| Invalid amount | `mint -10` | "Amount must be non-negative" |

---

## 5.7 References

- Kernel spec: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- IR and lowering: [`6_ir_and_lowering.md`](6_ir_and_lowering.md)
- WASM ABI: [`8_wasm_abi_v1.md`](8_wasm_abi_v1.md)
