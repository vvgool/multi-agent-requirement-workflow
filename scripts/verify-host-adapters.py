#!/usr/bin/env python3
"""Render real Protocol 4 host templates into an authorized empty fixture directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True

ROLES = {
    "product": ("product-agent", "requirement-analysis", "澄清需求并输出验收标准"),
    "development": ("development-agent", "feature-development", "实现已批准需求并完成自验"),
    "testing": ("testing-agent", "acceptance-testing", "独立验收当前开发基线并报告缺陷"),
    "bug": ("bug-agent", "bug-fixing", "诊断并修复缺陷并完成自验"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render(text, values):
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text or "}}" in text:
        raise ValueError("unresolved template parameter")
    return text


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
    helper = root / "skills/setup-requirement-workflow/scripts/codex_registry.py"
    spec = importlib.util.spec_from_file_location("codex_registry", helper)
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)

    adapter = (root / "skills/setup-requirement-workflow/references/opencode-adapter.md").read_text(
        encoding="utf-8"
    )
    assert "不创建业务 `host.yaml`" in adapter or "不创建业务host.yaml" in adapter

    zed_adapter = (root / "skills/setup-requirement-workflow/references/zed-adapter.md").read_text(
        encoding="utf-8"
    )
    host_entry = (root / "workflow/host-adapters.md").read_text(encoding="utf-8")
    for zed_text in (zed_adapter, host_entry):
        assert "规则型宿主" in zed_text
        assert "AGENTS.md" in zed_text
        assert "native_role_probes" in zed_text
        assert "not_applicable" in zed_text
    assert "不生成 Zed 角色文件" in zed_adapter
    assert "不生成 `.zed/agents`" in host_entry

    entry = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "requirement-workflow:begin" in entry and "requirement-workflow:end" in entry
    bridge = (templates / "claude-entry.md").read_text(encoding="utf-8")
    for guard in ("AGENTS.md", "明确局部低风险小修", "两道确认门禁", "静音连续巡航", "日常零核包开销"):
        assert guard in bridge, f"claude_bridge_missing: {guard}"
    assert "你是需求协作框架" not in bridge and "协议 4" not in bridge

    expected_bodies = {}
    for host, prefix, separator, extension in [
        ("codex", ".codex", "_", "toml"),
        ("claude-code", ".claude", "-", "md"),
        ("opencode", ".opencode", "-", "md"),
    ]:
        for logical, (role, skill, description) in ROLES.items():
            name = "requirement" + separator + logical
            values = dict(
                native_name=name,
                role=role,
                description=description,
                role_file=f"agents/{role}.md",
                skill_file=f"skills/{skill}/SKILL.md",
            )
            for key in ("role_file", "skill_file"):
                assert (root / values[key]).is_file(), values[key]
            body = render((templates / "role-body.md").read_text(encoding="utf-8"), values)
            values["role_body"] = body
            native = render(
                (templates / f"native-{host}.{extension}").read_text(encoding="utf-8"), values
            )
            for ceremonial in ("你是需求协作框架", "当前宿主原生名称为", "协议 4"):
                assert ceremonial not in native, (host, name, ceremonial)
            for guard in (
                "framework_cache_missing",
                "只读回读",
                "2～3 次",
                "未知外部操作先查原调用",
                "workflow.lock.yaml",
                values["role_file"],
                values["skill_file"],
            ):
                assert guard in native, (host, name, guard)
            if host == "codex":
                parsed = registry._parse(native.encode("utf-8"))
                assert parsed["name"] == name and parsed["developer_instructions"] == body + "\n"
                assert set(parsed) == {"name", "description", "developer_instructions"}
            else:
                head, actual_body = native.removeprefix("---\n").split("---\n\n", 1)
                assert actual_body == body
                expected = (
                    f"name: {name}\ndescription: {description}\n"
                    if host == "claude-code"
                    else f"description: {description}\nmode: subagent\n"
                )
                assert head == expected, (host, head)
            path = scratch / prefix / "agents" / f"{name}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(native.encode("utf-8"))
            if host == "opencode":
                expected_bodies[name] = body.strip()

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
        scope="template/helper regression, not setup installation or native activation",
        host_roles=12,
        rules_hosts=1,
        zed_rules_adapter="passed",
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
            observed = subprocess.run(
                command, cwd=scratch, capture_output=True, text=True, timeout=60
            )
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
        result["opencode_discovery"] = "passed; four native definitions loaded; invocation untested"
        result["discovery_command"] = command

    assert opencode_config.read_bytes() == user_jsonc
    assert not list(helper.parent.rglob("*.pyc")), "source bytecode contamination"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
