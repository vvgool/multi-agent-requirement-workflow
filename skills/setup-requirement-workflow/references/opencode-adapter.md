# OpenCode 薄适配

先执行 [通用安装步骤](installation.md)。提供项目Agent文件及共享包入口；OpenCode V1/V2和发行版能力须实际核对，不从其中一个版本推断其他版本已兼容。

## 文件与检查

四个项目角色为 `.opencode/agents/requirement-product.md`、requirement-development.md、requirement-testing.md、requirement-bug.md。使用 [原生模板](../assets/templates/native-opencode.md) 和 [角色正文](../assets/templates/role-body.md)：description、mode=subagent，原生名称由文件名取得；正文加载锁定包内角色、完整Skill及真实模板。不写Codex专用developer_instructions或Claude专用字段，不覆盖model、permission、默认primary Agent或插件设置。

主会话入口使用共同AGENTS区块。预检当前版本支持的 opencode.json/opencode.jsonc、.opencode配置、适用AGENTS规则、插件或全局同名Agent；尊重配置中的委派/文件权限和disabled设置。支持JSONC时使用相应解析能力，不能用严格JSON否定合法注释文件。若项目通过instructions排除了入口或配置同名Agent遮蔽角色，先报告冲突；不覆写现有配置或追加通配权限。无法确认当前格式时查实际schema/能力，报告host_format_unsupported而不是猜格式。

V2 使用 `agents`、`system`、`disabled` 和有序 `permissions` 列表，V1 常见字段为 `agent`、`prompt`、`disable`、`permission`。先核对当前发行版；兼容读取不代表应把V1字段写入V2。薄Markdown仍仅使用共同的description/mode和正文，不生成整份JSON配置。

先检查实际加载的配置来源与原始同名声明，再核对有效角色。OpenCode 2.0.32实测：合法JSONC中 `agent` 与 `agents` 均可读，但项目Markdown可能盖过JSON同名description乃至disabled字段；因此仅看 `debug agents` 中角色存在/未禁用会漏掉用户意图冲突。同名声明即停止整批安装，不能以“最终加载的角色正确”接管它。只读核对全局配置中的相关角色、权限和入口字段，日志不复制凭据或整份配置；不能可靠取得来源时报告预检能力不足。

## 生效与调用

原生委派前核对真实父会话的项目目录：CLI 从目标项目目录启动，API 创建会话时显式传该版本支持的 location。通过实际会话查询确认父会话目录与目标项目真实路径一致，再在同一目录查询有效角色；仅在提示词写目标路径、shell 中切换目录或在另一目录执行 `debug agents` 不会改变已有父会话绑定。目录不一致时停止探测并新建绑定正确目录的主会话；有活动业务任务时先按恢复规则核实，不迁移或重复派发。

遇到 `Unknown agent` 时先对照父会话目录与发现目录，并查询该父目录的角色表，保留失败调用身份；若真实目录不符，不先改角色名、覆盖配置、升级宿主或把 `--standalone` 当作目录修复。目录一致仍失败时再沿当前发行版解析/路由定位，无法核实则保持 blocked。

新会话/已证实重载后，通过实际原生子Agent委派能力选择四个名称进行 initialization_probe=true。记录真实会话/任务标识及读取事实；仅看到Agent菜单或Skill列表不算派发通过。包内Skill以明确文件读取方式加载，不要求外部Skill扫描开关或符号链接，也不声称注册了原生skill工具入口。

实际Task/委派工具的名称、参数、同步等待和会话恢复按当前版本说明使用，不把某版sessionID字段写成公共协议。协议3由宿主原生会话/任务保留真实host及ID，仅在恢复需要时引用，不创建业务host.yaml；旧协议1/2任务的host.yaml只由原锁定包解释。不支持查询旧任务时报告unknown/blocked，不伪造恢复。所有阶段遵守实际权限，不安装JS插件来绕过缺少的原生委派能力。

断连与服务崩溃按[恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续)处理。v2.1.4隔离实测中，私有服务进程退出后原消息可残留streaming，重启不会自动补成最终结果；结合原进程退出和实际活动查询（该版GET /api/session/active）确认无活动执行后，可在原会话接续尚未完成的只读工作。该实测不代表获得终止共享服务的授权，也不能证明其他版本接口或外部写入可以安全重试。文件安装或激活通过，不能视为自动恢复通过。

V2 的原生工具为 `subagent`，V1 常见为 `task`；父角色的实际委派权限同样必须允许该原生名称。`run --agent` 只选主角色，`debug agents` 只证明发现，均不能替代具名子角色调用。不得使用 `--auto` 或临时放开权限来让探测通过。

依据：[V1 Agents](https://opencode.ai/docs/agents/)、[V2 Agents](https://opencode.ai/v2/docs/agents/)、[V2迁移](https://opencode.ai/v2/docs/migrate-v1/)（2026-10-19核对）。机制依据、文件层适配和绑定包摘要的实际原生验收分别记录；不单凭文档说明宣称业务闭环通过。
