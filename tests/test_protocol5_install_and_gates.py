"""TDD & regression tests for Protocol 5 install_helper.py, precompiled roles, and gates."""
import base64
import errno
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills/setup-requirement-workflow/scripts/install_helper.py"
CODEX_REG = ROOT / "skills/setup-requirement-workflow/scripts/codex_registry.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_helper(*args, python_bin=sys.executable):
    return subprocess.run(
        [python_bin, "-B", str(HELPER), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def parse_toml_via_registry(raw: bytes) -> dict:
    reg = load_module("codex_registry_test", CODEX_REG)
    if reg.tomllib is not None:
        return reg._parse(raw)
    snip = (
        "import sys,importlib.util,json,base64;sys.dont_write_bytecode=True\n"
        "p=json.loads(sys.stdin.read());s=importlib.util.spec_from_file_location('cr',p['h'])\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "if m.tomllib is None:sys.exit(3)\n"
        "print(json.dumps(m._parse(base64.b64decode(p['d']))))\n"
    )
    inp = json.dumps({"h": str(CODEX_REG), "d": base64.b64encode(raw).decode("ascii")})
    for cand in (
        "python3.13",
        "python3.12",
        "python3.11",
        "/opt/homebrew/bin/python3.13",
        "/Users/wiesenwang/.local/bin/python3.11",
        "/usr/bin/python3",
    ):
        exe = shutil.which(cand)
        if exe:
            pr = subprocess.run([exe, "-B", "-c", snip], input=inp, capture_output=True, text=True)
            if pr.returncode == 0:
                return json.loads(pr.stdout)
            if pr.returncode != 3:
                raise AssertionError(f"TOML parse failed: {pr.stderr}")
    raise AssertionError("No TOML-capable Python interpreter found for round-trip verification")


class InstallHelperProtocol5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.scratch = Path(os.path.realpath(self.tmp.name))
        self.ih = load_module("install_helper_under_test", HELPER)

    def _make_protocol5_package(
        self,
        pkg_dir: Path,
        *,
        version: str = "3.0.0",
        protocol_version: int = 5,
        with_repo_extras: bool = False,
        custom_dev_skill: str = None,
    ) -> Path:
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "framework.yaml").write_text(
            f'schema_version: 1\nname: multi-agent-requirement-workflow\nversion: "{version}"\nprotocol_version: {protocol_version}\n',
            encoding="utf-8",
        )
        (pkg_dir / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        if with_repo_extras:
            (pkg_dir / "AGENTS.md").write_text("# Root Agents\n", encoding="utf-8")
            (pkg_dir / "README.md").write_text(f"# Readme {version}\n", encoding="utf-8")
            (pkg_dir / "workflow.yaml").write_text(
                'schema_version: 1\nworkspace:\n  features_dir: agent-features\n'
                'documents:\n  provider: local\n  feishu:\n    parent_node_url: null\n    write_enabled: false\n'
                'approval:\n  channel: coordinator\nissue_tracking:\n  binding: "off"\n  sync: "off"\n',
                encoding="utf-8",
            )

        for role in ("coordinator", "product", "development", "testing", "bug"):
            p = pkg_dir / "agents" / f"{role}-agent.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                f"# {role}-agent\n\n"
                f"负责 `{role}` 核心职责，遵循 [人工确认](../workflow/execution-contract.md#人工确认) 与 [最小交接](../workflow/handoff.md)。\n",
                encoding="utf-8",
            )

        default_skills = {
            "requirement-analysis": "需求分析与边界收敛",
            "feature-development": "契约设计与开发实施",
            "acceptance-testing": "独立对齐审查与对抗验收",
            "bug-fixing": "根因诊断与缺陷修复",
        }
        for skill, title in default_skills.items():
            p = pkg_dir / "skills" / skill / "SKILL.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            if skill == "feature-development" and custom_dev_skill is not None:
                p.write_text(custom_dev_skill, encoding="utf-8")
            else:
                (pkg_dir / "skills" / skill / "references").mkdir(parents=True, exist_ok=True)
                (pkg_dir / "skills" / skill / "references/guide.md").write_text("# Guide\n", encoding="utf-8")
                p.write_text(
                    f"---\nname: {skill}\ndescription: Desc for {skill}\n---\n\n"
                    f"# {title}\n\n"
                    f"遵循 [路径选择](../../workflow/routing.md#路径选择) 与 [阶段指南](references/guide.md)。\n",
                    encoding="utf-8",
                )

        setup_src = ROOT / "skills/setup-requirement-workflow"
        setup_dst = pkg_dir / "skills/setup-requirement-workflow"
        (setup_dst / "assets/templates").mkdir(parents=True, exist_ok=True)
        (setup_dst / "scripts").mkdir(parents=True, exist_ok=True)
        (setup_dst / "SKILL.md").write_text("---\nname: setup\ndescription: setup\n---\n\n# Setup\n", encoding="utf-8")
        for tpl in (setup_src / "assets/templates").iterdir():
            if tpl.is_file():
                (setup_dst / "assets/templates" / tpl.name).write_bytes(tpl.read_bytes())
        (setup_dst / "scripts/codex_registry.py").write_bytes((setup_src / "scripts/codex_registry.py").read_bytes())
        (setup_dst / "scripts/install_helper.py").write_bytes(HELPER.read_bytes())

        (pkg_dir / "workflow").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "workflow/routing.md").write_text("# 路由\n\n## 路径选择\n", encoding="utf-8")
        (pkg_dir / "workflow/execution-contract.md").write_text("# 执行约定\n\n## 人工确认\n", encoding="utf-8")
        (pkg_dir / "workflow/handoff.md").write_text("# 最小交接\n", encoding="utf-8")
        (pkg_dir / "templates").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "templates/task.md").write_text("# Task\n", encoding="utf-8")
        (pkg_dir / "templates/spec.md").write_text("# Spec\n", encoding="utf-8")
        return pkg_dir

    def _init_git(self, repo: Path) -> str:
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    # 1. AC-01: Stack-based 2n-indent YAML parser
    def test_parse_simple_yaml_nested_and_strict_rejections(self):
        wf_yaml = (
            "schema_version: 1 # top comment\n"
            "workspace:\n"
            "  features_dir: agent-features\n"
            "documents:\n"
            "  provider: local\n"
            "  feishu:\n"
            '    parent_node_url: "https://feishu.cn/wiki/node # keep hash"\n'
            "    write_enabled: false\n"
            "    nested_extra:\n"
            "      retry_budget: -2\n"
            "      optional_tag: ~\n"
            "approval:\n"
            "  channel: coordinator\n"
        )
        parsed = self.ih.parse_simple_yaml(wf_yaml)
        self.assertEqual(parsed["schema_version"], 1)
        self.assertEqual(parsed["workspace"]["features_dir"], "agent-features")
        self.assertEqual(
            parsed["documents"]["feishu"]["parent_node_url"],
            "https://feishu.cn/wiki/node # keep hash",
        )
        self.assertIs(parsed["documents"]["feishu"]["write_enabled"], False)
        self.assertEqual(parsed["documents"]["feishu"]["nested_extra"]["retry_budget"], -2)
        self.assertIsNone(parsed["documents"]["feishu"]["nested_extra"]["optional_tag"])
        self.assertEqual(parsed["approval"]["channel"], "coordinator")

        bad_cases = [
            ("tab_indent", "a:\n\tb: 1\n"),
            ("odd_indent_1", "a:\n b: 1\n"),
            ("odd_indent_3", "a:\n   b: 1\n"),
            ("skip_indent_0_to_4", "a:\n    b: 1\n"),
            ("skip_indent_2_to_6", "a:\n  b:\n      c: 1\n"),
            ("empty_parent_not_indented", "a:\nb: 1\n"),
            ("empty_nested_parent_not_indented", "a:\n  b:\nc: 1\n"),
            ("empty_parent_at_eof", "a:\n  b:\n"),
            ("child_under_scalar_int", "a: 1\n  b: 2\n"),
            ("child_under_scalar_null", "a: null\n  b: 2\n"),
            ("dup_root_key", "a: 1\na: 2\n"),
            ("dup_level1_key", "a:\n  b: 1\n  b: 2\n"),
            ("dup_level2_key", "a:\n  b:\n    c: 1\n    c: 2\n"),
            ("yaml_anchor", "a: &anc 1\n"),
            ("yaml_alias", "a: *anc\n"),
            ("missing_colon", "just_a_word\n"),
            ("unclosed_quote", 'a: "unclosed\n'),
        ]
        for label, bad_text in bad_cases:
            with self.subTest(case=label):
                with self.assertRaises(self.ih.HelperError):
                    self.ih.parse_simple_yaml(bad_text)

    # 2. AC-01: Protocol 5 pure package boundary, empty directory rejection, dirty tree & symlink rejection
    def test_protocol5_pure_package_digest_and_rejections(self):
        self.assertEqual(self.ih.PROTOCOL_VERSION, 5)
        self.assertEqual(self.ih.ROOT_FILES, {"framework.yaml", "LICENSE"})
        self.assertEqual(self.ih.ROOT_DIRS, {"agents", "skills", "workflow", "templates"})

        pkg = self._make_protocol5_package(self.scratch / "pure_pkg")
        res = run_helper("digest", "--package-root", str(pkg))
        self.assertEqual(res.returncode, 0, res.stderr)
        pkg_digest = json.loads(res.stdout)

        res_match = run_helper("digest", "--package-root", str(pkg), "--expected-sha256", pkg_digest["sha256"])
        self.assertEqual(res_match.returncode, 0)
        self.assertTrue(json.loads(res_match.stdout)["matches_expected"])

        res_mismatch = run_helper("digest", "--package-root", str(pkg), "--expected-sha256", "0" * 64)
        self.assertEqual(res_mismatch.returncode, 1)
        self.assertFalse(json.loads(res_mismatch.stdout)["matches_expected"])

        # Missing LICENSE must be rejected
        (pkg / "LICENSE").unlink()
        self.assertEqual(run_helper("digest", "--package-root", str(pkg)).returncode, 2)
        (pkg / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        # Root AGENTS.md / README.md / workflow.yaml inside --package-root must be rejected as extra
        for forbidden_root in ("AGENTS.md", "README.md", "workflow.yaml"):
            (pkg / forbidden_root).write_text("extra\n", encoding="utf-8")
            self.assertEqual(run_helper("digest", "--package-root", str(pkg)).returncode, 2)
            (pkg / forbidden_root).unlink()

        # Dirty bytecode / __pycache__ / .DS_Store rejected
        pyc = pkg / "skills/setup-requirement-workflow/scripts/junk.pyc"
        pyc.write_bytes(b"pyc")
        self.assertEqual(run_helper("digest", "--package-root", str(pkg)).returncode, 2)
        pyc.unlink()
        pycache = pkg / "skills/__pycache__"
        pycache.mkdir()
        self.assertEqual(run_helper("digest", "--source-root", str(pkg)).returncode, 2)
        pycache.rmdir()

        # Empty directory inside package must be rejected with empty_package_directory_present
        empty_sub = pkg / "workflow/empty_dir"
        empty_sub.mkdir()
        res_empty_pkg = run_helper("digest", "--package-root", str(pkg))
        self.assertEqual(res_empty_pkg.returncode, 2)
        self.assertIn("empty_package_directory_present", res_empty_pkg.stderr)
        res_empty_src = run_helper("digest", "--source-root", str(pkg), "--include-working-tree")
        self.assertEqual(res_empty_src.returncode, 2)
        self.assertIn("empty_package_directory_present", res_empty_src.stderr)
        empty_sub.rmdir()

        # In --source-root, root AGENTS.md / README.md / workflow.yaml and skills/system/** are excluded from digest!
        src_repo = self._make_protocol5_package(self.scratch / "src_repo", with_repo_extras=True)
        (src_repo / "skills/system/injected/SKILL.md").parent.mkdir(parents=True, exist_ok=True)
        (src_repo / "skills/system/injected/SKILL.md").write_text("# injected\n", encoding="utf-8")
        res_src1 = run_helper("digest", "--source-root", str(src_repo), "--include-working-tree")
        self.assertEqual(res_src1.returncode, 0, res_src1.stderr)
        d1 = json.loads(res_src1.stdout)
        self.assertEqual(d1["sha256"], pkg_digest["sha256"])
        self.assertEqual(d1["protocol_version"], 5)

        # Mutating root AGENTS.md / README.md / workflow.yaml must NOT change package sha256!
        (src_repo / "AGENTS.md").write_text("# Changed Agents Dramatically\n", encoding="utf-8")
        (src_repo / "README.md").write_text("# Changed Readme\n", encoding="utf-8")
        (src_repo / "workflow.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        res_src2 = run_helper("digest", "--source-root", str(src_repo), "--include-working-tree")
        self.assertEqual(res_src2.returncode, 0, res_src2.stderr)
        self.assertEqual(json.loads(res_src2.stdout)["sha256"], pkg_digest["sha256"])

        # Protocol 4 package must be rejected with invalid_protocol_version in digest & install
        p4_pkg = self._make_protocol5_package(self.scratch / "p4_pkg", protocol_version=4)
        res_p4 = run_helper("digest", "--source-root", str(p4_pkg))
        self.assertEqual(res_p4.returncode, 2)
        self.assertIn("invalid_protocol_version", res_p4.stderr)
        p4_target = self.scratch / "p4_target"
        p4_target.mkdir()
        res_p4_inst = run_helper(
            "install", "--source-root", str(p4_pkg), "--target-root", str(p4_target),
            "--hosts", "agents-md", "--source-kind", "manual", "--source-location", "wf@2.0.0",
        )
        self.assertEqual(res_p4_inst.returncode, 2)
        self.assertIn("invalid_protocol_version", res_p4_inst.stderr)

        # Git dirty-tree & symlink checks when include_working_tree=False:
        self._init_git(src_repo)
        (src_repo / "workflow/untracked_draft.md").write_text("# draft\n", encoding="utf-8")
        res_git_clean = run_helper("digest", "--source-root", str(src_repo))
        self.assertEqual(res_git_clean.returncode, 0, res_git_clean.stderr)
        self.assertEqual(json.loads(res_git_clean.stdout)["sha256"], pkg_digest["sha256"])

        ds_store = src_repo / "workflow/.DS_Store"
        ds_store.write_bytes(b"junk")
        self.assertEqual(run_helper("digest", "--source-root", str(src_repo)).returncode, 2)
        ds_store.unlink()

        # Top-level and nested symlinks inside git package must be rejected
        ext_agents = self.scratch / "ext_agents"
        shutil.move(str(src_repo / "agents"), str(ext_agents))
        (src_repo / "agents").symlink_to(ext_agents, target_is_directory=True)
        self.assertEqual(run_helper("digest", "--source-root", str(src_repo)).returncode, 2)
        (src_repo / "agents").unlink()
        shutil.move(str(ext_agents), str(src_repo / "agents"))

        ext_bug = self.scratch / "ext_bug"
        shutil.move(str(src_repo / "skills/bug-fixing"), str(ext_bug))
        (src_repo / "skills/bug-fixing").symlink_to(ext_bug, target_is_directory=True)
        self.assertEqual(run_helper("digest", "--source-root", str(src_repo)).returncode, 2)
        (src_repo / "skills/bug-fixing").unlink()
        shutil.move(str(ext_bug), str(src_repo / "skills/bug-fixing"))

    # 3. AC-02: source.kind == self single-round bootstrap, untracked package file parity & restore
    def test_self_bootstrap_single_round_and_restore_parity(self):
        repo = self._make_protocol5_package(self.scratch / "self_repo", with_repo_extras=True)
        self._init_git(repo)

        # Add a brand-new untracked file inside workflow/ BEFORE git add
        (repo / "workflow/agents-md-guide.md").write_text("# Agents-MD Guide\n", encoding="utf-8")

        res_dig = run_helper("digest", "--source-root", str(repo), "--include-working-tree")
        self.assertEqual(res_dig.returncode, 0, res_dig.stderr)
        expected_sha = json.loads(res_dig.stdout)["sha256"]

        # Invalid self invocations must fail
        other_target = self.scratch / "other_target"
        other_target.mkdir()
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(repo), "--target-root", str(other_target),
                "--hosts", "agents-md", "--source-kind", "self", "--source-location", ".",
            ).returncode,
            2,
        )
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(repo), "--target-root", str(repo),
                "--hosts", "agents-md", "--source-kind", "self", "--source-location", "./sub",
            ).returncode,
            2,
        )
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(repo), "--target-root", str(repo),
                "--hosts", "agents-md", "--source-kind", "self", "--source-location", ".",
                "--source-revision", "badrev",
            ).returncode,
            2,
        )

        # Single-round self bootstrap on repo itself (with untracked workflow/agents-md-guide.md!)
        res_inst = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(repo),
            "--hosts", "codex,opencode",
            "--source-kind", "self",
            "--source-location", ".",
        )
        self.assertEqual(res_inst.returncode, 0, res_inst.stderr)
        inst_out = json.loads(res_inst.stdout)
        self.assertEqual(inst_out["package_sha256"], expected_sha)

        # Second run is immediately idempotent (zero updated_files — single-round convergence!)
        res_inst2 = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(repo),
            "--hosts", "codex,opencode",
            "--source-kind", "self",
            "--source-location", ".",
        )
        self.assertEqual(res_inst2.returncode, 0, res_inst2.stderr)
        self.assertEqual(json.loads(res_inst2.stdout)["updated_files"], [])

        lock_parsed = self.ih.parse_simple_yaml((repo / "workflow.lock.yaml").read_text(encoding="utf-8"))
        self.assertEqual(lock_parsed["package"]["protocol_version"], 5)
        self.assertEqual(lock_parsed["package"]["sha256"], expected_sha)
        self.assertEqual(lock_parsed["source"], {"kind": "self", "location": ".", "revision": "self"})

        # Commit single atomic commit, remove cache, and verify restore works with identical sha256!
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "v3.0.0 single commit"], cwd=repo, check=True)
        shutil.rmtree(repo / ".agents/requirement-workflow-cache")

        res_rest = run_helper("restore", "--source-root", str(repo), "--target-root", str(repo))
        self.assertEqual(res_rest.returncode, 0, res_rest.stderr)
        rest_out = json.loads(res_rest.stdout)
        self.assertEqual(rest_out["package_sha256"], expected_sha)
        self.assertTrue(rest_out["restored"])
        self.assertTrue((repo / ".agents/requirement-workflow-cache" / expected_sha / "workflow/agents-md-guide.md").is_file())

        # Restore with self lock must reject mismatched source_root != target_root or tampered lock
        other_clone = self._make_protocol5_package(self.scratch / "other_clone")
        self.assertEqual(
            run_helper("restore", "--source-root", str(other_clone), "--target-root", str(repo)).returncode,
            2,
        )

    # 4. AC-02: Cache auto-pruning on --upgrade, malformed block markers, and concurrent rename idempotency
    def test_cache_pruning_on_upgrade_and_concurrent_rename_idempotency(self):
        pkg1 = self._make_protocol5_package(self.scratch / "pkg_v1", version="3.0.0")
        pkg2 = self._make_protocol5_package(self.scratch / "pkg_v2", version="3.1.0")
        (pkg2 / "workflow/routing.md").write_text("# 路由 v3.1\n\n## 路径选择\n", encoding="utf-8")

        target = self.scratch / "consumer_up"
        target.mkdir()
        # Half-broken AGENTS.md marker must be rejected
        (target / "AGENTS.md").write_text("<!-- requirement-workflow:begin -->\nbroken\n", encoding="utf-8")
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(pkg1), "--target-root", str(target),
                "--hosts", "agents-md", "--source-kind", "manual", "--source-location", "wf@3.0.0",
            ).returncode,
            2,
        )
        (target / "AGENTS.md").write_text("# Clean Project\r\nKeep CRLF!\r\n", encoding="utf-8")

        # Simulate legacy 6-line .gitignore managed block to prove upgrade cleans retired paths
        (target / ".gitignore").write_text(
            "# requirement-workflow-local:begin\n"
            "/.agents/requirement-workflow-cache/\n"
            "/.agents/requirement-workflow.local.json\n"
            "/.agents/requirement-workflow.pending.json\n"
            ".workflow/\n"
            "# requirement-workflow-local:end\n",
            encoding="utf-8",
        )

        # Initial install fails without --upgrade because .gitignore block differs from Protocol 5 template
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(pkg1), "--target-root", str(target),
                "--hosts", "opencode", "--source-kind", "manual", "--source-location", "wf@3.0.0",
            ).returncode,
            2,
        )
        res1 = run_helper(
            "install", "--source-root", str(pkg1), "--target-root", str(target),
            "--hosts", "opencode", "--source-kind", "manual", "--source-location", "wf@3.0.0", "--upgrade",
        )
        self.assertEqual(res1.returncode, 0, res1.stderr)
        sha1 = json.loads(res1.stdout)["package_sha256"]
        self.assertTrue((target / "AGENTS.md").read_bytes().startswith(b"# Clean Project\r\nKeep CRLF!\r\n"))

        gi_text = (target / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn(".local.json", gi_text)
        self.assertNotIn(".pending.json", gi_text)
        self.assertNotIn(".workflow/", gi_text)
        self.assertIn("/.agents/requirement-workflow-cache/", gi_text)

        cache_parent = target / ".agents/requirement-workflow-cache"
        stale_hex = cache_parent / ("a" * 64)
        stale_hex.mkdir(parents=True)
        (stale_hex / "dummy.txt").write_text("old\n", encoding="utf-8")
        non_hex = cache_parent / "README-note"
        non_hex.write_text("keep\n", encoding="utf-8")

        # Upgrade without --upgrade flag must fail with lock_mismatch_use_upgrade
        self.assertEqual(
            run_helper(
                "install", "--source-root", str(pkg2), "--target-root", str(target),
                "--hosts", "opencode", "--source-kind", "manual", "--source-location", "wf@3.1.0",
            ).returncode,
            2,
        )

        res2 = run_helper(
            "install", "--source-root", str(pkg2), "--target-root", str(target),
            "--hosts", "opencode", "--source-kind", "manual", "--source-location", "wf@3.1.0", "--upgrade",
        )
        self.assertEqual(res2.returncode, 0, res2.stderr)
        sha2 = json.loads(res2.stdout)["package_sha256"]
        self.assertNotEqual(sha1, sha2)
        self.assertTrue((cache_parent / sha2).is_dir())
        self.assertFalse((cache_parent / sha1).exists(), "previous sha1 cache must be pruned on --upgrade")
        self.assertFalse(stale_hex.exists(), "other 64-hex cache dirs must be pruned on --upgrade")
        self.assertTrue(non_hex.is_file(), "non-64-hex entries must not be deleted")

        # Concurrent rename race simulation in _populate_cache
        race_target = self.scratch / "race_target"
        race_target.mkdir()
        staged_dir = self.scratch / "staged_clean"
        staged_info = self.ih.stage_clean_package(pkg1, staged_dir)
        exp_sha = staged_info["sha256"]
        race_cache_dir = race_target / ".agents/requirement-workflow-cache" / exp_sha

        def win_race_valid(self_path: Path, dst_path: Path):
            shutil.copytree(staged_dir, dst_path)
            raise OSError(errno.ENOTEMPTY, "Directory not empty")

        with mock.patch.object(Path, "rename", win_race_valid):
            created = self.ih._populate_cache(staged_dir, race_target, exp_sha)
        self.assertFalse(created)
        self.assertTrue(race_cache_dir.is_dir())
        leftovers = [p.name for p in race_cache_dir.parent.iterdir() if p.name.startswith(".tmp-")]
        self.assertEqual(leftovers, [])

        # Corrupt concurrent winner must raise HelperError("framework_integrity_mismatch")
        shutil.rmtree(race_cache_dir)

        def win_race_corrupt(self_path: Path, dst_path: Path):
            shutil.copytree(staged_dir, dst_path)
            (dst_path / "LICENSE").write_text("TAMPERED\n", encoding="utf-8")
            raise OSError(errno.EEXIST, "File exists")

        with mock.patch.object(Path, "rename", win_race_corrupt):
            with self.assertRaisesRegex(self.ih.HelperError, "framework_integrity_mismatch"):
                self.ih._populate_cache(staged_dir, race_target, exp_sha)

    # 5. AC-04: Host normalization (agents-md & zed alias) + manual lock / tamper restore gates
    def test_host_normalization_and_agents_md_host(self):
        self.assertEqual(self.ih.HOSTS, ("codex", "claude-code", "opencode", "agents-md"))
        self.assertEqual(self.ih.HOST_ALIASES, {"zed": "agents-md"})
        self.assertEqual(self.ih.normalize_hosts("zed"), ["agents-md"])
        self.assertEqual(
            self.ih.normalize_hosts("codex, zed, opencode, agents-md"),
            ["codex", "agents-md", "opencode"],
        )
        for bad in ("", "  ,  ", "unknown-ide", "codex,invalid"):
            with self.assertRaisesRegex(self.ih.HelperError, "unsupported_or_empty_hosts"):
                self.ih.normalize_hosts(bad)

        repo = self._make_protocol5_package(self.scratch / "git_pkg")
        rev = self._init_git(repo)
        target = self.scratch / "agents_md_consumer"
        target.mkdir()

        res = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(target),
            "--hosts", "zed",
            "--source-kind", "git",
            "--source-location", "https://example.com/wf.git",
            "--source-revision", rev,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        self.assertEqual(out["installed_hosts"], ["agents-md"])
        self.assertTrue((target / "AGENTS.md").is_file())
        self.assertTrue((target / ".gitignore").is_file())
        self.assertTrue((target / "workflow.yaml").is_file())
        self.assertTrue((target / "workflow.lock.yaml").is_file())
        for absent in (".codex", ".claude", ".opencode", ".zed", "CLAUDE.md"):
            self.assertFalse((target / absent).exists(), f"{absent} should not exist for agents-md")

        # Restore works cleanly on agents-md-only consumer
        shutil.rmtree(target / ".agents/requirement-workflow-cache")
        res_rest = run_helper("restore", "--source-root", str(repo), "--target-root", str(target))
        self.assertEqual(res_rest.returncode, 0, res_rest.stderr)
        self.assertTrue((target / out["cache_dir"]).is_dir())

        # Manual lock, tampered lock version, tampered .gitignore, and tampered AGENTS.md must block restore
        orig_lock = (target / "workflow.lock.yaml").read_text(encoding="utf-8")
        (target / "workflow.lock.yaml").write_text(
            orig_lock.replace("kind: git", "kind: manual").replace(f"revision: {rev}", "revision: null"),
            encoding="utf-8",
        )
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / "workflow.lock.yaml").write_text(orig_lock.replace("version: 3.0.0", "version: 9.9.9"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / "workflow.lock.yaml").write_text(orig_lock, encoding="utf-8")

        orig_gi = (target / ".gitignore").read_text(encoding="utf-8")
        (target / ".gitignore").write_text(orig_gi.replace("requirement-workflow-cache/", "tampered/"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / ".gitignore").write_text(orig_gi, encoding="utf-8")

        orig_ag = (target / "AGENTS.md").read_text(encoding="utf-8")
        (target / "AGENTS.md").write_text(orig_ag.replace("## 需求协作入口", "## 被篡改入口"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / "AGENTS.md").write_text(orig_ag, encoding="utf-8")

    # 6. AC-03: Precompiled subagent roles, header stripping, link rewriting, TOML lossless roundtrip & byte-exact restore
    def test_precompiled_subagent_roles_link_rewriting_and_toml_roundtrip(self):
        # Unit checks on _strip_doc_header and _rewrite_pkg_links
        doc_sample = (
            "---\nname: sample\ndescription: test\n---\n\n"
            "# Top Heading To Strip\n\n"
            "Intro with [Guide](references/guide.md#节一), [`CodeSym`](../../workflow/execution-contract.md#人工确认), "
            "[External](https://example.com/a.md), [Anchor](#local-sec), [Tpl]({{tpl}}/a.md), [Angle](<path>/b.md), "
            "and inline `[SkipInline](../nope.md)` plus `` `[SkipDouble](../nope2.md)` ``.\n\n"
            "---\n\n"
            "## Keep Level 2\n\n"
            "<!-- [SkipComment](../comment.md) -->\n\n"
            "```markdown\n# Keep comment in fence\n[SkipFence](../fence.md)\n```\n\n"
            "~~~text\n[SkipTilde](../tilde.md)\n~~~\n"
        )
        stripped = self.ih._strip_doc_header(doc_sample)
        self.assertNotIn("name: sample", stripped)
        self.assertNotIn("# Top Heading To Strip", stripped)
        self.assertIn("## Keep Level 2", stripped)
        self.assertIn("\n---\n", stripped)
        self.assertIn("# Keep comment in fence", stripped)

        cache_rel = ".agents/requirement-workflow-cache/" + ("b" * 64)
        rewritten = self.ih._rewrite_pkg_links(stripped, "skills/feature-development", cache_rel)
        self.assertIn(f"]({cache_rel}/skills/feature-development/references/guide.md#节一)", rewritten)
        self.assertIn(f"[`CodeSym`]({cache_rel}/workflow/execution-contract.md#人工确认)", rewritten)
        self.assertIn("](https://example.com/a.md)", rewritten)
        self.assertIn("](#local-sec)", rewritten)
        self.assertIn("]({{tpl}}/a.md)", rewritten)
        self.assertIn("](<path>/b.md)", rewritten)
        self.assertIn("`[SkipInline](../nope.md)`", rewritten)
        self.assertIn("`` `[SkipDouble](../nope2.md)` ``", rewritten)
        self.assertIn("<!-- [SkipComment](../comment.md) -->", rewritten)
        self.assertIn("[SkipFence](../fence.md)", rewritten)
        self.assertIn("[SkipTilde](../tilde.md)", rewritten)

        for escape_bad in ("[Escape](../../../etc/passwd)", "[Abs](/etc/passwd)"):
            with self.assertRaises(self.ih.HelperError):
                self.ih._rewrite_pkg_links(escape_bad, "skills/feature-development", cache_rel)

        # End-to-end install & TOML roundtrip with complex escaping edge cases
        tricky_skill = (
            "---\nname: feature-development\ndescription: Tricky TOML & Markdown payload\n---\n\n"
            "# 契约设计与开发实施\n\n"
            "遵循 [路径选择](../../workflow/routing.md#路径选择) 与 [开发指南](references/dev.md#锚点)。\n"
            "校验无未替换 `{{placeholder}}`，正则示例 `\\A---\\r?\\n`、`C:\\\\temp\\\\x`、"
            '三引号 `"""`、四引号 `""""`、五引号 `"""""` 及控制符 \x07\x08\x0c\x1b\x7f。\n\n'
            "```python\n"
            'raw = """keep [unrewritten](../do-not-touch.md)"""\n'
            "```\n"
        )
        repo = self._make_protocol5_package(self.scratch / "tricky_repo", custom_dev_skill=tricky_skill)
        (repo / "skills/feature-development/references").mkdir(parents=True, exist_ok=True)
        (repo / "skills/feature-development/references/dev.md").write_text("# Dev\n\n## 锚点\n", encoding="utf-8")
        rev = self._init_git(repo)

        target = self.scratch / "full_consumer"
        target.mkdir()
        user_codex = b'# user comment\r\n[agents.custom_helper]\r\ndescription = "mine"\r\n'
        (target / ".codex").mkdir()
        (target / ".codex/config.toml").write_bytes(user_codex)

        res = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(target),
            "--hosts", "codex,claude-code,opencode,zed",
            "--source-kind", "git",
            "--source-location", "https://example.com/repo.git",
            "--source-revision", rev,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        sha = out["package_sha256"]
        cache_dir = f".agents/requirement-workflow-cache/{sha}"
        self.assertTrue((target / ".codex/config.toml").read_bytes().startswith(user_codex))

        opencode_dev = (target / ".opencode/agents/requirement-development.md").read_text(encoding="utf-8")
        _, md_body = opencode_dev.removeprefix("---\n").split("---\n\n", 1)

        claude_dev = (target / ".claude/agents/requirement-development.md").read_text(encoding="utf-8")
        _, claude_body = claude_dev.removeprefix("---\n").split("---\n\n", 1)
        self.assertEqual(claude_body, md_body)

        codex_dev_bytes = (target / ".codex/agents/requirement_development.toml").read_bytes()
        parsed_toml = parse_toml_via_registry(codex_dev_bytes)
        self.assertEqual(parsed_toml["name"], "requirement_development")
        self.assertEqual(parsed_toml["developer_instructions"], md_body + "\n")

        # Also test subprocess fallback path when reg.tomllib is None
        fake_reg = mock.MagicMock()
        fake_reg.tomllib = None
        with mock.patch.object(self.ih, "_load_codex_reg", return_value=(CODEX_REG, fake_reg)):
            roles_via_subproc = self.ih._build_roles(
                target / cache_dir,
                ["codex"],
                sha,
            )
        self.assertEqual(roles_via_subproc[".codex/agents/requirement_development.toml"], codex_dev_bytes)

        # Verify precompiled body invariants and ceremonial absence
        for forbidden in ("你是需求协作框架", "当前宿主原生名称为", "协议 4", "协议 5", "name: feature-development", "# 契约设计与开发实施"):
            self.assertNotIn(forbidden, md_body)
        for required in (
            cache_dir,
            "workflow.lock.yaml",
            "framework_cache_missing",
            "只读回读",
            "Spec Gate",
            "2～3 次",
            "未知外部操作先查原调用",
            f"]({cache_dir}/workflow/routing.md#路径选择)",
            f"]({cache_dir}/skills/feature-development/references/dev.md#锚点)",
            "[unrewritten](../do-not-touch.md)",
            "{{placeholder}}",
            '"""',
            '""""',
            '"""""',
            r"\A---\r?\n",
        ):
            self.assertIn(required, md_body)

        # Restore must enforce byte-exact precompiled role match (1-byte tamper blocked!)
        codex_role_path = target / ".codex/agents/requirement_development.toml"
        orig_bytes = codex_role_path.read_bytes()
        codex_role_path.write_bytes(orig_bytes + b"\n")
        res_tamper = run_helper("restore", "--source-root", str(repo), "--target-root", str(target))
        self.assertEqual(res_tamper.returncode, 2)
        self.assertIn("adapter_modified:.codex/agents/requirement_development.toml", res_tamper.stderr)
        codex_role_path.write_bytes(orig_bytes)

        # Restore passes once untampered
        shutil.rmtree(target / ".agents/requirement-workflow-cache")
        res_ok = run_helper("restore", "--source-root", str(repo), "--target-root", str(target))
        self.assertEqual(res_ok.returncode, 0, res_ok.stderr)


if __name__ == "__main__":
    unittest.main()
