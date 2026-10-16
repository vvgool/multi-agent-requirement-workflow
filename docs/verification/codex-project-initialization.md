# Codex 项目级初始化验证

> 本报告记录执行当时的版本与验证范围；当前能力及后续记录见 [验证索引](README.md)。不将旧统计或未验证项改写为本轮通过。

2026-10-15，已提供 [初始化 Skill](../../skills/setup-requirement-workflow/SKILL.md)、[Codex 安装流程](../../skills/setup-requirement-workflow/references/codex-installation.md) 和真实原生角色/项目入口模板。宿主按文档执行安装，不引入框架 CLI、后台服务或全局配置。

原生结构依据 OpenAI 官方 [自定义角色](https://learn.chatgpt.com/docs/agent-configuration/subagents) 及 [Skill 发现规则](https://learn.chatgpt.com/docs/build-skills)。三个执行角色使用 `.codex/agents/` 中的独立 TOML；协调角色通过项目 AGENTS.md 在主会话执行。模型、MCP 和权限沿用父会话，不将角色行为规则当作独立沙箱。

## 已实现内容

项目内 `.agents/requirement-workflow/` 保存统一规则快照；`.agents/skills/` 的三个相对目录链接指向专属 Skill，保留资源和相对引用；`.codex/agents/` 生成 requirement_product、requirement_development、requirement_testing。AGENTS.md 仅追加框架拥有的入口区块，已有 workflow.yaml 和 Codex 配置保持原字节。

installation.json 保存文件摘要、相对链接、入口摘要及验证状态。安装后分别记录文件检查、真实原生调用及完整闭环；重复初始化不重复注册，源变化或本地改动保留原安装并报告差异。当前不自动升级或卸载。

## 隔离验证

三个独立子 Agent 接收真实安装请求和隔离目标项目，未给出预期结论。其中一个负责普通项目安装及再次初始化；另两个检查已有角色和越界目录。后续从项目副本中的初始化 Skill 验证搬迁，不读取源框架。

| 场景 | 实际结果 |
| --- | --- |
| 已有项目规则、工作流配置、Codex 配置和其他角色 | 文件安装通过，保留原内容；48 个拥有文件、3 个相对 Skill 链接、1 个协调入口区块 |
| 重复初始化同一项目 | 文件摘要、修改时间和链接目标不变，无重复角色或入口 |
| 另一个文件已声明 requirement_testing | 在写入前阻塞，不因文件名不同而重复注册，不覆盖已有角色 |
| .agents 链接指向项目外 | 在写入前阻塞，外部目录未被写入 |
| 整项目搬至含中文和空格的路径 | 从副本可定位角色、Skill、模板和规则；重复初始化不重写，无原源路径依赖 |

本轮文档清理后，搬迁项目只保留原始安装清单，重复快照已逐字节核对后移除；完整原安装项目仍保留。清理范围见 [验证索引](README.md)，以下检查结果均为清理前实际验证。

证据在 [检查摘要](evidence/codex-initialization-2026-10-15/checks.json) 所在目录，包含实际安装快照和 installation.json；越界链接本身未归档，避免归档继续引用外部目录，其相对位置和结论另存 link-evidence.json。文件安装检查包括 TOML/YAML、所有核心本地 Markdown 链接、相对 Skill 目标、入口区块、清单摘要及原项目文件保护；源 Skill 未被评估角色改写。

## 尚未验证的门槛

当前会话有通用子 Agent 工具，但没有选择原生自定义角色的参数，也不能启动目标项目的新宿主会话；命令环境未找到 Codex 可执行文件。安装记录保留 `host_role_selection_unavailable`、`fresh_session_unavailable`，原生调用和主会话入口发现均为 pending，宿主任务 ID 为 null。这次评估 Agent 执行文件安装不等于调用了生成的原生角色。

因此只能认定“安装流程和生成文件已在隔离项目验证”，不能认定“Codex 新会话注册生效”。仍须在支持原生角色选择的 Codex 新会话执行三个 initialization_probe 并记录真实结果，之后才能验证用户确认、开发、独立测试和失败回归的完整需求闭环。

后续已验证缺省 workflow.yaml 创建、可信 pending 的部分落盘恢复及被修改残留的阻塞，见 [自检修复](audit-fixes.md)。源版本变化/完整安装后的本地拥有文件改动、配置显式禁用角色和 AGENTS.override.md 遮蔽等分支尚未逐项动态验证。其他宿主、真实飞书、自动升级/卸载及完整闭环未完成。
