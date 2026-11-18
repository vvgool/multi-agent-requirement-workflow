"""Source-contract regression for Protocol 4 light-kernel rules."""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rule_loading", ROOT / "scripts/verify-rule-loading.py"
)
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)


class RuleLoadingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "source"
        self.root.mkdir()
        for name in ["framework.yaml", "AGENTS.md", "README.md", "workflow.yaml", "LICENSE"]:
            shutil.copyfile(ROOT / name, self.root / name)
        ignore = shutil.ignore_patterns("system", "__pycache__", "*.pyc", ".DS_Store")
        for name in ["agents", "skills", "workflow", "templates"]:
            shutil.copytree(ROOT / name, self.root / name, ignore=ignore)

    def test_protocol4_source_and_size_budgets(self):
        self.assertEqual(RULES.MAX_PACKAGE_FILES, 58)
        self.assertEqual(RULES.MAX_PACKAGE_BYTES, 162373)
        result = RULES.check(self.root)
        self.assertEqual(result["framework"]["protocol_version"], 4)
        self.assertEqual(result["framework"]["version"], "1.0.1")
        self.assertLessEqual(result["entry_lines"], 60)
        self.assertLessEqual(result["package_file_count"], 58)
        self.assertLessEqual(result["package_total_bytes"], 162373)
        self.assertIsNone(result["selected_rule_utf8_bytes"]["before"])

    def test_runtime_hash_dead_words_and_agent_line_budget_enforced(self):
        for rel, bad_text in (
            ("agents/testing-agent.md", "\n每次启动运行 scripts/package_digest.py 计算哈希\n"),
            ("skills/setup-requirement-workflow/assets/templates/role-body.md", "\n读取 codex-bootstrap.local.json 回执\n"),
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
            agent_path.write_text(orig_agent + "\n" * 20, encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "agent_lines_exceeded"):
                RULES.check(self.root)
        finally:
            agent_path.write_text(orig_agent, encoding="utf-8")

    def test_ceremonial_framework_persona_labels_rejected(self):
        for rel, bad_text, pattern in (
            (
                "skills/setup-requirement-workflow/assets/templates/role-body.md",
                "你是需求协作框架（协议 4）的 {{role}}，当前宿主原生名称为 {{native_name}}。\n",
                "ceremonial_role_label_forbidden",
            ),
            (
                "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
                "\n<!-- 协议 4 轻内核 -->\n",
                "ceremonial_entry_label_forbidden",
            ),
            (
                "skills/setup-requirement-workflow/assets/templates/claude-entry.md",
                "\n<!-- 协议 4 -->\n",
                "ceremonial_claude_label_forbidden",
            ),
        ):
            path = self.root / rel
            orig = path.read_text(encoding="utf-8")
            try:
                path.write_text(bad_text + orig, encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, pattern):
                    RULES.check(self.root)
            finally:
                path.write_text(orig, encoding="utf-8")

    def test_entry_line_limit_and_relative_link_ban(self):
        path = self.root / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        original = path.read_text(encoding="utf-8")

        path.write_text(original + "\n" * 45, encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "entry_lines_exceeded"):
            RULES.check(self.root)

        path.write_text(original + "\n参见 [路由](workflow/routing.md)\n", encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "entry_forbids_consumer_relative_links"):
            RULES.check(self.root)
        path.write_text(original, encoding="utf-8")

    def test_clarification_and_async_receipts_need_real_approval(self):
        path = self.root / "workflow/execution-contract.md"
        original = path.read_text(encoding="utf-8")
        for guard in [
            "业务澄清不等于需求批准",
            "提问受理不等于用户答案",
            "等待真实用户回复后再判断批准",
            "需求确认后进入正式设计",
            "设计确认后实施",
            "批准不追溯覆盖",
        ]:
            with self.subTest(guard=guard):
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除确认守卫"), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_silent_cruise_whitelist_and_anti_drift_locks_cannot_be_removed(self):
        cases = [
            ("workflow/execution-contract.md", "中途打断白名单"),
            ("workflow/execution-contract.md", "只读回读"),
            ("workflow/execution-contract.md", "主会话单写"),
            ("workflow/execution-contract.md", "干净子上下文"),
            ("workflow/execution-contract.md", "连续 2～3 次修复失败且未缩小根因范围时立即熔断停手"),
            ("workflow/execution-contract.md", "内部验收自闭环"),
            ("skills/bug-fixing/references/systematic-debugging.md", "连续 2～3 次修改仍失败且未缩小根因范围时，立即触发盲修熔断"),
            ("skills/feature-development/references/architecture-review.md", "遗漏的 AC"),
            ("skills/feature-development/references/architecture-review.md", "擅自扩权范围"),
            ("skills/feature-development/references/architecture-review.md", "模块契约冲突"),
            ("skills/feature-development/references/architecture-review.md", "未证实假设与边界风险"),
            ("skills/acceptance-testing/references/completion-gate.md", "破坏性反例"),
        ]
        for rel, guard in cases:
            with self.subTest(path=rel, guard=guard):
                path = self.root / rel
                original = path.read_text(encoding="utf-8")
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除防偏航守卫"), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_first_principles_contracts_cannot_be_removed(self):
        cases = [
            ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", "穿透 XY 表象"),
            ("AGENTS.md", "穿透 XY 表象"),
            ("workflow/execution-contract.md", "穿透 XY 表象"),
            ("workflow/execution-contract.md", "先删减简化、再机械下沉"),
            ("workflow/execution-contract.md", "拒绝经验类比盲试"),
            ("skills/requirement-analysis/references/clarification.md", "穿透 XY 问题"),
            ("skills/requirement-analysis/references/clarification.md", "根本矛盾"),
            ("skills/requirement-analysis/assets/templates/requirements.md", "表面解法"),
            ("skills/feature-development/references/design-and-decomposition.md", "先删减、再下沉、后新增"),
            ("skills/feature-development/references/design-and-decomposition.md", "机械约束下沉"),
            ("skills/feature-development/assets/templates/technical-design.md", "先删减、再下沉、后新增"),
            ("skills/feature-development/references/architecture-review.md", "第一性原理与防叠补丁"),
            ("skills/bug-fixing/references/systematic-debugging.md", "拒绝经验类比盲试"),
            ("skills/bug-fixing/references/systematic-debugging.md", "破坏不变量"),
        ]
        for rel, guard in cases:
            with self.subTest(path=rel, guard=guard):
                path = self.root / rel
                original = path.read_text(encoding="utf-8")
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除第一性原理守卫"), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_confirmation_consumers_need_the_authoritative_pointer(self):
        for name in [
            *[f"agents/{role}-agent.md" for role in ["coordinator", "product", "development", "testing", "bug"]],
            *[f"skills/{stage}/SKILL.md" for stage in ["requirement-analysis", "feature-development", "acceptance-testing", "bug-fixing"]],
        ]:
            with self.subTest(path=name):
                path = self.root / name
                original = path.read_text(encoding="utf-8")
                pointer = "execution-contract.md#人工确认"
                self.assertIn(pointer, original)
                try:
                    path.write_text(original.replace(pointer, "execution-contract.md"), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_professional_delegation_loading_chain_cannot_be_removed(self):
        cases = [
            ("agents/coordinator-agent.md", "../workflow/routing.md", "../workflow/execution-contract.md"),
            ("workflow/routing.md", "host-adapters.md#业务派发与降级路径", "execution-contract.md"),
            (
                "workflow/host-adapters.md",
                "../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作",
                "../skills/setup-requirement-workflow/references/codex-adapter.md",
            ),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "对应包内角色和完整Skill路径", "父会话摘要"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "实际工具支持独立上下文时选择独立上下文", "总是继承父会话"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "父会话回读真实子任务标识、父子关系、加载与执行证据及结果", "父会话只看PASS"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "缺独立上下文、必要加载或实际结果时，受影响审查/验收仍阻塞", "缺加载也可继续"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md", "不将其计为具名激活探测通过", "通用子会话即具名激活"),
            ("skills/setup-requirement-workflow/assets/templates/role-body.md", "读取 `<缓存根>/{{role_file}}` 与完整 `<缓存根>/{{skill_file}}`", "只看角色名"),
        ]
        for name, guard, replacement in cases:
            with self.subTest(path=name, guard=guard):
                path = self.root / name
                original = path.read_text(encoding="utf-8")
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, replacement), encoding="utf-8")
                    with self.assertRaisesRegex(AssertionError, "professional_delegation_"):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_obsolete_confirmation_bypass_is_rejected(self):
        path = self.root / "skills/requirement-analysis/SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n小需求目标清楚即可执行，不强制再写需求稿和统一批准。\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AssertionError, "obsolete_confirmation_bypass"):
            RULES.check(self.root)

    def test_equal_or_larger_rules_only_fail_when_reduction_is_requested(self):
        baseline = Path(self.scratch.name) / "baseline"
        shutil.copytree(self.root, baseline)
        rules = self.root / "skills/feature-development/SKILL.md"
        rules.write_text(rules.read_text(encoding="utf-8") + "\n补充必要说明。\n", encoding="utf-8")
        result = RULES.check(self.root, baseline)
        self.assertGreater(
            result["selected_rule_utf8_bytes"]["after"],
            result["selected_rule_utf8_bytes"]["before"],
        )
        with self.assertRaisesRegex(AssertionError, "rule_size_not_reduced"):
            RULES.check(self.root, baseline, require_smaller=True)

    def test_unknown_or_mismatched_protocol_fails(self):
        path = self.root / "framework.yaml"
        path.write_text(
            path.read_text(encoding="utf-8").replace("protocol_version: 4", "protocol_version: 99"),
            encoding="utf-8",
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_broken_link_in_shared_workflow_is_detected(self):
        path = self.root / "workflow/routing.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n[缺失文件](absent-design-method.md)\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AssertionError, "linked_rule_missing"):
            RULES.check(self.root)

    def test_second_progress_checklist_in_non_task_template_fails(self):
        path = self.root / "skills/feature-development/assets/templates/technical-design.md"
        original = path.read_text(encoding="utf-8")
        for checkbox in ["- [ ] 待办", "* [ ] 待办", "1. [ ] 有序待办", "> - [x] 引用中的任务"]:
            with self.subTest(checkbox=checkbox):
                path.write_text(original + "\n" + checkbox + "\n", encoding="utf-8")
                with self.assertRaises(AssertionError):
                    RULES.check(self.root)

    def test_template_set_is_five_orthogonal_templates_and_old_paths_retired(self):
        result = RULES.check(self.root)
        self.assertLessEqual(result["package_file_count"], 58)
        self.assertLess(result["package_total_bytes"], 162373)
        for rel in RULES.RETIRED_TEMPLATES:
            with self.subTest(retired=rel):
                path = self.root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# stale\n阶段状态\n", encoding="utf-8")
                try:
                    with self.assertRaisesRegex(AssertionError, "retired_template_present"):
                        RULES.check(self.root)
                finally:
                    path.unlink()

    def test_confirmation_hard_cap_and_self_check_filler_cannot_return(self):
        caps = [
            "≤ 5 条", "≤5条", "<= 5 条", "≤５条", "≤ 5 个", "≤ 5 项", "≤5 questions", "<=5 Qs",
            "不超过5条", "不得超过 5 个必答项", "最多 5 项", "最多5条", "至多5条", "上限 5 条",
            "五条以内", "5 条以内", "≦5条", "no more than 5 items", "at most 5 items", "max 5 items",
        ]
        for cap in caps:
            for rel in ("templates/task.md", "workflow/documents.md", "README.md", "AGENTS.md"):
                with self.subTest(cap=cap, path=rel):
                    path = self.root / rel
                    original = path.read_text(encoding="utf-8")
                    try:
                        path.write_text(original + f"\n本次请确认（{cap}）\n", encoding="utf-8")
                        with self.assertRaisesRegex(AssertionError, "confirmation_hard_cap_forbidden"):
                            RULES.check(self.root)
                    finally:
                        path.write_text(original, encoding="utf-8")
        for ok in ("≤ 100 行", "最多 50 项", "至多生效一次", "≤ 15 条"):
            with self.subTest(allowed=ok):
                self.assertIsNone(RULES.HARD_CAP.search(ok))

        for rel, bad, pattern in (
            ("skills/requirement-analysis/assets/templates/requirements.md", "\n- **起草者自查**：已核对\n", "template_self_check_filler_forbidden"),
            ("templates/task.md", "\n## 自查清单\n", "template_self_check_filler_forbidden"),
            ("skills/requirement-analysis/assets/templates/requirements.md", "\n作者自检：ok\n", "template_self_check_filler_forbidden"),
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

        boxes = ["| a | [ ] | b |", "|[x]|", "| [ ] T1 | foo |", "| - [ ] T1 | foo |", "| x | [ ]", "| <br>- [ ] x |"]
        for box in boxes:
            for rel in (
                "skills/acceptance-testing/assets/templates/verification.md",
                "skills/feature-development/assets/templates/technical-design.md",
                "templates/task.md",
            ):
                with self.subTest(box=box, path=rel):
                    path = self.root / rel
                    original = path.read_text(encoding="utf-8")
                    try:
                        path.write_text(original + "\n" + box + "\n", encoding="utf-8")
                        with self.assertRaisesRegex(AssertionError, "table_checkbox_forbidden"):
                            RULES.check(self.root)
                    finally:
                        path.write_text(original, encoding="utf-8")
        for ok in ("| [P] |", "| T1 [P] |", "| [AC-01] |", "| [Q1 | x] |"):
            with self.subTest(allowed=ok):
                self.assertIsNone(RULES.TABLE_CHECKBOX.search(ok))

    def test_anchors_single_writer_and_approval_roundtrip_guards(self):
        for rel, guard in (
            ("templates/task.md", "requirements.md#功能与验收标准"),
            ("skills/requirement-analysis/assets/templates/requirements.md", "## 功能与验收标准"),
            ("skills/feature-development/assets/templates/technical-design.md", "## 文件变更与单元切分"),
            ("skills/feature-development/assets/templates/technical-design.md", "## 接口签名与异常契约"),
            ("workflow/handoff.md", "technical-design.md#接口签名与异常契约"),
            ("workflow/handoff.md", "验证报告唯一写入人"),
            ("workflow/documents.md", "验证报告唯一写入人"),
            ("skills/acceptance-testing/SKILL.md", "验证报告唯一写入人"),
            ("workflow/documents.md", "临时恢复"),
        ):
            with self.subTest(path=rel, guard=guard):
                path = self.root / rel
                original = path.read_text(encoding="utf-8")
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除守卫"), encoding="utf-8")
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_lock_template_protocol_must_match_source(self):
        path = self.root / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml"
        path.write_text(
            path.read_text(encoding="utf-8").replace("protocol_version: 4", "protocol_version: 3"),
            encoding="utf-8",
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_optimized_python_cannot_disable_the_checks(self):
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                str(ROOT / "scripts/verify-rule-loading.py"),
                "--source-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assertions required", result.stderr)


if __name__ == "__main__":
    unittest.main()
