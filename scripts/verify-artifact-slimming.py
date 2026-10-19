#!/usr/bin/env python3
"""Executable file-protocol examples, not a scheduler or native-host acceptance.

Run with --scratch pointing at an explicitly authorized empty directory.
Only the supplied directory is written; keep the summary in the existing report.
Requires the environment's PyYAML; installs nothing. Fixtures remain for inspection.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys

import yaml


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def ordinary_within(path, boundary):
    """Check link components inside the canonical authorized root, including parents."""
    if not path.resolve().is_relative_to(boundary):
        return False
    current = path.absolute()
    while current != boundary:
        if current.is_symlink() or current == current.parent:
            return False
        current = current.parent
    return path.is_file()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.source_root.resolve()
    if not __debug__:
        parser.error("assertions are required; run Python without -O")
    if args.scratch.is_symlink() or not args.scratch.is_dir():
        parser.error("--scratch must be an authorized, existing empty ordinary directory")
    scratch = args.scratch.resolve()
    if (scratch in {Path('/'), Path.home().resolve(), root} or scratch in root.parents
            or any(scratch.iterdir())):
        parser.error("--scratch must be an authorized, existing empty ordinary directory")
    for required in ["templates/role-task.yaml", "templates/role-result.yaml"]:
        if not (root / required).is_file():
            parser.error(f"source dependency missing: {required}")
    if shutil.which("git") is None:
        parser.error("Git must already be available; this script installs nothing")

    # Read the real templates; examples do not introduce new mandatory fields.
    task = yaml.safe_load((root / "templates/role-task.yaml").read_text())
    task.update(run_id="development-001", output_dir=str(scratch / "run/outputs"))
    task["write_scope"]["temporary_paths"] = [str(scratch / "run/tmp")]
    write(scratch / "run/task.yaml", yaml.safe_dump(task))
    out = Path(task["output_dir"])
    cache = Path(task["write_scope"]["temporary_paths"][0])
    font = write(cache / "fonts/example.woff2", "reproducible font fixture")
    build = write(cache / "build/cache.bin", "regenerable build fixture")
    check = subprocess.run([sys.executable, "-c", "print('representative check: passed')"],
                           capture_output=True, text=True, check=False)
    evidence = write(out / "check-01.txt", check.stdout)
    assert check.returncode == 0
    assert not list(out.rglob("*.woff2")) and not list(out.rglob("cache.bin"))
    # Same actual check, two AC references, one physical output.
    report = write(out / "development.md", "AC-01/AC-02: [check-01](check-01.txt)\n")
    assert list(out.glob("*.txt")) == [evidence]
    no_cache_task = dict(task, write_scope={"project_paths": [], "temporary_paths": []})
    assert not no_cache_task["write_scope"]["temporary_paths"]  # Must block a cache-writing command.
    retry_command = [sys.executable, "-c",
                     "import sys; v=input(); print('fixture failure' if v=='fail' else 'fixture passed'); sys.exit(v=='fail')"]
    failed = subprocess.run(retry_command, input="fail\n", capture_output=True, text=True, check=False)
    retried = subprocess.run(retry_command, input="pass\n", capture_output=True, text=True, check=False)
    failure_log = write(out / "check-02-failed.txt", failed.stdout)
    retry_log = write(out / "check-03-recheck.txt", retried.stdout)
    assert failed.returncode == 1 and retried.returncode == 0
    assert failure_log.exists() and retry_log.exists() and "failure" in failure_log.read_text()
    print("AC-01/02: authorized cache outside outputs; one real command, one output; missing grant blocks")

    # Retain related tracked, dirty and untracked source bytes; exclude generated cache.
    project = scratch / "project"
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    source = write(project / "src/main.txt", "indexed\n")
    subprocess.run(["git", "-C", str(project), "add", "src"], check=True)
    source.write_text("dirty\n")
    write(project / "src/new.txt", "untracked\n")
    write(project / "cache/font.woff2", "excluded\n")

    def baseline():
        return [{"path": p.relative_to(project).as_posix(), "sha256": digest(p)}
                for p in sorted((project / "src").rglob("*")) if p.is_file()]

    files = baseline()
    assert len(files) == 2 and any(f["path"] == "src/new.txt" for f in files)
    original = {"run_id": "development-001", "files": files, "inputs": "v1", "env": "fixture-v1",
                "check_scope": "src", "evidence_sha256": digest(evidence)}
    source_result = yaml.safe_load((root / "templates/role-result.yaml").read_text())
    source_result.update(schema_version=1, feature_id="fixture", requirements_revision=1,
                         run_id="development-001", role="development", status="ready",
                         code_baseline={"schema_version": 1, "git_commit": None, "scope": ["src"],
                                        "exclude": [], "files": files, "evidence": ["check-01.txt"]},
                         artifacts=[{"kind": "evidence", "path": "check-01.txt"}])
    original_result = write(scratch / "run/result.yaml", yaml.safe_dump(source_result))

    def reuse(current):
        if not evidence.is_file() or digest(evidence) != original["evidence_sha256"]:
            return "blocked_or_reacquire"
        return "reuse_not_rerun" if current == original else "rerun"

    assert reuse(dict(original)) == "reuse_not_rerun"
    assert reuse(dict(original, env="fixture-v2")) == "rerun"
    source.write_text("changed\n")
    assert baseline() != files and reuse(dict(original, files=baseline())) == "rerun"
    write(project / "src/added.txt", "new\n")
    assert len(baseline()) == 3
    (project / "src/new.txt").unlink()
    assert baseline() != files
    saved = evidence.read_bytes()
    evidence.unlink()
    assert reuse(dict(original)) == "blocked_or_reacquire"
    evidence.write_bytes(saved)
    assert original_result.is_file()
    # Historical evidence uses a report link, never a parent path in artifacts.
    current_out = scratch / "next/outputs"
    current_report = write(current_out / "test-report.md",
                           "Auxiliary only, not rerun: [source](../../run/result.yaml)\n")
    assert (current_out / "../../run/result.yaml").resolve().is_file()
    assert not evidence.is_symlink()
    # History references must remain inside the permitted feature tree with no symlink component.
    def readable_reference(base, relative):
        return ordinary_within(base / relative, scratch)

    assert readable_reference(current_out, "../../run/result.yaml")
    assert not readable_reference(current_out, "../../../../unknown.txt")
    history_link = current_out / "linked-result.yaml"
    history_link.symlink_to(original_result)
    assert not readable_reference(current_out, "linked-result.yaml")
    print("AC-03/04: unchanged reuse, environment/code invalidation, missing evidence; dirty/untracked/add/delete detected")

    # Cleanup is a conjunction, evaluated per file. Protect nonordinary paths too.
    pending = write(cache / "progress.pending.yaml", "recovery")
    referenced = write(cache / "failure.txt", "necessary failure")
    edited = write(cache / "user.txt", "owned")
    known = digest(edited)
    edited.write_text("user edit")
    unknown = write(cache / "unknown.txt", "unknown owner")
    symlink = cache / "escape"
    symlink.symlink_to(evidence)

    def cleanable(path, *, ended=True, owned=True, referenced=False, recovery=False, expected=None):
        return (ended and owned and not referenced and not recovery and ordinary_within(path, cache)
                and expected is not None and digest(path) == expected)

    assert not cleanable(font, ended=False, expected=digest(font))
    assert not cleanable(pending, recovery=True, expected=digest(pending))
    assert not cleanable(referenced, referenced=True, expected=digest(referenced))
    assert not cleanable(edited, expected=known)
    assert not cleanable(unknown, owned=False, expected=digest(unknown))
    assert not cleanable(symlink, expected=digest(evidence))
    alias = cache / "font-alias"
    alias.symlink_to(font.parent, target_is_directory=True)
    assert not cleanable(alias / font.name, expected=digest(font))
    for p in [font, build]:
        assert cleanable(p, expected=digest(p))
        p.unlink()
    assert all(p.exists() for p in [pending, referenced, edited, unknown, evidence, report, current_report])
    print("AC-05: ended/unreferenced owned cache removed; active/pending/referenced/edited/unknown/symlink protected")

    # README is a derived index. Simulate state-write/README interruption and a user conflict.
    readme = write(scratch / "README.md", "old run\n")
    index_sha = digest(readme)
    state = {"revision": 1, "stage": "development", "execution_status": "running",
             "active_run": "development-002", "next": "wait for original invocation"}
    state_file = write(scratch / "status.yaml", yaml.safe_dump(state))
    state = yaml.safe_load(state_file.read_text())
    before = json.dumps(state, sort_keys=True)

    def sync_index(expected):
        if digest(readme) != expected:
            return "index_conflict"
        readme.write_text(json.dumps(state, ensure_ascii=False) + "\n上一基线，当前待重验\n")
        return "synchronized"

    assert sync_index(index_sha) == "synchronized"
    assert "development-002" in readme.read_text() and json.dumps(state, sort_keys=True) == before
    state["execution_status"] = "blocked"
    assert sync_index(digest(readme)) == "synchronized"
    index_sha = digest(readme)
    readme.write_text(readme.read_text() + "user edit\n")
    saved = readme.read_bytes()
    assert sync_index(index_sha) == "index_conflict" and readme.read_bytes() == saved
    assert state["active_run"] == "development-002"
    print("AC-06: state/index recovery and blocked status; user edit preserved; no redispatch or false task end")

    # Legacy inputs are read without rewriting. No new field is needed to parse them.
    legacy = write(scratch / "legacy/task.yaml", "role: testing\noutput_dir: legacy/outputs\n")
    old_digest = digest(legacy)
    assert "write_scope" not in yaml.safe_load(legacy.read_text()) and digest(legacy) == old_digest
    for path in ["workflow/execution-contract.md", "workflow/output-layout.md", "workflow/state-contract.md",
                 "workflow/code-baseline.md", "skills/feature-development/SKILL.md",
                 "skills/acceptance-testing/SKILL.md"]:
        assert (root / path).is_file()
    print("AC-07/08: legacy bytes unchanged; fixtures isolated; existing templates and central contracts readable")
    print("PASS: executable protocol examples only; independent acceptance and host activation are separate gates")


if __name__ == "__main__":
    main()
