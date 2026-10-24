#!/usr/bin/env python3
"""Read-only protocol3 entry consistency and rule-size regression.

No model execution, runtime, token meter, installation or native acceptance.
The named scenarios are static contract checks, not business E2E tests.
"""
import argparse
import json
from pathlib import Path

ENTRY_FILES = [
    "agents/coordinator-agent.md", "agents/product-agent.md",
    "agents/development-agent.md", "agents/testing-agent.md", "agents/bug-agent.md",
    "workflow/execution-contract.md", "workflow/routing.md", "workflow/revisions.md",
    "workflow/handoff.md", "workflow/output-layout.md", "workflow/code-baseline.md",
    "skills/requirement-analysis/SKILL.md", "skills/feature-development/SKILL.md",
    "skills/bug-fixing/SKILL.md", "skills/acceptance-testing/SKILL.md",
    "skills/setup-requirement-workflow/assets/templates/role-body.md",
    "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
]


def check(root, baseline):
    texts = {p: (root / p).read_text(encoding="utf-8") for p in ENTRY_FILES}
    framework = (root / "framework.yaml").read_text(encoding="utf-8")
    lock = (root / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml").read_text()
    assert "protocol_version: 3" in framework and 'version: "0.6.0"' in framework
    assert "protocol_version: 3" in lock
    role = texts["skills/setup-requirement-workflow/assets/templates/role-body.md"]
    assert "不要求task.yaml" in role and "旧协议任务回原锁定包" in role
    assert "原生任务已有的派发/结束事实不重复落盘" in role
    for path in [p for p in ENTRY_FILES if p.startswith("agents/")]:
        assert "不要求task.yaml" in texts[path] and "单写" in texts[path], path
    entry = texts["skills/setup-requirement-workflow/assets/templates/project-entry-light.md"]
    assert entry.index("独立一次性") < entry.index("需要上述框架能力时")
    assert "无需读取workflow.lock.yaml、检查缓存" in entry
    assert "已有旧任务仍按原锁原包续接" in entry
    assert "本入口的授权、风险和未知操作边界" in entry
    execution = texts["workflow/execution-contract.md"]
    revisions = texts["workflow/revisions.md"]
    assert "无需先建文档、清单、计划或宿主原生任务" in execution
    assert "原因未知先由同一角色" in execution
    assert "不默认全量测试" in execution and "无意义测试" in execution
    assert "小任务在原文档列任务后" not in execution
    assert "消息提供当前任务文档路径" not in role
    assert "付款、权限、数据删除或大范围共享逻辑变更" in execution
    assert "另由一名角色独立验证" in execution
    assert "未知不等于结束" in execution and "不重复派发或重放外部操作" in execution
    assert "补充、修改验收、修复、重试、普通继续与完成后续改" in revisions
    assert "只有独立目标才新建事项" in revisions and "不删除、不合并、不静默迁移" in revisions
    task = (root / "templates/task.md").read_text()
    assert all(title in task for title in ["目标与范围", "- [ ]", "验证与未决项"])
    assert not any(field in task for field in ["baseline_id", "invocation_id", "delivery_id", "revision"])
    before = sum((baseline / p).stat().st_size for p in ENTRY_FILES if (baseline / p).is_file())
    after = sum(len(t.encode("utf-8")) for t in texts.values())
    assert after < before, (before, after)
    return dict(protocol=3, entry_files=len(texts),
                scenarios=["simple-document-or-known-fix", "same-item-continued-after-completion",
                           "cross-role-single-writer", "risk-confirmation-independent-verification",
                           "unknown-external-operation-no-replay", "old-lock-no-migration"],
                selected_rule_utf8_bytes=dict(before=before, after=after),
                scope="static contract consistency only; not native execution, tokens or elapsed time")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.source_root.resolve(), args.baseline_root.resolve()), ensure_ascii=False))


if __name__ == "__main__":
    main()
