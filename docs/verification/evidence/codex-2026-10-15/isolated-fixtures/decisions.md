# 隔离规则场景，非真实宿主故障注入

- unknown：读取 unknown.before.yaml 后，没有 ID 可查询，也无结束证据；实际选择阻塞，写 after，不调用产品。
- 旧结果：读取 stale.current 与 incoming，识别 revision/run 不符；保留来件，拒绝推进，after 与 current 完全一致。
- 同名歧义：假设请求“再做任务列表状态筛选”且未说明续改/独立。实际决策是待澄清“这是原需求续改还是新的独立需求？”，不覆盖有效演示目录、不派发。本夹具不模拟用户答复。

这是协调者场景核对及一次性断言，不是框架程序强制保障；host ID fixture-only-not-real-host-id 仅为隔离状态输入，绝非真实宿主证据。
