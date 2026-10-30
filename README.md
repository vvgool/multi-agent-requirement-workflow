# Multi-Agent Requirement Workflow

一次性、局部低风险且目标明确的小修由当前会话直接定位、最小修复、相关回归并简短返回，无需先建文档、清单、计划或宿主原生任务，也不默认另派角色、全量测试或无意义新增测试。原因未知先同一角色定位；需要跨会话恢复、交接或多步持久跟踪时才维护一个协调入口。复杂需求按职责维护需求、技术设计、实施计划及验收文档。不提供CLI、后台调度服务或新的模式开关。独立一次性明确局部低风险且非旧任务续接时，直接遵循已载项目入口的授权/风险/unknown规则，不为小修读取锁、缓存、协调规则或完整框架包；需要框架协作/角色/恢复/安装才核验，旧任务始终原锁原包。

## 使用

在目标项目中要求Agent从 https://github.com/vvgool/multi-agent-requirement-workflow 获取框架，读取 `skills/setup-requirement-workflow/SKILL.md`，为当前宿主初始化，保留项目已有规则。首次安装固定实际完整提交和包摘要；已有锁按原锁恢复，不自动升级。

安装后直接说明目标，例如“调整签到奖励”；需要持久跟踪时，当前会话维护 `agent-features/签到奖励/task.md`。文档先给人看的摘要、范围和验收，再记录任务和真实验证：

```markdown
# 签到奖励

| 项目     | 内容       |
| -------- | ---------- |
| 当前状态 | 进行中     |
| 最近更新 | 2026-10-25 |

## 目标与范围

每天首次签到奖励10积分，北京时间零点刷新。

### 验收标准

- [ ] 首次签到获得10积分。
- [ ] 同日重复签到不重复发放。
- [ ] 跨北京时间零点后可再次领取。

## 任务

- [ ] 调整奖励规则并验证首次、重复及跨日行为。

## 验证记录

| 检查                 | 状态   | 证据或说明   |
| -------------------- | ------ | ------------ |
| 首次、重复及跨日行为 | 未执行 | 待实现后验证 |
```

这是唯一协调和进度入口，并非只能有一个文件。补充、修复、重试、普通继续与完成后续改都更新对应文档与入口状态；不生成v2/v3目录、重复需求稿或平行进度索引。需要保留重要旧结论时在文档简述或引用Git历史。现有历史目录保留，旧锁旧任务继续原包，不批量迁移。

复杂需求在实施前形成或引用独立需求和技术设计，按依赖拆分实施单元；验收时维护实际结果。典型目录如下，按实际需要创建，已有项目文档直接引用：

```text
agent-features/飞书群机器人消息自动处理/
├── task.md                  # 当前状态、任务勾选、依赖、阻塞和链接
├── requirements.md          # 用户场景、业务规则和验收标准
├── technical-design.md      # 模块、接口、数据、授权和恢复设计
├── implementation-plan.md   # 实施单元、依赖、文件归属和检查方法
└── verification.md          # 验收结果和证据
```

复杂需求的 requirements.md 承载PRD：先分析问题、角色旅程和产品方案，再明确功能规则及验收；技术设计按职责与数据归属拆模块，实施计划按可验证交付拆任务。实施前检查需求覆盖、契约一致及模板适用内容，已有格式可映射使用，小修路径保持。

完整规则见 [文档分工](workflow/documents.md#按复杂度选择文档)。一个事项可包含多个实施任务，确需委派时才建立对应原生任务。详细规则、设计和证据各自维护，task.md 只汇总进度及链接；一般事项仍可只用 task.md，小修直接完成。

实际产稿时按 [格式规范](workflow/documents.md#人读文档格式) 组织结论、图示和证据：流程用流程图，模块关系用架构图，调用交互用时序图，接口/配置/命令用带语言标识的代码块。小修无需为套模板而写文档。

## 执行路径与交付门槛

协调Agent按 [路由](workflow/routing.md) 核实工作性质、业务确定性、职责依赖、状态副作用、风险及交付验证：明确局部小修直接完成，一般需求补局部决策，复杂需求主动形成PRD、模块分析及实施计划，Bug先诊断再决定修复深度。不按行数打分，不让用户负责提醒拆分。模块分析可以得出复用现有边界的结论。

复杂需求必须满足 [实施与完成门槛](workflow/execution-contract.md#实施与完成门槛)：实施前独立审查、分批交付及最终独立验收；产品拆功能、开发拆模块、协调组织交付和集成。复杂语义变化时补 [领域建模](skills/requirement-analysis/references/domain-modeling.md)，架构影响型Bug或重复失败时补 [架构审查](skills/feature-development/references/architecture-review.md)。技术审查复用独立开发专长，测试检查可验收性及实际业务，角色不是固定阶段链。可自动验证的业务代码默认 [测试先行](workflow/test-first.md)，原因不清的Bug按 [系统化诊断](skills/bug-fixing/references/systematic-debugging.md)，完成前按 [证据门槛](skills/acceptance-testing/references/completion-gate.md)，例外说明原因与替代验证，TDD不替代整体验收。

## 协作边界

当前会话能完成就直接处理。信息不足才澄清，需要其他专长才委派原生产品/开发/测试/Bug角色，不强制产品→开发→测试。需要文档时按职责维护正文，task.md 汇总当前进度与必要链接；需要委派时宿主原生任务记录派发及结束事实，不另建status/task/host/result YAML、调用授权版本、delivery、逐轮快照、全项目文件哈希或重复事件索引。

范围或验收有分歧先确认；涉及付款、权限、数据删除或大范围共享逻辑变更，执行前确认具体范围，并由另一角色独立验证。已确认范围继续有效，创建文档、切换角色或实施单元不重复审批；通用 Skill 按项目规则补充方法。普通已知小修无需统一边界评审。跨角色和中断恢复只交接目标、改动、已验结果、未决项及原生任务引用。确需避免验错版本时才保存相关文件版本或摘要，不扫描无关项目。外部写结果未知先查询原调用，查不清阻塞，不重复发送。

[协调](agents/coordinator-agent.md)负责必要路由；[产品](agents/product-agent.md)澄清规则；[开发](agents/development-agent.md)实现和自验；[Bug](agents/bug-agent.md)诊断修复；[测试](agents/testing-agent.md)按需独立验证。角色是可用专长，不是必经关卡。

## 安装与版本

本版本支持复杂需求按需求、技术设计、实施计划和验收分工，task.md 作为唯一协调与进度入口；同编号任务关联实施计划，独立验收有明确待办和完成条件。一次性局部低风险小修仍由当前会话直接完成。

本次发布版本为 **0.7.1，协议3**，在0.7.0基础上补齐代码库证据优先、单一workflow控制、实施单元契约、完成证据、失败熔断、交接终态及worktree身份边界。发布事实以 [GitHub Release](https://github.com/vvgool/multi-agent-requirement-workflow/releases) 的标签、提交与包摘要为准；本项目安装以workflow.lock.yaml为准，其他消费者须明确升级。历史候选的Codex/OpenCode验收仍绑定各自旧包摘要；不将旧候选结果冒称为0.7.1新发布字节的宿主验收结果。各候选和正式包的实际范围见 [验证摘要](docs/verification/README.md)。Claude Code真实运行、自动崩溃恢复和真实外部平台须单列；保留旧包和历史，旧任务继续使用原锁定包。

Codex、Claude Code、OpenCode共享规则，以各宿主原生角色薄文件适配；文件安装、真实角色激活和业务闭环分别报告。不能用一个宿主的结果替代另一个，也不能用模板存在证明原生调用。详情见 [包规则](workflow/package.md)、[安装Skill](skills/setup-requirement-workflow/SKILL.md)、[宿主适配](workflow/host-adapters.md)。

项目提交workflow.yaml、workflow.lock.yaml、AGENTS入口、选定宿主的四个薄角色及精确.gitignore区块；Claude按需增加CLAUDE桥接。完整包缓存在 `.agents/requirement-workflow-cache/<sha256>/`，安装回执及pending留本机。安装完整性校验仍保留，它不要求逐个业务任务建立机器账本。

可选外部文档/Issue按项目已有连接能力和用户具体授权使用，不主动发消息、评论或发布。配置默认外部写关闭，见 [配置](workflow/config.md) 与 [Issue](workflow/issue-tracking.md)。

## 源码验证

以下为源码维护检查，使用现有 Python 及 PyYAML；不作为业务运行依赖。当前候选的验证结论与宿主限制见 [验证摘要](docs/verification/README.md)，历史测试通过不自动覆盖当前候选。

- `python3 -B -m unittest discover -s tests -p 'test_codex_registry.py'`：既有配置合并回归。
- `python3 -B scripts/verify-host-adapters.py --source-root . --scratch /已授权的空目录`：三宿主真实模板/正文与配置保留检查，不是原生激活。
- `python3 -B scripts/verify-rule-loading.py --source-root .`：协议3规则、文档读取入口和模板一致性静态检查，不代表模型实际执行。
- 体积比较可追加 `--baseline-root /完整旧包目录`；只报告变化。精简实验需强制缩小时另加 `--require-smaller`，不作为普通改动的发布门槛，不测token或耗时。

历史机器协议相关模板、实验和验证记录仅供原版本解释/维护，不是协议3入口。历史检查不证明新协议实际业务闭环。运行包含根framework.yaml、AGENTS.md、README.md、workflow.yaml、LICENSE及agents/、skills/、workflow/、templates/；scripts/tests/docs不进入业务运行包。

本项目使用 [MIT License](LICENSE)。
