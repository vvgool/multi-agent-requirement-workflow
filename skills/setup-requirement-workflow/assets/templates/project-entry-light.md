<!-- requirement-workflow:begin -->

## 需求协作入口

命中本入口时按本节统一推进需求澄清、设计与任务（禁止混用外部通用规格工作流 Skill，保留领域/工具专项 Skill 正常调用）。

### 1. 复杂度分流与前期合并提问
- **明确局部低风险小修**：目标、方案、边界明确且在既有契约内时，当前会话直接**定位 → 最小修改 → 相关回归 → 简短返回**（零建档、零派发、无需读取下方框架文件）。原因不明的 Bug 先沿真实调用链取证复现。
- **前期先查代码、合并必答提问（第一性原理穿透 XY 表象）**：涉及新功能、行为变更或跨模块契约时，提问前先读相关代码与配置，剥离“表面解法”追问“根本矛盾与硬约束”；能从代码确认或属常规实现细节的不打断用户，**所有影响范围或验收的必答业务决策一次性合并提出**。

### 2. 两道 `<HARD-GATE>` 确认门禁与高危护栏
需对齐事项按显式**阶段状态**推进：`pending_req_approval` → `req_approved` → `pending_design_approval` → `ready_to_implement` → `verified`。
1. **`STOP 1`（需求未批）**：展示完整需求与验收标准（`AC`），单独请求需求批准后结束本轮。**业务澄清不等于批准**（仅答业务参数或提问工具仅回 `accepted:true` 回执均不算批准，须合入需求重新待批）。
2. **`STOP 2`（设计未批）**：`req_approved` 后按“先删减冗余假设、机械约束下沉脚本/代码”形成设计；状态性或复杂设计须先完成独立四项规格对齐审查（查遗漏 AC、扩权、契约冲突、未证假设）并消除阻断，展示设计请求批准并结束本轮。**未获明确设计批准前严禁编写业务实现代码**。
3. **局部重确认与未知外部操作**：实质变更仅重确认受影响部分；涉及**支付、权限、数据删除或大范围共享逻辑变更**须先确认具体范围并由独立角色验证；**结果未知的外部操作**先查原请求，幂等性未确认前保持阻塞，严禁自动重放或补偿。

### 3. 静音连续巡航与长跑抗偏航
进入 `ready_to_implement` 后开启**全链路静音连续巡航**（连续完成实施单元 → 联调自验 → 独立对抗验收 → 内部返修闭环，一次性交付）：
- **中途打断白名单**：除 **① 新证据证伪已批需求/核心契约、② 触及未授权高危副作用/未知外部写、③ 缺少外部凭据/环境（须先跑完其余独立单元后集中反馈）** 外，严禁因汇报进度、切换单元或常规报错修复询问“是否继续”（按锁文件安装本地依赖、复用当前宿主运行隔离验证、隔离环境内生成随机合成密钥/假数据均非打断白名单，声称缺环境前须先核实本机隔离可行性）。
- **抗偏航四道锁**：① 每单元完成后执行者**只读回读** `task.md` 首屏与关联 `AC` 锚点核对无缩水，主会话统一**单写勾选** `<features_dir>/<事项名称>/task.md`（≤ 100 行当前态，续改用 Delta 差量，不建 `v2/v3` 目录）；② 多单元复杂任务按需派发干净上下文子角色；③ 同一故障连续 2～3 次修复无新根因证据立即熔断转系统化诊断；④ 交付前须经独立角色真实运行 `AC` 与最高风险反例验收。

### 4. 按需规则索引（日常零核包开销）
框架文件位于 `.agents/requirement-workflow-cache/<lock.sha256>/`（见 `workflow.lock.yaml`），存在时**无需运行时计算包哈希或读取回执**，按职责读取：
- 路由与升降级：`workflow/routing.md` ｜ 门禁与巡航细则：`workflow/execution-contract.md`
- 文档首屏与 Delta 规范：`workflow/documents.md` ｜ 最小派发卡片与恢复：`workflow/handoff.md`
- 四宿主派发与降级：`workflow/host-adapters.md` ｜ 配置与可选 Issue：`workflow/config.md`
- 专业方法读缓存根下 `agents/*-agent.md` 与 `skills/{requirement-analysis,feature-development,bug-fixing,acceptance-testing}/SKILL.md`。
- **克隆缺缓存一次性恢复**：仅当缺失 `.agents/requirement-workflow-cache/<lock.sha256>/` 时，按 `workflow.lock.yaml` 检出 `source.location` 的 `source.revision` 至临时目录，执行 `python3 -B <tmp>/skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root <tmp> --target-root .` 补齐缓存（`manual` 源阻塞待包）。

<!-- requirement-workflow:end -->
