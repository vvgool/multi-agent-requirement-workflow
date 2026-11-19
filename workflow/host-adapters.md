# 宿主适配与安装锁定契约

安装、升级与恢复期由纯标准库 `install_helper.py` 完成纯净运行包摘要核验、受管块合并与具名子角色无损预编译内联，使主会话日常零核包、具名子角色冷启动 **0 规则跳读**。

## 四宿主映射与规则型宿主

| 宿主档位 | 原生角色（product / development / testing / bug） | 项目内受管位置 | 适配细则 |
| --- | --- | --- | --- |
| `codex` | `requirement_{product,development,testing,bug}`（预编译） | `.codex/config.toml` + `.codex/agents/*.toml` | [Codex](../skills/setup-requirement-workflow/references/codex-adapter.md) |
| `claude-code` | `requirement-{product,development,testing,bug}`（预编译） | `CLAUDE.md` + `.claude/agents/*.md` | [Claude Code](../skills/setup-requirement-workflow/references/claude-code-adapter.md) |
| `opencode` | `requirement-{product,development,testing,bug}`（预编译） | `.opencode/agents/*.md` | [OpenCode](../skills/setup-requirement-workflow/references/opencode-adapter.md) |
| `agents-md`（兼容 `zed`） | 规则型宿主（不建专属角色目录） | 仅复用根 `AGENTS.md`（Zed / Cursor / Windsurf / Antigravity 等） | [通用 AGENTS.md](../skills/setup-requirement-workflow/references/agents-md-adapter.md) |

- **通用规则宿主与被动权限边界**：`--hosts zed` 自动归一化为 `agents-md`，不建 `.zed/agents` 等目录；优先调用宿主原生问答组件；**严禁生成或修改宿主的模型、权限、沙箱或 Hook 配置**。

## 安装期校验与日常零核包

1. **纯净运行包边界**：仅统计复制根 `framework.yaml`、`LICENSE` 及 `agents/ skills/ workflow/ templates/`（根 `AGENTS.md`、`README.md`、`workflow.yaml` 不入包摘要）；业务仓提交 `workflow.yaml`、`workflow.lock.yaml`、受管块与预编译角色，忽略 `.agents/requirement-workflow-cache/<sha256>/`。
2. **三类来源锁与双路径恢复**（见 [setup Skill](../skills/setup-requirement-workflow/SKILL.md)）：
   - `self`（源码仓自举，`location: .`、`revision: self`）：单轮收敛并清旧缓存；缺缓存跑 `python3 -B skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root . --target-root .`。
   - `git`（外部业务仓 40 位 SHA）：缺缓存按锁检出临时目录 `<tmp>` 跑一次 `<tmp>/skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root <tmp> --target-root .`。
   - `manual`（`revision: null`）：禁自动 `restore`，缺缓存报 `framework_cache_missing` 阻塞。

## 业务派发与降级路径

1. **具名角色可用**：按上表名称传入 [派发短卡片](handoff.md#派发短卡片正反例)（职责、`SKILL` 与缓存链接已预编译内联）。
2. **无具名但支持独立子会话**（见 [Codex 无具名](../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作) 与 [通用非具名](../skills/setup-requirement-workflow/references/agents-md-adapter.md#非具名独立协作)）：派发全新独立子会话，传入项目根、锁定缓存、`agents/<role>.md` + `skills/<skill>/SKILL.md` 及允许写集，回读真实子任务 ID 与输出（禁同会话自审）。
3. **纯单会话**：每单元后只读回读 `task.md` 与 `AC`；必需独立审查/验收无法建立独立上下文时披露限制并标阻塞。

## 恢复判定与接续

中断时先查原任务状态与文件差异，禁整单盲目重派：运行中等待；状态不明保阻塞；已停则核对 `git diff` 或写集快照只补缺口；未知外部操作先查原请求，幂等未明禁重放。
