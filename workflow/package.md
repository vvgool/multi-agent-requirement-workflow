# 通用框架包与项目绑定

实际使用框架协作、原生角色、任务恢复、安装、换机或升级等能力时读取；独立一次性、明确局部低风险且非旧任务续接的小修只遵循已载入项目入口的授权/风险/未知操作规则，不为其读锁、缓存或本文件。共享核心不依赖某个宿主的插件格式；插件可作为分发渠道，原生注册仍由 [宿主适配契约](host-adapters.md) 处理。

## 包与内容身份

框架包包含根 framework.yaml、AGENTS.md、README.md、workflow.yaml、LICENSE（存在时必须纳入），以及 agents/、skills/、workflow/、templates/ 内的全部普通文件。排除 docs/、agent-features/、Git 元数据、宿主安装目录及本机回执。包内不接受符号链接或特殊文件，未知根文件不纳入包；安装时无需扫描整个开发仓库。

framework.yaml 仅含 schema_version=1、name、非空 version、protocol_version=3（本包）；它声明版本而非已发布事实。包名固定为 multi-agent-requirement-workflow。使用宿主文件/计算工具实际生成清单：所有包文件按相对 POSIX 路径升序，取 `[相对路径,原字节SHA256]`，将全部条目编码为 UTF-8 紧凑 JSON 数组（ensure_ascii=false、无额外空格），整体 SHA-256 为 package.sha256。framework.yaml 自身也参与摘要计算，因此不在其中存储自引用摘要。文本不转换换行；同名同版本不同字节按不同内容身份处理，不能自动接受。

## GitHub URL 与固定提交

官方源码：https://github.com/vvgool/multi-agent-requirement-workflow。新项目可以直接向宿主提供仓库 URL；初始化按 [Git 获取步骤](../skills/setup-requirement-workflow/references/installation.md#githubgit-url-获取) 取得完整代码并解析实际提交。未指定版本时仅首次安装解析默认分支，最终锁中保存完整提交 SHA，后续恢复固定该提交，不跟随分支。官方仓库公开，可匿名读取；用户自行使用的私有来源仍需已有权限。仓库 URL 不是插件协议或工作流执行入口；仍须读取 setup Skill 并完成当前宿主适配。

## 项目内的两类文件

需提交的最小内容为 workflow.yaml、workflow.lock.yaml、AGENTS.md 中的入口区块、目标宿主各自的四个薄角色文件、.gitignore 的本地目录忽略区块；Claude Code 如需读取入口另加 CLAUDE.md 的短桥接区块。不修改无关设置；默认安装当前宿主及项目检测到的宿主，用户显式选择范围优先；未检测且未选择的宿主不生成文件。具体见 [宿主选择](../skills/setup-requirement-workflow/references/installation.md#宿主选择与批量初始化)。事项文档及实际成果按 [成果规则](output-layout.md) 共享，不默认建立本机业务执行记录。

本地不提交：`.agents/requirement-workflow-cache/<package.sha256>/`（完整只读包）、`.agents/requirement-workflow.local.json`（各宿主安装与探测回执）、`.agents/requirement-workflow.pending.json`（中断意图）及任意层级的 `.workflow/`（本机执行现场）。不忽略整个 .agents、.codex、.claude、.opencode 或 agent-features，保留用户配置和共享成果。不创建 Skill 符号链接或复制阶段 Skill 到宿主目录；原生角色按明确包内路径读取完整 Skill 及模板，属于文件加载，不宣称原生 Skill 发现已验证。

锁文件使用 [模板](../skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml)，只含 schema_version、package、source。package.name/version/protocol_version 必须与真实包一致，sha256 为64位小写十六进制。source.kind 为 git/manual：git 的 location 是用户明确的 HTTPS/SSH Git 地址、revision 是完整提交哈希，拒绝嵌入口令/令牌和本机路径；manual 的 location 是 `包名@版本` 分发标识、revision=null。手动包由同事提供或用户另行下载，标识不能自动解析为下载地址。没有真实仓库信息时使用 manual，不编造 Git URL/tag。Git 来源须从指定提交实际取包并复核内容，不将当前脏工作树冒称为该提交。

锁文件是跨机器绑定；本机绝对路径只进入任务/回执，不写锁文件或薄角色。其他成员拉取项目后，须按锁定来源取得包、核对摘要并在本地初始化；提交配置不等于其机器已经安装。缺包时主会话先按 [启动恢复](bootstrap.md) 从锁定来源恢复并核验；子角色直接返回 framework_not_installed。无法恢复则阻塞，不自动使用最新全局包或其他项目的包。

## 运行与版本

新轻量安装的框架根目录固定为项目根下 `.agents/requirement-workflow-cache/<锁定sha256>`；当前会话实际使用框架能力前首次完整校验包清单、当前宿主薄角色与入口及其实际生效状态；后续按下节复用未变化的环境核验。缓存或薄角色被修改返回 framework_integrity_mismatch/adapter_modified。读取不同宿主的回执不能证明当前宿主生效。初始化 pending 存在时先恢复，不能运行半安装结果。

0.7.0采用协议3，一次性局部低风险小修可直接在当前会话完成，需要持久文档时维护一个协调入口并按复杂度拆分职责文档，需要委派才用原生任务；不创建机器状态/调用/交付，不沿用协议2的schema/layout。协议1/2的旧任务必须使用原锁定包，不得用本包续写、迁移或重新审批。源码仓库的旧受管入口只代表其当前锁，分发时使用新入口模板，不复制该区块作为新协议运行要求。

显式升级前确认原生活动调用已经结束，旧协议还须按原包核对其active_run。旧包、旧需求版本和审批原样保留。升级不静默迁移历史；如果需要继续旧任务先保持原绑定直到其结束。

## 会话内核验复用

各原生会话在相同工作空间、宿主和锁定包下，自行完整校验后可在自己的上下文保留结果及文件变化快照（路径、类型、大小、纳秒级mtime/ctime），不新增回执字段或报告。同一角色的初始化探测与后续业务任务也适用；主会话或其他角色的结论不替代本角色首次核验。后续调用仍重读锁、检查安装pending，并核对包及受管入口/角色的文件集合与变化快照；未变时复用完整校验和当前宿主激活证据，不重复逐文件哈希、restore或原生探测。元数据比较仅用于可信本机只读缓存的性能优化，不作为抗恶意并写保证；无法可靠取得变化信息时完整校验。

新会话、上下文丢失、换机/换宿主、锁或受管文件变化、安装/升级/恢复后，以及任何内容或并写疑点，均使复用失效：重新完整核验，发现修改仍按完整性规则阻塞，不将变化快照直接认作新合法内容。当前任务文档、允许范围和原生任务状态按实际工作核对；环境复用不替代业务事实。

## 升级、离线与旧安装

默认按锁复用，源目录变了不等于用户要求升级。显式升级先确认无未结束任务，获取新包并验证协议和适配器变化；按初始化 pending 的 before/after 规则更新锁和本框架拥有的薄入口，保留旧包及全部需求证据。若本框架拥有的文件已被修改，应先列出差异，不直接覆盖。不自动升级其他项目，也不自动清理旧包或卸载。

旧 `.agents/requirement-workflow/installation.json` 是快照安装：沿用旧入口与原字节，另见 [旧 Codex 快照流程](../skills/setup-requirement-workflow/references/codex-installation.md)。不因运行新版 setup 而自动迁移、删快照或改历史任务；无新锁且有旧完整清单时先报告 legacy_snapshot，只有用户明确要求迁移才另列差异。旧 pending 优先按旧记录恢复。离线用户可分发相同内容的手动包；旧快照模式保留为兼容选项，不是新项目默认。
