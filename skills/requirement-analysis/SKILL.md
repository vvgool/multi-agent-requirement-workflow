---
name: requirement-analysis
description: Design a PRD for complex features or clarify missing goals, user journeys, business rules and acceptance before implementation.
---

# 需求分析与产品设计

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。task.md 是唯一协调和进度入口，相关文档按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 维护，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，返回结果由文档写入者合并。

先按 [路径选择](../../workflow/routing.md#路径选择) 核实职责，不代替协调者另开流程；专业审查由协调者安排，不递归派角色。先核实用户已有目标、相关实现和现有约定，优先记录可定位的代码/配置/测试证据，并区分已确认事实、Agent建议与待验证假设；只问会影响实现/验收的缺失决策。已有授权和已回答问题不重复询问。小需求目标清楚即可执行，不强制再写需求稿和统一批准。

把必要目标、范围、可验证行为及业务确认结论写回需求文档；小事项可合并在 task.md，不复制原输入、完整对话或历史版本。用户补充沿用同事项入口，仅在目标独立时新建事项。范围/验收存在分歧或具体风险时按执行约定确认，不能借澄清扩大授权。

一般事项使用 [任务模板](../../templates/task.md)。复杂需求在实施前按 [产品设计方法](references/clarification.md) 完成问题分析、轻量领域建模、用户旅程、方案取舍和需求自检，将独立 requirements.md 写成可指导设计与验收的 PRD。已有文档按同一内容标准补缺后引用。task.md 只保留目标摘要、当前任务和阻塞链接，不复制完整需求。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)。复杂需求起草或续改前读取 [PRD模板](assets/templates/requirements.md)，并按 [领域建模方法](references/domain-modeling.md) 判断是否需要把术语、实体、状态、不变量和业务责任主体写入 PRD；提交前按产品设计方法核对内容覆盖及可实施性。已有项目格式保留，按内容映射检查，不能以标题齐全代替质量检查。已确认结论持续有效，文档拆分不触发重新澄清或重复批准。区分已确定、可由实施者决定和必须澄清的事项；按 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛) 提交必要独立审查，自检不能替代审查。
