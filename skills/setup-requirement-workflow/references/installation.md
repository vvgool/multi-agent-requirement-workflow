# 通用安装、恢复与升级

遵循 [宿主适配与安装锁定契约](../../../workflow/host-adapters.md)，由纯标准库 [install_helper.py](../scripts/install_helper.py) 与 [codex_registry.py](../scripts/codex_registry.py) 完成确定性校验、预编译内联与原子缓存写入。

## GitHub/Git URL 获取

1. **按锁检出**：已有 `workflow.lock.yaml` 且非 `--upgrade` 时，`git` 源按锁内 `location` 与 40 位 `revision` 检出；`self` 源直接以源码仓 `.` 为源（默认遍历纯净工作树包目录）。
2. **首次获取与摘要校验**：远程首次安装检出仓库（默认 `https://github.com/vvgool/multi-agent-requirement-workflow`）取 `git rev-parse HEAD` 40 位 SHA（禁含凭据 URL）；可用 `install_helper.py digest --source-root <包>` 校验纯净包摘要，拦截软链、空目录、`.pyc` 与 `.DS_Store`。

## 宿主选择与批量初始化

默认选当前会话宿主加目标项目已有宿主目录；用户显式指定优先（`zed` 自动归一化为 `agents-md`）。

| 宿主档位 | 检测信号 | 受管生成内容 |
| --- | --- | --- |
| `codex` | `.codex/` | `.codex/config.toml` 注册块 + 预编译 `.codex/agents/requirement_*.toml` |
| `claude-code` | `.claude/` 或 `CLAUDE.md` | `CLAUDE.md` 桥接块 + 预编译 `.claude/agents/requirement-*.md` |
| `opencode` | `.opencode/` 或 `opencode.json(c)` | 预编译 `.opencode/agents/requirement-*.md` |
| `agents-md`（兼容 `zed`） | 通用根规则宿主 | 仅维护 `AGENTS.md`、`.gitignore`、`workflow.yaml`、`workflow.lock.yaml` |

## 确定性预编译、恢复与升级保护

1. **全内存预检与预编译**：渲染受管块（[薄入口](../assets/templates/project-entry-light.md)、[忽略块](../assets/templates/gitignore.txt)、[锁模板](../assets/templates/workflow.lock.yaml)），由 `_build_roles` 剥离头信息、重写包内相对链接为缓存路径并合成 [角色正文](../assets/templates/role-body.md)（Codex `.toml` 经无损转义与往返解析断言）；遇残缺标记或非升级篡改零写入退出。
2. **原字节保护与并发幂等缓存**：保留受管块外注释与 CRLF；缓存写临时目录核验摘要后原子 `rename`。
3. **双路径 `restore` 与 `--upgrade` 清理**：`restore` 仅支持规范 `self | git` 锁（拦截 `manual` 锁及 1 字节篡改）；`--upgrade` 同步锁、受管块与预编译角色，并自动清理旧 64 位 hex 缓存目录。
