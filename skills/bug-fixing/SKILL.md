---
name: bug-fixing
description: Diagnose root causes along real call chains, enforce 2-3 strike blind-fix circuit breaker, and land minimal regression-locked fixes.
---

# 根因诊断与缺陷修复

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。

1. **小修直通 vs 契约升级门禁**：
   - **既有契约内的明确局部小修**：当前会话直接定位 → 最小根因修复 → 相关回归 → 简短返回，零建档、零派发。
   - **涉及预期或跨模块契约变更**：按 [人工确认](../../workflow/execution-contract.md#人工确认) 对受影响规格发起 `Spec Gate` 确认；触及支付、权限、删数据或大范围共享逻辑时须先确认范围并安排独立验证。
2. **真实调用链取证与 2～3 次盲修熔断**：
   - 先收集复现条件与调用链证据，验证可证伪根因假设，严禁盲试改代码；复杂或间歇性故障读取 [系统化缺陷诊断](references/systematic-debugging.md)。
   - **盲修熔断硬锁**：每次修复失败须写出区分根因的新证据；**同一故障连续 2～3 次修复失败且未缩小根因范围时立即停手**，重核调用链与契约，严禁叠猜测补丁或放宽断言。
3. **测试锁定、单写交接与按需留痕**：
   - 遵循 [契约先行与分层验证](../../workflow/execution-contract.md#契约先行与分层验证)：可自动复现的代码缺陷先用失败测试锁定 `RED`，再最小修复达 `GREEN` 并跑边界回归；未知外部操作先查原调用禁重放。
   - 遵循 [单写归属与中断恢复](../../workflow/handoff.md#单写归属与中断恢复) 与 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛)；仅复杂根因需独立归档时按 [人读文档格式](../../workflow/documents.md#人读文档格式) 读取 [复杂缺陷模板](assets/templates/bug-report.md)。
