<!-- requirement-workflow:begin -->
## 需求协作入口

发起、继续或优化命名需求时，以本项目为工作空间，先读 workflow.lock.yaml。缓存位于 `.agents/requirement-workflow-cache/<package.sha256>/`，不随 Git 提交；首次进入或上下文丢失时按包规则完整核验，同会话后续按变化快照复用。单纯问答、审查和维护不创建需求；只读或 initialization_probe=true 时不下载、修复或写入，缺环境只报告阻塞。

用户明确说“新需求”即进入协调接单，未命名时先收集目标并确定名称，再创建状态和产品任务。后续补充沿用原需求上下文，直到用户明确取消、切换需求或要求退出流程；即使修改对象是框架规则、Skill 或模板，也由协调层按阶段派发。上述维护例外仅用于未进入需求流程的独立请求，或用户明确退出流程后要求直接维护；协调层不以维护为由代做需求实现。

明确只修 Bug 时按锁定包 workflow/bugfix.md 的独立入口作为上述默认产品路由的例外：原生 Bug 先只读整理边界，由协调展示并取得本版明确确认后再修复，交原生测试独立验收；开发后接续和开发中补充也按该契约交接。缺陷不自动授权扩大范围，未知调用先恢复，保留共享尝试上限。

1. 锁须可解析且无重复键，固定包含 schema_version=1、package 身份和 source；包名为 multi-agent-requirement-workflow、protocol_version为受支持的1或2且与取得包完全一致（不得跨协议续写任务），sha256 为64位小写十六进制，git revision 必须是完整提交 SHA。已有 `.agents/requirement-workflow.pending.json` 时先恢复原计划；锁缺失、格式不合法或计划身份不一致即停止，不重新规划。
2. 缓存必须是锁定摘要对应的完整普通文件包；按根文件及 agents/、skills/、workflow/、templates/ 的相对 POSIX 路径和原字节 SHA256 排序计算紧凑 JSON 摘要，拒绝链接和额外文件。内容、来源提交或包身份不符时返回 framework_integrity_mismatch，不自动覆盖；缺缓存时按锁定提交恢复，只读获取并核验实际 HEAD，不跟随分支、不执行下载脚本。
3. 身份核验后才读取 setup Skill，以 restore_only=true 补缓存或回执；不自动升级、扩展宿主、覆盖用户文件、改变项目配置、审批、业务文稿或 active_run。以下路径均相对于已核验的锁定缓存根 `.agents/requirement-workflow-cache/<package.sha256>/`（以本项目根为起点，摘要取本项目 `workflow.lock.yaml`，不使用原机器绝对路径）：具体清单、摘要算法和失败语义读取 `workflow/package.md` 与 `workflow/bootstrap.md`。不得将这些路径当作项目根下的文件；克隆缺缓存时仍按上述固定来源恢复并核验，不复制规则到项目根、不扩大运行包。
4. 按缓存 host-adapters 映射选择当前宿主的四个原生角色，并分别记录文件安装、宿主激活和完整业务闭环；不能用通用 Agent 或其他宿主结论替代原生证据。
5. 业务阶段前核对当前需求 status、task 和 active_run；unknown 或无法查询的调用先恢复核实，不重复派发。Issue 默认关闭，启用时仅由协调层按授权处理。

<!-- requirement-workflow:end -->
