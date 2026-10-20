---
name: acceptance-testing
description: Use when testing-agent receives an approved feature baseline for acceptance or defect regression, including requirement drift, incorrect existing cases, and baseline mismatch checks.
---

# 需求验收与回归

独立核对已批准需求、实际开发基线和用例，执行验收并返回真实结论。项目适用规则和测试约定优先；开发自验只作输入，不能代替独立证据。内部run及原始证据链接留本run执行记录。

接单及交付前遵循 [阶段执行契约](../../workflow/execution-contract.md)，统一核对身份、授权、结果位置和过期任务。正式文稿及根状态由协调层维护。

## 接单与基线

完成执行契约核对后，按开发交付索引读取记录和已有用例。开发简版一份记录或完整版多文档都可接受，按实际内容读取，不要求固定文件名。

按 [代码基线契约](../../workflow/code-baseline.md) 在接单和结束时核对实际源码、范围及相关未提交改动，绑定任务和原开发交付；不符时保留差异并返回 blocked。

## 文档选择

先读 [测试流程与判定](references/workflow.md)，再读所需真实模板，在 task.output_dir 生成实例：

| 条件 | 模板与输出 |
| --- | --- |
| 默认 | [测试报告](assets/templates/test-report.md) → test-report.md，合并用例、偏离核对、缺陷及结论 |
| 用例矩阵、环境或步骤复杂到影响报告阅读 | 额外使用 [用例](assets/templates/test-cases.md) → test-cases.md；报告引用用例编号及必要观察，不重抄 |

仅拆分用例时说明理由。源模板、旧用例及开发资料保持不变；填写实际内容并删除不适用的条件段，已有用例通过链接引用。

## 检查、执行与交接

按已读测试流程建立 AC/TC 覆盖、核对需求/实现/用例偏离，独立执行必验项及受影响回归。用例修正、部分阻塞后的执行范围、证据复用及 passed/failed/blocked 门槛统一按该流程判断，不另建覆盖或偏离报告。

按 [公共结果模板](../../templates/role-result.yaml) 在指定结果位置写 result.yaml，填实际验收结果、development_run_id、基线、缺陷和限制；artifacts 每项含 kind/path，相对本 run 输出。passed/failed/blocked 按流程门槛判断，报告与结果一致。

业务源码修复交开发，需求歧义交协调层；改变批准正文须进入新修订评审。向协调 Agent 返回结果路径、状态及简要结论。
