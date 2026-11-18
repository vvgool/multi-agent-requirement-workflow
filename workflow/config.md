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

- 发现重复键、未知字段或非法类型（如用布尔值代替 `"off"` 字符串，`binding: "off"` 却开启 `sync`）时先报告配置异常，不静默篡改用户配置文件。
- 修改 `features_dir` 仅作用于新事项，不自动搬迁已有历史目录。外部凭据走宿主已有连接环境，严禁写入配置文件或事项文档。

## 可选Issue关联

默认关闭（`binding: "off"`），不主动询问、读取远端或发表评论。仅当项目明确配置 `required`，或配置 `optional` 且用户明确要求关联/操作 Issue 时，才按需读取 [Issue Skill](../skills/issue-tracking/SKILL.md)。

- **明确身份与逐项授权**：以完整主机、仓库与 Issue 编号定位目标；发表评论、关闭 Issue、触发发布均须各自获得用户具体授权，用户仅提供参考链接或本地测试全绿均不代表获得远端写入/关闭授权。
- **最小留痕与防重放**：确有真实远端写入时，仅在原 `task.md` 记录目标编号、调用结果链接与未决状态，不新建本地同步目录或重复机器账本；远端调用结果未知时先查询原请求与远端状态，查清前保持阻塞，严禁盲目重发。
