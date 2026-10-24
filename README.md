# Multi-Agent Requirement Workflow

一次性、局部低风险且目标明确的小修由当前会话直接定位、最小修复、相关回归并简短返回，无需先建文档、清单、计划或宿主原生任务，也不默认另派角色、全量测试或无意义新增测试。原因未知先同一角色定位；需要跨会话恢复、交接或多步持久跟踪时才维护一份任务文档。复杂任务才增加必要方案、确认或独立验证。不提供CLI、后台调度服务或新的模式开关。独立一次性明确局部低风险且非旧任务续接时，直接遵循已载项目入口的授权/风险/unknown规则，不为小修读取锁、缓存、协调规则或完整框架包；需要框架协作/角色/恢复/安装才核验，旧任务始终原锁原包。

## 使用

在目标项目中要求Agent从 https://github.com/vvgool/multi-agent-requirement-workflow 获取框架，读取 `skills/setup-requirement-workflow/SKILL.md`，为当前宿主初始化，保留项目已有规则。首次安装固定实际完整提交和包摘要；已有锁按原锁恢复，不自动升级。

安装后直接说明目标，例如“调整签到奖励”；需要持久跟踪时，当前会话维护 `agent-features/签到奖励/task.md`：

```markdown
# 签到奖励

目标与范围：每账号每天首次签到奖励10积分，北京时间零点刷新。

- [ ] 调整奖励规则并验证首次、重复及跨日行为。

验证与未决项：待执行。
```

这是唯一当前入口。补充、修复、重试、普通继续与完成后续改都更新它；不生成v2/v3目录、重复需求稿或平行进度索引。需要保留重要旧结论时在文档简述或引用Git历史。现有历史目录保留，旧锁旧任务继续原包，不批量迁移。

## 协作边界

当前会话能完成就直接处理。信息不足才澄清，需要其他专长才委派原生产品/开发/测试/Bug角色，不强制产品→开发→测试。需要文档时只记录目标、范围、勾选任务、真实验证和必要待办，已有文档必要时合并结果；需要委派时宿主原生任务记录派发及结束事实，不另建status/task/host/result YAML、调用授权版本、delivery、逐轮快照、全项目文件哈希或重复事件索引。

范围或验收有分歧先确认；涉及付款、权限、数据删除或大范围共享逻辑变更，执行前确认具体范围，并由另一角色独立验证。普通已知小修无需统一边界评审。跨角色和中断恢复只交接目标、改动、已验结果、未决项及原生任务引用。确需避免验错版本时才保存相关文件版本或摘要，不扫描无关项目。外部写结果未知先查询原调用，查不清阻塞，不重复发送。

[协调](agents/coordinator-agent.md)负责必要路由；[产品](agents/product-agent.md)澄清规则；[开发](agents/development-agent.md)实现和自验；[Bug](agents/bug-agent.md)诊断修复；[测试](agents/testing-agent.md)按需独立验证。角色是可用专长，不是必经关卡。

## 安装与版本

已发布 [**0.6.0，协议3**](https://github.com/vvgool/multi-agent-requirement-workflow/releases/tag/v0.6.0)，本源码项目的Codex/OpenCode文件安装已升级，具体来源提交及摘要以workflow.lock.yaml为准。升级后的本项目原生角色激活需新会话验证，未沿用其他项目的通过回执。本次发布验证范围为Codex/OpenCode；Claude Code适配保留，真实运行未纳入本次验收。其他消费者不会自动升级。新包不得解释/续写旧task；显式升级必须先确认旧调用结束，保留旧包和历史，完成旧任务后才能采用新契约。

Codex、Claude Code、OpenCode共享规则，以各宿主原生角色薄文件适配；文件安装、真实角色激活和业务闭环分别报告。不能用一个宿主的结果替代另一个，也不能用模板存在证明原生调用。详情见 [包规则](workflow/package.md)、[安装Skill](skills/setup-requirement-workflow/SKILL.md)、[宿主适配](workflow/host-adapters.md)。

项目提交workflow.yaml、workflow.lock.yaml、AGENTS入口、选定宿主的四个薄角色及精确.gitignore区块；Claude按需增加CLAUDE桥接。完整包缓存在 `.agents/requirement-workflow-cache/<sha256>/`，安装回执及pending留本机。安装完整性校验仍保留，它不要求逐个业务任务建立机器账本。

可选外部文档/Issue按项目已有连接能力和用户具体授权使用，不主动发消息、评论或发布。配置默认外部写关闭，见 [配置](workflow/config.md) 与 [Issue](workflow/issue-tracking.md)。

## 源码验证

- `python3 -B -m unittest discover -s tests -p 'test_codex_registry.py'`：既有配置合并回归。
- `python3 -B scripts/verify-host-adapters.py --source-root . --scratch /已授权的空目录`：三宿主真实模板/正文与配置保留检查，不是原生激活。
- `python3 -B scripts/verify-rule-loading.py --source-root . --baseline-root /旧包目录`：规则体积与代表场景静态检查，不测token或耗时。

历史机器协议相关模板、实验和验证记录仅供原版本解释/维护，不是协议3入口。历史检查不证明新协议实际业务闭环。运行包含根framework.yaml、AGENTS.md、README.md、workflow.yaml、LICENSE及agents/、skills/、workflow/、templates/；scripts/tests/docs不进入业务运行包。

本项目使用 [MIT License](LICENSE)。
