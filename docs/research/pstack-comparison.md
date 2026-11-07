# Pstack comparison with Multi-Agent Requirement Workflow

**Research date:** 2026-11-07
**Scope:** Pstack as the first-party product and source repository, compared with this repository's current requirements-collaboration framework.
**Source policy:** Only first-party sources were used for Pstack facts. The main sources are the [official Cursor plugins repository](https://github.com/cursor/plugins/tree/main/pstack), its [Pstack README](https://github.com/cursor/plugins/blob/main/pstack/README.md), the [Pstack manifest](https://github.com/cursor/plugins/blob/main/pstack/plugin.json), and Lauren Tan's [official X article, Part 2](https://x.com/poteto/article/2097732320606507506), which is linked from the article to `x.ai`.

## Executive summary

### Facts

- Pstack is an open-source, MIT-licensed agent plugin authored by Lauren Tan. The official manifest describes it as a collection of rigorous agent workflows, principles, and subagents, not as a model or standalone workflow server. The manifest currently reports version `0.15.36`. ([manifest](https://github.com/cursor/plugins/blob/main/pstack/plugin.json), [README](https://github.com/cursor/plugins/blob/main/pstack/README.md))
- Its main entry point is `/poteto-mode`. It classifies a request into one of 23 playbooks and invokes other skills as needed. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md))
- Its core operating loop is evidence-first engineering. The official materials emphasize grounding in the existing system, narrow changes, parallel exploration or design when useful, and verification against the real behavior rather than treating compilation or a narrow test as proof. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [Part 2](https://x.com/poteto/article/2097732320606507506))
- It is primarily a coding-agent workflow. The source repository provides skills, playbooks, principles, agents, docs, and optional Cursor automation files. ([Pstack tree](https://github.com/cursor/plugins/tree/main/pstack))

### Inference for this repository

Pstack is best viewed as a rigorous execution and verification layer that could complement this repository. It is not a direct replacement for this repository's requirements framework, which has explicit product requirements, technical design, implementation planning, acceptance evidence, role routing, persistence rules, approval boundaries, and host/package integrity controls. This conclusion follows from comparing the official Pstack tree and README with this repository's [README](../../README.md), [workflow](../../workflow.yaml), [role/workflow documentation](../planning/agent-responsibilities-and-workflows.md), and [verification guide](../verification/README.md).

## What Pstack is

### Facts

The official Pstack README presents Pstack as Lauren Tan's personal set of skills used for high-quality engineering work at Cursor. Its stated goal is to write less, higher-quality code and to make parallel agent work trustworthy. The plugin is installed through Cursor's plugin mechanism and has a Claude Code marketplace adapter. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [manifest](https://github.com/cursor/plugins/blob/main/pstack/plugin.json))

The Pstack source is distributed as ordinary repository content. Its main parts are:

- `skills/`, containing `SKILL.md` instructions for routing, investigation, architecture, review, verification, writing, and principles.
- `agents/`, containing `poteto-agent` and `comment-sicko` agent definitions.
- `docs/`, containing the guide and harness material.
- `automations/benny/`, a dormant Cursor automation pack for Slack issue reports.
- plugin metadata and a license. ([Pstack tree](https://github.com/cursor/plugins/tree/main/pstack), [plugin manifest](https://github.com/cursor/plugins/blob/main/pstack/plugin.json))

The official README explicitly says that some referenced features are not bundled in Pstack itself, including `control-cli`, `control-ui`, and `deslop`, which are supplied by the separate Cursor Team Kit plugin. ([README, “not shipped here”](https://github.com/cursor/plugins/blob/main/pstack/README.md#not-shipped-here))

### Inference

Pstack is a process library encoded as agent-readable instructions and host metadata. It is not, in the official source reviewed, a persistent requirements database, a general-purpose workflow engine with a server-side state machine, or an approval-management product.

## Workflow model

### Facts

`/poteto-mode` is the default router. The README lists 23 playbooks covering investigation, bug fixing, performance, runtime and trace forensics, feature work, refactoring, prototyping, visual parity, skill authoring, evals, PR babysitting, shipping, autonomous runs, orchestration, autopilot variants, session pickup, safe pause, multi-phase plans, worktree cleanup, and opening a PR. ([README, “the twenty-three playbooks”](https://github.com/cursor/plugins/blob/main/pstack/README.md#the-twenty-three-playbooks))

The router's documented behavior is to select a playbook, open a todo list containing its steps, and route to supporting skills as the work proceeds. It can invoke skills such as `how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, `tdd`, and `technical-writing`. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md))

Pstack's planning model is deliberately code- and evidence-oriented. The README says that it does not ship a default planning skill because Cursor's plan mode is sufficient and the author prefers code as the best specification. Part 2 describes README-driven development, throwaway prototypes, and a later tactical multi-phase plan when needed. ([README, “why are there no planning skills?”](https://github.com/cursor/plugins/blob/main/pstack/README.md#why-are-there-no-planning-skills), [Part 2](https://x.com/poteto/article/2097732320606507506))

The `architect` skill has explicit phases named Ground, Sketch, Agree, Implement, and Scrap. It grounds the existing system, runs parallel design candidates through `arena`, synthesizes a design, implements against the sketch, and restarts the design if implementation repeatedly contradicts it. ([architect skill](https://github.com/cursor/plugins/blob/main/pstack/skills/architect/SKILL.md))

### Inference for requirements collaboration

Pstack's workflow is optimized for turning an already meaningful engineering request into an evidence-backed implementation. It does not make product discovery, requirement clarification, domain modeling, or formal acceptance specification the universal first gate. Those can be requested through prompts and playbooks, but they are not the same as this repository's explicit requirements and document-routing contracts.

## Agent orchestration

### Facts

Pstack has two declared subagent types in the official plugin: `poteto-agent` for delegates spawned during a `poteto-mode` run, and `comment-sicko` for comment-focused review. ([agents directory](https://github.com/cursor/plugins/tree/main/pstack/agents), [poteto-agent](https://github.com/cursor/plugins/blob/main/pstack/agents/poteto-agent.md))

The orchestration skills use different shapes for different kinds of work:

- `swarm` fans out parallel workers across investigation slices or races, then aggregates one report.
- `arena` runs multiple candidate designs, cross-judges them, picks a base, grafts useful pieces from losing candidates, and verifies the result.
- `architect` uses `arena` for competing interface and module sketches.
- `interrogate` runs adversaries that must prove findings with a failing test, reproduction, or command output. ([swarm](https://github.com/cursor/plugins/blob/main/pstack/skills/swarm/SKILL.md), [arena](https://github.com/cursor/plugins/blob/main/pstack/skills/arena/SKILL.md), [architect](https://github.com/cursor/plugins/blob/main/pstack/skills/architect/SKILL.md), [interrogate](https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md))

Pstack supports per-role model selection. `/setup-pstack` writes a user-level `~/.cursor/rules/pstack-models.mdc` rule with model assignments for implementation, judgment, explorers, arena runners, swarm workers, architect runners, and interrogators. ([setup-pstack](https://github.com/cursor/plugins/blob/main/pstack/skills/setup-pstack/SKILL.md))

The README says the default panel uses Opus and Grok roles, and that the skills use multi-model workflows where useful. ([README, “get started”](https://github.com/cursor/plugins/blob/main/pstack/README.md#get-started))

### Inference

Pstack's orchestration is prompt- and host-driven fan-out, not a durable coordinator service. A Pstack run has a lead chat, spawned workers, local files, worktrees, model configuration, and the host's task/session machinery. This gives it flexible multi-model reasoning but leaves persistence, scheduling, retries, identity, and task accounting to the host and repository conventions.

## Artifacts, state, and memory

### Facts

Pstack's durable artifacts are primarily repository or user files:

- Skills, playbooks, principles, agent definitions, and automation sources live in the plugin repository.
- `/setup-pstack` writes model preferences to `~/.cursor/rules/pstack-models.mdc`.
- The `show-me-your-work` skill defines an optional append-only TSV decision log with one row per decision. It is local by default and is committed only when an auditable trail is needed. ([Pstack tree](https://github.com/cursor/plugins/tree/main/pstack), [setup-pstack](https://github.com/cursor/plugins/blob/main/pstack/skills/setup-pstack/SKILL.md), [show-me-your-work](https://github.com/cursor/plugins/blob/main/pstack/skills/show-me-your-work/SKILL.md))

The `recall` skill reconstructs recent context from agent transcripts under the host's project transcript directory and from shared records searched by the `why` workflow. It returns a compact current-state brief rather than defining a domain database. ([recall](https://github.com/cursor/plugins/blob/main/pstack/skills/recall/SKILL.md))

The official Part 2 article says that Pstack's multi-phase plans may be committed temporarily for large projects and are typically deleted afterward so they do not leave the codebase in a confusing state. ([Part 2](https://x.com/poteto/article/2097732320606507506))

The optional `benny` pack has configuration and feature-map templates intended to be copied into a target repository. Its README says to keep user-owned configuration outside the copied pack and to review a harmless test before enabling the automations. ([benny README](https://github.com/cursor/plugins/blob/main/pstack/automations/benny/README.md), [benny setup](https://github.com/cursor/plugins/blob/main/pstack/automations/benny/FOR_AGENTS.md))

### Inference for this repository

Pstack has useful working memory patterns, especially transcript recall, decision logs, generated setup rules, and temporary plans. It does not appear to provide a canonical, durable requirements record with a stable item identity, status lifecycle, requirement revisions, verification matrix, or cross-session handoff contract. This is a material difference from this repository's single `task.md` coordination entry and separate requirements, technical-design, implementation-plan, and verification documents.

## Approvals and verification

### Facts

Verification is a first-class Pstack principle. The official principle index includes “prove it works,” “fix root causes,” “sequence verifiable units,” and “test behavior, not implementation.” The README repeatedly distinguishes real behavior verification from merely compiling or passing a narrow test. ([README, principles](https://github.com/cursor/plugins/blob/main/pstack/README.md#principles), [prove-it-works](https://github.com/cursor/plugins/blob/main/pstack/skills/principle-prove-it-works/SKILL.md))

The `interrogate` skill keeps only findings proven by a run against the real code. The `architect` skill has no default human checkpoint. It proceeds directly unless the invoker explicitly requests “with checkpoint” or an equivalent pause. ([interrogate](https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md), [architect](https://github.com/cursor/plugins/blob/main/pstack/skills/architect/SKILL.md))

Pstack's `poteto-mode` instructions include an autonomy posture. Reversible work proceeds without asking, while irreversible actions are the stated pause boundary. The README's shipping and babysitting playbooks are designed to drive PRs and CI toward merge-ready or landed states. ([poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md), [README](https://github.com/cursor/plugins/blob/main/pstack/README.md))

The official source does not describe a general product-owner approval gate, a role-based sign-off matrix, or a mandatory approval record for every change. ([Pstack tree](https://github.com/cursor/plugins/tree/main/pstack), [README](https://github.com/cursor/plugins/blob/main/pstack/README.md))

### Inference for this repository

Pstack is stronger than a typical coding prompt at implementation proof and adversarial review. This repository is stronger at explicit authorization and completion governance for requirements work. In particular, this repository's workflow requires confirmation for specified high-risk categories and separates implementation, independent review, and final acceptance. Pstack's default posture favors autonomous progress and optional checkpoints, so adopting it unchanged would not preserve those governance guarantees.

## Integrations and host dependence

### Facts

The official Pstack plugin is hosted in Cursor's plugin marketplace repository. The README documents a Claude Code installation adapter and says that Cursor-only features such as Bugbot or automations are skipped with a note under that adapter. ([README, install](https://github.com/cursor/plugins/blob/main/pstack/README.md#install))

Pstack itself includes no broad catalog of business-system integrations. The `why` skill discovers available MCPs at runtime and can query source control, issue trackers, long-form documents, team chat, observability, error tracking, and analytics when the host exposes matching MCPs. ([why](https://github.com/cursor/plugins/blob/main/pstack/skills/why/SKILL.md))

The optional `benny` automation is Cursor-only and is designed for Slack issue reports. It triages reports and may reproduce confirmed bugs with UI evidence. It is dormant setup material rather than an automatically active slash skill. ([benny README](https://github.com/cursor/plugins/blob/main/pstack/automations/benny/README.md), [Pstack README, automations](https://github.com/cursor/plugins/blob/main/pstack/README.md#automations))

The source README says `control-cli`, `control-ui`, and `deslop` are supplied by the separate `cursor-team-kit` plugin, not by Pstack. ([README, “not shipped here”](https://github.com/cursor/plugins/blob/main/pstack/README.md#not-shipped-here))

### Inference

Pstack's integration boundary is the agent host and its available tools, MCPs, plugins, transcripts, and repository. It can become well integrated with a team's systems, but the integrations are environment-dependent rather than a uniform Pstack data model. This repository's optional issue binding and local document provider are more explicit and conservative, with external writing disabled by default in [`workflow.yaml`](../../workflow.yaml).

## Comparison with this repository

| Dimension            | Pstack                                                                         | Multi-Agent Requirement Workflow                                                                         | Practical reading                                                                                         |
| -------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Primary purpose      | Rigorous AI-assisted software engineering                                      | Requirements clarification, role collaboration, implementation, and acceptance governance                | Complementary rather than equivalent                                                                      |
| Entry model          | `/poteto-mode` routes to playbooks and skills                                  | Main session routes by scope, complexity, risk, role, and persistence need                               | Both route dynamically; this repository makes requirements and governance more explicit                   |
| Planning             | Code-shaped plans, prototypes, README-driven design, optional multi-phase plan | Explicit requirements, technical design, implementation plan, and verification docs for complex work     | Pstack is lighter on durable product artifacts                                                            |
| Orchestration        | Swarm, arena, architect, interrogate, model panels, `poteto-agent`             | Product, development, bug, testing, and coordinator roles, with native tasks only when needed            | Pstack has richer model-level design/review fan-out; this repository has clearer business-role boundaries |
| State and memory     | Transcripts, recall, local decision TSV, temporary plans, user model rule      | Single task entry plus linked durable documents, package locks, handoff facts, and verification evidence | This repository favors durable item identity and recovery                                                 |
| Verification         | Runtime proof, behavior checks, adversarial findings, staged PR/CI flows       | Tests plus acceptance evidence, independent review, final independent acceptance, explicit limitations   | Both are evidence-first; this repository formalizes completion and acceptance more broadly                |
| Approval             | Optional checkpoint; autonomy by default except irreversible actions           | Coordinator approval channel and explicit confirmation for high-risk scope                               | Pstack should not replace the repository's approval rules                                                 |
| Integrations         | Host/MCP dependent, with optional Cursor Slack automation                      | Optional issue binding, local docs, host adapters, external writing disabled by default                  | Different integration philosophies                                                                        |
| Release/installation | Plugin marketplace and host adapters                                           | Locked package identity, integrity verification, installation receipts, host-specific activation checks  | This repository has stronger framework supply-chain and installation governance                           |

The repository-side facts in this table come from [`README.md`](../../README.md), [`workflow.yaml`](../../workflow.yaml), [`docs/planning/agent-responsibilities-and-workflows.md`](../planning/agent-responsibilities-and-workflows.md), [`agents/coordinator-agent.md`](../../agents/coordinator-agent.md), and [`docs/verification/README.md`](../verification/README.md).

## Limitations relevant to a requirements collaboration framework

### Facts from the official Pstack sources

1. **Coding scope.** The official positioning and examples are about codebase exploration, design, implementation, bug fixing, PRs, CI, and runtime verification. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [Part 2](https://x.com/poteto/article/2097732320606507506))
2. **No default planning skill.** Pstack intentionally relies on code, prototypes, host plan mode, and optional playbooks rather than a permanent requirements-planning artifact. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md#why-are-there-no-planning-skills))
3. **Host feature dependence.** Some capabilities are Cursor-only or supplied by separate plugins, and Claude Code behavior has adapter caveats. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md#install), [README](https://github.com/cursor/plugins/blob/main/pstack/README.md#not-shipped-here))
4. **Resource cost.** The official Part 2 article describes multi-agent prototyping and architecture as a deliberate tradeoff involving additional model calls and runtime. ([Part 2](https://x.com/poteto/article/2097732320606507506))
5. **Verification dependency.** Pstack can require a real application, browser, telemetry, MCP, or other tool to verify behavior. The source explicitly treats missing host capabilities as a limitation or skipped step rather than making the capability universal. ([README](https://github.com/cursor/plugins/blob/main/pstack/README.md), [poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md))

### Inference for adoption here

- Pstack should be adopted, if at all, as an execution/review method inside the existing workflow, not as the owner of requirements state.
- The repository should retain its explicit requirements, design, implementation, acceptance, approval, issue-binding, package-lock, and host-adapter contracts.
- Pstack's `how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, and `prove-it-works` ideas are the most directly reusable for development and verification roles.
- Pstack's temporary-plan and autonomous-shipping defaults should be constrained by this repository's single-entry, single-writer, high-risk confirmation, and external-write rules.
- A port would need a compatibility layer for this repository's task identity, document links, native-task references, evidence summaries, and protocol/version rules. This is an architectural inference, not a feature claimed by Pstack.

## Bottom line

Pstack packages disciplined agent behavior for software engineering. Its distinctive strengths are evidence-first execution, competing designs, model-diverse review, runtime verification, and practical recovery from unfamiliar codebases. This repository packages a broader collaboration contract around requirements, roles, durable artifacts, approvals, handoffs, host adapters, and acceptance governance.

The two systems overlap around coordination and verification, but they solve different control problems. Pstack can improve how a development or testing role performs a task. It should not silently become the project's requirements ledger, approval authority, or package/recovery protocol.

## Sources consulted

### First-party Pstack sources

- [Pstack official directory](https://github.com/cursor/plugins/tree/main/pstack)
- [Pstack README](https://github.com/cursor/plugins/blob/main/pstack/README.md)
- [Pstack plugin manifest](https://github.com/cursor/plugins/blob/main/pstack/plugin.json)
- [Pstack `poteto-mode` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md)
- [`architect` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/architect/SKILL.md)
- [`arena` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/arena/SKILL.md)
- [`swarm` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/swarm/SKILL.md)
- [`interrogate` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md)
- [`why` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/why/SKILL.md)
- [`recall` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/recall/SKILL.md)
- [`setup-pstack` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/setup-pstack/SKILL.md)
- [`show-me-your-work` skill](https://github.com/cursor/plugins/blob/main/pstack/skills/show-me-your-work/SKILL.md)
- [Pstack agent definitions](https://github.com/cursor/plugins/tree/main/pstack/agents)
- [Benny automation README](https://github.com/cursor/plugins/blob/main/pstack/automations/benny/README.md)
- [Benny automation setup guide](https://github.com/cursor/plugins/blob/main/pstack/automations/benny/FOR_AGENTS.md)
- [Lauren Tan, “The Complete Guide to pstack Pt. 2”](https://x.com/poteto/article/2097732320606507506)

### Repository sources used for comparison

- [`README.md`](../../README.md)
- [`workflow.yaml`](../../workflow.yaml)
- [`docs/planning/agent-responsibilities-and-workflows.md`](../planning/agent-responsibilities-and-workflows.md)
- [`agents/coordinator-agent.md`](../../agents/coordinator-agent.md)
- [`docs/verification/README.md`](../verification/README.md)
