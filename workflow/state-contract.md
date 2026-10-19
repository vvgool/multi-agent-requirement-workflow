# 状态与更新规则

协调 Agent 创建、更新或恢复需求时读取本文。字段模板见 [status.yaml](../templates/status.yaml)。这是 Agent 执行规范，不提供跨会话锁或事务保证；同一需求只允许一个协调会话。

## 字段

- `feature_id`：内部唯一标识，首次新建时生成 UUID，改名、修订不改变；存量 REQ-001 等值保持不变。
- `title`、`workspace_root`、`target_project`：名称及当前宿主动态解析的绝对路径。后两者是本机运行定位信息；复制或迁移后须按 [portability.md](portability.md) 核对并重新绑定，不能当作框架安装约定。
- `requirements_revision`：正整数；当前修订版目录为 revisions/vN。
- `layout_version`：当前修订布局，新增需求/新版为 2；缺字段的存量为 1，规则见 [成果目录](output-layout.md)，不原地改变旧版。
- `state_version`：每次成功更新递增，与需求修订号不同。
- `stage`：draft、requirement_review、development、testing、completed。
- `execution_status`：idle、running、waiting_user、blocked。
- `coordinator_session`：当前负责的真实会话标识；宿主不提供可核实标识时记录 null，并遵守单会话约束，不编造标识。
- `active_run`：null 或含 run_id、role、revision、dispatch_status、host_task_id 的对象。新锁定安装另含 host、framework 四字段身份（见 [包规则](package.md)）；历史active_run不补写。dispatch_status 为 prepared、unknown 或 running。prepared 在真正调用前改为 unknown；得到宿主返回后保存真实任务标识并改为 running。
- `approval`：null 或含 feature_id、revision、review_digest、user_response、confirmed_at、source_session 的审批记录。人工确认后才填入；审批原文保留，时间和来源不能伪造。
- `pending_review`：null 或含 revision、document_digests、source_digests、config_digest、review_digest、displayed_at 的待审记录。
- `artifacts`：含 kind、path、revision、run_id（适用时）的列表；path 默认相对需求目录。正式文稿同时记录 sha256、source_path、source_sha256（候选路径相对需求目录），按目录规则更新当前版有效项并保留 run 原产物索引。设计维护中在需求目录外的产物必须标记 `base: workspace`，不能作为角色输出例外。
- `block_reason`：null 或具体原因，缺角色时另记录 `required_role`；`development_attempt`、`max_development_attempts` 为非负/正整数。开发调用次数按 [routing.md](routing.md) 记录，缺角色时不消耗次数。
- `development_baseline`：null 或当前待测开发 run_id、代码标识和证据路径；每次开发完成后更新，测试必须绑定该基线；结构与兼容见 [代码基线契约](code-baseline.md)。
- `issue_tracking`：缺失/null 时按默认策略；启用后记录需求级选择、真实绑定、评论授权和同步记录相对路径，见 [Issue 规则](issue-tracking.md)。同步摘要与业务 stage/execution_status 分开，不以远端评论代替审批。
- `last_event`：最近发生的事实。框架自身的 `design_review`、`implementation_review` 可附加记录，不代替业务需求审批。

## 迁移与条件

| 当前阶段 | 条件 | 下一状态 |
| --- | --- | --- |
| draft | 信息不足，产品返回具体问题 | draft/waiting_user，active_run 清空，问题及结果保留 |
| draft | 无活动任务，仍有有效未决问题且无待处理变化/分析/产稿，仅部分答复、无新信息或已有选项解释 | draft/waiting_user，仅记录答复与决策，不创建 run |
| draft | 首次需求整理、需新分析或答齐整理文稿，且已实际调用产品 | draft/running，保存真实宿主任务标识 |
| draft | 产品返回 ready、质量检查记录及必要产物齐全，评审内容已展示 | requirement_review/waiting_user |
| requirement_review | 用户对当前展示版本明确确认，摘要仍一致 | development/idle，检查开发角色并派发；角色缺失则 development/blocked、role_not_available |
| development | 有效审批，开发 ready 且报告/代码基线交接完整 | testing/idle，检查测试角色并派发；角色缺失则 testing/blocked、role_not_available |
| testing | 所有验收通过、无未执行项/未解决缺陷、代码基线一致 | completed/idle，保存最终证据，不发布 |
| testing | 有可复现失败报告，已核对本版开发基线 | development/idle 并带报告修复；开发次数用尽则 development/blocked |
| testing | 环境不可用、证据不足或检查待完成 | testing/blocked，保留未执行项，不冒记通过 |
| 任意未完成阶段 | 范围改变且旧任务确认结束 | 归档旧版，下一版 draft/idle，重新评审 |
| 任意阶段 | 业务角色调用、权限、身份或证据异常 | 保持 stage，execution_status=blocked，记录原因 |

全阶段选择、角色可用性、各类结果及重试上限见 [routing.md](routing.md)。各阶段质量检查由对应角色负责，协调层核对交接完整性后更新状态；角色文件与路由规则不代表真实调用已完成。新版不继承审批。关键文档缺失不等同测试失败。completed 的历史完成记录保留。

## 每次更新

1. 先读根 status.yaml，核对 ID、当前修订、state_version 和活动任务。记录所读版本；另一个协调会话或写入冲突存在时暂停。
2. 持久化本步任务、结果或证据，所有路径指向实际存在的文件。清空 active_run 前保留真实宿主任务信息。
3. 写入前再次核对 state_version；不一致时重读并停止本次写入，不能覆盖。
4. 更新根状态、递增 state_version，然后回读比对，按 [需求入口模板](../templates/feature-readme.md) 更新根 README 的当前进展和有效成果链接；events.jsonl 追加同一版本、事实和证据路径，记录宿主可取得的真实时间。派发的 prepared/unknown/running、阻塞、交接和恢复都同步当前修订、阶段/执行状态、下一动作；真实活动 run（无则明确无）保存在状态和事件，README 按共享入口规则展示进展；已有开发/测试报告在新基线未验时标“上一基线，当前待重验”。
5. 若需 Issue 留痕，业务状态与事件已回读有效后按 [Issue 规则](issue-tracking.md) 调用支持 Skill。元数据更新同样递增版本，仅记 issue_sync_* 等控制事件，不递归生成业务留痕；同步失败不覆盖业务状态、审批或基线。
6. 任一步中断恢复时核对根状态、run 文件和事件，同时核对 README 的 feature_index 归属/已知摘要及当前状态内容。状态已保存而入口未同步时只补派生入口，保持活动调用，不创建新 run；入口摘要不符或被用户编辑时保留原内容，在现有事件中记录入口同步冲突和位置，报告给用户，不把索引冲突写成业务调用已结束或擅自停止。入口变更后保存新的 feature_index 摘要；无法证明上次入口更新归属时不覆盖。事件缺失但状态已写入，核查后补记 recovery 事件；需 Issue 留痕的事实若有持久证据可还原原业务版本和事件内容，另按原 event_id 补齐一次原业务事件，recovery 仅引用它；无法还原时保留待核查，不从当前阶段猜造旧事件；发生矛盾则阻塞，不通过“补全历史”伪造成功。

发现未知或旧字段时先读已有记录说明，迁移只在确定语义且无活动任务时进行。恢复不因为 schema 存量差异而删除历史信息。

## 无新 run 的澄清更新

draft 阶段的答复按 [产品路由](routing.md#产品澄清答复) 处理；记录格式与累计交接见 [交接](handoff.md#澄清记录与再次派发)。没有新调用仍须使动作可追踪：input.md 追加真实答复和决策依据；仍有有效未决问题且无待处理变化/分析/产稿时，根状态保持 draft/waiting_user，active_run=null，last_event 记 clarification_recorded 或 clarification_waiting；events.jsonl 引用输入记录及来源 run/result，记录动作、原因、未决问题与待处理答复位置。事件可关联来源 run，但不得伪称发生新调用或创建空 run。

存在 active_run 时保留其身份、dispatch_status 和当前真实执行状态，追加新答复并以 clarification_pending 标记待处理，不清除任务、不改为无任务等待。确认原调用结束且结果交接核对后，再将累计答复和结果一并按路由重新决策，处理完成追加处理记录；真实 host 结束信息按原交接保存。

上述持久化更新全部遵循“每次更新”：读取及再次比较 state_version、递增、回读、入口同步、同版本事件与冲突即停；不以只写 input.md 代替状态协议。恢复时先从状态、input.md、事件及来源结果重建当前有效问题、累计答复和待处理项，优先恢复未完成的分析/产稿决策；最新消息为空、重复或“继续”不能清除已保存的待处理动作。无活动任务但尚待分析/产稿时保留 clarification_pending 及对应输入引用，按路由继续；仅保存输入或准备派发不记为处理完成。已处理记录须关联覆盖这些输入的真实 run/适用结果；已有调用先核实，已有适用结果接续交接，不重复执行旧动作；状态已写而事件缺失按原恢复规则核查补记，矛盾时阻塞，不靠重派消除矛盾。无新答复的重复展示可以引用已有记录，不凭空产生答复或 run。

澄清选择不写 approval/pending_review；产品 ready 后仍按文档规则展示并取得本版明确审批。已批准内容变化按修订规则保留历史并重新评审。

## 开发方案展示状态

运行中方案按 [通知契约](execution-contract.md#协调消费) 与 [候选展示](output-layout.md#开发中候选展示) 消费。只新增/更新 artifacts 中 development_progress 的显示来源元数据及状态；stage、active_run、development_attempt和审批保持真实业务事实。每次显示元数据持久化也执行 state_version 比较、递增、回读、事件及入口同步；事件记 development_plan_display_pending/displayed/blocked，附run、版本、清单摘要与实际原因，不伪造实现完成或最终ready。

同一run更高版本才可替换当前显示来源，相同版本相同摘要只恢复未完成展示；相同版本不同摘要、用户修改README/正式稿、未知任务身份或索引矛盾先保留并报告阻塞。展示blocked与实施进度分开，不能凭展示失败更改开发真实执行状态；若开发回报needs_input/blocked则按原结果流转并展示已有方案。plan_partial展示记录保留execution、missing_artifacts及真实问题/解除条件，仅表示已列批次通过检查，不表示方案完整或阻塞解除；running/full缺稿不能展示为就绪。旧通知只留存，不覆盖较新版本；已提交版本显示中断按原更新恢复规则补办，不重复派发。任务未知先查原调用，不能通过创建新run解决展示问题。最终正式固化后入口以最终结果为准，保留原候选来源和展示证据。
