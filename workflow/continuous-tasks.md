# 持续角色任务（协议2）

这是协议2任务、调用、交付的唯一执行契约，阶段角色接单读“身份与布局”“调用与授权”“交付与恢复”及自己的角色条目；协调按本轮动作读后续段。规则是宿主执行规范，不是调度服务或跨进程锁。

## 身份与布局

协议2只用于明确绑定protocol_version=2、schema_version=2、layout_version=4的新工作上下文任务（0.5.0起）。布局3及协议1的run与布局1/2继续由其原锁定包解释；新包不得接管旧活动调用、续写旧task、迁移审批或重算历史。未知组合blocked；框架升级仅改变安装，不使旧修订自动改协议。每个实际评审基线经用户明确确认后才进入写阶段。

一个feature_id表示业务事项；修订定位持续目录上下文，baseline_id区分目录内实际评审内容；同目标未完成范围/规则/验收变化遵循[增量契约](incremental-changes.md)，原目录续原任务重审。同修订每个实际需要的product/development/testing/bug默认只有一个持续task_id（默认取角色名），协调只用根状态，不建立自己的task。仅独立目标/明确拆分独立工作、修订变化、用户明确终止后替代才建新任务，并在既有input中记关系。调用结束、等待、断线、换Agent/宿主、代码变化、失败回修或同范围授权更新均不增任务。

```text
revisions/vN/
  input.md                         # 累计输入、问题/答复、处理关联
  documents/                       # 当前正式成果（协调维护）
  .workflow/
    snapshots/                     # 已有锁/配置，不新增账本
    reviews/<baseline_id>/          # 布局4必要正文/manifest/批准，非整套修订包
    tasks/<task_id>/
      task.yaml                    # 稳定身份、路径、授权版本
      host.yaml                    # 依序追加调用，协调单写
      result.yaml                  # 依序追加已完整交付，执行角色单写
      outputs/                     # 工作稿按需建立，不预建每轮目录
        <delivery_id>/             # 真正提交时保存必要不可变版本/证据
```

任务身份是feature_id+requirements_revision+task_id+role；调用身份是任务内invocation_id（如i001）；交付身份是任务内delivery_id（如d001）。不再使用run_id混指三者，不在它们外面加session/batch/run目录。同一角色任务的交付序号不随宿主变化归零。task.output_dir/result_path固定指向该任务（明确迁移时按portability核对并保存原定位证据，不新建业务任务）。任务与host/result包含schema_version=2及任务身份；布局4的授权版本、每项交付、审批及待验交付必须按[最小基线](incremental-changes.md#最小基线与历史)关联baseline_id和approval_digest，不能用旧审批授权新范围；无需在每轮复制framework或完整需求。

## 调用与授权

每次执行重新核对锁/快照、根status、任务身份、阶段、本版审批、输入、授权与适用代码基线。环境完整校验仅首次/上下文丢失/受管文件变化时执行，按[包复用](package.md#会话内核验复用)处理；缓存不代替业务核对。确认路径均为授权普通文件，拒绝链接逃逸、未知归属及并写。

一个事项同时仅一个活动调用/写者。根字段仍名active_run，但协议2保存{task_id,role,revision,invocation_id,host,dispatch_status,framework}及实际可得host_task_id。无调用时为null；持续task、未答问题及待处理输入仍存在。host.yaml的invocations按序追加，每项包含：

- id、host、agent_id、call_id（实际不可得为null并说明限制）；本地序号不是宿主call_id，Agent ID不冒充调用ID。
- status=unknown/running/ended/cancelled、started_at、结束时ended_at及end_evidence。ended只证明宿主调用结束，不表示业务完成；取消须有真实证据。
- input={path,sha256}、authorization（task.authorizations内版本id）、本次source_delivery（适用时）。输入路径相对feature_dir，摘要绑定本次实际读到的累计输入。历史输入还须可重建：input保持只追加，host.input.sha256对应调用前文件的原字节前缀，协调可按该摘要唯一定位前缀；无法重建则blocked。用户修改历史input时保留现场，不将新文件冒作原输入。输入原文保留在input.md；历史原始外部来源按原快照保留，不反复复制累计输入全文。

task.authorizations按序追加{id,purpose,baseline_id,approval_digest,write_scope,completion_criteria}，只含实际需要的授权；第一版即明确范围，无授权不执行。required_files、boundary_path/boundary_digest、source_delivery及外部写授权等按适用情况放对应版本，避免task上有相互冲突的当前授权副本。每次调用指向其中一版；协调仅在无活动调用时追加新版本，保留批准依据和生效顺序。既有版本不可扩大/覆盖，旧调用仍绑定旧授权。

product只写候选与必要授权正文；development/bug fix必须有当前有效审批及明确源码路径；testing始终modify_business_source=false，不修业务源码。Bug boundary仅只读项目，不写测试/源码/探针；边界正式确认后同task追加fix授权，旧boundary调用不变。修改范围/验收语义按增量契约原目录重审（完成后才新修订），同范围授权调整也必须有真实依据，不因Agent续接默认沿用写权。

原Agent可续接优先复用；不支持续接/上下文丢失/换宿主时先确认旧调用ended/cancelled，核对持续身份、产物归属、最新输入、权限和原生角色，再用同task追加调用。新宿主需自己的真实激活证据；不能推广别的宿主能力。unknown或查询不可靠先恢复核实，不取消标记掩盖疑点；无法恢复blocked并指出缺项。

## 交付与恢复

工作稿可按已知摘要安全更新；在正式提交时才分配delivery_id，将有变化的必要文稿保存outputs/<delivery_id>/不可变副本。若复用同任务已有不可变文件，只引用原安全路径和摘要，不复制；同一真实检查只保留一份证据，失败与真实重验有不同编号。artifacts.path相对task.output_dir，禁止绝对路径、..及链接逃逸。

result.yaml为{schema_version,feature_id,requirements_revision,task_id,role,deliveries:[]}；按[结果模板](../templates/role-result.yaml)追加完整交付，已有条目及其文件永不覆盖。每项至少id、invocation_id、status、summary、input_sha256、artifacts；开发/Bug ready、测试passed/failed包含精确code_baseline，开发/Bug另含changed_files；测试含source_delivery={task_id,delivery_id}及acceptance_results，failed含defects。blocked有block_reason，needs_input有questions。Bug boundary_ready有边界稿及摘要；product ready有验收id与自检，ready不等于人工批准。身份三元组外还需核对交付所引用调用和输入授权，不仅看同一task_id。

中间澄清不写result：产品通过本次真实宿主返回稳定题id、具体问题/影响、必要选项与依赖；协调作为input.md唯一写者追加问题及用户原话/对应题。问题已存则返回其位置即可，不另写问卷；产品不与协调并写input。调用可ended且根execution_status=waiting_user，不必长期挂起Agent。中间blocked也可在host结束原因及根block_reason轻记录；无实际交付不预建result、空outputs或delivery目录。确需提交报告的失败/阻塞是完整交付，照常不可变保存。

提交顺序：核对仍有效的调用/授权/输入 → 准备完整不可变产物 → 计算摘要与精确基线 → 原子追加result并回读 → 报告交付id → 协调确认宿主结束及完整交接 → 一次更新根阶段、基线、计数/索引。写任何已有文件前核对已知摘要/归属，内容相同不重写；多个文件不是事务。部分写入或无最终result不推进，确认原调用结束后原角色依据已知文件补交；归属不明/用户编辑/摘要不符blocked，禁止通过改摘要绕过重验。

旧交付/旧调用迟到时只保留原关联，不能清当前active_run、改当前基线或完成新输入。输入新鲜性按当前待处理输入与调用input摘要及其覆盖答复逐项核对；input中追加的纯处理标记可依据覆盖映射证明不影响结论，不能仅因全文件摘要变化就无限重跑，也不能以“同任务”跳过未处理新诉求。新输入未覆盖的ready不得提交评审/进入测试。无变化轮询、普通进度只读/通知，不生成完整结果、事件或状态版本。

## 协调与澄清

根stage仍draft→requirement_review→development→testing→completed；execution_status仍idle/running/waiting_user/blocked。task、调用、某轮交付、事项完成分别表达，不另建任务状态机。根artifacts按需索引kind=task的目录；正式文稿来源含task_id+delivery_id+kind+sha256，解析该交付唯一产物；只有初建任务登记一次目录。development_baseline={task_id,delivery_id,code_baseline}明确当前待验交付，不能只绑定task_id。

协调每次业务动作合并必要状态/计数/索引；state_version写前比较并回读。events只记录实际业务变化并引用input/host/result，不复制正文；普通通知不做阶段内容自检或重跑测试，不写事件/README。输入追加轻量原话与题关联，已有处理映射引用覆盖它的invocation/delivery；已处理重复答复不执行，不把新输入误判为重复。

部分回答先判断剩余问题是否仍有效：无新分析需要则继续等待；影响依赖、冲突或需要查源码才续原产品任务。答案齐全只续一次整理；有调用时新输入保留待处理，不并发。仅保存答复或准备调用不表示已处理；恢复先核对累计待处理项及已有适用结果，最新重复消息不能清掉待处理项。方向认可不是正式审批。产品只问影响行为、范围和验收的实质问题，信息足够直接交评审稿。

## 开发、测试与Bug

开发持续设计/实现/自验/回修。低风险小修只在原记录补变化、检查和限制，引用未变方案，不重新拆全套任务。普通进度只更新原计划；提交待验才新delivery及精确基线。完成一次检查不等于整体需求完成。

测试续原testing任务，每次调用授权的source_delivery绑定真实开发/Bug交付和当前development_baseline；先后两次交付即使task相同也须不同绑定。按[代码基线](code-baseline.md)重新枚举当前文件；变化影响的代码、输入、依赖、环境检查重跑。可核实适用的本测试角色既有独立证据/辅助证据只引用，写明“本轮未重跑”及依据；开发/Bug自验不替代独立验收，局部通过不作整体通过。复验报告只补差异与最终覆盖，不复制历史验收表和日志；旧failed及旧基线永久保留。

普通缺陷默认原development任务修复；独立只修Bug、复杂定位或确需专门诊断才启用bug任务。切换前确认原写调用结束；Bug自验后仍独立测试，确需局部验收才保留supplement链，回原development任务继续，不默认每个缺陷都走完整切换链。

诊断按证据裁剪：已知原因且证据充分直接最小修复与回归，不凑3–5假设/探针/逐因素最小化；未知原因验证实际候选假设，按需最小化/探针。两者保留可靠症状、可判定反馈、原场景与适用回归；无法验证不得ready。失败/重验分开保存。

## 尝试额度

根development_attempt/max_development_attempts在本修订开发与Bug fix共享。首次实际写阶段尝试计一次；独立测试failed后的下一次真实修复计一次。计数绑定attempt（授权版本在需要时含attempt=正整数），不绑定task数或宿主调用数。

同一修复尝试的自验重跑、普通进度、断线恢复、开发↔Bug转交与回开发继续不重复计/不清零。独立验收失败后新修复须新attempt；只读Bug boundary、角色不可用/有证据未调用不扣。写前在同一根更新预留计数，unknown先核实不能再次扣/退；确认未调用才纠正。达到上限blocked等待用户明确决策，不换角色绕开；额度和授权不能借澄清或换宿主重置。

## 最小交接核对

协调不重做阶段内容分析：确认实际调用结束、任务/调用/交付与当前输入授权匹配、产物普通文件且摘要正确、审批有效及适用基线一致，再固化文稿并一次流转。完整性不足blocked而非伪造失败；stale/迟到仅保存旧关联。开发ready→testing；独立测试failed→development并保留失败交付；passed必须全部适用验收通过且无未解决项及基线一致才completed；Bug supplement局部passed只回原开发，不完成事项。新修复开始即把旧报告标为“上一交付，待重验”。
