# 通用 AGENTS.md 规则宿主适配（agents-md）

配套见 [四宿主映射与规则型宿主](../../../workflow/host-adapters.md#四宿主映射与规则型宿主) 与 [通用安装、恢复与升级](installation.md)。

`agents-md` 是原生读取项目根 `AGENTS.md` 的**通用规则型宿主**标准档位，覆盖 **Zed、Cursor、Windsurf、Antigravity** 等环境（`--hosts zed` 自动归一化为 `agents-md`）。安装、恢复与升级仅维护根 `AGENTS.md`、`.gitignore`、`workflow.yaml`、`workflow.lock.yaml` 与缓存，**不生成 `.zed/agents`、`.cursor/agents` 等专属角色目录**，也不修改宿主模型、权限或全局设置。

## 根规则加载与权限边界

- 核对当前工作区根与高优先级本地规则（如 `.rules`、`.cursorrules`、`.windsurfrules`）是否遮蔽根 `AGENTS.md` 受管块，冲突时提示用户对齐，禁静默覆盖。
- 宿主权限开关（如 Zed `Write / Ask / Minimal` 或 IDE 自动执行）仅管工具调用，绝不替代 [人工确认](../../../workflow/execution-contract.md#人工确认) 的 `Spec Gate` 业务批准。

### 非具名独立协作

宿主提供可建**全新独立上下文**的子代理工具（如 Zed `spawn_agent` 或 Antigravity / Cursor 独立子代理）时，按以下契约委派异体审查、独立验收或写集隔离单元：

- **显式注入缓存与写集**：传入项目根、锁定缓存 `.agents/requirement-workflow-cache/<sha256>/`、对应 `agents/<role>.md` + `skills/<skill>/SKILL.md`、关联 `AC` 及允许写集（可配 `verify_feature.py --write-snapshot / --check-writes --since` 锁边界）。
- **回读真实标识与证据**：回读真实子会话 ID、独立上下文关系与运行输出后方可计入审查/验收（如实记为非具名子代理，**严禁同会话换口吻自审**，且 `Spec Gate` 前审查与实施后验收禁复用同一子会话）。
- **纯单会话降级**：不支持独立子会话时按 [业务派发与降级路径](../../../workflow/host-adapters.md#业务派发与降级路径) 披露限制并标阻塞。

## Zed ACP 外部 Codex 边界

Zed 经 ACP 挂载外部 Codex 时须核对真实项目根目录，具名子角色可用性按 [Codex 适配](codex-adapter.md) 实际能力判定，仍不建 `.zed/agents`；外部 CLI 单跑不等同于宿主会话联调通过。
