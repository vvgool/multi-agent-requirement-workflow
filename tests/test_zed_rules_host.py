"""Executable contract fixtures for the Zed rules-only host.

These tests validate the documented pending/receipt shape and selection boundary.
They do not claim to run the Zed desktop application or implement installation.
"""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZED_ENTRY = ROOT / "workflow/hosts/zed.md"
ZED_ADAPTER = ROOT / "skills/setup-requirement-workflow/references/zed-adapter.md"


class ZedRulesHostTests(unittest.TestCase):
    def test_host_entry_and_adapter_define_rules_only_semantics(self):
        entry = ZED_ENTRY.read_text(encoding="utf-8")
        adapter = ZED_ADAPTER.read_text(encoding="utf-8")
        for text in (entry, adapter):
            self.assertIn("规则型宿主", text)
            self.assertIn("AGENTS.md", text)
            self.assertIn("native_role_probes", text)
            self.assertIn("not_applicable", text)
        self.assertIn("不生成 `.zed/agents`", entry)
        self.assertIn("不注册 product、development、testing、bug", entry)

    def test_zed_is_selected_only_by_explicit_or_current_host_signal(self):
        detected_hosts = {"codex", "opencode"}
        self.assertNotIn("zed", detected_hosts)

        explicit_hosts = set(detected_hosts)
        explicit_hosts.add("zed")
        self.assertIn("zed", explicit_hosts)

        current_host = "zed"
        current_targets = set(detected_hosts)
        if current_host == "zed":
            current_targets.add(current_host)
        self.assertIn("zed", current_targets)

    def test_zed_pending_plan_has_no_native_role_files(self):
        pending = {
            "schema_version": 2,
            "operation": "install",
            "host": "zed",
            "hosts": ["zed"],
            "planned_files": {
                "AGENTS.md": {"before": "existing", "after_sha256": "entry"},
            },
        }
        planned_paths = set(pending["planned_files"])
        self.assertEqual(pending["hosts"], ["zed"])
        self.assertIn("AGENTS.md", planned_paths)
        self.assertFalse(any(path.startswith(".zed/") for path in planned_paths))
        self.assertFalse(any("agents/requirement-" in path for path in planned_paths))

    def test_zed_receipt_marks_native_roles_not_applicable(self):
        zed_host = {
            "file_installation": "passed",
            "entry_probe": "passed",
            "role_mapping": {},
            "native_role_probes": [],
            "native_role_invocation": "not_applicable",
            "end_to_end": "pending",
        }
        self.assertEqual(zed_host["file_installation"], "passed")
        self.assertEqual(zed_host["entry_probe"], "passed")
        self.assertEqual(zed_host["native_role_probes"], [])
        self.assertEqual(zed_host["native_role_invocation"], "not_applicable")
        self.assertEqual(zed_host["end_to_end"], "pending")
        self.assertNotIn("host_task_id", zed_host)


if __name__ == "__main__":
    unittest.main()
