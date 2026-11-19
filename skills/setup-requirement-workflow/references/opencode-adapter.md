# OpenCode 适配

通用流程见 [通用安装、恢复与升级](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与检查

1. 四个项目级预编译角色为 `.opencode/agents/requirement-{product,development,testing,bug}.md`，由 `install_helper.py` 将重写缓存链接后的角色职责、`SKILL` 与 [角色正文](../assets/templates/role-body.md) 内联渲染进 [原生模板](../assets/templates/native-opencode.md)（仅含 `description` 与 `mode: subagent`，不覆盖 `opencode.json`/`opencode.jsonc`，不创建业务 `host.yaml`）。
2. 安装前核对 `opencode.json(c)` 是否存在同名角色声明或显式禁用（支持 JSONC 注释）；遇冲突零写入退出并保留用户原字节。

## 生效与调用

委派前确认父会话工作目录绑定目标项目根，通过原生子代理工具（V2 `subagent` / V1 `task`）调用预编译子角色并传入 [最小派发短卡片](../../../workflow/handoff.md#派发短卡片正反例)；`Spec Gate` 前独立审查与实施后最终对抗验收严禁复用同一子会话 `sessionID`。V2 后台异步挂起等待回传时注明“后台完成后自动接续，无需回复继续”，唤醒后若处于 `ready_to_implement` 则继续巡航。`run --agent` 仅选主角色、`debug agents` 仅证配置发现，均不替代具名子角色调用；断连按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 处理。
