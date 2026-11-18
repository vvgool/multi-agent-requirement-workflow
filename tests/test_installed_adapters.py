"""Regression checks for the source repository's generated host adapters."""
import subprocess
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "skills/setup-requirement-workflow/assets/templates"
ZED_ADAPTER = ROOT / "skills/setup-requirement-workflow/references/zed-adapter.md"
ROLES = {
    "product": ("product-agent", "requirement-analysis", "澄清需求并输出验收标准"),
    "development": ("development-agent", "feature-development", "实现已批准需求并完成自验"),
    "testing": ("testing-agent", "acceptance-testing", "独立验收当前开发基线并报告缺陷"),
    "bug": ("bug-agent", "bug-fixing", "诊断并修复缺陷并完成自验"),
}


def render(template, values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


class InstalledAdapterTests(unittest.TestCase):
    def _locked_entry_template(self):
        lock = yaml.safe_load((ROOT / "workflow.lock.yaml").read_text(encoding="utf-8"))
        package = lock["package"]
        package_sha = package["sha256"]
        cached = (
            ROOT
            / ".agents"
            / "requirement-workflow-cache"
            / package_sha
            / "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
        )
        if cached.is_file():
            return cached.read_text(encoding="utf-8"), "locked cache"

        revision = lock["source"].get("revision")
        if lock["source"].get("kind") == "git" and revision:
            try:
                fw_raw = subprocess.check_output(
                    ["git", "show", f"{revision}:framework.yaml"],
                    cwd=ROOT,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                rev_fw = yaml.safe_load(fw_raw) or {}
                if (
                    str(rev_fw.get("version")) == str(package.get("version"))
                    and rev_fw.get("protocol_version") == package.get("protocol_version")
                ):
                    path = "skills/setup-requirement-workflow/assets/templates/project-entry-light.md"
                    content = subprocess.check_output(
                        ["git", "show", f"{revision}:{path}"],
                        cwd=ROOT,
                        stderr=subprocess.DEVNULL,
                        text=True,
                    )
                    return content, f"locked Git revision {revision}"
            except (OSError, subprocess.CalledProcessError):
                pass

        return None, "locked package cache and matching Git revision are unavailable"

    def test_managed_entry_matches_template(self):
        actual = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        begin = "<!-- requirement-workflow:begin -->"
        end = "<!-- requirement-workflow:end -->"
        block = actual[actual.index(begin):actual.index(end) + len(end)] + "\n"
        expected, source = self._locked_entry_template()
        if expected is None:
            self.skipTest(source)
        self.assertEqual(block, expected)

    def test_zed_rules_adapter_matches_contract(self):
        adapter = ZED_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("规则型宿主", adapter)
        self.assertIn("AGENTS.md", adapter)
        self.assertIn("不生成 Zed 角色文件", adapter)
        self.assertIn("native_role_probes", adapter)
        self.assertIn("not_applicable", adapter)
        self.assertIn(".zed/agents", adapter)

    def test_codex_and_opencode_roles_match_templates(self):
        body_template = (TEMPLATES / "role-body.md").read_text(encoding="utf-8")
        for logical, (role, skill, description) in ROLES.items():
            for host, separator, extension in (("codex", "_", "toml"), ("opencode", "-", "md")):
                name = "requirement" + separator + logical
                values = {
                    "native_name": name,
                    "role": role,
                    "description": description,
                    "role_file": f"agents/{role}.md",
                    "skill_file": f"skills/{skill}/SKILL.md",
                }
                values["role_body"] = render(body_template, values)
                expected = render(
                    (TEMPLATES / f"native-{host}.{extension}").read_text(encoding="utf-8"), values
                )
                path = ROOT / f".{host}/agents/{name}.{extension}"
                self.assertEqual(path.read_text(encoding="utf-8"), expected, path)


if __name__ == "__main__":
    unittest.main()
