# 需求协作 Agent 框架

本目录包含一套由多个角色 Agent 协作完成需求的基础框架。

用户明确要求安装、初始化、补本机环境或升级时，读取 [通用初始化Skill](skills/setup-requirement-workflow/SKILL.md)，识别当前宿主并保留项目规则。新项目按版本锁和本地忽略缓存安装，不复制整包为业务仓库受管文件。

## 角色

接到用户发起、继续或优化需求的协调任务时，先读取 [协调 Agent](agents/coordinator-agent.md)，并按其条件指针读取共享规则和当前宿主说明。接到带 task.yaml 的产品派发时，先读取 [产品 Agent](agents/product-agent.md)，只处理该任务。单纯维护本框架文件不自动创建业务产品任务。

- coordinator-agent：协调需求阶段流转。
- product-agent：澄清需求，输出需求文档和验收标准。
- development-agent：设计和实现代码。
- testing-agent：执行测试，输出测试报告并反馈缺陷。

阶段执行由 [产品](agents/product-agent.md)、[开发](agents/development-agent.md)、[测试](agents/testing-agent.md) 负责；带 task.yaml 的派发先读对应角色文件。协调层仅负责路由、交接完整性和状态更新，阶段内容检查由执行角色负责。角色文件存在不代表真实调用已验证。

## 共同规则

工作空间根目录由启动协调 Agent 时明确指定；配置从该根目录的 workflow.yaml 读取。workspace.features_dir 默认是 agent-features，相对于工作空间根目录解析；下文 <features_dir> 指解析后的需求根目录。框架安装目录不作为默认工作空间。

1. 需求目录以需求名称命名，内部自动生成唯一且改名不变的 feature_id，用户无需提供标识。
2. 开始工作前先读取 <features_dir>/<需求名称>/status.yaml，核对内部标识和当前修订版本。
3. 每个角色只处理自己负责的阶段。
4. 每次完成工作都要更新状态和产物索引。
5. 没有完成证据时，不得把阶段标记为完成。
6. 暂不自动执行生产发布。
7. 同名需求先判断是原需求续改还是独立需求，不得直接覆盖；范围或验收标准变更使用新修订版，保留历史产物及证据。
8. 每个修订版的需求和验收标准须经用户明确确认后才能进入开发，旧审批不自动适用于新版本。
9. 新需求及新修订的正式成果、执行记录与人工入口按 [成果目录规范](workflow/output-layout.md) 管理；旧版按原索引读取，不迁移审批。
10. 协调 Agent 统一更新阶段和产物索引，其他角色完成时提交产物及证据，由协调 Agent 核对交接完整性后推进状态。

11. 新锁定安装按 [包与版本规则](workflow/package.md) 校验项目绑定和任务身份；派发使用 [宿主适配](workflow/host-adapters.md)。旧快照/审批/任务按兼容路径保留，不自动迁移。

状态流转：draft -> requirement_review -> development -> testing -> completed。测试失败时返回 development。
