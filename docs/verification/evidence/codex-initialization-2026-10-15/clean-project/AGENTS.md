# 项目规则

保留现有文字；业务代码仅放在 src/。

<!-- requirement-workflow:begin -->
## 需求协作入口

用户要求发起、继续或优化命名需求时，主会话先读 `.agents/requirement-workflow/agents/coordinator-agent.md`，以本项目为工作空间，按状态推进；单纯代码问答、审查或框架维护不自动创建需求。

协调主会话按产品/开发/测试阶段分别选择原生 requirement_product / requirement_development / requirement_testing。派发必须带当前 task.yaml 和动态解析的项目框架路径，要求读取对应角色和专属 Skill；不能只给角色名称。

初始化后须在新会话或宿主重载后验证上述原生角色调用；缺少原生角色选择能力时阻塞派发，不用通用 Agent 冒充已注册角色。审批、来源、恢复和生产发布边界按协调规则执行。
<!-- requirement-workflow:end -->
