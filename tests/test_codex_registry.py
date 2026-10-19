"""Real TOML semantics and byte-preserving registry planning; no host simulation."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'skills/setup-requirement-workflow/scripts/codex_registry.py'
spec = importlib.util.spec_from_file_location('codex_registry', HELPER)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)
BLOCK = (ROOT / 'skills/setup-requirement-workflow/assets/templates/codex-registry.toml').read_bytes()


class RegistryTests(unittest.TestCase):
    def test_append_preserves_unrelated_bytes(self):
        original = b'# user comments\r\n[agents.custom]\r\ndescription="mine"\r\n'
        after = registry.merge(original, BLOCK)
        self.assertTrue(after.startswith(original))
        self.assertEqual(registry.merge(after, BLOCK), after)

    def test_semantic_conflicts(self):
        for value in [b'[agents.requirement_product]\ndescription="mine"\n',
                      b'[agents."requirement_product"]\ndescription="mine"\n',
                      b'agents.requirement_product.description="mine"\n',
                      b'agents={requirement_product={description="mine"}}\n',
                      b'agents={enabled=false}\n', b'agents=false\n',
                      b'[profiles.test.agents.requirement_testing]\ndescription="mine"\n']:
            with self.subTest(value=value), self.assertRaises(registry.RegistryError):
                registry.merge(value, BLOCK)

    def test_invalid_and_markers(self):
        for value in [b'[bad', b'a=1\na=2', BLOCK + BLOCK,
                      BLOCK.split(b'# requirement-workflow:codex-registry:end')[0],
                      b'x="""\n' + BLOCK + b'"""\n']:
            with self.subTest(value=value), self.assertRaises(registry.RegistryError):
                registry.merge(value, BLOCK)

    def test_restore_claim_and_missing(self):
        with self.assertRaisesRegex(registry.RegistryError, 'host_not_initialized'):
            registry.merge(b'# user\n', BLOCK, restore_only=True)
        after = registry.merge(b'# user\n', BLOCK)
        self.assertEqual(registry.merge(after, BLOCK, restore_only=True), after)

    def test_user_edit_protected_and_upgrade(self):
        old = BLOCK.replace('澄清需求并输出验收标准'.encode(), b'old')
        original = b'# user\n' + old + b'\n[unrelated]\nx=1\n'
        with self.assertRaisesRegex(registry.RegistryError, 'adapter_modified'):
            registry.merge(original, BLOCK)
        old_hash = hashlib.sha256(old).hexdigest()
        after = registry.merge(original, BLOCK, previous_sha256=old_hash)
        self.assertEqual(after, original.replace(old, BLOCK))
        with self.assertRaises(registry.RegistryError):
            registry.merge(original + b'\n[agents.requirement_testing]\nx=1\n', BLOCK,
                           previous_sha256=old_hash)
        with self.assertRaises(registry.RegistryError):
            registry.merge(original, BLOCK, restore_only=True, previous_sha256=old_hash)

    def test_old_receipt_must_match_even_if_new_template_matches(self):
        with self.assertRaises(registry.RegistryError):
            registry.merge(BLOCK, BLOCK, previous_sha256='0' * 64)

    def test_pending_whole_file_boundary(self):
        before = b'# user\n'
        after = registry.merge(before, BLOCK)
        self.assertTrue(registry.matches_plan(before, before, after))
        self.assertTrue(registry.matches_plan(after, before, after))
        self.assertFalse(registry.matches_plan(after + b'# user edit\n', before, after))


if __name__ == '__main__':
    unittest.main()
