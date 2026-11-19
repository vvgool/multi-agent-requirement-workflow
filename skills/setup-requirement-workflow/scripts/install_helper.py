#!/usr/bin/env python3
"""Deterministic Protocol 5 install, restore, and digest helper (stdlib only)."""
import sys

sys.dont_write_bytecode = True

import argparse, base64, hashlib, importlib.util, json, os, posixpath, re, shutil, stat, subprocess, tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

PROTOCOL_VERSION = 5
ROOT_FILES = {"framework.yaml", "LICENSE"}
ROOT_DIRS = {"agents", "skills", "workflow", "templates"}
FORBIDDEN = {"__pycache__", ".DS_Store"}
EXCLUDED_PREFIXES = ("skills/system/",)
HEX64, HEX40 = re.compile(r"[0-9a-f]{64}\Z"), re.compile(r"[0-9a-f]{40}\Z")
HOSTS = ("codex", "claude-code", "opencode", "agents-md")
HOST_ALIASES = {"zed": "agents-md"}
TPL_REL = "skills/setup-requirement-workflow/assets/templates"
CODEX_REG_REL = "skills/setup-requirement-workflow/scripts/codex_registry.py"
PY_CANDS = ("python3.13", "python3.12", "python3.11", "python3.10", "/opt/homebrew/bin/python3", "/usr/bin/python3")
BLOCKS = (
  ("AGENTS.md", "project-entry-light.md", b"requirement-workflow:", b"<!-- requirement-workflow:begin -->", b"<!-- requirement-workflow:end -->"),
  (".gitignore", "gitignore.txt", b"requirement-workflow-local:", b"# requirement-workflow-local:begin", b"# requirement-workflow-local:end"),
  ("CLAUDE.md", "claude-entry.md", b"requirement-workflow-bridge:", b"<!-- requirement-workflow-bridge:begin -->", b"<!-- requirement-workflow-bridge:end -->"),
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
_TPL_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0d\x0e-\x1f\x7f]")
_CTRL_MAP = {"\x08": r"\b", "\x0c": r"\f", "\x0d": r"\r"}
_LINK_RE = re.compile(
  r"(?m)^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?(?:^ {0,3}\1[ \t]*(?=\r?\n|\Z)|\Z)"
  r"|<!--[\s\S]*?-->|(`+)(?!`)[^\n]*?(?<!`)\2(?!`)|\]\(([^)\s]+)\)"
)


class HelperError(ValueError):
  pass


def _req(ok: bool, err: str) -> None:
  if not ok:
    raise HelperError(err)


def normalize_hosts(raw: str) -> list[str]:
  _req(isinstance(raw, str), "unsupported_or_empty_hosts")
  hs = list(dict.fromkeys(HOST_ALIASES.get(h, h) for h in (x.strip() for x in raw.split(",")) if h))
  _req(bool(hs) and all(h in HOSTS for h in hs), "unsupported_or_empty_hosts")
  return hs


def _bad_loc(loc) -> bool:
  return not isinstance(loc, str) or not loc.strip() or ("://" in loc and "@" in loc.split("://", 1)[1].split("/", 1)[0])


def _strip_comment(raw: str) -> str:
  if raw.lstrip(" ").startswith("#"):
    return ""
  q = None
  for i, ch in enumerate(raw):
    if q is None:
      if ch in ('"', "'"):
        q = ch
      elif ch == "#" and (i == 0 or raw[i - 1] == " "):
        return raw[:i].rstrip(" ")
    elif ch == q and (q == "'" or i == 0 or raw[i - 1] != "\\"):
      q = None
  _req(q is None, "yaml_unclosed_quote")
  return raw.rstrip(" ")


def _scalar(raw: str):
  v = raw.strip()
  if not v or v in ("null", "~"):
    return None
  if v in ("true", "false"):
    return v == "true"
  if re.fullmatch(r"-?[0-9]+", v):
    return int(v)
  _req(not v.startswith(("&", "*")), "yaml_anchor_rejected")
  if v[0] in ('"', "'"):
    _req(len(v) >= 2 and v[-1] == v[0], "yaml_unclosed_quote")
    return v[1:-1]
  return v


def parse_simple_yaml(text: str) -> dict:
  root: dict = {}
  stack, need = [root], False
  for no, raw in enumerate(text.splitlines(), 1):
    _req("\t" not in raw, f"yaml_tab_rejected:{no}")
    ln = _strip_comment(raw)
    if not ln.strip():
      continue
    ind = len(ln) - len(ln.lstrip(" "))
    _req(ind % 2 == 0, f"yaml_odd_indent:{no}")
    lvl = ind // 2
    if need:
      _req(lvl == len(stack) - 1, f"yaml_unexpected_indent:{no}")
      need = False
    else:
      _req(lvl < len(stack), f"yaml_unexpected_indent:{no}")
      del stack[lvl + 1 :]
    body = ln[ind:]
    _req(":" in body, f"yaml_invalid_line:{no}")
    rk, rv = body.split(":", 1)
    k = rk.strip()
    _req(rk == k and bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)), f"yaml_invalid_key:{no}")
    _req(not rv or rv.startswith(" "), f"yaml_invalid_line:{no}")
    rest, cur = rv.strip(), stack[lvl]
    _req(k not in cur, f"yaml_duplicate_key:{k}")
    if rest == "":
      cur[k] = child = {}
      stack.append(child)
      need = True
    else:
      cur[k] = _scalar(rest)
  _req(not need, "yaml_empty_mapping_rejected")
  return root


def _read_fw(pkg_root: Path) -> dict:
  fw = parse_simple_yaml((pkg_root / "framework.yaml").read_text(encoding="utf-8"))
  ver, pv = fw.get("version"), fw.get("protocol_version")
  _req(fw.get("schema_version") == 1 and fw.get("name") == "multi-agent-requirement-workflow" and isinstance(ver, str) and bool(ver.strip()), "invalid_framework_yaml")
  _req(type(pv) is int and pv == PROTOCOL_VERSION, "invalid_protocol_version")
  return fw


def format_lock_yaml(*, name: str, version: str, protocol_version: int, sha256: str, kind: str, location: str, revision) -> bytes:
  rev = "null" if revision is None else revision
  return f"schema_version: 1\npackage:\n  name: {name}\n  version: {version}\n  protocol_version: {protocol_version}\n  sha256: {sha256}\nsource:\n  kind: {kind}\n  location: {location}\n  revision: {rev}\n".encode("utf-8")


def _bad_art(p: Path) -> None:
  _req(p.name not in FORBIDDEN and p.suffix not in {".pyc", ".pyo"}, f"bytecode or system artifact rejected: {p}")


def _excl(rel: str) -> bool:
  return any(rel == px.rstrip("/") or rel.startswith(px) for px in EXCLUDED_PREFIXES)


def _no_sym(path: Path) -> None:
  cur = path.absolute()
  for part in (*reversed(cur.parents), cur):
    _req(not (os.path.lexists(part) and stat.S_ISLNK(part.lstat().st_mode)), f"symlink_rejected:{part}")


def compute_digest(root: Path) -> dict:
  _req(stat.S_ISDIR(root.lstat().st_mode), "package root must be an ordinary directory")
  names, exp = {p.name for p in root.iterdir()}, ROOT_FILES | ROOT_DIRS
  _req(names == exp, f"missing={sorted(exp - names)}, extra={sorted(names - exp)}")
  rows = []

  def visit(p: Path) -> None:
    _bad_art(p)
    m = p.lstat().st_mode
    if stat.S_ISREG(m):
      rows.append([p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()])
    elif stat.S_ISDIR(m):
      ch = list(p.iterdir())
      _req(bool(ch), f"empty_package_directory_present:{p.relative_to(root).as_posix()}")
      for c in ch:
        visit(c)
    else:
      raise HelperError(f"link or special file rejected: {p}")

  for n in names:
    p = root / n
    _req((stat.S_ISDIR if n in ROOT_DIRS else stat.S_ISREG)(p.lstat().st_mode), f"unexpected package entry type: {p}")
    visit(p)
  rows.sort(key=lambda r: r[0])
  return {"file_count": len(rows), "sha256": hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()}


def stage_clean_package(source_root: Path, dest: Path, *, include_working_tree: bool = False) -> dict:
  _no_sym(source_root)
  _req(source_root.is_dir(), "source_root_not_directory")
  allowed = ROOT_FILES | ROOT_DIRS
  tracked = None
  if (source_root / ".git").exists() and not include_working_tree:
    tracked = {e for e in subprocess.check_output(["git", "ls-files", "-z"], cwd=source_root).decode("utf-8").split("\0") if e}
  dest.mkdir(parents=True, exist_ok=True)

  def walk(p: Path, top: bool = False) -> None:
    rel = p.relative_to(source_root).as_posix()
    if not top and _excl(rel):
      return
    _no_sym(p)
    _bad_art(p)
    m = p.lstat().st_mode
    if top:
      _req((stat.S_ISDIR if p.name in ROOT_DIRS else stat.S_ISREG)(m), f"unexpected package entry type: {p}")
    if stat.S_ISDIR(m):
      if tracked is None:
        (dest / rel).mkdir(parents=True, exist_ok=True)
      for sub in p.iterdir():
        walk(sub)
    else:
      _req(stat.S_ISREG(m), f"non_regular_package_file:{rel}")
      if tracked is None or rel in tracked:
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(p.read_bytes())

  for name in allowed:
    if os.path.lexists(source_root / name):
      walk(source_root / name, top=True)
  return compute_digest(dest)


def _merge_block(orig: bytes, block: bytes, tok: bytes, b_ln: bytes, e_ln: bytes, *, upgrade: bool, restore_only: bool) -> bytes:
  block = block if block.endswith(b"\n") else block + b"\n"
  cnt = orig.count(tok)
  _req(cnt in (0, 2), "adapter_modified:incomplete_or_duplicate_markers")
  if cnt == 2:
    sm = list(re.finditer(rb"(?m)^" + re.escape(b_ln) + rb"\r?\n", orig))
    em = list(re.finditer(rb"(?m)^" + re.escape(e_ln) + rb"(?:\r?\n|\Z)", orig))
    _req(len(sm) == 1 and len(em) == 1 and em[0].start() >= sm[0].end(), "adapter_modified:noncanonical_markers")
    s, e = sm[0].start(), em[0].end()
    norm = orig[s:e].replace(b"\r\n", b"\n")
    if (norm if norm.endswith(b"\n") else norm + b"\n") != block:
      _req(upgrade and not restore_only, "adapter_modified:block_differs_without_upgrade")
      return orig[:s] + block + orig[e:]
    return orig
  _req(not restore_only, "restore_failed:managed_block_missing")
  return orig + (b"\n" if orig and not orig.endswith(b"\n") else b"") + block


def _load_codex_reg(pkg_root: Path):
  hp = pkg_root / CODEX_REG_REL
  spec = importlib.util.spec_from_file_location("codex_registry", hp)
  reg = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(reg)
  return hp, reg


def _toml_sub(hp: Path, body: str, payload: dict, err: str) -> str:
  snip = (
    "import sys,importlib.util as u,json,base64 as b;sys.dont_write_bytecode=True;"
    "p=json.loads(sys.stdin.read());s=u.spec_from_file_location('cr',p['h']);"
    "m=u.module_from_spec(s);s.loader.exec_module(m);m.tomllib is None and sys.exit(3)\n" + body
  )
  inp = json.dumps({"h": str(hp), **payload})
  for c in PY_CANDS:
    if exe := shutil.which(c):
      pr = subprocess.run([exe, "-B", "-c", snip], input=inp, capture_output=True, text=True)
      if pr.returncode == 0:
        return pr.stdout.strip()
      if pr.returncode != 3:
        raise HelperError(pr.stderr.strip() or err)
  raise HelperError("toml_parser_unavailable")


def _merge_codex(pkg_root: Path, orig: bytes, block: bytes, *, upgrade: bool, restore_only: bool) -> bytes:
  hp, reg = _load_codex_reg(pkg_root)
  prev = hashlib.sha256(orig[slice(*reg._span(orig))]).hexdigest() if (upgrade and b"requirement-workflow:codex-registry:" in orig) else None
  if reg.tomllib is not None:
    try:
      return reg.merge(orig, block, restore_only=restore_only, previous_sha256=prev)
    except reg.RegistryError as exc:
      raise HelperError(str(exc)) from exc
  b64 = lambda x: base64.b64encode(x).decode()
  return base64.b64decode(
    _toml_sub(
      hp,
      "print(b.b64encode(m.merge(b.b64decode(p['o']),b.b64decode(p['b']),restore_only=p['r'],previous_sha256=p['p'])).decode())\n",
      {"o": b64(orig), "b": b64(block), "r": restore_only, "p": prev},
      "codex_registry_merge_failed",
    )
  )


def _strip_doc_header(markdown: str) -> str:
  t = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n*", "", markdown, count=1, flags=re.S)
  return re.sub(r"\A(?:\r?\n)*#[ \t]+[^\r\n]*(?:\r?\n)*", "", t, count=1).strip()


def _rewrite_pkg_links(markdown: str, rel_dir: str, cache_rel: str) -> str:
  bd, cb = rel_dir.strip("/"), cache_rel.rstrip("/")

  def repl(m: re.Match) -> str:
    t = m.group(3)
    if not t or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", t) or t[0] == "#" or "{" in t or "<" in t:
      return m.group(0)
    fp, sep, frag = t.partition("#")
    _req(not fp.startswith("/") and "\\" not in fp, f"link_escapes_package_root:{t}")
    np = posixpath.normpath(posixpath.join(bd, fp) if bd and bd != "." else fp)
    _req(np not in ("", ".", "..") and not np.startswith("../"), f"link_escapes_package_root:{t}")
    return f"]({cb}/{np}{sep}{frag})"

  return _LINK_RE.sub(repl, markdown)


def _toml_escape_multiline(text: str) -> str:
  return _CTRL_RE.sub(lambda m: _CTRL_MAP.get(m.group(0), f"\\u{ord(m.group(0)):04x}"), text.replace("\\", "\\\\").replace('"""', r'\"\"\"'))


def _render(tpl: str, vals: dict) -> str:
  rem = _TPL_RE.sub("", tpl)
  _req("{{" not in rem and "}}" not in rem, "unresolved_template_parameter")

  def repl(m: re.Match) -> str:
    _req(m.group(1) in vals, f"unresolved_template_parameter:{m.group(1)}")
    return vals[m.group(1)]

  return _TPL_RE.sub(repl, tpl)


def _build_roles(pkg_root: Path, hosts: list[str], sha256: str) -> dict[str, bytes]:
  _req(isinstance(sha256, str) and bool(HEX64.fullmatch(sha256)), "invalid_package_sha256")
  cdir, td = f".agents/requirement-workflow-cache/{sha256}", pkg_root / TPL_REL
  btpl = (td / "role-body.md").read_text(encoding="utf-8")
  specs = {"codex": (".codex/agents", "_", "toml", "native-codex.toml"), "claude-code": (".claude/agents", "-", "md", "native-claude-code.md"), "opencode": (".opencode/agents", "-", "md", "native-opencode.md")}
  secs = {
    lg: (
      rl,
      dc,
      _rewrite_pkg_links(_strip_doc_header((pkg_root / f"agents/{rl}.md").read_text(encoding="utf-8")), "agents", cdir),
      _rewrite_pkg_links(_strip_doc_header((pkg_root / f"skills/{sk}/SKILL.md").read_text(encoding="utf-8")), f"skills/{sk}", cdir),
    )
    for lg, (rl, sk, dc) in ROLES.items()
  }
  out, checks = {}, []
  for rh in hosts:
    h = HOST_ALIASES.get(rh, rh)
    if h == "agents-md":
      continue
    _req(h in specs, "unsupported_or_empty_hosts")
    rdir, sep, ext, tn = specs[h]
    nt = (td / tn).read_text(encoding="utf-8")
    for lg, (rl, dc, rb, sb) in secs.items():
      nm = f"requirement{sep}{lg}"
      vals = {"native_name": nm, "role": rl, "description": dc, "cache_dir": cdir, "role_content": rb, "skill_content": sb}
      body = _render(btpl, vals)
      vals.update(role_body=body, role_body_toml=_toml_escape_multiline(body))
      raw = _render(nt, vals).encode("utf-8")
      out[f"{rdir}/{nm}.{ext}"] = raw
      if h == "codex":
        checks.append((raw, nm, dc, body + "\n"))
  if checks:
    hp, reg = _load_codex_reg(pkg_root)
    if reg.tomllib is not None:
      for raw, nm, dc, exp in checks:
        try:
          p = reg._parse(raw)
        except reg.RegistryError as exc:
          raise HelperError(str(exc)) from exc
        _req(p.get("name") == nm and p.get("description") == dc and p.get("developer_instructions") == exp, f"codex_role_toml_roundtrip_mismatch:{nm}")
    else:
      _toml_sub(
        hp,
        "for r,n,d,i in p['c']:\n x=m._parse(b.b64decode(r))\n if x.get('name')!=n or x.get('description')!=d or x.get('developer_instructions')!=i:sys.exit(4)\n",
        {"c": [[base64.b64encode(r).decode(), n, d, i] for r, n, d, i in checks]},
        "codex_role_toml_roundtrip_mismatch",
      )
  return out


def _populate_cache(staged: Path, target_root: Path, expected_sha: str, *, prune_others: bool = False) -> bool:
  parent = target_root / ".agents/requirement-workflow-cache"
  cdir = parent / expected_sha
  _no_sym(cdir)
  if cdir.exists():
    _req(cdir.is_dir() and compute_digest(cdir)["sha256"] == expected_sha, "framework_integrity_mismatch")
    created = False
  else:
    parent.mkdir(parents=True, exist_ok=True)
    tmp = parent / f".tmp-{os.getpid()}-{id(staged)}-{expected_sha[:12]}"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(staged, tmp)
    if compute_digest(tmp)["sha256"] != expected_sha:
      shutil.rmtree(tmp, ignore_errors=True)
      raise HelperError("staged_cache_digest_mismatch")
    try:
      tmp.rename(cdir)
      created = True
    except OSError:
      shutil.rmtree(tmp, ignore_errors=True)
      _no_sym(cdir)
      _req(cdir.is_dir() and compute_digest(cdir)["sha256"] == expected_sha, "framework_integrity_mismatch")
      created = False
  if prune_others and parent.is_dir():
    for e in list(parent.iterdir()):
      if e.name != expected_sha and HEX64.fullmatch(e.name):
        _no_sym(e)
        if e.is_dir():
          shutil.rmtree(e)
  return created


def _jout(obj: dict) -> None:
  print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def cmd_digest(args) -> int:
  _req(args.expected_sha256 is None or bool(HEX64.fullmatch(args.expected_sha256)), "expected_sha256 must be 64 lowercase hex characters")
  if args.package_root is not None:
    _no_sym(args.package_root)
    res = compute_digest(args.package_root)
    _read_fw(args.package_root)
  else:
    with tempfile.TemporaryDirectory() as tmp:
      st = Path(tmp) / "pkg"
      info = stage_clean_package(args.source_root.resolve(), st, include_working_tree=args.include_working_tree)
      fw = _read_fw(st)
      res = {"version": str(fw["version"]), "protocol_version": PROTOCOL_VERSION, "file_count": info["file_count"], "total_bytes": sum(p.stat().st_size for p in st.rglob("*") if p.is_file()), "sha256": info["sha256"]}
  if args.expected_sha256 is not None:
    res["matches_expected"] = res["sha256"] == args.expected_sha256
    _jout(res)
    return 0 if res["matches_expected"] else 1
  _jout(res)
  return 0


def cmd_install(args) -> int:
  src, dst = args.source_root.resolve(), args.target_root.resolve()
  _no_sym(dst)
  _req(dst.is_dir(), "target_root_not_directory")
  hosts, sk = normalize_hosts(args.hosts), args.source_kind
  if sk == "self":
    _req(src == dst and args.source_location == ".", "invalid_source_metadata:self_requires_same_root_and_dot_location")
    _req(args.source_revision in (None, "self"), "invalid_source_metadata:self_revision_must_be_self")
    rev, inc_wt = "self", True
  elif sk == "git":
    _req(not _bad_loc(args.source_location), "invalid_source_metadata")
    _req(bool(args.source_revision) and bool(HEX40.fullmatch(args.source_revision)), "git_source_requires_40_hex_revision")
    rev, inc_wt = args.source_revision, args.include_working_tree
  elif sk == "manual":
    _req(not _bad_loc(args.source_location), "invalid_source_metadata")
    _req(not args.source_revision, "manual_source_forbids_revision")
    rev, inc_wt = None, args.include_working_tree
  else:
    raise HelperError("invalid_source_metadata")

  with tempfile.TemporaryDirectory() as tmp:
    st = Path(tmp) / "pkg"
    info = stage_clean_package(src, st, include_working_tree=inc_wt)
    sha, fw, td, planned = info["sha256"], _read_fw(st), st / TPL_REL, {}
    lp = dst / "workflow.lock.yaml"
    lock_b = format_lock_yaml(name=fw["name"], version=str(fw["version"]), protocol_version=PROTOCOL_VERSION, sha256=sha, kind=sk, location=args.source_location, revision=rev)
    if lp.exists():
      _no_sym(lp)
      ex_sha = (parse_simple_yaml(lp.read_text(encoding="utf-8")).get("package") or {}).get("sha256")
      _req(ex_sha == sha or args.upgrade, "lock_mismatch_use_upgrade")
      if lp.read_bytes() != lock_b:
        _req(args.upgrade or ex_sha != sha, "lock_metadata_modified")
        planned["workflow.lock.yaml"] = lock_b
    else:
      planned["workflow.lock.yaml"] = lock_b

    wfp = dst / "workflow.yaml"
    _no_sym(wfp) if wfp.exists() else planned.setdefault("workflow.yaml", DEFAULT_WORKFLOW_YAML)

    for rel, tpl_n, tok, bl, el in BLOCKS:
      if rel == "CLAUDE.md" and "claude-code" not in hosts:
        continue
      fp = dst / rel
      if fp.exists():
        _no_sym(fp)
      orig = fp.read_bytes() if fp.exists() else b""
      m = _merge_block(orig, (td / tpl_n).read_bytes(), tok, bl, el, upgrade=args.upgrade, restore_only=False)
      if m != orig:
        planned[rel] = m

    if "codex" in hosts:
      cxp = dst / ".codex/config.toml"
      if cxp.exists():
        _no_sym(cxp)
      ocx = cxp.read_bytes() if cxp.exists() else b""
      mcx = _merge_codex(st, ocx, (td / "codex-registry.toml").read_bytes(), upgrade=args.upgrade, restore_only=False)
      if mcx != ocx:
        planned[".codex/config.toml"] = mcx

    for rel, content in _build_roles(st, hosts, sha).items():
      fp = dst / rel
      if fp.exists():
        _no_sym(fp)
        if fp.read_bytes() != content:
          _req(args.upgrade, f"role_file_modified_without_upgrade:{rel}")
          planned[rel] = content
      else:
        planned[rel] = content

    _populate_cache(st, dst, sha, prune_others=args.upgrade)
    for rel, content in sorted(planned.items()):
      fp = dst / rel
      fp.parent.mkdir(parents=True, exist_ok=True)
      fp.write_bytes(content)
    _jout({"package_sha256": sha, "file_count": info["file_count"], "cache_dir": f".agents/requirement-workflow-cache/{sha}", "installed_hosts": hosts, "updated_files": sorted(planned)})
    return 0


def cmd_restore(args) -> int:
  src, dst = args.source_root.resolve(), args.target_root.resolve()
  _no_sym(dst)
  lp = dst / "workflow.lock.yaml"
  _req(lp.is_file(), "restore_failed:missing_workflow_lock")
  _no_sym(lp)
  lock = parse_simple_yaml(lp.read_text(encoding="utf-8"))
  _req(lock.get("schema_version") == 1, "restore_blocked:invalid_lock_schema")
  pkg, sm = lock.get("package") or {}, lock.get("source") or {}
  exp_sha, kind, loc, rev, lpv = pkg.get("sha256"), sm.get("kind"), sm.get("location"), sm.get("revision"), pkg.get("protocol_version")
  _req(type(lpv) is int and lpv == PROTOCOL_VERSION, "invalid_protocol_version")
  if kind == "git":
    _req(not _bad_loc(loc) and isinstance(rev, str) and bool(HEX40.fullmatch(rev)), "restore_blocked:requires_canonical_git_or_self_lock")
    inc_wt = args.include_working_tree
  elif kind == "self":
    _req(src == dst and loc == "." and rev == "self", "restore_blocked:invalid_self_lock")
    inc_wt = True
  else:
    raise HelperError("restore_blocked:requires_canonical_git_or_self_lock")
  _req(isinstance(exp_sha, str) and bool(HEX64.fullmatch(exp_sha)), "restore_failed:invalid_lock_sha256")

  with tempfile.TemporaryDirectory() as tmp:
    st = Path(tmp) / "pkg"
    info = stage_clean_package(src, st, include_working_tree=inc_wt)
    fw = _read_fw(st)
    _req(info["sha256"] == exp_sha, "framework_integrity_mismatch:source_differs_from_lock")
    exp_lock = format_lock_yaml(name=fw["name"], version=str(fw["version"]), protocol_version=PROTOCOL_VERSION, sha256=exp_sha, kind=kind, location=loc, revision=rev)
    _req(lp.read_bytes().replace(b"\r\n", b"\n") == exp_lock, "restore_failed:lock_metadata_modified")
    td = st / TPL_REL
    for rel, tpl_n, tok, bl, el in BLOCKS:
      if rel == "CLAUDE.md" and not (dst / ".claude/agents").is_dir():
        continue
      fp = dst / rel
      if not fp.is_file():
        _req(rel != "AGENTS.md", "restore_failed:missing_agents_md")
        continue
      _no_sym(fp)
      _merge_block(fp.read_bytes(), (td / tpl_n).read_bytes(), tok, bl, el, upgrade=False, restore_only=True)

    det = []
    if (dst / ".codex/config.toml").is_file() or (dst / ".codex/agents").is_dir():
      det.append("codex")
      cxp = dst / ".codex/config.toml"
      _req(cxp.is_file(), "restore_failed:missing_codex_config")
      _merge_codex(st, cxp.read_bytes(), (td / "codex-registry.toml").read_bytes(), upgrade=False, restore_only=True)
    for h, d in (("claude-code", ".claude/agents"), ("opencode", ".opencode/agents")):
      if (dst / d).is_dir():
        det.append(h)
    for rel, exp_b in _build_roles(st, det, exp_sha).items():
      fp = dst / rel
      _req(fp.is_file() and fp.read_bytes() == exp_b, f"adapter_modified:{rel}")
    _jout({"package_sha256": exp_sha, "file_count": info["file_count"], "cache_dir": f".agents/requirement-workflow-cache/{exp_sha}", "restored": _populate_cache(st, dst, exp_sha)})
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
  for fl in ("--source-root", "--target-root"):
    i.add_argument(fl, required=True, type=Path)
  for fl in ("--hosts", "--source-kind", "--source-location"):
    i.add_argument(fl, required=True)
  i.add_argument("--source-revision", default=None)
  i.add_argument("--upgrade", action="store_true")
  i.add_argument("--include-working-tree", action="store_true")
  r = sub.add_parser("restore")
  for fl in ("--source-root", "--target-root"):
    r.add_argument(fl, required=True, type=Path)
  r.add_argument("--include-working-tree", action="store_true")
  try:
    a = p.parse_args()
    return {"digest": cmd_digest, "install": cmd_install, "restore": cmd_restore}[a.command](a)
  except (OSError, ValueError, subprocess.CalledProcessError) as exc:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
  sys.exit(main())
