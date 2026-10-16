# 偶数判断：测试报告

需求/修订/run：4d2c6225-3335-4b70-a88a-c858d8699eb8 / v1 / run-testing-layout-001；待测开发run：run-development-layout-001。基线与结果见本 run 的 result.yaml 及[基线证据](code-baseline.json)。

依据与范围：[批准夹具文稿](../../../../documents/requirements.md)、项目 AGENTS.md、正式与候选开发记录、开发结果索引及实际 parity.py / tests/test_parity.py。采用真实测试报告模板；本次只有一个纯函数，直接在本报告合并用例。环境 Python 3.9.6，标准库 unittest 与独立验收脚本，全部 Python 命令使用 -B。本次显式合成审批仅用于角色工作流及输出布局验证，不代表真实用户审批或原生注册。

## 用例与结果

共用前提：feature_id、revision、testing active_run、manifest 原始摘要、需求/有效配置摘要、开发 run 及实际文件 SHA256 均匹配；执行前后核验一致。用例预期独立取自 AC-001 至 AC-003，未修改既有源码或用例。原始命令、输出与链接复现均见[执行证据](verification.log)，可复现脚本为[独立验收脚本](acceptance-check.py)。

| 用例/验收编号 | 操作与预期 | 实际结果/证据 |
| --- | --- | --- |
| TC-001 / AC-001 | 调用 is_even(0/2/-2/1/-1)；预期 True/True/True/False/False，严格 bool | passed；额外验证 10**300 及 -(10**300+1)，全部符合；见执行证据 |
| TC-002 / AC-002 | True、False、1.0、"2"、None 均应抛 TypeError 且无转换 | passed；额外验证 list、dict、complex 拒绝行为；见执行证据 |
| TC-003 / AC-003 | 读取实际模块 AST，核对标准库/无新增 CLI、网络和依赖约束 | passed；parity.py 无 imports，仅纯函数；实际测试通过，无安装依赖；见执行证据 |
| TC-004 / 回归 | 运行原项目 unittest，核对既有预期与需求一致 | passed；2 项测试退出码 0；原用例无需修正 |
| TC-005 / 交接与布局 | 正式开发文稿引用应可读取，执行前后基线一致 | blocked；源码基线一致，但正式文稿有 3 个唯一坏链接；见基线证据 broken_document_links 与执行证据 |

## 偏离核对与结论

需求行为、实际接口与实现、现有用例和开发自验声明一致；独立执行证据对应相同源码/测试 SHA256，aggregate_sha256 为 5e7f67c361e7ef1c9b5701d727710851fd2f639f45b461e7aa07579e83bf7578。没有发现实现缺陷、错误旧用例或未批准功能。源码由调用方实际导入执行，不以开发自验代替独立执行。

缺陷或阻塞：B-001（成果交接偏离，非业务实现缺陷）。正式 documents/development.md 中需求、自验日志、代码基线的链接包含跨根路径 ../../…/private/var/...；从当前 macOS /var -> /private/var 别名路径解析后成为 /private/private/var/...，3 个唯一目标均不存在。复现：读取该文稿 Markdown 链接，以文稿父目录拼接并调用 Path.exists()，得到 False；实际解析路径已记录在基线证据。任务明确列出的原始资料本身可读取，故功能验收均已执行。解除条件：协调层修正正式成果链接并重新核对索引摘要，按有效任务重验交接。测试角色未修改正式文稿、审批、根状态或源码。

结论与下一步：blocked。AC-001 至 AC-003 全部 passed，无功能未执行项；成果链接交接偏离尚未解决，不能将本次框架完整布局验证标为 passed。结束时任务、身份、审批、实际源码及全部受保护输入摘要与执行前一致。交协调层处理 B-001 后复核，必要时派发新 run。本结论范围为本地 Python 夹具工作流，不证明真实用户审批或宿主原生注册。
