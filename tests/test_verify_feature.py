"""Contract-First TDD tests for skills/acceptance-testing/scripts/verify_feature.py (AC-05, AC-06)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills/acceptance-testing/scripts/verify_feature.py"
LEGACY_FEATURE_DIR = ROOT / "agent-features/工作流最优收敛演进"
V3_SPEC_PATH = ROOT / "agent-features/工作流v3全局最优重构/spec.md"


def _load_verify_module():
    assert SCRIPT_PATH.is_file(), f"script_not_found: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("verify_feature", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    if not SCRIPT_PATH.is_file():
        return subprocess.CompletedProcess(
            args=[sys.executable, "-B", str(SCRIPT_PATH), *args],
            returncode=127,
            stdout="",
            stderr=json.dumps({"ok": False, "error": "script_missing"}),
        )
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _valid_regular_task(
    *,
    state: str = "pending_approval",
    approval: str = "待确认",
    colon: str = "：",
    include_confirm_section: bool = True,
    tasks: str = "- [ ] T-01 [P] [AC-01]：实现导出逻辑\n- [ ] T2 [依赖 T1] [AC-01]：独立验收",
    table_rows: str = "| AC-01 空表导出 | 未执行 | 待运行 `python3 -m unittest` |",
    blocker: str = "无 <!-- 注释不应干扰无阻塞判定 -->",
    ac_line: str = "- **目标与验收标准（AC）**：AC-01 空表导出返回仅表头且退出码为 0",
) -> str:
    confirm_block = (
        "\n## 本次请确认\n- **[Q1 | 影响 AC-01] 分隔符**：推荐逗号\n"
        if include_confirm_section
        else ""
    )
    return (
        "# 常规导出优化\n\n"
        f"> **阶段状态**{colon}`{state}` <!-- 状态注释 -->\n"
        f"> **批准记录**{colon}{approval}\n\n"
        "**当前结论**：常规单文件事项测试。\n"
        f"{confirm_block}\n"
        "## 目标、AC 与文档\n"
        f"{ac_line}\n\n"
        "## 任务进度\n"
        f"{tasks}\n\n"
        "## 验证摘要与阻塞\n\n"
        "| 检查范围 | 状态 | 证据 |\n"
        "| --- | --- | --- |\n"
        f"{table_rows}\n\n"
        f"- **当前阻塞**{colon}{blocker}\n"
    )


def _valid_complex_spec(
    *,
    unit_rows: str = (
        "| **T1..T2**（可与 T3 并行） | `src/a.py` | `AC-01`：核心实现 | `python3 -m unittest` |\n"
        "| **T3**（依赖 T1, T2） | `src/b.py` | `AC-02`：边界处理 | `python3 -m unittest` |\n"
        "| **T4** (依赖 T3) | `verification.md` | `AC-01..02`：独立验收 | `python3 -m unittest` |"
    ),
    extra_body: str = "",
) -> str:
    return (
        "# 复杂事项规格：统一规格与架构契约（Spec）\n\n"
        "**核心结论**：状态统一由 `task.md` 维护（如 `阶段状态`、`批准记录`、`[x]`、`{{...}}` 仅在反引号内讨论）。\n\n"
        "---\n\n"
        "## 1. 目标、边界与验收标准\n\n"
        "| AC | 触发条件 | 预期结果 |\n"
        "| --- | --- | --- |\n"
        "| AC-01 | 正常请求 | 返回 200 |\n"
        "| AC-02 | 非法参数 | 返回 400 |\n\n"
        f"{extra_body}\n"
        "## 2. 架构取舍、接口契约与单元切分\n\n"
        "### 2.1 架构取舍\n\n"
        "| 编号 | 决策点 | 选定方案 | 放弃方案 | 关联 AC |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| D-01（影响 T1） | 存储 | 内存结构 | 外部依赖 | AC-01 |\n\n"
        "### 2.3 AC → 验证映射与实施单元切分\n\n"
        "| 单元与依赖 | 允许写入文件 | 关联 AC | 验证命令 |\n"
        "| --- | --- | --- | --- |\n"
        f"{unit_rows}\n"
    )


def _valid_verification_md(*, status: str = "通过", extra: str = "") -> str:
    return (
        "# 复杂事项：验证报告\n\n"
        f"> **验收结论状态**：`{status}` <!-- 通过 | 有条件通过 | 未完成 | 阻塞 -->\n"
        "> **写入人**：testing-agent\n\n"
        "**结论与证据摘要**：独立上下文实测通过（反例注入 `- [ ]` 或 `阶段状态` 均在反引号中记录）。\n\n"
        "## AC 与反例检查\n\n"
        "| 验收项 | 角色 | 命令 | 状态 | 证据 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| AC-01 | 独立验收 | `python3 -m unittest` | 通过 | `exit=0` |\n"
        f"{extra}\n"
    )


class VerifyFeatureGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_module_uses_only_stdlib_and_disables_bytecode(self):
        mod = _load_verify_module()
        self.assertTrue(sys.dont_write_bytecode)
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("sys.dont_write_bytecode = True", source)
        self.assertNotIn("import yaml", source)
        self.assertTrue(callable(getattr(mod, "strip_code_and_comments", None)))

    def test_cli_invalid_arguments_exit_2_with_single_line_json(self):
        for bad_args in (
            (),
            ("--phase", "spec-gate"),
            ("--feature-dir", str(self.base), "--phase", "spec-gate", "--check-writes"),
            ("--write-snapshot", str(self.base / "s.json")),
            ("--check-writes",),
        ):
            with self.subTest(args=bad_args):
                proc = _run_cli(*bad_args)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout.strip(), "")
                lines = proc.stderr.strip().splitlines()
                self.assertEqual(len(lines), 1)
                payload = json.loads(lines[0])
                self.assertIs(payload["ok"], False)
                self.assertIn("error", payload)

    def test_regular_feature_spec_gate_and_verified_and_missing_ac(self):
        fdir = self.base / "regular-feature"
        fdir.mkdir()
        (fdir / "task.md").write_text(_valid_regular_task(colon=": "), encoding="utf-8")

        res = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        out = json.loads(res.stdout.strip())
        self.assertIs(out["ok"], True)
        self.assertIs(out["complex"], False)

        # Missing AC in regular task.md must fail even if Q1 in 本次请确认 mentions AC-01
        (fdir / "task.md").write_text(
            _valid_regular_task(
                tasks="- [ ] T1：仅做修改\n- [ ] T2 [依赖 T1]：收口",
                table_rows="| 基本检查 | 未执行 | 待验证 |",
                ac_line="- **背景说明**：仅调整内部变量命名",
            ),
            encoding="utf-8",
        )
        bad_ac = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(bad_ac.returncode, 2)
        self.assertIn("missing_regular_ac", json.loads(bad_ac.stderr.strip())["error"])

        # Regular verified without spec.md or verification.md succeeds
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批准导出优化｜用户回复确认｜2026-11-19",
                colon=": ",
                include_confirm_section=False,
                tasks="- [x] T-01 [P] [AC-01]：实现导出逻辑\n- [X] T2 [依赖 T1] [AC-01]：独立验收",
                table_rows=(
                    "| AC-01 空表导出 | 通过 | `python3 -B -m unittest` 全绿 |\n"
                    "| 前端样式回归 | 不适用（纯后端 CLI 工具无前端界面） | 无 UI 变更 |"
                ),
                blocker="无",
            ),
            encoding="utf-8",
        )
        ver_res = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
        self.assertEqual(ver_res.returncode, 0, msg=ver_res.stderr)
        self.assertIs(json.loads(ver_res.stdout.strip())["ok"], True)

    def test_complex_feature_spec_gate_delta_ranges_and_pending_req_approval(self):
        fdir = self.base / "complex-feature"
        fdir.mkdir()
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="pending_approval",
                approval="初版已批｜2026-11-18；Δ 待确认",
                tasks=(
                    "- [x] T1 [AC-01]：初版实现\n"
                    "- [x] T-02 [依赖 T1] [AC-01]：初版验证\n"
                    "- [ ] T3 [依赖 T1, T2] [AC-02]：Δ 增量边界修复\n"
                    "- [ ] T4 [依赖 T3] [AC-01..02]：Δ 独立复验"
                ),
                ac_line="- **目标与验收标准（AC）**：见 `spec.md#1-目标边界与验收标准`\n- **文档**：`spec.md` ｜ `verification.md`",
                table_rows="| 初版闭环 | 通过 | `python3 -m unittest` |\n| Δ 边界复验 | 未执行 | 待执行 |",
            ),
            encoding="utf-8",
        )
        (fdir / "spec.md").write_text(_valid_complex_spec(), encoding="utf-8")

        res = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        payload = json.loads(res.stdout.strip())
        self.assertTrue(payload["complex"])

        # T1-T2 hyphen range expansion in spec.md also works
        (fdir / "spec.md").write_text(
            _valid_complex_spec(
                unit_rows=(
                    "| **T1-T2** | `src/a.py` | `AC-01` | `unittest` |\n"
                    "| **T3..T4**（依赖 T1, T2） | `src/b.py` | `AC-02` | `unittest` |"
                )
            ),
            encoding="utf-8",
        )
        self.assertEqual(_run_cli("--feature-dir", str(fdir), "--phase", "spec-gate").returncode, 0)

        # Unit mismatch between task.md {T1..T4} and spec.md {T1..T3}
        (fdir / "spec.md").write_text(
            _valid_complex_spec(
                unit_rows="| **T1..T3** | `src/a.py` | `AC-01` | `unittest` |"
            ),
            encoding="utf-8",
        )
        mismatch = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(mismatch.returncode, 2)
        self.assertIn("task_spec_unit_mismatch", json.loads(mismatch.stderr.strip())["error"])

        # All tasks already [x] in spec-gate is forbidden
        (fdir / "spec.md").write_text(_valid_complex_spec(), encoding="utf-8")
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="pending_approval",
                approval="初版已批；Δ 待确认",
                tasks="- [x] T1：a\n- [x] T2：b\n- [x] T3：c\n- [x] T4：d",
                ac_line="- **文档**：`spec.md`",
            ),
            encoding="utf-8",
        )
        all_checked = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(all_checked.returncode, 2)

        # pending_req_approval without unit table in spec.md §2 is allowed
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="pending_req_approval",
                approval="待确认",
                tasks="- [ ] T1：待需求边界锁定后拆分单元",
                ac_line="- **文档**：`spec.md`",
            ),
            encoding="utf-8",
        )
        (fdir / "spec.md").write_text(
            "# 超大事项规格\n\n## 1. 目标、边界与验收标准\n- AC-01：锁边界\n\n## 2. 架构取舍、接口契约与单元切分\n待需求确认后细化单元。\n",
            encoding="utf-8",
        )
        req_gate = _run_cli("--feature-dir", str(fdir), "--phase", "spec-gate")
        self.assertEqual(req_gate.returncode, 0, msg=req_gate.stderr)

    def test_markdown_stripping_fences_comments_and_p3a_inline_code(self):
        fdir = self.base / "strip-check"
        fdir.mkdir()
        fenced_and_comment_noise = (
            "<!--\n"
            "> **阶段状态**：`verified`\n"
            "{{未替换注释占位符}}\n"
            "- [ ] T999\n"
            "-->\n"
            "```markdown\n"
            "> **阶段状态**：`pending_approval`\n"
            "> **批准记录**：待确认\n"
            "{{代码块占位符}}\n"
            "- [ ] T888\n"
            "| 假表 | [x] | {{bad}} |\n"
            "```\n"
            "~~~\n"
            "### 结论状态：未完成\n"
            "- [x] T777\n"
            "~~~\n"
            "正文自指讨论：`> **批准记录**：待确认`、`{{模板占位符}}`、`[x]`、`- [ ]` 均在行内反引号中。\n"
        )
        (fdir / "spec.md").write_text(
            _valid_complex_spec(
                unit_rows="| **T1..T2** | `a.py` | `AC-01` | `unittest` |",
                extra_body=fenced_and_comment_noise,
            ),
            encoding="utf-8",
        )
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="批准｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：实现 `{{非占位符}}`\n- [x] T2 [依赖 T1]：核验 `[ ]` 反例",
                ac_line="- **文档**：`spec.md` ｜ `verification.md`",
                table_rows="| 核心检查 | 通过 | `verification.md` 记录 `[x]` 拦截实证 |",
            ),
            encoding="utf-8",
        )
        (fdir / "verification.md").write_text(
            _valid_verification_md(status="有条件通过", extra=fenced_and_comment_noise),
            encoding="utf-8",
        )
        ok_res = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
        self.assertEqual(ok_res.returncode, 0, msg=ok_res.stderr)

        (fdir / "spec.md").write_text(
            _valid_complex_spec(
                unit_rows="| **T1..T2** | `a.py` | `AC-01` | `unittest` |",
                extra_body="残留 {{未替换字段}} 在正文中\n",
            ),
            encoding="utf-8",
        )
        ph_res = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
        self.assertEqual(ph_res.returncode, 2)
        self.assertIn("unresolved_template_placeholder", json.loads(ph_res.stderr.strip())["error"])

        for bad_header in (
            "> **阶段状态**：`verified`",
            "> 批准记录: 已批准",
            "### 验收结论状态：通过",
            "## 诊断结论状态：阻塞",
        ):
            with self.subTest(bad_header=bad_header):
                (fdir / "spec.md").write_text(
                    _valid_complex_spec(
                        unit_rows="| **T1..T2** | `a.py` | `AC-01` | `unittest` |",
                        extra_body=f"{bad_header}\n",
                    ),
                    encoding="utf-8",
                )
                r = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
                self.assertEqual(r.returncode, 2)
                self.assertIn("spec_mutable_status_forbidden", json.loads(r.stderr.strip())["error"])

        for bad_cb in ("- [ ] 偷放复选框", "| [x] | 表格复选框 |"):
            with self.subTest(bad_cb=bad_cb):
                (fdir / "spec.md").write_text(
                    _valid_complex_spec(
                        unit_rows="| **T1..T2** | `a.py` | `AC-01` | `unittest` |",
                        extra_body=f"{bad_cb}\n",
                    ),
                    encoding="utf-8",
                )
                r = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
                self.assertEqual(r.returncode, 2)
                self.assertIn("spec_checkbox_forbidden", json.loads(r.stderr.strip())["error"])

    def test_task_md_redlines_lines_duplicates_statuses_volatile_evidence_and_blockers(self):
        fdir = self.base / "redlines"
        fdir.mkdir()

        base_task = _valid_regular_task(
            state="verified",
            approval="已批｜2026-11-19",
            include_confirm_section=False,
            tasks="- [x] T1：a\n- [x] T2：b",
            table_rows="| AC-01 | 通过 | `python3 -m unittest` |",
        )
        cur_lines = len(base_task.splitlines())
        exact_100 = base_task + ("\n" * (100 - cur_lines))
        self.assertEqual(len(exact_100.splitlines()), 100)
        (fdir / "task.md").write_text(exact_100, encoding="utf-8")
        self.assertEqual(_run_cli("--feature-dir", str(fdir), "--phase", "verified").returncode, 0)

        over_101 = exact_100 + "# line 101\n"
        self.assertEqual(len(over_101.splitlines()), 101)
        (fdir / "task.md").write_text(over_101, encoding="utf-8")
        r_lines = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
        self.assertEqual(r_lines.returncode, 2)
        self.assertIn("task_lines_exceeded", json.loads(r_lines.stderr.strip())["error"])

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：a\n- [x] T2：b",
                table_rows="| [x] AC-01 | 通过 | `python3 -m unittest` |",
            ),
            encoding="utf-8",
        )
        r_tcb = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
        self.assertEqual(r_tcb.returncode, 2)
        self.assertIn("table_checkbox_forbidden", json.loads(r_tcb.stderr.strip())["error"])

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="ready_to_implement",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：a",
                table_rows="| AC-01 | 通过 | `unittest` |",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "invalid_stage_state",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="初版已批；Δ 待确认",
                include_confirm_section=False,
                tasks="- [x] T1：a",
                table_rows="| AC-01 | 通过 | `unittest` |",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "invalid_approval_record",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=True,
                tasks="- [x] T1：a",
                table_rows="| AC-01 | 通过 | `unittest` |",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "confirmation_section_remaining",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：a\n- [x] T4：b\n- [x] T-04：c",
                table_rows="| AC-01 | 通过 | `unittest` |",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "duplicate_task_id:T4",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：a\n- [ ] T2：b",
                table_rows="| AC-01 | 通过 | `unittest` |",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "unchecked_tasks_remaining",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

        for corrupt_status in ("通过通过", "进行中通过", "不适用", "不适用（）"):
            with self.subTest(corrupt_status=corrupt_status):
                (fdir / "task.md").write_text(
                    _valid_regular_task(
                        state="verified",
                        approval="已批｜2026-11-19",
                        include_confirm_section=False,
                        tasks="- [x] T1：a",
                        table_rows=f"| AC-01 | {corrupt_status} | `unittest` |",
                    ),
                    encoding="utf-8",
                )
                err = json.loads(
                    _run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip()
                )["error"]
                self.assertIn(f"invalid_table_status:{corrupt_status}", err)

        for unverified_rows in (
            "| AC-01 | 通过 | `unittest` |\n| AC-02 | 未执行 | `unittest` |",
            "| AC-01 | 不适用（无前端） | 无须执行 |",
        ):
            with self.subTest(unverified_rows=unverified_rows):
                (fdir / "task.md").write_text(
                    _valid_regular_task(
                        state="verified",
                        approval="已批｜2026-11-19",
                        include_confirm_section=False,
                        tasks="- [x] T1：a",
                        table_rows=unverified_rows,
                    ),
                    encoding="utf-8",
                )
                err = json.loads(
                    _run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip()
                )["error"]
                self.assertIn("unverified_table_row", err)

        for bad_ev in (
            "`/tmp/test-output.log`",
            "详见 /private/tmp/run_1/verification.md（exit=0）",
            "输出保存在 /var/folders/ab/cd/T/tmp99/check.py",
        ):
            with self.subTest(bad_ev=bad_ev):
                (fdir / "task.md").write_text(
                    _valid_regular_task(
                        state="verified",
                        approval="已批｜2026-11-19",
                        include_confirm_section=False,
                        tasks="- [x] T1：a",
                        table_rows=f"| AC-01 | 通过 | {bad_ev} |",
                    ),
                    encoding="utf-8",
                )
                err = json.loads(
                    _run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip()
                )["error"]
                self.assertIn("volatile_evidence_only", err)

        for good_ev in (
            "`verify-host-adapters.py --scratch /tmp/adapter-sandbox`（exit=0）",
            "`unittest` 全绿（临时目录 `/var/folders/xx/yy/T/z`，归档 `evidence/run.log`）",
        ):
            with self.subTest(good_ev=good_ev):
                (fdir / "task.md").write_text(
                    _valid_regular_task(
                        state="verified",
                        approval="已批｜2026-11-19",
                        include_confirm_section=False,
                        tasks="- [x] T1：a",
                        table_rows=f"| AC-01 | 通过 | {good_ev} |",
                    ),
                    encoding="utf-8",
                )
                self.assertEqual(
                    _run_cli("--feature-dir", str(fdir), "--phase", "verified").returncode, 0
                )

        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：a",
                table_rows="| AC-01 | 通过 | `unittest` |",
                blocker="等待生产密钥授权",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "active_blocker_remaining",
            json.loads(_run_cli("--feature-dir", str(fdir), "--phase", "verified").stderr.strip())["error"],
        )

    def test_verification_md_statuses_and_symlink_rejection(self):
        fdir = self.base / "ver-and-symlink"
        fdir.mkdir()
        (fdir / "spec.md").write_text(
            _valid_complex_spec(unit_rows="| **T1** | `a.py` | `AC-01` | `unittest` |"),
            encoding="utf-8",
        )
        (fdir / "task.md").write_text(
            _valid_regular_task(
                state="verified",
                approval="已批｜2026-11-19",
                include_confirm_section=False,
                tasks="- [x] T1：完成",
                ac_line="- **文档**：`spec.md` ｜ `verification.md`",
                table_rows="| AC-01 | 通过 | 详见 `verification.md` |",
            ),
            encoding="utf-8",
        )
        self.assertEqual(_run_cli("--feature-dir", str(fdir), "--phase", "verified").returncode, 2)

        for bad_ver_status in ("未完成", "阻塞", "待定"):
            (fdir / "verification.md").write_text(
                _valid_verification_md(status=bad_ver_status), encoding="utf-8"
            )
            r = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
            self.assertEqual(r.returncode, 2)
            self.assertIn("verification_not_passed", json.loads(r.stderr.strip())["error"])

        (fdir / "verification.md").write_text(
            _valid_verification_md(status="通过").replace("验收结论状态", "结论状态"),
            encoding="utf-8",
        )
        self.assertEqual(_run_cli("--feature-dir", str(fdir), "--phase", "verified").returncode, 0)

        sym_dir = self.base / "symlink-feature-dir"
        sym_dir.symlink_to(fdir)
        r_sym_dir = _run_cli("--feature-dir", str(sym_dir), "--phase", "verified")
        self.assertEqual(r_sym_dir.returncode, 2)
        self.assertIn("symlink_rejected", json.loads(r_sym_dir.stderr.strip())["error"])

        ext_md = self.base / "external.md"
        ext_md.write_text("# external\n", encoding="utf-8")
        (fdir / "notes.md").symlink_to(ext_md)
        try:
            r_sym_md = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
            self.assertEqual(r_sym_md.returncode, 2)
            self.assertIn("symlink_rejected", json.loads(r_sym_md.stderr.strip())["error"])
        finally:
            (fdir / "notes.md").unlink()

        ext_sub = self.base / "ext_sub"
        ext_sub.mkdir()
        (fdir / "evidence_link").symlink_to(ext_sub)
        try:
            r_sym_sub = _run_cli("--feature-dir", str(fdir), "--phase", "verified")
            self.assertEqual(r_sym_sub.returncode, 2)
            self.assertIn("symlink_rejected", json.loads(r_sym_sub.stderr.strip())["error"])
        finally:
            (fdir / "evidence_link").unlink()

    def test_real_legacy_and_v3_specs_parse_cleanly_in_temp_copies(self):
        copy_dir = self.base / "工作流最优收敛演进"
        if LEGACY_FEATURE_DIR.is_dir():
            shutil.copytree(LEGACY_FEATURE_DIR, copy_dir)
            r_clean = _run_cli("--feature-dir", str(copy_dir), "--phase", "verified")
            self.assertEqual(r_clean.returncode, 0, msg=r_clean.stderr)
            self.assertEqual(json.loads(r_clean.stdout.strip())["tasks"], ["T1", "T2", "T3", "T4", "T5", "T6"])
        else:
            copy_dir.mkdir()
            (copy_dir / "spec.md").write_text(
                "# 历史收敛规格\n\n## 1. 问题与 AC\n- AC-01：收敛\n\n## 2. 单元切分\n| 单元 | 说明 |\n| --- | --- |\n| **T1..T3**（初版） | 初版 |\n| **T4** | 门禁 |\n| **T5** | 精炼 |\n| **T6** | 复验 |\n",
                encoding="utf-8",
            )
            (copy_dir / "verification.md").write_text(
                "# 验证报告\n\n> **验收结论状态**：通过\n\n正文无复选框。\n",
                encoding="utf-8",
            )
            (copy_dir / "task.md").write_text(
                "# 历史事项\n\n> **阶段状态**：`verified`\n> **批准记录**：用户批准｜2026-11-19\n\n## 任务进度\n"
                + "\n".join(f"- [x] T{i}：单元 {i}" for i in range(1, 7))
                + "\n\n## 验证摘要与阻塞\n\n| 检查范围 | 状态 | 证据 |\n| --- | --- | --- |\n| 全量 | 通过 | `python3 -m unittest` |\n\n- **当前阻塞**：无\n",
                encoding="utf-8",
            )

        clean_task = (copy_dir / "task.md").read_text(encoding="utf-8")
        dup_task = clean_task.replace("- [x] T4", "- [x] T4 重复项\n- [x] T4", 1)
        (copy_dir / "task.md").write_text(dup_task, encoding="utf-8")
        r_dup = _run_cli("--feature-dir", str(copy_dir), "--phase", "verified")
        self.assertEqual(r_dup.returncode, 2)
        self.assertIn("duplicate_task_id:T4", json.loads(r_dup.stderr.strip())["error"])

        bad_status_task = clean_task.replace("| 通过 |", "| 通过通过 |", 1)
        (copy_dir / "task.md").write_text(bad_status_task, encoding="utf-8")
        r_status = _run_cli("--feature-dir", str(copy_dir), "--phase", "verified")
        self.assertEqual(r_status.returncode, 2)
        self.assertIn("invalid_table_status:通过通过", json.loads(r_status.stderr.strip())["error"])

        if V3_SPEC_PATH.is_file():
            v3_copy = self.base / "v3_copy"
            v3_copy.mkdir()
            shutil.copyfile(V3_SPEC_PATH, v3_copy / "spec.md")
            (v3_copy / "task.md").write_text(
                _valid_regular_task(
                    state="pending_approval",
                    approval="待确认",
                    tasks="\n".join(f"- [ ] T{i}：单元 {i}" for i in range(1, 6)),
                    ac_line="- **文档**：`spec.md` ｜ `verification.md`",
                ),
                encoding="utf-8",
            )
            r_v3 = _run_cli("--feature-dir", str(v3_copy), "--phase", "spec-gate")
            self.assertEqual(r_v3.returncode, 0, msg=r_v3.stderr)

class VerifyFeatureWriteBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Dev"], cwd=self.repo, check=True)

        (self.repo / ".gitignore").write_text("agent-features/\n", encoding="utf-8")
        (self.repo / "src").mkdir()
        (self.repo / "src/keep_dirty.py").write_text("x = 1\n", encoding="utf-8")
        (self.repo / "src/rename_src.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (self.repo / "src/to_delete.py").write_text("del_me = True\n", encoding="utf-8")
        (self.repo / "目录").mkdir()
        (self.repo / "目录/中文模块.py").write_text("val = 'init'\n", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests/test_alpha.py").write_text("pass\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=self.repo, check=True)

    def test_snapshot_and_check_writes_differential_unicode_gitignore_rename_symlink_and_delete(self):
        (self.repo / "src/keep_dirty.py").write_text("x = 2  # pre-dirty\n", encoding="utf-8")
        fdir = self.repo / "agent-features/测试事项"
        fdir.mkdir(parents=True)
        (fdir / "task.md").write_text("# task baseline\n", encoding="utf-8")
        (fdir / "spec.md").write_text("# spec baseline\n", encoding="utf-8")

        snap = fdir / ".write-snap.json"
        s_res = _run_cli(
            "--write-snapshot",
            str(snap),
            "--repo-root",
            str(self.repo),
            "--feature-dir",
            str(fdir),
        )
        self.assertEqual(s_res.returncode, 0, msg=s_res.stderr)
        self.assertTrue(snap.is_file())

        c0 = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
        )
        self.assertEqual(c0.returncode, 0, msg=c0.stderr)
        self.assertEqual(json.loads(c0.stdout.strip())["violations"], [])

        (self.repo / "目录/中文模块.py").write_text("val = 'updated'\n", encoding="utf-8")
        (self.repo / "tests/test_beta.py").write_text("assert True\n", encoding="utf-8")

        c_deny = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
            "--allow",
            "tests/test_*.py",
        )
        self.assertEqual(c_deny.returncode, 2)
        deny_json = json.loads(c_deny.stderr.strip())
        self.assertEqual(deny_json["error"], "unauthorized_write_detected")
        self.assertEqual(
            deny_json["violations"],
            [unicodedata.normalize("NFC", "目录/中文模块.py")],
        )

        nfd_dir_allow = unicodedata.normalize("NFD", "目录/")
        c_allow = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
            "--allow",
            "tests/test_*.py",
            nfd_dir_allow,
        )
        self.assertEqual(c_allow.returncode, 0, msg=c_allow.stderr)

        (fdir / "task.md").write_text("# tampered by subagent!\n", encoding="utf-8")
        c_feat = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
            "--allow",
            "tests/test_*.py",
            "目录",
        )
        self.assertEqual(c_feat.returncode, 2)
        feat_json = json.loads(c_feat.stderr.strip())
        self.assertEqual(feat_json["error"], "unauthorized_write_detected")
        self.assertEqual(feat_json["violations"], ["agent-features/测试事项/task.md"])

        (fdir / "task.md").write_text("# task baseline\n", encoding="utf-8")
        subprocess.run(
            ["git", "mv", "src/rename_src.py", "src/renamed_dst.py"],
            cwd=self.repo,
            check=True,
        )
        c_ren_half = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
            "--allow",
            "tests/test_*.py",
            "目录",
            "src/renamed_dst.py",
        )
        self.assertEqual(c_ren_half.returncode, 2)
        self.assertEqual(
            json.loads(c_ren_half.stderr.strip())["violations"],
            ["src/rename_src.py"],
        )

        c_ren_both = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--since",
            str(snap),
            "--feature-dir",
            str(fdir),
            "--allow",
            "tests/test_*.py",
            "目录",
            "--allow",
            "src/rename_src.py",
            "src/renamed_dst.py",
        )
        self.assertEqual(c_ren_both.returncode, 0, msg=c_ren_both.stderr)

        (self.repo / "src/to_delete.py").unlink()
        (self.repo / "src/link.py").symlink_to("keep_dirty.py")
        snap2 = self.base / "snap2.json"
        self.assertEqual(
            _run_cli("--write-snapshot", str(snap2), "--repo-root", str(self.repo)).returncode,
            0,
        )
        snap2_data = json.loads(snap2.read_text(encoding="utf-8"))
        git_map = snap2_data["git_entries"]
        self.assertEqual(git_map["src/to_delete.py"]["sha256"], "DELETED")
        self.assertEqual(git_map["src/link.py"]["sha256"], "SYMLINK")

        c_nosince = _run_cli(
            "--check-writes",
            "--repo-root",
            str(self.repo),
            "--allow",
            "src/",
            "tests/test_*.py",
        )
        self.assertEqual(c_nosince.returncode, 2)
        self.assertEqual(
            json.loads(c_nosince.stderr.strip())["violations"],
            ["目录/中文模块.py"],
        )


if __name__ == "__main__":
    unittest.main()
