---
name: issue-tracking
description: Handle explicitly authorized existing Issue operations with minimal recovery facts in the current task document.
---

# 可选Issue操作

只在明确需要时读取目标，按 [Issue规则](../../workflow/issue-tracking.md)核实完整主机、仓库、编号与用户授权。默认关闭，读取链接不代表获得写入授权；不主动发消息或评论。

使用宿主已有连接，缺权限/能力报告实际缺口。写入前明确目标、操作和范围，关闭还须确认当前事项真正完成及允许关闭；发布需另行授权。共享Issue包含其他范围时不得因局部完成关闭全部。

用原生调用与远端回读确认实际结果；只在原任务文档保留恢复必需的目标、操作/回执及未决项，不新增绑定/事件/授权/result YAML或同步目录。写入结果未知时先查询原调用及远端状态，不盲目重发。同步失败不改变已发生的业务完成事实。

旧 lifecycle.py 和机器模板仅用于识别历史协议，不是协议3运行依赖，不用模拟检查冒充真实平台联调。
