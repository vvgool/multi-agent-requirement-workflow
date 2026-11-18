#!/usr/bin/env python3
"""Deterministic install, restore, and digest helper for Protocol 4; Python stdlib only."""
import sys

sys.dont_write_bytecode = True

import argparse, base64, hashlib, importlib.util, json, os, re, shutil, stat, subprocess, tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT_FILES = {"framework.yaml", "AGENTS.md", "README.md", "workflow.yaml"}
ROOT_DIRS = {"agents", "skills", "workflow", "templates"}
FORBIDDEN = {"__pycache__", ".DS_Store"}
EXCLUDED_PREFIXES = ("skills/system/",)
HEX64, HEX40 = re.compile(r"[0-9a-f]{64}\Z"), re.compile(r"[0-9a-f]{40}\Z")
HOSTS = ("codex", "claude-code", "opencode", "zed")
TPL_REL = "skills/setup-requirement-workflow/assets/templates"
CODEX_REG_REL = "skills/setup-requirement-workflow/scripts/codex_registry.py"
BLOCKS = (
    ("AGENTS.md", "project-entry-light.md", b"requirement-workflow:",
     b"<!-- requirement-workflow:begin -->", b"<!-- requirement-workflow:end -->"),
    (".gitignore", "gitignore.txt", b"requirement-workflow-local:",
     b"# requirement-workflow-local:begin", b"# requirement-workflow-local:end"),
    ("CLAUDE.md", "claude-entry.md", b"requirement-workflow-bridge:",
     b"<!-- requirement-workflow-bridge:begin -->", b"<!-- requirement-workflow-bridge:end -->"),
)
ROLES = {
    "product": ("product-agent", "requirement-analysis", "澄清需求并输出验收标准"),
    "development": ("development-agent", "feature-development", "实现已批准需求并完成自验"),
    "testing": ("testing-agent", "acceptance-testing", "独立验收当前开发基线并报告缺陷"),
    "bug": ("bug-agent", "bug-fixing", "诊断并修复缺陷并完成自验"),
}
DEFAULT_WORKFLOW_YAML = (
    "schema_version: 1\nworkspace:\n  features_dir: agent-features\n"
    "documents:\n  provider: local\n  feishu:\n    parent_node_url: null\n    write_enabled: false\n"
    'approval:\n  channel: coordinator\nissue_tracking:\n  binding: "off"\n  sync: "off"\n'
).encode("utf-8")


class HelperError(ValueError):
    pass


def _bad_loc(loc) -> bool:
    return not isinstance(loc, str) or not loc.strip() or (
        "://" in loc and "@" in loc.split("://", 1)[1].split("/", 1)[0]
    )


def _scalar(raw: str):
    v = raw.strip()
    if not v or v in ("null", "~"):
        return None
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?[0-9]+", v):
        return int(v)
    if v.startswith(("&", "*")):
        raise HelperError("yaml_anchor_rejected")
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'") else v


def parse_simple_yaml(text: str) -> dict:
    root, sec = {}, None
    for no, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise HelperError(f"yaml_tab_rejected:{no}")
        ln = "" if raw.lstrip().startswith("#") else re.sub(r"\s+#.*$", "", raw)
        if not ln.strip():
            continue
        ind = len(ln) - len(ln.lstrip(" "))
        if ":" not in ln:
            raise HelperError(f"yaml_invalid_line:{no}")
        k, rest = (s.strip() for s in ln.strip().split(":", 1))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
            raise HelperError(f"yaml_invalid_key:{no}")
        if ind == 0:
            if k in root:
                raise HelperError(f"yaml_duplicate_key:{k}")
            sec = {} if rest == "" else None
            root[k] = sec if rest == "" else _scalar(rest)
        elif ind == 2 and isinstance(sec, dict):
            if k in sec:
                raise HelperError(f"yaml_duplicate_nested_key:{k}")
            sec[k] = _scalar(rest)
        else:
            raise HelperError(f"yaml_unexpected_indent:{no}")
    return root


def format_lock_yaml(*, name: str, version: str, protocol_version: int, sha256: str,
                     kind: str, location: str, revision) -> bytes:
    rev = "null" if revision is None else revision
    return (
        f"schema_version: 1\npackage:\n  name: {name}\n  version: {version}\n"
        f"  protocol_version: {protocol_version}\n  sha256: {sha256}\n"
        f"source:\n  kind: {kind}\n  location: {location}\n  revision: {rev}\n"
    ).encode("utf-8")


def _bad_artifact(p: Path):
    if p.name in FORBIDDEN or p.suffix in {".pyc", ".pyo"}:
        raise HelperError(f"bytecode or system artifact rejected: {p}")


def compute_digest(root: Path) -> dict:
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise HelperError("package root must be an ordinary directory")
    names = {p.name for p in root.iterdir()}
    miss, extra = (ROOT_FILES | ROOT_DIRS) - names, names - ROOT_FILES - ROOT_DIRS - {"LICENSE"}
    if miss or extra:
        raise HelperError(f"missing={sorted(miss)}, extra={sorted(extra)}")
    rows = []

    def visit(p: Path):
        _bad_artifact(p)
        m = p.lstat().st_mode
        if stat.S_ISREG(m):
            rows.append([p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()])
        elif stat.S_ISDIR(m):
            for c in p.iterdir():
                visit(c)
        else:
            raise HelperError(f"link or special file rejected: {p}")

    for n in names:
        p = root / n
        if not (stat.S_ISDIR if n in ROOT_DIRS else stat.S_ISREG)(p.lstat().st_mode):
            raise HelperError(f"unexpected package entry type: {p}")
        visit(p)
    rows.sort(key=lambda r: r[0])
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"file_count": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}


def _no_symlink(path: Path):
    cur = path.absolute()
    for part in [*reversed(cur.parents), cur]:
        if os.path.lexists(part) and stat.S_ISLNK(part.lstat().st_mode):
            raise HelperError(f"symlink_rejected:{part}")


def stage_clean_package(source_root: Path, dest: Path, *, include_working_tree: bool = False) -> dict:
    _no_symlink(source_root)
    if not source_root.is_dir():
        raise HelperError("source_root_not_directory")
    tracked = None
    if (source_root / ".git").exists() and not include_working_tree:
        out = subprocess.check_output(["git", "ls-files", "-z"], cwd=source_root).decode("utf-8")
        tracked = {e for e in out.split("\0") if e}
    dest.mkdir(parents=True, exist_ok=True)
    allowed = ROOT_FILES | {"LICENSE"} | ROOT_DIRS

    def copy_rel(rel: str):
        if any(rel.startswith(px) for px in EXCLUDED_PREFIXES):
            return
        src = source_root / rel
        if not os.path.lexists(src):
            return
        _no_symlink(src)
        _bad_artifact(src)
        if not stat.S_ISREG(src.lstat().st_mode):
            raise HelperError(f"non_regular_package_file:{rel}")
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    def visit_dir(d: Path):
        for sub in d.iterdir():
            rel = sub.relative_to(source_root).as_posix()
            if any(rel == px.rstrip("/") or rel.startswith(px) for px in EXCLUDED_PREFIXES):
                continue
            _no_symlink(sub)
            _bad_artifact(sub)
            m = sub.lstat().st_mode
            if stat.S_ISDIR(m):
                visit_dir(sub)
            elif stat.S_ISREG(m):
                copy_rel(rel)
            else:
                raise HelperError(f"non_regular_package_file:{rel}")

    if tracked is not None:
        for rel in sorted(tracked):
            if rel.split("/", 1)[0] in allowed:
                copy_rel(rel)
    else:
        for ch in source_root.iterdir():
            if ch.name not in allowed:
                continue
            _no_symlink(ch)
            if ch.name in ROOT_FILES or ch.name == "LICENSE":
                copy_rel(ch.name)
            elif stat.S_ISDIR(ch.lstat().st_mode):
                visit_dir(ch)
            else:
                raise HelperError(f"unexpected package entry type: {ch}")
    return compute_digest(dest)


def _merge_block(orig: bytes, block: bytes, token: bytes, begin: bytes, end: bytes, *,
                 upgrade: bool, restore_only: bool) -> bytes:
    block = block if block.endswith(b"\n") else block + b"\n"
    cnt = orig.count(token)
    if cnt not in (0, 2):
        raise HelperError("adapter_modified:incomplete_or_duplicate_markers")
    if cnt == 2:
        s_m = list(re.finditer(rb"(?m)^" + re.escape(begin) + rb"\r?\n", orig))
        e_m = list(re.finditer(rb"(?m)^" + re.escape(end) + rb"(?:\r?\n|\Z)", orig))
        if len(s_m) != 1 or len(e_m) != 1 or e_m[0].start() < s_m[0].end():
            raise HelperError("adapter_modified:noncanonical_markers")
        s, e = s_m[0].start(), e_m[0].end()
        norm = orig[s:e].replace(b"\r\n", b"\n")
        if (norm if norm.endswith(b"\n") else norm + b"\n") != block:
            if restore_only or not upgrade:
                raise HelperError("adapter_modified:block_differs_without_upgrade")
            return orig[:s] + block + orig[e:]
        return orig
    if restore_only:
        raise HelperError("restore_failed:managed_block_missing")
    return orig + (b"\n" if orig and not orig.endswith(b"\n") else b"") + block


def _merge_codex(pkg_root: Path, orig: bytes, block: bytes, *, upgrade: bool, restore_only: bool) -> bytes:
    hp = pkg_root / CODEX_REG_REL
    spec = importlib.util.spec_from_file_location("codex_registry", hp)
    reg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reg)
    prev = None
    if upgrade and b"requirement-workflow:codex-registry:" in orig:
        s, e = reg._span(orig)
        prev = hashlib.sha256(orig[s:e]).hexdigest()
    if reg.tomllib is not None:
        try:
            return reg.merge(orig, block, restore_only=restore_only, previous_sha256=prev)
        except reg.RegistryError as exc:
            raise HelperError(str(exc)) from exc
    snip = (
        "import sys,importlib.util,json,base64;sys.dont_write_bytecode=True\n"
        "p=json.loads(sys.stdin.read());s=importlib.util.spec_from_file_location('cr',p['h'])\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "if m.tomllib is None:sys.exit(3)\n"
        "print(base64.b64encode(m.merge(base64.b64decode(p['o']),base64.b64decode(p['b']),"
        "restore_only=p['r'],previous_sha256=p['p'])).decode('ascii'))\n"
    )
    inp = json.dumps({"h": str(hp), "o": base64.b64encode(orig).decode("ascii"),
                      "b": base64.b64encode(block).decode("ascii"), "r": restore_only, "p": prev})
    for cand in ("python3.13", "python3.12", "python3.11", "python3.10", "/usr/bin/python3"):
        exe = shutil.which(cand)
        if exe:
            pr = subprocess.run([exe, "-B", "-c", snip], input=inp, capture_output=True, text=True)
            if pr.returncode == 0:
                return base64.b64decode(pr.stdout.strip())
            if pr.returncode != 3:
                raise HelperError(pr.stderr.strip() or "codex_registry_merge_failed")
    raise HelperError("toml_parser_unavailable")


def _render(tpl: str, vals: dict) -> str:
    for k, v in vals.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    if "{{" in tpl or "}}" in tpl:
        raise HelperError("unresolved_template_parameter")
    return tpl


def _build_roles(pkg_root: Path, hosts: list) -> dict:
    td = pkg_root / TPL_REL
    body_tpl = (td / "role-body.md").read_text(encoding="utf-8")
    specs = {
        "codex": (".codex/agents", "_", "toml", "native-codex.toml"),
        "claude-code": (".claude/agents", "-", "md", "native-claude-code.md"),
        "opencode": (".opencode/agents", "-", "md", "native-opencode.md"),
    }
    out = {}
    for h in hosts:
        if h == "zed":
            continue
        rel_dir, sep, ext, tn = specs[h]
        nt = (td / tn).read_text(encoding="utf-8")
        for logical, (role, skill, desc) in ROLES.items():
            name = f"requirement{sep}{logical}"
            vals = {"native_name": name, "role": role, "description": desc,
                    "role_file": f"agents/{role}.md", "skill_file": f"skills/{skill}/SKILL.md"}
            vals["role_body"] = _render(body_tpl, vals)
            out[f"{rel_dir}/{name}.{ext}"] = _render(nt, vals).encode("utf-8")
    return out


def _populate_cache(staged: Path, target_root: Path, expected_sha: str) -> bool:
    parent = target_root / ".agents/requirement-workflow-cache"
    cache_dir = parent / expected_sha
    _no_symlink(cache_dir)
    if cache_dir.exists():
        if compute_digest(cache_dir)["sha256"] != expected_sha:
            raise HelperError("framework_integrity_mismatch")
        return False
    parent.mkdir(parents=True, exist_ok=True)
    tmp_c = parent / f".tmp-{os.getpid()}-{expected_sha[:12]}"
    if tmp_c.exists():
        shutil.rmtree(tmp_c)
    shutil.copytree(staged, tmp_c)
    if compute_digest(tmp_c)["sha256"] != expected_sha:
        shutil.rmtree(tmp_c)
        raise HelperError("staged_cache_digest_mismatch")
    tmp_c.rename(cache_dir)
    return True


def cmd_digest(args) -> int:
    if args.expected_sha256 is not None and not HEX64.fullmatch(args.expected_sha256):
        raise HelperError("expected_sha256 must be 64 lowercase hex characters")
    if args.package_root is not None:
        res = compute_digest(args.package_root)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            st = Path(tmp) / "pkg"
            info = stage_clean_package(args.source_root.resolve(), st, include_working_tree=args.include_working_tree)
            fw = parse_simple_yaml((st / "framework.yaml").read_text(encoding="utf-8"))
            tb = sum(p.stat().st_size for p in st.rglob("*") if p.is_file())
            res = {"version": str(fw["version"]), "protocol_version": int(fw["protocol_version"]),
                   "file_count": info["file_count"], "total_bytes": tb, "sha256": info["sha256"]}
    if args.expected_sha256 is not None:
        res["matches_expected"] = res["sha256"] == args.expected_sha256
        print(json.dumps(res, separators=(",", ":")))
        return 0 if res["matches_expected"] else 1
    print(json.dumps(res, separators=(",", ":")))
    return 0


def cmd_install(args) -> int:
    src, dst = args.source_root.resolve(), args.target_root.resolve()
    _no_symlink(dst)
    if not dst.is_dir():
        raise HelperError("target_root_not_directory")
    hosts = list(dict.fromkeys(h.strip() for h in args.hosts.split(",") if h.strip()))
    if not hosts or any(h not in HOSTS for h in hosts):
        raise HelperError("unsupported_or_empty_hosts")
    if args.source_kind not in ("git", "manual") or _bad_loc(args.source_location):
        raise HelperError("invalid_source_metadata")
    if args.source_kind == "git":
        if not args.source_revision or not HEX40.fullmatch(args.source_revision):
            raise HelperError("git_source_requires_40_hex_revision")
        rev = args.source_revision
    elif args.source_revision:
        raise HelperError("manual_source_forbids_revision")
    else:
        rev = None

    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp) / "pkg"
        info = stage_clean_package(src, st, include_working_tree=args.include_working_tree)
        sha = info["sha256"]
        fw = parse_simple_yaml((st / "framework.yaml").read_text(encoding="utf-8"))
        if fw.get("schema_version") != 1 or fw.get("name") != "multi-agent-requirement-workflow":
            raise HelperError("invalid_framework_yaml")
        td, planned = st / TPL_REL, {}

        lp = dst / "workflow.lock.yaml"
        lock_b = format_lock_yaml(name=fw["name"], version=str(fw["version"]),
                                  protocol_version=int(fw["protocol_version"]), sha256=sha,
                                  kind=args.source_kind, location=args.source_location, revision=rev)
        if lp.exists():
            _no_symlink(lp)
            ex_sha = (parse_simple_yaml(lp.read_text(encoding="utf-8")).get("package") or {}).get("sha256")
            if ex_sha != sha and not args.upgrade:
                raise HelperError("lock_mismatch_use_upgrade")
            if lp.read_bytes() != lock_b:
                if not args.upgrade and ex_sha == sha:
                    raise HelperError("lock_metadata_modified")
                planned["workflow.lock.yaml"] = lock_b
        else:
            planned["workflow.lock.yaml"] = lock_b

        wf_p = dst / "workflow.yaml"
        if not wf_p.exists():
            planned["workflow.yaml"] = DEFAULT_WORKFLOW_YAML
        else:
            _no_symlink(wf_p)

        for rel, tpl_name, tok, b_ln, e_ln in BLOCKS:
            if rel == "CLAUDE.md" and "claude-code" not in hosts:
                continue
            fp = dst / rel
            if fp.exists():
                _no_symlink(fp)
            orig = fp.read_bytes() if fp.exists() else b""
            merged = _merge_block(orig, (td / tpl_name).read_bytes(), tok, b_ln, e_ln,
                                  upgrade=args.upgrade, restore_only=False)
            if merged != orig:
                planned[rel] = merged

        if "codex" in hosts:
            cx_p = dst / ".codex/config.toml"
            if cx_p.exists():
                _no_symlink(cx_p)
            orig_cx = cx_p.read_bytes() if cx_p.exists() else b""
            merged_cx = _merge_codex(st, orig_cx, (td / "codex-registry.toml").read_bytes(),
                                     upgrade=args.upgrade, restore_only=False)
            if merged_cx != orig_cx:
                planned[".codex/config.toml"] = merged_cx

        for rel, content in _build_roles(st, hosts).items():
            fp = dst / rel
            if fp.exists():
                _no_symlink(fp)
                if fp.read_bytes() != content:
                    if not args.upgrade:
                        raise HelperError(f"role_file_modified_without_upgrade:{rel}")
                    planned[rel] = content
            else:
                planned[rel] = content

        _populate_cache(st, dst, sha)
        updated = []
        for rel, content in sorted(planned.items()):
            fp = dst / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(content)
            updated.append(rel)
        print(json.dumps({"package_sha256": sha, "file_count": info["file_count"],
                          "cache_dir": f".agents/requirement-workflow-cache/{sha}",
                          "installed_hosts": hosts, "updated_files": updated},
                         ensure_ascii=False, separators=(",", ":")))
        return 0


def cmd_restore(args) -> int:
    src, dst = args.source_root.resolve(), args.target_root.resolve()
    _no_symlink(dst)
    lp = dst / "workflow.lock.yaml"
    if not lp.is_file():
        raise HelperError("restore_failed:missing_workflow_lock")
    _no_symlink(lp)
    lock = parse_simple_yaml(lp.read_text(encoding="utf-8"))
    pkg, sm = lock.get("package") or {}, lock.get("source") or {}
    exp_sha, kind, loc, rev = pkg.get("sha256"), sm.get("kind"), sm.get("location"), sm.get("revision")
    if lock.get("schema_version") != 1 or kind != "git" or _bad_loc(loc) or not isinstance(rev, str) or not HEX40.fullmatch(rev):
        raise HelperError("restore_blocked:requires_canonical_git_lock")
    if not isinstance(exp_sha, str) or not HEX64.fullmatch(exp_sha):
        raise HelperError("restore_failed:invalid_lock_sha256")

    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp) / "pkg"
        info = stage_clean_package(src, st, include_working_tree=args.include_working_tree)
        if info["sha256"] != exp_sha:
            raise HelperError("framework_integrity_mismatch:source_differs_from_lock")
        fw = parse_simple_yaml((st / "framework.yaml").read_text(encoding="utf-8"))
        exp_lock = format_lock_yaml(name=fw["name"], version=str(fw["version"]),
                                    protocol_version=int(fw["protocol_version"]), sha256=exp_sha,
                                    kind="git", location=loc, revision=rev)
        if lp.read_bytes().replace(b"\r\n", b"\n") != exp_lock:
            raise HelperError("restore_failed:lock_metadata_modified")
        td = st / TPL_REL
        for rel, tpl_name, tok, b_ln, e_ln in BLOCKS:
            if rel == "CLAUDE.md" and not (dst / ".claude/agents").is_dir():
                continue
            fp = dst / rel
            if not fp.is_file():
                if rel == "AGENTS.md":
                    raise HelperError("restore_failed:missing_agents_md")
                continue
            _no_symlink(fp)
            _merge_block(fp.read_bytes(), (td / tpl_name).read_bytes(), tok, b_ln, e_ln,
                         upgrade=False, restore_only=True)

        detected = []
        if (dst / ".codex/config.toml").is_file() or (dst / ".codex/agents").is_dir():
            detected.append("codex")
            cx_p = dst / ".codex/config.toml"
            if not cx_p.is_file():
                raise HelperError("restore_failed:missing_codex_config")
            _merge_codex(st, cx_p.read_bytes(), (td / "codex-registry.toml").read_bytes(),
                         upgrade=False, restore_only=True)
        if (dst / ".claude/agents").is_dir():
            detected.append("claude-code")
        if (dst / ".opencode/agents").is_dir():
            detected.append("opencode")

        for rel, exp_b in _build_roles(st, detected).items():
            fp = dst / rel
            if not fp.is_file() or fp.read_bytes() != exp_b:
                raise HelperError(f"adapter_modified:{rel}")

        restored = _populate_cache(st, dst, exp_sha)
        print(json.dumps({"package_sha256": exp_sha, "file_count": info["file_count"],
                          "cache_dir": f".agents/requirement-workflow-cache/{exp_sha}",
                          "restored": restored}, ensure_ascii=False, separators=(",", ":")))
        return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("digest")
    dg = d.add_mutually_exclusive_group(required=True)
    dg.add_argument("--package-root", type=Path)
    dg.add_argument("--source-root", type=Path)
    d.add_argument("--include-working-tree", action="store_true")
    d.add_argument("--expected-sha256", default=None)
    i = sub.add_parser("install")
    for flag in ("--source-root", "--target-root"):
        i.add_argument(flag, required=True, type=Path)
    for flag in ("--hosts", "--source-kind", "--source-location"):
        i.add_argument(flag, required=True)
    i.add_argument("--source-revision", default=None)
    i.add_argument("--upgrade", action="store_true")
    i.add_argument("--include-working-tree", action="store_true")
    r = sub.add_parser("restore")
    for flag in ("--source-root", "--target-root"):
        r.add_argument(flag, required=True, type=Path)
    r.add_argument("--include-working-tree", action="store_true")
    try:
        args = p.parse_args()
        return {"digest": cmd_digest, "install": cmd_install, "restore": cmd_restore}[args.command](args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
