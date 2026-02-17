# NK-2 Unit Tests: Scheduler

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk2.scheduler import GreedyCurvScheduler, SchedulerMode, AppendLog, Batch
from nk2.exec_plan import ExecPlan, OpSpec, OpStatus


class TestAppendLog(unittest.TestCase):
    """Test AppendLog."""
    
    def test_append(self):
        log = AppendLog()
        log.append("op:001")
        log.append("op:002")
        self.assertEqual(log.entries, ["op:001", "op:002"])
    
    def test_get_last(self):
        log = AppendLog()
        log.append("op:001")
        log.append("op:002")
        self.assertEqual(log.get_last(), "op:002")
    
    def test_get_last_empty(self):
        log = AppendLog()
        self.assertIsNone(log.get_last())
    
    def test_compute_digest(self):
        log = AppendLog()
        log.append("op:001")
        digest = log.compute_digest()
        self.assertTrue(digest.startswith("h:"))


class TestGreedyCurvScheduler(unittest.TestCase):
    """Test GreedyCurvScheduler."""
    
    def test_schedule_empty(self):
        scheduler = GreedyCurvScheduler()
        plan = ExecPlan(plan_id="test")
        batches = scheduler.schedule(plan, {})
        self.assertEqual(len(batches), 0)
    
    def test_schedule_single_op(self):
        scheduler = GreedyCurvScheduler()
        plan = ExecPlan(plan_id="test")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        plan.operations = [op]
        
        batches = scheduler.schedule(plan, {"op:001": 1.0})
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0].operations), 1)


class TestBatch(unittest.TestCase):
    """Test Batch."""
    
    def test_add_operation(self):
        batch = Batch(batch_id="batch:001")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        batch.add_operation(op)
        self.assertEqual(len(batch.operations), 1)
    
    def test_append_log_updated(self):
        batch = Batch(batch_id="batch:001")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        batch.add_operation(op)
        self.assertEqual(batch.append_log.get_last(), "op:001")
    
    def test_compute_cost(self):
        batch = Batch(batch_id="batch:001")
        op1 = OpSpec(op_id="op:001", kernel_id="kernel:add")
        op2 = OpSpec(op_id="op:002", kernel_id="kernel:mul")
        batch.add_operation(op1)
        batch.add_operation(op2)
        
        cost = batch.compute_cost({"op:001": 1.0, "op:002": 2.0})
        self.assertEqual(cost, 3.0)


class TestExecPlan(unittest.TestCase):
    """Test ExecPlan."""
    
    def test_create_exec_plan(self):
        plan = ExecPlan(plan_id="test")
        self.assertEqual(plan.plan_id, "test")
    
    def test_get_op(self):
        plan = ExecPlan(plan_id="test")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        plan.operations = [op]
        
        found = plan.get_op("op:001")
        self.assertEqual(found.op_id, "op:001")
    
    def test_get_op_not_found(self):
        plan = ExecPlan(plan_id="test")
        found = plan.get_op("nonexistent")
        self.assertIsNone(found)
    
    def test_mark_completed(self):
        plan = ExecPlan(plan_id="test")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        plan.operations = [op]
        
        plan.mark_completed("op:001")
        self.assertEqual(op.status, OpStatus.COMPLETED)
    
    def test_mark_failed(self):
        plan = ExecPlan(plan_id="test")
        op = OpSpec(op_id="op:001", kernel_id="kernel:add")
        plan.operations = [op]
        
        plan.mark_failed("op:001")
        self.assertEqual(op.status, OpStatus.FAILED)
    
    def test_is_complete_all_completed(self):
        plan = ExecPlan(plan_id="test")
        op1 = OpSpec(op_id="op:001", kernel_id="kernel:add", status=OpStatus.COMPLETED)
        op2 = OpSpec(op_id="op:002", kernel_id="kernel:add", status=OpStatus.COMPLETED)
        plan.operations = [op1, op2]
        
        self.assertTrue(plan.is_complete())
    
    def test_is_complete_with_pending(self):
        plan = ExecPlan(plan_id="test")
        op1 = OpSpec(op_id="op:001", kernel_id="kernel:add", status=OpStatus.COMPLETED)
        op2 = OpSpec(op_id="op:002", kernel_id="kernel:add", status=OpStatus.PENDING)
        plan.operations = [op1, op2]
        
        self.assertFalse(plan.is_complete())
    
    def test_has_failures(self):
        plan = ExecPlan(plan_id="test")
        op1 = OpSpec(op_id="op:001", kernel_id="kernel:add", status=OpStatus.COMPLETED)
        op2 = OpSpec(op_id="op:002", kernel_id="kernel:add", status=OpStatus.FAILED)
        plan.operations = [op1, op2]
        
        self.assertTrue(plan.has_failures())


if __name__ == '__main__':
    unittest.main()
