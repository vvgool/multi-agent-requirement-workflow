# Zed 宿主入口

项目初始化先读 [通用 setup Skill](../../skills/setup-requirement-workflow/SKILL.md)，按 [包规则](../package.md) 取得锁定版本，再执行 [Zed 适配](../../skills/setup-requirement-workflow/references/zed-adapter.md)。Zed 在本框架中是规则型宿主：复用项目根目录的 `AGENTS.md`，不生成 `.zed/agents`，也不注册 product、development、testing、bug 四个原生角色。

Zed 没有可靠的项目级检测信号，只有用户明确指定 Zed 或当前会话确认为 Zed 时纳入宿主选择。`AGENTS.md` 是共享入口，不能单独证明当前会话由 Zed 运行；实际宿主版本、规则加载和工具能力必须分别核对。

Zed 的文件安装事实仅包括共享 `AGENTS.md` 入口存在且内容符合锁定包；回执中的 `native_role_probes` 为空，`native_role_invocation` 为 `not_applicable`。规则读取不等于原生角色激活，也不等于业务闭环完成。

一次性局部低风险小修由当前 Agent 直接执行；需要其他专长时明确说明当前宿主没有项目级原生角色委派，不把普通会话或通用子会话冒称为已激活的框架角色。复杂事项仍按共享规则维护唯一 `task.md`，外部写入和真实业务闭环分别验证。
