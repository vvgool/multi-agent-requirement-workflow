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
- needs_input：questions 非空，列具体问题与影响；有选项/推荐时一并原样转达，不将推荐记为用户选择。本轮理解使用 summary，不固化为已评审需求。协调 Agent 将实际问题、用户原文答复及对应关系追加至 input.md，再创建新 run，携带此前未决问题和已答记录。未获得实际答复不重复派发；部分答复交产品判断剩余缺口，不由协调层补业务规则。
- blocked：block_reason 非空，说明缺的能力、权限或证据；不能冒记 ready。
- stale_task：按阶段执行契约记录旧任务失效事实，不作为本阶段交付。

拒绝推进：身份不符、旧修订版或 run、所声明产物不存在、路径越界，或 ready 缺少产品质量检查记录。收到旧结果只保存来件说明，不覆盖新版结果和 active_run。

根状态的 artifacts 由协调 Agent 维护，记录 task、host、result、文稿和检查证据，标注 revision/run_id。状态更新和审批条件见 [state-contract.md](state-contract.md) 及 [documents.md](documents.md)。
