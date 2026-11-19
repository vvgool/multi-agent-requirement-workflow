#!/usr/bin/env python3
"""Render real Protocol 5 precompiled host roles into an authorized empty fixture directory (stdlib only)."""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--opencode", type=Path, help="optional existing CLI, discovery only")
    args = parser.parse_args()
    if not __debug__:
        parser.error("assertions required; do not use -O")
    root = args.source_root.resolve()
    raw_scratch = args.scratch.absolute()
    scratch = raw_scratch.resolve()
    current = raw_scratch
    linked = False
    while current != current.parent:
        linked |= current.is_symlink()
        current = current.parent
    if (
        linked
        or not scratch.is_dir()
        or any(scratch.iterdir())
        or scratch in {Path("/"), Path.home().resolve(), root}
        or scratch in root.parents
    ):
        parser.error("scratch must be an authorized existing empty ordinary directory")

    templates = root / "skills/setup-requirement-workflow/assets/templates"
    ih_path = root / "skills/setup-requirement-workflow/scripts/install_helper.py"
    reg_path = root / "skills/setup-requirement-workflow/scripts/codex_registry.py"
    ih = _load_module("install_helper_verify", ih_path)
    registry = _load_module("codex_registry_verify", reg_path)

    assert ih.normalize_hosts("zed") == ["agents-md"]
    assert ih.normalize_hosts("codex,zed,agents-md") == ["codex", "agents-md"]

    adapter = (root / "skills/setup-requirement-workflow/references/opencode-adapter.md").read_text(
        encoding="utf-8"
    )
    assert "不创建业务 `host.yaml`" in adapter or "不创建业务host.yaml" in adapter

    assert not (root / "skills/setup-requirement-workflow/references/zed-adapter.md").exists()
    agents_md_adapter = (
        root / "skills/setup-requirement-workflow/references/agents-md-adapter.md"
    ).read_text(encoding="utf-8")
    host_entry = (root / "workflow/host-adapters.md").read_text(encoding="utf-8")
    for rules_text in (agents_md_adapter, host_entry):
        assert "规则型宿主" in rules_text
        assert "AGENTS.md" in rules_text
        assert "agents-md" in rules_text
        assert "native_role_probes" not in rules_text
    assert ".zed/agents" in agents_md_adapter

    if (root / "AGENTS.md").is_file():
        entry = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "requirement-workflow:begin" in entry and "requirement-workflow:end" in entry
    bridge = (templates / "claude-entry.md").read_text(encoding="utf-8")
    for guard in ("AGENTS.md", "明确局部低风险小修", "Spec Gate", "静音连续巡航", "日常零核包开销"):
        assert guard in bridge, f"claude_bridge_missing: {guard}"
    for ceremonial in ("你是需求协作框架", "协议 4", "协议 5"):
        assert ceremonial not in bridge, f"ceremonial_claude_label_forbidden: {ceremonial}"

    with tempfile.TemporaryDirectory() as pkg_tmp:
        staged_pkg = Path(pkg_tmp) / "pkg"
        pkg_info = ih.stage_clean_package(root, staged_pkg, include_working_tree=True)
        pkg_sha = pkg_info["sha256"]
        cache_prefix = f".agents/requirement-workflow-cache/{pkg_sha}/"
        built = ih._build_roles(
            staged_pkg, ["codex", "claude-code", "opencode", "agents-md"], pkg_sha
        )
        assert len(built) == 12
        assert not any(rel.startswith(".zed/") or rel.startswith(".agents-md/") for rel in built)

    expected_bodies = {}
    for rel, raw_bytes in sorted(built.items()):
        native = raw_bytes.decode("utf-8")
        for ceremonial in ("你是需求协作框架", "当前宿主原生名称为", "协议 4", "协议 5"):
            assert ceremonial not in native, (rel, ceremonial)
        for guard in (
            "framework_cache_missing",
            "只读回读",
            "2～3 次",
            "未知外部操作先查原调用",
            "workflow.lock.yaml",
            cache_prefix,
        ):
            assert guard in native, (rel, guard)
        assert "](../" not in native, f"unrewritten_relative_link_in_precompiled_role: {rel}"

        if rel.startswith(".codex/agents/"):
            name = Path(rel).stem
            logical = name.removeprefix("requirement_")
            description = ih.ROLES[logical][2]
            parsed = registry._parse(raw_bytes)
            assert set(parsed) == {"name", "description", "developer_instructions"}
            assert parsed["name"] == name and parsed["description"] == description
            assert cache_prefix in parsed["developer_instructions"]
        else:
            name = Path(rel).stem
            logical = name.removeprefix("requirement-")
            description = ih.ROLES[logical][2]
            head, actual_body = native.removeprefix("---\n").split("---\n\n", 1)
            expected_head = (
                f"name: {name}\ndescription: {description}\n"
                if rel.startswith(".claude/agents/")
                else f"description: {description}\nmode: subagent\n"
            )
            assert head == expected_head, (rel, head)
            if rel.startswith(".opencode/agents/"):
                expected_bodies[name] = actual_body.strip()

        path = scratch / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw_bytes)

    original = b'# exact user bytes\r\n[agents.other_reader]\r\ndescription="User"\r\n'
    block = (templates / "codex-registry.toml").read_bytes()
    merged = registry.merge(original, block)
    assert merged.startswith(original)
    assert registry.merge(merged, block, previous_sha256=sha(block)) == merged
    assert registry.merge(merged, block, restore_only=True) == merged
    assert not registry.matches_plan(merged + b"# user edit\n", original, merged)
    config = scratch / ".codex/config.toml"
    config.write_bytes(merged)
    assert set(registry._parse(merged)["agents"]) == {
        "other_reader",
        "requirement_product",
        "requirement_development",
        "requirement_testing",
        "requirement_bug",
    }

    user_jsonc = b'// user comment\r\n{"agents":{"other-reader":{"description":"User","mode":"subagent"}},}\r\n'
    opencode_config = scratch / "opencode.jsonc"
    opencode_config.write_bytes(user_jsonc)
    result = dict(
        scope="precompiled Protocol 5 role/helper regression, not live invocation",
        host_roles=12,
        rules_hosts=1,
        agents_md_rules_adapter="passed",
        codex_registry="passed",
        markdown_minimal_fields="passed",
        opencode_discovery="not_requested",
        config_preserved=True,
    )
    if args.opencode:
        config_observation = subprocess.run(
            [str(args.opencode.resolve()), "debug", "config"],
            cwd=scratch,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if config_observation.returncode:
            raise RuntimeError("OpenCode configuration preflight unavailable; no config rewritten")
        json.loads(config_observation.stdout)
        command = [str(args.opencode.resolve()), "debug", "agents"]
        attempts = []
        for attempt in range(3):
            observed = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=60)
            if observed.returncode:
                raise RuntimeError(
                    f"OpenCode discovery failed, exit {observed.returncode}; no config rewritten"
                )
            agents = json.loads(observed.stdout)
            actual = {a["name"]: a for a in agents if a.get("name") in expected_bodies}
            attempts.append(dict(exit=observed.returncode, required_roles=sorted(actual)))
            if set(actual) == set(expected_bodies):
                break
            if attempt < 2:
                time.sleep(1)
        result["discovery_attempts"] = attempts
        assert set(actual) == set(expected_bodies), "required roles not discovered"
        for name, body in expected_bodies.items():
            assert actual[name]["mode"] == "subagent"
            assert actual[name].get("system", actual[name].get("prompt", "")).strip() == body
        assert any(a.get("name") == "other-reader" for a in agents), "user role not loaded"
        result["opencode_discovery"] = "passed; four precompiled definitions loaded; invocation untested"
        result["discovery_command"] = command

    assert opencode_config.read_bytes() == user_jsonc
    assert not list(reg_path.parent.rglob("*.pyc")), "source bytecode contamination"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
