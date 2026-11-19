# 复杂事项的契约设计与单元拆分

起草 `spec.md` §2、拆分实施单元或 Delta 续改前读取。缺关键业务分叉先交主会话按 [人工确认](../../../workflow/execution-contract.md#人工确认) 合并澄清，不靠猜测硬写架构。

## 1. 先定模块边界与契约，再拆实施单元

1. **调用链取证与第一性原理**：沿真实入口识别可复用模块与约束；先删减冗余兼容层与中间状态，将校验/同步等**机械约束下沉**至确定性代码或门禁脚本，再比较关键架构取舍。
2. **正交职责与 Contract-First 签名**：用 Mermaid 标清模块边界与状态唯一写入者，在 `spec.md` §2 前置跨模块签名、数据结构与异常契约。
3. **表示范围与复合失败契约**：沿 `输入 → 转换 → 存储 → 输出` 核对值域与精度；明确事务/清理复合异常优先级；未知外部操作先查原调用禁重放。

## 2. 按可独立验证的行为拆解单元（T1..Tn）

- **契约与主干优先**：首单元优先固定共享契约与失败测试，打通主干后再叠分支。
- **正交写集与回读**：每个 `T1..Tn`（与 `task.md` 同号，`spec.md` 禁放复选框）写清关联 `AC`、允许写集、验证命令（见 [契约先行与分层验证](../../../workflow/execution-contract.md#契约先行与分层验证)）及单元后 `AC` 回读。仅接口固定且写集正交无交集时可并行（配 `verify_feature.py --write-snapshot / --check-writes --since` 锁边界）。

## 3. 后台独立审查、`--phase spec-gate` 与单次 Spec Gate

按 [文档分工](../../../workflow/documents.md#按复杂度选择文档) 确认 `spec.md` 零状态头且 `F/AC → D/Contract → T` 全覆盖后，后台跑 [四项规格对齐审查](architecture-review.md) 与 `verify_feature.py --feature-dir <目录> --phase spec-gate`，通过后发起单次 `Spec Gate`（`pending_approval → ready_to_implement`）。
