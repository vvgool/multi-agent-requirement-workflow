# 协调闭环验证：正常流程已跑通

> 本报告记录执行当时的版本与验证范围；当前能力及后续记录见 [验证索引](README.md)。不将旧统计或未验证项改写为本轮通过。

“整数分金额格式化”v1 在独立示例项目中完成产品→真实用户确认→开发→独立测试→completed。三个角色均由协调主会话依据落盘状态实际派发，使用各自 Skill 及真实模板；没有把阶段内容工作交回协调层。当前结论仅为手动加载角色的宿主原型正常流程通过。

| 阶段 | 真实调用/确认 | 实际结果 |
| --- | --- | --- |
| 产品 | /root/lifecycle_product | ready；一份含六项验收及自检的文稿 |
| 用户评审 | 用户对当前展示的 v1 回复“继续” | 复核稿件、来源、配置及 review-manifest 摘要未变，记录审批原文及实际时间；真实会话 ID 不可取得，保持 null |
| 开发 | /root/lifecycle_development | ready；一份精简开发记录，方案→单模块/小任务→普通执行→完整自验；八项测试通过 |
| 测试 | /root/lifecycle_testing | passed；六项验收、额外 1,037 例边界/异常及开发八项测试通过；报告核对需求、实现、用例及当前基线无偏离 |
| 协调交付 | 根状态版本 14 | completed/idle；活动任务清空，首次开发计数为 1；保留审批、产物及事件，不发布 |

开发遵循示例项目规则；无既有架构时使用最小 Clean 职责划分：纯业务函数和调用测试，无第三方依赖、UI、CLI 或服务。为支持超大整数，使用整数十进制分块，未修改解释器全局限制。测试没有修改业务源码或开发用例。

协调层逐次核对身份、任务实际结束、产物路径和必需交接字段。接收开发与测试时核对全部相关源码/测试 SHA256；最终复核批准文稿及来源摘要，重新执行独立验收脚本和八项开发测试，均退出 0。运行中重新读取状态时选择等待已有测试任务，未重复派发；这不等同跨会话崩溃恢复验证。

## 证据

- [v1 评审稿](evidence/coordinated-lifecycle-2026-10-15/project/agent-features/整数分金额格式化/revisions/v1/review/requirements.md)
- [当前状态与真实审批](evidence/coordinated-lifecycle-2026-10-15/project/agent-features/整数分金额格式化/status.yaml)
- [事件](evidence/coordinated-lifecycle-2026-10-15/project/agent-features/整数分金额格式化/events.jsonl)
- [开发记录](evidence/coordinated-lifecycle-2026-10-15/project/agent-features/整数分金额格式化/revisions/v1/runs/run-development-001/outputs/development.md)
- [测试报告](evidence/coordinated-lifecycle-2026-10-15/project/agent-features/整数分金额格式化/revisions/v1/runs/run-testing-001/outputs/test-report.md)
- [闭环检查](evidence/coordinated-lifecycle-2026-10-15/checks.json)、[父会话最终复核](evidence/coordinated-lifecycle-2026-10-15/parent-final-verification.json)

## 未验证门槛

当前工具不支持选择 Codex 原生自定义角色，本机未发现 codex 可执行程序；三个实际任务均为手动加载框架角色的普通宿主子 Agent 调用，不能证明 .codex/agents 注册或新会话生效。原生注册后的完整闭环、测试失败自动反馈开发并再次回归、真实中断恢复、其他宿主适配及真实飞书读写仍待验证。

本例本次没有失败，不注入伪缺陷来冒充自然失败修复。历史隔离测试对故意偏离实现的失败判定仍是独立证据，不替代协调失败回退闭环。示例项目位于证据目录，不是默认分享核心；主框架维护需求未冒记 completed，无生产发布。
