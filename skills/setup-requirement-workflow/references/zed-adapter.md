# Zed 宿主适配

配套入口：[Zed 宿主入口](../../../workflow/hosts/zed.md)。

Zed 在本适配中是规则型宿主，项目级 Agent 规则入口使用仓库中的 `AGENTS.md`。初始化 Zed 时只需确保项目根目录存在并更新了本框架的 `AGENTS.md` 入口；不生成 Zed 角色文件，也不要为 Zed 伪造 `.zed/agents`、`.opencode/agents` 或其他宿主的原生角色注册文件。Zed 只有在用户明确指定或当前会话确认为 Zed 时参与宿主选择，`AGENTS.md` 本身不是可靠的 Zed 项目标识。

## Zed自带Agent

先核对真实Zed线程、项目根、版本、所选provider/model及Profile。Profile控制工具可用性，工具权限另行决定调用是否需要确认；Write/Ask/Minimal不是业务角色或阶段批准。核对本版Instructions实际来源：`.rules`、其他兼容指令文件可能优先于 `AGENTS.md`，个人指令和自动Skills也可能影响行为；入口被遮蔽先报告冲突，不覆盖用户规则或更改全局配置。

自带Agent从共享入口核验本臂锁包，按 [人工确认](../../../workflow/execution-contract.md#人工确认) 执行需求、设计、小修、交付与恢复。文件存在不等于实际加载，必须回读实际线程中的工具及修改证据。阶段Skill按锁包内完整路径读取，不复制到Zed发现目录。

### 非具名独立协作

没有项目级具名注册不等于没有委派能力。实际版本提供 `spawn_agent` 且能建立独立上下文时，可显式派发专业子Agent：给出真实项目根、本臂锁/包、对应 `agents/*.md`、完整阶段Skill、当前目标和只读/单写范围；子Agent自行完整核验并返回实际结果。核对真实父子任务/线程标识、角色及Skill加载、未参与受审对象起草、结果与结束事实，才能计入独立审查或验收。不同称呼或同一Agent换口吻不是独立验证。

此路径不宣称注册了四个具名角色，不把非具名子Agent填为四角色激活通过。模型/工具继承、停止/恢复以实际版本为准；缺必要能力或证据只阻塞受影响环节，可继续授权内独立部分，不能降为自审后报整体完成。

## ACP外部Codex

真实Zed外部Codex线程经ACP适配器调用Codex运行时，与自带Agent分开验证。分别核对Zed/适配器/Codex版本、实际运行入口及覆盖配置、项目根/ACP session/底层线程关联、工具与权限事件、MCP转发及原生MCP配置叠加。Zed Profile、Skills及指令加载器不能自动外推为Codex配置；具名角色按 [Codex适配](codex-adapter.md) 核对实际加载和调用，不创建 `.zed/agents`。

脱离Zed直连ACP只证明适配器路径；Codex CLI通过也不证明Zed通过。必要时由用户在真实Zed线程按固定输入操作并提供脱敏工具/日志证据，时间单列；未知调用先查原ID，不重发。不预设子会话显示、UI自动化或特定ACP扩展已支持。

## 共同能力边界

- **规则读取**：实际 Zed 会话读取项目规则后，可按 `AGENTS.md` 执行本框架的路由、风险、验证和文档约束；文件存在不等于已完成 Zed 会话探测。
- **角色执行**：自带Agent默认直接处理，必要独立协作按上述非具名契约取证；外部Codex按其实际运行时能力，不把普通会话自称为已注册的框架角色。
- **持久跟踪**：复杂事项仍按项目规则维护唯一的 `agent-features/<事项名称>/task.md`，并按需维护需求、技术设计、实施计划和验收文档。
- **验证**：Zed 中执行的命令、测试和文件修改必须绑定当前确认的项目根目录；局部验证不得外推为全量通过。
- **外部写入**：不因 Zed 具备 Agent Panel 就自动发送消息、发布或执行生产写入。未知外部结果先查询原调用，不重放。

## 安装与报告

Zed规则型安装事实是共享入口符合锁包；自带Agent的 `native_role_probes` 为空，`native_role_invocation` 为 `not_applicable`，不表示无独立子Agent能力。实际非具名协作及业务闭环结果留原验证文档，关联任务ID，不新增回执字段。外部Codex按运行层另列具名探测证据，不用Zed回执替代Codex激活，也不改历史回执。规则可读、实际加载、工具能力、独立协作、业务结果和未验项分别报告。

依据（2026-11-16）：[Zed Agent](https://zed.dev/docs/ai/zed-agent)、[Instructions](https://zed.dev/docs/ai/instructions)、[Tools](https://zed.dev/docs/ai/tools)、[External Agents](https://zed.dev/docs/ai/external-agents)。官网能力不代替本机版本实测。
