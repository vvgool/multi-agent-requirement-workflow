---
name: requirement-analysis
description: Clarify business goals, edge rules and verifiable AC with code grounding for task.md or unified spec.md.
---

# 需求分析与产品规格

遵循目标项目既有约定、[执行约定](../../workflow/execution-contract.md) 与 [文档分工](../../workflow/documents.md#按复杂度选择文档)。明确局部小修直接完成，不建需求文档；持续事项以 `task.md` 为唯一状态与批准入口，复杂跨模块事项将业务 `F/AC` 写入统一 `spec.md`。

1. **先读代码取证，合并澄清分叉**：
   - 先核实相关代码、配置与现有测试，区分**已证实事实、推荐默认值、待决业务分叉**；常规可逆工程细节不打断用户。
   - 按 [人工确认](../../workflow/execution-contract.md#人工确认) 将真正影响范围或验收的必答分叉**一次性合并提出**（意图明确时直接进入规格合稿以发起单次 `Spec Gate`；仅超大模糊范围可选先停 `pending_req_approval` 锁边界；仅回答业务参数或工具返回 `accepted:true` 绝不等于批准）。
2. **按复杂度产出可判定 AC**：
   - 常规事项按 [任务模板](../../templates/task.md) 在 `task.md` 直接维护目标与可判定 `AC`。
   - 复杂事项按 [统一规格模板](../../templates/spec.md)（`§1 目标、边界与验收标准`，零状态头、零复选框）与 [产品规格方法](references/clarification.md)（涉及多角色权限或持久状态时读 [轻量领域建模](references/domain-modeling.md)），输出稳定编号（`F-xx` / `AC-xx`）及非目标（Non-Goals）。
3. **正交格式与 Delta 续改**：
   - 遵循 [人读文档格式](../../workflow/documents.md#人读文档格式) 与 [Delta 差量规范](../../workflow/documents.md#delta-差量续改与归档)：可变状态与 `## 本次请确认` 唯一归属 `task.md`（经 `verify_feature.py --phase spec-gate` 校验）；续改就地更新当前有效规则并注简短 `Delta`，不建版本目录。
