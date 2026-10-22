# Bug 修复入口、审批与循环

协调层管理以下路由，角色完成内容判断。共享核心门槛不因新增角色改变。既有无 bug 字段的任务和审批仍用原流程，不迁移历史。

## 三种入口

- 开发后：普通缺陷默认原开发持续任务处理；只有复杂定位或确需专门诊断才启用Bug。已有 development_baseline 或测试 failed，且缺陷在已批准范围内，stage=development 时可选择 bug；传 requirements_path、有效 approval_digest、defect_report_path、source_delivery及source_baseline 及原始症状证据。无缺陷不强制 Bug 调用。testing 的失败目标以 bugfix 记录为准，无 bugfix 时原开发修复仍可用。
- 开发中补充：原开发提出局部缺陷及交接需求，协调核实原写入任务已结束或安全停止且宿主确认结束，保存 bugfix.mode=supplement 和 continuation（原task及交付、剩余任务、交接范围、原基线）。只有一个 active_run，不让开发/Bug 并发写重叠范围。Bug 自验通过交独立测试，测试针对批准局部范围通过后清理该局部挂起状态，stage=development，回交原开发持续任务（新调用优先复用原Agent）继续整体任务；携带修复变更、新基线、证据和未完成项，不标整个需求 completed。测试局部报告须明确 coverage_scope，最终整体仍须独立验收全部需求。
- 独立：明确只修 Bug 的请求可新建 workflow_kind=bugfix、bugfix.mode=standalone，stage=draft，直接派 bug、授权purpose=boundary，不要求产品阶段。沿用 feature_id、修订、布局和 Issue 规则。确认前只能读取项目和本任务输出，不写源码、测试或探针。信息缺失返回 needs_input；边界完整返回 boundary_ready，协调固化 documents/bug-boundary.md 后转 requirement_review/waiting_user 展示，待用户明确确认。

## 独立边界审批

边界含症状、预期行为、允许/禁止修改范围、逐项验证标准、必要环境、来源和限制。审批对象格式沿用 documents.md 的稳定评审摘要算法及 sources/配置绑定，将 requirements 正文位置替换为边界正文；pending_review.type=bug_boundary，approval.type=bug_boundary，记录 boundary_path 和原字节 sha256，当前授权boundary_path/boundary_digest 与之相符。review_digest 是包含 feature_id、修订、边界正文原字节摘要和有效配置依据的 review-manifest.yaml 原始字节 SHA256（验收包含在边界正文中），展示后任何变化使旧 pending_review 失效。普通“继续”、旧审批、澄清选择不算批准。已有 approval.type 缺失仅代表 requirements，不能拿来批准 standalone。

批准后 stage=development，授权purpose=fix，requirements_path 可空但 boundary_path 必填；审批和边界摘要仍每轮核对。布局4的boundary_path指当前批准reviews基线内不可变bug-boundary.md，baseline_id与approval_digest贯通fix授权、交付和独立测试；documents只展示当前稿。布局4同目标未完成改预期/范围/标准按[增量契约](incremental-changes.md)原目录经 Bug 重整边界并再次明确批准，原bug任务追加授权；完成后才新修订；已结束旧版与历史保留。confirmed 内容缺失或漂移时 blocked，不擅自修补审批。

## 派发与状态

bugfix 仅适用时添加：mode=post_development/supplement/standalone、purpose=boundary/fix、source_delivery、source_baseline、defect_report_path，supplement 另有 continuation；根状态/任务只保存本轮适用信息。task.role=bug，active_run.role=bug，原生映射读 host-adapters。当前授权purpose 区分读边界和写修复。

| 结果 | 协调动作 |
| --- | --- |
| bug boundary_ready | 固化边界，requirement_review/waiting_user；展示并等待本版确认 |
| bug needs_input | 保持阶段，waiting_user；只转达明确问题 |
| bug ready | 保存 development_baseline={task_id,delivery_id,code_baseline}绑定本Bug交付；testing/idle，派独立 testing |
| testing failed | 同一修订 development/idle，授权purpose=fix，附失败报告和实际待修复基线；额度用尽则 blocked |
| testing passed | standalone/post_development：全部适用验收通过且无未决项/基线一致才 completed；supplement：只完成局部，回交原开发继续 |
| blocked / stale_task / unknown | 按公共契约保留现场、恢复或暂停，不重派/推进 |

测试本次授权source_delivery={task_id,delivery_id}可绑定真实Bug交付，读取对应task/result的指定delivery，不猜开发run名。独立执行原始症状与适用回归，不拿Bug自验作独立通过。

## 有限循环

development_attempt/max_development_attempts按[持续任务额度](continuous-tasks.md#尝试额度)在开发/Bug共享；首次写阶段及独立失败后的下一实际修复尝试计一次，同次角色转交、回开发、自验重跑/恢复不重扣不清零。boundary只读不计；unknown先核实。达到上限blocked等待明确决策，不换任务绕额度。

每轮自验/独立测试留不可覆盖的失败与成功证据；新修复产生新基线。没有用户授权不自动 commit/push、Issue 评论或发布。

协议2边界与fix持续同一bug任务，确认后追加明确授权版本，旧调用仍绑定旧权限；source_run_id等仅旧协议保留，协议2用source_delivery。
