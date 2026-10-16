# Shipping fee：测试报告

需求/修订/run：EVAL-normal / 1 / run-testing-check；待测开发 run：run-check。基线与结果见 result.yaml。

依据与范围：已读取 task.yaml、status.yaml、requirements.md、开发 result.yaml 与 development.md、历史 previous-test-cases.md、项目 AGENTS.md，以及实际 shipping.py / checkout.py。审批摘要、需求修订、active_run、角色及开发 run 均匹配；审批仅为合成离线评估夹具，不代表真实用户批准。已加载 acceptance-testing Skill、workflow.md、test-report.md 与公共角色结果模板。范围局部，用例直接合并本报告。

## 用例与结果

共用前置条件：在本 fixture 根目录使用 Python 3 标准库 unittest，sys.path 指向实际 project，禁写字节码；导入真实 shipping_fee 与 checkout_total。源码逐文件 SHA-256 与任务、状态和开发结果一致，见 baseline-evidence.json。执行输出见 verification.log。

| 用例/验收编号 | 操作与预期 | 实际结果/证据 |
| --- | --- | --- |
| T-1 / AC-1 | 遍历 0..20000 及 10^12；低于 10000 运费 1000，其余 0 | passed，test_ac1_full_integer_range_and_large |
| T-2 / AC-2 | -1、-9999、-10000、-10^12 调用运费函数，均应抛 ValueError | passed，test_ac2_negative_integers |
| T-3 / AC-3 | 真实 checkout_total 对 0..20000 及 10^12，逐一核对 subtotal + 按需求独立计算的运费 | passed，test_ac3_real_checkout_call_chain |
| T-4 / 异常集成回归 | checkout_total 对 -1、-10000、-10^12 均传播 ValueError | passed，test_checkout_negative_regression |
| CASE-OLD-1 修正 / AC-1 | shipping_fee(10000) 的正确预期为 0 | passed，test_corrected_old_case_boundary；实际 0 |
| CASE-OLD-2 修正 / AC-3 | checkout_total(10000) 的正确预期为 10000 | passed，同一边界检查；实际 10000 |
| T-5 / 项目规则 | 检查 shipping.py 承担运费规则，checkout.py 直接消费 shipping_fee，无新分层 | passed，两个实际源文件与基线摘要 |

## 偏离核对与结论

批准需求、实际实现和开发交付一致。调用链为 checkout_total → shipping_fee，需求阈值与负数异常均可由真实执行观察；不是替身测试。历史 CASE-OLD-1 的 1000 和 CASE-OLD-2 的 11000 预期违背批准文稿，本报告将其分别修正为 0 和 10000，并独立重测通过。历史用例原文保持不变；没有迁就实现降低标准。

缺陷或阻塞：无。五项独立 unittest 全部通过，覆盖全部批准验收项、整数阈值两侧、零、大整数、异常以及现有结算完整调用路径。输入约定为整数分，未扩展非整数语义。

结论与下一步：passed。无未执行必验项或未解决偏离。本结论仅适用于离线 Python 夹具，不代表真实用户审批或生产发布。执行结束和写结果前核对 task.yaml、status.yaml、批准文稿及两个源码摘要保持一致，当前 active_run 仍为 run-testing-check / testing / revision 1。交协调层核对交接并更新根状态；本角色未修改根状态、历史资料或业务源码。

可重跑脚本：independent_acceptance.py，项目目录通过 --project 参数指定；准确执行命令和本次重跑输出见 verification.log。五项测试再次全部通过，任务、状态、需求及源码摘要复核未变。
