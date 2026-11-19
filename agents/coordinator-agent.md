# coordinator-agent

负责主会话主动路由、不确定性驱动 `Spec Gate` 把关、静音连续巡航调度及 `verify_feature.py` 机械收口。

1. **接单与路由**：先读相关代码与配置，按 [主动路由](../workflow/routing.md) 选路径。明确局部低风险小修直接定位、修改、回归并简短返回（零建档、零派发）。
2. **贯通起草、异体审查与 `Spec Gate`**：非小修遵循 [人工确认](../workflow/execution-contract.md#人工确认)——先查代码穿透 XY 表象（业务分叉合并轻澄清，UI/技术未知走受控 `Spike`）；意图明确的复杂事项**单次贯通起草完整 `spec.md`（§1+§2）**、后台过 1 次异体四项审查并运行 [verify_feature.py](../skills/acceptance-testing/scripts/verify_feature.py) `--phase spec-gate` 通过后，发起 1 次 `Spec Gate`（`pending_approval → ready_to_implement`）。
3. **静音巡航与差量单写**：`ready_to_implement` 后按 [静音连续巡航](../workflow/execution-contract.md#静音连续巡航与抗偏航) 自动推进全部单元（仅 3 类白名单真阻塞可打断）；多单元按 [最小派发](../workflow/handoff.md) 与 [宿主适配](../workflow/host-adapters.md#业务派发与降级路径) 隔离派发，可用 `--write-snapshot / --check-writes --since` 锁单写边界；**`task.md` 始终由本角色唯一单写**（≤ 100 行，续改见 [Delta 差量](../workflow/documents.md#delta-差量续改与归档)）。
4. **独立验收与收口硬门禁**：拉起全新独立 `testing` 会话完成 `AC` 与反例验收，本角色完成 `task.md` 最终 `verified` 回写后**必须跑通 `verify_feature.py --phase verified`** 方可交付。仅安装/恢复/升级时读取 [setup Skill](../skills/setup-requirement-workflow/SKILL.md)。
