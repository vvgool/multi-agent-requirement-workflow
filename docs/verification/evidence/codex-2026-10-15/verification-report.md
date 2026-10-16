# Codex 实际宿主验证

本次为预设场景演练，只验证协调/产品闭环，所有审批均保留 null。没有开发、测试或发布。

真实协调 ID：`/root/coordinator_smoke`。真实产品 ID：`/root/coordinator_smoke/product_smoke`。宿主实际返回 canonical task_name，并非 UUID。1 次 spawn + 3 次 followup 串行复用同一已结束产品 Agent；新 run 独立。详见 host-evidence.yaml 及各 run/host.yaml。

| 场景 | 实际动作与证据 | 结果 |
|---|---|---|
| 完整输入 | 状态筛选 v1 / run-980f4e4d852e，真实产品 ready，逐项检查 AC-001..007 | requirement_review/waiting_user（随后由 v2 替代，v1 快照保留） |
| 恢复待审 | 重读 status、配置、来源及真实 SHA-256，重新展示相同评审；v1/resume-check.yaml、resume-display.md | run 数 1→1，没有再次派发 |
| 缺规则→答复 | 任务导出 run-efaae801d73b 真实返回 needs_input；questions.yaml 和 needs-input-state.yaml 保留。仅用明确标注的预设测试答复继续新 run-f9e40b087d1e | 新 run 真实 ready；requirement_review/waiting_user |
| 范围变更 | 状态筛选建立 v2/run-f37298459b42；实际调用产品；v1/status.snapshot.yaml 和原产物保留 | 真实 ready，逐条检查 AC-001..013；requirement_review/waiting_user。旧版逐文件摘要未变 |
| 飞书示例 | 读取夹具说明，确认是无实际可读正文的示例；revisions/v1/source-check.md、sources/manifest.yaml | draft/blocked；不发网络请求，无外部写入；没有虚构读取成功或能力缺失 |
| unknown 恢复 | isolated-fixtures/unknown.before/after.yaml：无 host ID、无法确认开始/结束，实际选择阻塞，不重复派发 | 协调者隔离场景核对通过 |
| 旧结果 | isolated-fixtures/stale.current/incoming/after.yaml：识别 v1 结果不匹配 v2，保留来件，根状态保持字节一致 | 未推进新版、未清新 active_run |
| 同名歧义 | isolated-fixtures/decisions.md：待澄清续改还是独立需求，不覆盖有效需求 | 未派发、未假定用户答复 |

unknown/旧结果/同名场景为独立状态夹具上的协调者行为和一次性断言，不是实际宿主故障注入，也不是框架程序强制保障。

待审内容：状态筛选 v2 保留三种状态筛选、默认/刷新复位、空态、不改任务状态，新增标题大小写不敏感子串搜索与筛选交集、空词不限、刷新清空；任务导出 v1 仅当前结果、UTF-8 CSV、标题/状态、显示顺序、特殊字符转义、空态禁用、tasks.csv、不联网。完整逐条验收与实际文稿在各 revisions/vN/requirements.md 和 review-display.md；本次停在真实用户审批前，不代答。

未验证：真实用户审批及审批后 development/blocked 迁移、飞书真实授权读写集成、Claude Code/OpenCode/其他宿主、开发/测试调度、生产发布。一次性场景检查脚本不作为交付 CLI 或调度器。
