---
name: setup-requirement-workflow
description: Initialize the requirement workflow in a target Codex project, binding project-scoped roles and skills while preserving existing project configuration.
---

# 初始化需求协作框架

用户要求在指定项目安装本框架时使用。通过宿主文件工具执行，不引入工作流 CLI、调度服务或全局安装。当前仅实现 Codex；其他宿主返回尚未适配。

1. 从本 Skill 文件向上定位框架根目录，确认目标工作空间及宿主。框架目录不是默认目标项目；用户未指定目标且当前宿主项目不明确时，先询问目标。单纯维护框架不自动安装到自身。
2. 读取目标项目适用规则，检查已有 AGENTS.md、workflow.yaml、.codex/config.toml、角色文件、.agents/skills 及本框架安装记录。文件和符号链接均按真实路径核对；必要路径位于目标项目外、同名内容冲突或设置明确禁用子 Agent 时停止安装并说明冲突。保留用户配置，不自动提升权限或更改模型。
3. 先读 [Codex 安装流程](references/codex-installation.md)、[原生角色模板](assets/templates/agent.toml) 和 [项目入口模板](assets/templates/project-entry.md)。在写入前完成全部目标冲突检查；按流程创建项目内框架副本、三个原生执行角色、Skill 发现入口和协调主会话入口。workflow.yaml 仅在不存在时复制默认配置。
4. 校验全部 TOML/YAML、相对链接、安装文件及入口。保存项目内安装记录，区分文件安装、真实角色发现/调用和完整业务闭环。重复初始化核对已记录内容；无变更保持现状，有用户改动或新版本差异时返回具体差异，不覆盖。
5. 按安装流程在新会话或已重载配置的宿主验证三个原生角色及 Skill。无法选择已注册角色或无法启动新宿主时，只能报告“文件已安装，宿主生效待验证”，说明缺少哪项能力；不能将通用子 Agent 读取文件当作原生注册成功。

只写目标项目中本框架拥有的位置及 AGENTS.md 的指定区块，不写用户主目录、历史需求或业务源码；不会自动发布、修改审批或创建业务需求。返回安装记录路径、实际完成的检查和未完成项。
