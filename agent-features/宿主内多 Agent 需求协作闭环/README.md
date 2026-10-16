# 宿主内多 Agent 需求协作闭环

当前版本：v1；状态：draft / idle（框架自身的存量维护记录）。

角色与阶段 Skill、布局 2、项目初始化及可选 Issue 支持已提供；静态/隔离验证与真实宿主门槛分开记录。新业务需求及新修订采用布局 2；本维护记录和已批准历史文稿沿用旧索引。

## 当前成果

| 文档 | 用途/结论 | 来源 |
| --- | --- | --- |
| [通用初始化验证](../../docs/verification/portable-initialization.md) | 版本锁、三宿主薄入口与本地缓存；文件验证通过，原生待验 | 本轮独立隔离验证 |
| [整体规划](../../docs/planning/overall-goals.md) | 当前目标、实现边界及后续顺序 | 本轮文档整理 |
| [验证索引](../../docs/verification/README.md) | 已验证门槛、历史记录及重复文件清理范围 | 当前维护入口 |
| [Issue 规则](../../workflow/issue-tracking.md) | 默认关闭的绑定、授权评论与恢复 | 本轮已实现，远程联调待完成 |
| [成果目录与保留规则](../../workflow/output-layout.md) | 新布局的正式规范 | 本轮用户已确认的目录方案 |
| [新格式案例](../../docs/verification/examples/README.md) | 完整三文档和待评审两种示例 | 用户指定归档，保留真实验证边界 |
| [目录验证报告](../../docs/verification/output-layout.md) | 新布局、旧版兼容、引用与用户改动保护的实际检查 | 本轮隔离评估，非业务审批 |
| [已有正常闭环验证](../../docs/verification/coordinated-lifecycle.md) | 真实用户确认后的原型正常流程已通过 | 存量示例，保留原路径与审批 |

待你处理：无额外审批。框架下一步仍需验证原生角色注册及失败回退闭环；这里没有标记整个框架已完成或已发布。

历史与阶段原始记录由 [status.yaml](status.yaml) 和 [events.jsonl](events.jsonl) 索引，排查时再读。
