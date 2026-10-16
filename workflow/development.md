# 开发阶段工作流入口

开发阶段流程已收敛到 [feature-development Skill](../skills/feature-development/SKILL.md)。开发 Agent 接单后读取入口，按其中指针加载阶段流程、普通/长任务执行指引和真实文档模板。

模块排序、小任务、执行模式、检查点及完整自验规则维护在 Skill 内；本文件保留为已有引用的兼容入口。结果继续使用框架公共角色结果格式，根状态仍由协调 Agent 更新。
