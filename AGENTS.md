# 需求协作 Agent 框架

本目录包含一套由多个角色 Agent 协作完成需求的基础框架。

用户明确要求安装、初始化、补本机环境或升级时，读取 [通用初始化Skill](skills/setup-requirement-workflow/SKILL.md)，识别当前宿主并保留项目规则。新项目按版本锁和本地忽略缓存安装，不复制整包为业务仓库受管文件。

## 角色

接到用户发起、继续或优化需求的协调任务时，先读取 [协调 Agent](agents/coordinator-agent.md)，并按其条件指针读取共享规则和当前宿主说明。接到带 task.yaml 的产品派发时，先读取 [产品 Agent](agents/product-agent.md)，只处理该任务。单纯维护本框架文件不自动创建业务产品任务。

用户明确说“新需求”即进入协调接单，即使尚未命名；后续说明、补充和优化沿用该需求上下文，直到用户明确取消、切换需求或要求退出流程。修改对象是本框架的规则、Skill 或模板，也不能据此转为直接维护。未命名时先收集目标并确定可区分名称，再创建状态和产品任务；协调层不直接修改目标文件。只有未进入需求流程的独立维护，或用户明确要求退出流程后直接修改，才适用上文的维护例外。

- coordinator-agent：协调需求阶段流转。
- product-agent：澄清需求，输出需求文档和验收标准。
- development-agent：设计和实现代码。
- testing-agent：执行测试，输出测试报告并反馈缺陷。

阶段执行由 [产品](agents/product-agent.md)、[开发](agents/development-agent.md)、[测试](agents/testing-agent.md) 负责；带 task.yaml 的派发先读对应角色文件。协调层仅负责路由、交接完整性和状态更新，阶段内容检查由执行角色负责。角色文件存在不代表真实调用已验证。

## 共同规则

工作空间根目录由启动协调 Agent 时明确指定；配置从该根目录的 workflow.yaml 读取。workspace.features_dir 默认是 agent-features，相对于工作空间根目录解析；下文 <features_dir> 指解析后的需求根目录。框架安装目录不作为默认工作空间。

1. 需求目录以需求名称命名，内部自动生成唯一且改名不变的 feature_id，用户无需提供标识。
2. 开始工作前先读取 <features_dir>/<需求名称>/status.yaml，核对内部标识和当前修订版本。
3. 每个角色只处理自己负责的阶段。
4. 每次完成工作都要更新状态和产物索引。
5. 没有完成证据时，不得把阶段标记为完成。
6. 暂不自动执行生产发布。
7. 同名需求先判断是原需求续改还是独立需求，不得直接覆盖；范围或验收标准变更使用新修订版，保留历史产物及证据。
8. 每个修订版的需求和验收标准须经用户明确确认后才能进入开发，旧审批不自动适用于新版本。
9. 新需求及新修订的正式成果、执行记录与人工入口按 [成果目录规范](workflow/output-layout.md) 管理；旧版按原索引读取，不迁移审批。
10. 协调 Agent 统一更新阶段和产物索引，其他角色完成时提交产物及证据，由协调 Agent 核对交接完整性后推进状态。

11. 新锁定安装按 [包与版本规则](workflow/package.md) 校验项目绑定和任务身份；派发使用 [宿主适配](workflow/host-adapters.md)。旧快照/审批/任务按兼容路径保留，不自动迁移。

状态流转：draft -> requirement_review -> development -> testing -> completed。测试失败时返回 development。
<!-- requirement-workflow:begin -->
## 需求协作入口

发起、继续或优化命名需求时，以本项目为工作空间，先读 workflow.lock.yaml。缓存位于 `.agents/requirement-workflow-cache/<package.sha256>/`，不随 Git 提交；首次进入或上下文丢失时按包规则完整核验，同会话后续按变化快照复用。单纯问答、审查和维护不创建需求；只读或 initialization_probe=true 时不下载、修复或写入，缺环境只报告阻塞。

用户明确说“新需求”即进入协调接单，未命名时先收集目标并确定名称，再创建状态和产品任务。后续补充沿用原需求上下文，直到用户明确取消、切换需求或要求退出流程；即使修改对象是框架规则、Skill 或模板，也由协调层按阶段派发。上述维护例外仅用于未进入需求流程的独立请求，或用户明确退出流程后要求直接维护；协调层不以维护为由代做需求实现。

1. 锁须可解析且无重复键，固定包含 schema_version=1、package 身份和 source；包名为 multi-agent-requirement-workflow、protocol_version=1，sha256 为64位小写十六进制，git revision 必须是完整提交 SHA。已有 `.agents/requirement-workflow.pending.json` 时先恢复原计划；锁缺失、格式不合法或计划身份不一致即停止，不重新规划。
2. 缓存必须是锁定摘要对应的完整普通文件包；按根文件及 agents/、skills/、workflow/、templates/ 的相对 POSIX 路径和原字节 SHA256 排序计算紧凑 JSON 摘要，拒绝链接和额外文件。内容、来源提交或包身份不符时返回 framework_integrity_mismatch，不自动覆盖；缺缓存时按锁定提交恢复，只读获取并核验实际 HEAD，不跟随分支、不执行下载脚本。
3. 身份核验后才读取 setup Skill，以 restore_only=true 补缓存或回执；不自动升级、扩展宿主、覆盖用户文件、改变项目配置、审批、业务文稿或 active_run。具体清单、摘要算法和失败语义按 [包规则](workflow/package.md) 与 [启动恢复](workflow/bootstrap.md) 执行。
4. 按缓存 host-adapters 映射选择当前宿主的三个原生角色，并分别记录文件安装、宿主激活和完整业务闭环；不能用通用 Agent 或其他宿主结论替代原生证据。
5. 业务阶段前核对当前需求 status、task 和 active_run；unknown 或无法查询的调用先恢复核实，不重复派发。Issue 默认关闭，启用时仅由协调层按授权处理。

<!-- requirement-workflow:end -->
