---
name: requirement-analysis
description: Clarify goals and acceptance when needed; maintain requirements separately for complex features.
---

# 按需澄清

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。task.md 是唯一协调和进度入口，相关文档按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 维护，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，返回结果由文档写入者合并。

先核实用户已有目标和相关实现，只问会影响实现/验收的缺失决策。已有授权和已回答问题不重复询问。小需求目标清楚即可执行，不强制再写需求稿和统一批准。

把必要目标、范围、可验证行为及业务确认结论写回需求文档；小事项可合并在 task.md，不复制原输入、完整对话或历史版本。用户补充沿用同事项入口，仅在目标独立时新建事项。范围/验收存在分歧或具体风险时按执行约定确认，不能借澄清扩大授权。

一般事项使用 [任务模板](../../templates/task.md)。复杂需求在实施前形成或引用独立 requirements.md，明确场景、范围、业务规则、异常/权限预期及验收标准；参考 [澄清指引](references/clarification.md)。task.md 只保留目标摘要、当前任务和阻塞链接，不复制完整需求。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)。复杂需求读取 [需求模板](assets/templates/requirements.md)；已有项目需求文档直接引用。已确认结论持续有效，文档拆分不触发重新澄清或重复批准。
