# Codex 薄适配

通用流程见 [安装与恢复](installation.md)，项目版本绑定见 [包规则](../../../workflow/package.md)。旧快照独立按 [旧安装流程](codex-installation.md) 处理，不共享新回执格式。

## 文件与检查

三个项目角色为 `.codex/agents/requirement_product.toml`、requirement_development.toml、requirement_testing.toml；分别绑定共享 product-agent/requirement-analysis、development-agent/feature-development、testing-agent/acceptance-testing。读取 [原生模板](../assets/templates/native-codex.toml) 和 [角色正文](../assets/templates/role-body.md)，填 name/description/developer_instructions，不指定 model、MCP或权限。

主会话通过 AGENTS.md 的 [薄入口](../assets/templates/project-entry-light.md) 协调；不创建第四角色，不创建三个 Skill 发现链接。阶段角色明确读取锁定包内完整 Skill 及其模板，不把全局同名 Skill 视为本项目依赖。

预检现有 .codex/config.toml、项目/可见用户同名角色与父级适用设置、AGENTS.override.md；解析现有TOML，检查所有名称声明而非只比文件名。`agents.enabled=false` 或已知旧版本禁用子Agent的设置均需尊重；不知道配置语义时先核实当前版本，不修改配置绕过。入口被覆盖、同名来自插件/全局且无法确定实际选择时报告冲突。只读可见设置，不遍历用户凭据。

## 生效与调用

在实际支持原生角色的Codex新会话或已证实重载后，通过工具真实角色选择机制调用上述三个名称并传 initialization_probe=true。没有名称选择参数不以通用spawn替代。记录实际宿主任务ID与结果，单独标明入口探测；终端不存在codex命令不能单独证明桌面/IDE宿主不支持。

业务派发、等待和查询按实际工具接口执行；名称、host任务标识与通用逻辑角色分别保存。未知调用先恢复，不重复派发。继承实际父会话权限，文案不等于独立只读沙箱。

依据：[官方自定义角色](https://learn.chatgpt.com/docs/agent-configuration/subagents)（2026-10-15核对）。格式文件验证与真实当前宿主调用分别报告；不宣称已验证所有Codex版本。
