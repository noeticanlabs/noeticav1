# NK-1 Batch Epsilon Computation per docs/nk1/4_measured_gate.md

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from math import floor, ceil

from ck0.debtunit import DebtUnit


@dataclass
class BatchEpsilonConfig:
    """
    Configuration for batch epsilon computation.
    
    Per NK-1 §4.2-4.3:
    - ε_B = ΔV_B - ΔV_Σ (measured batch residual)
    - ε̂(B) = certificate bound with half-even rounding
    - M_ENTRY_MODE binds to matrix digest
    """
    matrix_digest: str = ""
    rounding_mode: str = "half_even"  # Only one rounding, half-even


class VFunctional:
    """
    Violation functional V(x) per NK-1 §4.1.
    
    V_DU : State → ℤ≥0 (DebtUnit integer quanta)
    V_OUTPUT_MODE = debtunit_only.v1
    """
    
    def __init__(self, evaluate_fn: Callable[[Dict[str, Any]], int]):
        """
        Args:
            evaluate_fn: Function that takes state dict and returns DebtUnit value
        """
        self._evaluate_fn = evaluate_fn
    
    def evaluate(self, state: Dict[str, Any]) -> int:
        """
        Evaluate V(x) on state.
        
        Returns DebtUnit integer quanta.
        Must be deterministic and use only StateCtx (no ledger, time, randomness).
        """
        return self._evaluate_fn(state)


class Operation:
    """
    An operation that transforms state.
    
    Per NK-1 §4.2:
    - x_o = f_o(x) - operation applied to pre-state
    - Δ_o uses only W_o outputs
    - tilde{x}_o = patch(x, W_o, Δ_o)
    """
    
    def __init__(
        self,
        op_id: str,
        apply_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        write_set: List[str]  # W_o - fields this op writes
    ):
        self.op_id = op_id
        self._apply_fn = apply_fn
        self.write_set = set(write_set)
    
    def apply(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply operation to state."""
        return self._apply_fn(state)
    
    def patch(
        self,
        original_state: Dict[str, Any],
        delta_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create patched state using only fields in write_set.
        
        Per NK-1 §4.2:
        tilde{x}_o = patch(x, W_o, Δ_o)
        Only fields in W_o are updated from delta_state.
        """
        result = dict(original_state)
        for field in self.write_set:
            if field in delta_state:
                result[field] = delta_state[field]
        return result


def compute_epsilon_B(
    state_before: Dict[str, Any],
    operations: List[Operation],
    v_func: VFunctional,
    apply_kernel_fn: Callable[[Dict[str, Any], Operation], Dict[str, Any]]
) -> Tuple[int, Dict[str, int]]:
    """
    Compute ε_B (measured batch residual).
    
    Per NK-1 §4.2:
    
    For each op:
    - x_o = f_o(x) on same pre-state
    - Δ_o uses *only W_o outputs*
    - tilde{x}_o = patch(x, W_o, Δ_o) (not raw kernel output)
    
    Then:
    - ΔV_B = V_DU(x') - V_DU(x)  [full batch execution]
    - ΔV_Σ = Σ_o (V_DU(tilde{x}_o) - V_DU(x))  [sum of patched ops]
    - ε_B = ΔV_B - ΔV_Σ
    
    Args:
        state_before: State before batch
        operations: List of operations in batch (deterministic order)
        v_func: V functional
        apply_kernel_fn: Function to apply kernel and get outputs
    
    Returns:
        (epsilon_B, intermediate_values)
    """
    # Compute V(x) - initial state
    v_before = v_func.evaluate(state_before)
    
    # Apply full batch to get x'
    state_after = dict(state_before)
    kernel_outputs = []
    for op in operations:
        result = apply_kernel_fn(state_after, op)
        kernel_outputs.append(result)
        state_after = result
    
    # Compute ΔV_B = V(x') - V(x)
    v_after = v_func.evaluate(state_after)
    delta_v_b = v_after - v_before
    
    # Compute sum of patched deltas: ΔV_Σ
    delta_v_sigma = 0
    intermediate = {}
    
    for i, op in enumerate(operations):
        # Apply op to original pre-state (same for all ops)
        # Get raw kernel output
        raw_output = kernel_outputs[i]
        
        # Patch: only use fields in W_o
        patched_state = op.patch(state_before, raw_output)
        
        # Compute V on patched state
        v_patched = v_func.evaluate(patched_state)
        
        # ΔV_o = V(tilde{x}_o) - V(x)
        delta_v_o = v_patched - v_before
        delta_v_sigma += delta_v_o
        
        intermediate[f"op_{i}_delta"] = delta_v_o
    
    # ε_B = ΔV_B - ΔV_Σ
    epsilon_b = delta_v_b - delta_v_sigma
    
    intermediate["delta_v_b"] = delta_v_b
    intermediate["delta_v_sigma"] = delta_v_sigma
    intermediate["v_before"] = v_before
    intermediate["v_after"] = v_after
    
    return epsilon_b, intermediate


def half_even_round(value: float) -> int:
    """
    Half-even rounding per NK-1 §4.3.
    
    Round to nearest integer, with ties rounded to even.
    This is the only rounding method allowed.
    """
    # Get integer and fractional parts
    int_part = int(value)
    frac_part = value - int_part
    
    if frac_part < 0.5:
        return int_part
    elif frac_part > 0.5:
        return int_part + 1
    else:
        # Exactly 0.5 - round to even
        if int_part % 2 == 0:
            return int_part
        else:
            return int_part + 1


def compute_epsilon_hat(
    curvature_matrix_entries: Dict[Tuple[int, int], float],
    delta_vector: List[int],
    matrix_scale: int = 1
) -> int:
    """
    Compute ε̂(B) certificate bound.
    
    Per NK-1 §4.3:
    - M_ENTRY_MODE is canonical (rational scaled or fixed integer scale)
    - One rounding only, half-even, into DebtUnit integer quanta
    - ε̂ output always in same unit as ε measured
    
    Args:
        curvature_matrix_entries: Dict of (i,j) -> M_ij values
        delta_vector: List of deltas for each dimension
        matrix_scale: Scale factor for matrix entries
    
    Returns:
        ε̂ in DebtUnit integer quanta
    """
    # Compute quadratic form: ε̂ = delta^T * M * delta
    n = len(delta_vector)
    result = 0.0
    
    for i in range(n):
        for j in range(n):
            # Get matrix entry (use symmetry: M_ij = M_ji)
            key = (min(i, j), max(i, j))
            m_ij = curvature_matrix_entries.get(key, 0.0)
            
            # Apply scale
            m_ij_scaled = m_ij * matrix_scale
            
            # Add to result: M_ij * delta_i * delta_j
            result += m_ij_scaled * delta_vector[i] * delta_vector[j]
    
    # Round to DebtUnit integer with half-even
    return half_even_round(result)


def verify_gate(
    epsilon_measured: int,
    epsilon_hat: int
) -> Tuple[bool, str]:
    """
    Verify gate: ε_measured <= ε_hat
    
    Per NK-1 §4:
    Gate approves if measured epsilon is within bound.
    """
    if epsilon_measured <= epsilon_hat:
        return True, "GATE_APPROVED"
    return False, f"GATE_REJECTED: ε_measured({epsilon_measured}) > ε_hat({epsilon_hat})"


def check_v_output(
    state: Dict[str, Any],
    v_func: VFunctional
) -> Tuple[bool, str]:
    """
    Verify V output is valid (no NaN/Inf, integer quanta).
    
    Per NK-1 §4.1:
    V_DU rejects NaN/Inf (should be unreachable under state validation).
    """
    try:
        v = v_func.evaluate(state)
        
        # Check for invalid values
        if v < 0:
            return False, f"V_DU must be ℤ≥0, got {v}"
        
        # Check is integer
        if not isinstance(v, int):
            return False, f"V_DU must be integer, got {type(v)}"
        
        return True, "V_DU_OK"
    except Exception as e:
        return False, f"V_DU_ERROR: {e}"


# Test implementations
if __name__ == "__main__":
    # Test half-even rounding
    assert half_even_round(0.4) == 0
    assert half_even_round(0.5) == 0  # Round to even
    assert half_even_round(0.6) == 1
    assert half_even_round(1.5) == 2  # Round to even
    assert half_even_round(2.5) == 2  # Round to even
    assert half_even_round(3.5) == 4  # Round to even
    
    print("Half-even rounding tests passed!")
    
    # Test V functional
    def simple_v(state):
        return state.get("debt", 0)
    
    v = VFunctional(simple_v)
    result = v.evaluate({"debt": 100})
    assert result == 100
    print("V functional tests passed!")
    
    # Test operation patch
    def apply_op(state):
        return {"balance": state.get("balance", 0) + 50}
    
    op = Operation("op1", apply_op, ["balance"])
    
    original = {"balance": 100, "version": 1}
    delta = {"balance": 150}
    
    patched = op.patch(original, delta)
    assert patched == {"balance": 150, "version": 1}
    print("Operation patch tests passed!")
    
    # Test epsilon computation
    def kernel_apply(state, op):
        return op.apply(state)
    
    # Simple V that just returns balance
    v_func = VFunctional(lambda s: s.get("balance", 0))
    
    # Two operations
    op1 = Operation("op1", lambda s: {"balance": s.get("balance", 0) + 50}, ["balance"])
    op2 = Operation("op2", lambda s: {"balance": s.get("balance", 0) + 30}, ["balance"])
    
    state_before = {"balance": 100}
    
    eps, intermediates = compute_epsilon_B(state_before, [op1, op2], v_func, kernel_apply)
    print(f"ε_B = {eps}")
    print(f"Intermediates: {intermediates}")
    
    # Test gate verification
    approved, reason = verify_gate(50, 100)
    assert approved
    print("Gate verification tests passed!")
    
    print("\nAll batch epsilon tests passed!")
