# 成果目录与执行记录

协调 Agent 新建、切版、派发、接收产物或清理时读取本文；阶段角色只需读取 [阶段执行契约](execution-contract.md)。正式成果由协调层固化，角色只写本次候选产物和授权代码。

## 布局与兼容

新需求及新修订版使用 layout_version=2，根 status.yaml 记录当前修订版布局，task 同步该值。旧状态/任务缺此字段视为布局 1，沿用其 task 与 artifacts 实际路径；不得因加载新规则而搬迁、重算旧审批或重写旧任务。同一修订版保持布局不变；切新版时将旧布局连同状态保存到旧版快照，再采用布局 2。未知布局或状态/任务布局不一致时阻塞。

```text
<需求名称>/
  README.md                         # 当前版本、进度、待确认事项和正式成果索引
  status.yaml
  events.jsonl
  revisions/vN/
    input.md
    documents.yaml                  # 有覆盖策略时创建
    documents/                      # 正式成果，按阶段实际生成
      requirements.md
      development.md                # 简版；完整版改为方案/计划/自验三份
      test-report.md
    .workflow/
      review-manifest.yaml
      issue-sync/<sync_key>/        # 可选：关键事件的record.yaml与comment.md
      runs/<run_id>/
        task.yaml
        host.yaml
        effective-config.yaml
        result.yaml
        outputs/                    # 候选文稿、必要脚本及执行证据
        sources/                    # 有必需外部来源时创建
        tmp/                        # 可清理缓存，仅需要时创建
```

完整版开发文档为 technical-plan.md、implementation-plan.md、verification.md；测试确有必要才增加 test-cases.md。不预建空文件、空目录或每个任务一套报告。业务源码和项目测试仍在 target_project 的授权路径，不放 documents/。

## 角色写入与结果

任务路径、布局兼容、结果引用及执行角色写入边界统一按 [阶段执行契约](execution-contract.md) 填写和核对；协调层将 output_dir、result_path 及必要临时授权显式写入 task。

## 固化正式成果

1. 任务确已结束，协调层核对身份、当前版本/run、必要结果、产物边界及适用代码基线，再选择实际文稿。按结果的 kind 选择：产品 ready 固化 requirements（quality_check 指向同文稿时不复制第二份）；开发 ready 固化 development_record，或 technical_plan、implementation_plan、verification；测试的 passed/failed/blocked 报告在交接有效时均可固化，状态和未执行项须如实展示。其他问题或阻塞仅在需求入口说明，不冒充正式交付。
2. 仅将文稿按上述固定文件名固化到 documents/；脚本、日志、基线和 sources 留在原 run。使用副本，不用硬链接/符号链接把已批准内容绑定到可变候选。文稿中本地引用写为 Markdown 相对链接；固化时先将来源目标和正式文稿父目录都解析为真实路径，再以同一基准计算相对链接（包括 /var 与 /private/var 等宿主路径别名），重新定位到正式文稿或原 run 的实际证据，并从落盘的正式文件位置实际验证每个链接可读。重定位后的正文才是评审和审批对象，不能沿用候选文稿的摘要。未经索引的附加文稿不自动发布。
3. 写入前核对目标与来源真实路径不冲突。目标已存在时，只有根 artifacts 明确记录为本版受管理的正式文稿且当前摘要匹配，才可更新；同摘要可保留。用户修改、来源不明内容或符号链接冲突时停止。已批准 requirements.md 及其审批 manifest 不原地替换，范围变化走新修订。旧 run 候选和有效失败证据保留，正式位置只代表本版当前有效报告。
4. 文件采用同目录临时文件准备后原子替换；记录正式 path、kind、revision、run_id、sha256、source_path（相对需求目录的候选位置）及 source_sha256 到根 artifacts，并保留该 run 的原始产物索引。确认文件及引用有效后再推进状态，最后按实际状态更新 README。固化中断时先比较候选、目标、已存索引与状态，只有能证实同一有效 run 的同内容写入才补完；不一致则阻塞，不猜测成功。
5. 修复轮次进入新开发/测试 run 时，入口将旧报告标记为“上一基线，当前待重验”；新报告完成交接后才更新正式文件及其来源索引。不得让上一轮 passed 看起来已覆盖新代码。切新版时入口指向新版，旧版文档和审批保留。

## 人工入口

协调层使用 [需求入口模板](../templates/feature-readme.md) 创建需求根 README.md。只列当前版本、阶段、真实进度、待确认事项、已存在的正式文档及其来源 run；启用 Issue 时按 [Issue 规则](issue-tracking.md) 补真实绑定链接及未完成/未知同步提示（包括旧目标），从未启用且无历史记录时省略；不重复文档正文、日志或完整验收表。未产出、过期、失败、阻塞要明确标注。默认人工确认当前 requirements.md，交付时看 test-report.md 与实际功能；技术决策需要人时链接适用开发文档，不新增所有阶段的强制审批。

README 是派生索引，不代替状态或审批；恢复时核对 status.yaml 并修正索引。生成后在根 artifacts 记录 kind: feature_index、path: README.md 和 sha256；下次只更新可由索引及摘要确认属于框架的入口。已有用户 README 或入口被用户编辑时不覆盖，先报告冲突。旧布局可在无路径冲突时生成指向已有文稿的入口，不搬旧文档。对话同步给出该需求目录、版本和待办。

## 保留与清理

- 保留：输入、正式文稿、审批、状态/事件、任务/结果、有效配置、必要 Issue 绑定与同步记录，以及复现结论/缺陷所必需的来源、脚本和执行证据。同一检查保留一份原始输出并引用，不为父层或多个报告重复抄存。无外部来源时 review manifest 的 sources 为 []，不新建空 sources/；旧来源清单继续校验。
- 仅清理：已确认任务结束、无恢复依赖且没有任何产物/审批/证据引用的本次 tmp/ 内容。核对真实路径及归属后清理，活动任务、来源不明残留、必要失败证据和历史版本不自动删除。不按天数或“已完成”批量删除 runs/。
- 框架开发验证：完整安装副本、一次性检查和重复源快照默认在宿主临时目录；仓库仅留精简结论及必要可复现证据，正常闭环示例保留一套。不复制整个隔离项目作为每轮修复的新归档；历史证据保持原索引，不追溯清空。共享核心不包含这些测试现场。
