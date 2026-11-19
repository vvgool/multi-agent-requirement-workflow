# Multi-Agent Requirement Workflow（v3.0.0 / 协议 5）

面向 Codex、Claude Code、OpenCode 与 `agents-md` 通用规则宿主（覆盖 Zed、Cursor、Windsurf、Antigravity 等，兼容 `--hosts zed` 别名）的**无包袱纯净运行包、子角色预编译内联、单次 `Spec Gate` 与确定性门禁**需求协作框架（`3.0.0` / `protocol_version: 5`，全仓 100% Python 标准库零第三方依赖）。

## 核心机制

- **纯净运行包与单提交自举（协议 5）**：运行包仅含 `framework.yaml`、`LICENSE` 及 `agents/ skills/ workflow/ templates/`（剥离源码仓根 `AGENTS.md`、`README.md`、`workflow.yaml`），支持 `source.kind: self` 单轮自举收敛与 `self | git` 缺缓存确定性 `restore`。
- **具名子角色安装期预编译内联**：`install_helper.py` 在安装/升级期剥离 `SKILL.md` 头信息、重写包内相对链接为锁定缓存路径并做无损 TOML 转义，将缓存根 + `Role` + `SKILL` 直接预编译进具名子角色（0 冷启动跳读，消除自指重读），主会话 `AGENTS.md` 受管薄入口保持 `≤ 16` 行 / `≤ 2,000 B`。
- **不确定性驱动 `Spec Gate` 与静音连续巡航**：明确局部小修 `0` 门禁直通；跨模块或复杂事项后台贯通起草零状态头 `spec.md`、过异体四项对齐审查并跑通 `verify_feature.py --phase spec-gate`，向用户发起 **1 次 `Spec Gate`（`pending_approval → ready_to_implement`）**；获批后静音连续巡航（仅 3 类真阻塞可打断，2～3 次盲修熔断，全新 `sessionID` 反例验收）。
- **事项产物与差量单写确定性门禁（`verify_feature.py`）**：随包内置纯标准库门禁脚本，支持 `--phase spec-gate`、`--write-snapshot / --check-writes --since` 差量单写边界核验，以及主会话回写 `task.md` 为 `verified` 后强制执行的 `--phase verified` 收口校验。

## 安装、自举与恢复

详见 [`skills/setup-requirement-workflow/SKILL.md`](skills/setup-requirement-workflow/SKILL.md)：

```bash
# 外部业务项目（git 源 40 位提交 SHA 锁定安装）
python3 -B <pkg>/skills/setup-requirement-workflow/scripts/install_helper.py install \
  --source-root <pkg> --target-root <project> --hosts codex,claude-code,opencode,agents-md \
  --source-kind git --source-location https://github.com/vvgool/multi-agent-requirement-workflow.git \
  --source-revision <40位commit_sha>

# 源码仓自身单轮自举同步（self 源）
python3 -B skills/setup-requirement-workflow/scripts/install_helper.py install \
  --source-root . --target-root . --hosts codex,opencode --source-kind self --source-location . --upgrade

# 克隆缺缓存恢复（self 源传 . ；git 源传按锁检出的 <pkg>）
python3 -B <pkg>/skills/setup-requirement-workflow/scripts/install_helper.py restore \
  --source-root <pkg> --target-root <project>
```

## 索引与回归验证

- [路由](workflow/routing.md) ｜ [执行约定](workflow/execution-contract.md) ｜ [文档与 Delta](workflow/documents.md) ｜ [最小派发](workflow/handoff.md) ｜ [宿主适配](workflow/host-adapters.md) ｜ [配置](workflow/config.md) ｜ [协调](agents/coordinator-agent.md) ｜ [产品](agents/product-agent.md) ｜ [开发](agents/development-agent.md) ｜ [缺陷](agents/bug-agent.md) ｜ [验收](agents/testing-agent.md)

```bash
python3 -B skills/setup-requirement-workflow/scripts/install_helper.py restore --source-root . --target-root .
python3 -B -m unittest discover -s tests
python3 -B scripts/verify-rule-loading.py --source-root .
python3 -B scripts/verify-host-adapters.py --source-root . --scratch /path/to/empty_dir
python3 -B skills/acceptance-testing/scripts/verify_feature.py --feature-dir <feature_dir> --phase verified
```

遵循 [MIT License](LICENSE)。
