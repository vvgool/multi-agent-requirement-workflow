# 通用安装、恢复与升级

遵循 [宿主适配与安装锁定契约](../../../workflow/host-adapters.md)，由纯标准库 [install_helper.py](../scripts/install_helper.py) 与 [codex_registry.py](../scripts/codex_registry.py) 在安装期完成确定性校验与写入。

## GitHub/Git URL 获取

1. 已有 `workflow.lock.yaml` 且非显式升级时，严格按锁中 `source.location` 与 40 位 `source.revision` 检出，不跟随分支漂移。
2. 无锁首次安装时，在临时目录检出指定仓库（默认 `https://github.com/vvgool/multi-agent-requirement-workflow`）并用 `git rev-parse HEAD` 取 40 位 SHA；禁写凭据入锁。
3. 可用 `python3 -B <包>/skills/setup-requirement-workflow/scripts/install_helper.py digest --source-root <包>`（或 `--package-root`）校验摘要并拦截软链、`.pyc` 与 `.DS_Store`。

## 宿主选择与批量初始化

默认目标宿主为当前会话宿主加目标项目根检测到的宿主；用户显式指定范围优先。

| 宿主 | 检测信号 | 生成内容 |
| --- | --- | --- |
| `codex` | `.codex/` 目录 | `.codex/config.toml` 受管块 + `.codex/agents/requirement_*.toml` |
| `claude-code` | `.claude/` 或 `CLAUDE.md` | `CLAUDE.md` 桥接块 + `.claude/agents/requirement-*.md` |
| `opencode` | `.opencode/` 或 `opencode.json(c)` | `.opencode/agents/requirement-*.md` |
| `zed` | 仅用户明确指定或确认为 Zed 会话 | 仅核对 `AGENTS.md` 受管块，不建 `.zed/agents` |

## 确定性写入、恢复与升级保护

1. **全内存预检**：`install` 先渲染模板（[入口](../assets/templates/project-entry-light.md)、[忽略块](../assets/templates/gitignore.txt)、[锁模板](../assets/templates/workflow.lock.yaml)、[角色正文](../assets/templates/role-body.md)）并检查标记完整性，遇残缺标记或非升级篡改零写入退出。
2. **原字节与默认配置保护**：块外注释与 CRLF 原字节保留；无 `workflow.yaml` 时生成 `issue_tracking.binding: "off"`，已有保留不动；同版重跑零重写。
3. **克隆恢复（`restore`）**：仅支持规范 `git` 源锁（`manual` 源或锁元数据被篡改直接阻断），核验受管块未改后原子补齐缓存。
4. **显式升级（`--upgrade`）**：确认无在途子任务后用 `--upgrade` 同步缓存、锁与已装宿主薄文件，历史事项文档不静默改写。
