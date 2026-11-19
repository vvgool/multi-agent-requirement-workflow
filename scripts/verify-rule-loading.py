#!/usr/bin/env python3
"""Read-only Protocol 4 rule consistency, anti-drift gates, and size verification."""

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import json  # noqa: E402
import unicodedata  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

ENTRY_FILES = [
    "agents/coordinator-agent.md",
    "agents/product-agent.md",
    "agents/development-agent.md",
    "agents/testing-agent.md",
    "agents/bug-agent.md",
    "workflow/routing.md",
    "workflow/execution-contract.md",
    "workflow/documents.md",
    "workflow/handoff.md",
    "workflow/host-adapters.md",
    "workflow/config.md",
    "skills/requirement-analysis/SKILL.md",
    "skills/feature-development/SKILL.md",
    "skills/bug-fixing/SKILL.md",
    "skills/acceptance-testing/SKILL.md",
    "skills/setup-requirement-workflow/SKILL.md",
    "skills/issue-tracking/SKILL.md",
    "skills/setup-requirement-workflow/assets/templates/role-body.md",
    "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
]

MAX_PACKAGE_FILES = 58
MAX_PACKAGE_BYTES = 162373  # template consolidation must stay below the pre-consolidation package
MAX_ENTRY_LINES = 60
MAX_AGENT_LINES = 20
FORBIDDEN_RUNTIME_HASH_TERMS = ("package_digest", ".local.json", "codex-bootstrap", "bootstrap.md", "package.md", "sha256sum", "shasum", "hashlib.sha256", "安装回执")
RETIRED_TEMPLATES = (
    "skills/feature-development/assets/templates/implementation-plan.md",
    "skills/feature-development/assets/templates/technical-plan.md",
    "skills/feature-development/assets/templates/verification.md",
    "skills/acceptance-testing/assets/templates/test-report.md",
)
REQUIRED_TEMPLATES = (
    "templates/task.md",
    "skills/requirement-analysis/assets/templates/requirements.md",
    "skills/feature-development/assets/templates/technical-design.md",
    "skills/acceptance-testing/assets/templates/verification.md",
    "skills/bug-fixing/assets/templates/bug-report.md",
)
HARD_CAP = re.compile(
    r"(?:[≤≦<]=?|不(?:得)?超过|最多|至多|上限|no more than|at most|max(?:imum)?(?:\s+of)?)\s*[5五]\s*"
    r"(?:条|个|项|items?|questions?|Qs?\b)|[5五]\s*(?:条|个|项)\s*以内",
    re.I,
)
SELF_CHECK_FILLER = re.compile(r"起草者自查|自查清单|自检清单|作者自检")
TABLE_CHECKBOX = re.compile(r"(?:\||<br\s*/?>)[ \t]*(?:[-+*][ \t]+)?\[[ xX]\](?=[ \t|]|$)", re.M)


def _iter_package_files(root: Path):
    for name in ("framework.yaml", "AGENTS.md", "README.md", "workflow.yaml", "LICENSE"):
        p = root / name
        if p.is_file():
            yield p
    for directory in ("agents", "skills", "workflow", "templates"):
        base = root / directory
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(root).as_posix()
            if rel.startswith("skills/system/"):
                continue
            if p.name in {"__pycache__", ".DS_Store"} or p.suffix in {".pyc", ".pyo"}:
                continue
            if p.is_file():
                yield p


def check_local_rule_links(root: Path) -> int:
    """Validate package Markdown pointers outside fenced code blocks."""
    checked = 0
    for directory in ("agents", "skills", "workflow", "templates"):
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if rel.startswith("skills/system/"):
                continue
            raw_text = path.read_text(encoding="utf-8")
            stripped = re.sub(r"```.*?```", "", raw_text, flags=re.S)
            for target in re.findall(r"\]\(([^)\s]+)\)", stripped):
                if target.startswith("#") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                    continue
                if "{" in target or target.startswith("<"):
                    continue
                checked += 1
                destination = path.parent / target.split("#", 1)[0]
                assert destination.is_file(), (
                    f"linked_rule_missing: {path.relative_to(root)} -> {target}"
                )
    return checked


def check(root: Path, baseline: Path = None, *, require_smaller: bool = False) -> dict:
    for rel in ENTRY_FILES:
        assert (root / rel).is_file(), f"linked_rule_missing: {rel}"
    for rel in RETIRED_TEMPLATES:
        assert not (root / rel).exists(), f"retired_template_present: {rel}"
    for rel in REQUIRED_TEMPLATES:
        assert (root / rel).is_file(), f"required_template_missing: {rel}"
    texts = {p: (root / p).read_text(encoding="utf-8") for p in ENTRY_FILES}

    framework = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8"))
    lock = yaml.safe_load(
        (root / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert framework["schema_version"] == 1
    assert framework["name"] == "multi-agent-requirement-workflow"
    assert isinstance(framework["version"], str) and framework["version"].strip()
    assert framework["version"] == "1.0.2", (
        f"version_or_exact_file_count_mismatch: framework.yaml -> {framework['version']}"
    )
    assert type(framework["protocol_version"]) is int and framework["protocol_version"] == 4
    assert lock["package"]["protocol_version"] == framework["protocol_version"]

    # Quantitative light-kernel limits & exact 58-file package budget
    pkg_files = list(_iter_package_files(root))
    pkg_file_count = len(pkg_files)
    pkg_total_bytes = sum(p.stat().st_size for p in pkg_files)
    assert pkg_file_count == MAX_PACKAGE_FILES, (
        f"version_or_exact_file_count_mismatch: package_file_count={pkg_file_count}"
    )
    assert pkg_total_bytes <= MAX_PACKAGE_BYTES, f"package_bytes_exceeded: {pkg_total_bytes}"

    for meta_name in ("README.md", "AGENTS.md"):
        meta_path = root / meta_name
        if meta_path.is_file():
            meta_text = meta_path.read_text(encoding="utf-8")
            assert framework["version"] in meta_text and "1.0.1" not in meta_text, (
                f"version_or_exact_file_count_mismatch: {meta_name}"
            )

    for rel, body in texts.items():
        if rel.startswith("agents/"):
            line_cnt = len(body.splitlines())
            assert line_cnt <= MAX_AGENT_LINES, f"agent_lines_exceeded: {rel} ({line_cnt})"
        for dead in FORBIDDEN_RUNTIME_HASH_TERMS:
            assert dead not in body, f"runtime_hash_or_receipt_dead_word: {rel} -> {dead}"

    entry = texts["skills/setup-requirement-workflow/assets/templates/project-entry-light.md"]
    entry_lines = entry.splitlines()
    assert len(entry_lines) <= MAX_ENTRY_LINES, f"entry_lines_exceeded: {len(entry_lines)}"
    assert "```" not in entry, "entry_forbids_inline_code_blocks"
    assert not re.search(r"\]\((?:workflow|skills|agents|templates)/", entry), (
        "entry_forbids_consumer_relative_links"
    )
    assert ".local.json" not in entry and "无需运行时计算包哈希" in entry
    assert "穿透 XY 表象" in entry, "first_principles_entry_missing"

    claude_entry = (
        root / "skills/setup-requirement-workflow/assets/templates/claude-entry.md"
    ).read_text(encoding="utf-8")
    for ceremonial in ("你是需求协作框架", "协议 4"):
        assert ceremonial not in entry, f"ceremonial_entry_label_forbidden: {ceremonial}"
        assert ceremonial not in claude_entry, f"ceremonial_claude_label_forbidden: {ceremonial}"

    project_entry_path = root / "AGENTS.md"
    project_entry = None
    if project_entry_path.is_file():
        project_entry = project_entry_path.read_text(encoding="utf-8")
        assert "<!-- requirement-workflow:begin -->" in project_entry
        assert "<!-- requirement-workflow:end -->" in project_entry
        for guard in ("前期先查代码、合并必答提问", "穿透 XY 表象", "严禁自动重放或补偿", "中途打断白名单"):
            assert guard in project_entry, f"project_entry_guard_missing: {guard}"

    # Thin role body zero runtime hash, cache-missing block & zero ceremonial persona
    role = texts["skills/setup-requirement-workflow/assets/templates/role-body.md"]
    assert "framework_cache_missing" in role
    for ceremonial in ("你是需求协作框架", "当前宿主原生名称为", "协议 4"):
        assert ceremonial not in role, f"ceremonial_role_label_forbidden: {ceremonial}"
    assert "日常无需重算全包哈希" in role
    assert "读取 `<缓存根>/{{role_file}}` 与完整 `<缓存根>/{{skill_file}}`" in role, (
        "professional_delegation_role_loading_missing"
    )

    # Explicit stage states & 2-gate confirmation contracts
    execution = texts["workflow/execution-contract.md"]
    routing = texts["workflow/routing.md"]
    for state in (
        "pending_req_approval",
        "req_approved",
        "pending_design_approval",
        "ready_to_implement",
        "verified",
    ):
        assert state in entry and state in execution, f"stage_state_missing: {state}"

    for guard in (
        "一次性合并提出",
        "需求确认后进入正式设计",
        "设计确认后实施",
        "批准不追溯覆盖",
        "业务澄清不等于需求批准",
        "提问受理不等于用户答案",
        "等待真实用户回复后再判断批准",
        "设计确认前核对审查适用性",
        "付款、权限、数据删除或大范围共享逻辑变更",
        "另由一名角色独立验证",
        "严禁自动重放或补偿",
    ):
        assert guard in execution, f"confirmation_contract_missing: {guard}"

    assert "结束本轮" in entry and "accepted:true" in entry, "confirmation_wait_missing"
    assert "单一服务或改动文件少不能作为免审依据" in routing, "review_applicability_basis_missing"
    assert all(
        route in routing for route in ("明确局部修改", "一般需求", "复杂需求", "Bug/技术异常")
    )

    consumers = [
        *[p for p in ENTRY_FILES if p.startswith("agents/")],
        "skills/requirement-analysis/SKILL.md",
        "skills/feature-development/SKILL.md",
        "skills/acceptance-testing/SKILL.md",
        "skills/bug-fixing/SKILL.md",
    ]
    for path in consumers:
        assert "execution-contract.md#人工确认" in texts[path], (
            f"confirmation_pointer_missing: {path}"
        )

    codex_adapter = (root / "skills/setup-requirement-workflow/references/codex-adapter.md").read_text(
        encoding="utf-8"
    )
    for guard in ("execution-contract.md#人工确认", "accepted:true", "仅证明问题已受理", "核对后续真实用户答案"):
        assert guard in codex_adapter, f"codex_confirmation_contract_missing: {guard}"

    host_adapter = texts["workflow/host-adapters.md"]
    for path, body, pointer in [
        ("agents/coordinator-agent.md", texts["agents/coordinator-agent.md"], "../workflow/routing.md"),
        ("workflow/routing.md", routing, "host-adapters.md#业务派发与降级路径"),
        (
            "workflow/host-adapters.md",
            host_adapter,
            "../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作",
        ),
    ]:
        assert f"]({pointer})" in body, f"professional_delegation_pointer_missing: {path}"

    _, heading, remainder = codex_adapter.partition("### 无具名选择参数时的业务独立协作\n")
    assert heading, "professional_delegation_section_missing"
    fallback = re.split(r"(?m)^ {0,3}#{1,3}[ \t]+", remainder, maxsplit=1)[0]
    for guard in (
        "对应包内角色和完整Skill路径",
        "实际工具支持独立上下文时选择独立上下文",
        "读取对应角色和完整Skill",
        "父会话回读真实子任务标识、父子关系、加载与执行证据及结果",
        "缺独立上下文、必要加载或实际结果时，受影响审查/验收仍阻塞",
        "不将其计为具名激活探测通过",
    ):
        assert guard in fallback, f"professional_delegation_contract_missing: {guard}"

    obsolete = (
        "不增加统一人工阶段审批",
        "审查不新增统一人工批准",
        "小需求目标清楚即可执行，不强制再写需求稿和统一批准",
        "Lite / Standard / Complex",
        "Lite、Standard、Complex",
    )
    for path in [*ENTRY_FILES, "skills/feature-development/assets/templates/technical-design.md"]:
        body = (root / path).read_text(encoding="utf-8")
        assert not any(term in body for term in obsolete), f"obsolete_confirmation_bypass: {path}"

    # Silent continuous cruise, interruption whitelist & anti-drift 4 locks
    for guard in (
        "中途打断白名单",
        "契约证伪",
        "高危副作用",
        "外部凭据缺失",
        "只读回读",
        "主会话单写",
        "干净子上下文",
        "连续 2～3 次修复失败且未缩小根因范围时立即熔断停手",
        "内部验收自闭环",
    ):
        assert guard in execution, f"anti_drift_contract_missing: {guard}"

    debugging = (root / "skills/bug-fixing/references/systematic-debugging.md").read_text(
        encoding="utf-8"
    )
    assert "连续 2～3 次修改仍失败且未缩小根因范围时，立即触发盲修熔断" in debugging

    # First-principles operational loop across requirement, design, review & debugging
    for guard in ("穿透 XY 表象", "先删减简化、再机械下沉", "拒绝经验类比盲试"):
        assert guard in execution, f"first_principles_execution_missing: {guard}"

    clarification = (root / "skills/requirement-analysis/references/clarification.md").read_text(
        encoding="utf-8"
    )
    req_tpl = (root / "skills/requirement-analysis/assets/templates/requirements.md").read_text(
        encoding="utf-8"
    )
    for guard in ("穿透 XY 问题", "表面解法", "根本矛盾"):
        assert guard in clarification, f"first_principles_clarification_missing: {guard}"
    for guard in ("表面解法", "根本矛盾"):
        assert guard in req_tpl, f"first_principles_req_template_missing: {guard}"

    design_decomp = (root / "skills/feature-development/references/design-and-decomposition.md").read_text(
        encoding="utf-8"
    )
    tech_tpl = (root / "skills/feature-development/assets/templates/technical-design.md").read_text(
        encoding="utf-8"
    )
    for guard in ("先删减、再下沉、后新增", "机械约束下沉"):
        assert guard in design_decomp, f"first_principles_design_missing: {guard}"
    assert "先删减、再下沉、后新增" in tech_tpl, "first_principles_tech_template_missing"

    for guard in ("拒绝经验类比盲试", "破坏不变量"):
        assert guard in debugging, f"first_principles_debugging_missing: {guard}"

    # 4-point pre-implementation alignment review & adversarial counterexample gate
    arch_review = (root / "skills/feature-development/references/architecture-review.md").read_text(
        encoding="utf-8"
    )
    for dim in ("遗漏的 AC", "擅自扩权范围", "模块契约冲突", "未证实假设与边界风险"):
        assert dim in arch_review, f"alignment_review_dimension_missing: {dim}"
    for guard in ("第一性原理与防叠补丁", "治标补丁"):
        assert guard in arch_review, f"first_principles_review_missing: {guard}"

    completion_gate = (root / "skills/acceptance-testing/references/completion-gate.md").read_text(
        encoding="utf-8"
    )
    for guard in ("最高风险", "破坏性反例", "无适用运行反例"):
        assert guard in completion_gate, f"completion_gate_missing: {guard}"

    handoff = texts["workflow/handoff.md"]
    assert "合格派发卡片" in handoff and "不合格派发反例" in handoff

    setup = texts["skills/setup-requirement-workflow/SKILL.md"]
    assert "回读宿主实际子任务记录" in setup and "install_helper.py" in setup

    # First-screen template rules, Delta continuation & single task.md checklist
    documents = texts["workflow/documents.md"]
    assert "≤ 100 行" in documents and "Delta 差量" in documents and "禁止新建 `v2/v3` 版本目录" in documents

    task_tpl = (root / "templates/task.md").read_text(encoding="utf-8")
    for req in ("阶段状态", "本次请确认", "- [ ]", "≤ 100 行", "Delta"):
        assert req in task_tpl, f"task_template_missing: {req}"

    # v1.0.2 anti-idle cruise, pseudo-blocker exclusion, entry exclusivity, session isolation & task dump guards
    for rel in ("workflow/execution-contract.md", "skills/feature-development/SKILL.md"):
        for guard in (
            "可行性探针须在 `STOP 2` 前最小取证或并入已批 `T1`",
            "严禁将探针/测试夹具拆成多轮 `pending_design_approval`",
            "未完成对应业务源码实现前严禁将纯探针/夹具通过标为 `verified`",
        ):
            assert guard in texts[rel], f"probe_micro_approval_guard_missing: {rel} -> {guard}"

    pseudo_blocker_targets = [
        ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", entry),
        ("workflow/execution-contract.md", execution),
    ]
    if project_entry is not None:
        pseudo_blocker_targets.append(("AGENTS.md", project_entry))
    for rel, body in pseudo_blocker_targets:
        for guard in (
            "按锁文件安装本地依赖",
            "复用当前宿主运行隔离验证",
            "隔离环境内生成随机合成密钥/假数据",
            "均非打断白名单",
            "声称缺环境前须先核实本机隔离可行性",
        ):
            assert guard in body, f"pseudo_blocker_whitelist_guard_missing: {rel} -> {guard}"

    exclusivity_targets = [
        ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", entry),
        ("skills/setup-requirement-workflow/assets/templates/claude-entry.md", claude_entry),
    ]
    if project_entry is not None:
        exclusivity_targets.append(("AGENTS.md", project_entry))
    for rel, body in exclusivity_targets:
        for guard in (
            "禁止混用外部通用规格工作流 Skill",
            "保留领域/工具专项 Skill 正常调用",
        ):
            assert guard in body, f"external_spec_skill_exclusivity_missing: {rel} -> {guard}"

    opencode_adapter = (
        root / "skills/setup-requirement-workflow/references/opencode-adapter.md"
    ).read_text(encoding="utf-8")
    session_guard = "实施前设计审查与实施后最终对抗验收严禁复用同一子会话 `sessionID`"
    for rel, body in (
        ("workflow/handoff.md", handoff),
        ("agents/testing-agent.md", texts["agents/testing-agent.md"]),
        ("skills/setup-requirement-workflow/references/opencode-adapter.md", opencode_adapter),
    ):
        assert session_guard in body, (
            f"review_session_isolation_or_async_resume_missing: {rel} -> {session_guard}"
        )
    for guard in (
        "后台完成后自动接续，无需回复继续",
        "被唤醒后若处于 `ready_to_implement` 则直接推进后续单元",
    ):
        assert guard in opencode_adapter, (
            f"review_session_isolation_or_async_resume_missing: opencode-adapter.md -> {guard}"
        )

    for rel, body in (("workflow/documents.md", documents), ("templates/task.md", task_tpl)):
        for guard in (
            "严禁借单行塞入长流水账绕过",
            "严禁仅留 `/tmp` 等易失路径作唯一验收证据",
        ):
            assert guard in body, (
                f"task_single_line_dump_or_ephemeral_evidence_missing: {rel} -> {guard}"
            )
    assert "复杂跨模块事项标 `verified` 前须落盘 `verification.md`" in documents, (
        "task_single_line_dump_or_ephemeral_evidence_missing: workflow/documents.md -> verification.md_required"
    )

    qa_interaction_targets = [
        ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", entry),
        ("workflow/execution-contract.md", execution),
    ]
    if project_entry is not None:
        qa_interaction_targets.append(("AGENTS.md", project_entry))
    for rel, body in qa_interaction_targets:
        for guard in (
            "推荐优先调用宿主原生交互问答组件",
            "确认选项必须具备明确授权语义",
            "严禁仅凭业务参数澄清选项流转状态",
        ):
            assert guard in body, f"native_qa_interaction_guard_missing: {rel} -> {guard}"
    assert "推荐优先调用宿主原生交互问答组件" in host_adapter, (
        "native_qa_interaction_guard_missing: workflow/host-adapters.md"
    )

    local_rule_links = check_local_rule_links(root)

    for stage in ("requirement-analysis", "feature-development", "acceptance-testing", "bug-fixing"):
        skill = root / "skills" / stage / "SKILL.md"
        body = skill.read_text(encoding="utf-8")
        assert "../../workflow/documents.md#人读文档格式" in body, skill
        templates = list((skill.parent / "assets/templates").glob("*.md"))
        assert templates, skill
        for template in templates:
            rel_tpl = template.relative_to(skill.parent).as_posix()
            assert rel_tpl in body, template
            tpl_text = template.read_text(encoding="utf-8")
            assert ("阶段状态" in tpl_text or "结论状态" in tpl_text), (
                f"template_first_screen_status_missing: {template}"
            )
            assert not re.search(
                r"^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[[ xX]\](?:[ \t]+|$)",
                tpl_text,
                re.M,
            ), f"non_task_template_checkbox_forbidden: {template}"
        for link in re.findall(r"\]\((assets/templates/[^)#]+\.md)\)", body):
            assert (skill.parent / link).is_file(), link

    # Template consolidation (7 -> 5): retired paths, orthogonal set, anchors & single-writer
    for path in _iter_package_files(root):
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        body = path.read_text(encoding="utf-8")
        assert not HARD_CAP.search(unicodedata.normalize("NFKC", body)), (
            f"confirmation_hard_cap_forbidden: {rel}"
        )
        if "/assets/templates/" in rel or rel.startswith("templates/"):
            if "setup-requirement-workflow" in rel:
                continue
            assert not SELF_CHECK_FILLER.search(body), f"template_self_check_filler_forbidden: {rel}"
            assert not TABLE_CHECKBOX.search(body), f"table_checkbox_forbidden: {rel}"
    assert "requirements.md#功能与验收标准" in task_tpl, "task_template_requirements_anchor_missing"
    assert "## 功能与验收标准" in req_tpl, "requirements_template_merged_section_missing"
    design_tpl_text = (root / "skills/feature-development/assets/templates/technical-design.md").read_text(
        encoding="utf-8"
    )
    for heading in ("## 文件变更与单元切分", "## 接口签名与异常契约"):
        assert heading in design_tpl_text, f"technical_design_section_missing: {heading}"
    assert "technical-design.md#接口签名与异常契约" in handoff, "handoff_design_anchor_stale"
    for rel in ("workflow/documents.md", "workflow/handoff.md", "skills/acceptance-testing/SKILL.md"):
        assert "验证报告唯一写入人" in texts[rel], f"verification_single_writer_missing: {rel}"
    assert "批准记录" in documents and "临时恢复" in documents, "approval_record_roundtrip_missing"

    before = (
        sum((baseline / p).stat().st_size for p in ENTRY_FILES)
        if baseline is not None
        else None
    )
    after = sum(len(t.encode("utf-8")) for t in texts.values())
    if require_smaller:
        assert before is not None, "size_baseline_required"
        assert after < before, f"rule_size_not_reduced: {before} -> {after}"

    return dict(
        framework=framework,
        protocol=framework["protocol_version"],
        entry_files=len(texts),
        entry_lines=len(entry_lines),
        package_file_count=pkg_file_count,
        package_total_bytes=pkg_total_bytes,
        local_rule_links=local_rule_links,
        scenarios=[
            "light-kernel-size-and-entry-budget",
            "install-time-verification-zero-runtime-hash",
            "separate-human-confirmations",
            "professional-delegation-loading-chain",
            "silent-continuous-cruise-and-whitelist",
            "anti-drift-four-locks-and-circuit-breaker",
            "four-point-alignment-review-and-adversarial-gate",
            "first-screen-templates-and-delta-evolution",
            "first-principles-xy-subtractive-and-ground-truth",
            "unknown-external-operation-no-replay",
            "anti-probe-micro-approval-and-host-convergence",
        ],
        selected_rule_utf8_bytes=dict(
            before=before,
            after=after,
            delta=after - before if before is not None else None,
            reduction_required=require_smaller,
        ),
        scope="static contract consistency only; not native execution, tokens or elapsed time",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--baseline-root", type=Path, help="optional complete baseline for size reporting")
    parser.add_argument("--require-smaller", action="store_true", help="require size reduction vs baseline")
    args = parser.parse_args()
    if not __debug__:
        parser.error("assertions required; do not use -O")
    if args.require_smaller and args.baseline_root is None:
        parser.error("--require-smaller requires --baseline-root")
    baseline = args.baseline_root.resolve() if args.baseline_root is not None else None
    print(
        json.dumps(
            check(args.source_root.resolve(), baseline, require_smaller=args.require_smaller),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
