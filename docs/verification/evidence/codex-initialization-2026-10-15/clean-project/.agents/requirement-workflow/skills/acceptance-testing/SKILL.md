---
name: acceptance-testing
description: Use when testing-agent receives an approved feature baseline for acceptance or defect regression, including requirement drift, incorrect existing cases, and baseline mismatch checks.
---

# 需求验收与回归

独立核对已批准需求、实际开发基线和用例，执行验收并返回真实结论。项目适用规则和测试约定优先；开发自验只作输入，不能代替独立证据。

## 接单与基线

读取 task.yaml、status.yaml、批准文稿、项目规则和开发结果索引。核对 feature_id、requirements_revision、run_id、role=testing、active_run、审批及 development_run_id。开发简版一份记录或完整版多文档都可接受，按实际内容读取，不要求固定文件名。

比较实际源码与任务/开发交付中的基线，包括相关未提交改动。基线不符或必需资料无法核实时返回 blocked，记录差异，等待协调层重新绑定；不能把旧证据用于当前代码。旧任务返回 stale_task，由协调层记录，避免写入新版任务。

## 文档选择

先读 [测试流程与判定](references/workflow.md)，再读所需真实模板，在 task.output_dir 生成实例：

| 条件 | 模板与输出 |
| --- | --- |
| 默认 | [测试报告](assets/templates/test-report.md) → test-report.md，合并用例、偏离核对、缺陷及结论 |
| 用例矩阵、环境或步骤复杂到影响报告阅读 | 额外使用 [用例](assets/templates/test-cases.md) → test-cases.md；报告引用用例编号及执行证据，不重抄 |

用一句话说明拆分理由；不因开发采用完整版就自动拆测试文档。源模板、旧用例及开发资料保持不变；填写实际内容，无需创建单独偏离报告、空缺陷清单或无意义的环境表。

## 检查、执行与交接

用例预期来自批准需求。已有用例也要核对，发现错误时在当前测试输出修正并重测，说明差异；保留原文，禁止迁就错误实现降低验收标准。

按流程对齐需求→实际实现→用例→证据，覆盖必要边界、异常、集成和修复回归。同一检查可关联多个验收项，事实只记一处。环境或权限不足记录未执行项，不将其冒记实现缺陷。技术方案调整本身不自动判失败，核对实际业务与接口约束。

执行结束再次核对当前任务和基线；代码变化则暂停并返回 blocked，已得结果只保留为原基线历史，不能认证新代码。

按 [公共结果模板](../../templates/role-result.yaml) 写 result.yaml，填实际验收结果、development_run_id、基线、缺陷和限制；artifacts 每项含 kind/path，相对本 run 输出。passed/failed/blocked 按流程门槛判断，报告与结果一致。

只写任务授权的测试输出/临时位置，业务源码修复交开发，需求歧义由协调层交产品。向协调 Agent 返回结果路径、状态及简要结论，根状态与索引由协调层维护。
