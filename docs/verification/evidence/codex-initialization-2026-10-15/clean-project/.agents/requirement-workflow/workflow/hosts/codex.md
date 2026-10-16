# Codex 宿主入口

入口是当前 Codex 主会话。项目初始化读取 [setup-requirement-workflow](../../skills/setup-requirement-workflow/SKILL.md)，由宿主执行安装；角色 Markdown 本身不构成原生注册。原生格式依据见 [安装流程](../../skills/setup-requirement-workflow/references/codex-installation.md)。

## 已初始化项目

主会话通过项目 AGENTS.md 区块加载协调规则，产品、开发、测试映射到 `.codex/agents/` 中的 requirement_product、requirement_development、requirement_testing。三个专属 Skill 由项目 `.agents/skills/` 入口发现，角色按明确的项目内路径加载。框架副本位于 `.agents/requirement-workflow/`，迁移时跟随项目。

派发优先核对 installation.json 及真实宿主生效记录；使用当前工具实际支持的原生角色选择机制，传递本轮 task.yaml，记录真实任务 ID。不硬编码某个工具的参数名。不具备原生角色选择能力时报告 host_role_selection_unavailable，保留阶段，不回退成通用子 Agent 扮演已注册角色。

安装文件可解析只代表文件安装通过；需新会话或已证实的重载后完成真实原生角色/Skill 探测，才能报告初始化生效。父会话权限由宿主继承，产品/测试的写入约束是行为规则，不冒称独立沙箱。初始化不自动改全局配置、模型或权限。

## 未初始化时的原型加载

用户可直接说（替换路径及需求内容）：

> 加载本框架的 agents/coordinator-agent.md，作为协调 Agent，在当前宿主工作空间中处理“用户签到奖励”：首次签到奖励 10 积分，每个账号每天一次，按北京时间零点刷新，断网时提示重试、不发放。目标项目就是该工作空间。

> 加载本框架的 agents/coordinator-agent.md，继续当前宿主工作空间中的“用户签到奖励”，先核对现有状态和活动任务。

先把实际框架目录提供给宿主读取，从加载的角色文件位置确定 framework_root。按 [共享与路径定位](../portability.md) 动态解析本机路径，不在角色、模板或示例里写入作者的安装目录。

## 原型环境曾验证的调用契约

本次验证环境提供 collaboration.spawn_agent、followup_task、send_message、list_agents、wait_agent。工具名可能因宿主环境变化而不同，运行时以真实工具列表和说明为准；这些名字不是额外 CLI。

1. 协调 Agent 按阶段选定角色，核实对应角色文件存在，先保存 task.yaml、快照和 active_run。将 dispatch_status 改为 unknown，再调用真实 spawn_agent，message 指定动态解析的选定角色文件和 task 路径，要求先核对状态；尽可能仅传必要上下文。
2. 立即将返回的真实任务标识写入 host.yaml 及 active_run.host_task_id。本次工具返回 canonical task_name 路径，原样保存即可；其他环境若返回 agent_id，则保存其真实值，不要求它是 UUID。后续结果与这个标识、run_id 关联。
3. 已结束角色 Agent 可通过 followup_task 接收同一角色的一个新 run；保存实际复用的任务标识，不另造宿主标识。本轮 run_id 仍保持独立，跨角色创建独立 Agent。
4. 用宿主状态查询、返回通知和必要的等待接收完成情况；本地核查结果文件，不能只信子 Agent 的成功文字。
5. 中断恢复先核对实际宿主任务。无法查询旧 ID 或证明已结束时报告阻塞，不将另一会话的新 Agent 当成旧任务已经结束。

上述通用子 Agent 调用是手动加载原型的历史证据，不证明 `.codex/agents/` 注册已在新会话生效。协调角色已定义全阶段路由，三个执行角色 Skill 已通过隔离检查；初始化后的完整需求闭环尚未实测。按所需角色实际检查并报告 role_not_available，不伪造调用。没有子 Agent 能力的 Codex 环境报告 host_delegation_unavailable，不能退化为协调 Agent 扮演业务角色。

本地完整开发目录中的验证记录位于 docs/verification/coordinator-first-milestone.md；核心分享包不包含该运行证据，接收者应在自己的宿主中验证，不能将作者记录当作本机通过。
