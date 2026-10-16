# Claude Code 宿主接入边界

当前提供通用角色读取入口，专用子 Agent 注册及真实调用尚未适配、未验证。框架中的 agents/*.md 不自动等于 Claude Code 已注册的子 Agent。

用户可在会话中要求读取框架的 agents/coordinator-agent.md，明确工作空间及需求名称。协调 Agent 随后检查当前实际工具和项目规则：具备原生子 Agent 委派能力时，按 [handoff.md](../handoff.md) 传入产品角色与 task.yaml 的绝对路径，保存真实任务标识并等待结果；能力缺失时报告 host_delegation_unavailable。

不要求用户运行框架 CLI。专用注册格式和工具名称应在实际 Claude Code 环境核实后再补充；本文件不宣称自动调用已可用。工作空间状态、产物和审批规则与其他宿主一致，切换宿主也须先核对旧活动任务。
