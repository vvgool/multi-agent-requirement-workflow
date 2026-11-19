---
name: acceptance-testing
description: Perform independent pre-gate 4-point alignment review, differential write-boundary checks, and adversarial runtime acceptance with verify_feature.py gates.
---

# 独立对齐审查与对抗验收

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。必须由**未参与该稿起草或代码实现的独立上下文**承担，只读审查文档与业务源码并运行验证命令，不越权修改业务源码或 `task.md`。

1. **实施前独立对齐审查（`Spec Gate` 后台前置）**：
   - 按 [四项规格对齐与架构审查](../feature-development/references/architecture-review.md) 比对 `spec.md`（`§1` `F/AC` vs `§2` 契约与 `T1..Tn`），固定输出四项诊断：**① 遗漏的 AC、② 擅自扩权范围、③ 模块契约冲突、④ 未证实假设与边界风险**，给出 `可推进 | 需修正复审 | 阻塞`。
   - 配合纯标准库门禁 [verify_feature.py](scripts/verify_feature.py) 运行 `--feature-dir <事项目录> --phase spec-gate` 校验状态头、批准待定态与单元集合一致性；按 [人工确认](../../workflow/execution-contract.md#人工确认)，审查 `可推进` 仅允许呈交 `Spec Gate`，绝不等于获准改源码。
2. **实施后独立对抗验收与差量写集核验**：
   - 必须使用与前期审查不同的全新会话，按 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛)、[完成前证据门槛](references/completion-gate.md) 与 [契约先行与分层验证](../../workflow/execution-contract.md#契约先行与分层验证) 核查全部已批 `AC`（可运行 `verify_feature.py --check-writes --repo-root . [--since <snap.json>] --feature-dir <事项目录> --allow <允许写集...>` 校验单写边界）。
   - **强制构造并亲自运行对抗反例**：针对最高风险行为亲自运行正向检查及**至少 1 个破坏性/边界/异常反例**，凭真实退出码与输出判定。
3. **结论维护与最终 `--phase verified` 关门核验**：
   - 结论严格使用 `通过 | 有条件通过 | 未完成 | 阻塞`；抓出非白名单缺陷时返回复现输入交主会话内部返修复验。
   - 按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 与 [人读文档格式](../../workflow/documents.md#人读文档格式)，复杂事项按 [验证报告模板](assets/templates/verification.md) 由同批次唯一写入人维护 `verification.md`。**主会话完成最后一笔 `task.md` `verified` 回写后，必须运行 `verify_feature.py --feature-dir <事项目录> --phase verified` 通过方可交付**。
