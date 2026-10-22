# 通用交接

## 派发

协议2按[持续任务的调用与授权](continuous-tasks.md#调用与授权)准备/续接既有角色任务；按需首次读取[产品任务](../templates/product-task.yaml)或[角色任务](../templates/role-task.yaml)。布局4按[增量基线](incremental-changes.md#最小基线与历史)把当前baseline_id和approval_digest放本次授权并核对输入覆盖；产品候选分析不冒用旧批准范围。只在首次创建task，后续追加必要授权版本和host调用，不复制任务包。派发消息只传工作空间、task路径、本次invocation_id、真实framework_root及必要变化；授权以该调用绑定版本为准，消息矛盾blocked。

调用前完整准备task、输入及适用快照，host追加unknown，根active_run绑定该task+invocation并预留适用attempt；回读后调用正确原生角色。获得实际ID再写running；宿主没有call_id时null并注明限制，Agent ID另存agent_id。unknown/running仅宿主事实更新，不生成业务事件；结束先写真实ended_at/end_evidence再交接。未知调用/部分写入先恢复，不因目录或task存在推断已调用/已结束。

旧协议1必须加载原锁定包的handoff与模板；不以本版模板续写旧run。缺原包blocked，不自动迁移。

## 产品结果

产品只有真实评审稿才追加[产品交付](../templates/product-result.yaml)，ready含requirements文稿、自检和唯一acceptance_ids，问题未解决不得ready；方向认可不代替正式稿审批。中间问题按下节记录，不生成完整result或空输出目录。阻塞/过期按执行契约轻记录，旧交付不覆盖。交接核对由[路由](routing.md#交接核对)统一执行。

## 澄清记录与再次派发

沿用当前修订input.md，产品轻返回、协调单写稳定题id、question/impact、必要选项/推荐及真实依赖；语义变化新题id并注明替代。协调只追加用户原话、题映射及必要待处理/已处理关联，不重复整轮累计目标/问卷。原问题可引用input位置，不复制。缺依赖证据/新范围变化交原产品分析，不能代选。

部分回答未改变其他前提时等待；有实质分析需要或答案齐全才续原task。调用结束、等待与待处理输入分别按[协调与澄清](continuous-tasks.md#协调与澄清)处理。input已保存/task已准备不等于已处理，必须有覆盖输入的真实调用/交付关联；重复消息不执行也不遮蔽待处理变化。活动调用存在时只积累输入，先确认其结束与输入覆盖，不接受过时ready。
