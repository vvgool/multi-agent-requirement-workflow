# GitHub / GitLab 平台能力

运行时先发现宿主已有的连接器/MCP/API 工具，按该能力实际说明使用；已配置的 gh/glab 等也可使用，但不是框架依赖，不自动安装、登录或切换主机。没有相应能力如实记录。只使用核实过的主机及仓库，不把凭据传给从正文推断的地址。

| 平台 | 绑定核验 | 评论能力 |
| --- | --- | --- |
| GitHub（含可核实的企业实例） | 读取完整 owner/repo 下的 issue_number，核对 html_url、number、仓库身份；含 pull_request 的资源拒绝为 Issue 绑定 | 列出 Issue comments（全部分页）、创建一条 comment、按 comment ID 读取验证 |
| GitLab（含可核实的自建实例） | 读取完整 namespace/project（可含多级子组），取得真实 project_id；使用项目内 iid，不能把全局 id 当 iid；拒绝 MR | 列出该 Issue notes（全部分页）、创建普通 note、按 note ID 读取验证；系统 note 不当成我们创建的普通评论 |

用户提供的 HTTPS Issue URL 用于定位，最终以真实返回的主机、仓库和编号为准。Git remote 只给候选，不能将所有自建主机猜成 GitLab；托管在路径前缀下的实例按已配置 API 能力定位，不从网页路径自行拼凭据请求。仓库不匹配需核实用户选择，不自动改用 origin。

读取成功不证明有评论权限。写回须满足绑定、配置及明确目标授权，使用真实能力检查并记录实际失败，不为“探测写权限”发送无意义测试评论。结果核验需要原始 Markdown body、ID 和目标归属；能力无法读原文或完成分页时，不声称已查无重复。

官方接口依据（核对日期 2026-10-15；宿主实际版本仍须确认）：

- [GitHub Issue API](https://docs.github.com/en/rest/issues/issues)：读取单个 Issue，并注意 Issue 端点也可能返回 PR。
- [GitHub Issue comments](https://docs.github.com/en/rest/issues/comments)：列出、创建和读取 comment。
- [GitLab Issues API](https://docs.gitlab.com/api/issues/)：project 与 issue_iid 的身份语义。
- [GitLab Notes API](https://docs.gitlab.com/api/notes/)：Issue notes 的列表、创建和读取。

本文件只规定所需操作与核验，不要求某个固定工具名、模型、认证方案或 API 版本；其他平台首版返回 unsupported_issue_provider，不套用以上格式。隔离模拟可验证规则，真实权限/网络/读写须单独验证。

## 状态能力（仅按生命周期契约获授权后）

分别发现同一完整目标的状态读取、open→closed写入及原请求回执读取能力。GitHub按真实Issue identity更新state=closed；GitLab按真实project与iid执行close状态操作；字段和调用形式必须按宿主现有工具说明核实，不从评论能力推断关闭能力。缺任一能力报告具体限制。状态只表达open/closed，业务阶段用摘要评论，不要求Project/看板/标签。重定向、PR/MR、global id/iid冲突拒绝，不自动重开。返回成功仍须同目标回读，归因不足保持unknown。
