<!-- requirement-workflow:begin -->
## 需求协作入口

发起、继续或优化命名需求时，以本项目为工作空间，先读 workflow.lock.yaml。框架缓存为 `.agents/requirement-workflow-cache/<package.sha256>/`；缓存不随 Git 提交，由主会话在派发前按以下步骤补齐。单纯问答/审查/维护不创建需求；用户要求只读或 initialization_probe=true 时不下载、修复或写入，缺环境仅报告阻塞。

1. 锁必须能可靠解析且无重复键，包含 schema_version=1、package{name,version,protocol_version,sha256}、source{kind,location,revision}；包名为 multi-agent-requirement-workflow，协议为1，摘要为64位小写十六进制。已有 `.agents/requirement-workflow.pending.json` 时先读取原计划；有锁时计划包身份/来源须与锁一致。缺锁仅在可信的原安装pending明确来源/身份时按原计划恢复，不重新规划或派发任务；无该计划或锁格式不合法则停止。
2. 缓存目录完整时先核验下述包身份；目录存在但内容不符、含链接/额外文件时返回 framework_integrity_mismatch，不自动覆盖。完整缓存但缺本机回执时可直接从缓存执行下一步，无需联网。
3. 缓存不存在且 source.kind=git 时，用已有 Git 能力在独立临时目录从 source.location 获取 source.revision 的完整提交并检出，核实实际 HEAD 一致；不解析最新分支或改锁。URL须为无凭据HTTPS/SSH远程Git来源，拒绝本机路径；revision须为完整提交SHA。只读获取，不执行下载的脚本或安装依赖。manual来源需用户提供同摘要包；标识不能当下载URL。无工具、无网络或无权限时返回 framework_restore_unavailable 及原因，不推进需求。
4. 执行下载包的指令前先计算身份：文件清单为根 framework.yaml、AGENTS.md、README.md、workflow.yaml、LICENSE（存在时）以及 agents/、skills/、workflow/、templates/ 全部普通文件；拒绝清单内链接/特殊文件。按相对POSIX路径字符串升序生成 [路径,原字节SHA256] 条目数组，以UTF-8紧凑JSON编码（ensure_ascii=false、分隔符为逗号和冒号），其SHA256须等于锁中sha256；framework.yaml中的name/version/protocol_version须等于锁。来源提交或摘要不符时停止，不能读取其Skill执行修复。
5. 身份通过后读取该包 skills/setup-requirement-workflow/SKILL.md，以 restore_only=true 补本地环境：先核对已有受管入口/角色/忽略区块均符合锁定模板，再按原pending或新restore计划补缓存/回执。自动恢复不得增改版本锁、项目配置、受管入口/角色、业务文稿、审批或active_run；缺角色、用户修改或冲突时报告具体问题，等待明确初始化/修复，不自动升级。成功核验并清理匹配的pending后才加载缓存中的 agents/coordinator-agent.md。

按缓存 workflow/host-adapters.md 的当前宿主映射真实选择三个原生角色，传入 task、包身份和当机框架路径。只读取角色文件不等于原生调用；文件安装、当前宿主激活、完整业务闭环分别记录。业务阶段前核对活动任务；未知调用不重复派发，不借环境恢复换宿主、升级或重置状态。Issue默认关闭，启用时仅由协调层按授权处理。
<!-- requirement-workflow:end -->
