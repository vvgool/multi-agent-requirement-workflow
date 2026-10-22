# 状态与更新规则

协调 Agent 创建、更新或恢复需求时读取本文。字段模板见 [status.yaml](../templates/status.yaml)。这是 Agent 执行规范，不提供跨会话锁或事务保证；同一需求只允许一个协调会话。

## 字段

协议2的身份、调用、交付及恢复以[持续任务](continuous-tasks.md)为准；本文件仅维护根路由和写入顺序。协议1加载原锁定包，不将下列字段解释倒灌历史。

模板只保留通用字段。可选字段首次适用时添加，解除后可删除或置 null；缺失与 null 均不提供审批、基线、权限或阻塞解除证据。已存在的旧字段保持兼容，不批量清理历史。

- `feature_id`：内部唯一标识，首次新建时生成 UUID，改名、修订不改变；存量 REQ-001 等值保持不变。
- `title`、`workspace_root`、`target_project`：名称及当前宿主动态解析的绝对路径。后两者是本机运行定位信息；复制或迁移后须按 [portability.md](portability.md) 核对并重新绑定，不能当作框架安装约定。
- `requirements_revision`：正整数；当前修订版目录为 revisions/vN。
- `layout_version`：当前修订布局，0.5.0协议2新工作上下文为 4（0.4.0为3，协议1为2）；缺字段的存量为 1，规则见 [成果目录](output-layout.md)，不原地改变旧版。
- `content_baseline`：布局4当前实际展示的baseline_id（尚未评审为null）；审批、授权、交付及历史最小格式按[增量基线](incremental-changes.md#最小基线与历史)。进行中重审保留requirements_revision和attempt，不复制状态快照。
- `state_version`：每次成功更新递增，与需求修订号不同。
- `stage`：draft、requirement_review、development、testing、completed。
- `execution_status`：idle、running、waiting_user、blocked。
- `coordinator_session`：当前负责的真实会话标识；宿主不提供可核实标识时可省略，并遵守单会话约束，不编造标识。
- `active_run`：协议2为null或{task_id,role,revision,invocation_id,host,dispatch_status,framework}及真实可得host_task_id，指向host内本次调用；unknown/running先恢复，不代表持续任务结束。协议1仍按原run身份解释。
- `approval`：null 或含 feature_id、revision、baseline_id、review_digest、user_response、confirmed_at、source_session 的审批记录。人工确认后才填入；审批原文保留，时间和来源不能伪造。
- `pending_review`：null 或含 revision、baseline_id、review_digest、displayed_at 的待审记录；文件、来源和配置摘要统一从本版不可变 review manifest 核对，不在根状态复制。旧待审记录仍按原清单核验。
- `artifacts`：当前正式成果、入口及kind=task的持续目录；路径相对feature_dir。正式成果含kind/path/revision/task_id/delivery_id/sha256，来源从该任务result的具体交付按kind唯一解析。task目录只登记一次，详细文件不重复索引；旧run索引只读保留。
- `block_reason`：null 或具体原因，缺角色时另记录 `required_role`；`development_attempt`、`max_development_attempts` 为非负/正整数。实际写阶段尝试按 [routing.md](routing.md) 记录，缺角色时不消耗次数。
- `development_baseline`：{task_id,delivery_id,baseline_id,approval_digest,code_baseline}，绑定具体开发/Bug交付；testing授权source_delivery必须一致，精确内容见[基线](code-baseline.md)。
- `issue_tracking`：缺失/null 时按默认策略；启用后记录需求级选择、真实绑定、独立评论/关闭授权、范围覆盖、当前精确交付的最终完成确认事件引用、发布适用性、已核实远端状态和同步记录相对路径，见 [Issue 规则](issue-tracking.md)。同步摘要与业务 stage/execution_status 分开，不以远端评论代替审批。
事件以 events.jsonl 为准，新状态不写重复的 last_event；存量值只作历史线索，不作为当前路由依据。

## 迁移与条件

阶段选择、结果迁移和重试条件统一见 [阶段路由](routing.md)，范围变化见 [修订规则](revisions.md)。协调层只在真实任务结束、交接完整且适用审批/基线有效后推进；新版不继承审批，关键证据缺失不等同测试失败，历史完成记录保留。

## 每次更新

1. 先读根 status.yaml，核对 ID、当前修订、state_version 和活动任务。记录所读版本；另一个协调会话或写入冲突存在时暂停。
2. 持久化本步任务、结果或证据，所有路径指向实际存在的文件；输入/答复以input.md、授权以task、宿主调用事实以host、角色结论和详细证据索引以result为准。状态仅保存当前路由及必要身份/审批/基线绑定，事件引用事实位置和变化原因，不复制这些正文或完整产物清单。清空 active_run 前保留真实宿主任务信息。
3. 写入前再次核对 state_version；不一致时重读并停止本次写入，不能覆盖。
4. 更新根状态、递增 state_version并回读。业务阶段、审批、阻塞、交接和恢复事实追加 events.jsonl，使用同一版本、真实时间和证据路径；仅改变宿主调用状态的 unknown/running 更新由 host.yaml 与 active_run 保存，不重复追加事件。一次动作的路由、索引和计数合并一次状态更新，无变化的轮询/重读不写状态或事件；README仅按 [人工入口](output-layout.md#人工入口) 的触发条件更新，未触发时保留原入口及其摘要。
5. 若需 Issue 留痕，业务状态与事件已回读有效后按 [Issue 规则](issue-tracking.md) 调用支持 Skill。元数据更新同样递增版本，仅记 issue_sync_* 等控制事件，不递归生成业务留痕；同步失败不覆盖业务状态、审批或基线。
6. 任一步中断恢复时核对根状态、task/host/result 文件、host.yaml 和事件，同时核对 README 的 feature_index 归属/已知摘要及当前状态内容。已满足入口更新条件但未同步时只补派生入口，保持活动调用，不创建新任务；入口摘要不符或被用户编辑时保留原内容，在现有事件中记录入口同步冲突和位置，报告给用户，不把索引冲突写成业务调用已结束或擅自停止。入口变更后保存新的 feature_index 摘要；业务事件缺失时核查后补记 recovery 事件，host.yaml 已记录的 unknown/running 变化不补造事件；需 Issue 留痕的事实若有持久证据可还原原业务版本和事件内容，另按原 event_id 补齐一次原业务事件，recovery 仅引用它；无法还原时保留待核查，不从当前阶段猜造旧事件；发生矛盾则阻塞，不通过“补全历史”伪造成功。

发现未知或旧字段时先读已有记录说明，迁移只在确定语义且无活动任务时进行。恢复不因为 schema 存量差异而删除历史信息。

## 无新任务的澄清更新

按[持续澄清](continuous-tasks.md#协调与澄清)在既有input保留真实答复与处理映射；待答可无活动调用，持续任务仍可定位。新输入先保留待处理，已处理重复输入不执行。只写答复不等于处理完成；unknown先恢复。必要业务变化按上文合并状态/事件，无变化不写。方向选择不写approval，正式稿评审依旧。

## 开发方案展示

普通方案展示在当前对话说明，README按人工入口触发条件更新，不维护独立显示状态、递增state_version或追加展示事件；实质业务变化及交接仍按本文件更新。旧development_progress产物、展示状态及事件按 [存量通知协议](legacy-plan-notifications.md) 读取保留，不新增或迁移。

## 可选 Bug 字段

workflow_kind=bugfix 与 bugfix 对象只在 [Bug 入口](bugfix.md) 适用时添加，stage 仍五阶段，active_run.role 可为 bug，approval/pending_review.type 可为 bug_boundary。字段缺失沿既有 requirements 审批语义，不推导独立 Bug 授权。所有交接、计数、回交和写入仍仅协调维护。
