---
name: feature-development
description: Use when development-agent receives an approved feature or defect-fix task, including module planning, ordinary execution, and resuming interrupted development.
---

# 开发工作流

在已批准范围内完成实现与完整功能自验。文档按复杂度裁剪，执行方式按模块选择；两者分别判断。

## 接单与开发原则

读取 task.yaml、status.yaml、批准文稿及目标项目适用规则，核对任务、审批和授权；业务决策缺失返回 needs_input，必需资料或执行条件缺失返回 blocked。根状态由协调层维护。

先读 [开发原则](references/development-principles.md)：遵循适用项目规则和已有架构约定；缺少约定时按 Clean Architecture 的职责划分和依赖方向做最小设计。规则来源和技术选择记入下述文档，不另建原则报告。

## 选择文档档位

阅读 [阶段流程](references/workflow.md)，分析代码后按实际影响选择：

| 档位 | 适用条件 | 读取真实模板并生成到 task.output_dir |
| --- | --- | --- |
| 简版 | 范围清楚、局部低风险，依赖和验证路径简单 | [开发记录](assets/templates/development.md) → development.md |
| 完整版 | 跨多个业务模块/系统、关键接口或数据迁移、高风险行为，或技术不确定性需要展开 | [方案](assets/templates/technical-plan.md)、[计划](assets/templates/implementation-plan.md)、[自验](assets/templates/verification.md) → 对应同名文件 |

用一句话记录档位及理由；不按行数或工期机械分类。小需求可以只有一个模块、少量可验证任务。每模块仍按复杂度、依赖及恢复需要选择普通/长任务，完整文档不代表所有模块都要长任务。

先读取模板再填实际内容，替换占位符；只生成适用档位，不额外生成空方案、改动清单或检查点文件。已有文稿、旧 run 和证据保留，按索引读取，不为统一格式批量重建。简版升级时引用已有内容、补足缺项即可。

## 规划、执行与恢复

修改代码前明确方案、任务及检查方法。大需求先拆独立可验证模块并按依赖排序，再拆小任务并逐模块选模式。简版将这些信息合并在一页，不制造没有实际意义的层级。

- 普通模块按 [普通执行](references/normal-execution.md) 实施。
- 长任务或恢复按 [恢复指引](references/long-execution.md) 实施，恢复信息放当前计划的条件章节。

计划只维护进度和证据引用，验证记录维护检查事实。同一真实检查能满足多个条件时执行一次并引用，不重复抄写；真实集成要求仍须满足。使用当前宿主工具即可，不依赖个人安装的辅助 Skill 或后台服务。

## 自验与交接

所有批准需求都需完整功能自验，包含适用的集成、异常和回归。简版写在 development.md，完整版写在 verification.md；改动及限制并入该交付记录。未执行不预填通过，局部通过不代替整体自验。

按 [结果模板](../../templates/role-result.yaml) 生成 result.yaml。身份、阶段结果及最终代码基线统一以它为交接来源，文档引用即可；基线覆盖相关源码与未提交改动，排除报告和日志自身。artifacts 每项含 kind/path，路径相对当前输出目录：简版可用 kind: development_record，完整版用 technical_plan、implementation_plan、verification。

ready 要求全部必需任务/模块检查及整体自验通过、无影响交付的未解决项、基线对应已验证代码。否则继续修复或如实返回 needs_input/blocked。向协调层返回实际产物和结果路径；交接按实际内容核对，不要求简版提供完整版文件名。
