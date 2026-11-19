---
name: feature-development
description: Design modular technical contracts, decompose verifiable units, and execute TDD implementation with anti-drift anchor checks.
---

# 功能设计与开发实施

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。

1. **小修直通 vs 复杂设计门禁**：
   - **明确局部低风险小修**：当前会话直接定位 → 最小修改 → 相关回归 → 简短返回，零建档、零派发。
   - **需对齐事项**：按 [人工确认](../../workflow/execution-contract.md#人工确认) 核实处于 `req_approved`；复杂或状态性需求按 [方案与拆分方法](references/design-and-decomposition.md) 产出 `technical-design.md`（含 `文件变更与单元切分` 表，不另建实施计划文件），经独立角色完成 [四项规格对齐审查](references/architecture-review.md) 无阻断后请求批准，进入 `ready_to_implement` 后才写业务代码。可行性探针须在 `STOP 2` 前最小取证或并入已批 `T1`，严禁将探针/测试夹具拆成多轮 `pending_design_approval` 循环，未完成对应业务源码实现前严禁将纯探针/夹具通过标为 `verified`。
2. **测试先行（TDD）与静音连续巡航**：
   - 遵循 [项目开发原则](references/development-principles.md) 与 [测试先行与根因诊断](../../workflow/execution-contract.md#测试先行与根因诊断)：可自动验证的行为先写失败测试核实真实 RED，再最小实现达 GREEN 并必要重构，不借机重构无关代码。
   - 进入 `ready_to_implement` 后遵循 [静音连续巡航与抗偏航](../../workflow/execution-contract.md#静音连续巡航与抗偏航)：除 3 类白名单真阻塞外连续推进；同一故障**连续 2～3 次修复失败且未缩小根因范围时立即熔断停手**，转系统化根因诊断重核调用链与设计契约。
3. **单元锚点只读回读与单写交接**：
   - `task.md` 是唯一进度勾选清单且**统一由主会话（Coordinator）单写更新**；实施单元仅在允许写入边界内修改。
   - **每完成一个实施单元，必须只读回读 `task.md` 首屏目标及对应 `AC`/接口契约原文**，确认无缩水无越界，返回结构化结果与真实运行输出。
4. **按需加载模板与格式**：
   - 写文档遵循 [人读文档格式](../../workflow/documents.md#人读文档格式) 与 [Delta 差量规范](../../workflow/documents.md#delta-差量续改与归档)，按需读取 [任务模板](../../templates/task.md)、[技术设计模板](assets/templates/technical-design.md) 或 [验证报告模板](../acceptance-testing/assets/templates/verification.md)（开发仅在返回卡片上报 RED→GREEN，验证报告唯一写入人见 [文档分工](../../workflow/documents.md#按复杂度选择文档)）。
