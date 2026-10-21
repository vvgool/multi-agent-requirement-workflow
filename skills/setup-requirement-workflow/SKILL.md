---
name: setup-requirement-workflow
description: Initialize or restore a version-pinned requirement workflow in Codex, Claude Code, or OpenCode using thin native role adapters while preserving project configuration.
---

# 通用需求协作初始化

用户要求安装、初始化、补本机环境或明确升级，或协调入口要求按现有锁自动恢复缺失缓存/回执时使用。在宿主内执行文件操作，无独立工作流 CLI，不修改全局目录或真实业务项目之外的环境。共享框架、项目策略与宿主注册分开；文件安装、原生生效和业务闭环分别报告。

1. **定位和选择**：用户提供 GitHub/Git URL 时先按 [Git 获取步骤](references/installation.md#githubgit-url-获取) 在临时目录取得并核实实际提交，再从该提交读取本 Skill；本地包则从本 Skill 定位。确认用户的目标项目与实际宿主；不根据业务项目名称猜宿主，不默认装进框架自身。读取 [包与版本绑定](../../workflow/package.md)、[宿主契约](../../workflow/host-adapters.md)，按 [宿主选择](references/installation.md#宿主选择与批量初始化) 确定目标宿主集合，逐个加载其适配说明。当前支持 codex、claude-code、opencode 的薄文件格式；不等于三个真实宿主均已验证。
2. **读取现状**：restore_only=true 时先读 [启动恢复](../../workflow/bootstrap.md)，只按原锁补本机缓存/回执，不生成或修改受管入口/角色，不扩大宿主集合；配置/入口/角色不完整时报告阻塞，只有明确初始化才可新增。读取项目规则、workflow.yaml、workflow.lock.yaml、本地回执及新旧 pending。已有锁默认恢复同一包，提供了不同源版本也不自动升级。已有旧快照且无新锁时按包规则报告 legacy_snapshot，不覆盖旧入口或暗中迁移。明确升级必须先确认所有相关 active_run 结束。
3. **完整预检**：按 [通用安装步骤](references/installation.md) 核对来源、实际包摘要、所有目标/祖先路径、全部目标宿主的同名角色与已有规则遮蔽，生成变更计划；文件解析、锁/配置、权限或归属不可靠时先停止，不留下半配置。保留用户文件，只增改本框架拥有的区块及薄角色。
4. **安装或恢复**：按同一 pending 意图准备忽略规则、本地内容缓存、版本锁和各目标宿主入口及Codex显式注册区块；不将全包列为待提交文件，不生成 Skill 符号链接。模板须从 assets/templates/ 的真实文件读取。已有无本机回执的克隆项目，按通用流程核对受管入口真实内容后才重建回执，不覆盖未知内容。
5. **分层核验**：包摘要、模板实例、相对路径、角色及入口一致后分别记录每个目标宿主 file_installation=passed。只有当前实际宿主可执行原生探测；其他宿主保留自己的已有有效证据或标记 pending，不继承当前宿主结果。新会话或已证实重载后按宿主契约真实只读探测入口及四个原生角色；缺能力保留 pending，不用通用子 Agent 模拟通过。end_to_end 仅在真实需求闭环后更新。

返回框架版本/摘要、当前宿主、检测依据与目标宿主集合、逐宿主安装/激活结果、需提交的少量路径、忽略的本地目录、真实探测与未完成项。相同安装重复执行不重写；明确升级也不覆盖用户修改、不删旧包、不重算历史审批。真实远程 Issue、文档写入、发布及宿主全局安装不属于初始化。
