---
name: acceptance-testing
description: Use when testing-agent receives an approved feature baseline for acceptance or defect regression, including requirement drift, incorrect existing cases, and baseline mismatch checks.
---

# 需求验收与回归

独立核对已批准需求、实际开发基线和用例，执行验收并返回真实结论。项目适用规则和测试约定优先；开发自验只作输入，不能代替独立证据。

接单及交付前遵循 [阶段执行契约](../../workflow/execution-contract.md)，统一核对身份、授权、结果位置和过期任务。正式文稿及根状态由协调层维护。

执行前按其 [缓存与证据](../../workflow/execution-contract.md#缓存与证据) 核对实际缓存写入范围、单份检查记录及跨轮复用条件；报告合并记录命令/范围、结果、基线及环境，同一检查跨AC引用一次。独立必验项实际执行，开发日志只作输入；原证据不能核实则补验或blocked，不复制历史现场。现场清理由协调在确认调用结束后处理。

## 接单与基线

完成执行契约核对后，按开发交付索引读取记录和已有用例。开发简版一份记录或完整版多文档都可接受，按实际内容读取，不要求固定文件名。

按 [代码基线契约](../../workflow/code-baseline.md) 比较实际源码与任务/开发交付基线，独立核对范围及相关未提交改动。基线不符或必需资料无法核实时返回 blocked，记录差异，等待协调层重新绑定；不能把旧证据用于当前代码。旧任务返回 stale_task，由协调层记录，避免写入新版任务。

## 文档选择

先读 [测试流程与判定](references/workflow.md)，再读所需真实模板，在 task.output_dir 生成实例：

| 条件 | 模板与输出 |
| --- | --- |
| 默认 | [测试报告](assets/templates/test-report.md) → test-report.md，合并用例、偏离核对、缺陷及结论 |
| 用例矩阵、环境或步骤复杂到影响报告阅读 | 额外使用 [用例](assets/templates/test-cases.md) → test-cases.md；报告引用用例编号及执行证据，不重抄 |

仅拆分用例时用一句话说明理由；不因开发采用完整版就自动拆测试文档。源模板、旧用例及开发资料保持不变；填写实际内容并删除不适用的条件段，TC 用例编号与 AC 验收编号分别记录并关联，执行状态单列；复杂步骤及缺陷用条目展开，已有用例通过链接引用。无需创建单独偏离报告、空缺陷清单或无意义的环境表。

## 检查、执行与交接

用例预期来自批准需求。已有用例也要核对，发现错误时在当前测试输出修正并重测，说明差异；保留原文，禁止迁就错误实现降低验收标准。

按流程建立验收覆盖，优先执行核心/高风险路径及修复回归，再完成其他必验项；优先级不豁免剩余必验项。检查风险选择、独立证据和阻塞后的执行范围统一按流程处理，不单建覆盖矩阵文件。

执行结束再次核对当前任务和基线；代码变化则暂停并返回 blocked，已得结果只保留为原基线历史，不能认证新代码。

按 [公共结果模板](../../templates/role-result.yaml) 在指定结果位置写 result.yaml，填实际验收结果、development_run_id、基线、缺陷和限制；artifacts 每项含 kind/path，相对本 run 输出。passed/failed/blocked 按流程门槛判断，报告与结果一致。

只写任务授权的测试输出、单一 result_path 和临时位置，业务源码修复交开发，需求歧义由协调层组织澄清；需要改变批准正文时按新修订进入产品评审，不在 testing 阶段直接派发只接受 draft 的产品任务。向协调 Agent 返回结果路径、状态及简要结论，根状态与索引由协调层维护。
