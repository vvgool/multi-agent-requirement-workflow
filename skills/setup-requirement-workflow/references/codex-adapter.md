# Codex 薄适配

通用流程见 [安装与恢复](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与配置合并

1. 四个项目级薄角色为 `.codex/agents/requirement_{product,development,testing,bug}.toml`，由 [原生模板](../assets/templates/native-codex.toml) 与 [角色正文](../assets/templates/role-body.md) 渲染 `name`、`description`、`developer_instructions`，并将 [注册区块](../assets/templates/codex-registry.toml) 通过 [codex_registry.py](../scripts/codex_registry.py) 合并至 `.codex/config.toml`（始终以 `-B` 运行，保留用户既有角色、注释与 CRLF 原字节，不篡改模型、权限或 `agents.enabled`）。
2. 人工确认按 [权威门禁](../../../workflow/execution-contract.md#人工确认) 执行：若宿主提供异步提问工具（如 `request_user_input_async`），返回 `accepted:true` 仅证明问题已受理，必须停在本轮等待并核对后续真实用户答案，严禁将受理回执或默认选项当作批准。

## 生效与调用

### 无具名选择参数时的业务独立协作

业务确需独立审查、验收或多单元上下文隔离时，优先调用已注册具名角色；若当前工具缺少具名角色选择参数但支持创建独立子会话，按以下降级契约执行（不将其计为具名激活探测通过）：

- 派发携带目标项目根、当前锁定缓存路径、必要业务文档、目标与允许范围，以及对应包内角色和完整Skill路径；实际工具支持独立上下文时选择独立上下文，不借父会话自审代替。
- 子会话自己定位锁定缓存、读取对应角色和完整Skill后再执行审查或验收；审查者须未参与被审内容起草或实现。
- 父会话回读真实子任务标识、父子关系、加载与执行证据及结果；缺独立上下文、必要加载或实际结果时，受影响审查/验收仍阻塞。

### 原生只读/沙箱被动兼容

本框架不主动修改 Codex 沙箱或审批配置。若用户或宿主显式以原生只读沙箱启动规划阶段会话，前期协调、规格起草与后台独立审查结论暂留对话，待 `Spec Gate` 真实批准完成后由用户/宿主开启可写会话落盘事项文档并进入静音连续巡航。断连或异常退出按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 处理。
