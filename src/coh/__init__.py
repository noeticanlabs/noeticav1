"""
Coh - Category of Coherent Spaces

A category-theoretic framework for systems that bind:
- Geometric state space (X)
- Violation potential (V: X → ℝ≥0)
- Algebra of certified transitions (receipts: RV ⊆ X × X × Rec)

Supports:
- Products and pullbacks
- Functorial time (F: ℕ → Coh)
- Natural transformations
- CK-0 as full subcategory

References:
- docs/coh/0_overview.md - Main overview
- docs/coh/1_objects.md - Object definitions
- docs/coh/2_morphisms.md - Morphism definitions
- docs/coh/3_category.md - Category structure
- docs/coh/4_limits.md - Products and pullbacks
- docs/coh/5_functors.md - Functorial time
- docs/coh/6_ck0_integration.md - CK-0 integration
- docs/coh/7_functors_builtin.md - Built-in functors
- docs/coh/8_examples.md - Examples
- docs/coh/9_reference_api.md - API reference
"""

# Core types
from .types import (
    CohObject,
    CohMorphism,
    StateCarrier,
    ReceiptCarrier,
    FiniteStateCarrier,
    FiniteReceiptCarrier,
    create_finite_coh_object,
)

# Object functions
from .objects import (
    verify_faithfulness,
    verify_algebraic_geometric_binding,
    verify_deterministic_validity,
    transition_relation,
    descent_preorder,
    reachable_from,
    reachable_states,
)

# Morphism functions
from .morphisms import (
    verify_admissibility_preservation,
    verify_receipt_covariance,
    verify_order_preservation,
    apply_morphism,
    apply_morphism_to_receipt,
)

# Category structure
from .category import (
    identity,
    compose,
    compose_checked,
    verify_identity_left,
    verify_identity_right,
    verify_associativity,
    CohCategory,
)

# Limits
from .limits import (
    product,
    product_projections,
    pullback,
    pullback_projections,
)

# Functors
from .functors import (
    TimeFunctor,
    NaturalTransformation,
    create_time_functor,
)

# CK-0 integration
from .ck0_integration import (
    CohCK0Object,
    CohCK0Morphism,
    CohCK0Category,
    InclusionFunctor,
    CK0ViolationFunctor,
    is_ck0_receipt,
    CK0_RECEIPT_FIELDS,
    create_ck0_potential,
    create_ck0_validator,
)

# Built-in functors
from .functors_builtin import (
    ViolationFunctor,
    AdmissibleFunctor,
    TransitionFunctor,
    BudgetFunctor,
    ValidatorFunctor,
    Projector,
    compose_vio_adm,
    compose_trans_reachable,
)

__version__ = '1.0.0'

__all__ = [
    # Types
    'CohObject',
    'CohMorphism',
    'StateCarrier',
    'ReceiptCarrier',
    'FiniteStateCarrier',
    'FiniteReceiptCarrier',
    'create_finite_coh_object',
    
    # Object functions
    'verify_faithfulness',
    'verify_algebraic_geometric_binding',
    'verify_deterministic_validity',
    'transition_relation',
    'descent_preorder',
    'reachable_from',
    'reachable_states',
    
    # Morphism functions
    'verify_admissibility_preservation',
    'verify_receipt_covariance',
    'verify_order_preservation',
    'apply_morphism',
    'apply_morphism_to_receipt',
    
    # Category
    'identity',
    'compose',
    'compose_checked',
    'verify_identity_left',
    'verify_identity_right',
    'verify_associativity',
    'CohCategory',
    
    # Limits
    'product',
    'product_projections',
    'pullback',
    'pullback_projections',
    
    # Functors
    'TimeFunctor',
    'NaturalTransformation',
    'create_time_functor',
    
    # CK-0
    'CohCK0Object',
    'CohCK0Morphism',
    'CohCK0Category',
    'InclusionFunctor',
    'CK0ViolationFunctor',
    'is_ck0_receipt',
    'CK0_RECEIPT_FIELDS',
    'create_ck0_potential',
    'create_ck0_validator',
    
    # Built-in functors
    'ViolationFunctor',
    'AdmissibleFunctor',
    'TransitionFunctor',
    'BudgetFunctor',
    'ValidatorFunctor',
    'Projector',
    'compose_vio_adm',
    'compose_trans_reachable',
]
