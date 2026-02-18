# NK-3 Unit Tests: Canon Inputs

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk3.canon_inputs import NSCProgram, InputBundle, PolicyBundleRef, KernelRegistryRef, create_example_nsc_program


class TestNSCProgram(unittest.TestCase):
    """Test NSCProgram."""
    
    def test_default_ids(self):
        prog = NSCProgram()
        self.assertEqual(prog.nsc_id, "id:nsc.v1")
        self.assertEqual(prog.canon_profile_id, "id:nk1.valuecanon.v1")
    
    def test_to_canonical_bytes(self):
        prog = NSCProgram(
            schema_id="id:schema.test",
            kernel_registry_digest="h:abc123",
            policy_digest="h:def456",
            entry="main",
            decls=[]
        )
        cb = prog.to_canonical_bytes()
        self.assertIsInstance(cb, bytes)
        self.assertTrue(cb.startswith(b'{'))
    
    def test_compute_digest(self):
        prog = NSCProgram(
            entry="main",
            decls=[]
        )
        digest = prog.compute_digest()
        self.assertTrue(digest.startswith("h:"))
        self.assertEqual(len(digest), 66)  # "h:" + 64 hex
    
    def test_decl_sorting(self):
        prog = NSCProgram(
            entry="main",
            decls=[
                {'decl_id': 'z_func', 'params': [], 'body': {}},
                {'decl_id': 'a_func', 'params': [], 'body': {}},
            ]
        )
        cb = prog.to_canonical_bytes()
        # a_func should come before z_func
        a_pos = cb.find(b'a_func')
        z_pos = cb.find(b'z_func')
        self.assertLess(a_pos, z_pos)


class TestInputBundle(unittest.TestCase):
    """Test InputBundle."""
    
    def test_validate_valid(self):
        bundle = InputBundle(
            program_nsc=NSCProgram(
                entry="main", 
                decls=[],
                policy_digest="h:abc",
                kernel_registry_digest="h:def"
            ),
            policy_bundle=PolicyBundleRef(policy_bundle_id="pb:001", policy_digest="h:abc"),
            kernel_registry=KernelRegistryRef(kernel_registry_digest="h:def")
        )
        self.assertTrue(bundle.validate())
    
    def test_validate_no_entry(self):
        bundle = InputBundle(
            program_nsc=NSCProgram(entry="", decls=[]),
            policy_bundle=PolicyBundleRef(policy_bundle_id="pb:001", policy_digest="h:abc"),
            kernel_registry=KernelRegistryRef(kernel_registry_digest="h:def")
        )
        self.assertFalse(bundle.validate())


class TestCreateExampleProgram(unittest.TestCase):
    """Test create_example_nsc_program."""
    
    def test_example_program(self):
        prog = create_example_nsc_program()
        self.assertEqual(prog.entry, "main")
        self.assertIsNotNone(prog.kernel_registry_digest)


if __name__ == '__main__':
    unittest.main()
