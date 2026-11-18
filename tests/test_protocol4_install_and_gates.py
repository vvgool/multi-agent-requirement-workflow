"""TDD & regression tests for Protocol 4 install_helper.py and light-kernel gates."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from package_digest import digest as reference_digest  # noqa: E402

HELPER = ROOT / "skills/setup-requirement-workflow/scripts/install_helper.py"


def run_helper(*args, python_bin=sys.executable):
    return subprocess.run(
        [python_bin, "-B", str(HELPER), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


class InstallHelperProtocol4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.scratch = Path(os.path.realpath(self.tmp.name))

    def _make_minimal_package(self, pkg_dir: Path, version="1.0.0"):
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "framework.yaml").write_text(
            f'schema_version: 1\nname: multi-agent-requirement-workflow\nversion: "{version}"\nprotocol_version: 4\n',
            encoding="utf-8",
        )
        (pkg_dir / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (pkg_dir / "README.md").write_text("# Readme\n", encoding="utf-8")
        (pkg_dir / "workflow.yaml").write_text(
            'schema_version: 1\nworkspace:\n  features_dir: agent-features\ndocuments:\n  provider: local\n  feishu:\n    parent_node_url: null\n    write_enabled: false\napproval:\n  channel: coordinator\nissue_tracking:\n  binding: "optional"\n  sync: "milestones"\n',
            encoding="utf-8",
        )
        (pkg_dir / "LICENSE").write_text("MIT\n", encoding="utf-8")
        for role in ("coordinator", "product", "development", "testing", "bug"):
            p = pkg_dir / "agents" / f"{role}-agent.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {role}-agent\n", encoding="utf-8")
        for skill in ("requirement-analysis", "feature-development", "acceptance-testing", "bug-fixing"):
            p = pkg_dir / "skills" / skill / "SKILL.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {skill}\n", encoding="utf-8")
        setup_src = ROOT / "skills/setup-requirement-workflow"
        setup_dst = pkg_dir / "skills/setup-requirement-workflow"
        (setup_dst / "assets/templates").mkdir(parents=True, exist_ok=True)
        (setup_dst / "scripts").mkdir(parents=True, exist_ok=True)
        (setup_dst / "SKILL.md").write_text("# setup\n", encoding="utf-8")
        for tpl in (setup_src / "assets/templates").iterdir():
            if tpl.is_file():
                (setup_dst / "assets/templates" / tpl.name).write_bytes(tpl.read_bytes())
        (setup_dst / "scripts/codex_registry.py").write_bytes(
            (setup_src / "scripts/codex_registry.py").read_bytes()
        )
        if HELPER.is_file():
            (setup_dst / "scripts/install_helper.py").write_bytes(HELPER.read_bytes())
        (pkg_dir / "workflow").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "workflow/routing.md").write_text("# routing\n", encoding="utf-8")
        (pkg_dir / "templates").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "templates/task.md").write_text("# task\n", encoding="utf-8")
        return pkg_dir

    def test_digest_matches_reference_and_rejects_pyc_or_extra_files(self):
        pkg = self._make_minimal_package(self.scratch / "pkg")
        ref = reference_digest(pkg)

        res = run_helper("digest", "--package-root", str(pkg))
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data, ref)

        res_match = run_helper("digest", "--package-root", str(pkg), "--expected-sha256", ref["sha256"])
        self.assertEqual(res_match.returncode, 0, res_match.stderr)
        self.assertTrue(json.loads(res_match.stdout)["matches_expected"])

        res_mismatch = run_helper("digest", "--package-root", str(pkg), "--expected-sha256", "0" * 64)
        self.assertEqual(res_mismatch.returncode, 1)
        self.assertFalse(json.loads(res_mismatch.stdout)["matches_expected"])

        pyc = pkg / "skills/setup-requirement-workflow/scripts/junk.pyc"
        pyc.write_bytes(b"pyc")
        res_bad = run_helper("digest", "--package-root", str(pkg))
        self.assertEqual(res_bad.returncode, 2)
        pyc.unlink()

    def test_digest_source_root_and_directory_symlink_rejection(self):
        pkg = self._make_minimal_package(self.scratch / "src_pkg")
        ref = reference_digest(pkg)

        # --source-root returns rich metadata and matches --package-root sha256
        res_src = run_helper("digest", "--source-root", str(pkg), "--include-working-tree")
        self.assertEqual(res_src.returncode, 0, res_src.stderr)
        src_data = json.loads(res_src.stdout)
        self.assertEqual(src_data["sha256"], ref["sha256"])
        self.assertEqual(src_data["file_count"], ref["file_count"])
        self.assertEqual(src_data["version"], "1.0.0")
        self.assertEqual(src_data["protocol_version"], 4)
        self.assertGreater(src_data["total_bytes"], 0)

        # Dirty artifacts in --source-root must be rejected with exit code 2
        for bad in (
            pkg / "skills/setup-requirement-workflow/scripts/bad.pyc",
            pkg / "workflow/.DS_Store",
        ):
            bad.write_bytes(b"bad")
            self.assertEqual(run_helper("digest", "--source-root", str(pkg)).returncode, 2)
            bad.unlink()
        pycache = pkg / "skills/__pycache__"
        pycache.mkdir()
        self.assertEqual(run_helper("digest", "--source-root", str(pkg)).returncode, 2)
        pycache.rmdir()

        # Top-level directory symlink (agents -> external_agents) must be rejected in digest & install
        ext_agents = self.scratch / "ext_agents"
        shutil.move(str(pkg / "agents"), str(ext_agents))
        (pkg / "agents").symlink_to(ext_agents, target_is_directory=True)
        self.assertEqual(run_helper("digest", "--source-root", str(pkg)).returncode, 2)
        target = self.scratch / "sym_target"
        target.mkdir()
        res_inst_sym = run_helper(
            "install", "--source-root", str(pkg), "--target-root", str(target),
            "--hosts", "zed", "--source-kind", "manual", "--source-location", "pkg@1.0.0",
        )
        self.assertEqual(res_inst_sym.returncode, 2)

        # Intermediate directory symlink inside a Git repository must also be rejected
        git_pkg = self._make_minimal_package(self.scratch / "git_sym_pkg")
        subprocess.run(["git", "init", "-q"], cwd=git_pkg, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=git_pkg, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=git_pkg, check=True)
        subprocess.run(["git", "add", "."], cwd=git_pkg, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=git_pkg, check=True)
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_pkg, text=True).strip()
        ext_bug = self.scratch / "ext_bug_fixing"
        shutil.move(str(git_pkg / "skills/bug-fixing"), str(ext_bug))
        (git_pkg / "skills/bug-fixing").symlink_to(ext_bug, target_is_directory=True)
        res_git_sym = run_helper(
            "install", "--source-root", str(git_pkg), "--target-root", str(target),
            "--hosts", "zed", "--source-kind", "git",
            "--source-location", "https://example.com/repo.git", "--source-revision", rev,
        )
        self.assertEqual(res_git_sym.returncode, 2)

    def test_install_excludes_git_untracked_and_preserves_user_bytes_and_defaults_off(self):
        repo = self._make_minimal_package(self.scratch / "git_source")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

        untracked = repo / "skills/system/run-workflow/SKILL.md"
        untracked.parent.mkdir(parents=True, exist_ok=True)
        untracked.write_text("# host injected\n", encoding="utf-8")
        (repo / "workflow/.DS_Store").write_bytes(b"junk")

        target = self.scratch / "consumer"
        target.mkdir()
        user_agents = b"# My Project Rules\r\nKeep CRLF!\r\n"
        (target / "AGENTS.md").write_bytes(user_agents)
        user_codex = b'# user comment\r\n[agents.custom_helper]\r\ndescription = "mine"\r\n'
        (target / ".codex").mkdir()
        (target / ".codex/config.toml").write_bytes(user_codex)

        res = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(target),
            "--hosts", "codex,claude-code,opencode,zed",
            "--source-kind", "git",
            "--source-location", "https://github.com/vvgool/multi-agent-requirement-workflow.git",
            "--source-revision", rev,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        sha = out["package_sha256"]
        cache_dir = target / ".agents/requirement-workflow-cache" / sha
        self.assertTrue(cache_dir.is_dir())
        self.assertFalse((cache_dir / "skills/system").exists(), "untracked dir leaked into cache!")
        self.assertFalse((cache_dir / "workflow/.DS_Store").exists(), ".DS_Store leaked into cache!")

        wf_text = (target / "workflow.yaml").read_text(encoding="utf-8")
        self.assertIn('binding: "off"', wf_text)
        self.assertIn('sync: "off"', wf_text)

        self.assertTrue((target / "AGENTS.md").read_bytes().startswith(user_agents))
        self.assertTrue((target / ".codex/config.toml").read_bytes().startswith(user_codex))
        self.assertTrue((target / "CLAUDE.md").is_file())
        self.assertFalse((target / ".zed/agents").exists())
        self.assertEqual(len(list((target / ".codex/agents").glob("*.toml"))), 4)
        self.assertEqual(len(list((target / ".claude/agents").glob("*.md"))), 4)
        self.assertEqual(len(list((target / ".opencode/agents").glob("*.md"))), 4)

        res2 = run_helper(
            "install",
            "--source-root", str(repo),
            "--target-root", str(target),
            "--hosts", "codex,claude-code,opencode,zed",
            "--source-kind", "git",
            "--source-location", "https://github.com/vvgool/multi-agent-requirement-workflow.git",
            "--source-revision", rev,
        )
        self.assertEqual(res2.returncode, 0, res2.stderr)
        self.assertEqual(json.loads(res2.stdout)["updated_files"], [])

        shutil.rmtree(target / ".agents/requirement-workflow-cache")
        res_restore = run_helper("restore", "--source-root", str(repo), "--target-root", str(target))
        self.assertEqual(res_restore.returncode, 0, res_restore.stderr)
        self.assertTrue(cache_dir.is_dir())

        # Manual source in workflow.lock.yaml must block restore (both with revision and null revision)
        orig_lock = (target / "workflow.lock.yaml").read_text(encoding="utf-8")
        shutil.rmtree(target / ".agents/requirement-workflow-cache")
        (target / "workflow.lock.yaml").write_text(orig_lock.replace("kind: git", "kind: manual"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / "workflow.lock.yaml").write_text(
            orig_lock.replace("kind: git", "kind: manual").replace(f"revision: {rev}", "revision: null"),
            encoding="utf-8",
        )
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        # Tampered lock version must also block restore
        (target / "workflow.lock.yaml").write_text(orig_lock.replace("version: 1.0.0", "version: 9.9.9"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / "workflow.lock.yaml").write_text(orig_lock, encoding="utf-8")

        # Tampered .gitignore block must block restore
        orig_gi = (target / ".gitignore").read_text(encoding="utf-8")
        (target / ".gitignore").write_text(orig_gi.replace("requirement-workflow-cache/", "tampered/"), encoding="utf-8")
        self.assertEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 2)
        (target / ".gitignore").write_text(orig_gi, encoding="utf-8")

        # Tamper managed block in AGENTS.md -> restore must reject!
        tampered = (target / "AGENTS.md").read_text(encoding="utf-8").replace("## 需求协作入口", "## 被篡改入口")
        (target / "AGENTS.md").write_text(tampered, encoding="utf-8")
        self.assertNotEqual(run_helper("restore", "--source-root", str(repo), "--target-root", str(target)).returncode, 0)

    def test_malformed_block_markers_rejected_and_upgrade_supported(self):
        pkg1 = self._make_minimal_package(self.scratch / "pkg1", version="1.0.0")
        pkg2 = self._make_minimal_package(self.scratch / "pkg2", version="1.0.1")
        (pkg2 / "workflow/routing.md").write_text("# routing v1.0.1\n", encoding="utf-8")

        target = self.scratch / "proj"
        target.mkdir()
        (target / "AGENTS.md").write_text("<!-- requirement-workflow:begin -->\nbroken\n", encoding="utf-8")
        res_half = run_helper(
            "install", "--source-root", str(pkg1), "--target-root", str(target),
            "--hosts", "zed", "--source-kind", "manual", "--source-location", "multi-agent-requirement-workflow@1.0.0",
        )
        self.assertNotEqual(res_half.returncode, 0)

        (target / "AGENTS.md").write_text("# Clean Project\n", encoding="utf-8")
        res1 = run_helper(
            "install", "--source-root", str(pkg1), "--target-root", str(target),
            "--hosts", "opencode", "--source-kind", "manual", "--source-location", "multi-agent-requirement-workflow@1.0.0",
        )
        self.assertEqual(res1.returncode, 0, res1.stderr)

        res_no_up = run_helper(
            "install", "--source-root", str(pkg2), "--target-root", str(target),
            "--hosts", "opencode", "--source-kind", "manual", "--source-location", "multi-agent-requirement-workflow@1.0.1",
        )
        self.assertNotEqual(res_no_up.returncode, 0)

        res_up = run_helper(
            "install", "--source-root", str(pkg2), "--target-root", str(target),
            "--hosts", "opencode", "--source-kind", "manual", "--source-location", "multi-agent-requirement-workflow@1.0.1",
            "--upgrade",
        )
        self.assertEqual(res_up.returncode, 0, res_up.stderr)
        self.assertIn("version: 1.0.1", (target / "workflow.lock.yaml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
