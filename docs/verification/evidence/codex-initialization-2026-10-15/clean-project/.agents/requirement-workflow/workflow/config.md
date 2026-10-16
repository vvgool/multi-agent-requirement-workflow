# 配置与工作空间

协调 Agent 首次接单或恢复时读取本文。配置由 Agent 使用宿主文件工具解释，不要求安装解析器或运行 CLI。

## 定位顺序

1. 确定用户指定的绝对工作空间。只有用户明确采用当前目录时才使用 cwd。目标业务项目可以是工作空间自身或用户明确指定的另一个目录。
2. 读取工作空间根目录的 `workflow.yaml`，不存在时采用下述默认值。框架安装目录的配置不自动套用到其他工作空间。
3. 将 `workspace.features_dir` 相对工作空间根目录解析，默认 `agent-features`。只接受非空相对路径；拒绝 `..` 路径段、绝对路径及通过符号链接逃出工作空间的路径。
4. 在该目录按名称匹配需求，再读取当前 `revisions/vN/documents.yaml`，其中只允许 `documents` 字段。

框架路径、工作空间、需求目录、目标业务项目应在首次状态记录及每次派发中明确，不依赖子 Agent 继承 cwd。这些是当前宿主动态解析的运行信息，不是共享配置常量；搬迁时按 [portability.md](portability.md) 重新定位。

## 字段与默认值

```yaml
schema_version: 1
workspace:
  features_dir: agent-features
documents:
  provider: local
  feishu:
    parent_node_url: null
    write_enabled: false
approval:
  channel: coordinator
```

- `schema_version`：整数，当前仅接受 1。
- `documents.provider`：`local` 或 `feishu`。
- `documents.feishu.parent_node_url`：空值或指定知识库父节点的 HTTPS 链接，仅用于新文档存放。
- `documents.feishu.write_enabled`：布尔值，默认 false。
- `documents.requirements`、`references`、`design`、`test_report`：文档配置，references 是列表，其余是单个文档。每项字段为 `provider`（可选，继承默认）、`path`（本地）、`source_revision`（仅本地，可选）、`url`（飞书）、`access`（read/read_write，默认 read）。本地 path 默认相对当前修订版目录解析；source_revision 指定本需求中已有的来源修订版，须为不大于当前版的正整数，path 改为相对该来源修订版解析，仍禁止越界。飞书 url 使用 HTTPS 文档或知识库链接，不同时配置 path 和 url。
- `approval.channel`：首版仅接受 `coordinator`，在协调会话内明确确认。

按字段递归覆盖：内置默认值 → 工作空间配置 → 当前修订版文档配置；列表整体替换。空值不能用于清除必填字段。未知字段、重复键、类型不符、无法可靠读取的配置先报告具体问题，不创建或修改需求状态。凭据从宿主已配置的连接能力取得，不写进上述文件。

本地默认无外部需求正文时，以 input.md 为输入，由产品在本地产出需求。默认来源为飞书却没有 requirements.url 时，先请用户指定正文链接；仅配置父节点不代表已有需求正文。

`review/`、`runs/` 以及 input.md、documents.yaml、status.snapshot.yaml 是框架维护的修订内输出/控制位置，不接受作为配置的本地外部来源；先检查冲突，再创建输入和派发。用户原有的 requirements.md 可以作为只读来源，生成评审稿另存 review/requirements.md。每次写入仍检查目标是否与任一来源真实路径相同；相同则阻塞，不能因 access=read_write 而覆盖来源。存量历史产物按原索引读取，不批量移动或覆盖。

新修订版不能因缺少 documents.yaml 就丢失上一版来源。切版前读取上一版有效文档配置，按 [revisions.md](revisions.md) 显式延续 provider、来源定位和权限策略；来源无法核实时阻塞，不退回 local。默认值仅适用于没有历史文档策略的新需求。

## 权限与变更

读链接不授予写权限。更新已有飞书正文要求有效配置 write_enabled=true、文档 access=read_write 和实际宿主权限同时满足；创建还需父节点。一般参考文档只读。正文写入范围限于当前需求授权的产物，不自动评论、发消息或修改其他文档。

每次派发保存 `effective-config.yaml` 并记录其内容摘要。配置改变后重新读取、检查并展示影响；待审批记录失效。改变 features_dir 不自动迁移资料，旧新目录冲突时先解决冲突。改动需求范围的处理见 [revisions.md](revisions.md)，正文与审批见 [documents.md](documents.md)。

## 路径例子

框架根目录记作 F，两个业务工作空间分别记作 A、B。A 使用默认配置时，需求目录是 A/agent-features；B 配置 `features_dir: planning/features` 时，需求目录是 B/planning/features。它们都不从 F 推导业务需求位置，F、A、B 的实际目录由当前宿主确定。
