# 整数分金额格式化：测试报告

需求/修订/run：02dd476d-921a-41f3-b264-7ed65fa52ec5 / v1 / run-testing-001；待测开发 run：run-development-001。基线与结果见 result.yaml。

依据与范围：已读取批准 review/requirements.md、review-manifest.yaml、项目 AGENTS.md/workflow.yaml、当前 status.yaml 和开发 result.yaml/development.md/verification.json/code-baseline.json。已加载 acceptance-testing Skill、references/workflow.md、assets/templates/test-report.md 和公共角色结果模板。本需求局部纯函数，报告内合并用例，无需拆分。

环境：macOS Python 3.9.6，独立验收使用 python3 -B -I -S，通过显式项目路径导入真实 amount.py，不替身。业务环境仅标准库；编排阶段使用宿主已有 YAML 解析器核对协议文件，未给业务项目增加依赖。全部命令、stdout、stderr 和退出码保存在 verification.json；验收脚本 acceptance-check.py 可重复执行。

## 用例与结果

共用前置条件：任务身份、v1 审批摘要、批准文稿及来源/配置文件摘要、开发 run 和两个交付文件 SHA256 与任务及状态一致。批准记录 user_response 为“继续”。所有检查直接调用真实函数；预期由批准需求给定，额外精度预期采用十进制字符串切片，不依赖源码分块算法。

| 用例/验收编号 | 操作与预期 | 实际结果/证据 |
| --- | --- | --- |
| TC-001 / AC-001 | 0、1、105、10000 → 批准的四个固定两位小数字符串 | passed，4 例；verification.json independent-acceptance AC-001 |
| TC-002 / AC-002 | 99、100、101、123456789 → 批准的四个无符号/分隔符结果 | passed，4 例；同证据 AC-002 |
| TC-003 / AC-003 | 9007199254740993、10**100+1 → 精确批准字符串；检查整数运算 | passed，2 例；同证据 AC-003；源码 divmod/整数分块，无浮点 |
| TC-004 / AC-004 | -1、-100、-(10**100) 均抛 ValueError | passed，3 例；同证据 AC-004 |
| TC-005 / AC-005 | 七个批准非整数含两个 bool 和负浮点，均抛 TypeError | passed，7 例；同证据 AC-005 |
| TC-006 / AC-006 | -I -S 标准库环境导入并调用；核对源码与项目文件无新增第三方、网络、UI、服务或 CLI | passed；同证据 AC-006；AST 核查无导入/浮点/真除法；交付仅 amount.py 和 tests/test_amount.py |
| TC-R01 / AC-002、003 | 固定种子产生 1 至 1000 位整数各一例；9 个幂边界 ±1；5001 位整数与相邻值，预期由十进制字符串构建 | passed，1029 例；同证据 REG-001 |
| TC-R02 / AC-005 | bytes、列表、字典、集合、object、complex、NaN、Infinity 均抛 TypeError | passed，8 例；同证据 REG-002 |
| TC-R03 / AC-001～006 | 重跑开发标准库全套 8 个测试方法，包括 0..10000 枚举 | passed，8 项；verification.json development-tests-regression，退出码 0 |

## 偏离核对与结论

需求、实现、已有用例及开发报告一致：类型判断先于负数判断，bool 显式拒绝，负浮点不会误抛 ValueError；整数 divmod 和十进制块拼接保持精度，余数固定两位。源码及项目交付范围符合纯标准库函数约束。已逐项复核开发测试预期，没有错误旧用例需要修正；开发报告八项测试及大整数描述与本次独立执行相符，其旧证据未替代本次执行。

缺陷或阻塞：无。六项必验全部执行通过，无未执行验收项或未解决需求偏离。

结论与下一步：passed，交协调层核对交接后更新状态。本角色未更新根状态或审批，未修改源码与开发测试。结束复核 state_version=13、active_run=run-testing-001，任务、批准文件及项目内输出范围外 26 个文件摘要与接单快照完全相同，两个待测文件仍匹配绑定基线，未产生 __pycache__；见 baseline-before.json/baseline-after.json。

证据范围：本隔离 Python 项目的真实函数和标准库导入验收；属于手工加载角色的实际宿主原型，不证明原生角色注册验证成功，不涉及生产发布。
