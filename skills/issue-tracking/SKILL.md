---
name: issue-tracking
description: Handle explicitly authorized existing Issue operations with minimal recovery facts in the current task document.
---

# 可选 Issue 操作

本能力默认关闭（`binding: "off"`）。仅当项目明确启用且用户要求关联或操作远端 Issue 时，按 [可选 Issue 关联规则](../../workflow/config.md#可选issue关联) 核实完整主机、仓库、Issue 编号与用户逐项授权；读取参考链接绝不代表获得评论或关闭授权。

1. **逐项授权与范围核查**：使用宿主既有连接，缺权限或能力时如实报告缺口。发表评论、关闭 Issue、触发发布须各自取得具体授权；关闭前还须核实当前事项已通过独立验收且覆盖该 Issue 全部范围（共享 Issue 含未完成范围时严禁因局部完成而关闭）。
2. **远端回读与未知防重放**：写入后通过远端回读确认真实结果，仅在原 `task.md` 保留目标编号、操作回执与未决项，不新建本地同步目录或日常机器账本；调用超时或结果未知时先查询原请求与远端当前状态，查清前保持阻塞，严禁盲目重发。
3. **可选严格契约夹具说明**：包内 `scripts/lifecycle.py`、[生命周期契约](references/lifecycle.md) 与 `assets/templates/*.yaml` 仅作为显式启用严格平台关闭/回执审计或兼容历史校验时的确定性检查工具，协议 4 日常业务流程零依赖，且严禁用本地模拟检查冒充真实平台联调通过。
