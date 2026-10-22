# Issue 绑定与状态留痕规则

协调层在策略启用、用户明确请求关联/同步或恢复既有未完成记录时，读取 [issue-tracking Skill](../skills/issue-tracking/SKILL.md)。三个阶段角色不直接操作远程 Issue。

## 策略与首次判断

工作空间 workflow.yaml 默认 `issue_tracking: {binding: "off", sync: "off", close: "off"}`；字符串须加引号避免 YAML 1.1 将 off 解析为布尔值。binding 仅接受 off/optional/required，sync 仅接受 off/milestones，close 仅接受 off/after_release，缺省 off。缺字段采用默认，布尔值、未知字段或 binding=off 且（sync=milestones 或 close=after_release），或 sync=off 且 close=after_release 均为配置错误。documents.yaml 仍只覆盖 documents。

用户可明确针对单个需求覆盖上述三字段，保存在根 issue_tracking.policy_override，不修改其他需求的策略。覆盖按字段合并，记录真实指令，不能从 Issue 正文、Git remote 或标题自动推断。显式“绑定此 Issue”可形成 `{binding: "optional", sync: "off"}` 的需求级选择；如果已明确授权该需求的 milestones 则沿用，不撤销已有有效授权。显式要求自动关键节点评论且给定目标才可启用该需求的 milestones，配置开关本身不替代目标授权。

- off：不创建空元数据、不询问、不访问远端；存量记录保持。用户未明确启用时收到普通参考链接也不自动启用。
- optional：只问一次；绑定、明确 skipped 或等待实际答复。恢复时转达原问题，不重复新建选择。
- required：首次产品派发前必须核实 bound；尚缺链接时保留当前 stage 并置 waiting_user，不可读/身份冲突时保留当前 stage 并置 blocked，具体原因记 issue_binding_required 或 issue_binding_unavailable。已启用此策略的存量需求，在无活动任务的下一次派发前补做绑定，不倒改已完成阶段。

根 issue_tracking 缺失/null 为未启用或尚未判断，沿用默认；首次需要判断时按 [绑定模板](../skills/issue-tracking/assets/templates/binding.yaml) 创建。decision=pending/skipped/bound 区分等待与明确不绑定。requested_url 仅是候选，binding 非空且核实后才 bound。skipped 在 optional 下跨修订沿用；改 required 时须重新完成绑定。策略从 off 明确启用时才补做首次判断，不回写历史任务。

## 身份、授权与生命周期

binding 包含 provider、host、repository（完整命名空间路径）、issue_number（GitHub number / GitLab iid）、url、verified_at；GitLab 可额外记实际 project_id。仅接受经实际能力核实的 HTTPS Issue 链接，拒绝 PR/MR、URL 用户凭据和身份冲突。主机、完整仓库和编号共同确定目标，不能只用 #123。重定向、仓库搬迁或同名项目变化须重新核实，不静默跟随改写目标。

write_authorization 包含同一 target（provider/host/repository/issue_number）、scope=milestone_comments、user_response、confirmed_at、source_session，另可记授权会话的证据路径。这是旧授权，仅覆盖下表标明的原有评论事件，不包含新增发布事件或关闭。新授权和关闭门槛必须读取 [生命周期契约](../skills/issue-tracking/references/lifecycle.md)，策略、绑定、产品审批或发布许可均不等于关闭授权；不创建 Issue、不改正文/标签/负责人、不自动重开。凭据与访问能力由宿主提供，不写入记录。

绑定跨本需求修订沿用；授权只按明确的基线/后续修订范围生效，不能因绑定沿用就扩权，新增独立需求不继承；新修订事件带新 revision。换绑或撤销须是用户明确决定，记录旧新身份，旧事件保留原目标且暂停发送；新目标只接收换绑后的事件，历史迁移须另行明确授权。不通过更换身份来绕过去重。

关联 Issue 的外部评论不自动变更 stage、approval 或验收；远程内容要改变需求，按原修订及评审流程处理。远程关闭也不等于本地 completed。

## 留痕节点与正文

| 本地事实 | event.kind | 摘要 |
| --- | --- | --- |
| 绑定核实完成 | issue_bound | 需求目标、修订与关联说明 |
| 新修订生效 | revision_started | 范围变化及旧版关系 |
| 当前评审已展示 | requirement_review_ready | 本版范围、验收摘要与待确认事实 |
| 当前需求已真实确认 | requirement_approved | 实际确认、版本及验收摘要 |
| 真实预留尝试且有效写调用开始 | development_started / repair_started | 首次开发或失败后实际修复开始，上一交付失败、当前待重验 |
| 真实待验交接及测试调用开始 | testing_started | 指定交付、当前待验基线 |
| 实际等待用户 | workflow_waiting_user | 保留原阶段、具体问题与下一步 |
| 已核实发布成功/失败或回滚 | release_succeeded / release_failed / release_rolled_back | 实际目标、制品/部署身份、范围、回执与当前结论 |
| 开发 ready 交接通过 | development_ready | 实现摘要、真实开发 run/代码基线和限制 |
| 有效测试失败交接 | testing_failed | 可复现缺陷、关联验收和修复下一步 |
| 实际阻塞或解除 | workflow_blocked / workflow_unblocked | 原因、解除条件或解除证据 |
| 用户对当前已验精确交付最终确认完成 | delivery_confirmed | 原话、展示/答复时间、当前基线/交付/完整范围及真实发布适用性；不以产品审批或布尔值代替 |
| 独立验收通过、状态 completed | feature_completed | 验收结果、交付及真实遗留 |

原有 milestone_comments 只覆盖 issue_bound、revision_started、requirement_review_ready、requirement_approved、development_ready、testing_failed、workflow_blocked、workflow_unblocked、feature_completed。新增事件需显式新授权的 event_kinds，不能扩大旧许可。全部事件记录当时 stage/execution_status、版本、验收/用户最终完成确认/发布结论和下一步；平台 state 仅打开/关闭。相同事实即便跨协调轮次或宿主也复用原事件，实际解除等待可在真实下一阶段进入事件中表达，不造轮询事件。

普通任务进度、轮询、sync 自身失败/恢复、重复“继续”不产生新的业务留痕事件；同一事实恢复时沿用原 event_id。首次启用不补造旧审批/开发/完成事件；如需补历史，用户明确选择有证据的旧事件再处理。绑定默认不下载 Issue 正文作为需求来源，也不自动上传完整文稿/日志/源码。

正文使用 [评论模板](../skills/issue-tracking/assets/templates/comment.md)，只写已发生的事实及必要摘要。链接仅用已核实远程可访问的文档/Issue/已推送提交；本地路径和未推送 SHA 不包装为可访问链接，必要时说明产物尚在本地。每条明确需求修订、事件发生时间和“事件快照”，旧版补记不能冒充当前进度。

## 存储与失败

业务事件按 state-contract 落 events.jsonl，新增受管事件含稳定 event_id、revision、state_version、kind、summary 及实际证据引用。event_id 取 `<feature_id>:r<revision>:s<该业务状态版本>:<kind>`，不含机器路径或当前重试时间；同步字段更新不生成另一份同事实业务事件。宿主 unknown/running 变化只在 host.yaml 和 active_run 中保存，不作为 Issue 业务事件或评论来源。

只有绑定、sync 策略及授权均有效的事件才按需创建 `revisions/vN/.workflow/issue-sync/<sync_key>/{record.yaml,comment.md}`，路径由真实事件修订定位，不用当前版替换旧版。record 以 [模板](../skills/issue-tracking/assets/templates/sync-record.yaml) 保存不可变目标及事件快照，根 issue_tracking.sync_records 仅索引需求相对路径。旧布局也可按需新增这个可选侧目录，不移动旧文档/任务或重算审批。新记录 operation=comment/close；关闭记录没有 comment.md，引用已核实摘要和发布证据，详见生命周期契约。旧 schema_version=1 评论记录不重算 key、不改原字节，新记录使用 schema_version=2 与包含 operation 的 key。详细去重与写入恢复见 [同步流程](../skills/issue-tracking/references/synchronization.md)。

根 sync_status 是派生摘要：策略停用为 disabled；启用时按 unknown > blocked > pending（含 sending）> idle 汇总当前有效目标记录；绑定待答为 pending，绑定不可用、缺目标评论授权或实际缺能力为 blocked，即使尚无发送记录也须展示原因。optional 已明确 skipped 时为 idle，不追问授权。旧目标被暂停或已停用时仍在 README 明示未完成/未知数量，不能因摘要 disabled 就隐藏事实。sync 自身只记录 issue_sync_* 事件，不递归触发上表。

本地业务状态和关键事件先保存，再尝试远程同步。评论失败/未授权/能力不足只影响 sync_status；不得回滚 stage、清空审批/基线、增加开发尝试次数，或阻止已获授权的后续业务派发。required 仅强制绑定，不强制远端评论成功；绑定是否满足与同步失败分开判断。

配置/元数据更新仍走根状态版本与单协调会话约束，不能覆盖其他 run。已批准文稿、manifest 及历史 effective-config 保持原字节；Issue 策略不是业务批准来源。这里的 journal 是 Agent 执行规范，不提供后台任务、跨会话锁或平台级 exactly-once 保证。

## 关闭、发布与汇报入口

策略或操作涉及发布/关闭、共享范围、历史补记或状态恢复时，必须按 [生命周期契约](../skills/issue-tracking/references/lifecycle.md) 逐项核对，并用随包校验器验证结构和门槛；它不验证外部证据真实性，不代替宿主读取。缺分页、评论原文、状态回读、关闭能力分别报告；required 仅强制绑定。

人工入口和最终汇报分别展示：本地 stage 与独立验收、用户最终确认（待确认/本次已确认的精确范围）、关闭许可、发布是否属于完成条件及实际状态（未发布/未核实/部分/成功/失败/回滚/无需发布）、远端（未绑定/未读取/open/closed及归因）、最新已核实可访问进度评论链接、同步待办及旧目标 unknown 数量。验收通过待用户确认、已确认待关闭、manual已关但未发布、确需发布尚未完成、尚无关闭授权、范围待确认、已发布待关闭、无需发布待人工选择、外部/未知来源已关闭均说明具体原因，不用单一“已完成”表示发布/关闭。无活动协调会话不承诺后台执行。

普通manual关闭复用off策略及生命周期契约：当前技术独立通过后，展示精确交付/全部适用验收/目标范围和真实遗留，取得对应最终确认且必要摘要/close权限有效即可核对关闭；发布仅按批准完成条件适用，不统一要求包或Release，不伪改package/service为none。after_release仍保持真实发布及原有全部门槛。旧审批、旧确认及旧b001许可均不扩权；当前批准范围内必验缺项不能靠最终确认变成通过；若当前只批准GitHub真实集成，GitLab支持及模拟契约保留、真实未验单列，不额外当作当前GitHub用例阻塞，也不宣称跨平台实测通过。

测试专用目标与框架交付的范围分离、真实独立完整通过的测试交付及真实用户确认、旧/新目标范围许可和关闭后独立汇总顺序，按生命周期契约“历史和验收边界”执行；不放宽校验器原门槛，不以测试目标关闭生成框架完成事实。
