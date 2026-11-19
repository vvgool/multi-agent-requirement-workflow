# Codex 适配

通用流程见 [通用安装、恢复与升级](installation.md)，项目派发契约见 [宿主适配](../../../workflow/host-adapters.md)。

## 文件与预编译配置合并

1. 四个项目级预编译角色为 `.codex/agents/requirement_{product,development,testing,bug}.toml`：安装期自动剥离对应 `agents/*.md` 与 `skills/*/SKILL.md` 头信息、将包内相对链接重写为锁定缓存路径，合入 [角色正文](../assets/templates/role-body.md) 后对 `\`、`"""` 与控制字符做无损转义写入 [原生模板](../assets/templates/native-codex.toml)，并经 [codex_registry.py](../scripts/codex_registry.py) `_parse` 往返等价核验；同时将 [注册区块](../assets/templates/codex-registry.toml) 保原字节合并至 `.codex/config.toml`（不篡改既有角色、模型、权限或 `agents.enabled`）。
2. 人工确认遵循 [权威门禁](../../../workflow/execution-contract.md#人工确认)：若宿主提供异步提问工具（如 `request_user_input_async`），返回 `accepted:true` 仅代表问题已受理，必须停在本轮等待真实用户授权，严禁将受理回执当作批准。

## 生效与调用

### 无具名选择参数时的业务独立协作

业务确需异体独立审查、独立验收或多单元上下文隔离时，优先调用上述已注册具名角色（冷启动零规则跳读）；若当前工具缺少具名角色选择参数但支持创建独立子会话，按以下降级契约执行（不冒称具名激活通过）：

- 派发携带项目根、锁定缓存路径、目标与允许写集，以及对应缓存内 `agents/<role>.md` 与 `skills/<skill>/SKILL.md` 路径，启用独立上下文而非父会话自审。
- 子会话未参与被审内容起草或实现，按缓存规则只读审查或运行反例验收。
- 父会话回读真实子任务标识与执行证据；缺独立上下文或真实输出时受影响门禁保持阻塞。

### 原生只读/沙箱被动兼容

本框架不主动修改 Codex 沙箱或审批策略。若用户以只读沙箱启动规划会话，前期规格与审查结论暂留对话，待 `Spec Gate` 获真实批准后在可写会话落盘文档并进入静音巡航。异常中断按 [恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续) 处理。
