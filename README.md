# Multi-Agent Requirement Workflow（v1.0 / 协议 4 轻内核）

面向 Codex、Claude Code、OpenCode 与 Zed 的**第一性原理驱动、抗偏航、少打断**需求协作框架（`1.0.0` / `protocol_version: 4`）。

## 核心机制

- **第一性原理贯穿全链**：需求期穿透 XY 表象直击根本矛盾与硬约束；设计期质疑假设“先删减、再下沉脚本/类型、后新增”；排障期拒绝经验盲试，沿真实数据流与不变量推导根因。
- **自适应分流与两次精准对齐**：局部小修零建档直通；复杂变更先读代码合并必答提问，严守 `pending_req_approval` → `req_approved` → `pending_design_approval` → `ready_to_implement` → `verified` 两道 `<HARD-GATE>`。
- **静音连续巡航与抗偏航四锁**：`ready_to_implement` 后连续推进各单元与内部验收，仅 **3 类真阻塞**可打断；靠**回读 AC 锚点 + 单写 `task.md` + 干净子上下文 + 2～3 次盲修熔断 + 独立反例验收**防偏航。
- **安装期核验、日常零开销**：`install_helper.py` 一次性完成包 SHA256 核验与宿主适配，日常缓存存在时零哈希重算。

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
