# Shipping fee fixture：技术方案

- feature_id：EVAL-resume
- requirements_revision：1
- run_id：run-check
- 批准文稿与摘要：feature/requirements.md；SHA256 1f427e6d1b0791c6e34a6d051ebb050319fee2ee696927f2784954419fc87512（合成评估夹具，不代表真人审批）
- 目标项目：/var/folders/p7/6lh96zx51qz0ksknm0qj5v3r0000gp/T/development-skill-check-hku9qg2v/resume/project

## 目标与现状

恢复已有 M01/M02 局部完成记录；shipping.py 处理运费及负数，checkout.py 实际导入 shipping_fee 并加总。历史整体验证因离线失败。源码和检查脚本只读。

## 需求与实现对应

| 验收 | 实现 | 风险 | 检查 |
| --- | --- | --- | --- |
| AC-1 | shipping.shipping_fee，10000 为免运费边界 | 边界回归 | 0、1、9999、10000、10001、100000 |
| AC-2 | shipping_fee 负数抛 ValueError | 异常传播 | -1、-10000 |
| AC-3 | checkout.checkout_total 实际消费 shipping_fee | 局部结果不代表外部环境可用 | 总额边界及负数，另运行 integration_check.py |

## 接口、数据流及影响

整数分输入 → checkout_total → shipping_fee → 加总；负数抛出 ValueError。当前无需源码修改，恢复时比对内容摘要并重验。

## 技术选择与待决策问题

保留既有实现及检查，无法在只读授权内修复离线集成环境；无业务规则待决策。

## 验证与交付范围

先验证 M01，再验证 M02 的真实导入、全用户函数流程与异常；最后原样执行必需 integration_check.py。每次保留命令、退出码、输出及源码摘要。必需集成失败时 blocked。
