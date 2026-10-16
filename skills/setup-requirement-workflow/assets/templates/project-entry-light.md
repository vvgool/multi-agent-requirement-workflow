<!-- requirement-workflow:begin -->
## 需求协作入口

发起、继续或优化命名需求时，先读取本项目 workflow.lock.yaml；框架位于 `.agents/requirement-workflow-cache/<package.sha256>/`，核实包身份后读取其中 agents/coordinator-agent.md，以本项目为工作空间按状态派发。单纯问答/审查/维护不自动创建需求。

有 `.agents/requirement-workflow.pending.json` 先按原安装计划恢复。缺缓存时按锁定来源取得同一包并使用其 setup-requirement-workflow Skill 补本机环境；manual来源需用户提供同摘要包，不能把分发标识当下载地址，不用全局最新版本替代。缺能力则具体报告。

按框架 workflow/host-adapters.md 的当前宿主映射真实选择三个原生角色，传入 task、包身份和当机框架路径。只读取角色文件不等于原生调用；初始化文件通过、当前宿主激活、完整业务闭环分别记录。业务阶段前先检查活动任务；未确认旧任务结束不换宿主或升级。Issue默认关闭，启用时仅由协调层按授权处理。
<!-- requirement-workflow:end -->
