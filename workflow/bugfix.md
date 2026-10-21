# Bug 修复入口、审批与循环

协调层管理以下路由，角色完成内容判断。共享核心门槛不因新增角色改变。既有无 bug 字段的任务和审批仍用原流程，不迁移历史。

## 三种入口

- 开发后：已有 development_baseline 或测试 failed，且缺陷在已批准范围内，stage=development 时可选择 bug；传 requirements_path、有效 approval_digest、defect_report_path、source_run_id/source_baseline 及原始症状证据。无缺陷不强制 Bug 调用。testing 的失败目标以 bugfix 记录为准，无 bugfix 时原开发修复仍可用。
- 开发中补充：原开发提出局部缺陷及交接需求，协调核实原写入任务已结束或安全停止且宿主确认结束，保存 bugfix.mode=supplement 和 continuation（原 run、剩余任务、交接范围、原基线）。只有一个 active_run，不让开发/Bug 并发写重叠范围。Bug 自验通过交独立测试，测试针对批准局部范围通过后清理该局部挂起状态，stage=development，回交原开发角色新 run（同角色宿主可复用）继续整体任务；携带修复变更、新基线、证据和未完成项，不标整个需求 completed。测试局部报告须明确 coverage_scope，最终整体仍须独立验收全部需求。
- 独立：明确只修 Bug 的请求可新建 workflow_kind=bugfix、bugfix.mode=standalone，stage=draft，直接派 bug、bug_purpose=boundary，不要求产品阶段。沿用 feature_id、修订、布局和 Issue 规则。确认前只能读取项目和本 run 输出，不写源码、测试或探针。信息缺失返回 needs_input；边界完整返回 boundary_ready，协调固化 documents/bug-boundary.md 后转 requirement_review/waiting_user 展示，待用户明确确认。

## 独立边界审批

边界含症状、预期行为、允许/禁止修改范围、逐项验证标准、必要环境、来源和限制。审批对象格式沿用 documents.md 的稳定评审摘要算法及 sources/配置绑定，将 requirements 正文位置替换为边界正文；pending_review.type=bug_boundary，approval.type=bug_boundary，记录 boundary_path 和原字节 sha256，task.boundary_path/boundary_digest 与之相符。review_digest 是包含 feature_id、修订、边界正文原字节摘要和有效配置依据的 review-manifest.yaml 原始字节 SHA256（验收包含在边界正文中），展示后任何变化使旧 pending_review 失效。普通“继续”、旧审批、澄清选择不算批准。已有 approval.type 缺失仅代表 requirements，不能拿来批准 standalone。

批准后 stage=development，bug_purpose=fix，requirements_path 可空但 boundary_path 必填；审批和边界摘要仍每轮核对。改预期/范围/标准进入新修订，经 Bug 重整边界并再次明确批准；已结束旧版与历史保留。confirmed 内容缺失或漂移时 blocked，不擅自修补审批。

## 派发与状态

bugfix 仅适用时添加：mode=post_development/supplement/standalone、purpose=boundary/fix、source_run_id、source_baseline、defect_report_path，supplement 另有 continuation；根状态/任务只保存本轮适用信息。task.role=bug，active_run.role=bug，原生映射读 host-adapters。task.bug_purpose 区分读边界和写修复。

| 结果 | 协调动作 |
| --- | --- |
| bug boundary_ready | 固化边界，requirement_review/waiting_user；展示并等待本版确认 |
| bug needs_input | 保持阶段，waiting_user；只转达明确问题 |
| bug ready | 保存 development_baseline.run_id=本 Bug run 及 code_baseline；testing/idle，派独立 testing |
| testing failed | 同一修订 development/idle，bug_purpose=fix，附失败报告和实际待修复基线；额度用尽则 blocked |
| testing passed | standalone/post_development：全部适用验收通过且无未决项/基线一致才 completed；supplement：只完成局部，回交原开发继续 |
| blocked / stale_task / unknown | 按公共契约保留现场、恢复或暂停，不重派/推进 |

测试任务沿用 development_run_id/development_baseline 字段，它们可指向 bug run，须读取该真实 task/result，不猜开发 run 名。测试对原始未最小化症状、真实回归接缝及适用边界/AC独立执行，不复制 Bug 自验作通过。

## 有限循环

development_attempt/max_development_attempts 在本修订共享，默认 3 次，首次开发或 Bug fix 新派发也算一次；boundary 只读调用不算。角色缺失或未真正发起不扣，unknown 先恢复；开发→Bug、测试失败→Bug、补充修复后重新派开发都不能重置额度。每次实际写阶段派发前检查上限，达到后 development/blocked、development_attempt_limit，等待用户明确调整或决策。角色内重跑反馈命令不算新派发，但无新证据、缺环境、无可判定复现、范围变更均需暂停而非耗尽算成功。

每轮自验/独立测试留不可覆盖的失败与成功证据；新修复产生新基线。没有用户授权不自动 commit/push、Issue 评论或发布。
