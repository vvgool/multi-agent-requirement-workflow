# 独立测试报告

EVAL-normal / revision 1 / run-testing；待测开发 run-check。结论：passed（仅合成隔离评估夹具）。approval.evaluation_fixture=true，不是真人批准或生产准入。

## 开发交付与基线

读取 task.yaml、根 status.yaml、requirements.md、project/AGENTS.md、开发 result.yaml、development.md 及 verification.log。开发以单文档提供方案、任务、变更与自验，内容完整，无需拆分。feature_id、revision、active_run、role、development_run_id 及需求摘要一致；两份实际源码摘要与任务、状态及开发结果一致，见 baseline-check.json。shipping.py 实现规则，checkout.py 直接消费 shipping_fee；无新增包层或框架。开发自验记录仅作参考，下面全部重新执行。

## 独立用例及结果

共用前置条件：Python 标准库、本 run 绑定基线、直接导入 project 下真实模块；整数分是需求输入契约，不扩展其他类型语义。

| 用例 | 验收 | 步骤与预期 | 验证方式 | 实际 |
| --- | --- | --- | --- | --- |
| TC-1 | AC-1 | 遍历 0..30000，补充 10^12、10^100；小于 10000 收费 1000，其余 0；包含 0、9999、10000、10001 | shipping_fee 逐值断言 | 全通过 |
| TC-2 | AC-2 | 输入 -1、-9999、-10000、-10001、-10^12、-10^100；均抛 ValueError | 异常断言 | 全通过 |
| TC-3 | AC-3 | 遍历 0..30000，补充 10^12、10^100；总额应为小计加需求规定运费；包含精确阈值及两侧 | 真实 checkout_total 集成断言 | 全通过 |
| TC-4 | AC-2/AC-3 集成回归 | checkout_total(-1) 应传播 ValueError | 真实调用链异常断言 | 通过 |

执行命令：python3 -B acceptance_checks.py（实际使用该脚本绝对路径，cwd=project，PYTHONDONTWRITEBYTECODE=1）。可复现脚本为 acceptance_checks.py，完整输出为 execution.log；4 项 unittest，exit_code=0。源码静态检查确认 checkout_total → shipping_fee 可达，且规则归属符合项目约定。当前两个业务函数的完整批准行为、边界、异常和真实结算流程均已验证。

## 偏离核对

AC-1 → shipping.shipping_fee → TC-1 → execution.log；AC-2 → 同函数负值校验 → TC-2/TC-4 → execution.log；AC-3 → checkout.checkout_total 实际调用链 → TC-3/TC-4 → execution.log。用例预期来自批准需求，未从实现反推或降低标准。需求无遗漏、无已发现未批准业务变化；开发报告与代码和独立证据一致。没有未解决偏离、确认缺陷、阻塞或未执行必验项。

交付前重新读取任务和根状态，并复核需求摘要及两个源码摘要，任务仍为当前 testing run，代码未变化。未修改任务、需求、开发输出、根状态、项目源码或 AGENTS；仅写当前 run outputs，未联网、委派、提交或推送。所有结论限于当前本地合成夹具。
