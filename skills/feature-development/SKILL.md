---
name: feature-development
description: Implement scoped work with a task document and relevant verification, without mandatory stage records.
---

# 开发

遵循目标项目规则及 [执行约定](../../workflow/execution-contract.md)。一次性、局部低风险且目标明确的小修在当前会话直接定位、最小修复、相关回归并简短返回，无需先建文档、清单、计划或原生任务；需要持久跟踪才维护一份事项文档，需要委派才用原生任务；不创建机器业务账本、逐轮快照或版本目录。旧任务回原锁定包，不以本 Skill 解释旧任务的权限。共享文档单写，需要长期保留的结果由文档写入者合并。

按需要读取已有文档、相关代码与 [项目开发原则](references/development-principles.md)。明确允许改动的范围和验证方法；简单修改直接执行，原因未知先同一角色定位；跨会话恢复、交接或多步持久跟踪才补文档。复杂逻辑只在需要时补必要方案与依赖。确需较长的设计说明时才拆分文件，避免为每次交接生成方案、计划、自验三件套。

有文档时只在原文档勾选，不为小步骤新增文档或原生任务。修改遵循既有调用链与架构，不借机重构无关内容。修复先确认错误行为；适用时用已有检查或有意义的回归验证修复前后的行为差异。失败按新证据查因，反复失败且没有新证据时，停止盲目修改。

按影响完成相关自验和必要集成/异常检查，不默认全量测试或无意义新增测试，记录真实通过、失败、未执行及限制，已有证据适用时注明未重跑。交接仅返回改动、检查和未决项。需要避免验证错内容时才按 [内容定位](../../workflow/code-baseline.md) 记录相关版本，不对整个项目逐文件计算摘要。

仅在创建或更新人读文档时读取 [格式规范](../../workflow/documents.md#人读文档格式)，按实际产物读取 [任务](../../templates/task.md)、[设计](assets/templates/technical-plan.md)、[实现说明](assets/templates/development.md)、[依赖与步骤](assets/templates/implementation-plan.md) 或 [验证](assets/templates/verification.md) 模板。补充稿解释细节，任务勾选只在 task.md；一次性小修不为加载规范而产稿。
