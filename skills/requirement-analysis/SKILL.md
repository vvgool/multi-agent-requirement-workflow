---
name: requirement-analysis
description: Clarify business goals, edge rules and verifiable AC with code grounding, or write a focused PRD before design.
---

# 需求分析与产品设计

遵循目标项目既有约定、[执行约定](../../workflow/execution-contract.md) 与 [文档分工](../../workflow/documents.md#按复杂度选择文档)。明确局部低风险小修直接完成，不建需求文档；需持久跟踪的事项以 `task.md` 为唯一进度入口（主会话单写勾选），复杂跨模块需求单独维护 `requirements.md`。

1. **先读代码取证，一次性合并必答提问**：
   - 先核实相关代码、配置与现有测试，区分**已证实事实、Agent 推荐默认值、待确认业务决策**；能从代码确认或属常规可逆工程细节的不打断用户。
   - 按 [人工确认](../../workflow/execution-contract.md#人工确认) 将真正影响产品范围、用户可观察行为、权限或验收的必答问题**一次性合并提出**，展示当前需求稿并将首屏置为 `pending_req_approval`。
   - 用户仅补充业务答案或提问工具仅返回受理回执（如 `accepted:true`）不等于需求获批；须合入答案展示完整需求，待用户明确批准（`req_approved`）后才进入正式设计。
2. **按复杂度产出可判定 AC**：
   - 一般事项直接按 [任务模板](../../templates/task.md) 在 `task.md` 合并维护目标与可判定 AC。
   - 复杂需求读取 [PRD 模板](assets/templates/requirements.md) 与 [产品设计方法](references/clarification.md)（涉及多角色权限、持久状态或不变量时按需读取 [轻量领域建模](references/domain-modeling.md)），输出覆盖正常、关键异常与边界条件的稳定编号（`F-xx` / `AC-xx`）及明确非目标（Non-Goals）。
3. **首屏可读与 Delta 差量续改**：
   - 创建或更新文档时遵循 [人读文档格式](../../workflow/documents.md#人读文档格式) 与 [Delta 差量规范](../../workflow/documents.md#delta-差量续改与归档)：同事项补充直接更新当前有效规则并简述 `Delta（原规则 → 现规则）`，不新建版本目录；实质变更范围或验收时仅重确认受影响部分。
