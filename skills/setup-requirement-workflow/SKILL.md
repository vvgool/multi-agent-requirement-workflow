---
name: setup-requirement-workflow
description: Initialize, self-bootstrap, restore, or upgrade the Protocol 5 requirement workflow across Codex, Claude Code, OpenCode, and universal agents-md hosts via stdlib install_helper.py.
---

# 通用需求协作初始化、自举与升级

由纯标准库 [install_helper.py](scripts/install_helper.py) 完成纯净运行包（`framework.yaml`、`LICENSE` 及 `agents/ skills/ workflow/ templates/`）摘要核验、受管块合并与具名子角色无损预编译内联。

1. **来源获取与宿主归一化**：
   - 外部业务仓按 [通用安装](references/installation.md#githubgit-url-获取) 检出仓库取 40 位 SHA（`git`）；源码仓自举用 `self`（`--source-location .`）；本地副本用 `manual`。
   - 按 [宿主选择](references/installation.md#宿主选择与批量初始化) 选 `codex`、`claude-code`、`opencode` 或通用 `agents-md`（覆盖 Zed/Cursor/Windsurf/Antigravity，`zed` 归一化为 `agents-md`）。
2. **预检与执行**：
   - 参考适配细则（[Codex](references/codex-adapter.md)、[Claude Code](references/claude-code-adapter.md)、[OpenCode](references/opencode-adapter.md)、[通用 AGENTS.md](references/agents-md-adapter.md)）检查同名角色与语法。
   - **安装**：`python3 -B <包根>/skills/setup-requirement-workflow/scripts/install_helper.py install --source-root <包根> --target-root <项目根> --hosts <列表> --source-kind self|git|manual --source-location <.|URL|标识> [--source-revision <40位SHA>]`。
   - **恢复（`restore`）**：支持规范 `self` 锁（`--source-root . --target-root .`）与 `git` 锁，验明受管块与预编译角色未篡改后补齐缓存。
   - **升级（`--upgrade`）**：确认无在途子任务后追加 `--upgrade`，同步受管文件并清理旧 64 位缓存目录。
3. **分层核验**：区分“文件落盘”与“子角色激活”（OpenCode `run --agent` 不充当子角色调用证据）；返回版本、SHA256、宿主与变更文件，不自动远程提交。
