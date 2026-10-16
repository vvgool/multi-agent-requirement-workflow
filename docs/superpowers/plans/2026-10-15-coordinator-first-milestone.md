# 协调 Agent 首个闭环 Implementation Plan

> 历史设计/实施记录：仅供追溯，不作为当前待执行计划。当前目标见 [整体规划](../../planning/overall-goals.md)，执行以 agents/、skills/、workflow/ 为准；验证边界见 [验证索引](../../verification/README.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 用户直接在宿主会话中启动协调 Agent，自动调用产品 Agent，形成需求与验收标准并等待用户确认。

**Architecture:** 交付角色说明、宿主入口、共享流程、配置和交接模板。协调 Agent 使用宿主自带的文件工具管理 agent-features，使用原生子 Agent 工具派发任务；没有独立 CLI、额外程序或常驻服务。

**Tech Stack:** Markdown 角色与规则、YAML 配置和状态、宿主原生文件及子 Agent 工具。

**Spec:** [首个闭环设计](../specs/2026-10-15-coordinator-first-milestone-design.md)；[总体设计](../specs/2026-10-15-host-orchestration-design.md)。

## Global Constraints

- 工作空间由用户指定；workspace.features_dir 默认 agent-features，相对该根目录解析。
- 需求名称用于目录，feature_id 用于内部关联，同名续改保留修订版和证据。
- 协调 Agent 唯一负责更新状态；本版仅支持单个协调会话驱动同一需求。
- 人工审批绑定实际展示的修订版和内容；没有明确确认不进入开发。
- 状态检查属于 Agent 执行规范，不宣称具有程序级强制校验、并发锁或事务保证。
- 本里程碑确认后停在 development/blocked，原因为 development_dispatch_not_implemented。
- 飞书实际读写、开发与测试自动循环、Claude Code/OpenCode 的真实调用分别报告进度。
- 不初始化 Git，不发布，不推送。

## Review Focus

- 框架安装目录与工作空间不同：任务 1、5 验证需求仍写到指定工作空间。
- 同名续改与新建歧义：任务 2、5 验证先澄清，旧需求不覆盖。
- 子 Agent 派发结果未知：任务 3、5 验证恢复先核查，不重复启动。
- 飞书权限不足或关键附件未读取：任务 2、5 验证明确阻塞，不沿用旧内容。
- 审批前需求已变化：任务 3、5 验证重新展示及确认，不复用旧批准。

## Task 1：共享规则和配置模板

**Files:** workflow/config.md、workflow/state-contract.md、templates/status.yaml、templates/input.md；现有 workflow.yaml、AGENTS.md。

- [x] 写清配置字段、默认值和覆盖顺序；修订版 documents.yaml 只覆盖文档策略，不修改工作空间。
- [x] 定义状态字段与合法迁移，沿用 feature_id、requirements_revision、state_version、stage、execution_status、approval、active_run、artifacts。
- [x] 提供状态和输入模板，定义更新前重读、更新后回读及不一致时阻塞的步骤。
- [x] 用两个不同工作空间路径检查示例的解析结果，确认规则不依赖框架 cwd。

## Task 2：协调 Agent 定义

**Files:** agents/coordinator-agent.md、workflow/documents.md、workflow/revisions.md。

- [x] 写入按名称识别需求、加载状态与配置、明确目标项目、准备任务、派发、校验、展示评审、记录审批和恢复的有序步骤，每步明确完成条件。
- [x] 定义新建、当前版本修复、新修订版、独立需求四个分支，匹配歧义时询问用户；活动任务未结束时不改名或切版。
- [x] 定义本地和飞书来源、只读建议稿、来源快照、正文版本及审批摘要的关联；优先使用宿主已配置的飞书能力，缺失时说明阻塞。
- [x] 定义待审批内容变化、关键附件缺失和飞书权限不足的停止条件；写入权限需同时满足配置策略和宿主实际权限。
- [x] 按新需求、同名优化、资料缺失、权限不足四个输入逐步检查角色定义，记录能否确定下一动作及产物位置。

## Task 3：最小产品角色和交接模板

**Files:** agents/product-agent.md、templates/product-task.yaml、templates/product-result.yaml、templates/requirements.md、workflow/handoff.md。

- [x] 产品任务包含内部 ID、版本、run_id、角色、绝对需求目录、目标项目、必读文件、答复和输出位置。
- [x] 产品角色先读任务与状态，只写当前 run 产物，返回 ready、needs_input 或 blocked；影响范围或业务规则的未确认假设必须提出问题。
- [x] 产品结果包含身份字段、产物路径、问题和阻塞原因；验收条目必须有唯一编号、前置条件、操作和可观察结果。
- [x] 协调角色检查真实产物及每条验收标准，通过后固化评审稿并进入 requirement_review/waiting_user。
- [x] 在交接规则中明确迟到或旧版结果、缺失产物、结果未知和审批内容变化的处理；审批成功停在本里程碑边界。
- [x] 人工逐项核对任务、结果和状态模板字段一致，不用虚构脚本测试代替角色验证。

## Task 4：宿主入口和使用说明

**Files:** workflow/hosts/codex.md、workflow/hosts/claude-code.md、workflow/hosts/opencode.md；AGENTS.md、README.md。

- [x] 在根 AGENTS.md 中加入启动协调任务和接收产品任务时读取对应角色文件的条件指针。
- [x] Codex 入口提供直接在会话中使用的自然语言示例：加载框架协调角色，指定工作空间，发起或恢复某个名称的需求。
- [x] 记录当前宿主实际暴露的子 Agent 工具，给出派发、保存宿主标识、等待和恢复的步骤；没有子 Agent 能力时明确不支持，不能由协调 Agent 自演其他角色。
- [x] Claude Code 和 OpenCode 使用相同角色契约，分别记录原生加载与调用方式；只依据实际可验证能力编写，未知部分标为未适配，不编造专用配置格式。
- [x] README 说明角色文件不会仅因存在于 agents/ 而自动注册；用户首次加载后由协调 Agent 驱动，不需要手动切换产品角色。
- [x] 将已适配、已验证、未实现区分展示，保留自然语言启动及恢复示例。

## Task 5：真实会话场景验证

**Files:** docs/verification/coordinator-first-milestone.md；本框架需求状态和产物索引。

- [x] 创建独立演示工作空间，用实际 Codex 子 Agent 执行产品任务，保留宿主任务标识、任务输入、产品结果和产物。
- [x] 验证完整输入能够到达 requirement_review/waiting_user；向用户展示真实需求和验收标准，未确认前不进入开发。
- [x] 验证缺少关键业务规则时等待用户、补充后继续；同名优化生成新版本且历史证据保留。
- [x] 验证等待用户时恢复不重复派发；派发结果未知时先核查；旧版本结果不推进新状态。
- [x] 验证指定飞书来源而无法读取时明确阻塞；未完成真实飞书连接验证则报告未验证。
- [x] 真实人工确认尚未发生时保持等待，不编造批准；审批后续路径仅在实际确认后验证。
- [x] 分别记录角色规则检查、真实 Codex 调用、人工确认、飞书及其他宿主的证据和限制。首个里程碑不等于整个框架完成。

## 自审与交接

本计划仅交付可被宿主直接使用的 Agent 规则与入口。检查依据是文件契约一致、真实子 Agent 调用和可观察状态，不引入程序开发、依赖安装或 CLI 使用门槛。建议在当前会话顺序完善上述文件，再按场景验证；产品子 Agent 仅在执行验证时实际调用。
