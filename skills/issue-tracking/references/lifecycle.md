> 历史协议1/2及严格平台审计参考；协议3与协议4日常流程默认不调用此机器流程，仅作显式开启远端 Issue 严格关闭/回执校验时的只读标准库契约说明保留。旧任务只读其原锁定包，不迁移或改写历史记录。

# Issue 生命周期只读门禁参考

先阅读 [可选 Issue 关联规则](../../../workflow/config.md#可选issue关联) 与 [Issue Skill](../SKILL.md)。本页说明随包保留的确定性检查器 `scripts/lifecycle.py` 及其配套模板夹具的输入/验证边界；日常协议 4 事项仅在原 `task.md` 记录远端目标、回执与未决项，不建立本地事件流或机器账本。

## 1. 授权、完成确认与发布证据分离

技术独立验收通过、用户最终交付确认、远端 `comment/close` 授权与真实发布是四项独立事实，互不替代：
- **逐项授权**：按 [授权模板](../assets/templates/authorization.yaml) 绑定精确 `provider / host / repository / issue_number`、允许的 `operations`（`comment` / `close`）与 `event_kinds`，产品需求或设计批准不授予远端写权限。
- **手动关闭最终确认**：`mode=manual` 关闭前按 [最终完成确认模板](../assets/templates/completion-confirmation.yaml) 核实 `passed_at <= presented_at <= confirmed_at`、全部必验 `AC` 已通过、无未决阻塞，且已覆盖该 Issue 完整范围（共享 Issue 仍有剩余范围时禁止关闭）。
- **发布证据核验**：仅当批准完成条件要求发布（`release_required=true` 或 `close=after_release`）时，按 [发布证据模板](../assets/templates/release-evidence.yaml) 核实公开非草稿版本或目标环境真实运行回执；无需发布的源码/文稿交付如实保留原发布状态，不伪造 `succeeded`。

## 2. 确定性检查器调用与未知状态防重放

```bash
python3 -B <Skill目录>/scripts/lifecycle.py <config|target|authorization|release|close|confirmation|recovery|comment|outcome|key> <输入.json>
```

- 仅使用 Python 标准库只读校验 JSON（拒绝重复键与非法组合，缺省 `binding/sync/close="off"`），不访问网络、不改写业务文件。
- **未知状态恢复**：发送超时、断连或回读失败统一记为 `unknown`；恢复时必须先查询原请求回执与同目标远端当前状态——可归因且远端已闭合才记 `synced`，远端闭合但无原请求归因记 `external_or_unknown`，服务端终局未确认前保持阻塞，严禁盲目重发或循环重试。
