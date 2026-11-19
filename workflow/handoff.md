# 最小派发与单写交接

仅在**确需异体审查/验收、多单元写集隔离、复杂领域探索或疑难诊断**时派发子角色（意图明确时单人贯通起草 `spec.md`，禁串行拼稿）。具名角色已预编译内联职责与 `SKILL`，派发仅传最小上下文；`Spec Gate` 前审查与实施后最终验收严禁复用同一子会话 `sessionID`。

## 派发短卡片正反例

### 合格派发卡片
```markdown
- **项目根与缓存**：`/abs/project` ｜ `.agents/requirement-workflow-cache/<sha256>`
- **任务与状态**：单元 `T2`（`development-agent`）｜`ready_to_implement`（批准见 `task.md`）
- **目标与 AC**：实现订单超时释放库存，满足 `AC-02`、`AC-04`
- **允许写集**：`src/order/expire.py`、`tests/test_order_expire.py`（`task.md` / `spec.md` 只读）
- **契约与证据**：复用 `InventoryRepo.release(order_id)`；`T1` 已过 `pytest tests/test_inventory.py`
- **完成条件**：RED→GREEN 验证并发幂等，只读回读 `task.md` 与 `AC-02/04` 后返回结果卡片
```

### 禁止反例
```markdown
- 粘贴大段聊天记录或无关日志；不给单写边界或多角色并写 `task.md`；
- 未获用户批准把“审查通过”当源码修改授权，或复用审查会话 `sessionID` 做最终验收。
```

## 单写归属与中断恢复

1. **严格单写与差量核验**：
   - **`task.md` 始终由主会话唯一单写**（回写 `verified` 后必跑 [verify_feature.py](../skills/acceptance-testing/scripts/verify_feature.py) `--phase verified`），子角色仅只读回读。
   - 多单元并行须接口已固定且写集**正交无交集**；派发前后可用 `verify_feature.py --write-snapshot <snap.json> --repo-root . --feature-dir <目录>` 与 `--check-writes --repo-root . --since <snap.json> --feature-dir <目录> --allow <写集...>` 拦截越界改动与控制面篡改。
   - 审查/验收默认只读业务源码；`verification.md` 同批仅一人写入（主会话或显式授权的 `testing-agent`）。
2. **结构化终态返回**：
   - **实施/修复**：完成项与 `T/AC`、改动文件、验证命令与真实输出、回读结论、遗留限制，标 `通过 | 需修正 | 阻塞`。
   - **审查/验收**：四项对齐诊断（`遗漏AC | 擅自扩权 | 契约冲突 | 未证假设与边界风险`）+ 反例运行证据与级别（`P1/P2/P3`），审查标 `可推进 | 需修正复审 | 阻塞`，验收标 `通过 | 有条件通过 | 未完成 | 阻塞`。
3. **中断恢复**：终态返回后不轮询；异常中断按 [恢复判定与接续](host-adapters.md#恢复判定与接续) 查原任务与差异后补缺口，未知非幂等外部操作保 `blocked` 禁重放。
