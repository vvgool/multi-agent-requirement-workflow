> 历史协议1/2参考；协议3不调用此机器流程。旧任务只读其原锁定包，本候选不解释或改写旧记录。

# Issue 生命周期：授权、发布、关闭

本契约是协调主会话的按需执行规则；不新增服务、阶段、角色或第二份进度账本。先读 Issue 规则和完整 Skill。源事件、审批、交付与发布事实先保存；同步仅改变自身摘要，不改变 stage、审批、基线、尝试次数或妨碍已授权业务派发。completed 仅表示独立验收通过。

## 一次性授权与兼容

新授权按 [授权模板](../assets/templates/authorization.yaml) 保存真实用户原话、时间及来源。target 固定 provider/host/repository/issue_number；feature_id、baseline_id、scope_description 明确展示覆盖范围。operations 只接受 comment/close；event_kinds 列出允许评论的真实事件；include_future_revisions=true 只有用户明确涵盖同事项后续修订时才能记录。新范围必须新审批、独立验收及本次最终完成确认；发布仅在批准完成条件或after_release下要求，跨事项不继承。revisions 不扩展操作/事件权限。授权撤销用 revoked=true 保留原记录。旧 scope=milestone_comments 仅支持旧规则九类事件，无关闭或新增发布事件权。

binding、close 策略、产品审批、发布许可、“继续优化”均不授予远程写。可一次展示目标、允许事件、关闭策略、完整范围及后续修订边界后确认，范围内不逐事件重复问。新增事件/范围或目标变化先补授权。close=off 不自动关闭；用户明确单次关闭时 mode=manual，必须核对 comment+close 及必要进度/独立验收/最终完成确认和真实发布适用性摘要的授权；可与本次最终确认在同次展示/答复取得，已有有效范围许可不逐次重复询问，不能用 sync=off 绕过审计。关闭权限不授予部署、重开或编辑 Issue。

## 用户最终完成确认

manual 复用现有关闭模式，不新增配置策略。技术验收、用户最终完成确认、comment/close授权、真实发布是四个独立事实。产品审批、“继续”、feature_completed、manual_summary_authorized 或 no_release 布尔标记均不等于最终确认。用户可在一次明确展示后的答复同时确认完成及授予关闭/摘要许可，不机械分成多轮；事前已获有效许可则只需本次完成确认。旧b001许可不静默覆盖新范围或新事件。

采用 [最终完成确认模板](../assets/templates/completion-confirmation.yaml)，由协调保留原始答复与展示证据，调用 confirmation 检查后，按真实状态契约只生成一次 delivery_confirmed 事件（不替代技术通过的feature_completed）。授权 event_kinds 必须显式涵盖该新事件，旧 milestone_comments 不扩权。记录按现有事件/同步机制引用，不建独立进度账本。

confirmation 及 close 的manual分支必须核对：

- completion_requirements 来自当前批准完成标准，绑定 feature_id、baseline_id、scope_ids、全部 required_acceptance_ids、release_required 和真实 release_kind，保存实际证据引用；不是用户临时口述后随意改布尔值。
- 当前独立验收 passed，acceptance_results 完整覆盖批准的全部适用验收且均passed、有证据；failed/blocked/未验、缺GitLab必验等不能被概括passed或用户确认覆盖。
- 最终确认为 kind=delivery_completion，绑定当前事项、基线、精确 delivery_id/code_baseline_digest、完整scope及具体Issue。原话、response_evidence、confirmed_at和展示presentation不可缺；真实 source_session 不可得可null，不捏造。
- presentation 绑定相同身份、目标、范围、验收证据；delivery_summary及acceptance_results快照完整展示交付摘要、全部适用验收结果，scope_coverage_evidence保留完整Issue范围核对引用；及真实遗留（unresolved_items必须为空），实际发布种类/状态、是否属于完成条件及影响证据。独立passed_at ≤ presented_at ≤ confirmed_at，均为有时区时间。孤立“可以/继续”只有实际对应明确展示的最终交付和关闭请求才可解析，不能挪用产品审批答复；校验器不判读自然语言，协调须核查原始上下文。
- 发布属于范围外时也必须如实展示failed/partial/回滚等影响，release_impact包含实际核实证据且没有影响当前交付的未决项。最终确认只表示用户接受已独立通过的具体交付，不造发布成功。

## 发布证据和完整范围

是否要求发布由 completion_requirements 和关闭模式决定，与实际 release.kind/status 分开。普通源码、框架、工具、配置、文稿等manual交付，若批准标准release_required=false，可以保留实际package/service的unknown、unpublished、failed、partial、rolled_back或revoked并在最终确认中真实披露，不要求生成包/tag/Release/部署回执。不能把真实package/service伪改none以通过；completion_requirements.release_kind必须与实际对象一致，none仅用于确无发布对象且not_required的情况。发布状态变化需重新展示影响；不能复用旧状态的确认。

manual且release_required=true，或automatic/after_release时，才必须运行严格release检查：使用 [发布证据模板](../assets/templates/release-evidence.yaml) 原始回执及实际读取结论，与当前独立通过的delivery/code_baseline_digest及范围一致。

- package：实际公开非草稿版本及不可变制品/固定源码身份，只有tag/commit/push/build不算发布。
- service：核实指定environment部署/运行版本，repository Release不能替代运行证据。
- partial/failed/rolled_back/revoked/unknown/unpublished不满足严格发布门槛。范围内仍未完成，after_release始终不自动关闭；范围外披露且无影响当前交付遗留时可走manual。保留原成功/失败历史，已关闭后不自动重开。

绑定时明确 scope_coverage.mode=exclusive/shared、事项覆盖范围及用户确认。关闭前重读最新 Issue 正文/清单、已知关联事项及用户剩余范围说明（记录 inspected_at、evidence、remaining、unknown）；exclusive 也须验证确实覆盖全部。共享范围无法枚举/外部未确认保持打开，不能以取消事项或未披露排除项冒充完成。最新范围摘要必须与授权、当前已验范围及所选模式适用的发布范围匹配；新增输入、活动写调用、未完成增量、新外部剩余工作或身份变化立即暂停。

## 关闭门槛和接口

使用随包 `scripts/lifecycle.py`：`python3 <Skill目录>/scripts/lifecycle.py <检查名> <输入.json>`，检查名 config/target/authorization/release/close/confirmation/recovery/comment/outcome/key。仅使用标准库、只读 JSON（拒绝重复键），输出 JSON 和退出码；不写业务文件、不访问网络、不安装依赖。输入/错误契约以脚本函数及回归为准，模板字段与脚本同名；非完整上下文返回明确缺项。配置先校验工作空间与用户 policy_override 按字段合并后的有效值；缺省 binding/sync/close=off，未知字段/值、布尔值、off下的无效组合拒绝。

两个模式共同要求：有效目标/审批/独立通过，无活动写调用/待处理输入/未完成变更，整个Issue范围已核实完成，必要摘要已回读，无相关unknown/冲突，写前最后核对远端open、身份/范围/授权未变。manual额外需要上述本次最终确认；发布按批准标准适用。

自动关闭 mode=automatic 保持原有严格门槛，必须全部满足：

1. binding 当前完整可靠，策略 sync=milestones、close=after_release；授权覆盖当前事项/基线/全部范围，包含 comment+close 且未撤销。
2. 独立验收 passed 且与当前 delivery/code_baseline_digest 绑定；无活动写调用、未处理输入、未完成变更，审批有效。
3. 匹配实际发布及完整 Issue 范围，非失败/部分/回滚/撤销。
4. required_comments 非空，每条固定当前目标且 synced，回读证据存在；覆盖必要进度、独立验收、已核实发布事实，无未知/冲突的相关同步记录。
5. 发送前重新读远端身份、状态和最新范围，确认授权仍有效；远端 open 且无外部重开冲突。已 closed 不重复请求，只汇报外部或已归因关闭。

必要摘要可以一条评论承载多个事实：required_comments每项有固定target/status/receipt/verified_at，facts列出各kind/event_kind/event_id/evidence。manual必含progress、acceptance和confirmation；确认事实精确引用completion_confirmation.event_id及response_evidence，验收事实引用当前独立验收证据。只有要求发布时才额外要求release事实；不可用虚假no_release替代确认。旧单事实评论格式可读，automatic旧检查不迁移。每个事实均核对实际事件与允许event_kinds；不为多事实刷重复评论，复合摘要绑定一个真实源事件，稳定键不变，其他事实通过evidence引用。

先保存 operation=close、稳定 key、source_event、实际 authorization_ref、open→closed、验收/最终确认/适用发布/范围与必要评论证据和原始远端状态；回读本地记录后才调用一次状态写入。缺 close/state_read 能力返回具体限制，与评论分页/原文能力分别判断。写后读取同一 Issue 确认 closed，且原请求回执可归因才记 synced。必要评论未成功不得进入关闭，部分成功只恢复未完成步骤。

## 状态操作与 unknown 恢复

新 schema_version=2 的 key=SHA256(UTF-8紧凑JSON `[feature_id,revision,event_id,provider,host,repository,issue_number,operation]`)；operation=comment/close 分开，重试/换宿主不换 key。旧 schema1 评论 key 保持七项原算法，永不批量迁移。新记录沿用 issue-sync 目录与 sync_records 索引，close 不复制评论正文；expected_state 固定 open→closed，操作/目标/原事件/预期状态/正文或证据一旦发送不可改写。旧已成功评论被外部改动不静默重建。

状态：pending 尚未发送或终局证据证实未执行；sending 发送前已持久化；synced 有可复核同目标回读与归因；blocked 为缺能力/权限/身份/正文/授权冲突；unknown 为超时、发送中断、成功响应但回读失败或原请求执行情况不明。每次协调轮次每操作至多一次写，不循环重试。

恢复 sending/unknown 先查询原操作/请求回执与同目标当前事实，不先重发：

- 可归因原请求且当前 closed、目标与证据匹配，补 synced。
- closed 无原请求归因：保留原操作 unknown，remote_state=closed、attribution=external_or_unknown；报告当前已关闭，不声称本次成功。
- open 无服务端终局证据：保留 unknown，可能延迟或被重开，不能仅凭 open 回 pending。
- 有明确终局未执行/明确失败证据才回 pending；权限拒绝 blocked。用户就已展示的不确定风险作新具体决定时，另记录 decision_ref 和新尝试依据，不改旧事实。
- 外部重开、身份变化、内容/授权冲突停止写入，交用户核实，不自动覆盖人工操作。

评论保持完整分页、原始正文摘要与标识去重；缺完整分页不能判定“查无”。缺原文、状态读取、close 能力分别报告。同步策略停用、撤销授权、换绑时停止对应新写，原目标的 unknown/未决保留可见，不转发到新目标。关闭策略 off 停止自动 close，仍可执行有效评论授权。

## 历史和验收边界

首次启用/升级不补造历史。用户明确指定历史目标、原修订/事件、范围和允许操作后，核对旧任务、独立验收、manual所需的原最终完成确认及按原范围/模式适用的发布证据，只补真实事实；评论同时注明 original_occurred_at、原 revision、backfilled_at。授权 history_event_ids 明确列出允许旧事件，当前绑定/旧评论权不能替代。换绑不自动转发；旧包任务只读，不迁移审批或写旧 task。

自验与独立验收分别记录文件协议/隔离模拟、Codex 原生、OpenCode 原生、真实 GitHub、真实 GitLab、按场景适用的发布门。隔离 fixture 不调用平台；没有用户指定授权的测试 Issue 时平台门未验，不能认定上线就绪。Claude 不在本版实际宿主验收范围；另一个宿主/平台通过不替代本门。

普通无包/Release的manual关闭真实集成按当前已批准范围的实际平台分别核对绑定→阶段摘要→完整独立验收交付→真实用户最终确认→必要摘要→关闭回读。平台门的选择必须经本版明确审批，不默认要求每个项目同时有GitHub和GitLab目标。若当前只批准当前GitHub集成，GitLab契约/身份/授权/状态恢复与模拟支持保留，真实集成未验单列，不阻塞当前GitHub用例，也不得报为两平台真实通过或无条件跨平台GO。范围内全部必验项仍需通过；不能通过删除未完成项或更名局部结果绕过门槛。真实发行/部署及after_release全链路仅在另选该场景且具备目标授权时执行，不作为所有普通manual关闭的统一前提。

测试专用Issue可绑定范围明确、真实独立完整passed的已有测试交付，先核实精确身份、批准完整范围、全部适用验收和完整报告，再取得真实用户对该交付的最终确认及目标摘要/关闭许可，执行实际关闭回读，最后由独立测试汇总框架整体验收，避免要求框架先通过其尚未执行的平台关闭用例。旧目标若承载另一范围，须先向用户明确展示旧/新范围、旧范围尚未完成和框架整体仍待汇总的事实，取得具体范围调整与许可；产品审批不代替该远端决定，不授予编辑正文或重开。真实用户确认须晚于完整测试交付passed及展示，synthetic控制器确认不得用于真实Issue。

该关闭上下文始终绑定所选测试交付自身的真实身份、全部验收、精确范围和确认。不得把框架局部26/27、几个fixture或旧blocked重命名为完整passed；该范围内的failed/blocked/未验、活动写调用、待处理变化、共享剩余或unknown仍阻止关闭。关闭摘要明确“测试交付已确认，框架整体尚待独立汇总”，不生成框架feature_completed或框架最终确认；实际平台回读及归因通过后，独立测试才可判该平台用例，再核对框架当前全量批准范围与代码基线。框架最终确认及业务Issue关闭仍单独按原门槛办理，不因测试Issue已关而自动完成。
