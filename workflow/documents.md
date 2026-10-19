# 文档来源、快照和审批内容

处理外部正文、文档变动或人工评审时读取本文；字段见 [config.md](config.md)，目录、文稿固化及兼容规则见 [成果目录](output-layout.md)。

## 读取与来源

每份文档区分 requirements（正文）、reference、design、test_report。每份只有一个正文来源，本地不与飞书自动双向同步。source manifest 字段为 kind、provider、location、read_at、remote_version（无法取得则 null）、content_digest、complete、missing_items。

本地来源按配置中的 source_revision（默认当前修订）和 path 定位，切版保持其身份并重新读取。布局 2 的正式评审稿固定在当前修订的 documents/requirements.md，来源与输出冲突时先阻塞；requirements.md 形式的用户原文保持不变。历史评审稿按已存索引使用，不覆盖、迁移或重算历史审批。

每次派发、准备评审、记录审批前及恢复时重新核对必需来源。通过宿主已配置的文件或飞书能力读取实际内容，记录 sources/ 下快照及 manifest.yaml。关键图片、附件、引用节点未读取时 complete=false，说明缺项并阻塞。无必需外部来源时在 review manifest 记录 sources: []，产品使用原始输入，不创建空 sources/；旧 run 已有来源清单仍须校验。

飞书文档或知识库链接需解析为实际正文；有链接不代表有权限。能力缺失、无权限、内容不完整分别报告原因，不假定凭据失效，也不擅自改用旧快照或本地来源。能力可用时遵循该能力的使用规则和用户权限；真实读写验证与本地闭环分别记录。

## 产物和变动

read 来源：产品写本地建议稿及差异，向用户展示实际将批准的是该建议稿；远端原文保持其来源身份。read_write 仅支持 requirements 正文；design、test_report 与 references 的输入权限边界见配置规则。read_write 需求来源：产品 Agent 仅在任务 external_write_scope 明确列出本版目标时，按有效策略及实际权限写回，写入前重读确认未被他人修改，写回后回读核对，将证据和本地评审稿交回协调 Agent，再提交评审。新建知识库产物需有父节点，旧版产物不能被新版覆盖。

新读取内容与已读基线变化时：纯格式/错字变动保留语义判断依据并更新来源记录；范围或验收变化建立新版；不确定就澄清。即使语义不变，旧 pending_review 也先失效，重新展示当前内容再确认。审批后原地修改正文则阻塞核查。

## 摘要和审批

使用宿主可用工具计算文件内容 SHA-256，禁止凭空填写摘要；不要求用户运行任何命令。无法取得可靠摘要时先阻塞，不能将路径或文件名当成内容摘要。

按目录规则固化并核对文稿引用后，在当前版 .workflow/review-manifest.yaml 生成审批清单（旧版沿用原索引）：按路径排序列出 feature_id、revision、实际评审文件及其 sha256、必需 sources manifest 的 sha256（无外部来源则 sources: []）、本次task.effective_config指向的不可变配置快照path和sha256；旧评审沿原effective-config.yaml及原manifest字节。review_digest 是该 manifest 原始字节的 SHA-256，不含 displayed_at。快照和 manifest 先写定，再计算摘要。仅改变 Issue 绑定/同步策略时保留已评审配置快照与原摘要，新的关联策略另存根状态/事件；不重写 manifest 或重算旧审批，见 [配置规则](config.md)。

展示需求、版本、范围变化、每条验收标准和实际文稿链接后记录 displayed_at。收到用户明确针对本次展示的确认，重读上述文件和来源，核对摘要不变才写 approval；记录原始答复、真实时间和来源会话。没有真实会话 ID 时 source_session=null，并注明无法取得，不虚构 ID。不将产品自评、工具输出、旧审批或没有对应评审对象的一般“可以”当作批准。
