# 验证索引

本目录是框架开发证据，不随核心包默认安装。先看本页判断能力边界；各报告描述其执行当时的版本，旧模板、目录、数量及“尚未实现”不能直接当作当前事实。原始审批、快照、任务及日志不为套用新规则重写。

## 当前门槛

| 能力 | 已有证据 | 尚待验证 |
| --- | --- | --- |
| 产品、开发、测试 Skill | 独立角色隔离执行，真实模板和结果产物 | 初始化后原生角色完整流程 |
| 需求正常闭环 | 真实用户确认后的手动加载原型正常流程 | 原生注册闭环、完整测试失败修复循环 |
| 项目级初始化 | 三宿主薄入口、同摘要缓存、重复/冲突保护；Codex 克隆恢复、Codex/OpenCode 中断恢复 | 三宿主新会话原生发现/调用；多宿主追加、显式升级 |
| 成果布局 2 | 三文档案例、待评审案例、固化/路径/保护检查 | 原生注册后的完整新版闭环 |
| Issue | 静态检查及 15 个独立协议模拟 | 真实平台权限、读写、直接 ID 恢复及全部故障路径 |
| 飞书 | 来源/授权契约 | 真实飞书读写 |

规则存在、模拟成功、文件安装、原生激活、完整需求验收和生产可用是不同结论，不互相替代。

## 按目的查证

| 目的 | 记录 |
| --- | --- |
| 看新格式及人工确认入口 | [案例](examples/README.md)、[目录收敛](output-layout.md) |
| 看产品澄清和需求输出 | [产品 Skill](requirement-analysis-skill.md) |
| 看开发及精简文档 | [精简开发](adaptive-development-skill.md)、[初版开发历史](feature-development-skill.md) |
| 看测试偏离和基线核对 | [测试 Skill](acceptance-testing-skill.md) |
| 看正常需求闭环 | [协调原型正常流程](coordinated-lifecycle.md) |
| 看三宿主轻量安装与共享 | [通用初始化](portable-initialization.md) |
| 看旧 Codex 快照安装及恢复 | [初始化](codex-project-initialization.md)、[后续修复](audit-fixes.md) |
| 看 Issue 绑定与留痕 | [Issue 验证](issue-tracking.md) |
| 查早期路由/规则设计 | [首个里程碑](coordinator-first-milestone.md)、[协调规则走查](coordinator-routing.md)、[开发测试走查](development-testing-workflows.md)、[早期可移植性](portability.md) |

后续的自适应澄清、规划覆盖和按风险测试优化已写入当前 Skill；不是上述所有旧夹具逐一复测的声明。Issue 报告中的静态统计也只代表其执行时点。

## 本轮文档整理与清理（2026-10-15）

README 和两份规划统一到当前角色/Skill、布局 2、可选 Issue 和实际验证边界；旧 specs/plans 标为历史，不再用作待执行计划。保留旧兼容入口，因为历史索引仍引用它们。

清理前逐文件核对 Codex 初始化夹具：`clean-project` 与 `搬迁 Project With Spaces` 的 54 个普通文件及 3 个符号链接完全相同。保留一份 [原安装项目](evidence/codex-initialization-2026-10-15/clean-project/) 和原始检查记录；删除搬迁副本中 53 个重复文件、3 个重复链接及随后的空目录，保留原路径的 [搬迁安装清单](<evidence/codex-initialization-2026-10-15/搬迁 Project With Spaces/.agents/requirement-workflow/installation.json>)。

搬迁清单是历史证据，不再代表一个完整可执行安装目录；其中 owned_files 可与原安装项目核对。旧检查记录中的两套完整安装通过是当时事实，不是清理后的双份快照检查。未删除审批、需求案例、原始日志或独立测试证据。未发现额外缓存/备份文件，不按扩展名盲删日志。

整理后检查：5 个 Skill 校验通过；全仓 395 个本地 Markdown 链接可达，无断开的符号链接；157 个 YAML、51 个 JSON、7 个 JSONL、12 个 TOML 可解析，YAML 无重复键。除明确删除的重复项外，403 个历史证据/案例文件摘要不变；两份安装清单均能与保留的原安装快照逐项核对。该检查不包含新的原生或远程调用。
