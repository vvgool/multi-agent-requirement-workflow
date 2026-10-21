# 宿主适配契约

初始化按 [宿主选择规则](../skills/setup-requirement-workflow/references/installation.md#宿主选择与批量初始化) 加载全部目标宿主行；业务协调派发只加载当前实际宿主一行。统一产品/开发/测试/Bug角色及交接，宿主只负责真实注册、文件读取、派发、等待、结果和恢复；不复制阶段业务规则。

| host | 原生角色 product / development / testing / bug | 定义位置 | 适配说明 |
| --- | --- | --- | --- |
| codex | requirement_product / requirement_development / requirement_testing / requirement_bug | .codex/config.toml 受管registry区块 + .codex/agents/*.toml | [Codex](../skills/setup-requirement-workflow/references/codex-adapter.md) |
| claude-code | requirement-product / requirement-development / requirement-testing / requirement-bug | .claude/agents/*.md | [Claude Code](../skills/setup-requirement-workflow/references/claude-code-adapter.md) |
| opencode | requirement-product / requirement-development / requirement-testing / requirement-bug | .opencode/agents/*.md | [OpenCode](../skills/setup-requirement-workflow/references/opencode-adapter.md) |

## 确定的模板参数

原生文件以UTF-8/LF写入：product对应role=product-agent、role_file=agents/product-agent.md、skill_file=skills/requirement-analysis/SKILL.md、description=澄清需求并输出验收标准；development对应development-agent、agents/development-agent.md、skills/feature-development/SKILL.md、description=实现已批准需求并完成自验；testing对应testing-agent、agents/testing-agent.md、skills/acceptance-testing/SKILL.md、description=独立验收当前开发基线并报告缺陷。bug 对应 bug-agent、agents/bug-agent.md、skills/bug-fixing/SKILL.md、description=诊断并修复缺陷并完成自验。native_name取上表，不自行润色描述。

先对role-body.md进行上述原样字符串替换，再将完整正文（包括末尾换行，不strip/rstrip）替换原生模板的role_body；其他占位符同样替换，保留模板其余字节。共同入口、桥接和忽略区块使用模板完整原字节，不自选空白风格。追加时保留原文：原文非空且不以LF结束则先补一个LF，再追加完整模板；区块拥有摘要包含起始标记至结束标记后的LF，不包含原文或分隔LF。已有锁保持原字节，不要求其他机器重序列化。这样克隆后无本机回执也能确定性核对薄文件和拥有区块。

## 初始化输出与能力

本机回执 schema_version=2：package（真实四字段身份）、framework_path（项目相对路径）、owned_files（路径与实际SHA256）、owned_blocks（文件、标记、区块实际SHA256）、hosts。普通已有文件不作为整体拥有项；AGENTS/CLAUDE/.gitignore/.codex/config.toml 只拥有指定区块。默认初始化当前宿主和项目检测到的宿主；显式范围优先。全部目标先预检，再用同一 pending 安装，共享一份锁和缓存。非当前宿主只准备文件，不启动其程序；逐宿主报告 file_installation 和原生 pending。

hosts.<host> 保存真实可取得的 host_version（不可得=null）、role_mapping、file_installation、entry_probe、四个 native_role_probes（status、真实host_task_id或null、实际结果/原因）、native_role_invocation、end_to_end。状态为 passed/pending/failed；相同包下追加宿主时保留其他宿主有效回执，不把它们改成当前宿主通过；升级或拥有内容变化则将旧探测连同原包身份移入 hosts.<host>.probe_history，当前探测重置 pending。回执缺失不能接管已有未声明文件。

current host 必须来自实际会话或用户明确选定，不能从项目名称或安装目录推断。检查可用的注册格式、文件读取、原生角色选择、委派、等待/结束事实、恢复/查询、项目权限及外部连接；工具名和版本以实际宿主为准。不强行改模型/权限或安装宿主工具。原生选择缺失记 host_role_selection_unavailable，委派缺失记 host_delegation_unavailable；未知宿主返回 unsupported_host。某版本格式不支持时返回 host_format_unsupported，不套用另一个宿主配置。

文件校验只证明适配文件完整。生效后真实分别调用四个角色、传 initialization_probe=true 及当机项目/锁/框架路径；角色只读核对框架身份、角色、完整Skill及模板，返回实际事实。保存真实任务标识；缺标识说明限制。入口与四个原生探测均通过才将当前宿主 native_role_invocation=passed，不能用通用 Agent 阅读定义替代。不提供统一的重载命令，按实际能力启动新会话/重载；缺能力保持 pending。安装探测不执行 Issue/飞书写入，不创建业务需求。

回执中的 unavailable/pending 是上次探测事实，不能直接推断当前会话仍缺能力。当前会话实际提供映射的原生角色选择及委派工具时，重新执行只读探测并保存新任务标识及结果；工具出现本身不算 passed，end_to_end 仍只由真实需求闭环证明。

## 业务派发和恢复

本节与开头的当前host映射行用于正常派发；模板参数、初始化输出和探测步骤仅在初始化/恢复/升级时读取。协调层由逻辑角色映射当前宿主原生名，带 task、framework_root、包身份、授权及必读资料；原生角色在自身上下文加载共享角色和完整阶段 Skill。root active_run/run host.yaml 保存 host、实际任务标识、包身份和调用状态；查不到原任务不等于已结束。所有宿主使用同一状态、审批、修订与基线格式。

只有确认旧活动任务结束后才换宿主；新宿主须另有真实激活证据，生成新 run 和本机路径，保留旧宿主 ID，不尝试跨宿主复用它。恢复失败返回具体解除条件；不退化为协调 Agent 自演全部阶段。角色文案约束不是平台沙箱保证。

## 同 run 的方案通信

宿主有真实即时消息能力时，开发发送文稿路径、版本及状态，协调在原调用未结束时读取；没有即时能力时通过原任务查询及已有文稿恢复展示，说明实际尚未展示及能力限制，不创建额外通知文件。开发正常通知后继续，不等待展示回执、不结束/重派原任务。具体格式和消费以 [执行契约](execution-contract.md#开发中方案通知) 为准；消息只证明发送，展示/索引更新须有协调实际证据，不能将候选实践冒称锁定包已启用。
