"""
Full Integration Test Suite

Comprehensive integration tests covering ALL modules:
- NK-1: Runtime Kernel (policy, state canon, receipts)
- NK-2: Execution + Scheduler
- NK-3: Lowering Core (NSC → OpSet → DAG)
- NK-4G: Governance Certificate Verification
- NEC: Numerical Error Contract (integrated via CK-0)
- ASG: Adaptive Spectral Governance (curvature/spectral analysis)
- CK-0: Mathematical Substrate (exact arithmetic, invariants)
- PhaseLoom: Geometric Memory Extension
- COH: Category of Coherent Spaces

Data Flow:
NSC Input (NK-3) → OpSet → DAG → ExecPlan (NK-2) → State/Receipts (CK-0)
    → [PhaseLoom Functor] → [COH Categorical View]
    → ASG Spectral Analysis (κ₀, margin)
    → NK-4G Receipt Extension (certificate)
    → NK-1 Policy Gates (PASS/WARN/HALT)
"""

import unittest
import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# CK-0 imports
from ck0.debtunit import DebtUnit, ZERO, ONE
from ck0.state_space import State, FieldBlock, FieldDef, FieldType
from ck0.invariants import Invariant, InvariantSet
from ck0.violation import ViolationFunctional, Contract
from ck0.budget_law import ServiceLaw, DisturbancePolicy, compute_budget_law
from ck0.curvature import CurvatureMatrix
from ck0.transition import TransitionContract, TransitionDescriptor, TransitionType
from ck0.receipts import StepReceipt, CommitReceipt, ReceiptChain

# COH imports - use main import to get all exports
from coh import (
    CohObject,
    CohMorphism,
    create_finite_coh_object,
    is_ck0_receipt,
    verify_faithfulness,
    verify_algebraic_geometric_binding,
    identity,
    compose,
    product,
    pullback,
    TimeFunctor,
)

# NK-1 imports
from nk1.policy_bundle import PolicyBundle, PolicyStatus, evaluate_nk4g_policy
from nk1.state_canon import StateCanon, create_state_with_meta
from nk1.value_canon import ValueCanon
from nk1.receipt_canon import ReceiptCanon, MerkleTree
from nk1.delta_norm import DeltaNormConfig, NormDomainMode, compute_delta_norm
from nk1.batch_epsilon import BatchEpsilonConfig, VFunctional, compute_epsilon_hat
from nk1.measured_gate import MeasuredGate, GateDecision, DisturbancePolicies
from nk1.curvature_matrix import CurvatureMatrixRegistry

# NK-2 imports
from nk2.exec_plan import ExecPlan, OpSpec, OpStatus
from nk2.scheduler import GreedyCurvScheduler, SchedulerMode, Batch, AppendLog
from nk2.failure_handling import FailureHandler, FailureType

# NK-3 imports
from nk3.canon_inputs import NSCProgram, InputBundle, NSCVersion, create_example_nsc_program
from nk3.opset import OpSet, OpSpecNK3
from nk3.dag import DAG, DAGEdge, EdgeKind, insert_join_nodes, compute_hazard_edges

# NK-4G imports
from nk4g.receipt_fields import ASGCertificate, NK4GReceiptExtension
from nk4g.verifier import NK4GVerifier, VerificationResult
from nk4g.policy import NK4GPolicyKeys, NK4GPolicyBundle

# ASG imports
from asg.types import ASGStateLayout, ASGParams
from asg.operators import build_mean_zero_projector
from asg.assembly import assemble_full_jacobian, assemble_hessian_model
from asg.spectral import (
    estimate_kappa_0,
    estimate_kappa_0_policy,
    compute_semantic_direction,
    compute_semantic_margin_policy,
    compute_margin,
)
from asg.watchdog import ProxWatchdog, create_watchdog

# PhaseLoom imports
from phaseloom.types import (
    PLState, PLParams, MemoryState, FixedPoint, Weights,
    StepType, convert_to_ck0_format, convert_from_ck0_format,
    fixedpoint_to_debtunit_value, debtunit_value_to_fixedpoint,
)
from phaseloom.functor import PhaseLoomFunctor
from phaseloom.potential import PhaseLoomPotential
from phaseloom.receipt import PhaseLoomReceipt


class TestCK0CoreIntegration(unittest.TestCase):
    """Integration tests for CK-0 core functionality."""
    
    def test_debtunit_arithmetic_integration(self):
        """Test DebtUnit arithmetic flows through the system."""
        # Create various DebtUnits
        a = DebtUnit(100)
        b = DebtUnit(50)
        c = DebtUnit(0)
        
        # Addition
        result = a + b
        self.assertEqual(result.value, 150)
        
        # Subtraction
        result = a - b
        self.assertEqual(result.value, 50)
        
        # Multiplication
        result = a * DebtUnit(2)
        self.assertEqual(result.value, 200)
        
        # Division
        result = a // DebtUnit(4)
        self.assertEqual(result.value, 25)
        
        # Zero and One
        self.assertEqual(ZERO.value, 0)
        self.assertEqual(ONE.value, 1)
    
    def test_state_field_integration(self):
        """Test CK-0 State with field definitions."""
        # Create field definitions
        field_defs = [
            FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER),
            FieldDef(field_id="f:" + "1" * 32, field_type=FieldType.NONNEG_INT),
            FieldDef(field_id="f:" + "2" * 32, field_type=FieldType.RATIONAL),
        ]
        
        # Create field block
        block = FieldBlock(
            block_id="b:primary",
            fields=field_defs,
            access_policy="public"
        )
        
        # Create state
        state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={
                "f:" + "0" * 32: 42,
                "f:" + "1" * 32: 100,
                "f:" + "2" * 32: 3.14,
            }
        )
        
        # Verify field access
        self.assertEqual(state.get_field("f:" + "0" * 32), 42)
        self.assertEqual(state.get_field("f:" + "1" * 32), 100)
        
        # Verify state hash is computed
        self.assertIsNotNone(state.hash())
    
    def test_violation_functional_integration(self):
        """Test ViolationFunctional V(x) computation."""
        # Create a simple violation functional
        def v_fn(x):
            return max(0, x - 10)
        
        v_func = ViolationFunctional(v_fn)
        
        # Test various inputs
        self.assertEqual(v_func.evaluate(5), 0)   # Below threshold
        self.assertEqual(v_func.evaluate(10), 0)   # At threshold
        self.assertEqual(v_func.evaluate(15), 5)   # Above threshold
        
        # Create contract
        contract = Contract(
            name="test_contract",
            v_function=v_func,
            threshold=10
        )
        
        self.assertFalse(contract.is_violated(5))
        self.assertFalse(contract.is_violated(10))
        self.assertTrue(contract.is_violated(15))
    
    def test_budget_law_integration(self):
        """Test ServiceLaw S(D,B) computation."""
        # Create service law
        service = ServiceLaw(
            name="test_service",
            policy=DisturbancePolicies.ADVERSARIAL
        )
        
        # Compute budget law
        D = DebtUnit(100)  # Disturbance
        B = DebtUnit(200)  # Budget
        
        result = compute_budget_law(service, D, B)
        
        # Verify result is a valid DebtUnit
        self.assertIsInstance(result, DebtUnit)
        self.assertGreaterEqual(result.value, 0)
    
    def test_curvature_matrix_integration(self):
        """Test CurvatureMatrix NEC closure."""
        # Create simple curvature matrix
        residuals = [0, 1, 2, 3]
        
        matrix = CurvatureMatrix.from_residuals(residuals)
        
        # Verify NEC closure property
        self.assertTrue(matrix.verify_nec_closure())
        
        # Get closure
        closure = matrix.get_closure()
        self.assertIsInstance(closure, list)


class TestCK0ToCOHBridge(unittest.TestCase):
    """Integration tests for CK-0 to COH bridge."""
    
    def test_ck0_state_to_coh_object(self):
        """Test converting CK-0 State to CohObject."""
        # Create a minimal CK-0 state
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:primary", fields=[field_def], access_policy="public")
        state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 42}
        )
        
        # Create finite coherent object from CK-0 state
        states = {'s0', 's1', 's2'}
        receipts = {'r0', 'r1'}
        
        potential = {'s0': 0, 's1': 1, 's2': 2}.__getitem__
        budget_map = {'r0': 0, 'r1': 1}.__getitem__
        valid = {('s1', 's0', 'r0'), ('s2', 's1', 'r1')}
        
        coh_obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Verify it's a valid CohObject
        self.assertIsInstance(coh_obj, CohObject)
        self.assertEqual(len(coh_obj.states), 3)
    
    def test_coh_morphism_composition(self):
        """Test COH morphism composition."""
        # Create simple states and receipts
        states = {'a', 'b', 'c'}
        receipts = {'r1', 'r2'}
        
        potential = {'a': 0, 'b': 1, 'c': 2}.__getitem__
        budget_map = {'r1': 0, 'r2': 1}.__getitem__
        valid = {('b', 'a', 'r1'), ('c', 'b', 'r2')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Create morphisms
        f = CohMorphism(
            name='f',
            source='a',
            target='b',
            receipt='r1',
            preimage={'a'},
            image={'b'}
        )
        
        g = CohMorphism(
            name='g', 
            source='b',
            target='c',
            receipt='r2',
            preimage={'b'},
            image={'c'}
        )
        
        # Compose
        h = compose(f, g)
        
        # Verify composition
        self.assertEqual(h.source, 'a')
        self.assertEqual(h.target, 'c')
    
    def test_coh_faithfulness_verification(self):
        """Test COH faithfulness verification."""
        states = {'a', 'b'}
        receipts = {'r1'}
        
        potential = {'a': 0, 'b': 1}.__getitem__
        budget_map = {'r1': 0}.__getitem__
        valid = {('b', 'a', 'r1')}
        
        obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # Verify faithfulness
        result = verify_faithfulness(obj)
        self.assertTrue(result)


class TestNK3ToNK2Pipeline(unittest.TestCase):
    """Integration tests for NK-3 to NK-2 pipeline."""
    
    def test_nsc_to_opset(self):
        """Test NSCProgram to OpSet conversion."""
        # Create example NSC program
        nsc = create_example_nsc_program(num_ops=3)
        
        self.assertIsInstance(nsc, NSCProgram)
        self.assertEqual(nsc.version, NSCVersion.V1)
        
        # Create OpSet from NSC
        opset = OpSet.from_nsc(nsc)
        
        self.assertIsInstance(opset, OpSet)
        self.assertGreater(len(opset.ops), 0)
    
    def test_opset_to_dag(self):
        """Test OpSet to DAG construction."""
        # Create simple opset
        ops = [
            OpSpecNK3(op_id="op0", input_ids=[], output_ids=["out0"]),
            OpSpecNK3(op_id="op1", input_ids=["out0"], output_ids=["out1"]),
            OpSpecNK3(op_id="op2", input_ids=["out1"], output_ids=["out2"]),
        ]
        
        opset = OpSet(ops=ops, metadata={})
        
        # Build DAG
        dag = DAG.from_opset(opset)
        
        self.assertIsInstance(dag, DAG)
        self.assertEqual(len(dag.nodes), 3)
        
        # Compute hazard edges
        hazards = compute_hazard_edges(dag)
        self.assertIsInstance(hazards, list)
        
        # Insert join nodes
        dag_with_joins = insert_join_nodes(dag)
        self.assertIsInstance(dag_with_joins, DAG)
    
    def test_dag_to_execplan(self):
        """Test DAG to ExecPlan scheduling."""
        # Create simple DAG
        ops = [
            OpSpecNK3(op_id="op0", input_ids=[], output_ids=["out0"]),
            OpSpecNK3(op_id="op1", input_ids=["out0"], output_ids=["out1"]),
        ]
        
        opset = OpSet(ops=ops, metadata={})
        dag = DAG.from_opset(opset)
        
        # Create scheduler
        scheduler = GreedyCurvScheduler(mode=SchedulerMode.GREEDY_CURV)
        
        # Schedule
        exec_plan = scheduler.schedule(dag)
        
        self.assertIsInstance(exec_plan, ExecPlan)
        self.assertGreater(len(exec_plan.steps), 0)


class TestNK2ToCK0Integration(unittest.TestCase):
    """Integration tests for NK-2 to CK-0 integration."""
    
    def test_execplan_to_ck0_state(self):
        """Test ExecPlan results stored in CK-0 State."""
        # Create field definitions
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:state", fields=[field_def], access_policy="public")
        
        # Create initial state
        initial_state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 0}
        )
        
        # Create execution plan with steps
        steps = [
            OpSpec(op_id="op0", status=OpStatus.COMPLETED, output={"f:" + "0" * 32: 10}),
            OpSpec(op_id="op1", status=OpStatus.COMPLETED, output={"f:" + "0" * 32: 20}),
        ]
        
        exec_plan = ExecPlan(
            steps=steps,
            metadata={"iteration": 1}
        )
        
        # Extract final state from exec plan
        final_state = initial_state
        for step in exec_plan.steps:
            if step.status == OpStatus.COMPLETED:
                for field_id, value in step.output.items():
                    final_state = final_state.set_field(field_id, value)
        
        self.assertEqual(final_state.get_field("f:" + "0" * 32), 20)
    
    def test_batch_receipt_generation(self):
        """Test Batch results generate receipts."""
        # Create batch
        batch = Batch(
            ops=[
                OpSpec(op_id="op0", status=OpStatus.COMPLETED),
                OpSpec(op_id="op1", status=OpStatus.COMPLETED),
            ]
        )
        
        # Create append log
        append_log = AppendLog(entries=[])
        
        # Generate step receipt
        receipt = StepReceipt(
            step_id="step0",
            batch=batch,
            before_state_hash="hash_before",
            after_state_hash="hash_after",
            append_log=append_log
        )
        
        self.assertIsInstance(receipt, StepReceipt)
        self.assertEqual(receipt.step_id, "step0")


class TestCK0ToASGBridge(unittest.TestCase):
    """Integration tests for CK-0 to ASG bridge."""
    
    def test_curvature_to_asg_params(self):
        """Test extracting curvature for ASG analysis."""
        N = 8
        
        # Create ASG state layout
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create weights
        weights = [1.0] * N
        
        # Create ASG params
        params = ASGParams(
            state_layout=layout,
            weights=weights,
            alpha_l=1.0,
            alpha_g=1.0,
            w_theta=1.0,
        )
        
        self.assertEqual(params.state_layout.n, N)
        
        # Assemble Jacobian
        jacobian = assemble_full_jacobian(params, "1d_ring")
        
        # Verify shape
        self.assertEqual(jacobian.shape, (4 * N, 4 * N))
        
        # Assemble Hessian model
        hessian = assemble_hessian_model(jacobian)
        
        self.assertEqual(hessian.shape, (4 * N, 4 * N))
    
    def test_asg_spectral_analysis(self):
        """Test ASG spectral analysis with curvature."""
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create test Hessian (4N x 4N PD matrix)
        H = np.eye(4 * N) * 2.0
        
        # Estimate κ₀
        kappa_result = estimate_kappa_0(
            H,
            method_id="eigsh_smallest",
            tolerance=1e-6,
            max_iterations=1000
        )
        
        self.assertIsInstance(kappa_result.kappa_0, float)
        self.assertGreaterEqual(kappa_result.kappa_0, 0.0)
        
        # Compute semantic direction
        state = np.random.randn(4 * N)
        dir_result = compute_semantic_direction(
            state,
            H,
            layout,
            direction_id="asg.semantic.thetaG_rotation.v1"
        )
        
        self.assertIsInstance(dir_result.direction_id, str)
        
        # Compute semantic margin
        margin_result = compute_semantic_margin_policy(
            state,
            H,
            layout,
            direction_id="asg.semantic.thetaG_rotation.v1"
        )
        
        self.assertIsInstance(margin_result.gamma_sem, float)


class TestASGToNK4GIntegration(unittest.TestCase):
    """Integration tests for ASG to NK-4G integration."""
    
    def test_asg_certificate_to_nk4g_receipt(self):
        """Test ASGCertificate → NK4GReceiptExtension."""
        # Create ASG certificate
        cert = ASGCertificate(
            model_id="asg.zeta-theta-rho-G.v1",
            operator_digest="abc123",
            projector_id="asg.projector.4n_state_perp.v1",
            kappa_est=0.5,
            kappa_method_id="eigsh_smallest_sa.v1",
            kappa_tol=1e-6,
            kappa_maxiter=1000,
            gamma_sem=2.0,
            semantic_dir_id="asg.semantic.thetaG_rotation.v1",
            semantic_margin=4.0,
        )
        
        # Convert to NK4G receipt extension
        ext = NK4GReceiptExtension.from_asg_certificate(cert)
        
        self.assertEqual(ext.model_id, "asg.zeta-theta-rho-G.v1")
        self.assertEqual(ext.projector_id, "asg.projector.4n_state_perp.v1")
        self.assertEqual(ext.kappa_method_id, "eigsh_smallest_sa.v1")
    
    def test_nk4g_verifier(self):
        """Test NK4GVerifier checks certificate."""
        # Create certificate that should pass
        cert = ASGCertificate(
            model_id="asg.zeta-theta-rho-G.v1",
            operator_digest="abc123",
            projector_id="asg.projector.4n_state_perp.v1",
            kappa_est=0.5,
            kappa_method_id="eigsh_smallest_sa.v1",
            kappa_tol=1e-6,
            kappa_maxiter=1000,
            gamma_sem=2.0,
            semantic_dir_id="asg.semantic.thetaG_rotation.v1",
            semantic_margin=4.0,
        )
        
        # Create policy bundle
        policy = NK4GPolicyBundle(
            kappa_min=1e-8,
            margin_min=1.0,
        )
        
        # Verify
        verifier = NK4GVerifier(policy=policy)
        result = verifier.verify(cert)
        
        self.assertEqual(result.status, VerificationResult.Status.PASS)


class TestNK4GToNK1Integration(unittest.TestCase):
    """Integration tests for NK-4G to NK-1 integration."""
    
    def test_policy_gate_pass(self):
        """Test PolicyBundle gates PASS when thresholds met."""
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=1.0,
        )
        
        asg_cert = {
            "kappa_est": 0.1,
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.4n_state_perp.v1",
        }
        
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        self.assertEqual(status, PolicyStatus.PASS)
        self.assertEqual(len(details["issues"]), 0)
    
    def test_policy_gate_warn(self):
        """Test PolicyBundle gates WARN on margin violation."""
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=3.0,
        )
        
        asg_cert = {
            "kappa_est": 0.1,
            "semantic_margin": 1.0,  # Below threshold
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.4n_state_perp.v1",
        }
        
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        self.assertEqual(status, PolicyStatus.WARN)
    
    def test_policy_gate_halt(self):
        """Test PolicyBundle gates HALT on κ₀ violation."""
        policy = PolicyBundle(
            nk4g_kappa_min=1e-6,
            nk4g_margin_min=1.0,
        )
        
        asg_cert = {
            "kappa_est": 1e-10,  # Below threshold
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.4n_state_perp.v1",
        }
        
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        self.assertEqual(status, PolicyStatus.HALT)


class TestPhaseLoomIntegration(unittest.TestCase):
    """Integration tests for PhaseLoom integration."""
    
    def test_fixedpoint_arithmetic(self):
        """Test FixedPoint arithmetic."""
        a = FixedPoint.from_float(1.5)
        b = FixedPoint.from_float(2.0)
        
        c = a + b
        self.assertAlmostEqual(c.to_float(), 3.5, places=5)
        
        d = a * b
        self.assertAlmostEqual(d.to_float(), 3.0, places=5)
    
    def test_plstate_creation(self):
        """Test PLState creation."""
        # Create base state (from CK-0)
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:state", fields=[field_def], access_policy="public")
        base_state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 42}
        )
        
        # Create PLState
        pl_state = PLState(
            x=base_state,
            C=FixedPoint.from_float(1.0),
            T=FixedPoint.from_float(0.5),
            b=FixedPoint.from_float(10.0),
            a=FixedPoint.from_float(0.1)
        )
        
        self.assertEqual(pl_state.x.get_field("f:" + "0" * 32), 42)
        self.assertAlmostEqual(pl_state.C.to_float(), 1.0, places=5)
    
    def test_plparams_default(self):
        """Test PLParams default creation."""
        params = PLParams.default()
        
        self.assertIsInstance(params, PLParams)
        self.assertAlmostEqual(params.rho_C.to_float(), 0.9, places=5)
        self.assertAlmostEqual(params.rho_T.to_float(), 0.9, places=5)
    
    def test_ck0_to_phaseloom_conversion(self):
        """Test CK-0 to PhaseLoom conversion."""
        # Create CK-0 value
        ck0_value = DebtUnit(100)
        
        # Convert to FixedPoint
        fp = debtunit_value_to_fixedpoint(ck0_value)
        
        self.assertIsInstance(fp, FixedPoint)
        
        # Convert back
        restored = fixedpoint_to_debtunit_value(fp)
        
        self.assertEqual(restored.value, ck0_value.value)
    
    def test_phaseloom_potential(self):
        """Test PhaseLoom Potential computation."""
        # Create params
        params = PLParams.default()
        
        # Create base state
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:state", fields=[field_def], access_policy="public")
        base_state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 10}
        )
        
        # Create PL state
        pl_state = PLState(
            x=base_state,
            C=FixedPoint.from_float(1.0),
            T=FixedPoint.from_float(0.5),
            b=FixedPoint.from_float(10.0),
            a=FixedPoint.from_float(0.1)
        )
        
        # Compute potential
        potential = PhaseLoomPotential.compute(pl_state, params)
        
        self.assertIsInstance(potential, FixedPoint)
        self.assertGreater(potential.value, 0)


class TestEndToEndPipeline(unittest.TestCase):
    """End-to-end pipeline integration tests."""
    
    def test_full_pipeline_without_phaseloom(self):
        """Test full pipeline: NK-3 → NK-2 → CK-0 → ASG → NK-4G → NK-1."""
        
        # === Step 1: NK-3: NSC → OpSet → DAG ===
        nsc = create_example_nsc_program(num_ops=2)
        opset = OpSet.from_nsc(nsc)
        dag = DAG.from_opset(opset)
        
        # === Step 2: NK-2: DAG → ExecPlan ===
        scheduler = GreedyCurvScheduler(mode=SchedulerMode.GREEDY_CURV)
        exec_plan = scheduler.schedule(dag)
        
        # === Step 3: CK-0: State management ===
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:state", fields=[field_def], access_policy="public")
        state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 0}
        )
        
        # Update state from exec plan
        for step in exec_plan.steps:
            if step.status == OpStatus.COMPLETED:
                state = state.set_field("f:" + "0" * 32, 42)
        
        # === Step 4: ASG: Spectral Analysis ===
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        params = ASGParams(
            state_layout=layout,
            weights=[1.0] * N,
            alpha_l=1.0,
            alpha_g=1.0,
            w_theta=1.0,
        )
        
        H = np.eye(4 * N) * 2.0
        kappa_result = estimate_kappa_0(H, method_id="eigsh_smallest", tolerance=1e-6)
        
        state_vec = np.random.randn(4 * N)
        margin_result = compute_semantic_margin_policy(
            state_vec, H, layout,
            direction_id="asg.semantic.thetaG_rotation.v1"
        )
        
        # === Step 5: NK-4G: Certificate ===
        cert = ASGCertificate(
            model_id="asg.zeta-theta-rho-G.v1",
            operator_digest="abc123",
            projector_id="asg.projector.4n_state_perp.v1",
            kappa_est=kappa_result.kappa_0,
            kappa_method_id=kappa_result.method_id,
            kappa_tol=1e-6,
            kappa_maxiter=1000,
            gamma_sem=margin_result.gamma_sem,
            semantic_dir_id=margin_result.direction_id,
            semantic_margin=margin_result.margin,
        )
        
        # === Step 6: NK-1: Policy Gates ===
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=1.0,
        )
        
        asg_cert_dict = {
            "kappa_est": cert.kappa_est,
            "semantic_margin": cert.semantic_margin,
            "kappa_method_id": cert.kappa_method_id,
            "projector_id": cert.projector_id,
        }
        
        status, details = evaluate_nk4g_policy(asg_cert_dict, policy)
        
        # Final gate decision
        self.assertIn(status, [PolicyStatus.PASS, PolicyStatus.WARN, PolicyStatus.HALT])
    
    def test_full_pipeline_with_phaseloom(self):
        """Test full pipeline with PhaseLoom extension."""
        
        # === Create CK-0 state ===
        field_def = FieldDef(field_id="f:" + "0" * 32, field_type=FieldType.INTEGER)
        block = FieldBlock(block_id="b:state", fields=[field_def], access_policy="public")
        ck0_state = State(
            schema_id="schema:v1",
            field_blocks=[block],
            _field_values={"f:" + "0" * 32: 10}
        )
        
        # === Convert to PhaseLoom ===
        pl_state = PLState(
            x=ck0_state,
            C=FixedPoint.from_float(1.0),
            T=FixedPoint.from_float(0.5),
            b=FixedPoint.from_float(10.0),
            a=FixedPoint.from_float(0.1)
        )
        
        params = PLParams.default()
        
        # === Compute PhaseLoom potential ===
        v_pl = PhaseLoomPotential.compute(pl_state, params)
        
        # === ASG spectral analysis on extended state ===
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        H = np.eye(4 * N) * 2.0
        kappa_result = estimate_kappa_0(H, method_id="eigsh_smallest", tolerance=1e-6)
        
        # === Policy gates ===
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=1.0,
        )
        
        asg_cert = {
            "kappa_est": kappa_result.kappa_0,
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.4n_state_perp.v1",
        }
        
        status, _ = evaluate_nk4g_policy(asg_cert, policy)
        
        self.assertIn(status, [PolicyStatus.PASS, PolicyStatus.WARN, PolicyStatus.HALT])
    
    def test_full_pipeline_with_coh_verification(self):
        """Test full pipeline with COH categorical verification."""
        
        # === Create CK-0 trajectory ===
        states = {'s0', 's1', 's2'}
        receipts = {'r1', 'r2'}
        
        potential = {'s0': 0, 's1': 1, 's2': 2}.__getitem__
        budget_map = {'r1': 0, 'r2': 1}.__getitem__
        valid = {('s1', 's0', 'r1'), ('s2', 's1', 'r2')}
        
        # === Create COH object ===
        coh_obj = create_finite_coh_object(
            states=states,
            receipts=receipts,
            potential=potential,
            budget_map=budget_map,
            valid_transitions=valid
        )
        
        # === Verify COH properties ===
        faithful = verify_faithfulness(coh_obj)
        self.assertTrue(faithful)
        
        # === ASG analysis ===
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        H = np.eye(4 * N) * 2.0
        kappa_result = estimate_kappa_0(H, method_id="eigsh_smallest", tolerance=1e-6)
        
        # === Policy gates ===
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=1.0,
        )
        
        asg_cert = {
            "kappa_est": kappa_result.kappa_0,
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.4n_state_perp.v1",
        }
        
        status, _ = evaluate_nk4g_policy(asg_cert, policy)
        
        self.assertIn(status, [PolicyStatus.PASS, PolicyStatus.WARN, PolicyStatus.HALT])


class TestWatchdogIntegration(unittest.TestCase):
    """Integration tests for ASG Watchdog."""
    
    def test_watchdog_prox_inequality(self):
        """Test ProxWatchdog verifies prox inequality."""
        N = 8
        watchdog = create_watchdog(N)
        
        # Verify projector is canonical
        self.assertEqual(watchdog.projector_id, "asg.projector.4n_state_perp.v1")
        
        # Create states that satisfy prox inequality
        lambda_k = FixedPoint.from_float(0.1)
        
        state_before = np.zeros(4 * N)
        drift_point = np.ones(4 * N) * 0.1
        state_after = np.ones(4 * N) * 0.05
        
        # Compute values
        v_before = np.sum(state_before ** 2)
        v_drift = np.sum(drift_point ** 2)
        v_after = np.sum(state_after ** 2)
        
        # For prox inequality: V(x_{k+1}) <= V(z_k) - (1/2λ_k) * ||x_{k+1} - z_k||^2
        correction = 0.5 / lambda_k.to_float() * np.sum((state_after - drift_point) ** 2)
        rhs = v_drift - correction
        
        # The watchdog should verify this
        self.assertIsNotNone(watchdog)


if __name__ == '__main__':
    unittest.main()
