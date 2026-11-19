# Claude Code 适配

通用流程见 [通用安装、恢复与升级](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与检查

1. 四个项目级预编译角色为 `.claude/agents/requirement-{product,development,testing,bug}.md`，由 `install_helper.py` 将重写缓存链接后的角色职责、`SKILL` 与 [角色正文](../assets/templates/role-body.md) 内联渲染进 [原生模板](../assets/templates/native-claude-code.md)（仅含 `name`、`description` 与预编译正文，不覆写 `model`、`tools`、`permissionMode` 或 `.claude/settings*.json`）。
2. `AGENTS.md` 写入共同 [薄入口](../assets/templates/project-entry-light.md)，`CLAUDE.md` 保留用户原文并合并 [桥接区块](../assets/templates/claude-entry.md)。安装前检查同名角色冲突并被动尊重用户既有权限与 Hook。

## 生效与调用

主会话负责路由、单次 `Spec Gate` 确认、静音连续巡航与 `verify_feature.py` 收口门禁；需独立审查、独立验收或多单元隔离时直接委派预编译子角色并传入 [最小派发短卡片](../../../workflow/handoff.md#派发短卡片正反例)。断连或未知调用按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 核实。
