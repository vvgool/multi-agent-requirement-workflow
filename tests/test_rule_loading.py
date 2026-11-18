"""Source-contract regression; these checks do not run a native agent."""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
        for name in ["framework.yaml", "AGENTS.md"]:
            shutil.copyfile(ROOT / name, self.root / name)
        for name in ["agents", "skills", "workflow", "templates"]:
            shutil.copytree(ROOT / name, self.root / name)

    def test_current_source_does_not_need_a_size_baseline(self):
        result = RULES.check(self.root)
        self.assertEqual(result["framework"]["protocol_version"], 3)
        self.assertIsNone(result["selected_rule_utf8_bytes"]["before"])

    def test_confirmation_contract_is_part_of_static_checks(self):
        self.assertIn("separate-human-confirmations", RULES.check(self.root)["scenarios"])

    def test_clarification_and_async_receipts_need_real_approval(self):
        path = self.root / "workflow/execution-contract.md"
        original = path.read_text()
        for guard in [
            "业务澄清不等于需求批准",
            "提问受理不等于用户答案",
            "等待真实用户回复后再判断批准",
        ]:
            with self.subTest(guard=guard):
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除答复边界"))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_distributed_entry_stops_at_confirmation_request(self):
        path = self.root / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        original = path.read_text()
        guard = "以确认问题结束本轮，等待真实用户回复"
        self.assertIn(guard, original)
        path.write_text(original.replace(guard, "确认工具返回即可继续"))
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_confirmation_boundary_cannot_be_removed(self):
        path = self.root / "workflow/execution-contract.md"
        original = path.read_text()
        for guard in ["需求确认后进入正式设计", "设计确认后实施", "批准不追溯覆盖"]:
            with self.subTest(guard=guard):
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除确认边界"))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_stateful_design_review_applicability_is_required(self):
        cases = [
            ("workflow/routing.md", "单一服务或文件少不能作为免审依据"),
            ("workflow/execution-contract.md", "设计确认前核对审查适用性"),
            ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
             "状态性设计先按路由核对审查适用性"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "accepted:true"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "仅证明问题已受理"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "核对后续真实用户答案"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "execution-contract.md#人工确认"),
        ]
        for name, guard in cases:
            with self.subTest(path=name, guard=guard):
                path = self.root / name
                original = path.read_text()
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除适用性边界"))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_confirmation_consumers_need_the_authoritative_pointer(self):
        for name in [
            "workflow/routing.md", "workflow/handoff.md", "workflow/bugfix.md",
            *[f"agents/{role}-agent.md" for role in
              ["coordinator", "product", "development", "testing", "bug"]],
            *[f"skills/{stage}/SKILL.md" for stage in
              ["requirement-analysis", "feature-development", "acceptance-testing", "bug-fixing"]],
        ]:
            with self.subTest(path=name):
                path = self.root / name
                original = path.read_text()
                pointer = "execution-contract.md#人工确认"
                self.assertIn(pointer, original)
                try:
                    path.write_text(original.replace(pointer, "execution-contract.md"))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_professional_delegation_loading_chain_cannot_be_removed(self):
        cases = [
            ("agents/coordinator-agent.md", "../workflow/routing.md",
             "../workflow/execution-contract.md"),
            ("workflow/routing.md", "host-adapters.md", "execution-contract.md"),
            ("workflow/host-adapters.md",
             "../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作",
             "../skills/setup-requirement-workflow/references/codex-adapter.md"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "对应包内角色和完整Skill路径", "父会话摘要"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "实际工具支持独立上下文时选择独立上下文", "总是继承父会话"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "子会话自己核对包身份、读取对应角色和完整Skill", "沿用父会话加载结论"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "父会话回读真实子任务标识、父子关系、加载与执行证据及结果", "父会话只看PASS"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "缺独立上下文、必要加载或实际结果时，受影响审查/验收仍阻塞", "缺加载也可继续"),
            ("skills/setup-requirement-workflow/references/codex-adapter.md",
             "不将其计为具名激活探测通过", "通用子会话即具名激活"),
            ("skills/setup-requirement-workflow/assets/templates/role-body.md",
             "读取锁定包内 {{role_file}} 和完整 {{skill_file}}", "只看角色名"),
        ]
        for name, guard, replacement in cases:
            with self.subTest(path=name, guard=guard):
                path = self.root / name
                original = path.read_text()
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, replacement))
                    with self.assertRaisesRegex(
                        AssertionError, "professional_delegation_"
                    ):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_fallback_contract_must_remain_in_its_linked_section(self):
        path = self.root / "skills/setup-requirement-workflow/references/codex-adapter.md"
        original = path.read_text()
        start = original.index("### 无具名选择参数时的业务独立协作\n")
        end = original.index("\n### ", start + 1)
        section = original[start:end]
        replacements = [""]
        for level in [1, 2, 3]:
            replacements.append(
                "### 无具名选择参数时的业务独立协作\n\n见其他说明。\n"
                + "\n" + "#" * level + " 历史示例\n"
                + section.split("\n", 1)[1]
            )
        for replacement in replacements:
            with self.subTest(replacement=replacement[:40]):
                try:
                    path.write_text(original[:start] + replacement + original[end:])
                    with self.assertRaisesRegex(
                        AssertionError, "professional_delegation_"
                    ):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_obsolete_confirmation_bypass_is_rejected(self):
        path = self.root / "skills/requirement-analysis/SKILL.md"
        path.write_text(path.read_text() + "\n小需求目标清楚即可执行，不强制再写需求稿和统一批准。\n")
        with self.assertRaisesRegex(AssertionError, "obsolete_confirmation_bypass"):
            RULES.check(self.root)

    def test_equal_or_larger_rules_only_fail_when_reduction_is_requested(self):
        baseline = Path(self.scratch.name) / "baseline"
        shutil.copytree(self.root, baseline)
        rules = self.root / "skills/feature-development/SKILL.md"
        rules.write_text(rules.read_text() + "\n补充必要说明。\n")
        result = RULES.check(self.root, baseline)
        self.assertGreater(
            result["selected_rule_utf8_bytes"]["after"],
            result["selected_rule_utf8_bytes"]["before"],
        )
        with self.assertRaisesRegex(AssertionError, "rule_size_not_reduced"):
            RULES.check(self.root, baseline, require_smaller=True)

    def test_patch_version_is_read_from_metadata(self):
        path = self.root / "framework.yaml"
        original = RULES.check(self.root)["framework"]["version"]
        self.assertNotEqual(original, "99.0.0")
        path.write_text(path.read_text().replace(f'"{original}"', '"99.0.0"'))
        self.assertEqual(RULES.check(self.root)["framework"]["version"], "99.0.0")

    def test_unknown_or_mismatched_protocol_fails(self):
        path = self.root / "framework.yaml"
        path.write_text(
            path.read_text().replace("protocol_version: 3", "protocol_version: 99")
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_missing_document_format_pointer_fails(self):
        path = self.root / "skills/feature-development/SKILL.md"
        path.write_text(
            path.read_text().replace(
                "../../workflow/documents.md", "../../workflow/absent.md"
            )
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_evidence_free_retry_allowance_is_rejected(self):
        path = self.root / "skills/bug-fixing/references/systematic-debugging.md"
        path.write_text(
            path.read_text().replace(
                "没有改变假设、失败类别或验证范围时停止修改",
                "三次没有新证据的失败后停止盲改",
            )
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_native_receipt_requires_actual_child_relationship(self):
        path = self.root / "skills/setup-requirement-workflow/SKILL.md"
        path.write_text(
            path.read_text().replace("回读宿主实际子任务记录", "仅看命令成功")
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_root_and_distributed_entry_guards_are_required(self):
        for name in [
            "AGENTS.md",
            "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
        ]:
            path = self.root / name
            original = path.read_text()
            for guard in ["**修改前判断**", "不执行或实现自动重放、补偿"]:
                with self.subTest(path=name, guard=guard):
                    path.write_text(original.replace(guard, "已移除守卫"))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
            path.write_text(original)

    def test_pstack_lightweight_contracts_are_required(self):
        cases = [
            (
                "skills/acceptance-testing/references/completion-gate.md",
                "无适用反例",
            ),
            (
                "skills/feature-development/references/design-and-decomposition.md",
                "不建立阶段状态",
            ),
            (
                "skills/acceptance-testing/assets/templates/test-report.md",
                "按需证据绑定",
            ),
        ]
        for relative_path, guard in cases:
            with self.subTest(path=relative_path, guard=guard):
                path = self.root / relative_path
                original = path.read_text()
                self.assertIn(guard, original)
                try:
                    path.write_text(original.replace(guard, "已移除候选守卫", 1))
                    with self.assertRaises(AssertionError):
                        RULES.check(self.root)
                finally:
                    path.write_text(original)

    def test_missing_stage_template_fails(self):
        (
            self.root / "skills/feature-development/assets/templates/technical-plan.md"
        ).unlink()
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_missing_linked_design_method_is_detected(self):
        (
            self.root
            / "skills/feature-development/references/design-and-decomposition.md"
        ).unlink()
        with self.assertRaisesRegex(AssertionError, "linked_rule_missing"):
            RULES.check(self.root)

    def test_broken_link_in_shared_workflow_is_detected(self):
        path = self.root / "workflow/routing.md"
        path.write_text(
            path.read_text() + "\n[必要设计方法](absent-design-method.md)\n"
        )
        with self.assertRaisesRegex(AssertionError, "linked_rule_missing"):
            RULES.check(self.root)

    def test_external_links_and_document_fragments_are_not_file_paths(self):
        path = self.root / "workflow/routing.md"
        path.write_text(
            path.read_text()
            + "\n[外部](https://example.invalid/missing.md) [本页](#路径选择)\n"
        )
        RULES.check(self.root)

    def test_second_progress_checklist_fails(self):
        path = (
            self.root
            / "skills/feature-development/assets/templates/implementation-plan.md"
        )
        original = path.read_text()
        for checkbox in [
            "- [ ] 待办",
            "* [ ] 待办",
            "+ [ ] 待办",
            "  - [ ] 嵌套待办",
            "1. [ ] 有序待办",
            "> - [x] 引用中的任务",
            "- [ ]",
        ]:
            with self.subTest(checkbox=checkbox):
                path.write_text(original + "\n" + checkbox + "\n")
                with self.assertRaises(AssertionError):
                    RULES.check(self.root)

    def test_lock_template_protocol_must_match_source(self):
        path = (
            self.root
            / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml"
        )
        path.write_text(
            path.read_text().replace("protocol_version: 3", "protocol_version: 2")
        )
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_reduction_flag_needs_a_baseline(self):
        with self.assertRaisesRegex(AssertionError, "size_baseline_required"):
            RULES.check(self.root, require_smaller=True)

    def test_incomplete_size_baseline_is_rejected(self):
        baseline = Path(self.scratch.name) / "baseline"
        baseline.mkdir()
        with self.assertRaises(FileNotFoundError):
            RULES.check(self.root, baseline)

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
