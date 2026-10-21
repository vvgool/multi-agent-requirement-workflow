# 状态与更新规则

协调 Agent 创建、更新或恢复需求时读取本文。字段模板见 [status.yaml](../templates/status.yaml)。这是 Agent 执行规范，不提供跨会话锁或事务保证；同一需求只允许一个协调会话。

## 字段

模板只保留通用字段。可选字段首次适用时添加，解除后可删除或置 null；缺失与 null 均不提供审批、基线、权限或阻塞解除证据。已存在的旧字段保持兼容，不批量清理历史。

- `feature_id`：内部唯一标识，首次新建时生成 UUID，改名、修订不改变；存量 REQ-001 等值保持不变。
- `title`、`workspace_root`、`target_project`：名称及当前宿主动态解析的绝对路径。后两者是本机运行定位信息；复制或迁移后须按 [portability.md](portability.md) 核对并重新绑定，不能当作框架安装约定。
- `requirements_revision`：正整数；当前修订版目录为 revisions/vN。
- `layout_version`：当前修订布局，新增需求/新版为 2；缺字段的存量为 1，规则见 [成果目录](output-layout.md)，不原地改变旧版。
- `state_version`：每次成功更新递增，与需求修订号不同。
- `stage`：draft、requirement_review、development、testing、completed。
- `execution_status`：idle、running、waiting_user、blocked。
- `coordinator_session`：当前负责的真实会话标识；宿主不提供可核实标识时可省略，并遵守单会话约束，不编造标识。
- `active_run`：null 或含 run_id、role、revision、dispatch_status、host_task_id 的对象。新锁定安装另含 host、framework 四字段身份（见 [包规则](package.md)）；历史active_run不补写。新 run 的 dispatch_status 只写 unknown 或 running：调用前持久化 unknown，得到宿主返回后保存真实任务标识并改为 running；派发步骤见 [交接](handoff.md#派发)。存量 prepared 仍须先核实调用，不据此重派。
- `approval`：null 或含 feature_id、revision、review_digest、user_response、confirmed_at、source_session 的审批记录。人工确认后才填入；审批原文保留，时间和来源不能伪造。
- `pending_review`：null 或含 revision、review_digest、displayed_at 的待审记录；文件、来源和配置摘要统一从本版不可变 review manifest 核对，不在根状态复制。旧待审记录仍按原清单核验。
- `artifacts`：只索引当前正式成果、需求入口和各 run 目录（kind: run），含 kind、path、revision、run_id（适用时）；path 默认相对需求目录。布局2的 run 目录须为所标注revision的 `.workflow/runs/<run_id>/`，普通目录且无链接越界；task.yaml、host.yaml、result.yaml和详细证据按该run内实际文件及result索引读取，不逐项重复登记。调用前保存 unknown 时登记一次目录入口；目录内文件仍逐项核对普通文件及授权路径，缺文件不能从目录索引推断已派发或已完成。旧索引沿用，不批量删改。正式文稿记录自身 sha256；来源由该 revision/run_id 对应的 result.artifacts 按 kind 定位，路径和来源摘要不再复制到根状态。来源须唯一且可核验，按目录规则更新当前版有效项并保留原 result；旧 source_path/source_sha256 仍须核对，不追溯删除。设计维护中在需求目录外的产物必须标记 `base: workspace`，不能作为角色输出例外。
- `block_reason`：null 或具体原因，缺角色时另记录 `required_role`；`development_attempt`、`max_development_attempts` 为非负/正整数。开发调用次数按 [routing.md](routing.md) 记录，缺角色时不消耗次数。
- `development_baseline`：null 或当前待测开发 run_id、代码标识和证据路径；每次开发完成后更新，测试必须绑定该基线；结构与兼容见 [代码基线契约](code-baseline.md)。
- `issue_tracking`：缺失/null 时按默认策略；启用后记录需求级选择、真实绑定、评论授权和同步记录相对路径，见 [Issue 规则](issue-tracking.md)。同步摘要与业务 stage/execution_status 分开，不以远端评论代替审批。
事件以 events.jsonl 为准，新状态不写重复的 last_event；存量值只作历史线索，不作为当前路由依据。

## 迁移与条件

阶段选择、结果迁移和重试条件统一见 [阶段路由](routing.md)，范围变化见 [修订规则](revisions.md)。协调层只在真实任务结束、交接完整且适用审批/基线有效后推进；新版不继承审批，关键证据缺失不等同测试失败，历史完成记录保留。

## 每次更新

1. 先读根 status.yaml，核对 ID、当前修订、state_version 和活动任务。记录所读版本；另一个协调会话或写入冲突存在时暂停。
2. 持久化本步任务、结果或证据，所有路径指向实际存在的文件；输入/答复以input.md、授权以task、宿主调用事实以host、角色结论和详细证据索引以result为准。状态仅保存当前路由及必要身份/审批/基线绑定，事件引用事实位置和变化原因，不复制这些正文或完整产物清单。清空 active_run 前保留真实宿主任务信息。
3. 写入前再次核对 state_version；不一致时重读并停止本次写入，不能覆盖。
4. 更新根状态、递增 state_version并回读。业务阶段、审批、阻塞、交接和恢复事实追加 events.jsonl，使用同一版本、真实时间和证据路径；仅改变宿主调用状态的 unknown/running 更新由 host.yaml 与 active_run 保存，不重复追加事件。一次动作的路由、索引和计数合并一次状态更新，无变化的轮询/重读不写状态或事件；README仅按 [人工入口](output-layout.md#人工入口) 的触发条件更新，未触发时保留原入口及其摘要。
5. 若需 Issue 留痕，业务状态与事件已回读有效后按 [Issue 规则](issue-tracking.md) 调用支持 Skill。元数据更新同样递增版本，仅记 issue_sync_* 等控制事件，不递归生成业务留痕；同步失败不覆盖业务状态、审批或基线。
6. 任一步中断恢复时核对根状态、run 文件、host.yaml 和事件，同时核对 README 的 feature_index 归属/已知摘要及当前状态内容。已满足入口更新条件但未同步时只补派生入口，保持活动调用，不创建新 run；入口摘要不符或被用户编辑时保留原内容，在现有事件中记录入口同步冲突和位置，报告给用户，不把索引冲突写成业务调用已结束或擅自停止。入口变更后保存新的 feature_index 摘要；业务事件缺失时核查后补记 recovery 事件，host.yaml 已记录的 unknown/running 变化不补造事件；需 Issue 留痕的事实若有持久证据可还原原业务版本和事件内容，另按原 event_id 补齐一次原业务事件，recovery 仅引用它；无法还原时保留待核查，不从当前阶段猜造旧事件；发生矛盾则阻塞，不通过“补全历史”伪造成功。

发现未知或旧字段时先读已有记录说明，迁移只在确定语义且无活动任务时进行。恢复不因为 schema 存量差异而删除历史信息。

## 无新 run 的澄清更新

draft 阶段的答复按 [产品路由](routing.md#产品澄清答复) 处理；记录格式与累计交接见 [交接](handoff.md#澄清记录与再次派发)。没有新调用仍须使动作可追踪：input.md 追加真实答复和决策依据；仍有有效未决问题且无待处理变化/分析/产稿时，根状态保持 draft/waiting_user，active_run=null；events.jsonl记 clarification_recorded 或 clarification_waiting，引用输入记录及来源run/result，仅记动作和原因；问题、答复及待处理位置以input记录为准。事件可关联来源 run，但不得伪称发生新调用或创建空 run。

存在 active_run 时保留其身份、dispatch_status 和当前真实执行状态，追加新答复并以 clarification_pending 标记待处理，不清除任务、不改为无任务等待。确认原调用结束且结果交接核对后，再将累计答复和结果一并按路由重新决策，处理完成追加处理记录；真实 host 结束信息按原交接保存。

上述持久化更新全部遵循“每次更新”：读取及再次比较 state_version、递增、回读、按需入口同步、同版本事件与冲突即停；不以只写 input.md 代替状态协议。恢复时先从状态、input.md、事件及来源结果重建当前有效问题、累计答复和待处理项，优先恢复未完成的分析/产稿决策；最新消息为空、重复或“继续”不能清除已保存的待处理动作。无活动任务但尚待分析/产稿时保留 clarification_pending 及对应输入引用，按路由继续；仅保存输入或准备派发不记为处理完成。已处理记录须关联覆盖这些输入的真实 run/适用结果；已有调用先核实，已有适用结果接续交接，不重复执行旧动作；状态已写而事件缺失按原恢复规则核查补记，矛盾时阻塞，不靠重派消除矛盾。无新答复的重复展示可以引用已有记录，不凭空产生答复或 run。

澄清选择不写 approval/pending_review；产品 ready 后仍按文档规则展示并取得本版明确审批。已批准内容变化按修订规则保留历史并重新评审。

## 开发方案展示

普通方案展示在当前对话说明，README按人工入口触发条件更新，不维护独立显示状态、递增state_version或追加展示事件；实质业务变化及交接仍按本文件更新。旧development_progress产物、展示状态及事件按 [存量通知协议](legacy-plan-notifications.md) 读取保留，不新增或迁移。

## 可选 Bug 字段

workflow_kind=bugfix 与 bugfix 对象只在 [Bug 入口](bugfix.md) 适用时添加，stage 仍五阶段，active_run.role 可为 bug，approval/pending_review.type 可为 bug_boundary。字段缺失沿既有 requirements 审批语义，不推导独立 Bug 授权。所有交接、计数、回交和写入仍仅协调维护。
