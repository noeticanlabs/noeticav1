# CK-0 Transition Contract: Deterministic Evolution T(x, u)

from typing import Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .state_space import State


class TransitionType(Enum):
    """Types of transitions."""
    KERNEL_CALL = "kernel_call"
    FIELD_UPDATE = "field_update"
    COMPOSITE = "composite"


@dataclass
class TransitionDescriptor:
    """
    A transition descriptor u_k.
    
    Per docs/ck0/6_transition_contract.md:
    - Defines deterministic state evolution
    - Contains all information needed to compute x_{k+1} = T(x_k, u_k)
    """
    transition_id: str
    transition_type: TransitionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.transition_id:
            raise ValueError("transition_id is required")


@dataclass 
class TransitionResult:
    """Result of applying a transition."""
    new_state: State
    transition_descriptor: TransitionDescriptor
    success: bool
    error_message: Optional[str] = None


class TransitionContract:
    """
    The deterministic transition map T: X × U → X.
    
    Per docs/ck0/6_transition_contract.md:
    - Deterministic evolution
    - All transitions are replay-verifiable
    """
    
    def __init__(self):
        self._kernels: Dict[str, Callable[[State, Dict], State]] = {}
    
    def register_kernel(
        self, 
        kernel_id: str, 
        kernel_fn: Callable[[State, Dict], State]
    ) -> None:
        """Register a kernel function."""
        self._kernels[kernel_id] = kernel_fn
    
    def apply(
        self, 
        state: State, 
        descriptor: TransitionDescriptor
    ) -> TransitionResult:
        """
        Apply transition: x_{k+1} = T(x_k, u_k)
        
        Returns new state and result info.
        """
        try:
            if descriptor.transition_type == TransitionType.KERNEL_CALL:
                new_state = self._apply_kernel(state, descriptor)
            elif descriptor.transition_type == TransitionType.FIELD_UPDATE:
                new_state = self._apply_field_update(state, descriptor)
            elif descriptor.transition_type == TransitionType.COMPOSITE:
                new_state = self._apply_composite(state, descriptor)
            else:
                return TransitionResult(
                    new_state=state,
                    transition_descriptor=descriptor,
                    success=False,
                    error_message=f"Unknown transition type: {descriptor.transition_type}"
                )
            
            return TransitionResult(
                new_state=new_state,
                transition_descriptor=descriptor,
                success=True
            )
        except Exception as e:
            return TransitionResult(
                new_state=state,
                transition_descriptor=descriptor,
                success=False,
                error_message=str(e)
            )
    
    def _apply_kernel(
        self, 
        state: State, 
        descriptor: TransitionDescriptor
    ) -> State:
        """Apply kernel call transition."""
        kernel_id = descriptor.parameters.get('kernel_id')
        if kernel_id is None:
            raise ValueError("kernel_id required for kernel call")
        
        kernel_fn = self._kernels.get(kernel_id)
        if kernel_fn is None:
            raise ValueError(f"Unknown kernel: {kernel_id}")
        
        args = descriptor.parameters.get('args', {})
        return kernel_fn(state, args)
    
    def _apply_field_update(
        self, 
        state: State, 
        descriptor: TransitionDescriptor
    ) -> State:
        """Apply direct field update transition."""
        updates = descriptor.parameters.get('updates', {})
        if not updates:
            raise ValueError("updates required for field update")
        
        # Validate fields exist
        for field_id in updates.keys():
            if state.get_field(field_id) is None:
                raise ValueError(f"Unknown field: {field_id}")
        
        return state.with_fields(updates)
    
    def _apply_composite(
        self, 
        state: State, 
        descriptor: TransitionDescriptor
    ) -> State:
        """Apply composite transition (sequence of transitions)."""
        sub_transitions = descriptor.parameters.get('steps', [])
        if not sub_transitions:
            raise ValueError("steps required for composite transition")
        
        current_state = state
        for step in sub_transitions:
            step_descriptor = TransitionDescriptor(
                transition_id=step.get('id', ''),
                transition_type=TransitionType(step.get('type', 'field_update')),
                parameters=step.get('params', {})
            )
            result = self.apply(current_state, step_descriptor)
            if not result.success:
                raise ValueError(f"Composite step failed: {result.error_message}")
            current_state = result.new_state
        
        return current_state
    
    def __call__(
        self, 
        state: State, 
        descriptor: TransitionDescriptor
    ) -> TransitionResult:
        """Convenience: T(state, descriptor)."""
        return self.apply(state, descriptor)


# Example kernel

def example_add_kernel(state: State, args: Dict) -> State:
    """Example kernel: adds values to fields."""
    field_id = args.get('field_id')
    value = args.get('value', 0)
    
    current = state.get_field(field_id)
    if current is None:
        raise ValueError(f"Field not found: {field_id}")
    
    return state.set_field(field_id, current + value)


def create_example_contract() -> TransitionContract:
    """Create example transition contract."""
    contract = TransitionContract()
    contract.register_kernel("example.add", example_add_kernel)
    return contract


# Deterministic transition validation

def validate_transition_determinism(
    contract: TransitionContract,
    state: State,
    descriptor: TransitionDescriptor
) -> Tuple[bool, str]:
    """
    Validate transition is deterministic.
    
    A transition is deterministic if applying it twice with 
    same state produces same result.
    """
    result1 = contract.apply(state, descriptor)
    if not result1.success:
        return False, f"First application failed: {result1.error_message}"
    
    result2 = contract.apply(state, descriptor)
    if not result2.success:
        return False, f"Second application failed: {result2.error_message}"
    
    if result1.new_state.state_hash() != result2.new_state.state_hash():
        return False, "Transition is non-deterministic"
    
    return True, "OK"
