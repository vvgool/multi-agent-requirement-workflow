# Claude Code 薄适配

先执行 [通用安装步骤](installation.md)。本适配提供文件格式和派发契约，真实Claude Code会话激活及业务闭环需单独验证，不将Codex结果沿用。

## 文件与检查

四个项目角色位于 `.claude/agents/requirement-product.md`、requirement-development.md、requirement-testing.md、requirement-bug.md。使用 [原生模板](../assets/templates/native-claude-code.md) 及 [共用角色正文](../assets/templates/role-body.md)；frontmatter只填 name/description，正文按角色绑定锁定包内的角色文件和完整阶段Skill。默认不指定model/tools/permissionMode，不提升宿主权限，不要求另装阶段Skill或插件。

AGENTS.md使用共同 [薄入口](../assets/templates/project-entry-light.md)，CLAUDE.md保留原文并追加 [桥接区块](../assets/templates/claude-entry.md)。桥接仅指向AGENTS，不复制协调流程。已有桥接按拥有摘要核验，不重复追加。

预检当前版本实际加载的 .claude/settings.json、settings.local.json、适用CLAUDE规则及其导入文件、可见项目/用户/插件同名角色。解析JSON/JSONC以宿主实际支持语法为准；不能按普通JSON误判已被宿主支持的配置。检查Agent委派限制与实际加载优先级；同名遮蔽、规则冲突或明确禁用先停止，不更改权限、模型或插件设置。保留已有插件和Skill，不自动用户级注册。

## 生效与调用

按当前Claude Code可用的角色选择/委派接口调用 requirement-product、requirement-development、requirement-testing、requirement-bug，分别传 initialization_probe=true。使用新会话或宿主已证实的重载，记录实际任务/会话标识与只读结果；如果没有可取得ID则保留null并说明。列出或读取agents文件不等于真正调用，工具不暴露原生选择时保留pending。

协调在主会话运行，由当前原生角色独立加载Skill；不依赖子Agent再派子Agent。业务任务/结果及框架绑定共用原契约，超时/无法查询原调用时保持unknown，不能因新开会话就清空原任务。权限实际由Claude Code控制，薄模板不宣称权限隔离。

依据：[官方子Agent](https://code.claude.com/docs/en/sub-agents)、[官方插件](https://code.claude.com/docs/en/plugins)（2026-10-15核对）。插件是可选分发渠道，首版初始化不安装marketplace或全局插件；不承诺宿主间插件格式相同。
