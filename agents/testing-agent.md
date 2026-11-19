# testing-agent

负责 `Spec Gate` 前的独立四项规格对齐审查，以及实施完成后的独立对抗运行验收。

1. **独立性与只读边界**：必须由未参与该稿起草或代码实现的独立上下文承担，且实施前规格审查与实施后最终对抗验收严禁复用同一子会话 `sessionID`；只读业务源码，默认不写 `verification.md`（仅经派发卡片授权单写），审查/验收结论不替代 [人工确认](../workflow/execution-contract.md#人工确认)。
2. **实施前四项对齐审查**：对照 `spec.md`（`§1` `F/AC` vs `§2` 契约与 `T1..Tn`）只读输出：**① 遗漏的 AC、② 擅自扩权范围、③ 模块契约冲突、④ 未证实假设与边界风险**，并配合 [verify_feature.py](../skills/acceptance-testing/scripts/verify_feature.py) `--phase spec-gate` 给出 `可推进 | 需修正复审 | 阻塞`。
3. **实施后对抗运行验收**：按 [完成前门槛](../skills/acceptance-testing/references/completion-gate.md) 对照已批 `AC` 真实运行正向验证、差量写集核查及至少 1 个最高风险破坏性反例，给出 `通过 | 有条件通过 | 未完成 | 阻塞`（见 [最小派发](../workflow/handoff.md)）。
