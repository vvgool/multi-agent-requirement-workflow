<!-- requirement-workflow:begin -->

## 需求协作入口

命中本入口时按本节推进协作（禁混用外部通用规格工作流 Skill，保留领域/工具专项 Skill 正常调用）：

1. **只读问答与小修直通（零核包开销）**：只读问答不建档；既有契约内明确低风险小修直接**定位 → 最小修改 → 相关回归 → 简短返回**（`0` 门禁、零建档、零派发、免读缓存）。
2. **先查代码与按需读缓存**：新功能、行为调整、跨模块契约或未知异常先查代码穿透 XY 表象，按需读 `.agents/requirement-workflow-cache/<lock.sha256>/`（见 `workflow.lock.yaml`；仅缺目录时：`self` 源跑 `skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root . --target-root .`，`git` 源按锁检出临时目录跑一次 `restore`）下 `workflow/{routing,execution-contract,documents,handoff,host-adapters,config}.md` 与 `skills/acceptance-testing/scripts/verify_feature.py`。
3. **前置审查与单次 `Spec Gate`**：持续事项以 `<features_dir>/<事项>/task.md` 为唯一控制面（优先宿主原生问答，选项须具明确授权语义；业务澄清或 `accepted:true` 不算批准；受控 `Spike` 禁触高危/非幂等写）。复杂事项后台贯通起草零状态头 `spec.md`、过异体四项审查与 `verify_feature.py --phase spec-gate`，再发起 **1 次 `Spec Gate`（`pending_approval → ready_to_implement`）** 结束本轮，未获批禁改正式源码。
4. **静音巡航与机械收口**：`ready_to_implement` 后连续推进（仅 3 类真阻塞可打断；可用 `--check-writes` 锁写集，2～3 次盲修熔断，未知外部写先查原调用禁重放）及**全新独立会话**反例验收；主会话单写 `task.md`（≤ 100 行）回写 `verified` 后**必跑通 `verify_feature.py --phase verified`** 方可交付。

<!-- requirement-workflow:end -->
