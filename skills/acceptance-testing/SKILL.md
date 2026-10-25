---
name: acceptance-testing
description: Independently verify relevant work when requested or warranted by concrete risk and report actual findings.
---

# 按需独立验证

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。task.md 是唯一协调和进度入口，相关文档按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 维护，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，返回结果由文档写入者合并。

用户要求、具体风险或跨角色需要时独立验证，无需作为所有任务的必经阶段。读取目标与允许范围、相关实际改动、已验与未决项，核对当前内容；需要时才保存相关版本，不默认建立覆盖整个项目的逐文件基线。

依据行为选择已有检查、集成/异常/回归或实际操作，不为低风险可逆文稿修改新增镜像测试。不修改业务源码。已有自验结果可辅助判断，但不能据此判定本角色独立验收通过。当前内容或环境发生变化时，重新验证受影响的范围，未执行不报通过。

返回实际范围、检查与结果、可复现缺陷和限制；由当前文档写入者合并，无强制test-cases/test-report/result文件。保留失败事实，修复和复验继续更新原文档，不新建版本目录。复杂验收按验证对象、环境、权限及恢复场景维护 verification.md 或已有报告，task.md 只引用验证摘要，不等文档过长才拆。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)，复杂验收读取 [报告模板](assets/templates/test-report.md)，复杂用例读取 [用例模板](assets/templates/test-cases.md)。用例说明预期，实际结果记录在 task.md 或必要报告中并引用，避免多处维护。
