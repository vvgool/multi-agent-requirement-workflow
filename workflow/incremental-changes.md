# 进行中需求的增量与审批基线（布局4）

只用于0.5.0起明确绑定protocol_version=2、task.schema_version=2、layout_version=4的新工作上下文。requirements_revision仍定位revisions/vN，不再代表每次内容变化；baseline_id区分该目录内实际评审的内容。旧布局3及协议1继续原锁定包，不因安装新版而改身份、续写或重算审批；未知组合blocked。当前框架源码仓库进行中的v3不迁移。

## 分类与活动调用

协调先追加用户原话及稳定输入关联到既有input.md，重读status和实际调用事实：

| 输入 | 路由 |
| --- | --- |
| 澄清、补遗漏、纠正不符合已批要求且语义未变 | 原目录、原任务和批准范围继续；记录判断依据，不制造审批 |
| 同目标未完成，draft/requirement_review新增功能、规则或验收 | 合并当前稿，旧pending_review失效；核实活动调用结束后续原product（独立Bug则原bug boundary），展示新稿 |
| 同目标未完成，development/testing改变范围或验收 | 暂停后续派发，原目录重审；下述结束核实后续原product（独立Bug则原bug boundary） |
| 无法判断同目标还是独立目标 | 仅澄清身份，不猜建目录 |
| 独立目标或用户明确拆分 | 新建可区分事项和feature_id，input说明关联 |
| 已completed后优化或缺陷 | 新修订，保留旧完成、审批、证据 |

四阶段draft、requirement_review、development、testing均先识别事项类型：workflow_kind=bugfix且bugfix.mode=standalone时续原bug boundary授权重整边界，不要求product任务或伪造product ready；其他普通需求续原product。独立Bug边界须重新展示并明确批准后才可fix，旧批准不授权新增范围；下述running/unknown门禁同样适用。

同目标增量不复制task/host/result，不新建vN+1、status.snapshot、变更申请表、问卷或平行账本。三个连续相关增量也一样。语义未变的验收保留编号；真正新增或改变语义使用未占用编号并注明替代/删除关系，历史编号不得再利用。

有running调用时保持active_run和原授权，先保存待处理输入并阻止该调用的旧交付推进新范围；不并发派发、不修改旧授权。协调通知当前执行者仅在原授权范围安全收束，不要求其代改新范围。须查询到真实ended或cancelled及结束证据才清活动调用和转draft；unknown/查询不可靠保持blocked、保留身份，不伪造结束、不换Agent绕过。执行者发现明确范围变化即停止后续业务写入并交协调核实，保留已完成旧范围成果。无活动调用可直接转draft。

确认范围变化后立即将旧pending_review/approval/development_baseline视为不适用新增/修改范围；旧值在归档中保留，根当前approval和development_baseline置null。活动尚未结束时不得清active_run，根审批可保留旧值以恢复旧调用，但输入待处理标识使它不能授权任何新写调用或推进。结束后在一次根更新中转draft、清当前审批/待验基线并标明旧报告“上一基线，当前待重验”。原development_attempt/max_development_attempts始终保留。

## 最小基线与历史

baseline_id为本修订内b001、b002…，仅真正准备评审时分配下个未占用值；多次补充合并再评审可只有一个新基线。协调是基线、审批、input和根状态唯一写者。分配前枚举既有reviews及当前pending，不重用或覆盖旧id；中断残留先恢复。不是每次输入或调用都递增，不另建基线目录包。

- 根content_baseline为当前实际展示的baseline_id（首次尚未评审为null）；pending_review与approval均带baseline_id和review_digest。批准对象仍是manifest原始字节SHA256；不能只比较id。
- task身份及路径永不因基线变化修改。authorizations追加版本：每版含baseline_id（产品/边界分析可为null）及approval_digest；分析授权用source_baseline_id标明已有来源，无旧来源时null。开发/Bug fix、testing必须同时匹配当前批准baseline_id与review_digest；旧授权不变。
- 锁包身份及任务稳定定位不变；task.effective_config保留初始快照。若基线评审使用新有效配置，在新授权版本追加effective_config={path,sha256}，按host.authorization优先取该版本，否则取task初始引用；旧调用不继承新配置。manifest记录实际使用的不可变快照，不改旧manifest。
- host调用继续只绑定授权版本和输入原字节前缀。result每项交付含baseline_id，必须等于其调用授权；产品候选尚未评审可为null，协调将实际评审基线与其task_id/delivery_id绑定在manifest。产品ready不自行分配审批基线。
- 根development_baseline在既有task_id/delivery_id/code_baseline上增加baseline_id、approval_digest；测试授权及结果的baseline_id、approval_digest、source_delivery和精确代码基线均须一致。result开发/测试/Bug fix每项带approval_digest，等于当时调用授权；旧结果保留旧值，不能用根最新值回填。

只保留必要不可变文件：`.workflow/reviews/<baseline_id>/requirements.md`（独立Bug为bug-boundary.md）、`review-manifest.yaml`、`approval.yaml`。不放task副本、input副本、全量状态或整份代码。来源/配置按既有不可变快照引用复用，不反复复制；有新来源内容才保存实际新快照，历史manifest引用的旧sources不得覆盖。

## 评审固化与恢复顺序

1. 按既有产物归属、已知摘要和真实普通路径核对当前documents。当前已评审对象必须能由旧reviews正文、manifest及适用approval逐字节重建；缺失、用户编辑、链接、来源冲突或归属未知时blocked，禁止先覆盖再补历史。未审批的旧待审正文/manifest也不可覆盖。
2. 按评审类型核对真实来源及输入覆盖：requirements 使用 product 的 ready 具体交付；独立 Bug 的 bug_boundary 使用 bug 的 boundary_ready 具体交付，不要求存在产品任务，也不得伪造产品交付。沿来源 task/result/host 核对事项与修订、角色、调用结束、交付状态、正文产物路径/原字节摘要及输入覆盖，缺失或不匹配则 blocked。准备完整正文、差异、当前有效验收及来源/配置。将最终适用于documents位置的正文原字节写入新reviews基线正文，manifest列feature_id/revision/baseline_id、type（适用时）、正文归档path+sha256、display_path、source_delivery={task_id,delivery_id}及sources/配置摘要（角色与状态从真实任务/交付核对）；路径按序排列，写定再算review_digest，不含展示时间。归档正文是字节证据，其相对链接按display_path解析；从正式位置核验共享链接。
3. 普通文件/路径/摘要确认后才原子替换documents当前稿；历史归档和旧审批不改。根artifacts当前正式索引记录baseline_id及新来源，旧不可变交付仍可从原result回读。确认文件及索引完整后写pending_review、content_baseline和requirement_review；显示真实稿链接、差异、有效验收和baseline_id后记录displayed_at。不新增全量状态快照。
4. 用户明确针对展示的具体基线/范围确认才批准；含糊“继续”、方向认可、旧审批及产品ready均不提供新增范围写权。确认前重新读取正文、manifest、必需来源及配置并校验SHA256，任一变化使待审失效。approval.yaml原子新建，包含feature_id/revision/baseline_id/review_digest、用户原话、真实时间和来源会话（不可得null）；审批type须与manifest类型一致：独立Bug的manifest及approval均必须显式type=bug_boundary，与bugfix契约一致；普通requirements的缺失type仅按requirements兼容，显式错误/未知类型或不匹配均blocked，不能放宽摘要/来源校验。先保存并回读，再以同内容设置根approval并清pending。新授权只能在无活动调用且审批有效、额度允许时追加。
5. 任一步中断，先比较新reviews、当前documents、原交付、根索引/状态。只有归属已知、内容一致、来源和审批仍有效才能补完；没有approval文件不能凭stage猜已批准，没有根生效也不能凭候选文件推进。冲突保留现场blocked，不覆盖旧文件、不占用另一个id绕过残留。多文件不是事务，实际宿主事实和SHA核对是恢复依据。

## 开发、测试、输入与额度

新基线批准后续原development/bug任务，按变化调整原方案并保留未变代码，无需推倒重做。同目录重审、范围增加、断线、换角色或换宿主不重置attempt或上限，也不自动新增额度。已有尝试内新增范围继续同attempt；若独立测试failed之后实际开始新修复则attempt+1；重审不能抹掉该失败依据。达到上限即使新基线已批准也blocked，须用户明确额度决策，业务批准不等于额度授权。

旧ready/待验/passed不能代表合并后的需求；保留历史关联并标明上一基线。新范围必须有当前基线的新开发交付和独立测试，source_delivery精确到task+delivery，前后重枚举code_baseline。受影响代码/验收/输入/环境重新检查；可证明适用的同一测试角色独立证据只引用并注明“本轮未重跑”，开发自验不代替独立通过。全部当前有效验收通过、无未解决项且新输入逐项已覆盖才completed。

输入覆盖依既有input→host输入前缀→授权→result关联核验。已处理重复消息或纯处理标记不重跑；重复新消息不能清掉尚未处理原输入。迟到交付只能保留旧基线/调用关联，不能覆盖当前content_baseline、approval、active_run或待处理输入，不能评审/进测试/完成新范围。相同task_id或相同baseline_id均不足以证明新鲜性。

交接须区分历史回读、当前推进与已消费确认。当前推进绑定 active_run 的具体 task_id/invocation_id 及本次交付；active_run=null 不构成推进许可。中断补交须从既有 host/result/根索引恢复具体调用、交付、输入、审批及真实结束证据，并确认没有后续调用/交付或新输入；无法核实则 blocked，不能只取最新序号。同基线后续调用也使旧结果不能推进。已由根正式产物索引确认消费的同一交付，摘要和身份仍一致时仅幂等确认，不再次变更阶段/基线/输入；已有后续调用或交付时仅保留历史关联。复用现有索引和恢复证据，不新增消费账本。

## 验证边界

合同验证样例须从真实模板构造，在授权临时目录核对三次相关增量、一次测试失败及复验，报告目录、任务、调用、基线和必要文件数。静态规则/文件示例通过与真实原生宿主闭环分开；指令加载和合成批准不等于真人批准或宿主激活，框架本身不提供调度服务、事务或跨进程锁。
