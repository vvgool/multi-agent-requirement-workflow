# Zed 宿主适配

配套契约见 [宿主适配与规则型宿主](../../../workflow/host-adapters.md#四宿主映射与规则型宿主)。

Zed 在本框架中定义为**规则型宿主**，复用项目根目录 `AGENTS.md` 中的受管入口区块：初始化时不生成 Zed 角色文件，也不伪造 `.zed/agents` 或其他宿主目录。Zed 仅在用户明确指定或当前会话确认为 Zed 时纳入宿主选择；初始化核验中 `native_role_probes` 为空、`native_role_invocation` 记为 `not_applicable`。

## Zed 自带 Agent 与非具名独立协作

- 先核对真实 Zed 线程、项目根、Profile（Write/Ask/Minimal 为工具权限而非业务阶段批准）以及 `.rules` 等高优先级规则是否遮蔽 `AGENTS.md`；不覆盖用户规则或全局设置。
- 自带 Agent 按 `AGENTS.md` 与 [人工确认](../../../workflow/execution-contract.md#人工确认) 执行小修直通、不确定性驱动 `Spec Gate` 与静音连续巡航。

### 非具名独立协作

若当前 Zed 版本提供 `spawn_agent` 并能建立**独立上下文**，可在需要独立审查、独立验收或多单元隔离时显式派发非具名专业子 Agent：传入项目根、锁定缓存路径、对应 `agents/*.md` 与完整阶段 `SKILL.md` 及允许范围；父会话回读真实实际线程/子任务标识与执行结果后，可计入独立审查/验收（如实记录为非具名独立子 Agent，不冒称具名四角色注册激活；同一线程换口吻自审不计入独立验证）。

## ACP 外部 Codex 边界

Zed 经 ACP 调用外部 Codex 运行时与 Zed 自带 Agent 分属不同执行链路：需核对 ACP session 与底层 Codex 项目根关联，具名角色按 [Codex 适配](codex-adapter.md) 实际能力判断，仍不生成 `.zed/agents`，脱离真实 Zed 的独立 CLI 结果不自动代表真实 Zed 线程通过。
