# Multi-Agent Requirement Workflow

面向 Codex、Claude Code、OpenCode 的宿主内多 Agent 需求协作框架。当前已提供协调、产品、开发、测试角色规则及模板；真实调用验证状态见下方记录。

用户直接在 Codex、Claude Code 或 OpenCode 会话中使用协调 Agent，由宿主原生子 Agent 能力调用产品、开发和测试角色；框架不提供额外 CLI。需求与验收标准须由用户明确确认后才能进入开发；不自动执行生产发布。首个里程碑是自动调用产品 Agent 并等待人工需求确认。

## 工作空间布局

需求资料默认跟随目标工作空间保存，框架本身可安装在其他位置：

```text
目标工作空间/
  workflow.yaml
  agent-features/
    用户签到奖励/
      status.yaml
      revisions/
        v1/
        v2/
```

工作空间根目录在启动协调 Agent 时指定。[workflow.yaml](workflow.yaml) 中的 workspace.features_dir 默认 agent-features，相对于目标工作空间根目录解析。用户使用需求名称，内部自动生成 feature_id；同名优化按修订版管理，保留历史审批与验证证据。

本目录的既有需求已从 requests 迁移到 agent-features，内部标识值保持不变。配置由协调 Agent 使用宿主文件工具读取和检查，不引入额外 CLI 或运行时依赖。单需求覆盖文件为 revisions/vN/documents.yaml，字段见 [配置规则](workflow/config.md)。

## 直接在会话中使用

Codex 首次使用时，让宿主读取 [初始化 Skill](skills/setup-requirement-workflow/SKILL.md)，例如提供本框架目录后说：

> 按 skills/setup-requirement-workflow/SKILL.md，为我指定的目标项目初始化 Codex 需求协作框架，保留已有项目规则和配置，完成文件安装后核对新会话中的原生角色与 Skill。

初始化在项目内保存框架副本，生成三个原生角色及 Skill 入口，并把协调入口接入项目 AGENTS.md。当前已提供安装流程和模板；文件安装通过与真实宿主生效分别记录。尚未实现自动升级/卸载。未初始化时，仍可进行手动加载原型，例如：

> 加载本框架的 agents/coordinator-agent.md，作为协调 Agent，在当前宿主工作空间中处理“用户签到奖励”：首次签到奖励 10 积分，每个账号每天一次，按北京时间零点刷新，断网时提示重试、不发放。目标项目就是该工作空间。

继续已有需求：

> 按协调 Agent 流程，继续当前宿主工作空间中的“用户签到奖励”，先读取状态并核对活动任务。

通用 agents/ 中的 Markdown 本身不会自动注册。Codex 安装使用项目 .codex/agents/ 原生 TOML；真实生效后，各阶段由协调主会话按状态派发，用户无需手动切换角色。具体入口：[Codex](workflow/hosts/codex.md)、[Claude Code](workflow/hosts/claude-code.md)、[OpenCode](workflow/hosts/opencode.md)。

首次加载时把框架目录提供给宿主作为可读上下文；框架可以放在任意位置，协调 Agent 从实际加载文件定位框架。框架位置或目标工作空间无法确定时才询问用户，不要求修改文档中的作者路径。

## 共享给其他用户

共享 AGENTS.md、README.md、agents/、skills/、workflow/、templates/ 和不含凭据的 workflow.yaml 示例。接收者使用自己的工作空间配置及 agent-features，开发演示证据和已有需求不作为默认安装内容。目录定位、运行时路径与搬迁恢复规则见 [共享与路径定位](workflow/portability.md)。

框架规则使用宿主原生工具执行，不提供跨会话并发锁或事务保证；同一需求仅由一个协调会话推进。协调角色按 [全阶段路由](workflow/routing.md) 管理产品、人工评审、开发、测试、失败回退及完成。协调层负责状态路由、交接完整性和用户确认；产品负责需求质量，开发负责实现与开发验证，测试负责逐项验收及缺陷判断。缺少角色或宿主能力时保持阶段并阻塞。

## 当前设计

开发角色已接入 [feature-development Skill](skills/feature-development/SKILL.md)，按复杂度使用真实模板：小需求一份开发记录，复杂需求拆方案/计划/自验，恢复信息按需就地维护。开发遵循项目规则，缺少架构约定时按 Clean Architecture 原则做最小设计。测试角色已接入 [acceptance-testing Skill](skills/acceptance-testing/SKILL.md)，默认一份测试报告，复杂用例按需独立；核对批准需求、实际基线、用例和证据的偏离。产品角色已接入 [requirement-analysis Skill](skills/requirement-analysis/SKILL.md)，默认一份需求文稿合并差异和自检，关键规则未知时返回问题，来源不全时阻塞。Codex 项目初始化、原生角色模板及 Skill 绑定流程已提供，真实新会话生效仍待验证。

完整开发目录中的 docs/planning/overall-goals.md 和 docs/planning/agent-responsibilities-and-workflows.md 记录后续建设顺序：先明确职责和交接，再搭建角色 Skill，随后做宿主初始化适配。这些设计资料不作为共享核心包的运行依赖。

完整开发目录中的设计资料位于 docs/superpowers/specs/，不作为核心分享包的运行依赖；当前可执行规则以 agents/ 和 workflow/ 为准。

## 验证边界

- 完整开发目录的 docs/verification/coordinator-first-milestone.md 区分规则检查、真实 Codex 子 Agent、人工确认和外部集成。该记录属于作者环境，核心分享包不包含运行历史。
- 飞书文档来源与写入规则已定义，真实读写尚未验证；缺少能力或权限时明确阻塞。
- Claude Code 和 OpenCode 目前只有接入边界说明，专用适配及真实调用尚未验证。
- 开发、测试和失败回退的协调规则已定义，开发/测试角色规则已补齐，全流程真实调用未验证；不自动执行生产发布。
