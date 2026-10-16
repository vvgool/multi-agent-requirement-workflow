# 修正规则回归

重新读取协调角色、config、documents、revisions 后，仅在本隔离目录执行一次性宿主文件动作。原 4 次真实产品调用及 agent-features 全部文件在前后逐一比较 SHA-256，保持不变（normal-before/after.yaml）。没有新产品调用、真实审批或网络请求。

| 场景 | 实际结果 | 证据 |
|---|---|---|
| requirements.md 只读原文 | 原始字节及 hash 保持；已有已检查文稿固化至 review/requirements.md，输出与已有产品稿 hash 相同 | readonly-source/、checks.yaml case1 |
| 来源输出冲突 | review/ 保留路径直接阻塞；source.md 与输出符号链接真实路径相同也阻塞；未创建 input、未覆盖来源 | source-collision/、case2 |
| 飞书配置继承 | 工作空间默认 local；v1 正文 provider=feishu 的 URL/access/write_enabled/父节点策略显式写入 v2；示例无正文保持 blocked，未回落 local | inherit-feishu/、case3 |
| 自定义本地来源继承 | v2 documents 固定 source_revision=1；重新读取原 v1/custom/spec.md，身份与内容匹配；没有创建错误的 v2/custom/spec.md | inherit-local/、case4 |

这是准备与固化步骤的协调者回归和一次性断言，不是额外产品闭环，也不是框架程序强制保障。测试用固化稿来自已有检查通过的产品文稿，不宣称其内部业务身份已迁移为隔离夹具需求。未验证飞书实际访问或权限、真实审批、并发/事务保护及其他宿主。
