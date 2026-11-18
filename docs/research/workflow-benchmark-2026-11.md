# AI 软件开发工作流调研（2026-11）

> **性质**：背景研究与可借鉴机制，不是本框架的已批准实现设计、PRD、技术方案或实施任务。下文单独标出的“本轮已确认优化方向”是用户对调研结论的方向确认，不等于已修改框架。
>
> **研究日期**：2026-11-16。外部仓库均按本次读取的 `main` 提交固定链接引用；网页文档记录其页面更新时间或发布日期。本文不建立客观“最佳排名”，只比较与当前三个问题的相关证据：未确认就实施、文档过重/难读、结果不准且慢。

## 结论摘要

用户补充的质量重点为：**执行低效、文档难审阅、设计和实施脱节、需求理解偏差**。本轮未将“验证不可信”选为主要症状，因此后续应首先围绕这四类问题取真实案例和设计评测；验证仍是基本保障，不据此推断已有验证造假。

1. **需求和设计的人工确认应成为明确的流程状态，而不是从“有审查/有下一阶段命令”推断出来。** Superpowers 在适用的 brainstorming 路径对设计文档有清楚的人工批准硬规则，但有明确小任务、用户退出问答及获准 spike 等例外；Kiro 的标准 Feature Specs 描述了阶段间 review gate，但同时提供没有阶段批准门的 Quick Spec。OpenSpec 的 artifact 依赖和“先看计划再写代码”有助于排序与可追踪，却不能单独证明工具会阻止未获人工批准的实现。GitHub Spec Kit 的 `specify → plan → tasks → implement` 是结构化交付链，也不能仅凭命令顺序宣称有人工批准门。
2. **文档质量的有效方向是“分层、模板约束、可追溯”，不是继续堆叠全文。** 需求只写可观察行为与验收场景，设计只写技术决策及取舍，计划只写可执行任务和验证；把待确认决策、审查摘要、风险条件放在前面，把方法性检查清单留在模板/规则层。模板能减少遗漏，但不能替代人判断。
3. **质量与速度需要行为评测和分段计时，而不是凭体感或静态绿灯推断。** Anthropic 的一手材料建议从简单方案开始，用自动化评测、生产监控和定期人工校准组合判断；自动化测试验证功能，人工仍需判断是否符合更广泛的系统要求。多 Agent 只有在任务确实可并行、上下文或专业性超过单 Agent 时才可能值得其额外成本。
4. **本轮已确认优化方向（仍只调研，不实施）**：需求、设计分别人工确认；需求稿确认后进入正式设计，设计稿确认后才实施；影响已确认结论的实质变更重新确认。明确的局部低风险小修仍直接处理，确认后不逐实施任务重复询问。具体状态、文件字段、宿主适配和验证实现仍是建议，未修改框架。
5. **本仓当前只能提出流程强制要求，不能承诺工具层绝对拦截。** 当前是 Markdown/原生宿主指令，没有统一执行运行时（[既有技术设计](../../agent-features/文档模板与流程可读性优化/technical-design.md)第 3、38 行；[README](../../README.md)第 3 行）。因此 STOP 规则应表述为“流程强制要求”：指令要求代理在未批准时停止，不等同于宿主一定无法写文件。若未来要做到工具层拦写，需要分别适配各宿主的计划模式、权限或 hook，并做行为验证；本轮不建议默认引入大运行时。

## 调研范围、版本和证据边界

本次聚焦五组一手来源：Superpowers、OpenSpec、GitHub Spec Kit、Kiro 官方 Specs、Anthropic 工程材料；另以 Cursor Pstack 的 Architect/Interrogate 作为精简补充。读取了官方仓库源文件或官方文档页面，没有把二手排名、社区讨论或项目宣传数字当作质量结论。

| 来源 | 本次读取版本/日期 | 与问题最相关的原文事实 |
|---|---|---|
| `obra/superpowers` | `main` @ [`22f0b463e7a5e579904dd6211a520321035526f7`](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7)，`skills/brainstorming/SKILL.md`、`skills/writing-plans/SKILL.md` | 非简单任务先澄清、列方案、写设计、取得 human partner approval；设计获批前不得构建。设计还有 builder check/独立审查，但审查与人工批准是不同角色。 |
| `Fission-AI/OpenSpec` | `main` @ [`ea635dd255f8686dcf48626bbcbe0e3fd59b6067`](https://github.com/Fission-AI/OpenSpec/tree/ea635dd255f8686dcf48626bbcbe0e3fd59b6067)，[`README.md`](https://github.com/Fission-AI/OpenSpec/blob/ea635dd255f8686dcf48626bbcbe0e3fd59b6067/README.md)、[`schemas/spec-driven/schema.yaml`](https://github.com/Fission-AI/OpenSpec/blob/ea635dd255f8686dcf48626bbcbe0e3fd59b6067/schemas/spec-driven/schema.yaml) | proposal/spec/design/tasks 形成 artifact 依赖；README 示意“review plan before code”，同时明确可随时更新 artifact、强调 fluid/iterative。schema 的 `requires` 是生成依赖，不是人工批准证明。 |
| `github/spec-kit` | `main` @ [`2ee2b1e8005905db05f5717300a469b3068b908f`](https://github.com/github/spec-kit/tree/2ee2b1e8005905db05f5717300a469b3068b908f)，[`spec-driven.md`](https://github.com/github/spec-kit/blob/2ee2b1e8005905db05f5717300a469b3068b908f/spec-driven.md) | 用命令和模板将 specification、plan、tasks、实现串起来，并强调澄清、分析、契约/测试和可读层级。页面展示阶段顺序，但本次核对的源文件不足以把顺序解释成“人工批准后才可写代码”。 |
| Kiro 官方 Specs | 官方文档页面：Feature Specs 页面更新 2026-08-04；Quick Spec 页面更新 2026-08-04；Specs 索引页面更新 2026-11-12 | 标准 Feature Specs 有 Requirements → Design → Tasks 及 review/edit loops；Quick Spec 会一次生成三类 artifact，明确“no approval gates between phases”。这是按风险/熟悉度选择深浅流程的直接例子。 |
| Anthropic Engineering | [`Building effective agents`](https://www.anthropic.com/engineering/building-effective-agents)，发布 2024-12-19；[`Demystifying evals for AI agents`](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)，发布 2026-01-09 | 建议从最简单的方案和可组合 workflow 开始；agents 以更高成本/延迟换灵活性；评测应结合确定性 grader、模型 grader、人工校准、轨迹/结果检查和实际用时等指标。 |
| Cursor Pstack（补充） | `main` @ [`bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7`](https://github.com/cursor/plugins/tree/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7)，[`architect/SKILL.md`](https://github.com/cursor/plugins/blob/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7/pstack/skills/architect/SKILL.md)、[`interrogate/SKILL.md`](https://github.com/cursor/plugins/blob/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7/pstack/skills/interrogate/SKILL.md) | Architect 的 Agree 阶段是 opt-in，默认无人工 checkpoint；Interrogate 要求对发现用真实运行证明且不自动修复。可借鉴“未验证风险单列”，不能拿其默认流程解决人工门禁，也不应照搬多模型 fanout。 |

## 候选定位与逐维对照

| 候选 | 人工确认语义 | 文档组织 | 质量/验证 | 速度与适用性 | 本仓可借鉴的边界 |
|---|---|---|---|---|---|
| Superpowers | 最明确：设计文档人工批准是构建硬门；builder check 是独立审查，不冒充人审 | Brainstorming 与 writing-plans 分工清楚，计划强调文件、接口、测试和逐步验证 | builder check、计划自检、TDD/验证规则；并非所有质量由审查自动保证 | 适合非简单任务；对机械小修可能过重 | 借鉴“批准是独立事实”和 STOP 语义；不照搬所有阶段链、每项都完整 brainstorm |
| OpenSpec | 先 review/align 的产品叙事很清楚；schema 依赖不是人审门 | proposal/spec/design/tasks 按变更目录组织，Markdown 场景可测试 | validate 与场景格式约束；AI/人都可编辑 artifact，不能只靠依赖防越界 | “fluid not rigid”，适合 brownfield；自由迭代会增加状态解释成本 | 借鉴变更单目录、能力边界、场景格式、archive 更新源规范；不把 `requires` 当批准凭证 |
| Spec Kit | 阶段命令清楚，但本次证据不足以说命令本身强制人审 | 模板、澄清标记、计划/契约/quickstart 使信息有层级 | analyze、检查清单、契约/测试导向；仍需实际评测与人验收 | 文档和命令较重；结构化程度适合复杂功能，不适合每个小修 | 借鉴 `[NEEDS CLARIFICATION]`、从 spec 派生验收与任务、把细节移出主计划；不照搬全套文档仪式 |
| Kiro | 标准 Spec 有 review gates；Quick Spec 明确无阶段批准门，证明流程可按风险切换 | requirements/design/tasks 三件套，EARS 提升可测试性 | Analyze Requirements；可编辑并 Sync Files；官方另有 correctness 能力 | Quick Spec 以预先澄清换速度，适合熟悉/低风险；高风险仍用标准流程 | 借鉴按规模/熟悉度选择流程、EARS/审阅注释；不把 Quick Spec 用于需求质量关键场景 |
| Anthropic 模式 | 不是产品批准流程；强调在 checkpoint 或 blocker 回到人处判断 | 推荐简单、可组合的 workflow，透明显示计划 | 自动 eval + 生产监控 + 用户反馈 + 轨迹人工抽查；人审校准模型 grader | 明确提醒多 Agent 有协调和 token 成本；按任务复杂度加码 | 借鉴分段成本、结果评测和人审抽样；不凭单一 benchmark 或 agent 数量推断质量 |

## 逐项可借鉴机制、代价与不建议照搬

### 1. 把“批准”建模为不同于“审查”的流程事实

**证据。** Superpowers 的 brainstorming 明确要求先写设计并取得 human partner approval，且 `<HARD-GATE>` 将“构建”定义为包含产品代码、脚手架、依赖安装和实施 skill；其 builder check 只负责发现构建者仍需知道的问题。相反，Pstack Architect 明确默认直接进入实现，只有调用方显式要求 checkpoint 才暂停。两者一起说明：是否人审不是由“有一个 review 子代理”或“分了几阶段”自动推出的。

**可借鉴（建议）。** 在本框架中显式区分：

1. 授权调研/起草；
2. 人工确认需求；
3. 人工确认设计；
4. AI 独立审查；
5. 实际允许实施。

批准记录应绑定“当前文档、当前范围、批准者和时间/版本”。实质改变需求、设计、范围或关键约束时，使受影响批准失效；普通文字润色不必重审。只批准需求可以进入设计，但不能编码；AI 审查不能签署人工批准；已批准后不应每个单元重复询问。

**代价。** 增加等待和状态管理；批准粒度过细会造成确认疲劳，过粗则无法控制越界。当前本仓没有统一运行时，所以这首先是流程约束和可观察记录，不是写入 API 的绝对拒绝。

**不照搬。** 不把 Superpowers 的完整 brainstorm/plan 链应用于所有局部低风险小修；不把 Pstack 默认无 checkpoint 当作本仓应有的批准策略；不把自动 review、内容完整、依赖齐全当人工签字。

### 2. 用 artifact 依赖和能力边界改善文档，而非增加长文档

**证据。** OpenSpec schema 中 proposal 同时是 specs 和 design 的前置，tasks 依赖 specs 与 design，apply 依赖 tasks；不是所有产物严格串行。它把 requirement 写成可观察行为与带 WHEN/GIVEN、THEN 的场景；其 README 还主张每个 change 目录包含 proposal、spec、design、tasks。Spec Kit 通过模板、clarification marker、契约、数据模型和 quickstart 分担细节；Kiro 用 EARS 让 requirement 可直接转测试，并允许标准流程或 Quick Spec。上述机制解决的是“信息如何分层和追踪”，不是“文档越多越可靠”。

**结合本仓现状（证据）。** [文档规则](../../workflow/documents.md)第 18–26 行已有来源、场景和功能/验收/任务映射要求，第 66–96 行已有先结论、短表与图示格式，不应全盘重写。当前重复和拥挤点包括：

- `skills/feature-development/assets/templates/technical-plan.md:11-13` 的方案比较与 `:39-41` 的技术取舍内容相近；
- `:47-53` 的设计自检/独立审查与设计自检摘要相邻重复；
- 模块表六列承载多种长内容，降低扫描速度；
- 需求模板缺少靠前且紧凑的“本次请确认”决策区。

**可借鉴（建议）。** 保留现有核心映射，调整为：

- 开头放“结论摘要、范围/非目标、风险条件、本次请确认（最多若干项）”；
- 正文只保留行为、场景、关键设计决策、依赖和验证入口；
- 方案比较与技术取舍合并为“决策及替代方案”，只保留会改变实施的取舍；
- 设计自检和独立审查保留一份摘要，详细检查清单留在方法文件；
- 长模块表拆成短字段或链接，图仅在确有表达价值时使用；
- 用“来源 → 需求/AC → 设计决策 → 任务 → 验证”单向链接，避免同一结论在多个章节复制。

**代价。** 需要更新模板和迁移/兼容旧文档的规则；过度压缩会隐藏背景。可先把摘要和待确认区前置，而不立即改写历史文件。

**不照搬。** 不照搬 Spec Kit 的全部 constitution、数据模型、contracts、quickstart 文件集合到每个事项；不把 OpenSpec 的目录或 Kiro 的 EARS 语法当作本仓必须安装的运行时；不把模板 checklist 当作人工确认。

### 3. 将“正确性”和“速度”作为可配对评测的结果，而非流程印象

**证据。** Anthropic 明确建议从简单方案开始，复杂度只在结果证明需要时增加；其评测材料区分 code-based、model-based、human graders，并强调读取 transcripts、检查实际 outcome、隔离环境、校准 LLM judge。对 coding agent，自动测试能验证功能，但人审仍负责更广泛系统要求。多 Agent/并行适用于独立方向可并行、上下文不足或确有专业分工的任务，同时增加协调、token、延迟和故障面。

**结合本仓现状（证据）。** `scripts/verify-rule-loading.py:1-6` 明确是静态检查，不运行模型；`tests/test_rule_loading.py:1` 明确不跑原生 Agent，现有测试多断言关键字符串/链接存在。`tests/test_manual_confirmation.py` 测的是 Issue 最终关闭确认（引用 `test_issue_lifecycle`），不是“需求/设计获批后才实施”。这不表示没有真实原生验收价值，但 `docs/verification/README.md:13,153` 已说明缺少完整成本和同条件对照；120 项源码绿不能推出业务质量或提速。

**可借鉴（建议）。** 对相同模型、题集、权限、工具和环境做配对行为评测，至少记录：

- 越界实施：未批准产物是否写了业务实现；
- 规则遵守：是否引用无来源规则、是否将 AI 审查冒充人审；
- 覆盖：独立 AC/场景是否覆盖，需求—设计—任务链是否断裂；
- 结果：缺陷、返工、验收退回、人工发现的遗漏；
- 成本：实际墙钟时间、模型调用/工具耗时、token/费用（只有能可靠取得时才报告）。

按“能力质量集”和“回归集”分别维护；对主观输出保留人工抽样校准，不用单一自动分数代替验收。

**速度拆解（建议）。** 历史长等待不能直接归因于命令慢。分别计时：模型生成、工具调用、静态校验、原生验收、角色交接、人工等待、重试/返工。当前共用路径包含 AGENTS → package/bootstrap/coordinator → execution/routing/docs → Skill → references/templates 多跳，且有重复的低风险/旧锁/单写/不重放说明。已知读取量样本为 AGENTS 3549 字符、execution 2796、routing 3215、docs 4481、产品 Skill 1293、开发 Skill 1999；历史 task 331 行/17380 字符、verification 索引 552 行/45200 字符，只能作为拥挤样本，不能据此删除或迁移历史。

**优化方向（建议）。** 分离机械完整性核验和语义必读；同一会话复用已验证且未变化的上下文；每次委派只传递任务所需上下文；按任务复杂度选择单 Agent、顺序审查或并行审查。不能为了提速去掉完整性控制，也不能把“一次读过”泛化成全量缓存已读取语义。

**不照搬。** 不默认多模型 fanout；不把并行数量当质量指标；不以一次人工成功或静态绿灯宣称整体改进；不把无运行时的流程文本写成可靠的权限拦截。

## 面向本仓三个问题的具体建议

> 下列第一节的方向已由用户在本轮确认；其余实现细节、文档字段、宿主适配和评测落地仍是建议，均未实施。

### A. 防止需求/设计未确认就实施（本轮已确认优化方向）

本轮已确认的流程方向是：需求稿先人工确认，确认后进入正式设计；设计稿再人工确认，确认后才实施。影响已确认结论的实质变更重新确认；明确的局部低风险小修继续直接处理；确认后不对每个实施任务重复询问。

作为后续实现建议，可将流程输出标注为以下状态，而不是仅依赖文件存在或命令阶段：

```text
drafted → needs-human-requirements-approval
        → requirements-approved
        → needs-human-design-approval
        → design-approved
        → ai-reviewed
        → implementation-allowed
```

后续实现建议：

- 未批准的需求/设计产物不得写业务实现；允许调研、起草、只读诊断和明确标注的 spike；
- 需求批准不能自动批准设计；设计批准也不等于发布/外部写入授权；
- AI 独立审查只报告问题，不代签人审；
- 批准绑定当前文档、范围和关键决策；实质变更使相关批准失效；普通文字修改不重审；
- 小修保留当前直接路径，但只能用于目标明确、既有契约内、无新业务决策/跨服务契约的变更；
- 恢复任务不能把旧批准外推给新方案；已批准后不对每个单元重复询问。

这些具体状态和门禁字段仍不是本轮批准的实现设计。`workflow/execution-contract.md:17` 已明确现行政策“不增加统一人工阶段审批”，`:21-25` 的就绪条件是内容/Agent 审查，`:43` 允许确认范围后持续推进；`skills/feature-development/assets/templates/technical-plan.md:49` 和 `skills/feature-development/references/design-and-decomposition.md:35` 也分别说明审查不新增统一人工批准、已有授权内可继续实施。`workflow.yaml:9-10` 的 `approval.channel: coordinator` 只说明渠道，不是两道人工门。因此本轮确认的是优化方向，后续仍需另行设计如何在现行政策基础上落地，不能把框架现状误写成已经具备人工门。

### B. 减少文档重复并提高可读性

建议先做低风险模板实验，不改历史事项：

1. 在需求/设计文档最前面增加紧凑“本次请确认”区，列出决策、影响范围和未决风险；
2. 合并 technical plan 的方案比较/技术取舍，保留替代方案为何不选；
3. 将“自检结论”和“独立审查摘要”合并为一段，详细 checklist 只放方法引用；
4. 将六列模块表拆成“模块/接口/依赖/验证”短表，长解释移入链接段落；
5. 保留已有来源、场景和 F-AC-T 映射，使用链接而不是复制全文；
6. 图只服务于跨模块关系、状态机或时序，不能为了格式完整而添加。

### C. 提高准确性并查清慢在哪里

建议建立小型、可重复的配对行为集，而不是先改流程再凭感觉判断：

- 用同一批真实失败/边界需求，比较现行路径与候选路径；
- 设独立的“需求确认遗漏”“设计越界”“来源/状态误判”“实现质量”“返工”指标；
- 记录每次是否在批准前写业务实现，以及是否把 AI 审查当人审；
- 对同一任务运行多次并读取失败轨迹，区分模型随机性、规则误读、工具/宿主限制和任务歧义；
- 将墙钟时间按模型、工具、校验、交接、人工等待、返工分段；token/费用只有数据可取得且口径一致时才公布；
- 先用小题集验证信号，再决定是否扩大或引入并行/多 Agent；不宣称百分比改善，直到有同条件基线。

## 三层约束模型：指令、评测、工具

当前本仓必须明确区分三种强度：

1. **指令约束**：Markdown/Skill/AGENTS 中的 STOP、状态和交接规则。它能约束遵循指令的 Agent 行为，但不是宿主层不可绕过的文件写保护。
2. **行为评测**：在真实或隔离宿主中运行配对任务，观察是否越界、是否正确引用来源、是否覆盖 AC、结果和成本。这能验证“实际行为”，但不是事前拦截。
3. **工具强制**：宿主计划模式、权限系统、hook 或统一执行运行时在写入前拒绝不满足状态的操作。这才接近工具层拦截，但需要各宿主单独适配、测试和维护。

因此拟议 STOP 规则当前只能称为**流程强制要求**，不能称为**工具层绝对阻止**。未来若需要第三层，应先列出宿主矩阵、权限/hook 契约、失败安全行为和回归样例；不建议本轮为此引入大运行时，也不应以未验证的宿主行为对外承诺。

## 不确定与未测事项

- 本次没有对 Superpowers、OpenSpec、Spec Kit、Kiro 或 Pstack 做同题集、同模型、同权限的端到端基准，因此没有质量/速度排名，也没有百分比结论。
- Kiro 是官方在线产品文档，不是本仓可固定提交的开源实现；“standard review gates”描述了产品流程，但本次没有验证所有宿主界面在每种模式下是否都能阻止写入。
- Spec Kit 页面展示阶段命令和模板约束；本次没有把命令顺序解释为强制人工批准，也没有从未读取的宿主实现推导拦截能力。
- OpenSpec `requires` 验证的是 artifact 生成依赖；本次没有把它当作用户签字或写入权限控制。
- 主会话已运行 `python3 -B scripts/verify-rule-loading.py --source-root .` 并成功：版本为 `0.7.4/protocol3`，检查到 17 个入口、201 个规则链接，`selected_rule_utf8_bytes.after=51902`；104 个缓存文件摘要及来源字节匹配。该结果只证明代理体积/静态一致性，不是实际必读字节、实际 token、耗时或行为通过；本次未运行全量业务/原生行为测试。
- 主会话另运行 `python3 -B -m unittest discover -s tests -p test_rule_loading.py`，18 项通过。它们仍是源码规则回归，不是人工门禁行为评测。
- 本仓现有静态验证不运行原生 Agent；真实原生验收仍有价值，但当前证据不足以量化“越界实施率、返工率、质量或速度”。
- 历史长等待未被拆分为模型、工具、校验、交接、人工等待和返工；不能仅由文档读取字符数推断根因。
- Pstack Interrogate 要求运行证明很有价值，但本次没有对本仓潜在风险逐项运行；未运行的潜在风险应继续标为未验证，不能冒充确诊。
- 本轮已确认“需求、设计分别人工确认后再实施”的优化方向，以及小修直通、实质变更重确认、确认后不逐任务重复询问；状态字段、批准失效判定、模板改造、配对评测和未来工具适配仍是建议。本次没有修改框架政策、模板、测试或宿主运行时。

## 来源链接（固定或官方页面）

- [Superpowers brainstorming（固定提交）](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/brainstorming/SKILL.md)
- [Superpowers writing-plans（固定提交）](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/writing-plans/SKILL.md)
- [OpenSpec README（固定提交）](https://github.com/Fission-AI/OpenSpec/blob/ea635dd255f8686dcf48626bbcbe0e3fd59b6067/README.md)
- [OpenSpec spec-driven schema（固定提交）](https://github.com/Fission-AI/OpenSpec/blob/ea635dd255f8686dcf48626bbcbe0e3fd59b6067/schemas/spec-driven/schema.yaml)
- [GitHub Spec Kit spec-driven（固定提交）](https://github.com/github/spec-kit/blob/2ee2b1e8005905db05f5717300a469b3068b908f/spec-driven.md)
- [Kiro Feature Specs](https://kiro.dev/docs/specs/feature-specs/)
- [Kiro Quick Spec](https://kiro.dev/docs/specs/quick-spec/)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Cursor Pstack Architect（固定提交）](https://github.com/cursor/plugins/blob/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7/pstack/skills/architect/SKILL.md)
- [Cursor Pstack Interrogate（固定提交）](https://github.com/cursor/plugins/blob/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7/pstack/skills/interrogate/SKILL.md)


## 2026-11-18 增量研究：下一步优先借鉴什么

本节核对当前已提交源码 `e0be699` 与外部一手资料；只提出优化建议，不改变已批准验收、四路径144条、预算或发布边界。上文2026-11-16关于“尚未实施”的描述保留为当时事实：当前源码已包含两次人工确认、轻量模板、受影响范围复验、最小交接、独立验收和固定核包命令，本轮不重复推荐这些已实现机制。效果仍需实际验证。

### 一手来源与当前版本

2026-11-18通过官方原文和Git远端HEAD核对：

- Superpowers仍为 [`22f0b463`](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7)。[任务执行](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/subagent-driven-development/SKILL.md)强调为独立任务构造专用上下文；[任务审查模板](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/subagent-driven-development/task-reviewer-prompt.md)由一个审查者分别判断规格符合与代码质量，按具体风险扩查、按具体疑点补测。它并非必须设两个审查者。
- Spec Kit为 [`59d61c59`](https://github.com/github/spec-kit/tree/59d61c59630c3bd5a294f4c23e43a60d8ab98d02)。[`analyze`](https://github.com/github/spec-kit/blob/59d61c59630c3bd5a294f4c23e43a60d8ab98d02/templates/commands/analyze.md)只读分析spec/plan/tasks的重复、歧义、冲突和覆盖，先构造内部需求与任务映射，输出问题位置与严重程度。
- OpenSpec为 [`f085c850`](https://github.com/Fission-AI/OpenSpec/tree/f085c850f9440f497ccc76ecbc2859c09e0e0ac7)。[概念文档](https://github.com/Fission-AI/OpenSpec/blob/f085c850f9440f497ccc76ecbc2859c09e0e0ac7/docs/concepts.md)区分当前行为规范与提议变更，用差量表达既有系统的行为变化，规范承载可观察行为，设计与任务承载实现细节。
- Anthropic的[Agent评测文章](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)发布于2026-01-09；本次页面已从engineering路径重定向到research路径。文章区分能力评测与回归，建议用已知正确的参考解校验题目与判分，并根据最终环境结果及必要轨迹判断。它是评测方法资料，不是本仓已取得收益的证据。

### 优先级与具体落点

| 顺序 | 当前不足及已有基础 | 借鉴后的最小建议 | 成本与限制 |
| --- | --- | --- | --- |
| 1：先让验收本身可靠、可收口 | 题集已有公开业务和评分规则，但当前验收反复遇到材料歧义、计时/装配错误；现有源码测试不证明整套题目和判分能正确运行。 | 借鉴参考解校准：正式模型运行前，用已知正确实现及已知错误样例先跑公开判据、计时和终态收集。新改动先跑受影响的小回归集，再进入完整对照；另维护探索新能力的评测，避免每轮调试都背负完整比较。 | 需维护少量夹具和判据；参考解只证明验收可用，不证明Agent能完成。现有144方案继续有效；若调整发布门槛或运行层次，必须先明确变更并确认，不能事后缩减。 |
| 2：把“符合需求”审查得更具体 | `workflow/documents.md`已有F/AC→设计→任务→验证规则，`verify-rule-loading.py`主要验证规则/链接存在；两者不能单独发现某事项漏了AC、擅加范围或前后约束矛盾。 | 借鉴Spec Kit的只读诊断：复用原事项文档，集中返回“遗漏、额外、误解、冲突”及位置；适合确定性检测的编号、引用和占位符可做可选离线检查，语义仍由审查者判断。先查需求符合，再判断工程质量，同一适任审查者可以完成。 | 不新建第二份覆盖账本，不强制所有任务运行新命令，不让关键词匹配宣布语义通过。 |
| 3：让当前结论比历史更容易读取 | `workflow/revisions.md`和`documents.md`已经要求一个当前入口；本事项task与verification仍持续堆积历史，恢复者需要辨认大量旧包、旧失败和旧结论。 | 借鉴OpenSpec的当前规范/变更差量区分：原文首屏只保留当前有效范围、这次变化、阻塞和下一步，历史按原区块保留并链接；续改展示受影响规则的变化，不重复复制全套背景和批准说明。 | 先在当前事项验证可读性，不批量迁移旧协议或历史；不另建changes目录、全局规范库或新批准状态机，避免与唯一入口竞争。 |
| 4：降低每次协作的重复读取与复验 | `workflow/handoff.md`已有最小简报和禁止粘贴历史的规则；真正不足是执行不稳定，不能再靠增加相同原则解决。 | 借鉴Superpowers专用任务上下文和风险聚焦审查：给一份短简报正反例，明确本次对象/相关AC、允许文件、关键契约、已有证据及待查风险；审查先看实际变化，只有具体风险需要时扩到调用者或补测。完整包核验、完整角色/Skill读取及父回读仍按本仓契约执行。 | 不默认每任务新Agent、不强制双审查者，不复跑已有结果只为补展示。必需独立行为验收仍实际执行，不能照搬“只读diff/不重跑suite”来撤销本仓证据门槛。 |

以上判断分别来自外部机制与当前源码的对照，属于建议，不是已确诊的全部根因。第1项最直接回应近期验收反复；第2项针对需求与交付脱节；第3、4项用于降低阅读与协作成本。是否真的更快、更准，应通过同条件的小范围试点验证，不能预填改善百分比。

### 明确不照搬

- Superpowers当前包含独立ledger、默认每任务fresh agent及自行裁决模糊/超额事项的执行规则；这些与本仓唯一入口、按需委派、明确预算及未知操作规则不同，本节仅借鉴任务上下文与审查方法。
- OpenSpec的自由阶段顺序不能覆盖本仓两道人工确认；Spec Kit完整命令链和constitution也不作为新增必经流程。
- Anthropic多Agent研究系统的[官方经验](https://www.anthropic.com/research/multi-agent-research-system)指出并行适合独立方向和大上下文，同时增加成本，依赖紧密的编码任务未必适合。该研究场景的数值不能外推为本仓收益；先验证单会话或最小必要协作能否完成，再为有证据的独立工作增加并行。
