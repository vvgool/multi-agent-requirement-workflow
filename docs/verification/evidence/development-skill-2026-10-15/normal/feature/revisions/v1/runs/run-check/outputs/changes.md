# Shipping fee fixture：开发改动清单

- feature_id：EVAL-normal
- requirements_revision：1
- run_id：run-check
- 代码基线：sha256:4706d146074061ecfbfb5a11fb594f6a1d3ebc4be0c018fe17c45dc13fb3169d

## 实际改动

| 项目相对路径 | 改动行为/接口 | 模块/小任务编号 | 需求/验收编号 |
| --- | --- | --- | --- |
| shipping.py | 用负数 ValueError 及 10000 阈值运费实现替换 NotImplementedError | M1/M1-T1 | AC-1、AC-2 |

checkout.py 未改动，纳入真实整合检查及代码基线（M1-T2、AC-3）。

## 方案调整与修复

业务方案无调整。验证脚本初次根路径计算错误导致 ModuleNotFoundError，修正验证脚本并重跑全部检查通过；详见 verification.md 和 verification.log。

## 未解决项及交接限制

已核对 AC-1～AC-3 均通过，无影响交付的未解决项。仅离线合成夹具评估；没有生产发布、联网或提交推送。
