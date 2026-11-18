# Claude Code 薄适配

通用流程见 [安装与恢复](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与检查

1. 四个项目级薄角色为 `.claude/agents/requirement-{product,development,testing,bug}.md`，由 [原生模板](../assets/templates/native-claude-code.md) 与 [角色正文](../assets/templates/role-body.md) 生成（仅含 `name`、`description` 与正文，不覆写 `model`、`tools`、`permissionMode` 或 `.claude/settings*.json`）。
2. `AGENTS.md` 写入共同 [薄入口](../assets/templates/project-entry-light.md)，`CLAUDE.md` 保留用户原文并追加 [桥接区块](../assets/templates/claude-entry.md)。预检项目与插件中是否存在同名角色冲突或禁用配置；被动尊重用户已配置的 Claude Code 权限或 Hook，不生成额外拦截配置。

## 生效与调用

主会话负责路由、两道门禁确认与静音连续巡航调度；需要独立审查、独立验收或多单元干净上下文隔离时委派上述子角色并传入 [最小派发短卡片](../../../workflow/handoff.md#派发短卡片正反例)。断连或未知调用按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 查询核实，不盲目重派。
