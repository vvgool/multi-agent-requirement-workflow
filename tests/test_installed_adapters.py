"""Zero-skipTest regression checks for the source repository's Protocol 5 self-bootstrapped adapters."""

import importlib.util
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
IH_SPEC = importlib.util.spec_from_file_location(
    "install_helper", ROOT / "skills/setup-requirement-workflow/scripts/install_helper.py"
)
IH = importlib.util.module_from_spec(IH_SPEC)
IH_SPEC.loader.exec_module(IH)


class InstalledAdapterTests(unittest.TestCase):
    def setUp(self):
        self.lock = IH.parse_simple_yaml((ROOT / "workflow.lock.yaml").read_text(encoding="utf-8"))
        self.pkg = self.lock["package"]
        self.src = self.lock["source"]
        self.sha = self.pkg["sha256"]
        self.cache_dir = ROOT / ".agents/requirement-workflow-cache" / self.sha

    def test_self_lock_and_restored_cache_match_source(self):
        self.assertEqual(self.pkg["version"], "3.0.0")
        self.assertEqual(self.pkg["protocol_version"], 5)
        self.assertEqual(self.src["kind"], "self")
        self.assertEqual(self.src["location"], ".")
        self.assertEqual(self.src["revision"], "self")
        self.assertTrue(self.cache_dir.is_dir(), f"locked cache missing: {self.cache_dir}")
        self.assertEqual(IH.compute_digest(self.cache_dir)["sha256"], self.sha)

    def test_managed_entry_matches_locked_cache_template(self):
        actual = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        begin = "<!-- requirement-workflow:begin -->"
        end = "<!-- requirement-workflow:end -->"
        block = actual[actual.index(begin) : actual.index(end) + len(end)] + "\n"
        expected = (
            self.cache_dir / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(block, expected)

    def test_agents_md_universal_adapter_replaces_zed_adapter(self):
        self.assertFalse((ROOT / "skills/setup-requirement-workflow/references/zed-adapter.md").exists())
        adapter_path = ROOT / "skills/setup-requirement-workflow/references/agents-md-adapter.md"
        self.assertTrue(adapter_path.is_file())
        adapter = adapter_path.read_text(encoding="utf-8")
        for req in ("agents-md", "规则型宿主", "AGENTS.md", "Zed", "Cursor", "Windsurf", "Antigravity", ".zed/agents"):
            self.assertIn(req, adapter)
        self.assertNotIn("native_role_probes", adapter)

    def test_precompiled_codex_and_opencode_roles_match_locked_cache(self):
        expected_roles = IH._build_roles(self.cache_dir, ["codex", "opencode"], self.sha)
        self.assertEqual(len(expected_roles), 8)
        for rel, exp_bytes in expected_roles.items():
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"missing generated role: {rel}")
            self.assertEqual(path.read_bytes(), exp_bytes, f"role byte drift: {rel}")


if __name__ == "__main__":
    unittest.main()
