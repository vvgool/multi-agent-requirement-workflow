---
name: feature-development
description: Draft cohesive Contract-First specs, run controlled Spikes when needed, and execute stratified TDD/SDD implementation with write-boundary checks.
---

# 契约设计与开发实施

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。

1. **小修直通、受控 `Spike` 与贯通起草 `Spec Gate`**：
   - **明确局部低风险小修**：当前会话直接定位 → 最小修改 → 相关回归 → 简短返回，零建档、零派发。
   - **受控 `Spike` 探索**：UI 体感或高不确定技术选型需先看原型才能敲定 `AC` 时，限显式隔离路径且禁触高危/非幂等外部写，收敛后转入 `Spec Gate` 补正式契约，严禁将纯原型标为 `verified`。
   - **需对齐事项**：复杂或状态性事项按 [方案与拆分方法](references/design-and-decomposition.md) 一次性贯通产出 `spec.md`（§1 `F/AC` + §2 `Contract-First` 签名与单元切分），后台先过 1 次异体 [四项规格对齐审查](references/architecture-review.md) 与 [verify_feature.py](../acceptance-testing/scripts/verify_feature.py) `--phase spec-gate`，再按 [人工确认](../../workflow/execution-contract.md#人工确认) 发起单次 `Spec Gate`（`pending_approval → ready_to_implement`）。
2. **`Contract-First` 分层验证与静音连续巡航**：
   - 遵循 [项目开发原则](references/development-principles.md) 与 [契约先行与分层验证](../../workflow/execution-contract.md#契约先行与分层验证)：业务/脚本代码执行 `Contract-First` + 行为级 TDD（先落契约与失败测试核实真实 `RED`，再实现达 `GREEN`）；文档/规则演进执行 `SDD` + 纯结构/拓扑门禁校验，不写跨文件措辞快照。
   - `ready_to_implement` 后遵循 [静音连续巡航与抗偏航](../../workflow/execution-contract.md#静音连续巡航与抗偏航)：除 3 类白名单真阻塞外连续推进；同一故障连续 2～3 次修复失败无新根因证据立即熔断停手。
3. **锚点回读、正交模板与单写边界**：
   - 每完成一单元须**只读回读 `task.md` 目标与关联 `AC`/契约原文**确认无缩水无越界（主会话唯一单写 `task.md`，可配合 `verify_feature.py --check-writes` 核验写集）。
   - 遵循 [人读文档格式](../../workflow/documents.md#人读文档格式) 与 [Delta 差量规范](../../workflow/documents.md#delta-差量续改与归档)，按需读取 [任务模板](../../templates/task.md)、[统一规格模板](../../templates/spec.md) 或 [验证报告模板](../acceptance-testing/assets/templates/verification.md)。
