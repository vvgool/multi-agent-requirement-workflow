# 宿主适配与安装锁定契约

协议 4 将包完整性核验与宿主薄文件生成前置到**安装/升级/克隆恢复期一次性确定性完成**，使日常业务会话保持**零哈希计算、零回执查询开销**。

## 四宿主映射与规则型宿主

| 宿主 | 原生专业角色（product / development / testing / bug） | 项目内位置 | 适配细则 |
| --- | --- | --- | --- |
| `codex` | `requirement_{product,development,testing,bug}` | `.codex/config.toml` + `.codex/agents/*.toml` | [Codex 适配](../skills/setup-requirement-workflow/references/codex-adapter.md) |
| `claude-code` | `requirement-{product,development,testing,bug}` | `CLAUDE.md` + `.claude/agents/*.md` | [Claude Code 适配](../skills/setup-requirement-workflow/references/claude-code-adapter.md) |
| `opencode` | `requirement-{product,development,testing,bug}` | `.opencode/agents/*.md` | [OpenCode 适配](../skills/setup-requirement-workflow/references/opencode-adapter.md) |
| `zed` | 规则型宿主（不注册 product、development、testing、bug 文件） | 复用根目录 `AGENTS.md`（不生成 `.zed/agents`） | [Zed 适配](../skills/setup-requirement-workflow/references/zed-adapter.md) |

- **规则型宿主边界与原生问答**：Zed 仅在显式指定时选择，其初始化回执 `native_role_probes` 为空、`native_role_invocation` 为 `not_applicable`。宿主支持原生交互问答组件时，推荐优先调用宿主原生交互问答组件发起轻澄清或 `Spec Gate` 确认（选项须具明确授权语义）。
- **被动尊重宿主权限**：仅生成上述受管块与薄角色，**严禁生成或修改宿主的模型、权限、沙箱或 Hook 配置文件**；宿主开启只读或拦截策略时被动遵守。

## 安装期校验与日常零核包

1. **仓库提交 vs 本地忽略**：提交 `workflow.yaml`、`workflow.lock.yaml`、`AGENTS.md` 受管块、`.gitignore` 忽略块及具名宿主薄角色；本地忽略 `.agents/requirement-workflow-cache/<package.sha256>/`。
2. **确定性脚本与日常零开销**：安装/升级统一调用 [setup Skill](../skills/setup-requirement-workflow/SKILL.md) 的 `install_helper.py`。日常 `.agents/requirement-workflow-cache/<lock.sha256>/` 存在时直接按需读取规则与 Skill，无需重算哈希。
3. **克隆缺缓存恢复**：缺失缓存目录时，主会话按锁检出 `source.location` 的 `source.revision` 至临时目录，运行一次 `<tmp>/skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root <tmp> --target-root .` 补齐缓存（`manual` 源或子角色直接报告缺包阻塞）。

## 业务派发与降级路径

1. **具名角色可用**：按上表原生名称派发，传入 [最小派发短卡片](handoff.md#派发短卡片正反例)。
2. **无具名参数但支持独立子会话**（见 [Codex 无具名协作](../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作) 与 [Zed 非具名协作](../skills/setup-requirement-workflow/references/zed-adapter.md#非具名独立协作)）：派发全新独立上下文子会话读取缓存内 `agents/<role>.md` 与完整 `skills/<skill>/SKILL.md`，父会话回读子任务标识与执行证据（不冒称具名注册激活）。
3. **纯单会话环境**：当前会话执行并在每单元后重读 `task.md` 与 `AC` 锚点；必需独立审查/验收无法建立独立上下文时如实披露限制并标阻塞。

## 恢复判定与接续

断连或异常中断时先查宿主原任务状态与文件差异，禁止整单盲目重派：运行中则等待；状态不明保持 `unknown` 阻塞；已确认停止则核对 `git diff` 复用已完成成果只补缺口；外部操作结果未知时先查原请求，幂等性未确认前严禁重放。
