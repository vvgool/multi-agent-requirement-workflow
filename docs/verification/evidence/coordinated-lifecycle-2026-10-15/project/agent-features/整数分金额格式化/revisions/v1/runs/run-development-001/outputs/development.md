# 整数分金额格式化：开发记录

需求/修订/run：02dd476d-921a-41f3-b264-7ed65fa52ec5 / v1 / run-development-001；档位：简版，局部纯函数、标准库和验证路径明确。任务与基线见 result.yaml。

## 依据与方案

批准文稿：../../../review/requirements.md；项目规则：目标项目 AGENTS.md 和 workflow.yaml。已核对根状态的 feature_id、revision、active_run、role 和 approval，并对 review-manifest.yaml、requirements.md 的 SHA256 验真。审批摘要与 task 一致。

项目无历史源码、架构、CI 或测试约定；采用最小 Clean 职责划分，将业务规则集中在 amount.py 的纯函数 format_amount(cents)，不绑定 UI、网络、数据库或外部框架。先检查整数且排除 bool，再检查负数；divmod(cents, 100) 取得元与分，以两位数字输出余数，全程避免浮点；元部分分成最多 9 位的十进制块转换并拼接。用 unittest 覆盖行为并用独立解释器导入验证集成。分块转换兼容超过 Python 默认十进制转换安全上限的大整数，不改变解释器全局配置。

## 任务

单模块：金额纯函数与调用验证。普通执行，局部无外部依赖，无需长任务恢复。

1. [x] 编写 amount.py，覆盖类型、非负校验及整数格式化；检查 AC-001 至 AC-005。
2. [x] 编写 tests/test_amount.py，逐项断言批准输入和异常，并回归枚举 0..10000。
3. [x] 执行全量标准库测试、干净标准库解释器导入及源码约束核对，覆盖 AC-001 至 AC-006；保存真实证据。
4. [x] 再读状态核对有效性，生成源码/测试 SHA256 基线和 result.yaml。

## 自验与交付

变更：amount.py 提供纯函数；tests/test_amount.py 提供八个标准库测试方法。

| 验收项/适用检查 | 方法与预期 | 实际结果/证据 |
| --- | --- | --- |
| AC-001 | 0、1、105、10000 返回批准字符串 | 通过；verification.json 的 unit-tests / test_ac001_examples |
| AC-002 | 99、100、101、123456789 的边界输出 | 通过；同证据 test_ac002_boundaries |
| AC-003 | 两个批准大整数精确输出及整数运算核对 | 通过；test_ac003_precision 与 source-constraints |
| AC-004 | 三个负整数均抛 ValueError | 通过；test_ac004_negative_integers |
| AC-005 | 七个非整数（含 bool 和负浮点）均抛 TypeError | 通过；test_ac005_non_integer_inputs |
| AC-006 | 标准库解释器导入调用，核对文件和依赖 | 通过；stdlib-import、source-constraints；源码无导入、外部入口或依赖 |
| 回归与额外精度 | 0..10000、分块进位和 5001 位整数 | 通过；test_small_range_regression、test_chunk_boundaries_and_very_large_integer |
| 全量集成 | python3 -B -S -m unittest discover -s tests -v | 八项测试全部 OK，退出码 0；verification.json 保留精确命令和完整输出 |
| 交接有效性与基线 | 再读 status 并核对运行、审批，摘要覆盖源码和测试 | 有效；code-baseline.json，摘要与 result.yaml 一致；未产生 pycache |

限制及下一步：无影响本批准需求交付的未解决项；交接协调层安排独立测试。本次是手工加载角色的真实宿主原型执行，不证明原生角色注册通过，不包含生产发布。测试与 SHA256 仅覆盖本次交付的 amount.py、tests/test_amount.py，不将框架其他改动纳入业务基线。
