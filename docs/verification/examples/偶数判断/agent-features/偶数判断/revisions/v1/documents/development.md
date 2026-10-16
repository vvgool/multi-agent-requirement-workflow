# 偶数判断：开发记录

需求/修订/run：4d2c6225-3335-4b70-a88a-c858d8699eb8 / v1 / run-development-layout-001；档位：简版，单个纯函数、局部低风险且验证路径简单。任务与基线见本 run 的 result.yaml。

## 依据与方案

依据[批准夹具文稿](requirements.md)及目标项目 AGENTS.md：仅 Python 标准库，不增加 CLI、网络或依赖，使用 -B。已核对任务身份、active_run、布局、manifest 原始字节摘要、需求及有效配置摘要；这是显式合成审批夹具，不代表真实用户审批。项目无现存业务代码和架构约定，采用最小 Clean 设计：parity.py 中纯业务函数 is_even，无外部耦合。先排除 bool 及非 int，再用余数判断，返回 bool。

## 任务

单模块“整数偶数判断”，采用普通执行：无外部依赖、无中断恢复需求。

1. 已完成：实现 parity.py 的 is_even，覆盖 AC-001、AC-002。
2. 已完成：用 unittest 验证正常、负数、零、超大整数及拒绝类型，覆盖完整接口集成和异常行为。
3. 已完成：核对标准库/无 CLI/网络约束，保存自验原始输出及源码/测试 SHA256 基线。

## 自验与交付

变更：新增 parity.py 与 tests/test_parity.py，严格校验整数输入并返回 bool；全部任务共用一次[自验原始输出](../.workflow/runs/run-development-layout-001/outputs/verification.log)，对应[源码与测试基线](../.workflow/runs/run-development-layout-001/outputs/code-baseline.json)。

| 验收项/适用检查 | 方法与预期 | 实际结果/证据 |
| --- | --- | --- |
| AC-001 | 正负整数、零返回准确 bool | 通过，见[自验原始输出](../.workflow/runs/run-development-layout-001/outputs/verification.log) |
| AC-002 | bool、float、str、None 均 TypeError，不转换 | 通过，见[自验原始输出](../.workflow/runs/run-development-layout-001/outputs/verification.log) |
| AC-003 | 静态检查与标准库 unittest | 通过，见[自验原始输出](../.workflow/runs/run-development-layout-001/outputs/verification.log) |

限制及下一步：无影响交付的遗留项。交协调 Agent 核对产物；本次只是合成夹具工作流验证，不代表真实用户审批或原生注册验证。
