---
name: feature-development
description: Draft cohesive Contract-First specs, run controlled Spikes when needed, and execute stratified TDD/structural implementation with anti-drift checks.
---

# 契约设计与开发实施

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。

1. **小修直通、受控 `Spike` 与贯通起草 `Spec Gate`**：
   - **明确局部低风险小修**：当前会话直接定位 → 最小修改 → 相关回归 → 简短返回，零建档、零派发。
   - **受控 `Spike` 探索**：UI 体感或高不确定技术选型确需先看可运行原型才能敲定 `AC` 时，仅限显式隔离路径且禁触高危/非幂等外部写，收敛方向后转入 `Spec Gate` 补正式契约与验证；严禁将探针/夹具拆成多轮微型审批循环，严禁将纯原型/探针通过标为 `verified`。
   - **需对齐事项**：复杂或状态性事项按 [方案与拆分方法](references/design-and-decomposition.md) 产出 `spec.md`（业务意图已清晰时一次性贯通完成 §1 `F/AC` 与 §2 `Contract-First` 签名及单元切分，避免多角色串行拼稿），**在打断用户前先由 1 个异体独立会话完成 [四项规格对齐审查](references/architecture-review.md) 无阻断**，随后按 [人工确认](../../workflow/execution-contract.md#人工确认) 发起单次 `Spec Gate`（`pending_approval → ready_to_implement`）获批后才修改正式业务源码。
2. **`Contract-First` 分层验证与静音连续巡航**：
   - 遵循 [项目开发原则](references/development-principles.md) 与 [契约先行与分层验证](../../workflow/execution-contract.md#契约先行与分层验证)：业务/脚本代码执行 `Contract-First` + 行为级 TDD（先落接口契约与失败测试核实真实 `RED`，再实现达 `GREEN`）；文档/规则演进执行 `SDD` + 纯结构/拓扑不变量校验，不写跨文件散文措辞快照。
   - 进入 `ready_to_implement` 后遵循 [静音连续巡航与抗偏航](../../workflow/execution-contract.md#静音连续巡航与抗偏航)：除 3 类白名单真阻塞外连续推进；同一故障**连续 2～3 次修复失败且未缩小根因范围时立即熔断停手**。
3. **单元锚点只读回读与单写交接**：
   - `task.md` 是全事项唯一进度控制面且**由主会话（Coordinator）单写更新**；实施单元每完成一步必须**只读回读 `task.md` 目标及对应 `AC`/接口契约原文**，确认无缩水无越界。
4. **正交模板与格式**：
   - 遵循 [人读文档格式](../../workflow/documents.md#人读文档格式) 与 [Delta 差量规范](../../workflow/documents.md#delta-差量续改与归档)，按需读取 [任务模板](../../templates/task.md)、[统一规格模板](../../templates/spec.md) 或 [验证报告模板](../acceptance-testing/assets/templates/verification.md)（验证报告唯一写入人见 [文档分工](../../workflow/documents.md#按复杂度选择文档)）。
