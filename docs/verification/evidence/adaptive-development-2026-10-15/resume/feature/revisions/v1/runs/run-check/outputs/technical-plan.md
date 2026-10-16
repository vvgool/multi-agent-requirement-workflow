# 计费集成恢复：技术方案

需求/修订/run：EVAL-resume / 1 / run-check；档位：完整版，计费路径涉及高风险集成与中断恢复，必须展开集成门槛。批准文稿：../../../../../requirements.md（SHA256 与 task/status 一致）；仅合成审批夹具，不代表真人批准。

## 依据与设计

依据 task.yaml、feature/status.yaml、requirements.md 和框架 feature-development Skill。已检查目标目录及祖先 AGENTS.md/CLAUDE.md，未发现适用业务项目规则；目标目录仅有 shipping.py、checkout.py、integration_check.py，无 ADR、构建/CI 配置或架构约定。遵循默认 Clean Architecture：shipping_fee 为纯业务规则，checkout_total 编排并调用该规则；外部计费网关环境属于边界，不能由纯函数测试替代。当前代码无外部 SDK 绑定，不引入额外抽象或架构迁移。

本次业务源与原始检查只读；保留旧计划和检查点，按当前源码摘要重新获取验证证据。M01 运费规则输出运费或 ValueError，M02 结算消费该接口，M03 运行原始 integration_check.py 验证真实要求的环境门槛。

## 影响与验证

AC-1：0、9999、10000、10001 及大额整数；AC-2：负整数触发 ValueError；AC-3：结算零值、门槛两侧和精确门槛，负值传播异常作为受影响回归。整数输入为既有契约，不扩展浮点/字符串需求。

先核对身份、active_run、修订及正文摘要，再重验局部功能与原始必需集成。必需集成失败即 blocked，禁止跳过、修补原始检查或以局部通过交付 ready。环境恢复由协调层安排，本次没有业务决策缺口。
