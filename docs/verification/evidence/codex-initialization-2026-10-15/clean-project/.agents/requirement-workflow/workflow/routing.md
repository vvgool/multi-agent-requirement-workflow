# 阶段路由

协调 Agent 依据刚读取的 status.yaml 选择下一步。各阶段完成标准由对应角色文件定义，本文只定义派发与状态迁移。

## 决策顺序

1. 核对需求身份、版本和状态。已有状态缺失、未知或矛盾时阻塞核查。
2. active_run 非空先查询、等待或重连。prepared/unknown 先核实调用是否发生，即使 execution_status=idle 也不能重复派发。
3. waiting_user 先处理原问题或 pending_review；只有对应当前评审的明确回复才算批准。
4. blocked 先验证解除条件，普通“继续”不能清除阻塞。
5. 无活动任务且允许继续时按下表执行。每次状态变化后重读并重新决策。

| stage | 动作 | 角色 |
| --- | --- | --- |
| draft | 派发澄清与需求整理 | [产品](../agents/product-agent.md) |
| requirement_review | 展示需求并等待用户明确确认 | 协调层转达与记录 |
| development | 派发实现或修复，携带已批准需求和已有缺陷 | [开发](../agents/development-agent.md) |
| testing | 派发验收，携带已批准需求和待测开发基线 | [测试](../agents/testing-agent.md) |
| completed | 展示完成证据；优化按修订规则创建新版 | 无派发 |

派发前检查实际角色文件和宿主能力，缺失分别记录 role_not_available（含 required_role）或 host_delegation_unavailable。development/testing 须有本版有效审批，testing 还须有开发基线。审批已保存但阶段迁移中断时，核对有效性后补完迁移。

## 结果到状态

| 当前角色 / 结果 | 下一状态 |
| --- | --- |
| 产品 ready | 固化角色提供的需求稿，展示后 requirement_review/waiting_user |
| 产品 needs_input | draft/waiting_user，转达具体问题 |
| 用户批准当前评审 | development/idle |
| 开发 ready | 保存角色提供的 development_baseline，testing/idle |
| 开发 needs_input | development/waiting_user，转达决策问题 |
| 测试 passed | completed/idle，归档报告和证据 |
| 测试 failed | development/idle，携带失败报告；次数用尽则 blocked |
| 任一角色 blocked | 保持当前阶段并记录原因、解除条件 |

协调层检查真实任务结束、结果身份及版本、必要字段和产物存在、授权路径及测试基线匹配。角色负责本阶段内容真实性和完成判断；缺少必要报告、证据或结果字段时阻塞，不凭 declared status 推进。旧版或旧 run 结果仅留存，不能清除新 active_run。

## 交接与次数

产品使用 [产品任务](../templates/product-task.yaml) 和 [产品结果](../templates/product-result.yaml)；开发/测试使用 [角色任务](../templates/role-task.yaml) 和 [角色结果](../templates/role-result.yaml)。按所选角色文件填写 completion_criteria；任务 approval_digest 取 approval.review_digest。测试绑定 development_run_id 和 development_baseline，修复任务附 defect_report_path。

开发次数按修订版累计，默认 max_development_attempts=3，包含首次。实际发起新开发调用前增加一次并绑定 run；角色/宿主缺失不增加，未知调用恢复不重复计数。达到上限后 development/blocked、development_attempt_limit，等待用户调整或决策。

同一宿主 Agent 只在同一角色内复用。每次决策记录所读状态版本、阶段、执行状态、动作和原因。状态、历史、审批和范围变更分别遵循 [状态规则](state-contract.md)、[修订规则](revisions.md) 和 [文档规则](documents.md)。
