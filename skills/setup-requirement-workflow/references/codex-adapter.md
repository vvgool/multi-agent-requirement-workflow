# Codex 薄适配

通用流程见 [安装与恢复](installation.md)，项目版本绑定见 [包规则](../../../workflow/package.md)。旧快照独立按 [旧安装流程](codex-installation.md) 处理，不共享新回执格式。

## 文件与检查

三个项目角色为 `.codex/agents/requirement_product.toml`、requirement_development.toml、requirement_testing.toml；分别绑定共享 product-agent/requirement-analysis、development-agent/feature-development、testing-agent/acceptance-testing。读取 [原生模板](../assets/templates/native-codex.toml) 和 [角色正文](../assets/templates/role-body.md)，填 name/description/developer_instructions，不指定 model、MCP或权限。另读取 [注册区块模板](../assets/templates/codex-registry.toml)，原字节追加到 `.codex/config.toml`；三个 `agents.<name>.config_file` 相对该配置文件指向 `agents/<name>.toml`。name/description 保留用于薄角色元数据；显式 registry 是本适配的注册来源，三份正文仍仅在角色文件中，不再生成第二套角色定义。不能只生成 standalone 文件就宣称注册完整。

主会话通过 AGENTS.md 的 [薄入口](../assets/templates/project-entry-light.md) 协调；不创建第四角色，不创建三个 Skill 发现链接。阶段角色明确读取锁定包内完整 Skill 及其模板，不把全局同名 Skill 视为本项目依赖。

预检现有 .codex/config.toml、项目/可见用户同名角色与父级适用设置、AGENTS.override.md；解析现有TOML，检查所有名称声明而非只比文件名。`agents.enabled=false` 或已知旧版本禁用子Agent的设置均需尊重；不知道配置语义时先核实当前版本，不修改配置绕过。入口被覆盖、同名来自插件/全局且无法确定实际选择时报告冲突。只读可见设置，不遍历用户凭据。

## 配置区块与安全生命周期

使用包内 [纯合并 helper](../scripts/codex_registry.py) 的 `merge(original_bytes, template_bytes, restore_only=False, previous_sha256=None)` 生成计划字节；它不读写项目、不执行安装或调度。以 `python3 -B` 调用，或在导入前设置 `sys.dont_write_bytecode=True`，禁止在锁定包内生成 `__pycache__`/pyc；不能导入后再清理或把缓存当包内容。调用前按通用规则核对锁、全部目标和归属；已有回执必须传其真实旧区块 SHA256，无回执仅允许全新安装或已核实同锁克隆恢复。Python 3.11 的 tomllib 或已存在的 tomli 均可；缺可靠解析器返回 toml_parser_unavailable，不安装依赖或降级正则解析。预检本机可见父级/用户同名设置仍由安装主会话负责，helper只检查传入文本，不证明不存在外部遮蔽。

- TOML 语义检查覆盖引号键、inline/dotted tables、profile内同名和显式禁用；原配置无关角色/注释/换行均保持原字节，不重序列化。缺半/重复/非规范标记、未知归属或区块被改动均停止。只认领 `# requirement-workflow:codex-registry:begin` 至 end 后LF，不认领 config.toml 整文件。
- `owned_blocks` 登记 `.codex/config.toml` 的上述标记及真实区块摘要；不进 `owned_files`。pending仍记录完整原文件bytes与before/after摘要、区块摘要和同目录暂存路径；恢复必须符合完整文件before或after，块外用户编辑同样阻塞。helper的 `matches_plan` 仅表达此完整字节边界，不替代事务或写前复核。
- 同包重复 merge 返回同一bytes，安装层不得触碰文件/mtime。新机器同锁恢复只能认领与锁定模板完全一致的注册区块及三个角色；restore_only 缺注册返回 host_not_initialized，修改返回 adapter_modified，不补区块。旧包无registry模板时仍沿旧包模板，不把本版规则倒灌旧锁。
- 显式升级才可用经过验证的旧回执区块摘要替换旧区块；仍须全部旧任务结束、全部已安装宿主覆盖和用户编辑保护。旧版只有standalone的安装在明确升级后可新增区块，不能以restore/add_host修补已有Codex。升级后的Codex旧探测移入probe_history并重置pending；不沿用passed。
- 不写 features、agents.enabled、模型、权限、MCP或全局trust来绕过禁用。项目不可信时报告 project_config_untrusted；由用户/宿主正常信任流程处理。版本不支持格式/角色选择时分别报告 host_format_unsupported/host_role_selection_unavailable，不推断其他版本。

## 生效与调用

在实际支持原生角色的Codex新会话或已证实重载后，通过工具真实角色选择机制调用上述三个名称并传 initialization_probe=true。没有名称选择参数不以通用spawn替代。记录实际宿主任务ID与结果，单独标明入口探测；终端不存在codex命令不能单独证明桌面/IDE宿主不支持。

业务派发、等待和查询按实际工具接口执行；名称、host任务标识与通用逻辑角色分别保存。未知调用先恢复，不重复派发。继承实际父会话权限，文案不等于独立只读沙箱。

依据：[官方自定义角色](https://learn.chatgpt.com/docs/agent-configuration/subagents)与 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)（2026-10-18核对；config_file相对声明配置解析）。ChatGPT捆绑CLI 0.162.0-alpha.17.2已在只读单变量实验中实际加载旧薄文件并调用product，文件中的name/description未阻止config_file加载；完整新包仍须按下述三角色实测，不将接口出现等同生效。。格式文件验证与真实当前宿主调用分别报告；不宣称已验证所有Codex版本。
