# Multi-Agent Requirement Workflow

由协调 Agent 在宿主会话内按状态调用产品、开发、测试 Agent，完成需求澄清、用户确认、实现、独立验收和修复。使用宿主原生能力，不提供工作流 CLI 或后台调度服务，不自动执行生产发布。

## 快速开始

提供 Codex、Claude Code 和 OpenCode 文件适配；各宿主原生激活与业务闭环须分别验证。需要宿主具备项目文件读写、Git 获取及原生子 Agent 派发能力；初始化不需要独立工作流 CLI 或全局插件。

在**目标业务项目**中打开 Agent 会话，发送：

```text
请从 https://github.com/vvgool/multi-agent-requirement-workflow 获取需求协作框架。
在临时目录获取代码，读取其中 skills/setup-requirement-workflow/SKILL.md，
为当前项目初始化，自动检测项目内的 Codex、Claude Code、OpenCode 配置，
为当前宿主及检测到的宿主一起准备适配文件。
首次安装解析仓库默认分支并固定实际完整提交 SHA 和包摘要；
已有 workflow.lock.yaml 时按锁恢复，不自动升级。
保留项目已有规则和配置，不提交完整框架缓存。
分别报告文件安装、原生角色激活和未完成项。
```

这是由宿主 Agent 获取仓库并执行初始化 Skill，URL 本身不会自动注册角色，也不是原生插件安装命令。官方仓库公开，读取和安装无需 GitHub 登录；自行使用私有来源时使用已有认证，不把令牌写进 URL 或配置。

第一次安装默认取当时的默认分支，随后锁定实际提交。团队需要统一版本时，在提示中指定完整提交 SHA 或 tag；tag 也必须解析成完整 SHA 后入锁。安装步骤见 [初始化 Skill](skills/setup-requirement-workflow/SKILL.md) 和 [Git 获取规则](skills/setup-requirement-workflow/references/installation.md#githubgit-url-获取)。

### 初始化后会产生什么

| 内容 | 是否提交 |
| --- | --- |
| workflow.yaml：项目策略 | 是 |
| workflow.lock.yaml：Git URL、完整提交、版本和包摘要 | 是 |
| AGENTS.md 中的短入口、目标宿主各自的四个薄角色、.gitignore 区块 | 是 |
| Claude Code 的 CLAUDE.md 短桥接 | 使用 Claude Code 时提交 |
| documents/ 中的需求、方案和验收成果 | 按项目约定共享 |
| .workflow/ 执行现场、.agents/requirement-workflow-cache/、本机回执和中断记录 | 否 |

默认初始化当前宿主及项目中检测到的宿主：.codex/ 对应 Codex；.claude/ 或 CLAUDE.md 对应 Claude Code；.opencode/ 或 opencode.json/jsonc 对应 OpenCode。只在项目根检测，不因机器装了 CLI 就生成配置。可明确要求“只初始化当前宿主”或“全部三个宿主”。

全新项目单宿主 Codex/Claude Code 涉及 9 个文件、OpenCode 8 个，三个宿主一起共 18 个；共享一份版本锁、缓存和 AGENTS 入口。Codex通过 `.codex/config.toml` 的受管注册区块引用四个薄角色，仅拥有该区块，保留原有配置；restore不补缺失注册。已有文件保留原文，只添加受管区块。所有目标先预检，任一冲突先停止整批写入，写入中断则保留原批次计划供恢复，不将半安装标为成功。

文件可一次准备，原生激活按宿主分别验证：在 Codex 中不能把 Claude Code/OpenCode 标为已激活。未验证者保持 pending；后续进入对应宿主会话再只读探测。

协调 Agent **运行在主会话**：宿主读取项目 AGENTS.md 后，按版本锁定位缓存，再加载 agents/coordinator-agent.md 和状态路由规则。因此只注册产品、开发、测试、Bug 四个原生子 Agent。入口详见 [宿主适配](workflow/host-adapters.md)。

### 验证并使用

安装后开启新会话或使用宿主已支持的重载方式，发送：

```text
按项目 AGENTS.md 加载需求协作入口。
只读核对框架版本，并实际验证产品、开发、测试、Bug 四个原生角色是否可调用。
不创建需求，不执行开发。
```

角色可用后，直接提出需求：

```text
按需求协作流程处理“用户签到奖励”：
每账号每天首次签到奖励10积分，北京时间零点刷新。
先澄清需求，当前修订经我确认后再开发。
```

继续已有需求：`继续“用户签到奖励”，先核对状态和活动任务。`

### 团队、换机与升级

同事克隆业务项目后，直接发起或继续需求即可：主会话从已提交的 AGENTS.md 读取自包含入口，缓存缺失时从版本锁指定的完整提交获取核心，先核验摘要，再补本机缓存和回执；成功后才加载协调规则。缓存已完整时可以离线启动。Git缺失、离线且无缓存、提交不可得、摘要或入口不符时明确阻塞，不改锁或需求状态。

自动恢复仅限本地缓存/回执，不会自动升级、生成新宿主角色或覆盖用户修改。只读检查不会触发下载或修复。原生角色仍需当前宿主实际支持；恢复文件不代表激活完成。详细步骤见 [启动与恢复](workflow/bootstrap.md)。

也可以单独要求补环境：



```text
按当前项目 workflow.lock.yaml 获取并核验固定提交的框架，
补齐当前宿主及项目检测到的宿主的本机需求协作环境。保留版本和已有文件，不自动升级。
```

初始仓库 URL 用于找到框架；后续以项目锁为准。升级需要明确提出，并确认旧活动任务结束。旧快照或 manual 锁不会因为仓库上线而自动换源。

无法联网时，可先在有权限的机器获取相同提交的代码，再向 Agent 提供本地包目录；已有 Git 锁须核实该目录确实对应锁定提交，无法证明时停止，不能改成 manual 绕过。无锁的新项目仍可按手动包安装。

源码版本为 **0.4.0**，协议为 2；发布状态以仓库的 Git tag 和 Release 为准。本项目当前安装仍锁定 **0.2.6**；已有项目须显式升级版本锁和缓存才会采用新包。0.2.6 已合并共享文稿规则的按需读取精简、执行证据边界及 OpenCode 父会话目录核对说明。维护用离线实验工具不进入运行包，也不证明实际 token 收益。

历史 0.2.4 候选（核心摘要 `39c446bc4a6593b66086b01ae183718b471cb0b96bf319fa7d8cc197564f0843`）已验证三宿主文件适配、Codex/OpenCode 三原生角色及 Codex 代表性真实闭环；Claude Code 原生运行仍缺验。版本整理改变包身份，旧包原生及闭环证据不等于 0.2.6 验收。无原生选择能力时记录 pending，不使用通用 Agent 冒充通过。仓库中的 [验证摘要](docs/verification/README.md) 记录实际边界；完整测试快照和运行记录不随当前源码分发。

## 角色与流程

| 角色 | 职责 | 工作流入口 |
| --- | --- | --- |
| [协调](agents/coordinator-agent.md) | 状态路由、宿主派发、交接、用户确认和成果索引 | [协调路由](workflow/routing.md)；按条件加载 Issue 支持 Skill |
| [产品](agents/product-agent.md) | 澄清业务规则，整理需求与验收标准 | [requirement-analysis](skills/requirement-analysis/SKILL.md) |
| [开发](agents/development-agent.md) | 技术设计、模块/任务规划、实现、完整功能自验及基线 | [feature-development](skills/feature-development/SKILL.md) |
| [Bug](agents/bug-agent.md) | 边界整理、证据诊断、最小修复和自验 | [bug-fixing](skills/bug-fixing/SKILL.md) |
| [测试](agents/testing-agent.md) | 核对需求/实现/用例偏离，独立验收、回归和缺陷报告 | [acceptance-testing](skills/acceptance-testing/SKILL.md) |

阶段为 draft → requirement_review → development → testing → completed；测试失败回开发。开发前必须取得当前修订的真实用户确认；同名续改按 [修订规则](workflow/revisions.md) 保留历史，新版重新确认。恢复先核对活动任务，不能重复派发未知调用。

阶段 Agent 自行加载所属 Skill 和落盘模板。产品先核实事实、再按关键决策分轮澄清；小需求默认需求稿、开发记录和测试报告三份。复杂开发才展开技术方案、按依赖排序的大模块与小任务计划、整体自验；普通/长任务按模块选择。开发优先遵循项目规则，缺少架构约定时按 Clean Architecture 原则做最小设计。

## 工作空间与人工入口

```text
目标工作空间/
  workflow.yaml                   # 项目策略
  workflow.lock.yaml              # 框架来源、固定版本与摘要
  AGENTS.md                       # 简短主会话入口
  .codex/、.claude/或.opencode/    # 每个目标宿主四个薄角色
  .agents/requirement-workflow-cache/<sha256>/ # 本地缓存，Git忽略
  agent-features/<需求名称>/
    README.md                      # 人工入口：进度、有效文稿、待办及 Issue 同步提示
    status.yaml
    events.jsonl
    revisions/vN/
      input.md
      documents.yaml               # 有文档覆盖策略时才创建
      documents/                   # 正式需求稿、开发记录、测试报告
      .workflow/
        review-manifest.yaml
        tasks/<task_id>/           # 持续角色任务，host调用与result交付按序追加
        issue-sync/<sync_key>/     # 启用且有获授权事件时才创建
```

用户使用需求名称，内部 feature_id 稳定不变。配置与需求目录相对用户指定的工作空间解析；锁定包按摘要从本地缓存定位，框架来源目录不是默认工作空间。详情见 [配置](workflow/config.md)、[成果目录](workflow/output-layout.md) 和 [共享与路径定位](workflow/portability.md)。旧布局按原索引读取，不搬迁已批准文稿或重算审批。

人工日常只需看需求根 README；评审看当前 requirements.md，交付看 test-report.md 和实际功能。执行记录仅在排查或恢复时展开。

## 文档来源与 Issue 留痕

[workflow.yaml](workflow.yaml) 提供本地/飞书文档策略。修订内 documents.yaml 仅覆盖文档来源；Issue 的需求级策略保存在根状态。飞书受控写回目前仅覆盖产品需求正文，技术方案和测试报告仍输出本地文稿。权限和来源校验见 [文档规则](workflow/documents.md)。

Issue 默认关闭：

```yaml
issue_tracking:
  binding: "off"   # off / optional / required
  sync: "off"      # off / milestones
```

optional 在首次派发前选择绑定或跳过；required 在业务派发前要求绑定。sync=milestones 且用户明确授权目标后，协调主会话通过 [issue-tracking](skills/issue-tracking/SKILL.md) 在评审、确认、开发交付、测试失败、阻塞及完成等节点评论。选择和授权跨本需求修订保存，也可只对单个需求启用。

首版只关联已有 GitHub/GitLab Issue，不创建/关闭 Issue，不改标签或负责人。评论失败独立记录，不回退业务；未知写入先核实，不盲目重发。使用宿主已有连接能力。详细身份、授权及恢复语义见 [Issue 规则](workflow/issue-tracking.md)。

## 验证与维护

Codex注册区块的TOML语义与保留配置回归（仅源码分发提供测试，不是宿主激活验收）：`python3 -B -m unittest discover -s tests -p 'test_codex_registry.py'`。使用已有Python 3.11+ tomllib或tomli，不安装依赖。运行时setup所需纯合并helper位于包内 `skills/setup-requirement-workflow/scripts/codex_registry.py`。

三端实际模板/共用正文及配置保留回归：`python3 -B scripts/verify-host-adapters.py --source-root . --scratch /absolute/authorized/empty-directory`。可选 `--opencode /absolute/path/to/existing/opencode` 以已有CLI核对合法JSONC和四个原生定义的发现；首次发现可能短暂不完整，输出保留最多三次只读观察。脚本只生成授权空目录内的开发夹具，不安装项目、写回执或执行模型；发现列表不能证明实际委派。OpenCode/Claude使用原生Markdown文件发现，不需要复制Codex的TOML合并helper。三个宿主分别核对自身的同名角色、禁用和权限，不能从一个宿主成功推断其他宿主。


初始化区分文件安装、当前宿主原生激活和完整需求闭环，具体以本项目本机回执为准。验证范围见 docs/verification/README.md；历史手动加载正常闭环及旧快照证据不能作为当前三宿主原生通过的证明。真实飞书和Issue平台联调仍需独立完成。

开发源码提供 `scripts/verify-artifact-slimming.py`（不属于业务安装包），只需已有 Python 3.9+、PyYAML 和 Git，无需私有需求历史、本机框架缓存或联网安装。取得候选源码后，在其根目录运行（将示例位置替换成**任务明确授权、已创建的空目录**）：

```sh
python3 scripts/verify-artifact-slimming.py --source-root . --scratch /absolute/authorized/empty-directory
```

脚本只写该目录，拒绝非空目录、目录链接、源码根及其祖先等危险目标，保留现场供检查，不执行框架源码提交。输出覆盖缓存/证据、复用失效、源码基线、清理保护和入口恢复的文件协议样例；它包含模型辅助函数，**不能证明生产调度、隔离包安装、宿主原生激活或真实需求闭环**。依赖缺失时报告缺口，不自动安装。候选源码的 Git 发布状态与本地复验分开报告。

共享发布包包含framework.yaml、LICENSE、AGENTS.md、README.md、workflow.yaml、agents/、skills/、workflow/、templates/。docs/不默认安装到业务项目。框架自身agent-features/、早期docs/superpowers/、完整验证夹具及运行记录仅保留本地，不进入当前仓库版本。三个宿主不需要使用相同插件格式；插件只作为可选分发方式。

业务项目通常只需提交workflow.yaml、workflow.lock.yaml、入口和各目标宿主的四个薄角色，以及精确的.gitignore区块；Claude Code按需多一份CLAUDE.md短桥接。完整包缓存、本机探测回执和任意层级的 `.workflow/` 不提交，初始化写入忽略区块。`documents/` 独立可读，不链接本机任务和日志；本机仍保留恢复及审批记录。换机按锁重建环境，显式升级项目绑定；用户修改的入口不覆盖，旧包和需求证据不自动清理。详情见 [包与版本规则](workflow/package.md)。

旧 `.agents/requirement-workflow/installation.json` 快照安装保持原状，不自动迁移。本框架不新增后台服务或跨会话锁，同一需求仅一个协调会话推进。升级/换宿主前确认旧任务结束；审批、开发基线和历史run不得改写。更完整的目标和职责说明位于开发目录docs/planning/。

## 仓库与安装来源

源码：https://github.com/vvgool/multi-agent-requirement-workflow。推荐使用 Git 来源；锁定提交和实际包摘要共同确定安装身份。共享核心包含哪些文件、如何计算摘要以及旧版兼容，见 [包与版本规则](workflow/package.md)。


当前仓库布局：

```text
agents/              # 协调主会话及四个执行角色
skills/              # 阶段及支持 Skill、模板和宿主适配
workflow/            # 共享流程契约
templates/           # 交接及状态模板
docs/planning/       # 当前目标与职责
docs/verification/README.md  # 精简验证摘要
scripts/             # 随源码分发的最小开发复验入口，不进入业务安装包
```

## 开源许可

本项目使用 [MIT License](https://github.com/vvgool/multi-agent-requirement-workflow/blob/main/LICENSE)。分发核心包时保留LICENSE；早期无LICENSE的包按其原清单校验，版本锁不会因仓库公开而自动迁移。

## Bug 修复

0.3.0 历史候选引入 Bug 原生角色；当前 0.4.0 沿用并轻量化持续任务，当前源码版本不代表任何项目已升级。独立 Bug 先由 Bug Agent 整理边界经明确确认后修复，开发后/开发中补充按 [Bug 路由](workflow/bugfix.md) 交接。修复自验后必须由测试 Agent 独立验收，失败返回修复；全部写阶段派发共用默认 3 次额度。旧锁、历史任务、成果和审批不自动迁移。

文件模板检查不证明原生角色调用或真实修复闭环通过。

## 0.4 持续角色任务（协议2）

同一事项/修订每个实际角色一个持续任务；产品问答、开发回修、测试复验及换宿主不再自动建立任务包。调用身份与每轮不可变交付分别保存在已有host/result中，测试绑定具体交付和代码基线；普通问题轻记input。详见[持续任务契约](workflow/continuous-tasks.md)。新任务schema_version=2/layout_version=3，旧协议1及旧审批由原锁定包继续解释，不迁移、不自动升级本项目安装。框架是宿主执行规范，静态场景不证明真实宿主已激活或业务闭环通过。

持续任务的真实Codex产品续接、开发修复/独立复验、新上下文恢复和OpenCode未知原因Bug证据，均绑定各自包身份，见[持续任务验证](docs/verification/continuous-tasks.md)。最终验收另已覆盖 Codex 与 OpenCode 新主会话四原生角色及各自代表性业务闭环；Claude 未纳入本轮验收，真实消费者升级和生产部署仍须单独验证。
