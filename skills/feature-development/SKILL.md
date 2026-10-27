---
name: feature-development
description: Design and decompose complex features into modules and verifiable delivery tasks, or implement scoped work with relevant verification.
---

# 开发

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。一次性、局部低风险且目标明确的小修在当前会话直接定位、最小修复、相关回归并简短返回，无需先建文档、清单、计划或原生任务；需要持久跟踪才维护一个协调入口，需要委派才用原生任务；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，需要长期保留的结果由文档写入者合并。

按需要读取已有文档、相关代码与 [项目开发原则](references/development-principles.md)。明确允许改动的范围和验证方法；简单修改直接执行，原因未知先同一角色定位；跨会话恢复、交接或多步持久跟踪才补文档。复杂需求实施前读取 [方案与拆分方法](references/design-and-decomposition.md) 及下方技术设计、实施计划模板；按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 检查PRD输入，形成方案、模块边界与契约，再拆可验证的交付任务，完成需求覆盖、契约一致和可执行性自检。按复杂度拆分，不等文档过长才拆。跨能力或架构影响型变更按需读取 [架构审查与复盘](references/architecture-review.md)。

实施行为代码或修复前读取 [测试先行](../../workflow/test-first.md)，默认对可自动验证业务行为执行真实RED/GREEN及必要重构，例外说明原因与替代验证。路径选择见 [路由](../../workflow/routing.md#路径选择)，阶段就绪、复杂需求实施前独立审查及最终独立验收遵循 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛)。技术审查由未参与起草的开发专长承担；需要审查时请协调者安排，不自行递归委派，起草者自检不能替代。原需求已确定则引用，不重写PRD。

当前进度只在 task.md 勾选，详细单元维护在 implementation-plan.md；需要另一专长时交由协调者安排对应原生任务，一个事项可有多个实施任务。修改遵循既有调用链与架构，不借机重构无关内容。修复先确认错误行为；适用时用已有检查或有意义的回归验证修复前后的行为差异。失败按新证据查因，反复失败且没有新证据时，停止盲目修改。

按影响完成相关自验和必要集成/异常检查，不默认全量测试或无意义新增测试，记录真实通过、失败、未执行及限制，已有证据适用时注明未重跑。交接仅返回实际改动、检查和未决项，适用时附真实RED/GREEN证据；代码阅读、自验和独立验收分别说明。需要避免验证错内容时才按 [内容定位](../../workflow/code-baseline.md) 记录相关版本，不对整个项目逐文件计算摘要。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)，按实际产物读取 [任务](../../templates/task.md)、[设计](assets/templates/technical-plan.md)、[实现说明](assets/templates/development.md)、[依赖与步骤](assets/templates/implementation-plan.md) 或 [验证](assets/templates/verification.md) 模板。设计保存为 technical-design.md，计划保存为 implementation-plan.md，复杂验收使用 verification.md；已有对应文档直接引用。各类正文分别维护，任务勾选只在 task.md；一次性小修不为加载规范而产稿。
