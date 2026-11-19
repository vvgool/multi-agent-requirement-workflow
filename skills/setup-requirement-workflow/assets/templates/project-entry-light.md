<!-- requirement-workflow:begin -->

## 需求协作入口

命中本入口时按本节推进协作（禁止混用外部通用规格工作流 Skill，保留领域/工具专项 Skill 正常调用）：

1. **只读问答与小修直通（零核包开销）**：只读问答不建档；既有契约内明确低风险小修直接**定位 → 最小修改 → 相关回归 → 简短返回**（`0` 门禁、零建档、零派发、免读下方缓存）。
2. **先查代码与按需读缓存**：新功能、行为调整、跨模块契约或未知异常先读代码穿透 XY 表象，并从 `.agents/requirement-workflow-cache/<lock.sha256>/`（见 `workflow.lock.yaml`；仅缺目录时按锁检出临时目录执行一次 `restore`）按需读取 `workflow/{routing,execution-contract,documents,handoff,host-adapters,config}.md`（含受控 `Spike`、3 类打断白名单与 `Contract-First` 分层验证）。
3. **前置审查与单次 `Spec Gate`**：需对齐事项以 `<features_dir>/<事项>/task.md` 为**唯一状态与批准控制面**（优先宿主原生问答，确认选项须具明确授权语义；业务澄清或 `accepted:true` 不算批准）。意图明确时复杂事项先后台贯通起草零状态头 `spec.md` 并过独立四项审查，再发起 **1 次 `Spec Gate`（`pending_approval → ready_to_implement`）** 并结束本轮，未获批禁改正式源码；高危变更先确认范围，未知外部写先查原调用禁重放。
4. **静音巡航与独立反例收口**：`ready_to_implement` 后连续推进实施、2～3 次盲修熔断及**全新独立会话**反例验收，达 `verified` 后交付（每单元回读 `AC`，主会话单写 `task.md` ≤ 100 行）。

<!-- requirement-workflow:end -->
