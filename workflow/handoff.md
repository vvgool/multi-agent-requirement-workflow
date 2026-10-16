# 产品任务与结果交接

本文定义 product 专属契约；开发和测试的阶段路由及交接要求见 [routing.md](routing.md)。公共派发记录和 [阶段执行契约](execution-contract.md) 适用于所有角色，不能把 product 的 ready 分支套用为 testing 通过。

模板：[task](../templates/product-task.yaml)、[result](../templates/product-result.yaml)。结构化文件供 Agent 读取，不由额外程序调度。

## 派发

先读 [成果目录规范](output-layout.md) 确定布局。新修订 run 为 `<features_dir>/<名称>/revisions/vN/.workflow/runs/<run_id>/`；task.yaml、effective-config.yaml 及必要 sources/ 由协调层写。角色仅写 task.output_dir、task.result_path 及另外明确授权的位置；旧任务沿用原路径。

任务包含 schema_version、feature_id、requirements_revision、run_id、role、layout_version、framework_root、workspace_root、feature_dir、target_project、input_path、required_files、output_dir、result_path、completion_criteria；外部写回目标单列 external_write_scope，默认空。全路径必须与实际解析的目录一致。output_dir 和 result_path 必须分别匹配该布局下当前需求、修订版和 run 的指定位置；需求目录位于 target_project 内（包括 target_project 与 workspace_root 相同）是正常布局。解析符号链接后仍须位于该 run 内，不得改指业务源码、历史版本或其他 run；角色的源码写权限另按任务角色及目标项目规则判断。

新轻量安装按 [包规则](package.md) 在 task/active_run 保存真实framework身份，并在run下保存framework-lock.yaml；host.yaml还记录当前host和该身份。适配映射见 [宿主契约](host-adapters.md)。旧历史任务不回填或迁移。

准备记录不等于已派发。host.yaml 保存真实宿主、host_task_id 和实际取得的时间；宿主未返回 ID 时保持 unknown。结束后将宿主完成或失败事实记入同文件，再清空 active_run。

## 验收结果

result 必须带同一 schema_version、feature_id、requirements_revision、run_id、role=product。artifacts 路径相对当前 run 的 outputs/，拒绝绝对路径、.. 或符号链接越界。

- ready：questions 为空，无关键未确认 assumptions；requirements 文稿存在，acceptance_ids 唯一且对应正文。每条标准有前置条件、操作和可观察结果。产品 Agent 完成正文与验收质量检查，默认并入文稿自检段；artifacts 的 requirements 和 quality_check 可指向同一文件，兼容旧独立 quality-check.md。协调 Agent 核对文稿、检查记录与结果字段存在，向用户展示评审。
- needs_input：questions 非空，列具体问题与影响；有选项/推荐时一并原样转达，不将推荐记为用户选择。本轮理解使用 summary，不固化为已评审需求。新结果按下节提供问题依赖和适用条件。协调 Agent 保存真实答复，按 [路由判定](routing.md#产品澄清答复) 选择等待、转达或新调用；部分答复不必然产生新 run。
- blocked：block_reason 非空，说明缺的能力、权限或证据；不能冒记 ready。
- stale_task：按阶段执行契约记录旧任务失效事实，不作为本阶段交付。

拒绝推进：身份不符、旧修订版或 run、所声明产物不存在、路径越界，或 ready 缺少产品质量检查记录。收到旧结果只保存来件说明，不覆盖新版结果和 active_run。

根状态的 artifacts 由协调 Agent 维护，记录 task、host、result、文稿和检查证据，标注 revision/run_id。状态更新和审批条件见 [state-contract.md](state-contract.md) 及 [documents.md](documents.md)。

## 澄清记录与再次派发

新 needs_input 的每题除 question/impact 外，提供稳定 id、dependencies 和 validity；问题 ID 在当前修订内可追踪，语义变化时使用新 ID 并说明替代关系。dependencies 为所依赖问题 ID 或已知前提/来源引用列表；空列表表示本轮无问题依赖。validity 用简短文字说明当前适用条件、会使本题或其他题失效的回答；独立题也说明其独立性边界。推荐附理由，仍是待选建议。

协调层在当前修订 input.md 追加澄清记录：来源产品 run/result、问题 id（旧题无 id 时用原 run+题序定位）、原问题/选项/推荐及依赖原文或其可回读引用、用户原话、答复对应题及有效/待核实/未解决状态、剩余问题、动作与依据、待处理答复标记和相关状态版本。记录可用分段或表格，不额外新建问卷；已有记录只追加，不重写历史。旧结果仅含 question/impact 仍有效，缺依赖字段不补写；依据不足交产品分析。

恢复派发前先核对累计输入中尚未分析或产稿的动作与既有 run/结果；记录每次调用覆盖的答复引用及其适用结果，输入已落盘或 task 已准备不等于处理完成。对已经由适用结果处理的输入接续结果交接，未知调用先核实；最新重复消息不能遮蔽未完成动作，也不能使已完成动作重派。

需要新调用时才准备独立 run 的 task；input_path 指向累计输入，required_files 包含必要的此前结果/来源。交接说明本次触发原因（重新分析或整理文稿）、此前未决问题、累计答复及映射、变化和待核实项。原任务结束期间收到的答复也须带入；先核对旧结果输入适用性，不能忽略新答复接受旧结论。新 run 产出新结果，历史 run/result 保持原样；宿主 Agent 复用只记录真实调用身份。

答复记录、等待决策、恢复和写入冲突统一按 [状态规则](state-contract.md#无新-run-的澄清更新) 持久化；产品 ready 的正式评审与审批仍按原契约执行。
