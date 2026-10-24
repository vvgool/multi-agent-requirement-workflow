---
name: acceptance-testing
description: Independently verify relevant work when requested or warranted by concrete risk and report actual findings.
---

# 按需独立验证

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。当前事项文档是唯一目标与进度来源，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本Skill解释旧权限。共享文档单写，返回结果由文档写入者合并。

用户要求、具体风险或跨角色需要时独立验证，不是所有任务的必经阶段。读取目标与允许范围、相关实际改动、已验与未决项，核对当前内容；需要时才保存相关版本，不能默认全项目逐文件基线。

依据行为选择已有检查、集成/异常/回归或实际操作，不为低风险可逆文稿修改新增镜像测试。不修改业务源码。既有自验可辅助判断但不当成本角色独立通过。当前内容/环境变化重验受影响范围，未执行不报通过。

返回实际范围、检查与结果、可复现缺陷和限制；由当前文档写入者合并，无强制test-cases/test-report/result文件。失败保留事实，修复/复验继续原文档，不建版本。模板仅在确需独立长报告时参考。
