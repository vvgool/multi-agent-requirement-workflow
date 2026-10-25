---
name: requirement-analysis
description: Clarify missing goals and acceptance decisions in the current task document only when needed.
---

# 按需澄清

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。当前事项文档是目标与进度的唯一记录入口，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，返回结果由文档写入者合并。

先核实用户已有目标和相关实现，只问会影响实现/验收的缺失决策。已有授权和已回答问题不重复询问。小需求目标清楚即可执行，不强制再写需求稿和统一批准。

把必要目标、范围、可验证行为及确认结论写回当前文档，不复制原输入、完整对话或历史版本。用户补充沿用同事项入口，仅在目标独立时新建事项。范围/验收存在分歧或具体风险时按执行约定确认，不能借澄清扩大授权。

默认使用 [任务模板](../../templates/task.md)；复杂业务必要时补例外/失败行为，参考 [澄清指引](references/clarification.md)，不自动拆分为独立的正式需求书。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)。复杂业务规则确需单独展开时读取 [规则补充模板](assets/templates/requirements.md)；当前目标与进度仍记录在 task.md 中，不因模板存在而增加文稿。
