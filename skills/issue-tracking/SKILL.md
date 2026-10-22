---
name: issue-tracking
description: Use when coordinator-agent binds an existing GitHub/GitLab issue, synchronizes authorized lifecycle comments, closes a fully verified scope, or reconciles uncertain remote operations.
---

# Issue 绑定与关键事件留痕

协调主会话的可选支持 Skill，不新增角色或业务阶段。只绑定已有 Issue、追加获授权的关键事件评论并核对回执；业务阶段与本地证据仍由协调层维护。只在明确关闭授权且满足生命周期门槛时关闭；不新建 Issue、不自动重开、不改正文、标签、负责人或远程审批，不把远程评论当成需求确认。

## 入口与配置

先读 [Issue 规则](../../workflow/issue-tracking.md) 及当前根状态，合并工作空间策略与用户明确指定的需求级覆盖。binding=off 且没有本轮明确启用请求时，不询问、不创建记录、不访问远端。sync=off 时可只读核实绑定，不自动写评论或关闭；用户明确单次关闭须按生命周期契约另核对本次摘要及关闭许可；已保存的未确认写入保持原事实。

已有 active_run 先按协调路由处理；绑定判断不能覆盖运行中状态。恢复、续改先读已有选择，不重新提问。此 Skill 在主会话内执行，不占用业务 active_run，也不允许第二个会话并发同步同一需求。

## 判断与绑定

1. 未处理的 optional/required 策略，在首次产品派发前询问一次：不绑定（仅 optional）或指定已有 Issue。用户已明确提供目标时直接核实，不按标题猜 Issue。明确不绑定记录 skipped；没有答复则 pending/waiting_user，转达已保存问题，不反复询问或假装跳过。
2. 仅读取项目 Git remote 获取候选仓库；无 Git 或多个 remote 时不猜默认目标。已有 Issue 链接可绑定用户明确选定的跨仓库目标；须说明与业务仓库差异。按 [平台能力](references/providers.md) 读取真实 Issue，确认平台、主机、仓库和编号；不可读不标 bound。optional 时可由用户明确跳过，required 时保留当前 stage 并置 blocked（等用户提供链接时 waiting_user）。
3. 使用 [绑定模板](assets/templates/binding.yaml) 保存核实后的身份和真实选择。明确请求关联某链接只授予绑定，不自动授予评论；sync=milestones 还须有针对该目标、范围为关键节点摘要评论的明确授权，记录原文、真实时间和来源会话，无真实 ID 则 null。授权可在绑定时一次取得，不逐事件重复请求。未授权时保留已核实绑定、同步单独 blocked；绑定 required 不代表评论必须成功。
4. 模板中的 binding 只能来自真实读取（隔离探针须在报告注明模拟），不使用需求名代替仓库身份。Issue 正文只是关联资料；若要作为正式需求来源，显式配置 documents 并走原来源/评审规则，绑定本身不改变需求正文。

## 生命周期与校验

涉及新事件授权、发布适用性、用户最终完成确认、范围核对、关闭或历史补记时，先完整读取 [生命周期契约](references/lifecycle.md) 及其模板。按契约调用 `scripts/lifecycle.py` 的只读 JSON 校验接口核对配置、授权、本次最终完成确认、适用发布和关闭条件（路径相对本 Skill）；旧评论无需构造关闭上下文。校验器只处理输入，不读网络/写状态/发请求，证据真假由协调实际读取核对。没有能力时明确限制，不用 fixture 结论替代真实平台。

## manual完成确认

普通manual由协调执行，无统一打包或Release前提。先展示当前独立通过的精确基线/交付、全部适用验收、完整Issue范围及遗留，按生命周期契约核对 [最终完成确认模板](assets/templates/completion-confirmation.yaml) 的原话/来源/时间和展示快照；产品审批、继续及manual_summary_authorized不替代最终确认。comment+close许可可事先或同次取得，旧范围不扩权。release_required来自批准完成标准，真实package/service状态必须保留；automatic/after_release继续严格验证实际发布。进度/验收/确认可合并一条获授权摘要，事实证据各自可核实。

## 生成、发送与恢复

先按 Issue 规则保存本地业务状态和不可变事件快照，再读取 [同步流程](references/synchronization.md)，使用 [同步记录](assets/templates/sync-record.yaml) 和 [评论模板](assets/templates/comment.md) 准备本次留痕。

仅处理当前授权目标及允许的事件。远端读写使用宿主已配置的能力，缺能力或权限时记录实际原因；不安装工具、登录其他账号或把凭据写入项目。正文先落盘核对摘要和范围，远程写后读取评论验证，只有目标、事件标识和正文匹配才记 synced。

新事件与恢复按同一流程去重。每次协调轮次对每个事件/目标/操作至多一次写请求；pending 可在解除条件后补同步，sending/unknown 优先查询原写入，不盲重发。所有失败保持业务 stage、approval 和 development_baseline，不因 Issue 故障抹掉完成事实。

## 返回与边界

返回绑定选择、实际目标、同步回执或待补原因及所需用户动作。绑定与同步元数据由协调层按 state_version 规则更新；同步自身的事件不再次触发留痕。需求 README 和完成汇报按 Issue 规则分别展示本地技术验收、用户最终确认、关闭许可、发布适用性/实际状态、远端状态、最新已核实进度链接及同步待办，不重复评论正文。

关闭策略改为 off 只停止后续自动关闭；停用同步或撤销权限停止对应后续远程操作，保留历史、授权及未确认记录，不伪称已同步。换绑/撤销授权先保存真实决定，暂停旧目标待发记录，不把它们改写或转发到新目标。更多边界见 Issue 规则。仅完成文件检查或模拟交互不能声称真实 GitHub/GitLab 集成通过。

## 当前范围与专用测试目标

真实平台门只按当前明确批准范围选择；当前GitHub用例不要求额外构造GitLab目标，GitLab契约/模拟支持保留且真实未验单列，不外推跨平台通过。测试专用目标可采用真实独立完整通过的既有测试交付，按生命周期“历史和验收边界”先核对旧/新范围许可、完整报告与真实用户最终确认，再执行平台关闭回读，最后独立汇总框架；局部fixture、旧blocked或synthetic确认均不能替代，也不自动完成框架事项。
