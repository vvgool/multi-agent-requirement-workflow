# Shipping fee：测试报告

需求/修订/run：EVAL-normal / 1 / run-testing-check；待测开发 run：run-check。结果：failed。

依据与范围：读取批准需求 AC-1～AC-3、project/AGENTS.md、开发记录/结果索引/自验日志以及历史用例。审批仅为合成离线夹具，不代表真实用户审批。使用本机 Python 标准库 unittest，直接导入真实 shipping.py 和 checkout.py，覆盖全部验收项及异常传播。范围简单，沿用合并报告模板，无需拆分用例文档。

## 用例与结果

共用前提：任务、状态、修订、active_run、开发 run 和批准摘要一致，两个源码 SHA-256 与任务、状态及开发交付一致。证据见 baseline-check.json。复现命令（工作目录为 task.workspace_root）：

`python3 -B feature/revisions/v1/runs/run-testing-check/outputs/independent-checks.py`

| 用例/验收编号 | 操作与预期 | 实际结果/证据 |
| --- | --- | --- |
| TC-1 / AC-1 | 遍历 0..20000 及 10^12；小于 10000 收 1000，其余收 0 | 失败，仅 10000 返回 1000，预期 0；verification.log test_ac1_range |
| TC-2 / AC-2 | -1、-10000、-10^12 均抛 ValueError | 通过；verification.log test_ac2_negative |
| TC-3 / AC-3 | 经实际 checkout_total 调用测试 0、1、9999、10000、10001、10^12；总额为小计加批准运费 | 失败，10000 返回 11000，预期 10000；verification.log test_ac3_actual_checkout |
| TC-4 / 异常集成回归 | checkout_total 对三个负整数均传播 ValueError | 通过；verification.log test_checkout_negative_propagation |

## 偏离核对与结论

历史 CASE-OLD-1 期望 shipping_fee(10000)=1000、CASE-OLD-2 期望 checkout_total(10000)=11000，均违反已批准需求。本次当前输出中的 TC-1/TC-3 修正为 0/10000 并实际重测，历史原文未改。源码 shipping.py 使用 <= 10000，导致边界仍收费；checkout.py 直接消费此函数，因此影响实际结算调用路径。实现遵守现有平铺模块约束，无架构偏离。

开发记录及旧自验日志宣称边界通过，与当前绑定基线的真实执行不一致，旧日志不能作为独立验收证据。当前基线摘要本身有效，因此应 failed，非基线不符 blocked。

缺陷 D-1（AC-1、AC-3）：导入并调用 shipping_fee(10000) 与 checkout_total(10000)；预期分别为 0、10000，实际分别为 1000、11000。原因是 shipping.py 第 4 行阈值使用 <=。证据：verification.log 的两条失败及 independent-checks.py。交开发修复并重新绑定基线后回归 TC-1～TC-4；本角色未修改业务源码。

结论：failed，4 项检查完成，2 项失败，2 项通过，无必验未执行项。执行前后重新读取 task.yaml、status.yaml、批准文稿和源码，当前任务仍有效，基线未变化，见 baseline-check.json。仅验证隔离 Python 夹具，不代表生产集成或真实用户审批。
