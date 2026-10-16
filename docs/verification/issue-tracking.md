# Issue 绑定与留痕验证

> 本报告记录执行当时的版本与验证范围；当前能力及后续记录见 [验证索引](README.md)。不将旧统计或未验证项改写为本轮通过。

验证日期：2026-10-15。范围为协调层可选 [issue-tracking Skill](../../skills/issue-tracking/SKILL.md)，本轮未访问真实远程 Issue。

## 实现与配置

[workflow.yaml](../../workflow.yaml) 默认 binding="off"、sync="off"。支持已有 GitHub/GitLab Issue 绑定和经目标授权的关键节点摘要评论；不新增角色、工作流 CLI 或后台任务。[规则](../../workflow/issue-tracking.md) 与协调路由、状态、修订、人工入口及安装快照已接通。

仅实际启用时在根状态保存关联信息，发送事件才创建 `.workflow/issue-sync/<sync_key>/record.yaml` 与 `comment.md`。人工查看需求根 README 的 Issue 链接与待补/未知提示，无需逐一阅读同步记录。

## 静态检查

- 5 个 Skill 通过 skill-creator quick_validate。
- 56 个核心文件检查：147 个本地 Markdown 链接可达，无作者机器绝对路径。
- 全仓库 YAML 164、JSON 51、JSONL 7、TOML 18 个文件可解析，YAML 无重复键；默认 Issue 开关确认为字符串。

## 独立行为验证

独立 Agent 阅读 Skill 后，在系统临时目录生成状态、正文、真实 SHA-256、模拟回执及请求日志，执行 15 个协议模拟场景，断言全部通过：

| 场景 | 观察结果 |
| --- | --- |
| 默认关闭、optional 跳过后续改 | 无远程请求；保留选择，不重复询问 |
| required 首次未绑定；testing/development 中途开启 | 不派发业务角色，保留当前阶段及已有审批/基线 |
| 已绑定但未授权评论 | 同步 blocked，无 POST，不回退业务 |
| GitHub 发送/回读、同事件继续 | 核对正文及目标；只创建一次 |
| 写入超时后发现原评论 | 查询并核实后 synced，无第二次 POST |
| 未知写入后完整查询为空 | 仍为 unknown，不凭空判定失败或重发 |
| 权限拒绝 | 同步 blocked；业务状态、审批、基线和开发次数保持 |
| GitLab 多级子组 | 使用完整项目路径及项目内 iid，未误用全局 id |
| 换绑或关闭 | 旧目标停发，记录原目标；未知事实仍在入口提示 |
| 同标识正文冲突或多条匹配 | blocked，不修改、删除或再发评论 |

原始模拟工作区在本次会话系统临时目录 `issue-forward-eval-final`，不作为安装依赖、不复制进共享框架。

## 证据限制

以上为静态检查及独立协议模拟，不是运行时代码测试或完整宿主集成通过。真实 GitHub/GitLab 权限和读写、原生宿主工具调用、已知 comment ID 的直接恢复、解除 blocked 后的重试、全部重入路径、跨进程中断及并发冲突未验证。框架仍要求同一需求单协调会话，不承诺平台级严格只写一次。
