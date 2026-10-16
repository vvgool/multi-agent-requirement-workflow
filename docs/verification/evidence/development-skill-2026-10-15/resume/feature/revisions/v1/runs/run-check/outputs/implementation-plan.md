# Shipping fee fixture：模块与任务执行计划

- feature_id：EVAL-resume
- requirements_revision：1
- run_id：run-check
- 依据：feature/requirements.md；SHA256 1f427e6d1b0791c6e34a6d051ebb050319fee2ee696927f2784954419fc87512（合成评估夹具，不代表真人审批）；technical-plan.md；history/implementation-plan.before-resume.md

## 模块执行顺序

| 顺序 | 模块及目标 | 验收 | 依赖与接口 | 模式 | 理由 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | M01 运费 | AC-1/2 | 整数分 → 运费或 ValueError | 长任务 | 继承恢复检查点，需重新关联代码及历史证据 | 通过 | evidence/M01.json |
| 2 | M02 结算 | AC-3 | M01；checkout_total | 普通 | 单一调用链，可一次验证 | 通过 | evidence/M02.json |

## 模块 M01：运费

实现范围 shipping.py，只读；无模块依赖。

| 任务 | 目标/修改范围 | 前置 | 验收 | 检查及预期 | 完成条件 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01-T1 | 边界费用，不改源码 | 身份核对 | AC-1 | 0/1/9999→1000；10000/10001/100000→0 | 所有断言通过 | 通过 | evidence/M01.json |
| M01-T2 | 负数异常，不改源码 | M01-T1 | AC-2 | -1/-10000 抛 ValueError | 所有断言通过 | 通过 | evidence/M01.json |

模块完成条件：两项及组合模块检查通过。长任务检查点：checkpoints/M01.md。

## 模块 M02：结算

实现范围 checkout.py，只读；依赖 M01 当前验证通过。输入整数分，输出含运费总额。

| 任务 | 目标/修改范围 | 前置 | 验收 | 检查及预期 | 完成条件 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M02-T1 | 真实调用及边界/异常回归，不改源码 | M01 通过 | AC-3 | 0→1000、9999→10999、10000→10000、10001→10001；负数抛异常 | 所有断言通过 | 通过 | evidence/M02.json |

模块完成条件：完整结算函数流程通过；普通模式无需独立检查点。

## 跨模块整合与完整功能自验

| 检查 | 范围 | 前置 | 方法及预期 | 模块 | 状态/证据 |
| --- | --- | --- | --- | --- | --- |
| I01 | AC-1/2/3 真实函数调用 | M01、M02 局部通过 | 边界与异常整体断言通过 | M01/M02 | 通过，evidence/I01.json |
| I02 | 必需完整功能环境检查 | I01 | python3 integration_check.py，期望退出 0 | M01/M02 | 失败，exit 1；evidence/I02.json |

## 计划调整与恢复记录

| 时间 | 原计划/检查点 | 恢复依据 | 失效/重验 | 下一步 |
| --- | --- | --- | --- | --- |
| 2026-10-15T08:30:25.903612+00:00 | history/ 下完整原文 | 身份和摘要匹配，源码符合静态规则；无历史摘要或原始日志 | M01/M02/I01/I02 全部重验 | 顺序执行检查，集成不通过则保持 blocked |

Final recovery 2026-10-15T08:32:46.965764+00:00: M01/M02/I01 pass on current baseline; I02 fails offline. Historical source digest unavailable; all checks rerun. No source or root-state changes. Delivery blocked; restore environment and rerun I02.
