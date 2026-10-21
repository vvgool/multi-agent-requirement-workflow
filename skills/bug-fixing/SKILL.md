---
name: bug-fixing
description: Portable bounded bug diagnosis and repair with boundary approval, red-capable feedback loops and independent testing handoff.
---

# 缺陷诊断与修复

接单/结束遵循 [执行契约](../../workflow/execution-contract.md)，入口与审批遵循 [Bug 路由](../../workflow/bugfix.md)。参考 diagnosing-bugs 方法，本包已包含全部必要规则与 HITL 资源，不依赖作者本机 Skill。先读项目 CONTEXT.md（存在时）及相关 ADR，不为先猜原因而广泛读代码。

## 边界任务

bug_purpose=boundary：只读定位症状与资料，加载 [边界模板](assets/templates/bug-boundary.md)，写本 run 边界稿。明确预期、修复边界/禁止事项、逐项验收、环境和缺口，不写测试/源码/探针；缺实质决策返回 needs_input，否则按 [公共结果模板](../../templates/role-result.yaml) 填 bug_purpose=boundary、changed_files=[]、带实际摘要的 bug_boundary 文稿，返回 boundary_ready 交协调展示。尚无批准不执行下述修改环节。

## 修复任务

bug_purpose=fix：核对本版有效审批、实际写范围、有效配置快照及必要资料。加载内置 [修复记录](assets/templates/bug-report.md)，所有记录写当前 run 输出；旧失败不覆盖。先将症状、关联 AC/边界、拟建反馈命令/修改范围与检查方法写入修复记录并同 run 通知协调，自主继续，不等展示确认。边界超出即暂停重审。

## 1. 先建立反馈循环

优先失败测试，其次 HTTP/CLI 驱动、浏览器断言、真实 trace 重放、最小 harness、性质/压力循环、bisect 或旧新差分。最后才用 [HITL 模板](scripts/hitl-loop.template.sh)。命令必须实际运行，走真实缺陷路径，断言用户确切症状，记录命令、受控输入、判定信号、脱敏输出与耗时；“没崩溃”不是有效信号。固化时间/随机种子/环境并缩短循环到秒级；无法达到时明确耗时与必要性，不能称作快速确定性循环。偶现问题提升复现率，记录触发次数、失败次数、种子/压力参数与判定阈值，不把偶然一次通过作修复依据。

没有已运行、可判红且可由 Agent 重跑的命令，不进入原因假设和修改。无法建立循环时列已试方法、缺失环境或脱敏 HAR/日志/时间戳资料、解除条件，blocked；生产临时探针须另获明确授权。不得猜测性修代码。

## 2. 复现与最小化

确认红色信号对应原始症状，多次运行确认可重复（偶现记录高复现率）。每次减少一个输入/调用/配置因素后重跑，保留仍能触发的最小场景，说明剩余因素为什么必要。未复现并最小化不进入假设；不可继续缩小时注明具体环境或成本限制，不跳过而假称完成。

## 3. 可证伪假设与探针

先列 3–5 个排序假设及预测：“若 X 导致，改变 Y 应消失/改变 Z 应恶化”，向协调发送以便展示，不新增审批等待。每个探针对应一条预测，一次只改一个变量；优先 debugger/REPL，再用定向日志，禁全量日志碰运气。探针标记唯一 `[DEBUG-<id>]` 前缀。性能问题先测基线、profile/查询计划后再二分或修复。阶段裁剪只在有明确具体理由且不取消有效原始反馈循环时记录，不能用裁剪绕过审批/独立测试。

## 4. 修复、回归与自验循环

有正确接缝覆盖真实调用模式时，先将最小复现固化成测试并实际看红，再最小修复、看绿，最后重跑原始未最小化场景。多调用者缺陷不能用单调用浅层测试冒认覆盖。无合适接缝明确记录架构限制与影响，不制造浅层测试证明；原始反馈循环仍必需。

每轮用不同 evidence/iteration-NNN-* 文件或修复记录追加条目保存输入/假设/改动/失败成功事实，不覆盖上一轮。自验失败→新证据定位→修复→重验，始终在批准边界；无新证据或循环重复、环境缺失/范围变化时 blocked/needs_input，说明下一步。角色内命令重跑不新增派发次数；跨 run 上限由协调按共享计数管理。

## 5. 清理和独立交接

重跑原始症状及适用回归，清除所有本轮 `[DEBUG-...]` 探针并以相应前缀搜索确认；删除临时原型或移到明确 debug 位置，保留必要诊断证据。证据展示/保存前用 `<REDACTED>` 替换秘密，凭据仅经环境变量注入，不复制整份 auth header/config。修复记录写被证实原因、变更、限制及原场景/回归结果；只有用户明确要求提交时才提交，并将原因写入 commit/PR。

按 [基线契约](../../workflow/code-baseline.md) 捕获实际代码（含相关未提交文件），[公共结果模板](../../templates/role-result.yaml) 填 role=bug、changed_files、bug_purpose、真实 artifacts 和 code_baseline；完成自验/清理且无阻塞才 ready。ready 交独立测试，不代表 completed。独立测试失败接收真实失败报告和基线，回到循环并保留旧证据；全部适用独立验收通过才完成修复。supplement 只交回开发剩余工作，不能宣称整体完成。缺口返回 blocked/needs_input，交付前重核 task/status/审批/基线有效性，不跨阶段调用。
