# 任务与结果交接

所有角色派发只读“派发”；产品澄清或结果交接时再读后续产品专属章节。开发/测试结果及公共交接门槛见 [路由](routing.md#交接核对)，角色执行遵循 [执行契约](execution-contract.md)。结构化文件供Agent读取，不由额外程序调度。

## 派发

先读 [成果目录规范](output-layout.md) 确定布局。新修订 run 为 `<features_dir>/<名称>/revisions/vN/.workflow/runs/<run_id>/`；task.yaml及必要sources/由协调层写；锁和配置按包/配置规则引用本修订的不可变共享快照，不逐run复制。角色仅写 task.output_dir、task.result_path 及另外明确授权的位置；旧任务沿用原路径。

按 [产品任务](../templates/product-task.yaml) 或 [开发/测试任务](../templates/role-task.yaml) 填写身份、实际路径、输入、授权及完成标准。completion_criteria只写本轮目标和特有完成条件，阶段Skill已有门槛直接适用；input_path指向累计输入，required_files只列额外必读文件，不重复task专用字段已明确的同一文件。测试仍须列原开发result，复用证据时列原result及必要来源。

派发消息只传task路径、目标工作空间、真实framework身份/root及必要变化或缺陷摘要；完整授权和输入以task及其引用为准，不再另写任务简报或复制需求、规则和验收表。消息与task矛盾时阻塞核对，不用消息静默扩大授权。同角色续派复用宿主Agent，仍使用新run；首次或上下文丢失时读取适用规则，未变规则不重复传全文。

输出及结果路径须匹配布局指定的本需求/修订/run，普通文件或目录且无链接越界；需求位于目标项目内是正常布局，不授予角色写业务源码的权限。具体写范围由任务授权，公共路径核对见执行契约。

新轻量安装按 [包规则](package.md) 在 task/active_run 保存真实framework身份，task.framework_lock引用已核验的不可变锁快照；host.yaml记录当前host和该身份。旧run原锁及配置快照继续按原索引读取。适配映射见 [宿主契约](host-adapters.md)。旧历史任务不回填或迁移。

准备记录不等于已派发。host.yaml 保存真实宿主、host_task_id 和实际取得的时间；宿主未返回 ID 时保持 unknown。结束后将宿主完成或失败事实记入同文件，再清空 active_run。

## 产品结果

result 必须带同一 schema_version、feature_id、requirements_revision、run_id、role=product。artifacts 路径相对当前 run 的 outputs/，拒绝绝对路径、.. 或符号链接越界。

- ready：questions 为空，无关键未确认 assumptions；requirements 文稿存在，acceptance_ids 唯一且对应正文。每条标准有前置条件、操作和可观察结果。产品 Agent 完成正文与验收质量检查，正文保留简短自检结论，详细依据留本run执行记录；artifacts 的 requirements 和 quality_check 可指向同一文件，兼容旧独立 quality-check.md。协调Agent按公共交接核对后展示评审，不重复产品的内容质量检查。
- needs_input：questions 非空，列具体问题与影响；有选项/推荐时一并原样转达，不将推荐记为用户选择。本轮理解使用 summary，不固化为已评审需求。新结果按下节按需提供问题依赖和适用条件。协调 Agent 保存真实答复，按 [路由判定](routing.md#产品澄清答复) 选择等待、转达或新调用；部分答复不必然产生新 run。
- blocked：block_reason 非空，说明缺的能力、权限或证据；不能冒记 ready。
- stale_task：按阶段执行契约记录旧任务失效事实，不作为本阶段交付。

拒绝推进：身份不符、旧修订版或 run、所声明产物不存在、路径越界，或 ready 缺少产品质量检查记录。收到旧结果只保存来件说明，不覆盖新版结果和 active_run。

根状态的 artifacts 由协调 Agent 按 [状态字段](state-contract.md#字段) 维护，仅索引正式成果、入口及run目录；任务、宿主、结果和详细证据留在run内，不重复登记。状态更新和审批条件见 [state-contract.md](state-contract.md) 及 [documents.md](documents.md)。

## 澄清记录与再次派发

新 needs_input 的每题提供稳定 id、question、impact；语义变化时使用新ID并说明替代关系。有问题依赖时才填dependencies（问题ID或前提/来源引用）；有条件适用或失效影响时才填validity。普通独立题省略这两项，不补空字段或边界说明。省略仅表示产品未声明依赖，不足以证明累计答复仍适用；出现范围/前提变化、冲突或依据不足时仍交产品分析。推荐附理由，仍是待选建议。

协调层在当前修订 input.md 追加澄清记录：来源产品 run/result、问题 id（旧题无 id 时用原 run+题序定位）、原问题/选项/推荐及依赖原文或其可回读引用、用户原话、答复对应题及有效/待核实/未解决状态、剩余问题、动作与依据、待处理答复标记和相关状态版本。记录可用分段或表格，不额外新建问卷；已有记录只追加，不重写历史。旧结果仅含 question/impact 仍有效，缺依赖字段不补写；依据不足交产品分析。

恢复派发前先核对累计输入中尚未分析或产稿的动作与既有 run/结果；记录每次调用覆盖的答复引用及其适用结果，输入已落盘或 task 已准备不等于处理完成。对已经由适用结果处理的输入接续结果交接，未知调用先核实；最新重复消息不能遮蔽未完成动作，也不能使已完成动作重派。

需要新调用时才准备独立 run 的 task；input_path 指向累计输入，required_files 包含必要的此前结果/来源。交接说明本次触发原因（重新分析或整理文稿）、此前未决问题、累计答复及映射、变化和待核实项。原任务结束期间收到的答复也须带入；先核对旧结果输入适用性，不能忽略新答复接受旧结论。新 run 产出新结果，历史 run/result 保持原样；宿主 Agent 复用只记录真实调用身份。

答复记录、等待决策、恢复和写入冲突统一按 [状态规则](state-contract.md#无新-run-的澄清更新) 持久化；产品 ready 的正式评审与审批仍按原契约执行。
