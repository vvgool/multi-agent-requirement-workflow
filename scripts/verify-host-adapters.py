#!/usr/bin/env python3
"""Render real host templates into an authorized empty fixture directory.

Development regression only: no installation, receipt, lifecycle scheduler or
native invocation. Optional --opencode checks discovery via an existing CLI;
it does not grant permissions, invoke a model or prove native delegation.
"""
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
    if (linked or not scratch.is_dir() or any(scratch.iterdir())
            or scratch in {Path('/'), Path.home().resolve(), root} or scratch in root.parents):
        parser.error("scratch must be an authorized existing empty ordinary directory")
    templates = root / "skills/setup-requirement-workflow/assets/templates"
    helper = root / "skills/setup-requirement-workflow/scripts/codex_registry.py"
    spec = importlib.util.spec_from_file_location("codex_registry", helper)
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    expected_bodies = {}
    for host, prefix, separator, extension in [
        ("codex", ".codex", "_", "toml"),
        ("claude-code", ".claude", "-", "md"),
        ("opencode", ".opencode", "-", "md"),
    ]:
        for logical, (role, skill, description) in ROLES.items():
            name = "requirement" + separator + logical
            values = dict(native_name=name, role=role, description=description,
                          role_file=f"agents/{role}.md", skill_file=f"skills/{skill}/SKILL.md")
            for key in ("role_file", "skill_file"):
                assert (root / values[key]).is_file(), values[key]
            body = render((templates / "role-body.md").read_text(), values)
            values["role_body"] = body
            native = render((templates / f"native-{host}.{extension}").read_text(), values)
            assert "initialization_probe=true" in native and "task.yaml" in native
            assert "workflow.lock.yaml" in native and values["skill_file"] in native
            if host == "codex":
                parsed = registry._parse(native.encode())
                assert parsed["name"] == name and parsed["developer_instructions"] == body + "\n"
                assert set(parsed) == {"name", "description", "developer_instructions"}
            else:
                head, actual_body = native.removeprefix("---\n").split("---\n\n", 1)
                assert actual_body == body
                expected = (f"name: {name}\ndescription: {description}\n" if host == "claude-code"
                            else f"description: {description}\nmode: subagent\n")
                assert head == expected, (host, head)
            path = scratch / prefix / "agents" / f"{name}.{extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(native.encode())
            if host == "opencode":
                expected_bodies[name] = body.strip()
    # Real pure helper: preserve CRLF, user roles and bytes; no role config copies.
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
        "other_reader", "requirement_product", "requirement_development", "requirement_testing"}
    # A fixture configuration is retained byte-for-byte; it is never an owned item.
    user_jsonc = b'// user comment\r\n{"agents":{"other-reader":{"description":"User","mode":"subagent"}},}\r\n'
    opencode_config = scratch / "opencode.jsonc"
    opencode_config.write_bytes(user_jsonc)
    result = dict(scope="template/helper regression, not setup installation or native activation",
                  host_roles=9, codex_registry="passed", markdown_minimal_fields="passed",
                  opencode_discovery="not_requested", config_preserved=True)
    if args.opencode:
        # Read actual configuration sources first; do not persist full output
        # (it may contain provider credentials). Discovery alone is insufficient.
        config_observation = subprocess.run([str(args.opencode.resolve()), "debug", "config"],
                                            cwd=scratch, capture_output=True, text=True, timeout=60)
        if config_observation.returncode:
            raise RuntimeError("OpenCode configuration preflight unavailable; no config rewritten")
        json.loads(config_observation.stdout)
        command = [str(args.opencode.resolve()), "debug", "agents"]
        attempts = []
        for attempt in range(3):
            observed = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=60)
            if observed.returncode:
                raise RuntimeError(f"OpenCode discovery failed, exit {observed.returncode}; no config rewritten")
            agents = json.loads(observed.stdout)
            actual = {a["name"]: a for a in agents if a.get("name") in expected_bodies}
            attempts.append(dict(exit=observed.returncode, required_roles=sorted(actual)))
            if set(actual) == set(expected_bodies):
                break
            if attempt < 2:
                time.sleep(1)  # Read-only discovery retry, never repeat a task invocation.
        result["discovery_attempts"] = attempts
        assert set(actual) == set(expected_bodies), "required roles not discovered"
        for name, body in expected_bodies.items():
            assert actual[name]["mode"] == "subagent"
            assert actual[name].get("system", actual[name].get("prompt", "")).strip() == body
        assert any(a.get("name") == "other-reader" for a in agents), "user role not loaded"
        result["opencode_discovery"] = "passed; three native definitions loaded; invocation untested"
        result["discovery_command"] = command
    assert opencode_config.read_bytes() == user_jsonc
    assert not list(helper.parent.rglob("codex_registry.cpython-*.pyc")), "source bytecode contamination"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
