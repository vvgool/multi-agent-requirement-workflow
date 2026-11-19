#!/usr/bin/env python3
"""Deterministic stdlib gate for feature artifacts and differential write boundaries."""
from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import argparse, fnmatch, hashlib, json, os, re, subprocess, unicodedata  # noqa: E402
from pathlib import Path  # noqa: E402

MAX_TASK_LINES = 100
SPEC_GATE_STATES = {"pending_approval", "pending_req_approval"}
VERIFICATION_PASS_STATES = {"通过", "有条件通过"}

PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]+\}\}")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
CMT_INLINE_RE = re.compile(r"<!--[\s\S]*?(?:-->|$)|(?<!`)(`+)(?!`)(?:(?!\n\n)[\s\S])*?(?<!`)\1(?!`)")
INLINE_RE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")
LIST_CB_RE = re.compile(r"^[ \t]*(?:>[ \t]*)*(?:[-+*]|\d+[.)])[ \t]+\[([ xX])\](?:[ \t]+(.*))?$", re.M)
TASK_ITEM_RE = re.compile(r"^[ \t]*[-*+][ \t]+\[([ xX])\](?:[ \t]+(.*))?$")
TABLE_CB_RE = re.compile(r"(?:\||<br\s*/?>)[ \t]*(?:[-+*][ \t]+)?\[[ xX]\](?=[ \t|]|$)|^[ \t]*\|.*\[[ xX]\].*$", re.M)
SPEC_MUT_RE = re.compile(r"^[ \t]*(?:(?:>[ \t]*|#{1,6}[ \t]+)\*{0,2}|\*{2})(?:阶段状态|批准记录|(?:验收|诊断)?结论状态)\*{0,2}[ \t]*[:：]", re.M)
VALID_STATUS_RE = re.compile(r"^(?:通过|失败|未执行|阻塞|不适用（[^）\n]+）)$")
VOLATILE_RE = re.compile(r"(?<![A-Za-z0-9_.-])(?:/private/tmp|/tmp|/var/folders)(?:/[^\s`｜|,;，；)）\"']*)?")
PERSIST_RE = re.compile(
  r"(?:^|[\s`])--[A-Za-z0-9][\w-]*|\b(?:unittest|pytest|python3?(?:\.\d+)?|npm|pnpm|yarn|cargo|go\s+test|mvn|gradle|make|bash|sh|zsh)\b"
  r"|[A-Za-z0-9_./-]+\.(?:py|sh|js|ts|go|rs|java|rb)\b|\b(?:verification|spec)\.md\b"
  r"|\b(?:evidence|tests|scripts|skills|workflow|agents|templates|docs|src|agent-features)/|\b[A-Za-z0-9_.-]*[A-Za-z][A-Za-z0-9_.-]*/[A-Za-z0-9_./-]*\.[A-Za-z0-9]+\b"
)
DEP_RE = re.compile(r"\[[^\]\n]*依赖[^\]\n]*\]|（[^）\n]*依赖[^）\n]*）|\([^)\n]*依赖[^)\n]*\)")
BRK_RE = re.compile(r"（[^）\n]*）|\([^)\n]*\)|\[[^\]\n]*\]")
RANGE_RE = re.compile(r"\bT-?(\d+)\s*(?:\.{2,3}|[-–—~～])\s*T-?(\d+)\b|\bT-?(\d+)\s*\.{2,3}\s*(\d+)\b")
SINGLE_RE = re.compile(r"\bT-?(\d+)\b")


class GateViolation(Exception):
  def __init__(self, error: str, **extra: object) -> None:
    super().__init__(error)
    self.error, self.extra = error, extra


def _req(ok: bool, err: str, **extra: object) -> None:
  if not ok:
    raise GateViolation(err, **extra)


class _Parser(argparse.ArgumentParser):
  def error(self, message: str) -> None:
    raise GateViolation(f"invalid_arguments:{message}")


def _nfc(s: str) -> str:
  return unicodedata.normalize("NFC", s)


def _unq(v: str) -> str:
  s = v.strip()
  return s[1:-1].strip() if len(s) >= 2 and s[0] == "`" and s[-1] == "`" and "`" not in s[1:-1] else s


def strip_code_and_comments(markdown_text: str, *, strip_inline_code: bool = False) -> str:
  lns, fc, fl = [], "", 0
  for raw in markdown_text.splitlines(keepends=True):
    nl, bd = ("\n" if raw.endswith(("\n", "\r")) else ""), raw.rstrip("\r\n")
    if not fc:
      m = FENCE_RE.match(bd)
      if m and (m.group(1)[0] == "~" or "`" not in m.group(2)):
        fc, fl = m.group(1)[0], len(m.group(1))
        lns.append(nl)
      else:
        lns.append(raw)
    else:
      if re.match(rf"^[ \t]*{re.escape(fc)}{{{fl},}}[ \t]*$", bd):
        fc, fl = "", 0
      lns.append(nl)
  return CMT_INLINE_RE.sub(lambda m: "\n" * m.group(0).count("\n") if (m.group(1) is None or strip_inline_code) else m.group(0), "".join(lns))


def split_table_cells(line: str) -> list[str]:
  s = line.strip()
  if not s.startswith("|"):
    return []
  mk = INLINE_RE.sub(lambda m: m.group(0).replace("|", "\x00"), s)
  pts = [p.replace("\x00", "|").replace(r"\|", "|").strip() for p in re.split(r"(?<!\\)\|", mk)]
  if pts and pts[0] == "":
    pts = pts[1:]
  if pts and pts[-1] == "" and mk.endswith("|") and not mk.endswith(r"\|"):
    pts = pts[:-1]
  return pts


def _tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
  res, lns, i = [], text.splitlines(), 0
  while i < len(lns):
    if lns[i].strip().startswith("|"):
      blk = []
      while i < len(lns) and lns[i].strip().startswith("|"):
        if r := split_table_cells(lns[i]):
          blk.append(r)
        i += 1
      if len(blk) >= 2 and all(re.match(r"^:?-{3,}:?$", c.strip()) for c in blk[1]):
        res.append((blk[0], blk[2:]))
    else:
      i += 1
  return res


def _read_md(path: Path, name: str, *, cb_err: str | None = None) -> tuple[str, str, str]:
  _req(path.is_file(), f"missing_{name.replace('.', '_')}")
  try:
    raw = path.read_text(encoding="utf-8")
  except UnicodeDecodeError as exc:
    raise GateViolation(f"invalid_utf8:{name}:{exc}") from exc
  clean, no_in = strip_code_and_comments(raw), strip_code_and_comments(raw, strip_inline_code=True)
  if ph := PLACEHOLDER_RE.search(no_in):
    raise GateViolation(f"unresolved_template_placeholder:{name}:{ph.group(0)}")
  if cb_err and (LIST_CB_RE.search(no_in) or TABLE_CB_RE.search(no_in)):
    raise GateViolation(cb_err)
  return raw, clean, no_in


def _top(md: str) -> str:
  m = re.search(r"^[ \t]*##[ \t]+", md, re.M)
  return md[: m.start()] if m else md


def _sec(h_re: str, md: str, err: str) -> str:
  m = re.search(h_re, md, re.M)
  _req(m is not None, err)
  tail = md[m.end() :]
  nxt = re.search(r"^[ \t]*#{1,2}[ \t]+", tail, re.M)
  return tail[: nxt.start()] if nxt else tail


def _validate_spec(sp: Path, state: str, task_ids: set[str]) -> None:
  _, clean, no_in = _read_md(sp, "spec.md", cb_err="spec_checkbox_forbidden")
  _req(not SPEC_MUT_RE.search(no_in), "spec_mutable_status_forbidden")
  _req(bool(re.search(r"^[ \t]*##[ \t]+1\.", clean, re.M)), "missing_spec_section:1")
  sec2 = _sec(r"^[ \t]*##[ \t]+2\..*$", clean, "missing_spec_section:2")
  _req(bool(re.search(r"\bAC-\d+\b", clean)), "missing_spec_ac")
  tbls = _tables(sec2)
  utbls = [t for t in tbls if t[0] and re.search(r"单元|任务|\bunit\b", t[0][0], re.I)] or tbls
  sids: set[str] = set()

  def _exp(m: re.Match[str]) -> str:
    g1, g2, g3, g4 = m.groups()
    s, e = int(g1 or g3), int(g2 or g4)
    _req(s <= e and (e - s) <= 1000, f"task_spec_unit_mismatch:invalid_range_{s}_{e}")
    sids.update(f"T{k}" for k in range(s, e + 1))
    return " "

  for _, rows in utbls:
    for r in rows:
      if r:
        left = RANGE_RE.sub(_exp, strip_code_and_comments(BRK_RE.sub(" ", r[0])))
        sids.update(f"T{int(sm.group(1))}" for sm in SINGLE_RE.finditer(left))
  if not (state == "pending_req_approval" and not sids):
    _req(bool(sids) and sids == task_ids, f"task_spec_unit_mismatch:task={sorted(task_ids)},spec={sorted(sids)}")


def verify_feature_dir(feature_dir: Path, phase: str) -> dict[str, object]:
  _req(not feature_dir.is_symlink(), f"symlink_rejected:{feature_dir.name}")
  _req(feature_dir.exists() and feature_dir.is_dir(), f"feature_dir_not_found:{feature_dir}")
  for rt, ds, fs in os.walk(feature_dir, followlinks=False):
    b = Path(rt)
    for d in ds:
      _req(not (b / d).is_symlink(), f"symlink_rejected:{d}")
    for f in fs:
      fp = b / f
      _req(not (fp.is_symlink() and (f.lower().endswith(".md") or fp.is_dir())), f"symlink_rejected:{f}")
  raw, clean, no_in = _read_md(feature_dir / "task.md", "task.md")
  lines = len(raw.splitlines())
  _req(lines <= MAX_TASK_LINES, f"task_lines_exceeded:{lines}")
  _req(not TABLE_CB_RE.search(no_in), "table_checkbox_forbidden")
  top = _top(clean)
  st = re.findall(r"^[ \t]*>[ \t]*\*\*阶段状态\*\*[ \t]*[:：][ \t]*(.*?)[ \t]*$", top, re.M)
  _req(len(st) == 1, "invalid_stage_state:missing_or_duplicate")
  state = _unq(st[0])
  _req((phase == "spec-gate" and state in SPEC_GATE_STATES) or (phase == "verified" and state == "verified"), f"invalid_stage_state:{state}")
  ap = re.findall(r"^[ \t]*>[ \t]*\*\*批准记录\*\*[ \t]*[:：][ \t]*(.*?)[ \t]*$", top, re.M)
  _req(len(ap) == 1 and bool(_unq(ap[0])), "invalid_approval_record:empty_or_missing")
  _req(phase != "spec-gate" or "待确认" in ap[0], "invalid_approval_record:missing_pending")
  _req(phase != "verified" or "待确认" not in ap[0], "invalid_approval_record:contains_pending")
  _req(phase != "verified" or not re.search(r"^[ \t]*#{1,6}[ \t]+本次请确认(?:\s|$)", clean, re.M), "confirmation_section_remaining")

  tasks, seen = [], set()
  for ln in clean.splitlines():
    if m := TASK_ITEM_RE.match(ln):
      mk, rest = m.group(1), (m.group(2) or "").strip()
      idm = SINGLE_RE.search(strip_code_and_comments(DEP_RE.sub(" ", rest), strip_inline_code=True))
      if idm is None and (lt := re.match(r"^`([^`\n]+)`", rest)):
        idm = SINGLE_RE.fullmatch(lt.group(1).strip())
      _req(idm is not None, f"missing_task_id:{rest[:40]}")
      tid = f"T{int(idm.group(1))}"
      _req(tid not in seen, f"duplicate_task_id:{tid}")
      seen.add(tid)
      tasks.append((tid, mk))
  _req(bool(tasks), "no_task_checkboxes")
  tids, unck = {t for t, _ in tasks}, [t for t, m in tasks if m == " "]
  _req(phase != "spec-gate" or bool(unck), "no_unchecked_tasks_in_spec_gate")
  _req(phase != "verified" or not unck, f"unchecked_tasks_remaining:{','.join(unck)}")

  vtbls = _tables(_sec(r"^[ \t]*##[ \t]+验证摘要与阻塞[ \t]*$", clean, "missing_verification_section"))
  _req(bool(vtbls) and bool(vtbls[0][1]), "empty_verification_table")
  passed = 0
  for row in vtbls[0][1]:
    _req(len(row) >= 3, "invalid_verification_table_row")
    sv, ev = _unq(row[1]), row[2].strip()
    _req(bool(VALID_STATUS_RE.match(sv)), f"invalid_table_status:{sv}")
    if phase == "verified":
      if sv == "通过":
        passed += 1
        _req(bool(_unq(ev)), "empty_verification_evidence")
      else:
        _req(sv.startswith("不适用（"), f"unverified_table_row:{sv}")
      _req(not (VOLATILE_RE.search(ev) and not PERSIST_RE.search(VOLATILE_RE.sub(" ", ev))), "volatile_evidence_only")
  _req(phase != "verified" or passed >= 1, "unverified_table_row:no_passed_rows")

  blk = re.findall(r"^[ \t]*[-*+]?[ \t]*\*\*当前阻塞\*\*[ \t]*[:：][ \t]*(.*?)[ \t]*$", clean, re.M)
  _req((len(blk) == 1 and _unq(blk[0]) == "无") if phase == "verified" else (bool(blk) and bool(_unq(blk[0]))), "active_blocker_remaining" if phase == "verified" else "missing_blocker_field")

  sp = feature_dir / "spec.md"
  cpx = sp.exists() or bool(re.search(r"(?<![A-Za-z0-9_.-])(?:spec|verification)\.md(?![A-Za-z0-9_.-])", clean))
  if not cpx:
    nc = re.sub(r"^[ \t]*#{1,6}[ \t]+本次请确认(?:\s.*)?$(?:\n(?!^[ \t]*#{1,2}[ \t]+).*)*", "", clean, flags=re.M)
    body = "\n".join(ln for ln in nc.splitlines() if not re.match(r"^[ \t]*#", ln) and not TASK_ITEM_RE.match(ln))
    _req(bool(re.search(r"\bAC-?\d+\b", body) or re.search(r"(?:验收标准|验收条件|\bAC\b)[^\n:：]*[:：][ \t]*\S+", body)), "missing_regular_ac")
  else:
    _validate_spec(sp, state, tids)
    if phase == "verified":
      _, vc, _ = _read_md(feature_dir / "verification.md", "verification.md", cb_err="verification_checkbox_forbidden")
      vst = re.findall(r"^[ \t]*>[ \t]*\*\*(?:验收)?结论状态\*\*[ \t]*[:：][ \t]*(.*?)[ \t]*$", _top(vc), re.M)
      _req(len(vst) == 1 and _unq(vst[0]) in VERIFICATION_PASS_STATES, f"verification_not_passed:{_unq(vst[0]) if len(vst) == 1 else 'missing'}")
  return {"ok": True, "mode": "phase", "phase": phase, "complex": cpx, "stage_state": state, "task_lines": lines, "tasks": sorted(tids, key=lambda x: int(x[1:]))}


def _leaf(p: Path) -> Path:
  return p.parent.resolve() / p.name


def _rel(lf: Path, rr: Path) -> str:
  try:
    return _nfc(lf.relative_to(rr).as_posix())
  except ValueError:
    return _nfc(lf.as_posix())


def _dig(p: Path) -> dict[str, object]:
  if p.is_symlink():
    return {"sha256": "SYMLINK", "symlink_target": os.readlink(p)}
  if not p.exists():
    return {"sha256": "DELETED"}
  return {"sha256": hashlib.sha256(p.read_bytes()).hexdigest()} if p.is_file() else {"sha256": "DIR"}


def _git_entries(repo_root: Path, skip: Path | None) -> dict[str, dict[str, object]]:
  _req(repo_root.exists() and repo_root.is_dir(), f"repo_root_not_found:{repo_root}")
  pr = subprocess.run(["git", "-C", str(repo_root), "status", "-z", "--porcelain=v1", "-uall"], capture_output=True)
  _req(pr.returncode == 0, f"git_status_failed:{pr.stderr.decode('utf-8', 'replace').strip()}")
  rr = repo_root.resolve()
  srel = _rel(skip, rr) if skip is not None else None
  toks = [t for t in pr.stdout.split(b"\x00") if t]
  out: dict[str, dict[str, object]] = {}
  i = 0
  while i < len(toks):
    tok = toks[i]
    i += 1
    _req(len(tok) >= 4 and tok[2:3] == b" ", f"malformed_git_status_token:{tok!r}")
    xy, raw_r = tok[:2].decode("ascii", "replace"), tok[3:].decode("utf-8")
    rp, orig = _nfc(raw_r), None
    if "R" in xy or "C" in xy:
      _req(i < len(toks), f"missing_rename_source_for:{rp}")
      orig = _nfc(toks[i].decode("utf-8"))
      i += 1
    if srel is not None and rp == srel and orig is None:
      continue
    dk = repo_root / raw_r
    if not dk.is_symlink() and not dk.exists():
      dk = repo_root / rp
    out[rp] = {**_dig(dk), "status": xy, "orig_path": orig}
  return out


def _feat_files(repo_root: Path, fdir: Path | None, skip: Path | None) -> dict[str, dict[str, object]]:
  if fdir is None or (not fdir.exists() and not fdir.is_symlink()):
    return {}
  rr = repo_root.resolve()
  if fdir.is_symlink():
    lf = _leaf(fdir)
    return {_rel(lf, rr): _dig(fdir)} if lf != skip else {}
  out: dict[str, dict[str, object]] = {}
  for rt, ds, fs in os.walk(fdir, followlinks=False):
    b, br = Path(rt), Path(rt).resolve()
    for d in ds:
      dp, dl = b / d, br / d
      if dp.is_symlink() and dl != skip:
        out[_rel(dl, rr)] = _dig(dp)
    for f in fs:
      fp, fl = b / f, br / f
      if fl != skip:
        out[_rel(fl, rr)] = _dig(fp)
  return out


def write_snapshot(snap_path: Path, repo_root: Path, feature_dir: Path | None) -> dict[str, object]:
  skip = _leaf(snap_path)
  ge, ff = _git_entries(repo_root, skip), _feat_files(repo_root, feature_dir, skip)
  snap_path.parent.mkdir(parents=True, exist_ok=True)
  snap_path.write_text(json.dumps({"version": 1, "repo_root": _nfc(str(repo_root.resolve())), "feature_dir": _nfc(str(feature_dir)) if feature_dir is not None else None, "git_entries": ge, "feature_files": ff}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
  return {"ok": True, "mode": "write-snapshot", "snapshot": _nfc(str(snap_path)), "git_entry_count": len(ge), "feature_file_count": len(ff)}


def _allowed(rel_path: str, patterns: list[str]) -> bool:
  norm = _nfc(rel_path)
  for raw in patterns:
    pat = _nfc(raw.strip().replace("\\", "/"))
    while pat.startswith("./"):
      pat = pat[2:]
    if not pat or pat == "/":
      continue
    base = pat.rstrip("/")
    if norm == base or (not any(c in pat for c in "*?[") and norm.startswith(base + "/")) or fnmatch.fnmatchcase(norm, pat):
      return True
  return False


def check_writes(repo_root: Path, since_path: Path | None, feature_dir: Path | None, allow_patterns: list[str]) -> dict[str, object]:
  skip = _leaf(since_path) if since_path is not None else None
  cur_git, chg = _git_entries(repo_root, skip), set()
  if since_path is None:
    for p, info in cur_git.items():
      chg.add(p)
      if isinstance(info.get("orig_path"), str) and info["orig_path"]:
        chg.add(str(info["orig_path"]))
  else:
    _req(since_path.is_file(), f"snapshot_not_found:{since_path}")
    try:
      snap = json.loads(since_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
      raise GateViolation(f"invalid_snapshot:{exc}") from exc
    _req(isinstance(snap, dict) and "git_entries" in snap, "invalid_snapshot_schema")
    og, of = snap.get("git_entries", {}), snap.get("feature_files", {})
    cf = _feat_files(repo_root, feature_dir or (Path(snap["feature_dir"]) if snap.get("feature_dir") else None), skip)
    for p in set(cur_git) | set(og):
      ci, oi = cur_git.get(p), og.get(p)
      if ci != oi:
        chg.add(_nfc(p))
        for it in (ci, oi):
          if isinstance(it, dict) and isinstance(it.get("orig_path"), str) and it["orig_path"]:
            chg.add(_nfc(str(it["orig_path"])))
    chg.update(_nfc(fp) for fp in (set(cf) | set(of)) if cf.get(fp) != of.get(fp))
  v = sorted(p for p in chg if not _allowed(p, allow_patterns))
  _req(not v, "unauthorized_write_detected", violations=v)
  return {"ok": True, "mode": "check-writes", "changed": sorted(chg), "violations": []}


def main(argv: list[str] | None = None) -> int:
  try:
    p = _Parser(prog="verify_feature.py")
    for fl in ("--feature-dir", "--write-snapshot", "--repo-root", "--since"):
      p.add_argument(fl, type=Path, default=None)
    p.add_argument("--phase", choices=("spec-gate", "verified"), default=None)
    p.add_argument("--check-writes", action="store_true", default=False)
    p.add_argument("--allow", nargs="+", action="extend", default=[])
    a = p.parse_args(argv)
    _req(sum([a.phase is not None, a.write_snapshot is not None, bool(a.check_writes)]) == 1, "invalid_arguments:must_select_exactly_one_mode")
    if a.phase is not None:
      _req(a.feature_dir is not None and a.repo_root is None and a.since is None and not a.allow, "invalid_arguments:invalid_phase_args")
      res = verify_feature_dir(a.feature_dir, a.phase)
    elif a.write_snapshot is not None:
      _req(a.repo_root is not None and a.since is None and not a.allow, "invalid_arguments:invalid_snapshot_args")
      res = write_snapshot(a.write_snapshot, a.repo_root, a.feature_dir)
    else:
      _req(a.repo_root is not None, "invalid_arguments:check_writes_requires_repo_root")
      res = check_writes(a.repo_root, a.since, a.feature_dir, a.allow)
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    return 0
  except GateViolation as exc:
    sys.stderr.write(json.dumps({"ok": False, "error": exc.error, **exc.extra}, ensure_ascii=False) + "\n")
    return 2


if __name__ == "__main__":
  raise SystemExit(main())
