---
name: bug-fixing
description: Diagnose root causes along real call chains, enforce 2-3 strike blind-fix circuit breaker, and land minimal regression-locked fixes.
---

# 根因诊断与缺陷修复

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。

1. **小修直通 vs 预期/架构升级门禁**：
   - **明确既有契约内的局部小修**：当前会话直接定位 → 最小根因修复 → 相关回归 → 简短返回，零新建文档、零子角色派发。
   - **涉及预期或契约变更**：按 [人工确认](../../workflow/execution-contract.md#人工确认) 区分——不改业务预期的跨模块架构修复复用有效需求，仅对受影响新设计请求确认；改变用户可观察行为或业务规则时先确认受影响需求，再确认设计；涉及支付、权限、数据删除或大范围共享逻辑变更时须先确认范围并安排独立验证。
2. **真实调用链取证与 2～3 次盲修熔断**：
   - 先收集症状、复现条件与真实调用链证据，对照正常路径提出可证伪的根因假设并逐一验证，证据不足严禁直接试改代码；原因不清、跨模块或间歇性故障读取 [系统化缺陷诊断](references/systematic-debugging.md)。
   - **盲修熔断硬锁**：每次修复失败后必须写出区分根因的新证据或新假设；**同一故障连续 2～3 次修复失败且未缩小根因范围时立即停止改代码**，回到调用链与设计契约重新诊断或向主会话汇报阻塞点，严禁叠加猜测补丁或靠放宽断言掩盖问题。
3. **测试锁定与最小修复**：
   - 遵循 [测试先行与根因诊断](../../workflow/execution-contract.md#测试先行与根因诊断)：可自动复现的代码缺陷先用已有或新增失败测试稳定复现 RED，再做最小根因修复达 GREEN 并跑相关边界回归（不为补做形式化 TDD 删除重写既有实现；结果未知的外部操作先查询原调用，禁止自动重放）。
4. **单写交接与按需留痕**：
   - 遵循 [单写归属与中断恢复](../../workflow/handoff.md#单写归属与中断恢复) 与 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛)；同事项返修沿用原事项目录与唯一 `task.md`，仅在复杂根因确需独立归档时按 [人读文档格式](../../workflow/documents.md#人读文档格式) 读取 [复杂缺陷模板](assets/templates/bug-report.md)。
