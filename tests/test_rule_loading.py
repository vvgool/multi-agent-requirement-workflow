"""Structural, topological, tree-purity, and dual-root regression tests for Protocol 5 v3.0.0 rules."""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rule_loading", ROOT / "scripts/verify-rule-loading.py")
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)

IH_SPEC = importlib.util.spec_from_file_location(
    "install_helper", ROOT / "skills/setup-requirement-workflow/scripts/install_helper.py"
)
IH = importlib.util.module_from_spec(IH_SPEC)
IH_SPEC.loader.exec_module(IH)


class RuleLoadingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve() / "source"
        self.root.mkdir()
        for name in ["framework.yaml", "AGENTS.md", "README.md", "workflow.yaml", "LICENSE"]:
            shutil.copyfile(ROOT / name, self.root / name)
        ignore = shutil.ignore_patterns("system", "__pycache__", "*.pyc", ".DS_Store")
        for name in ["agents", "skills", "workflow", "templates"]:
            shutil.copytree(ROOT / name, self.root / name, ignore=ignore)

    def _sync_agents_managed_block(self):
        entry = (
            self.root / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        ).read_text(encoding="utf-8")
        agents_path = self.root / "AGENTS.md"
        agents_text = agents_path.read_text(encoding="utf-8")
        begin = "<!-- requirement-workflow:begin -->"
        end = "<!-- requirement-workflow:end -->"
        b_idx = agents_text.index(begin)
        e_idx = agents_text.index(end) + len(end)
        agents_path.write_text(
            agents_text[:b_idx] + entry.rstrip("\n") + agents_text[e_idx:],
            encoding="utf-8",
        )

    def test_v300_protocol5_source_cache_dual_root_and_stdlib_purity(self):
        for scan_dir in ("scripts", "skills", "tests"):
            for py_path in sorted((ROOT / scan_dir).rglob("*.py")):
                if py_path.resolve() == Path(__file__).resolve():
                    continue
                src = py_path.read_text(encoding="utf-8")
                self.assertNotRegex(
                    src,
                    r"(?m)^\s*(?:import\s+yaml\b|from\s+yaml\s+import\b)",
                    f"third_party_pyyaml_import_forbidden: {py_path}",
                )

        self.assertEqual(RULES.MAX_PACKAGE_FILES, 46)
        self.assertEqual(RULES.MAX_PACKAGE_BYTES, 122000)
        self.assertEqual(RULES.MAX_ENTRY_LINES, 16)
        self.assertEqual(RULES.MAX_ENTRY_BYTES, 2000)
        result = RULES.check(self.root)
        self.assertEqual(result["framework"]["protocol_version"], 5)
        self.assertEqual(result["framework"]["version"], "3.0.0")
        self.assertLessEqual(result["entry_lines"], RULES.MAX_ENTRY_LINES)
        self.assertLessEqual(result["entry_bytes"], RULES.MAX_ENTRY_BYTES)
        self.assertEqual(result["package_file_count"], 46)
        self.assertLessEqual(result["package_file_count"], RULES.MAX_PACKAGE_FILES)
        self.assertLessEqual(result["package_total_bytes"], RULES.MAX_PACKAGE_BYTES)

        cache_like = Path(self.scratch.name).resolve() / "cache_only"
        IH.stage_clean_package(self.root, cache_like, include_working_tree=True)
        self.assertFalse((cache_like / "AGENTS.md").exists())
        self.assertFalse((cache_like / "README.md").exists())
        self.assertFalse((cache_like / "workflow.yaml").exists())
        cache_result = RULES.check(cache_like)
        self.assertEqual(cache_result["package_file_count"], result["package_file_count"])
        self.assertEqual(cache_result["package_total_bytes"], result["package_total_bytes"])

    def test_version_sync_and_upper_bound_package_limits(self):
        for rel in ("README.md", "AGENTS.md"):
            with self.subTest(stale_version_in=rel):
                path = self.root / rel
                original = path.read_text(encoding="utf-8")
                try:
                    path.write_text(original.replace("3.0.0", "2.0.0"), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "version_mismatch"):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

        p = self.root / "workflow/extra-drift-0.md"
        p.write_text("# extra\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(AssertionError, "package_files_exceeded"):
                RULES.check(self.root)
        finally:
            if p.exists():
                p.unlink()

        lic = self.root / "LICENSE"
        orig_lic = lic.read_bytes()
        lic.unlink()
        try:
            with self.assertRaisesRegex(AssertionError, "required_package_file_missing"):
                RULES.check(self.root)
        finally:
            lic.write_bytes(orig_lic)

    def test_managed_block_drift_and_tree_purity_enforced(self):
        agents_path = self.root / "AGENTS.md"
        orig_agents = agents_path.read_text(encoding="utf-8")
        try:
            agents_path.write_text(
                orig_agents.replace("## 需求协作入口", "## 需求协作入口（手工漂移）"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "project_entry_managed_block_drift"):
                RULES.check(self.root)
        finally:
            agents_path.write_text(orig_agents, encoding="utf-8")

        for dirty_rel in ("workflow/.DS_Store", "skills/bug-fixing/junk.pyc"):
            dirty = self.root / dirty_rel
            dirty.write_bytes(b"dirty")
            try:
                with self.assertRaisesRegex(AssertionError, "dirty_package_artifact_present"):
                    RULES.check(self.root)
            finally:
                dirty.unlink()

        empty_dir = self.root / "skills/requirement-analysis/empty_leftover"
        empty_dir.mkdir()
        try:
            with self.assertRaisesRegex(AssertionError, "empty_package_directory_present"):
                RULES.check(self.root)
        finally:
            empty_dir.rmdir()

    def test_gfm_heading_anchors_and_full_package_link_reachability(self):
        anchors = RULES._heading_anchors(
            "# Title\n"
            "## GitHub/Git URL 获取\n"
            "### 1. 先定模块边界与契约，再拆实施单元 ###\n"
            "## `Spec Gate`（单次确认）\n"
            "## 重复标题\n"
            "## 重复标题\n"
            "```markdown\n## 代码块内假标题\n```\n"
            "<!-- ## 注释内假标题 -->\n"
        )
        self.assertIn("title", anchors)
        self.assertIn("githubgit-url-获取", anchors)
        self.assertIn("1-先定模块边界与契约再拆实施单元", anchors)
        self.assertIn("spec-gate单次确认", anchors)
        self.assertIn("重复标题", anchors)
        self.assertIn("重复标题-1", anchors)
        self.assertNotIn("代码块内假标题", anchors)
        self.assertNotIn("注释内假标题", anchors)

        routing = self.root / "workflow/routing.md"
        orig_routing = routing.read_text(encoding="utf-8")
        try:
            routing.write_text(orig_routing + "\n参见 [不存在文件](absent-design-method.md)\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "linked_rule_missing"):
                RULES.check(self.root)

            routing.write_text(orig_routing + "\n参见 [断锚点](execution-contract.md#不存在的锚点)\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "linked_anchor_missing"):
                RULES.check(self.root)

            routing.write_text(orig_routing + "\n参见 [页内断锚点](#本页不存在锚点)\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "linked_anchor_missing"):
                RULES.check(self.root)

            routing.write_text(
                orig_routing + "\n示例：`[假链接](missing.md#bad)`\n```md\n[代码块假链接](missing2.md#bad)\n```\n",
                encoding="utf-8",
            )
            RULES.check(self.root)
        finally:
            routing.write_text(orig_routing, encoding="utf-8")

    def test_spec_template_forbids_mutable_status_header_and_requires_sections(self):
        spec_tpl = self.root / "templates/spec.md"
        original = spec_tpl.read_text(encoding="utf-8")
        for forbidden in ("阶段状态", "批准记录", "结论状态"):
            with self.subTest(forbidden=forbidden):
                try:
                    spec_tpl.write_text(f"> **{forbidden}**：`pending_approval`\n" + original, encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "spec_template_mutable_status_forbidden"):
                        RULES.check(self.root)
                finally:
                    spec_tpl.write_text(original, encoding="utf-8")

        for heading in ("## 1. 目标、边界与验收标准", "## 2. 架构取舍、接口契约与单元切分"):
            with self.subTest(missing_heading=heading):
                try:
                    spec_tpl.write_text(original.replace(heading, "## 已篡改章节"), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "spec_template_section_missing|linked_anchor_missing"):
                        RULES.check(self.root)
                finally:
                    spec_tpl.write_text(original, encoding="utf-8")

    def test_orthogonal_templates_and_retired_assets_enforced(self):
        for rel in RULES.RETIRED_PATHS:
            with self.subTest(retired=rel):
                path = self.root / rel
                existed_dirs = []
                cur = path.parent
                while not cur.exists():
                    existed_dirs.append(cur)
                    cur = cur.parent
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# stale\n", encoding="utf-8")
                try:
                    with self.assertRaisesRegex(AssertionError, "retired_path_present"):
                        RULES.check(self.root)
                finally:
                    path.unlink()
                    for d in existed_dirs:
                        if d.exists() and not any(d.iterdir()):
                            d.rmdir()

        spec_tpl = self.root / "templates/spec.md"
        original = spec_tpl.read_text(encoding="utf-8")
        try:
            for checkbox in ["- [ ] 待办", "* [ ] 待办", "1. [ ] 有序待办", "> - [x] 引用中的任务"]:
                with self.subTest(checkbox=checkbox):
                    spec_tpl.write_text(original + "\n" + checkbox + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "non_task_template_checkbox_forbidden"):
                        RULES.check(self.root)
        finally:
            spec_tpl.write_text(original, encoding="utf-8")

    def test_obsolete_dual_gate_and_dead_terms_rejected_globally(self):
        target = self.root / "skills/requirement-analysis/SKILL.md"
        original = target.read_text(encoding="utf-8")
        try:
            for term in RULES.OBSOLETE_WORKFLOW_TERMS:
                with self.subTest(term=term):
                    target.write_text(original + f"\n遗留词：{term}\n", encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "obsolete_workflow_term"):
                        RULES.check(self.root)
        finally:
            target.write_text(original, encoding="utf-8")

    def test_key_mechanism_identifiers_and_topological_pointers_enforced(self):
        exec_path = self.root / "workflow/execution-contract.md"
        orig_exec = exec_path.read_text(encoding="utf-8")
        try:
            for state in RULES.STAGE_STATES_FULL:
                with self.subTest(state=state):
                    exec_path.write_text(orig_exec.replace(state, "removed_state"), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "stage_state_missing"):
                        RULES.check(self.root)
        finally:
            exec_path.write_text(orig_exec, encoding="utf-8")

        identifier_cases = [
            ("workflow/routing.md", "Spec Gate", "spec_gate_identifier_missing"),
            ("skills/setup-requirement-workflow/assets/templates/claude-entry.md", "Spec Gate", "spec_gate_identifier_missing"),
            ("skills/feature-development/SKILL.md", "Spike", "spike_identifier_missing"),
            ("skills/feature-development/references/development-principles.md", "Contract-First", "contract_first_sdd_identifier_missing"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "accepted:true", "async_receipt_identifier_missing"),
            ("workflow/handoff.md", "sessionID", "session_isolation_identifier_missing"),
            ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", "verify_feature.py", "verify_feature_gate_missing"),
        ]
        for rel, token, err in identifier_cases:
            with self.subTest(rel=rel, token=token):
                p = self.root / rel
                orig = p.read_text(encoding="utf-8")
                try:
                    p.write_text(orig.replace(token, "removed_token"), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, err):
                        RULES.check(self.root)
                finally:
                    p.write_text(orig, encoding="utf-8")

        pointer_cases = [
            ("skills/requirement-analysis/SKILL.md", "../../templates/spec.md", "../../workflow/documents.md", "spec_or_task_template_pointer_missing"),
            ("skills/feature-development/SKILL.md", "../../templates/spec.md", "../../workflow/documents.md", "spec_or_task_template_pointer_missing"),
            ("agents/product-agent.md", "execution-contract.md#人工确认", "execution-contract.md", "confirmation_pointer_missing"),
            ("skills/feature-development/SKILL.md", "execution-contract.md#契约先行与分层验证", "execution-contract.md", "contract_verification_pointer_missing"),
            ("workflow/routing.md", "host-adapters.md#业务派发与降级路径", "execution-contract.md", "professional_delegation_pointer_missing"),
            ("workflow/host-adapters.md", "../skills/setup-requirement-workflow/references/agents-md-adapter.md#非具名独立协作", "../workflow/routing.md", "professional_delegation_pointer_missing"),
        ]
        for rel, ptr, replacement, err in pointer_cases:
            with self.subTest(rel=rel, pointer=ptr):
                p = self.root / rel
                orig = p.read_text(encoding="utf-8")
                try:
                    p.write_text(orig.replace(ptr, replacement), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, err):
                        RULES.check(self.root)
                finally:
                    p.write_text(orig, encoding="utf-8")

    def test_runtime_hash_dead_words_self_reread_and_entry_limits(self):
        for rel, bad_text in (
            ("agents/testing-agent.md", "\n每次启动运行 scripts/package_digest.py 计算哈希\n"),
            ("skills/setup-requirement-workflow/assets/templates/role-body.md", "\n读取 codex-bootstrap.local.json 回执\n"),
            ("skills/setup-requirement-workflow/references/agents-md-adapter.md", "\n记录 native_role_probes 状态\n"),
        ):
            path = self.root / rel
            orig = path.read_text(encoding="utf-8")
            try:
                path.write_text(orig + bad_text, encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "runtime_hash_or_receipt_dead_word"):
                    RULES.check(self.root)
            finally:
                path.write_text(orig, encoding="utf-8")

        agent_path = self.root / "agents/testing-agent.md"
        orig_agent = agent_path.read_text(encoding="utf-8")
        try:
            agent_path.write_text(orig_agent + "\n先读 SKILL.md 再执行\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "subagent_self_reread_forbidden"):
                RULES.check(self.root)

            agent_path.write_text(orig_agent + "\n" * 20, encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "agent_lines_exceeded"):
                RULES.check(self.root)
        finally:
            agent_path.write_text(orig_agent, encoding="utf-8")

        entry_path = self.root / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        orig_entry = entry_path.read_text(encoding="utf-8")
        orig_agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        try:
            entry_path.write_text(orig_entry + "\n" * 10, encoding="utf-8")
            self._sync_agents_managed_block()
            with self.assertRaisesRegex(AssertionError, "entry_lines_exceeded"):
                RULES.check(self.root)

            entry_path.write_text(
                orig_entry.replace("<!-- requirement-workflow:end -->", "填充" * 60 + "\n<!-- requirement-workflow:end -->"),
                encoding="utf-8",
            )
            self._sync_agents_managed_block()
            with self.assertRaisesRegex(AssertionError, "entry_bytes_exceeded"):
                RULES.check(self.root)

            entry_path.write_text(
                orig_entry.replace("<!-- requirement-workflow:end -->", "参见 [路由](workflow/routing.md)\n<!-- requirement-workflow:end -->"),
                encoding="utf-8",
            )
            self._sync_agents_managed_block()
            with self.assertRaisesRegex(AssertionError, "entry_forbids_consumer_relative_links"):
                RULES.check(self.root)

            entry_path.write_text(
                orig_entry.replace("## 需求协作入口", "## 需求协作入口（协议 5）"),
                encoding="utf-8",
            )
            self._sync_agents_managed_block()
            with self.assertRaisesRegex(AssertionError, "ceremonial_entry_label_forbidden"):
                RULES.check(self.root)
        finally:
            entry_path.write_text(orig_entry, encoding="utf-8")
            (self.root / "AGENTS.md").write_text(orig_agents, encoding="utf-8")

    def test_confirmation_hard_cap_table_checkbox_and_self_check_filler_banned(self):
        for cap in ("≤ 5 条", "<= 5 items", "最多 5 项", "五条以内"):
            for rel in ("templates/task.md", "templates/spec.md", "workflow/documents.md"):
                with self.subTest(cap=cap, path=rel):
                    path = self.root / rel
                    original = path.read_text(encoding="utf-8")
                    try:
                        path.write_text(original + f"\n本次请确认（{cap}）\n", encoding="utf-8")
                        with self.assertRaisesRegex(AssertionError, "confirmation_hard_cap_forbidden"):
                            RULES.check(self.root)
                    finally:
                        path.write_text(original, encoding="utf-8")

        for rel, bad, pattern in (
            ("templates/spec.md", "\n- **起草者自查**：已核对\n", "template_self_check_filler_forbidden"),
            ("templates/task.md", "\n## 自查清单\n", "template_self_check_filler_forbidden"),
            ("templates/spec.md", "\n| [ ] T1 | foo |\n", "table_checkbox_forbidden"),
        ):
            with self.subTest(path=rel, bad=bad):
                path = self.root / rel
                original = path.read_text(encoding="utf-8")
                try:
                    path.write_text(original + bad, encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, pattern):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_equal_or_larger_rules_only_fail_when_reduction_is_requested(self):
        baseline = Path(self.scratch.name).resolve() / "baseline"
        shutil.copytree(self.root, baseline)
        rules = self.root / "skills/feature-development/SKILL.md"
        rules.write_text(rules.read_text(encoding="utf-8") + "\n补充说明。\n", encoding="utf-8")
        result = RULES.check(self.root, baseline)
        self.assertGreater(
            result["selected_rule_utf8_bytes"]["after"],
            result["selected_rule_utf8_bytes"]["before"],
        )
        with self.assertRaisesRegex(AssertionError, "rule_size_not_reduced"):
            RULES.check(self.root, baseline, require_smaller=True)

    def test_protocol_and_optimizations_enforced(self):
        fw = self.root / "framework.yaml"
        orig_fw = fw.read_text(encoding="utf-8")
        try:
            fw.write_text(orig_fw.replace("protocol_version: 5", "protocol_version: 4"), encoding="utf-8")
            with self.assertRaises(AssertionError):
                RULES.check(self.root)
        finally:
            fw.write_text(orig_fw, encoding="utf-8")

        lock = self.root / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml"
        orig_lock = lock.read_text(encoding="utf-8")
        try:
            lock.write_text(orig_lock.replace("protocol_version: 5", "protocol_version: 4"), encoding="utf-8")
            with self.assertRaises(AssertionError):
                RULES.check(self.root)
        finally:
            lock.write_text(orig_lock, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "-O", str(ROOT / "scripts/verify-rule-loading.py"), "--source-root", str(self.root)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assertions required", result.stderr)


if __name__ == "__main__":
    unittest.main()
