# Shipping fee fixture：技术方案

- feature_id：EVAL-normal
- requirements_revision：1
- run_id：run-check
- 批准文稿与摘要：/private/var/folders/p7/6lh96zx51qz0ksknm0qj5v3r0000gp/T/development-skill-check-hku9qg2v/normal/feature/requirements.md；1f427e6d1b0791c6e34a6d051ebb050319fee2ee696927f2784954419fc87512（合成测试夹具）
- 目标项目：/private/var/folders/p7/6lh96zx51qz0ksknm0qj5v3r0000gp/T/development-skill-check-hku9qg2v/normal/project

## 目标与现状

shipping.py 的 shipping_fee 尚为 NotImplementedError；checkout.py 已通过真实导入调用该函数后相加。项目内无 AGENTS.md 或额外构建配置。

## 需求与实现对应

| 需求/验收编号 | 实现方式 | 相关代码/接口 | 约束或风险 | 验证方式 |
| --- | --- | --- | --- | --- |
| AC-1 | 小于 10000 返回 1000，否则 0 | shipping.py:shipping_fee | 整数分，精确边界 | 0、1、9999、10000、10001、大整数 |
| AC-2 | 负数先抛 ValueError | shipping.py:shipping_fee | 不扩充非整数输入契约 | 负数调用及结算异常传播 |
| AC-3 | 保留已有真实调用并验证 | checkout.py:checkout_total | 不重复定义运费规则 | 全部非负代表值与边界整合 |

## 接口、数据流及影响

整数 subtotal_cents → shipping_fee 校验负数 → 根据阈值输出运费 → checkout_total 加至小计。负数异常沿真实调用传播。仅修改 shipping.py，公共函数签名不变。

## 技术选择与待决策问题

采用直接整数比较，避免浮点误差和额外依赖。已核对无业务待决策项；审批只用于离线评估，不表示真人审批。

## 验证与交付范围

一个普通模块，先验证独立运费，再经真实 checkout 导入验证完整结算和异常传播；执行 Python 编译及 0..20000 全整数回归。无设备、UI 或网络验收要求。
