---
name: acceptance-testing
description: Independently verify relevant work when requested or warranted by concrete risk and report actual findings.
---

# 独立审查与验证

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。task.md 是唯一协调和进度入口，相关文档按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 维护，原生任务保留派发和结束事实；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，返回结果由文档写入者合并。

按 [路径选择](../../workflow/routing.md#路径选择) 和 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛) 核对本次责任：复杂需求须实施前独立审查与最终独立验收，一般小修无需一律派测试。测试专长审查可验收性和遗漏场景；架构、接口质量由未参与起草的开发专长审查，协调者安排，不由测试角色自行递归派发。独立审查不等于已运行测试。读取目标与允许范围、相关实际改动、已验与未决项，核对当前内容；需要时才保存相关版本，不默认建立覆盖整个项目的逐文件基线。最终报告或勾选整体完成前，按 [完成前证据门槛](references/completion-gate.md) 逐项核对；结果可为通过、有条件通过、未完成或阻塞，不能用测试全绿替代范围、环境和独立验收证据。

实施前审查与验收时读取 [验证方法](references/workflow.md)，检查开发或Bug测试证据时读取 [测试先行](../../workflow/test-first.md)。依据行为选择已有检查、集成/异常/回归或实际操作，不为低风险可逆文稿修改新增镜像测试。不修改业务源码。已有自验结果可辅助判断，但不能据此判定本角色独立验收通过。当前内容或环境发生变化时，重新验证受影响的范围，未执行不报通过。

复杂需求或方案审查时，按 [内容质量检查](../../workflow/documents.md#复杂需求的内容质量) 核对PRD、模块边界、任务及验收的对应关系；模板标题齐全不代表内容合格，开发自检不等于独立验证。

返回实际范围、检查与结果、可复现缺陷和限制；由当前文档写入者合并，无强制test-cases/test-report/result文件。保留失败事实，修复和复验继续更新原文档，不新建版本目录。复杂验收按验证对象、环境、权限及恢复场景维护 verification.md 或已有报告，task.md 只引用验证摘要，不等文档过长才拆。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)，复杂验收读取 [报告模板](assets/templates/test-report.md)，复杂用例读取 [用例模板](assets/templates/test-cases.md)。用例说明预期，实际结果记录在 task.md 或必要报告中并引用，避免多处维护。
