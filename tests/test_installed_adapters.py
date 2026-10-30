"""Regression checks for the source repository's generated host adapters."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "skills/setup-requirement-workflow/assets/templates"
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
    def test_managed_entry_matches_template(self):
        actual = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        begin = "<!-- requirement-workflow:begin -->"
        end = "<!-- requirement-workflow:end -->"
        block = actual[actual.index(begin):actual.index(end) + len(end)] + "\n"
        self.assertEqual(block, (TEMPLATES / "project-entry-light.md").read_text(encoding="utf-8"))

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
                expected = render((TEMPLATES / f"native-{host}.{extension}").read_text(), values)
                path = ROOT / f".{host}/agents/{name}.{extension}"
                self.assertEqual(path.read_text(encoding="utf-8"), expected, path)


if __name__ == "__main__":
    unittest.main()
