# OpenCode 宿主入口

项目初始化先读 [通用setup Skill](../../skills/setup-requirement-workflow/SKILL.md)，按 [包规则](../package.md) 取得锁定版本，再执行 [OpenCode适配](../../skills/setup-requirement-workflow/references/opencode-adapter.md)。按通用选择规则为目标宿主生成薄角色，共用主会话入口；本说明负责本宿主的三个薄原生角色；完整框架放项目忽略缓存，不提交整包。

运行时主会话从项目入口找到版本锁和缓存，加载协调角色；按 [适配契约](../host-adapters.md) 的当前宿主映射调用产品/开发/测试。每次派发带真实task、包身份、framework_root和授权，阶段角色明确读取共享Skill及模板。没有原生角色选择能力时记录host_role_selection_unavailable，不以通用Agent模拟通过。

文件安装、当前宿主新会话激活和完整业务闭环分别报告。若已有旧快照或无锁的手动加载历史，先按 [兼容规则](../package.md) 核对，不直接迁移或清除旧活动任务。跨宿主只能在原任务已确认结束后新建run，新宿主须另行验证激活，旧宿主ID保持历史事实。

当前提供上述文件适配和执行契约，真实宿主探测以本项目回执为准；不根据其他宿主或历史原型成功宣称本机生效。独立框架开发目录中的 docs/verification/README.md 索引已有证据，不作为共享包运行依赖。
