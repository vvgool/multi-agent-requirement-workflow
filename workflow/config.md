# 项目配置与外部边界

业务项目根目录下的 `workflow.yaml` 定义工作区路径与外部协同开关；文件不存在时按默认安全值运行（外部写入全部默认关闭）。

## 配置字段说明

```yaml
schema_version: 1
workspace:
  features_dir: agent-features        # 事项文档相对根目录，禁止包含 .. 或经符号链接越界
documents:
  provider: local                     # local | feishu
  feishu:
    parent_node_url: null             # 可选 HTTPS 节点链接
    write_enabled: false              # 默认关闭远端写入
approval:
  channel: coordinator                # 主会话对话确认渠道，具体门禁见 execution-contract.md#人工确认
issue_tracking:
  binding: "off"                      # "off" | "optional" | "required"（新项目默认 "off"）
  sync: "off"                         # "off" | "milestones"
```

- 发现重复键、未知字段或非法类型（如用布尔值代替 `"off"` 字符串，或 `binding: "off"` 却开启 `sync`）时先报告配置异常，不静默篡改用户配置文件。
- 修改 `features_dir` 仅作用于新事项，不自动搬迁已有历史目录。外部凭据走宿主既有连接环境，严禁写入配置文件或事项文档。

## 可选Issue关联

外部 Issue 与远端文档写入默认关闭（`binding: "off"`、`feishu.write_enabled: false`），日常不主动询问、读取远端或发表评论。仅当项目明确启用配置且用户显式要求关联或操作远端对象时，使用宿主既有连接按以下最小契约执行（缺权限或连接时如实报阻塞）：

- **精确身份与逐项独立授权**：以完整主机、仓库与 Issue 编号（或明确 `parent_node_url`）定位目标。读取参考链接或本地验收全绿绝不代表获得远端写权限；发表评论、同步里程碑、关闭 Issue、更新远端飞书文档或触发发布均须各自取得用户具体授权。
- **关闭前置范围核查**：执行关闭 Issue 前，必须核实当前事项已通过独立验收（`verified`）且完整覆盖该 Issue 全部诉求；若多个事项共享同一 Issue 且尚有未完成范围，严禁因局部完成而提前关闭。
- **远端回读、最小留痕与防重放**：每次远端写入后须回读远端状态确认真实生效，仅在当前事项 `task.md` 记录目标标识、回读结果链接与未决项，不创建本地同步目录或额外机器账本；调用超时或结果未知时先查询原请求与远端当前状态，查清幂等性前保持 `blocked`，严禁盲目重发或自动补偿。
