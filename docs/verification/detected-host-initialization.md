# 项目宿主检测与批量初始化验证

日期：2026-10-16。框架 0.2.2 / protocol_version=1，72 个核心文件；摘要：`653565841845772fd8ab38577dae473ef99c39c837252473699354cd5f0760fd`。

默认初始化当前实际宿主与项目根检测到的宿主，显式选择范围优先。不遍历业务源码或全局工具目录。目标宿主先共同预检，再以同一 pending 安装；共享锁、缓存和 AGENTS 入口，激活证据分宿主保存。旧单宿主 pending 继续以 [host] 恢复，多宿主 pending 固定原 hosts 集合。升级覆盖全部已有适配，旧包探测保留历史并将当前探测重置 pending。

## 独立文件评估

评估会话读取真实 setup Skill、规则及模板，在系统临时目录用文件工具执行协议；临时辅助程序不是分发安装器。主会话另核对实际回执和 Git 空白检查。

| 用例 | 实际结果 |
| --- | --- |
| 当前 Codex，项目有 .codex/config.toml、用户 CLAUDE.md、合法注释 opencode.jsonc | 检测三个宿主；生成 9 个角色，共14项 Git 待提交文件 |
| 第一份 Codex 角色写入后中断 | 保留同一 pending，按原 hosts 集合恢复完整安装 |
| 重复初始化 | 文件字节和 mtime 均不变 |
| 显式只选当前 Codex | 仅7项待提交文件，Claude/OpenCode 文件和用户原文不变 |
| Claude 用户同名角色与本批次冲突 | 整批预检停止，项目零安装写入 |
| 冲突后明确缩小范围为 Codex | Codex 安装通过，Claude 冲突文件不变 |
| 共享与能力边界 | 单份缓存和锁，缓存/回执/pending 精确忽略，配置原字节保留，git diff --cached --check通过；三个宿主文件passed、原生pending |

没有调用真实原生宿主、远程服务、全局设置或业务项目。当前宿主原生选择不可用；其他宿主未在当前会话探测。真实版本支持、原生激活、完整需求闭环，以及本轮新增的升级探测历史规则尚未运行验证。旧单宿主 pending 的兼容规则已定义，本轮恢复实测对象为新多宿主计划。

旧报告保持执行时版本与范围；本轮全仓静态检查覆盖解析、链接、5个Skill及403个历史证据/案例字节保留。完整测试项目不复制进仓库。

入口：[初始化 Skill](../../skills/setup-requirement-workflow/SKILL.md)、[宿主选择与批量初始化](../../skills/setup-requirement-workflow/references/installation.md#宿主选择与批量初始化)。
