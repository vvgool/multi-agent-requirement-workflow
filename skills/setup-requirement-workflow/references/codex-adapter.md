# Codex 薄适配

通用流程见 [安装与恢复](installation.md)，项目版本绑定见 [包规则](../../../workflow/package.md)。旧快照独立按 [旧安装流程](codex-installation.md) 处理，不共享新回执格式。

## 文件与检查

四个项目角色为 `.codex/agents/requirement_product.toml`、requirement_development.toml、requirement_testing.toml、requirement_bug.toml；分别绑定共享 product-agent/requirement-analysis、development-agent/feature-development、testing-agent/acceptance-testing、bug-agent/bug-fixing。读取 [原生模板](../assets/templates/native-codex.toml) 和 [角色正文](../assets/templates/role-body.md)，填 name/description/developer_instructions，不指定 model、MCP或权限。另读取 [注册区块模板](../assets/templates/codex-registry.toml)，原字节追加到 `.codex/config.toml`；四个 `agents.<name>.config_file` 相对该配置文件指向 `agents/<name>.toml`。name/description 保留用于薄角色元数据；显式 registry 是本适配的注册来源，四份正文仍仅在角色文件中，不再生成第二套角色定义。不能只生成 standalone 文件就宣称注册完整。

主会话通过 AGENTS.md 的 [薄入口](../assets/templates/project-entry-light.md) 协调；不创建协调子角色，不创建 Skill 发现链接。阶段角色明确读取锁定包内完整 Skill 及其模板，不把全局同名 Skill 视为本项目依赖。

人工确认按 [权威规则](../../../workflow/execution-contract.md#人工确认) 执行。若本版宿主提供异步提问，`request_user_input_async` 的 `accepted:true` 仅证明问题已受理；保持等待，核对后续真实用户答案，不从 CLI 退出码、工具成功或所列默认选项推断批准。

预检现有 .codex/config.toml、项目/可见用户同名角色与父级适用设置、AGENTS.override.md；解析现有TOML，检查所有名称声明而非只比文件名。`agents.enabled=false` 或已知旧版本禁用子Agent的设置均需尊重；不知道配置语义时先核实当前版本，不修改配置绕过。入口被覆盖、同名来自插件/全局且无法确定实际选择时报告冲突。只读可见设置，不遍历用户凭据。

## 配置区块与安全生命周期

使用包内 [纯合并 helper](../scripts/codex_registry.py) 的 `merge(original_bytes, template_bytes, restore_only=False, previous_sha256=None)` 生成计划字节；它不读写项目、不执行安装或调度。以 `python3 -B` 调用，或在导入前设置 `sys.dont_write_bytecode=True`，禁止在锁定包内生成 `__pycache__`/pyc；不能导入后再清理或把缓存当包内容。调用前按通用规则核对锁、全部目标和归属；已有回执必须传其真实旧区块 SHA256，无回执仅允许全新安装或已核实同锁克隆恢复。Python 3.11 的 tomllib 或已存在的 tomli 均可；缺可靠解析器返回 toml_parser_unavailable，不安装依赖或降级正则解析。预检本机可见父级/用户同名设置仍由安装主会话负责，helper只检查传入文本，不证明不存在外部遮蔽。

- TOML 语义检查覆盖引号键、inline/dotted tables、profile内同名和显式禁用；原配置无关角色/注释/换行均保持原字节，不重序列化。缺半/重复/非规范标记、未知归属或区块被改动均停止。只认领 `# requirement-workflow:codex-registry:begin` 至 end 后LF，不认领 config.toml 整文件。
- `owned_blocks` 登记 `.codex/config.toml` 的上述标记及真实区块摘要；不进 `owned_files`。pending仍记录完整原文件bytes与before/after摘要、区块摘要和同目录暂存路径；恢复必须符合完整文件before或after，块外用户编辑同样阻塞。helper的 `matches_plan` 仅表达此完整字节边界，不替代事务或写前复核。
- 同包重复 merge 返回同一bytes，安装层不得触碰文件/mtime。新机器同锁恢复只能认领与锁定模板完全一致的注册区块及四个角色；restore_only 缺注册返回 host_not_initialized，修改返回 adapter_modified，不补区块。旧包无registry模板时仍沿旧包模板，不把本版规则倒灌旧锁。
- 显式升级才可用经过验证的旧回执区块摘要替换旧区块；仍须确认全部旧任务已结束、升级范围覆盖全部已安装宿主，并保护用户编辑的内容。旧版只有standalone的安装在明确升级后可新增区块，不能以restore/add_host修补已有Codex。升级后的Codex旧探测移入probe_history并重置pending；不沿用passed。
- 不写 features、agents.enabled、模型、权限、MCP或全局trust来绕过禁用。项目不可信时报告 project_config_untrusted；由用户/宿主正常信任流程处理。版本不支持格式/角色选择时分别报告 host_format_unsupported/host_role_selection_unavailable，不推断其他版本。

## 生效与调用

Codex原生CLI/App Server与Zed经ACP调用Codex须分开取证：后者同时核对实际Zed线程、ACP session与底层Codex线程/项目根，不能用独立CLI探测替代。可执行文件可能来自已安装适配器依赖，PATH缺命令不能判定缺能力。版本/实际配置来源、项目trust、原生工具及角色选择分别验证；最新文档的standalone支持不能证明本版registry已加载，格式不符先报告，不改真实安装、权限或基线来绕过。

在实际支持原生角色的Codex新会话或已证实重载后，通过工具真实角色选择机制调用上述四个名称并传 initialization_probe=true。具名激活探测中，没有名称选择参数不以通用spawn替代。记录实际宿主任务ID与结果，单独标明入口探测；终端不存在codex命令不能单独证明桌面/IDE宿主不支持。

具名调用不可用时分别核查三层：文件是否符合当前版本格式、宿主是否实际加载该项目注册、当前会话工具是否提供具名角色选择。宿主提供有效配置查询时（如支持config/read的版本），仅提取四角色路径、来源及配置层禁用原因，不输出整份用户配置或凭据。有效配置已加载仍不代表角色已调用；此时缺选择参数应记录host_role_selection_unavailable，不反复安装、改文件格式或重启来猜测修复。四角色探测保持pending，不能据此报全宿主激活通过；业务协作按下方实际能力判断，当前会话可直接完成的工作按[业务派发规则](../../../workflow/host-adapters.md#业务派发和恢复)继续。

### 无具名选择参数时的业务独立协作

业务确需另一专长时，先核对当前调用实际提供的角色选择和独立上下文能力；有具名选择机制时按映射调用。缺少具名选择参数但可以创建独立子会话时，允许该子会话显式承担包内专业职责，按以下方式执行，不将其计为具名激活探测通过：

- 派发携带目标项目、当前锁定包、必要业务文档、目标与允许范围，以及对应包内角色和完整Skill路径；实际工具支持独立上下文时选择独立上下文，不借父会话自审代替。
- 子会话自己核对包身份、读取对应角色和完整Skill，再实际审查或验收；审查者未参与被审内容起草或实现，结论绑定当前被审文稿或实现。只有角色名称、自述PASS或父会话摘要不足以成立。
- 父会话回读真实子任务标识、父子关系、加载与执行证据及结果，分别记录实际子会话身份与逻辑专业职责。如实称独立子会话显式加载角色，不称调用了已注册的`requirement_development/testing`；具名激活仍保持pending及实际缺能力原因。

该业务路径不改变模型、权限、全局配置、项目trust或回执schema，不绕过宿主明确禁用的子Agent设置。缺独立上下文、必要加载或实际结果时，受影响审查/验收仍阻塞；人工确认和未决问题仍按权威规则处理。CLI与Zed经ACP的实际调用分别取证，一条路径的能力不推断另一条。

业务派发、等待和查询按实际工具接口执行；名称、host任务标识与通用逻辑角色分别保存。未知调用按[恢复判定与接续](../../../workflow/host-adapters.md#恢复判定与接续)处理。子角色继承实际父会话的权限；仅在文案中要求只读，不等于已建立独立的只读沙箱。

### 显式选择的原生只读阶段

仅当用户或宿主所有者明确选择本任务采用分阶段原生权限，并已核实实际限制时使用本节。它与上方不改变权限的业务角色派发不同：权限由受约束模型之外的用户/宿主选择，不由模型根据自己的批准摘要切换。当前会话原本可写时，不能靠读取本节或发送“继续”宣称已变只读。

开始前须已有可只读核验的锁定包与安装环境；缺缓存、配置或来源时保持阻塞，不为开启本模式修复安装、改trust或设置可写文档目录。按当前版本实际入口核对父工具、原生补丁、必需独立子会话及路径别名的项目写入限制，以真实拒绝和文件核对为依据；参数存在、模型自拒或只测一个shell不足以证明其他通道。任一实际启用通道能绕过限制，或必需子会话不能受约束时，受影响流程保持阻塞，不退回可写加提示或新增拦截器。

1. 用户/宿主以原生只读且不可提权的权限启动本任务规划会话。本机Codex CLI 0.166.0已对`--no-daemon --sandbox read-only --ask-for-approval never exec -C <目标项目>`实际工具通道作限定校准；其他版本须查实际参数和行为，不能外推Zed/ACP。模型保留需求与设计两次展示/确认及适用独立前审；前期协调、需求、设计、计划与审查事实按[受约束文稿规则](../../../workflow/documents.md#原生只读阶段的前期文稿)暂留原生对话，项目已有文档只读引用。业务澄清、拒绝、未答、仅需求批准或提问受理均不开放写入。
2. 当前需求、设计都真实获批且适用独立审查无阻断后，先查询原执行并确认停止，由用户/宿主开启本任务新的可写上下文。模型不能自行重启为可写、提权或在原会话动态放权。新上下文先核对实际展示的当前稿、原用户回复/定位、审查对象及结论；只拿到“已批准”的AI摘要不足以继续。先将这些当前已审已批内容与原生引用保存到原唯一事项文档，再实施同一批准范围；内容实质改变时按权威规则确认受影响部分。
3. 规划阶段恢复仍须核对实际只读权限和原批准来源，不能由旧摘要推定写入许可。原执行或旧写入结果未知时先查原任务及文件/数据库，不重复启动写入者，不自动重放、回滚或补偿。稿件、批准来源或审查绑定无法核对时，受影响实施保持暂停。

该限制只覆盖实际验证过的受保护项目写入，不禁止对话输出设计或代码，也不约束宿主正常会话日志。新可写会话开放后不自动识别语义越界；遇到受影响的新方案，仍需用户/宿主停止写入并按原规则确认。普通永久可写会话仍依赖指令遵守，不能用本模式的结果撤销其既有反例；具名激活、完整业务流程、CLI与真实ACP路径均分别取证。不改变全局配置、模型、认证、角色注册、回执schema或其他任务权限。

依据：[官方自定义角色](https://learn.chatgpt.com/docs/agent-configuration/subagents)与 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)（2026-10-18核对；config_file相对声明配置解析）。ChatGPT捆绑CLI 0.162.0-alpha.17.2已在只读单变量实验中实际加载旧薄文件并调用product，文件中的name/description未阻止config_file加载；完整新包仍须按上述四角色实测，不将接口出现等同生效。格式文件验证与真实当前宿主调用分别报告；不宣称已验证所有Codex版本。
