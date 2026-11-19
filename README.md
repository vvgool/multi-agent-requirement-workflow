# Multi-Agent Requirement Workflow（v2.0 / 协议 4 轻内核）

面向 Codex、Claude Code、OpenCode 与 Zed 的**第一性原理驱动、零重复文档、不确定性单次确认**需求协作框架（`2.0.0` / `protocol_version: 4`）。

## 核心机制

- **不确定性驱动 `Spec Gate` 与受控 `Spike`**：局部小修 `0` 门禁直通；意图明确事项（含复杂跨模块变更）在后台先完成 `spec.md` 与独立四项对齐审查闭环，向用户发起 **1 次 `Spec Gate`（`pending_approval → ready_to_implement`）**；业务分叉或 UI 体感未知时先一次性轻澄清或执行隔离受控 `Spike`。
- **`task.md + spec.md` 零重复体系与 `Contract-First`**：`task.md` 为全事项唯一状态机、批准记录与复选框控制面；`spec.md` 合一承载业务 `F/AC` 与架构契约；代码走 `Contract-First + TDD`，文档/规则走 `SDD + 纯结构/GFM #锚点门禁 + 独立对抗验收`。
- **静音连续巡航与抗偏航硬锁**：`ready_to_implement` 后连续推进单元实施与独立验收，仅 **3 类真阻塞**可打断；靠**回读 AC 锚点 + 单写 `task.md` + 干净子上下文 + 2～3 次盲修熔断 + 独立 `sessionID` 反例验收**防偏航。
- **安装期核验、日常零开销**：`install_helper.py` 一次性完成包 SHA256 核验与四宿主薄适配，日常缓存存在时零哈希重算。

## 安装与恢复

详见 [`skills/setup-requirement-workflow/SKILL.md`](skills/setup-requirement-workflow/SKILL.md)：

```bash
python3 -B <pkg>/skills/setup-requirement-workflow/scripts/install_helper.py install \
  --source-root <pkg> --target-root <project> --hosts codex,claude-code,opencode,zed \
  --source-kind git --source-location https://github.com/vvgool/multi-agent-requirement-workflow.git \
  --source-revision <40位commit_sha>

python3 -B <pkg>/skills/setup-requirement-workflow/scripts/install_helper.py restore \
  --source-root <pkg> --target-root <project>
```

## 索引与回归验证

- [路由](workflow/routing.md) ｜ [执行约定](workflow/execution-contract.md) ｜ [文档与 Delta](workflow/documents.md) ｜ [最小派发](workflow/handoff.md) ｜ [宿主适配](workflow/host-adapters.md) ｜ [配置](workflow/config.md) ｜ [协调](agents/coordinator-agent.md) ｜ [产品](agents/product-agent.md) ｜ [开发](agents/development-agent.md) ｜ [缺陷](agents/bug-agent.md) ｜ [验收](agents/testing-agent.md)

```bash
python3 -B scripts/verify-rule-loading.py --source-root .
python3 -B scripts/verify-host-adapters.py --source-root . --scratch /path/to/empty_dir
python3 -B -m unittest discover -s tests
python3 -B tests/test_experiment_control.py --scratch-root /path/to/empty_dir
```

遵循 [MIT License](LICENSE)。
