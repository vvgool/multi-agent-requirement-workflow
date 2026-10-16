# 全量自检问题修复

> 本报告记录执行当时的版本与验证范围；当前能力及后续记录见 [验证索引](README.md)。不将旧统计或未验证项改写为本轮通过。

修正当前 run 输出路径、初始化中断恢复和历史文档时态，并删除确认为空的 scripts/、.claude/、.opencode/。保留历史需求、证据与兼容指针，不新增 CLI 或依赖。

## 修复与验证

| 问题 | 修复 | 实际验证 |
| --- | --- | --- |
| 默认输出位于目标项目内却被禁止 | [交接规则](../../workflow/handoff.md) 明确允许项目内当前需求/run 的 outputs，并保持真实路径边界 | 隔离产品任务 ready，文稿与自检合并一份；11 项检查通过，输入、状态、源码不变 |
| 安装中断只有残留，没有恢复依据 | [安装流程](../../skills/setup-requirement-workflow/references/codex-installation.md) 先存 pending 计划，再逐文件原子写入；按 before/after 摘要恢复 | 空格目录安装、部分落盘续装、完整清单与 pending 共存均通过；用户修改残留及无记录残留均阻塞且不覆盖 |
| 旧设计和验证记录被误读为当前状态 | 五份旧记录增加历史标记及当前入口 | 本地引用检查通过，历史正文未抹除 |

安装验证由独立 Agent 在临时目录按 Skill 执行，使用一次性 Python 辅助文件操作；辅助程序没有进入交付核心。中断是预设逐文件检查点，不是操作系统崩溃。初次测试后只补充了控制文件例外及计划内原生角色的说明，未改变实际执行分支；测试时与最终源摘要分别归档。

父 Agent 独立核对产品所有前置文件摘要、三份最终安装的全部文件/链接摘要及中断已写文件保留情况。四个 Skill 校验、45 个核心文件的 87 条本地引用、全目录结构化文件解析及旧安装证据完整性均通过。验收旧夹具复跑：正确实现 5 项通过，故意偏离实现仍出现预期的 2 项失败。

证据：[产品检查](evidence/audit-fixes-2026-10-15/product-checks.json)、[安装检查](evidence/audit-fixes-2026-10-15/installation-checks.json)、[中断计划](evidence/audit-fixes-2026-10-15/interrupted-plan.json)、[续装清单](evidence/audit-fixes-2026-10-15/resumed-manifest.json)、[静态检查](evidence/audit-fixes-2026-10-15/static-checks.json)。完整隔离现场路径保留在检查记录中；归档为精简证据，不作为可搬迁执行项目。

## 未验证边界

Codex 原生角色在新会话中的发现/调用、用户真实审批后的完整开发—测试—修复闭环仍待验证；Claude Code/OpenCode 专用适配、真实飞书读写、自动升级/卸载未完成。没有标记业务需求 completed，也没有新增审批或生产发布。
