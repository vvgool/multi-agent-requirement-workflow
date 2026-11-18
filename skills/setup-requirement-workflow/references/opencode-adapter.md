# OpenCode 薄适配

通用流程见 [安装与恢复](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与检查

1. 四个项目级薄角色为 `.opencode/agents/requirement-{product,development,testing,bug}.md`，由 [原生模板](../assets/templates/native-opencode.md) 与 [角色正文](../assets/templates/role-body.md) 生成（仅含 `description` 与 `mode: subagent`，不覆盖 `opencode.json`/`opencode.jsonc` 中的模型、权限或插件配置，不创建业务 `host.yaml`）。
2. 安装前核对 `opencode.json(c)` 中是否存在同名角色声明或显式禁用（支持 JSONC 注释语法）；发现同名冲突即停止整批写入，保留用户配置原字节。

## 生效与调用

委派前确认父会话工作目录绑定在目标业务项目根。通过宿主原生子代理工具（如 V2 `subagent` / V1 `task`）按需调用四个角色并传入 [最小派发短卡片](../../../workflow/handoff.md#派发短卡片正反例)；注意 `run --agent` 仅选择主角色、`debug agents` 仅证明配置发现，均不替代具名子角色调用。服务断连或遗留流式消息按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 确认无活动执行后再接续。
