---
name: acceptance-testing
description: Perform independent pre-implementation 4-point alignment review or adversarial runtime acceptance against AC and edge counterexamples.
---

# 独立对齐审查与对抗验收

遵循目标项目既有约定、[路径选择](../../workflow/routing.md#路径选择) 与 [执行约定](../../workflow/execution-contract.md)。本角色必须由**未参与该稿起草或代码实现的独立上下文**承担，只读审查文档与源码、运行必要验证命令，**严禁直接修改业务实现源码或越权改写 `task.md`**（检查结果返回主会话或对应文档单写责任人合并）。

1. **实施前独立对齐审查（`STOP 2` 前置）**：
   - 按 [四项规格对齐与架构审查](../feature-development/references/architecture-review.md) 对照已批需求与设计/计划，固定输出四项诊断：**① 遗漏的 AC、② 擅自扩权范围、③ 模块契约冲突、④ 未证实假设与边界风险**，给出 `可推进 | 需修正复审 | 阻塞` 结论。
   - 按 [人工确认](../../workflow/execution-contract.md#人工确认) 区分 Agent 审查与用户批准：审查 `可推进` 仅允许将设计展示给用户请求批准，绝不代表授权直接写代码。
2. **实施后独立对抗验收（交付前内部闭环）**：
   - 按 [实施与完成门槛](../../workflow/execution-contract.md#实施与完成门槛) 与 [完成前证据门槛](references/completion-gate.md) 核查全部已批 `AC`、单写边界及 [测试先行](../../workflow/execution-contract.md#测试先行与根因诊断) 真实证据。
   - **强制构造并亲自运行对抗反例**：开发自验报告仅作背景参考，不能替代独立验收；必须针对本次最高风险行为亲自运行正向检查及**至少 1 个破坏性/边界/异常反例**，凭真实命令退出码与实际输出判定。
3. **结论枚举与报告维护**：
   - 验收结论严格使用 `通过 | 有条件通过 | 未完成 | 阻塞`；内部验收抓出非白名单缺陷时返回可复现输入与预期偏差，由主会话安排返修并重跑受影响范围复验。
   - 按 [文档分工](../../workflow/documents.md#按复杂度选择文档) 与 [人读文档格式](../../workflow/documents.md#人读文档格式)，复杂事项维护 `verification.md` 或按需使用 [独立验收报告模板](assets/templates/test-report.md)，保留首次失败与复验闭环记录。
