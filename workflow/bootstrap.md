# 启动与缺失环境恢复

独立一次性、明确局部低风险且非旧任务续接的小修不触发本恢复过程；直接执行已载项目入口规则。实际需要框架协作、派发、恢复或安装时，主会话使用项目 AGENTS.md 的自包含入口；该入口在缓存不存在时仍能获取并核验锁定包。阶段子 Agent 不承担下载或安装，缺环境向协调层返回阻塞。流程是宿主按指令执行文件操作，不是后台服务、启动脚本或全局插件。

## 自动恢复范围

推进已命名的需求或用户要求补齐环境时，主会话可按已提交锁补本地缓存和回执。只读审查、只读探测及 initialization_probe=true 不触发下载或修复。缺锁不猜版本；Git来源固定完整提交，不跟随main/tag；manual来源等待用户提供包。已有完整合法缓存时不为恢复回执重新联网。

下载后先按 [包身份算法](package.md) 核实真实提交、摘要和清单，再读取取得包内的 setup Skill；入口保留最小算法以打破“缺缓存却先读缓存Skill”的循环。失败保留原项目，不执行未核实内容。恢复只重建本机环境，不自动生成缺失宿主角色或修复用户编辑。

## restore_only 交接

主会话须传入 restore_only=true、工作空间、锁定身份与来源，以及当前宿主。setup先核对项目已有入口、当前宿主角色（Codex还包含锁定模板要求的config.toml注册区块）及全部已声明拥有内容的真实字节与锁定包模板；配置合法且本地忽略规则有效。缺受管项返回 host_not_initialized/managed_entry_missing，内容差异返回 adapter_modified，缓存存在但被改动返回 framework_integrity_mismatch。完整预检通过前不写项目。

新机器没有回执时，仅认领确定性模板匹配的角色/标记区块；用户自定义原文保留。恢复所需临时文件和缓存逐文件清单写入 schema_version=2 pending；operation=restore，沿用当前host及核实的原宿主集合。只有本地缓存/回执是新恢复计划的写入项，锁/配置/入口/角色在pending.read_only_files中分别记录路径与before_sha256，不列为写入项；临时内容按清单原子落位并回读，遵守 [安装恢复规则](../skills/setup-requirement-workflow/references/installation.md)。

已有pending时先读取原计划，不另建restore覆盖它；若是原安装/升级中断，只能在其原始授权和before/after核对通过后完成原计划中的受管项，不因restore_only新加文件、扩大hosts或更换来源。缓存不完整且没有可信pending时视为完整性失败，不用新下载覆盖。

本机回执缺失时，各宿主原生探测都从pending开始；只在当前宿主真实探测后更新它的结果。已有完整同包回执时，重复恢复不改动字节或 mtime，也不把 pending 误记为 passed。当前任务文档和历史执行记录在缓存修复过程中保持原样；派发前仍须查询原宿主实际任务，unknown不证明结束。

## 失败与后续

| 条件 | 动作 |
| --- | --- |
| 没有Git、离线、来源无权限或提交无法取得 | framework_restore_unavailable，列出解除条件；不自动安装工具/改凭据 |
| 提交不符、清单或摘要不符 | framework_integrity_mismatch，不执行包内Skill、不覆盖项目 |
| 旧计划与锁不符或目标中途变化 | 保留pending，说明冲突；不清除业务状态 |
| manual来源没有同摘要包 | framework_not_installed，等待用户提供包 |
| 当前宿主尚未初始化 | host_not_initialized，要求明确初始化该宿主 |
| 文件恢复通过但缺原生角色选择能力 | 保持激活pending，需要委派时报告host_role_selection_unavailable；主会话可直接完成的简单任务不被阻塞 |

恢复成功后加载协调角色、读取当前任务文档及原生任务并选择下一动作。已完整核验且本机环境未变的同会话后续派发，按 [会话复用规则](package.md#会话内核验复用) 检查变化，不重复进入restore流程。恢复缓存不是需求完成证据，也不替代具体范围确认。
