#!/usr/bin/env python3
"""Read-only Protocol 4 structural, topological, tree-purity, and size invariants verification (v2.0.0)."""

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402
import urllib.parse  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

ENTRY_FILES = [
    "agents/coordinator-agent.md",
    "agents/product-agent.md",
    "agents/development-agent.md",
    "agents/testing-agent.md",
    "agents/bug-agent.md",
    "workflow/routing.md",
    "workflow/execution-contract.md",
    "workflow/documents.md",
    "workflow/handoff.md",
    "workflow/host-adapters.md",
    "workflow/config.md",
    "skills/requirement-analysis/SKILL.md",
    "skills/feature-development/SKILL.md",
    "skills/bug-fixing/SKILL.md",
    "skills/acceptance-testing/SKILL.md",
    "skills/setup-requirement-workflow/SKILL.md",
    "skills/issue-tracking/SKILL.md",
    "skills/setup-requirement-workflow/assets/templates/role-body.md",
    "skills/setup-requirement-workflow/assets/templates/project-entry-light.md",
]

MAX_PACKAGE_FILES = 58
MAX_PACKAGE_BYTES = 153000
MAX_ENTRY_LINES = 20
MAX_ENTRY_BYTES = 2200
MAX_AGENT_LINES = 20

FORBIDDEN_RUNTIME_HASH_TERMS = (
    "package_digest",
    ".local.json",
    "codex-bootstrap",
    "bootstrap.md",
    "package.md",
    "sha256sum",
    "shasum",
    "hashlib.sha256",
    "安装回执",
)

RETIRED_TEMPLATES = (
    "skills/feature-development/assets/templates/implementation-plan.md",
    "skills/feature-development/assets/templates/technical-plan.md",
    "skills/feature-development/assets/templates/verification.md",
    "skills/acceptance-testing/assets/templates/test-report.md",
    "skills/requirement-analysis/assets/templates/requirements.md",
    "skills/feature-development/assets/templates/technical-design.md",
)

REQUIRED_TEMPLATES = (
    "templates/task.md",
    "templates/spec.md",
    "skills/acceptance-testing/assets/templates/verification.md",
    "skills/bug-fixing/assets/templates/bug-report.md",
)

OBSOLETE_WORKFLOW_TERMS = (
    "不增加统一人工阶段审批",
    "审查不新增统一人工批准",
    "小需求目标清楚即可执行，不强制再写需求稿和统一批准",
    "Lite / Standard / Complex",
    "Lite、Standard、Complex",
    "pending_design_approval",
    "req_approved",
    "STOP 1",
    "STOP 2",
    "requirements.md",
    "technical-design.md",
)

STAGE_STATES_FULL = (
    "pending_approval",
    "ready_to_implement",
    "verified",
    "blocked",
    "pending_req_approval",
)
STAGE_STATES_CORE = (
    "pending_approval",
    "ready_to_implement",
    "verified",
)

HARD_CAP = re.compile(
    r"(?:[≤≦<]=?|不(?:得)?超过|最多|至多|上限|no more than|at most|max(?:imum)?(?:\s+of)?)\s*[5五]\s*"
    r"(?:条|个|项|items?|questions?|Qs?\b)|[5五]\s*(?:条|个|项)\s*以内",
    re.I,
)
SELF_CHECK_FILLER = re.compile(r"起草者自查|自查清单|自检清单|作者自检")
TABLE_CHECKBOX = re.compile(r"(?:\||<br\s*/?>)[ \t]*(?:[-+*][ \t]+)?\[[ xX]\](?=[ \t|]|$)", re.M)
NON_TASK_CHECKBOX = re.compile(
    r"^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[[ xX]\](?:[ \t]+|$)", re.M
)


def _iter_package_files(root: Path):
    for name in ("framework.yaml", "AGENTS.md", "README.md", "workflow.yaml", "LICENSE"):
        p = root / name
        if p.is_file():
            yield p
    for directory in ("agents", "skills", "workflow", "templates"):
        base = root / directory
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(root).as_posix()
            if rel == "skills/system" or rel.startswith("skills/system/"):
                continue
            if p.name in {"__pycache__", ".DS_Store"} or p.suffix in {".pyc", ".pyo"}:
                raise AssertionError(f"dirty_package_artifact_present: {rel}")
            if p.is_dir():
                visible_children = [
                    child
                    for child in p.iterdir()
                    if child.relative_to(root).as_posix() != "skills/system"
                ]
                assert visible_children, f"empty_package_directory_present: {rel}"
                continue
            if p.is_file():
                yield p


def _strip_blocks_and_comments(markdown_text: str, *, strip_inline_code: bool = False) -> str:
    stripped = re.sub(r"```.*?```|~~~.*?~~~", "", markdown_text, flags=re.S)
    stripped = re.sub(r"<!--.*?-->", "", stripped, flags=re.S)
    if strip_inline_code:
        stripped = re.sub(r"`[^`\n]*`", "", stripped)
    return stripped


def _heading_anchors(markdown_text: str) -> set[str]:
    """Extract GitHub-Flavored Markdown heading anchors outside code fences and HTML comments."""
    stripped = _strip_blocks_and_comments(markdown_text, strip_inline_code=False)
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for match in re.finditer(r"(?m)^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*#*$", stripped):
        raw = match.group(1)
        raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
        raw = raw.replace("`", "").strip().lower()
        raw = re.sub(r"[ \t]+", "-", raw)
        chars = [
            ch
            for ch in raw
            if ch in {"-", "_"} or unicodedata.category(ch)[0] in {"L", "N", "M"}
        ]
        slug = "".join(chars)
        if not slug:
            continue
        seen = counts.get(slug, 0)
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
        counts[slug] = seen + 1
    return anchors


def check_local_rule_links(root: Path) -> int:
    """Validate local Markdown file & GFM #anchor links across all package .md files."""
    resolved_root = root.resolve()
    anchor_cache: dict[Path, set[str]] = {}

    def get_anchors(md_path: Path) -> set[str]:
        rp = md_path.resolve()
        if rp not in anchor_cache:
            anchor_cache[rp] = _heading_anchors(rp.read_text(encoding="utf-8"))
        return anchor_cache[rp]

    checked = 0
    for path in _iter_package_files(root):
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        raw_text = path.read_text(encoding="utf-8")
        stripped = _strip_blocks_and_comments(raw_text, strip_inline_code=True)
        for target in re.findall(r"\]\(([^)\s]+)\)", stripped):
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                continue
            if "{" in target or target.startswith("<"):
                continue
            checked += 1
            if target.startswith("#"):
                anchor = urllib.parse.unquote(target[1:])
                if anchor:
                    assert anchor in get_anchors(path), (
                        f"linked_anchor_missing: {rel} -> {target}"
                    )
                continue
            file_part, sep, frag = target.partition("#")
            destination = (path.parent / urllib.parse.unquote(file_part)).resolve()
            try:
                destination.relative_to(resolved_root)
            except ValueError as exc:
                raise AssertionError(f"linked_rule_outside_package: {rel} -> {target}") from exc
            assert destination.is_file(), f"linked_rule_missing: {rel} -> {target}"
            if sep and frag and destination.suffix == ".md":
                anchor = urllib.parse.unquote(frag)
                assert anchor in get_anchors(destination), (
                    f"linked_anchor_missing: {rel} -> {target}"
                )
    return checked


def check(root: Path, baseline: Path = None, *, require_smaller: bool = False) -> dict:
    for rel in ENTRY_FILES:
        assert (root / rel).is_file(), f"linked_rule_missing: {rel}"
    assert (root / "LICENSE").is_file(), "required_package_file_missing: LICENSE"
    for rel in RETIRED_TEMPLATES:
        assert not (root / rel).exists(), f"retired_template_present: {rel}"
    for rel in REQUIRED_TEMPLATES:
        assert (root / rel).is_file(), f"required_template_missing: {rel}"
    texts = {p: (root / p).read_text(encoding="utf-8") for p in ENTRY_FILES}

    # 1. Version & Protocol Schema
    framework = yaml.safe_load((root / "framework.yaml").read_text(encoding="utf-8"))
    lock = yaml.safe_load(
        (root / "skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert framework["schema_version"] == 1
    assert framework["name"] == "multi-agent-requirement-workflow"
    assert isinstance(framework["version"], str) and framework["version"].strip()
    assert framework["version"] == "2.0.0", (
        f"version_mismatch: framework.yaml -> {framework['version']}"
    )
    assert type(framework["protocol_version"]) is int and framework["protocol_version"] == 4
    assert lock["package"]["protocol_version"] == framework["protocol_version"]

    for meta_name in ("README.md", "AGENTS.md"):
        meta_path = root / meta_name
        if meta_path.is_file():
            meta_text = meta_path.read_text(encoding="utf-8")
            assert (
                framework["version"] in meta_text
                and "1.0." not in meta_text
                and "v1." not in meta_text
            ), f"version_mismatch: {meta_name}"

    # 2. Tree Purity & Upper-bound Entry / Package Budgets (per-file checks before aggregate cap)
    pkg_files = list(_iter_package_files(root))
    pkg_file_count = len(pkg_files)
    pkg_total_bytes = sum(p.stat().st_size for p in pkg_files)
    assert pkg_file_count <= MAX_PACKAGE_FILES, f"package_files_exceeded: {pkg_file_count}"

    for rel, body in texts.items():
        if rel.startswith("agents/"):
            line_cnt = len(body.splitlines())
            assert line_cnt <= MAX_AGENT_LINES, f"agent_lines_exceeded: {rel} ({line_cnt})"

    entry = texts["skills/setup-requirement-workflow/assets/templates/project-entry-light.md"]
    entry_lines = entry.splitlines()
    entry_bytes = len(entry.encode("utf-8"))
    assert len(entry_lines) <= MAX_ENTRY_LINES, f"entry_lines_exceeded: {len(entry_lines)}"
    assert entry_bytes <= MAX_ENTRY_BYTES, f"entry_bytes_exceeded: {entry_bytes}"
    assert "```" not in entry, "entry_forbids_inline_code_blocks"
    assert not re.search(r"\]\((?:workflow|skills|agents|templates)/", entry), (
        "entry_forbids_consumer_relative_links"
    )
    assert "## 需求协作入口" in entry, "entry_heading_missing"

    claude_entry = (
        root / "skills/setup-requirement-workflow/assets/templates/claude-entry.md"
    ).read_text(encoding="utf-8")
    for ceremonial in ("你是需求协作框架", "协议 4"):
        assert ceremonial not in entry, f"ceremonial_entry_label_forbidden: {ceremonial}"
        assert ceremonial not in claude_entry, f"ceremonial_claude_label_forbidden: {ceremonial}"

    project_entry_path = root / "AGENTS.md"
    if project_entry_path.is_file():
        project_entry = project_entry_path.read_text(encoding="utf-8")
        begin_marker = "<!-- requirement-workflow:begin -->"
        end_marker = "<!-- requirement-workflow:end -->"
        assert begin_marker in project_entry and end_marker in project_entry, (
            "project_entry_managed_markers_missing"
        )
        b_idx = project_entry.index(begin_marker)
        e_idx = project_entry.index(end_marker) + len(end_marker)
        managed_block = project_entry[b_idx:e_idx] + "\n"
        assert managed_block == entry, "project_entry_managed_block_drift"

    assert pkg_total_bytes <= MAX_PACKAGE_BYTES, f"package_bytes_exceeded: {pkg_total_bytes}"

    role = texts["skills/setup-requirement-workflow/assets/templates/role-body.md"]
    assert "framework_cache_missing" in role
    for ceremonial in ("你是需求协作框架", "当前宿主原生名称为", "协议 4"):
        assert ceremonial not in role, f"ceremonial_role_label_forbidden: {ceremonial}"
    assert "<缓存根>/{{role_file}}" in role and "<缓存根>/{{skill_file}}" in role, (
        "professional_delegation_role_loading_missing"
    )

    # 3. Template Orthogonality, Zero Dual-Write Status Header on spec.md & Format Redlines
    task_tpl = (root / "templates/task.md").read_text(encoding="utf-8")
    for req in ("阶段状态", "批准记录", "本次请确认", "- [ ]"):
        assert req in task_tpl, f"task_template_missing: {req}"

    spec_tpl = (root / "templates/spec.md").read_text(encoding="utf-8")
    for forbidden_status in ("阶段状态", "批准记录", "结论状态"):
        assert forbidden_status not in spec_tpl, (
            f"spec_template_mutable_status_forbidden: {forbidden_status}"
        )
    for required_heading in ("## 1. 目标、边界与验收标准", "## 2. 架构取舍、接口契约与单元切分"):
        assert required_heading in spec_tpl, f"spec_template_section_missing: {required_heading}"

    for report_rel in (
        "skills/acceptance-testing/assets/templates/verification.md",
        "skills/bug-fixing/assets/templates/bug-report.md",
    ):
        report_text = (root / report_rel).read_text(encoding="utf-8")
        assert "结论状态" in report_text, f"template_first_screen_status_missing: {report_rel}"

    for non_task_rel in (
        "templates/spec.md",
        "skills/acceptance-testing/assets/templates/verification.md",
        "skills/bug-fixing/assets/templates/bug-report.md",
    ):
        non_task_text = (root / non_task_rel).read_text(encoding="utf-8")
        assert not NON_TASK_CHECKBOX.search(non_task_text), (
            f"non_task_template_checkbox_forbidden: {non_task_rel}"
        )

    for path in pkg_files:
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        body = path.read_text(encoding="utf-8")
        assert not HARD_CAP.search(unicodedata.normalize("NFKC", body)), (
            f"confirmation_hard_cap_forbidden: {rel}"
        )
        assert not TABLE_CHECKBOX.search(body), f"table_checkbox_forbidden: {rel}"
        for dead in FORBIDDEN_RUNTIME_HASH_TERMS:
            assert dead not in body, f"runtime_hash_or_receipt_dead_word: {rel} -> {dead}"
        for term in OBSOLETE_WORKFLOW_TERMS:
            assert term not in body, f"obsolete_workflow_term: {rel} -> {term}"
        if ("/assets/templates/" in rel or rel.startswith("templates/")) and (
            "setup-requirement-workflow" not in rel
        ):
            assert not SELF_CHECK_FILLER.search(body), (
                f"template_self_check_filler_forbidden: {rel}"
            )

    # 4. Key Mechanism Identifiers Bound to Authoritative Files
    execution = texts["workflow/execution-contract.md"]
    routing = texts["workflow/routing.md"]
    documents = texts["workflow/documents.md"]
    handoff = texts["workflow/handoff.md"]
    host_adapter = texts["workflow/host-adapters.md"]

    for rel, body in (
        ("workflow/execution-contract.md", execution),
        ("workflow/documents.md", documents),
        ("templates/task.md", task_tpl),
    ):
        for state in STAGE_STATES_FULL:
            assert state in body, f"stage_state_missing: {rel} -> {state}"
    for state in STAGE_STATES_CORE:
        assert state in entry, f"stage_state_missing: project-entry-light.md -> {state}"

    for rel, body in (
        ("workflow/routing.md", routing),
        ("workflow/execution-contract.md", execution),
        ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", entry),
        ("skills/setup-requirement-workflow/assets/templates/claude-entry.md", claude_entry),
    ):
        assert "Spec Gate" in body, f"spec_gate_identifier_missing: {rel}"

    for rel, body in (
        ("workflow/routing.md", routing),
        ("workflow/execution-contract.md", execution),
        ("skills/feature-development/SKILL.md", texts["skills/feature-development/SKILL.md"]),
    ):
        assert "Spike" in body, f"spike_identifier_missing: {rel}"

    dev_principles = (
        root / "skills/feature-development/references/development-principles.md"
    ).read_text(encoding="utf-8")
    for rel, body in (
        ("workflow/execution-contract.md", execution),
        ("skills/feature-development/SKILL.md", texts["skills/feature-development/SKILL.md"]),
        ("skills/feature-development/references/development-principles.md", dev_principles),
    ):
        assert "Contract-First" in body and "SDD" in body, (
            f"contract_first_sdd_identifier_missing: {rel}"
        )

    codex_adapter = (
        root / "skills/setup-requirement-workflow/references/codex-adapter.md"
    ).read_text(encoding="utf-8")
    for rel, body in (
        ("skills/setup-requirement-workflow/assets/templates/project-entry-light.md", entry),
        ("workflow/execution-contract.md", execution),
        ("skills/setup-requirement-workflow/references/codex-adapter.md", codex_adapter),
    ):
        assert "accepted:true" in body, f"async_receipt_identifier_missing: {rel}"

    opencode_adapter = (
        root / "skills/setup-requirement-workflow/references/opencode-adapter.md"
    ).read_text(encoding="utf-8")
    for rel, body in (
        ("workflow/handoff.md", handoff),
        ("agents/testing-agent.md", texts["agents/testing-agent.md"]),
        ("skills/setup-requirement-workflow/references/opencode-adapter.md", opencode_adapter),
    ):
        assert "sessionID" in body, f"session_isolation_identifier_missing: {rel}"

    # 5. Topological Link & Pointer Reachability
    local_rule_links = check_local_rule_links(root)

    for stage in ("requirement-analysis", "feature-development"):
        rel = f"skills/{stage}/SKILL.md"
        body = texts[rel]
        assert "../../templates/spec.md" in body and "../../templates/task.md" in body, (
            f"spec_or_task_template_pointer_missing: {rel}"
        )

    assert "assets/templates/verification.md" in texts["skills/acceptance-testing/SKILL.md"], (
        "report_template_pointer_missing: skills/acceptance-testing/SKILL.md"
    )
    assert "assets/templates/bug-report.md" in texts["skills/bug-fixing/SKILL.md"], (
        "report_template_pointer_missing: skills/bug-fixing/SKILL.md"
    )

    for stage in ("requirement-analysis", "feature-development", "acceptance-testing", "bug-fixing"):
        rel = f"skills/{stage}/SKILL.md"
        assert "../../workflow/documents.md#人读文档格式" in texts[rel], (
            f"document_format_pointer_missing: {rel}"
        )

    confirmation_consumers = [
        *[p for p in ENTRY_FILES if p.startswith("agents/")],
        "skills/requirement-analysis/SKILL.md",
        "skills/feature-development/SKILL.md",
        "skills/acceptance-testing/SKILL.md",
        "skills/bug-fixing/SKILL.md",
    ]
    for path in confirmation_consumers:
        assert "execution-contract.md#人工确认" in texts[path], (
            f"confirmation_pointer_missing: {path}"
        )

    design_decomp = (
        root / "skills/feature-development/references/design-and-decomposition.md"
    ).read_text(encoding="utf-8")
    for rel, body in (
        ("skills/acceptance-testing/SKILL.md", texts["skills/acceptance-testing/SKILL.md"]),
        ("skills/bug-fixing/SKILL.md", texts["skills/bug-fixing/SKILL.md"]),
        ("skills/feature-development/SKILL.md", texts["skills/feature-development/SKILL.md"]),
        ("skills/feature-development/references/design-and-decomposition.md", design_decomp),
    ):
        assert "execution-contract.md#契约先行与分层验证" in body, (
            f"contract_verification_pointer_missing: {rel}"
        )

    for path, body, pointer in [
        ("agents/coordinator-agent.md", texts["agents/coordinator-agent.md"], "../workflow/routing.md"),
        ("workflow/routing.md", routing, "host-adapters.md#业务派发与降级路径"),
        (
            "workflow/host-adapters.md",
            host_adapter,
            "../skills/setup-requirement-workflow/references/codex-adapter.md#无具名选择参数时的业务独立协作",
        ),
    ]:
        assert f"]({pointer})" in body, f"professional_delegation_pointer_missing: {path}"

    before = (
        sum((baseline / p).stat().st_size for p in ENTRY_FILES)
        if baseline is not None
        else None
    )
    after = sum(len(t.encode("utf-8")) for t in texts.values())
    if require_smaller:
        assert before is not None, "size_baseline_required"
        assert after < before, f"rule_size_not_reduced: {before} -> {after}"

    return dict(
        framework=framework,
        protocol=framework["protocol_version"],
        entry_files=len(texts),
        entry_lines=len(entry_lines),
        entry_bytes=entry_bytes,
        package_file_count=pkg_file_count,
        package_total_bytes=pkg_total_bytes,
        local_rule_links=local_rule_links,
        scenarios=[
            "light-kernel-upper-bound-size-and-entry-budget",
            "managed-entry-byte-sync-and-tree-purity",
            "install-time-verification-zero-runtime-hash",
            "uncertainty-driven-spec-gate-and-controlled-spike",
            "zero-duplication-task-and-spec-orthogonal-templates",
            "contract-first-sdd-tdd-stratified-verification",
            "full-package-gfm-heading-anchor-and-topology-reachability",
            "obsolete-dual-gate-and-split-template-term-elimination",
            "session-isolation-and-async-receipt-identifiers",
        ],
        selected_rule_utf8_bytes=dict(
            before=before,
            after=after,
            delta=after - before if before is not None else None,
            reduction_required=require_smaller,
        ),
        scope="structural, topological, and tree-purity invariants only; zero prose snapshot coupling",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--baseline-root", type=Path, help="optional complete baseline for size reporting")
    parser.add_argument("--require-smaller", action="store_true", help="require size reduction vs baseline")
    args = parser.parse_args()
    if not __debug__:
        parser.error("assertions required; do not use -O")
    if args.require_smaller and args.baseline_root is None:
        parser.error("--require-smaller requires --baseline-root")
    baseline = args.baseline_root.resolve() if args.baseline_root is not None else None
    print(
        json.dumps(
            check(args.source_root.resolve(), baseline, require_smaller=args.require_smaller),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
