# 项目配置

用户明确目标工作空间；根workflow.yaml不存在时使用默认配置，框架目录不是业务工作空间。workspace.features_dir默认agent-features，只接受不含..且不经链接越界的非空项目相对路径。需要持久跟踪的事项使用 `<features_dir>/<事项名称>/task.md`，一次性局部低风险小修不要求建文档，已有文档按职责引用，已有协调入口不转录副本；复杂事项按 [文档分工](documents.md#按复杂度选择文档) 拆分需求、设计及实施。

workflow.lock.yaml按 [包规则](package.md) 校验；协议3不建立业务配置快照、documents.yaml覆盖层或授权版本。旧配置/任务由原包解释，不批量重写。

支持schema_version=1；documents.provider默认local，也可为feishu；documents.feishu的parent_node_url为可选HTTPS父节点，write_enabled默认false。approval.channel=coordinator是已有对话确认渠道，不是每项工作强制审批。issue_tracking的binding为off/optional/required，sync为off/milestones，close为off/after_release，默认均off，须字符串而非布尔值。documents已有requirements/references/design/test_report来源项可继续只读引用（path或HTTPS url及access），不生成转录/覆盖层；read_write仍需具体授权。binding=off不得配置sync/close开启，sync=off不得配置after_release。发现重复键、未知字段或错误类型时，先说明问题，不隐式改用新的默认值。

外部文档配置仅说明来源及可用能力，不授予写入；实际目标、范围和权限按 [文档](documents.md) 与 [Issue](issue-tracking.md)核对。项目已有明确策略继续尊重，真实外部操作未知先恢复。凭据使用已有连接，不进入配置或任务文档。改变features_dir不自动搬迁历史。
