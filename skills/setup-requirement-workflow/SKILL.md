---
name: setup-requirement-workflow
description: Initialize, restore, or upgrade a version-pinned requirement workflow (Protocol 4) in Codex, Claude Code, OpenCode, or Zed using deterministic install_helper.py and thin host adapters.
---

# 通用需求协作初始化与升级（协议 4）

用户要求为目标业务项目安装、补齐克隆缓存或显式升级本框架时使用。通过纯标准库脚本 [install_helper.py](scripts/install_helper.py) 在安装期一次性完成包摘要核验与薄文件生成，使日常业务会话保持**零哈希计算、零回执查询开销**。

1. **获取与宿主选择**：
   - 用户提供 Git URL 时，按 [通用安装步骤](references/installation.md#githubgit-url-获取) 在临时目录检出完整代码并取得 40 位提交 SHA；本地包则由本文件位置向上定位包根。
   - 核实目标业务项目根（禁止默认安装进源框架自身）与目标宿主集合（见 [宿主选择规则](references/installation.md#宿主选择与批量初始化)）：支持 `codex`、`claude-code`、`opencode` 三个具名角色宿主及 `zed` 规则型宿主（Zed 仅复用 `AGENTS.md`，不生成四个角色文件，且仅在用户明确指定或当前确认为 Zed 会话时纳入）。
2. **预检与确定性执行**：
   - 先按各目标宿主适配说明（[Codex](references/codex-adapter.md)、[Claude Code](references/claude-code-adapter.md)、[OpenCode](references/opencode-adapter.md)、[Zed](references/zed-adapter.md)）检查同名角色遮蔽与既有配置语法。
   - **首次安装或同锁补宿主**：运行 `python3 -B <包根>/skills/setup-requirement-workflow/scripts/install_helper.py install --source-root <包根> --target-root <项目根> --hosts <宿主列表> --source-kind git|manual --source-location <来源> [--source-revision <提交SHA>]`（保护用户原有配置与非受管区块字节；新项目尚无 `workflow.yaml` 时自动生成外部写默认 `off` 的配置）。
   - **克隆缺缓存恢复**：已有 `workflow.lock.yaml` 与受管入口但缺本地缓存目录时，运行 `install_helper.py restore --source-root <包根> --target-root <项目根>` 只读核验受管块并补齐 `.agents/requirement-workflow-cache/<sha256>/`，不改写任何受管项目文件。
   - **显式升级**：确认当前无在途未完成子任务且受管文件未被手工篡改后，追加 `--upgrade` 更新缓存、锁与全部已装宿主的薄文件。
3. **分层核验与真实报告**：
   - 区分“文件安装完成”与“原生角色真实调用验证”。需要验证具名角色激活时，须在新会话或重载后回读宿主实际子任务记录，核对父会话关系、指定角色、目标项目及成功终态（OpenCode 的 `run --agent` 只选主角色，即使四个命令都成功也不能当作具名子角色派发通过；无法取得实际子任务关系时如实说明限制）。
   - 返回包版本、64 位 SHA256、目标宿主集合、新增/更新的待提交路径与本地忽略目录，不自动执行远程提交或生产发布。
