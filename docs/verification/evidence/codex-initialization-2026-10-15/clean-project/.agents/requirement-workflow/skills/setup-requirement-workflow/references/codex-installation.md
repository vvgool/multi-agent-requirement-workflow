# Codex 项目级安装

本流程由宿主执行文件操作，统一规则仍来自框架角色和 Skill。原生配置依据：[自定义角色](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Skill 发现](https://learn.chatgpt.com/docs/build-skills)。核实日期为 2026-10-15；使用不支持该格式的旧宿主时报告能力不足，不静默改用旧格式。

## 文件归属与映射

目标项目中使用以下固定相对位置；名称冲突时阻塞，不静默改名。安装目录内不包含作者机器路径。

| 位置 | 内容 |
| --- | --- |
| .agents/requirement-workflow/ | 框架快照：AGENTS.md、README.md、workflow.yaml、agents/、skills/、workflow/、templates/ |
| .codex/agents/requirement_product.toml | product-agent → requirement-analysis |
| .codex/agents/requirement_development.toml | development-agent → feature-development |
| .codex/agents/requirement_testing.toml | testing-agent → acceptance-testing |
| .agents/skills/requirement-analysis 等 | 三个执行 Skill 的相对目录符号链接，目标为 ../requirement-workflow/skills/同名目录 |
| AGENTS.md 的 requirement-workflow 区块 | 主会话加载协调角色，按状态委派原生执行角色 |
| workflow.yaml | 仅在项目缺少时创建默认配置，已有配置由框架配置规则校验 |
| .agents/requirement-workflow/installation.json | 安装清单及验证状态，不作为需求状态 |

协调角色留在主会话，使用项目入口；无需再派发协调子 Agent，也不新增阶段执行 Skill。初始化 Skill 是维护入口，不参与需求阶段调度；安装后的维护可直接读取框架副本中的本 Skill。

符号链接使原始 Skill 的模板及相对引用仍然有效。确认宿主支持目录符号链接；无法创建/读取时停止并说明，不创建不完整的 Skill 副本。同名已有 Skill（包括坏链接）不接管。可读的用户级同名 Skill 不修改；派发消息与角色绑定使用明确的项目内路径，避免误载全局同名项。

## 安装与重复执行

1. 解析目标真实根目录。检查全部待写祖先路径和终点：目录链接不可逃出目标项目；AGENTS.md、配置和已存在控制文件的链接也须核对。框架副本不允许指回源框架。目标路径不得包含未处理的占位符。
2. 在任何写入前检查所有目标：无 installation.json 时，框架目录、三个角色目标、三个 Skill 入口及同名原生角色声明须不存在；AGENTS.md 不得已有同名区块。解析现有项目角色 TOML 的 name 与旧 .codex/config.toml 中的 agents 声明，防止同名注册。AGENTS.override.md 若会遮蔽入口，报告冲突；不修改该文件。保留其他角色、Skill、配置和 AGENTS.md 原文。TOML/YAML 无法解析或配置明确禁用子 Agent 时阻塞，先说明问题。
3. 用宿主临时目录准备快照和已填模板。原生名称按上表，模板的 role_file、skill_file 替换为框架内相对路径，例如 agents/product-agent.md 和 skills/requirement-analysis/SKILL.md。不填写 model、权限或 MCP 配置；角色约束是行为指令，不是宿主沙箱隔离。
4. 创建框架快照、角色文件和相对 Skill 链接；按项目入口模板追加完整标记区块，保留原文。workflow.yaml 不存在才创建；已有文件保持原字节并按 [配置规则](../../../workflow/config.md) 检查。不创建 agent-features 业务需求，不复制源框架的 docs/、agent-features/ 或宿主配置。
5. 校验后保存 installation.json：schema_version=1、host=codex、framework_path（项目相对路径）、角色→Skill 映射、owned_files（项目相对路径及实际 sha256）、owned_links（项目相对路径和相对目标）、entry_block_sha256、created_workflow_config、file_installation=passed、native_role_invocation=pending、end_to_end=pending。清单不自包含摘要，也不把整个既有 AGENTS.md 当作拥有文件；已有 workflow.yaml 不纳入 owned_files。另记每个原生角色探测结果，仅在真实取得时更新。
6. 再次初始化先核对清单、全部已拥有文件/链接和入口区块，再比较当前源文件。完全相同则不重写任何已安装文件；源变化或本地改动列具体差异并停止，保留旧安装和需求。当前版本不自动升级或卸载；不要自行清空目录。写入失败时说明实际已写路径和未完成项，清单不得标为 passed；修复后先核对残留，不覆盖恢复。

## 宿主生效检查

安装后从目标项目启动新会话或使用宿主确实支持的重载。原生目录存在、普通子 Agent 读过 TOML、TOML 能解析均不能证明注册生效。

通过宿主实际提供的角色选择机制，分别调用 requirement_product、requirement_development、requirement_testing，消息标明 initialization_probe=true：只核对角色定义、专属 Skill 及其必需模板可读，报告实际路径、原生名称与自身职责，不创建任务/业务产物。探测分支由原生模板定义，不改变正常业务必须持有 task.yaml 的要求。保存真实宿主任务 ID、结果及各项核对事实；无 ID 就明确未取得。

宿主工具不支持选择自定义角色时，记录 host_role_selection_unavailable；无法新开会话时记录 fresh_session_unavailable，保持 pending，不把手工读取角色作为替代成功证据。若可查询角色列表，记录实际发现结果；不可查询则依赖明确选定角色的真实调用及响应，不编造列表。某个角色失败时单独记录 failed，不将其他角色或整个初始化标成全部通过。

最后核对主会话从 AGENTS.md 找到协调入口和角色映射。只有入口及三个原生角色/Skill 全部在真实宿主验证后，才能报告初始化生效；完整需求闭环仍单独验证。
