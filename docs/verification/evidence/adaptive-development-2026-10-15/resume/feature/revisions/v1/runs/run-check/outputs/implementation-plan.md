# Existing plan
M01 (long): shipping AC-1/2, all local unit tasks completed.
M02 (normal): checkout AC-3, local task completed.
Required full integration: FAILED; integration_check.py reports offline environment.
Preserve this history, recheck actual code and continue from this state.


---
# 本次恢复执行补充（保留以上历史）

需求/修订/run：EVAL-resume / 1 / run-check；方案：technical-plan.md；事实结果见 verification.md。

## 模块顺序

| 顺序/模块 | 目标及验收编号 | 依赖/接口 | 普通或长任务及理由 | 进度/证据引用 |
| --- | --- | --- | --- | --- |
| M01 | 运费 AC-1/2 | 整数分输入，运费/异常输出 | 长任务，继承既有恢复模式 | 已重新验证通过；evidence.json local_verification（退出码 0），verification.md AC-1/2 |
| M02 | 结算 AC-3 | 依赖 M01 shipping_fee | 普通，单一调用链可一次验证 | 已重新验证通过；evidence.json local_verification（退出码 0），verification.md AC-3 |
| M03 | 必需完整集成 | 原始 integration_check.py 与环境 | 普通，单次门禁检查 | 已原样执行，失败并阻塞交付；evidence.json required_integration（退出码 1，环境离线） |

## 小任务

| 模块/任务 | 改动目标与范围 | 前置条件 | 检查与完成标准 | 进度/证据引用 |
| --- | --- | --- | --- | --- |
| M01/T01 | 只读核验现有业务规则 | 有效任务及基线 | 阈值及异常断言通过 | 已通过；evidence.json local_verification（退出码 0） |
| M02/T01 | 只读核验现有结算调用链 | M01 通过 | 阈值结算及负值传播通过 | 已通过；evidence.json local_verification（退出码 0） |
| M03/T01 | 原样执行集成脚本 | 只读原始脚本 | 原始进程退出码为 0 | 已执行失败；evidence.json required_integration（退出码 1，RuntimeError：环境离线） |

模块及整合门槛：AC-1/2/3 局部验证与必需环境验证均通过才可 ready；局部结果不能覆盖环境失败。

## 恢复或调整

当前位置：暂停于 M03 必需集成环境门槛；当前代码标识见 evidence.json baseline_after。模块、任务结论及证据以以上表格和 verification.md 为准。

需重验范围：环境恢复后重跑原始 integration_check.py；若代码标识变化，则重验受影响局部功能及其下游。

下一步：由协调层恢复必需集成执行条件后继续；不得绕过或修改原始门禁。旧 checkpoints/M01.md 保留，不另建恢复状态。
