# 产品任务与结果交接

本文定义 product 专属契约；开发和测试的阶段路由及交接要求见 [routing.md](routing.md)。公共派发记录和身份核对也适用于其他角色，不能把 product 的 ready 分支套用为 testing 通过。

模板：[task](../templates/product-task.yaml)、[result](../templates/product-result.yaml)。结构化文件供 Agent 读取，不由额外程序调度。

## 派发

run 目录为 `<features_dir>/<名称>/revisions/vN/runs/<run_id>/`。task.yaml、sources/、effective-config.yaml 由协调 Agent 写，产品仅写其中 outputs/。

任务包含 schema_version、feature_id、requirements_revision、run_id、role、framework_root、workspace_root、feature_dir、target_project、input_path、required_files、output_dir、completion_criteria；外部写回目标单列 external_write_scope，默认空。全路径必须与实际解析的目录一致，output_dir 不可位于历史版、目标项目或需求目录外。

准备记录不等于已派发。host.yaml 保存真实宿主、host_task_id 和实际取得的时间；宿主未返回 ID 时保持 unknown。结束后将宿主完成或失败事实记入同文件，再清空 active_run。

## 验收结果

result 必须带同一 schema_version、feature_id、requirements_revision、run_id、role=product。artifacts 路径相对当前 run 的 outputs/，拒绝绝对路径、.. 或符号链接越界。

- ready：questions 为空，无关键未确认 assumptions；requirements 文稿存在，acceptance_ids 唯一且对应正文。每条标准有前置条件、操作和可观察结果。产品 Agent 完成正文与验收质量检查，默认并入文稿自检段；artifacts 的 requirements 和 quality_check 可指向同一文件，兼容旧独立 quality-check.md。协调 Agent 核对文稿、检查记录与结果字段存在，向用户展示评审。
- needs_input：questions 非空，列具体问题与影响，不固化为已评审需求；协调 Agent 向用户转达，答复追加至 input.md 后创建新 run。
- blocked：block_reason 非空，说明缺的能力、权限或证据；不能冒记 ready。

拒绝推进：身份不符、旧修订版或 run、产物不存在、路径越界、缺少产品质量检查记录。收到旧结果只保存来件说明，不覆盖新版结果和 active_run。

根状态的 artifacts 由协调 Agent 维护，记录 task、host、result、文稿和检查证据，标注 revision/run_id。状态更新和审批条件见 [state-contract.md](state-contract.md) 及 [documents.md](documents.md)。
