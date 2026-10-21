---
name: bug-fixing
description: Portable bounded bug diagnosis and repair with boundary approval, red-capable feedback loops and independent testing handoff.
---

# 缺陷诊断与修复

接单/结束遵循 [执行契约](../../workflow/execution-contract.md)，入口与审批遵循 [Bug 路由](../../workflow/bugfix.md)。参考 diagnosing-bugs 方法，本包已包含全部必要规则与 HITL 资源，不依赖作者本机 Skill。先读项目 CONTEXT.md（存在时）及相关 ADR，不为先猜原因而广泛读代码。

## 边界任务

当前调用绑定的授权purpose=boundary：只读定位症状与资料，加载 [边界模板](assets/templates/bug-boundary.md)，写本任务 边界稿。明确预期、修复边界/禁止事项、逐项验收、环境和缺口，不写测试/源码/探针；缺实质决策返回 needs_input，否则按 [公共结果模板](../../templates/role-result.yaml) 核对该调用boundary授权、填changed_files=[]、带实际摘要的 bug_boundary 文稿，返回 boundary_ready 交协调展示。尚无批准不执行下述修改环节。

## 修复任务

当前调用绑定的授权purpose=fix：核对本版有效审批、实际写范围、有效配置快照及必要资料。加载内置 [修复记录](assets/templates/bug-report.md)，所有记录写当前任务 输出；旧失败不覆盖。先将症状、关联 AC/边界、拟建反馈命令/修改范围与检查方法写入修复记录并同调用 通知协调，自主继续，不等展示确认。边界超出即暂停重审。

## 1. 确认症状与可判定反馈

先读取可靠原始症状、失败依据及真实调用路径。优先运行能区别错误/正确行为的测试、CLI/API检查、trace重放或适合现场的验证；人工才能完成时用[HITL模板](scripts/hitl-loop.template.sh)保存真实反馈，不能虚构自动红绿。记录受控输入、判定信号及实际环境，偶现问题记录触发/失败次数和参数，不把一次偶然通过作修复依据。缺少可判定反馈或必要环境则blocked，不猜测修复。

## 2. 按不确定性定位

已知原因且证据充分，直接最小修复与原场景/适用回归，不机械凑3–5假设、探针或逐因素最小化。原因不明才按实际证据列候选假设及可证伪预测，选择最小相关检查；必要时缩小场景、定向日志或debugger，一次控制相关变量，不强制数量。性能问题先量基线/profile。记录影响判断的限制，不用裁剪绕过授权/有效验证。

## 4. 修复、回归与自验循环

有正确接缝覆盖真实调用模式时，先将最小复现固化成测试并实际看红，再最小修复、看绿，最后重跑原始未最小化场景。多调用者缺陷不能用单调用浅层测试冒认覆盖。无合适接缝明确记录架构限制与影响，不制造浅层测试证明；原始反馈循环仍必需。

每轮用不同 evidence/iteration-NNN-* 文件或修复记录追加条目保存输入/假设/改动/失败成功事实，不覆盖上一轮。自验失败→新证据定位→修复→重验，始终在批准边界；无新证据或循环重复、环境缺失/范围变化时 blocked/needs_input，说明下一步。角色内重跑/断线恢复/同次转交不新增尝试；独立验收失败后下一次真实修复计共享attempt，见持续任务额度。

## 5. 清理和独立交接

重跑原始症状及适用回归，清除所有本轮 `[DEBUG-...]` 探针并以相应前缀搜索确认；删除临时原型或移到明确 debug 位置，保留必要诊断证据。证据展示/保存前用 `<REDACTED>` 替换秘密，凭据仅经环境变量注入，不复制整份 auth header/config。修复记录写被证实原因、变更、限制及原场景/回归结果；只有用户明确要求提交时才提交，并将原因写入 commit/PR。

按 [基线契约](../../workflow/code-baseline.md) 捕获实际代码（含相关未提交文件），[公共结果模板](../../templates/role-result.yaml) 在既有result追加不可变交付，填role=bug、changed_files、真实artifacts 和 code_baseline；完成自验/清理且无阻塞才 ready。ready 交独立测试，不代表 completed。独立测试失败接收真实失败报告和基线，回到循环并保留旧证据；全部适用独立验收通过才完成修复。supplement 只交回开发剩余工作，不能宣称整体完成。缺口返回 blocked/needs_input，交付前重核 task/status/审批/基线有效性，不跨阶段调用。

协议2边界确认后同bug任务追加fix授权，旧调用不扩权；[持续任务](../../workflow/continuous-tasks.md)约束身份、恢复、交付与共享额度。
