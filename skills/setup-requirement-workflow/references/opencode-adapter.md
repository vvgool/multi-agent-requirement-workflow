# OpenCode 薄适配

先执行 [通用安装步骤](installation.md)。提供项目Agent文件及共享包入口；OpenCode V1/V2和发行版能力须实际核对，不从其中一个版本推断其他版本已兼容。

## 文件与检查

三个项目角色为 `.opencode/agents/requirement-product.md`、requirement-development.md、requirement-testing.md。使用 [原生模板](../assets/templates/native-opencode.md) 和 [角色正文](../assets/templates/role-body.md)：description、mode=subagent，原生名称由文件名取得；正文加载锁定包内角色、完整Skill及真实模板。不写Codex专用developer_instructions或Claude专用字段，不覆盖model、permission、默认primary Agent或插件设置。

主会话入口使用共同AGENTS区块。预检当前版本支持的 opencode.json/opencode.jsonc、.opencode配置、适用AGENTS规则、插件或全局同名Agent；尊重配置中的委派/文件权限和disabled设置。支持JSONC时使用相应解析能力，不能用严格JSON否定合法注释文件。若项目通过instructions排除了入口或配置同名Agent遮蔽角色，先报告冲突；不覆写现有配置或追加通配权限。无法确认当前格式时查实际schema/能力，报告host_format_unsupported而不是猜格式。

## 生效与调用

新会话/已证实重载后，通过实际原生子Agent委派能力选择三个名称进行 initialization_probe=true。记录真实会话/任务标识及读取事实；仅看到Agent菜单或Skill列表不算派发通过。包内Skill以明确文件读取方式加载，不要求外部Skill扫描开关或符号链接，也不声称注册了原生skill工具入口。

实际Task/委派工具的名称、参数、同步等待和会话恢复按当前版本说明使用，不把某版sessionID字段写成公共协议。业务host.yaml记录真实host及ID；不支持查询旧任务时报告unknown/blocked，不伪造恢复。所有阶段遵守实际权限，不安装JS插件来绕过缺少的原生委派能力。

依据：[官方Agents](https://opencode.ai/docs/agents/)、[官方Skills](https://opencode.ai/docs/skills/)（2026-10-15核对）。文件层适配和真实版本验收分开，当前未完成OpenCode原生调用或完整需求闭环实测。
