#!/usr/bin/env python3
"""Read-only protocol3 entry consistency and optional rule-size comparison.

No model execution, runtime, token meter, installation or native acceptance.
The named scenarios are static contract checks, not business E2E tests.
"""

import argparse
import json
import re
from pathlib import Path

import yaml

ENTRY_FILES = [
    "agents/coordinator-agent.md",
    "agents/product-agent.md",
    "agents/development-agent.md",
    "agents/testing-agent.md",
    "agents/bug-agent.md",
    "workflow/execution-contract.md",
    "workflow/routing.md",
    "workflow/revisions.md",
    "workflow/handoff.md",
    "workflow/output-layout.md",
    "workflow/code-baseline.md",
    "skills/requirement-analysis/SKILL.md",
    "skills/feature-development/SKILL.md",
    "skills/bug-fixing/SKILL.md",
    "skills/acceptance-testing/SKILL.md",
    "skills/setup-requirement-workflow/assets/templates/role-body.md",
    "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
]


def check_local_rule_links(root):
    """Validate package document pointers, not agent behavior or prose quality."""
    checked = 0
    for directory in ["agents", "skills", "workflow", "templates"]:
        for path in sorted((root / directory).rglob("*.md")):
            for target in re.findall(
                r"\]\(([^)\s]+)\)", path.read_text(encoding="utf-8")
            ):
                if target.startswith("#") or re.match(
                    r"^[A-Za-z][A-Za-z0-9+.-]*:", target
                ):
                    continue
                # Templates may contain a destination to be supplied by the consumer.
                if "{" in target:
                    continue
                checked += 1
                destination = path.parent / target.split("#", 1)[0]
                assert destination.is_file(), (
                    f"linked_rule_missing: {path.relative_to(root)} -> {target}"
                )
    return checked


def check(root, baseline=None, *, require_smaller=False):
    texts = {p: (root / p).read_text(encoding="utf-8") for p in ENTRY_FILES}
    project_entry_path = root / "AGENTS.md"
    project_entry = (
        project_entry_path.read_text(encoding="utf-8")
        if project_entry_path.is_file()
        else ""
    )
    framework = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8"))
    lock = yaml.safe_load(
        (
            root
            / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml"
        ).read_text()
    )
    assert framework["schema_version"] == 1
    assert framework["name"] == "multi-agent-requirement-workflow"
    assert isinstance(framework["version"], str) and framework["version"].strip()
    assert (
        type(framework["protocol_version"]) is int
        and framework["protocol_version"] == 3
    )
    assert lock["package"]["protocol_version"] == framework["protocol_version"]
    role = texts["skills/setup-requirement-workflow/assets/templates/role-body.md"]
    assert "不要求task.yaml" in role and "旧协议任务回原锁定包" in role
    assert "原生任务已有的派发/结束事实不重复落盘" in role
    for path in [p for p in ENTRY_FILES if p.startswith("agents/")]:
        assert "不要求task.yaml" in texts[path] and "单写" in texts[path], path
    entry = texts[
        "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
    ]
    assert entry.index("独立一次性") < entry.index("需要上述框架能力时")
    assert "默认路径" in entry
    assert "执行前风险" in entry
    assert "原因不明先由同一角色诊断，再按新证据调整路由" in entry
    for label, body in [("distribution entry", entry), ("project entry", project_entry)]:
        if not body:
            continue
        assert "**修改前判断**" in body, label
        assert body.index("**修改前判断**") < body.index("对于独立一次性"), label
        assert body.index("**外部结果未知**") < body.index("对于独立一次性"), label
        assert "暂停依赖这些决策的实现" in body, label
        assert "仍未知且幂等性未确认" in body, label
        assert "不执行或实现自动重放、补偿" in body, label
        assert "已有请求的重入/重试与正常新请求须分别验证" in body, label
    assert not any(
        term in entry
        for term in ["Lite / Standard / Complex", "Lite、Standard、Complex"]
    )
    assert "无需读取workflow.lock.yaml、检查缓存" in entry
    assert "已有旧任务仍按原锁原包续接" in entry
    assert "本入口的授权、风险和未知操作边界" in entry
    execution = texts["workflow/execution-contract.md"]
    routing = texts["workflow/routing.md"]
    revisions = texts["workflow/revisions.md"]
    if project_entry:
        assert "默认路径" in project_entry
        assert "执行前风险" in project_entry
        assert not any(
            term in project_entry
            for term in ["Lite / Standard / Complex", "Lite、Standard、Complex"]
        )
    assert all(
        route in routing
        for route in ["明确局部修改", "一般需求", "复杂需求", "Bug/技术异常"]
    )
    assert "执行前风险门禁" in routing
    assert "不强行归入明确局部修改" in routing
    assert "切换到更合适的现有路由" in routing
    assert "首次修改前" in routing and "先暂停受影响实现" in routing
    assert "不执行或实现自动重放、补偿" in routing
    assert not any(
        term in routing or term in execution
        for term in ["Lite / Standard / Complex", "Lite、Standard、Complex"]
    )
    assert "无需先建文档、清单、计划或宿主原生任务" in execution
    assert "原因未知先由同一角色" in execution
    assert "不默认全量测试" in execution and "无意义测试" in execution
    assert "小任务在原文档列任务后" not in execution
    assert "消息提供当前任务文档路径" not in role
    assert "付款、权限、数据删除或大范围共享逻辑变更" in execution
    assert "另由一名角色独立验证" in execution
    assert "未知不等于结束" in execution and "不重复派发或重放外部操作" in execution
    debugging = (root / "skills/bug-fixing/references/systematic-debugging.md").read_text(encoding="utf-8")
    for body in [execution, debugging]:
        assert "每次失败后先分类并写出能区分根因的新证据" in body
        assert "没有改变假设、失败类别或验证范围时停止修改" in body
        assert "三次没有新证据" not in body
    setup = (root / "skills/setup-requirement-workflow/SKILL.md").read_text(encoding="utf-8")
    assert "回读宿主实际子任务记录" in setup
    assert "核对父会话关系、指定角色、目标项目及成功终态" in setup
    assert "即使四个命令都成功也不能填 native_role_invocation=passed" in setup
    assert "无法取得实际子任务关系时保持 pending" in setup
    assert "补充、修改验收、修复、重试、普通继续及完成后的修改" in revisions
    assert (
        "只有独立目标才新建事项" in revisions
        and "不删除、不合并、不静默迁移" in revisions
    )
    task = (root / "templates/task.md").read_text()
    assert all(title in task for title in ["目标与范围", "- [ ]", "验证与未决项"])
    assert not any(
        field in task
        for field in ["baseline_id", "invocation_id", "delivery_id", "revision"]
    )
    # Check the actual conditional loading path, not only template existence.
    for stage in [
        "requirement-analysis",
        "feature-development",
        "acceptance-testing",
        "bug-fixing",
    ]:
        skill = root / "skills" / stage / "SKILL.md"
        body = skill.read_text(encoding="utf-8")
        assert "../../workflow/documents.md#人读文档格式" in body, skill
        assert (root / "workflow/documents.md").is_file()
        templates = list((skill.parent / "assets/templates").glob("*.md"))
        assert templates, skill
        for template in templates:
            assert template.relative_to(skill.parent).as_posix() in body, template
            assert not re.search(
                r"^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[[ xX]\](?:[ \t]+|$)",
                template.read_text(encoding="utf-8"),
                re.M,
            ), template
        # A linked template must still be available if its file was removed.
        for link in re.findall(r"\]\((assets/templates/[^)#]+\.md)\)", body):
            assert (skill.parent / link).is_file(), link
    local_rule_links = check_local_rule_links(root)
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
        local_rule_links=local_rule_links,
        scenarios=[
            "simple-document-or-known-fix",
            "same-item-continued-after-completion",
            "cross-role-single-writer",
            "risk-confirmation-independent-verification",
            "preflight-risk-before-change",
            "route-switch-on-new-evidence",
            "unknown-external-operation-no-replay",
            "old-lock-no-migration",
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
    parser.add_argument(
        "--baseline-root",
        type=Path,
        help="optional complete baseline for size reporting",
    )
    parser.add_argument(
        "--require-smaller",
        action="store_true",
        help="require size reduction for a slimming experiment",
    )
    args = parser.parse_args()
    if not __debug__:
        parser.error("assertions required; do not use -O")
    if args.require_smaller and args.baseline_root is None:
        parser.error("--require-smaller requires --baseline-root")
    baseline = args.baseline_root.resolve() if args.baseline_root is not None else None
    print(
        json.dumps(
            check(
                args.source_root.resolve(),
                baseline,
                require_smaller=args.require_smaller,
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
