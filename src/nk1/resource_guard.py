# NK-1 Resource Guard: deterministic_reject.v1 per docs/nk1/1_constants.md

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# Import from ck0
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ck0'))

from debtunit import DebtUnit


class ResourceCapMode(Enum):
    """Resource cap enforcement modes."""
    HARD_REJECT = "hard_reject"  # Deterministic halt
    SOFT_LIMIT = "soft_limit"   # Warning but continue


@dataclass
class ResourceLimit:
    """A resource limit."""
    name: str
    max_value: int  # Maximum value in DebtUnit
    unit: str = "DebtUnit"


class ResourceGuard:
    """
    NK-1 Resource Guard per docs/ck0/F_failure_semantics.md.
    
    deterministic_reject.v1 - integrated into DebtUnit, V_DU, ε̂ computation.
    
    This is called from the NK-1 kernel layer, not only scheduler.
    """
    
    def __init__(self, limits: Dict[str, ResourceLimit] = None):
        self.limits = limits or {}
        self._current_usage: Dict[str, int] = {}
    
    def add_limit(self, limit: ResourceLimit) -> None:
        """Add a resource limit."""
        self.limits[limit.name] = limit
    
    def check(self, resource_name: str, value: int) -> bool:
        """
        Check if value exceeds limit.
        
        Returns True if within limits, False if exceeded.
        """
        if resource_name not in self.limits:
            return True  # No limit defined
        
        limit = self.limits[resource_name]
        return value <= limit.max_value
    
    def check_or_raise(self, resource_name: str, value: int) -> None:
        """
        Check value or raise ResourceCapError.
        
        Per docs/ck0/F_failure_semantics.md:
        Resource cap halt returns error with:
        - terminal_error_code: RESOURCE_CAP_HALT
        - op_id: identifier of failing operation
        - pre_state_hash: state hash before failure
        """
        if not self.check(resource_name, value):
            raise ResourceCapError(
                resource_name=resource_name,
                value=value,
                limit=self.limits[resource_name].max_value
            )
    
    def consume(self, resource_name: str, value: int) -> bool:
        """
        Consume resource and check limit.
        
        Returns True if successful, False if would exceed limit.
        """
        current = self._current_usage.get(resource_name, 0)
        new_value = current + value
        
        if not self.check(resource_name, new_value):
            return False
        
        self._current_usage[resource_name] = new_value
        return True
    
    def consume_or_raise(self, resource_name: str, value: int) -> None:
        """Consume or raise ResourceCapError."""
        if not self.consume(resource_name, value):
            limit = self.limits[resource_name]
            raise ResourceCapError(
                resource_name=resource_name,
                value=self._current_usage.get(resource_name, 0) + value,
                limit=limit.max_value
            )
    
    def get_usage(self, resource_name: str) -> int:
        """Get current usage for a resource."""
        return self._current_usage.get(resource_name, 0)
    
    def reset(self, resource_name: str = None) -> None:
        """Reset usage counters."""
        if resource_name:
            self._current_usage[resource_name] = 0
        else:
            self._current_usage.clear()


class ResourceCapError(Exception):
    """Raised when resource cap is exceeded."""
    
    def __init__(self, resource_name: str, value: int, limit: int):
        self.resource_name = resource_name
        self.value = value
        self.limit = limit
        super().__init__(
            f"Resource cap exceeded: {resource_name} = {value} > {limit}"
        )


# Standard resource limits

def create_standard_resource_guard() -> ResourceGuard:
    """Create standard resource guard with typical limits."""
    guard = ResourceGuard()
    
    # Standard limits per NK-1 spec
    guard.add_limit(ResourceLimit(
        name="max_debt",
        max_value=10**12,  # Maximum debt in system
        unit="DebtUnit"
    ))
    
    guard.add_limit(ResourceLimit(
        name="max_batch_size",
        max_value=1000,  # Maximum operations per batch
        unit="operations"
    ))
    
    guard.add_limit(ResourceLimit(
        name="max_state_size",
        max_value=10**9,  # Maximum state size
        unit="bytes"
    ))
    
    return guard
