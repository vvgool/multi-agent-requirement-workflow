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

任务路径、布局兼容、结果引用及执行角色写入边界统一按 [阶段执行契约](execution-contract.md) 填写和核对；协调层将 output_dir、result_path 及必要临时授权显式写入 task。派发和执行检查时按其 [缓存与证据规则](execution-contract.md#缓存与证据) 选择实际输出位置、保存最小持久证据及核对跨轮复用。

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
- 仅清理：协调确认宿主调用确已结束后，逐项核对本轮 tmp/ 或 task 明确授权的临时位置。真实路径必须在授权范围内、归属及创建后已知内容可核实，且所有现有文稿/产物/审批/证据无引用，无 pending/暂存恢复依赖、无用户修改。任一条件无法证明则保留并在现有记录说明原因；执行角色仍活动时保留现场。只允许清理满足全部条件的临时内容，不能用目录整体删除连带移除受保护文件或沿符号链接操作。
- 收敛后核对持久文稿及必要证据链接仍可读，在已有结果交接/状态事件记录清理对象与判断即可，不新增每文件清理报告。outputs/、sources/、历史 run 和必要失败证据继续保留；不按天数、体积或 completed 批量清理，不把 pending 和候选提交暂存误当普通缓存。
- 框架开发验证：完整安装副本、一次性检查和重复源快照默认在宿主临时目录；仓库仅留精简结论及必要可复现证据，正常闭环示例保留一套。不复制整个隔离项目作为每轮修复的新归档；历史证据保持原索引，不追溯清空。共享核心不包含这些测试现场。

## 开发中候选展示

原子提交、身份、摘要与双读检查以 [通知契约](execution-contract.md#开发中方案通知) 为准。开发正常通知后继续同 run；协调收到通知即处理，不能等最终 result 才首次展示。候选仍在 task.output_dir，不复制到 documents/，不另造方案正文；布局1按原task/output/artifacts路径读取，不搬迁历史、不补造旧通知。

核对完整版本后，在对话和需求 README 提供真实可读候选相对链接，标明“开发中方案，未验收”、修订/run、document_version及来源摘要；简版一份记录，完整版适用方案/计划，自验存在后才链接。既有正式开发/测试成果标“上一基线，当前待重验”，不能与候选混成当前正式交付。needs_input/blocked也展示已存在的稿件、缺口及解除条件；full部分稿须为契约允许的plan_partial，标“部分方案，未验收”，不要求缺稿存在、不链接缺稿、不放宽已列稿的整批稳定/摘要/有效链接检查；无稿明确未产出，不生成空成果。

协调以根 artifacts 的 kind: development_progress 记录当前已核对版本：path（清单相对需求目录）、revision、run_id、document_version、sha256（清单摘要）、documents（每项kind/path/sha256，路径相对需求目录）、display_status（pending/displayed/blocked）及实际原因，按 [状态规则](state-contract.md#开发方案展示状态) 维护；该项只是显示来源索引，不能代替代码基线或最终result。先保存pending来源，再安全更新入口及对话，确认实际展示后才记displayed；中断可补未完成展示，同版本已展示不重复处理成新任务。若入口已更新但显示状态未保存，先核对入口已知摘要与同版本内容再补状态；无法确认时保留内容并报告，不覆盖或猜成功。

README沿原 feature_index 拥有摘要规则检查，正式文稿沿原固化摘要规则检查。用户编辑或来源不明时停止覆盖、给出冲突位置及可读链接，记录展示blocked，不把其等同开发停止或成功。协调不同时写候选；开发清单过期或内容半更新只重读/请求开发恢复，不能索引未提交版本。最终ready须先核实宿主结束，按执行契约的结果链接收敛顺序检查末次清单、development_progress指针和最终artifacts摘要一致；未收敛不得固化。核对通过后，再按“固化正式成果”复制、重定位链接及保存来源；通知清单/恢复意图只留run证据，不当正式正文。开发结束后再有冲突也先保护用户内容，不能以最终结果绕过摘要检查。
