"""Source-contract regression; these checks do not run a native agent."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('rule_loading', ROOT / 'scripts/verify-rule-loading.py')
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)


class RuleLoadingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / 'source'
        self.root.mkdir()
        for name in ['framework.yaml']:
            shutil.copyfile(ROOT / name, self.root / name)
        for name in ['agents', 'skills', 'workflow', 'templates']:
            shutil.copytree(ROOT / name, self.root / name)

    def test_current_source_does_not_need_a_size_baseline(self):
        result = RULES.check(self.root)
        self.assertEqual(result['framework']['protocol_version'], 3)
        self.assertIsNone(result['selected_rule_utf8_bytes']['before'])

    def test_equal_or_larger_rules_only_fail_when_reduction_is_requested(self):
        baseline = Path(self.scratch.name) / 'baseline'
        shutil.copytree(self.root, baseline)
        rules = self.root / 'skills/feature-development/SKILL.md'
        rules.write_text(rules.read_text() + '\n补充必要说明。\n')
        result = RULES.check(self.root, baseline)
        self.assertGreater(result['selected_rule_utf8_bytes']['after'], result['selected_rule_utf8_bytes']['before'])
        with self.assertRaisesRegex(AssertionError, 'rule_size_not_reduced'):
            RULES.check(self.root, baseline, require_smaller=True)

    def test_patch_version_is_read_from_metadata(self):
        path = self.root / 'framework.yaml'
        original = RULES.check(self.root)['framework']['version']
        self.assertNotEqual(original, '99.0.0')
        path.write_text(path.read_text().replace(f'"{original}"', '"99.0.0"'))
        self.assertEqual(RULES.check(self.root)['framework']['version'], '99.0.0')

    def test_unknown_or_mismatched_protocol_fails(self):
        path = self.root / 'framework.yaml'
        path.write_text(path.read_text().replace('protocol_version: 3', 'protocol_version: 99'))
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_missing_document_format_pointer_fails(self):
        path = self.root / 'skills/feature-development/SKILL.md'
        path.write_text(path.read_text().replace('../../workflow/documents.md', '../../workflow/absent.md'))
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_missing_stage_template_fails(self):
        (self.root / 'skills/feature-development/assets/templates/technical-plan.md').unlink()
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_missing_linked_design_method_is_detected(self):
        (self.root / 'skills/feature-development/references/design-and-decomposition.md').unlink()
        with self.assertRaisesRegex(AssertionError, 'linked_rule_missing'):
            RULES.check(self.root)

    def test_broken_link_in_shared_workflow_is_detected(self):
        path = self.root / 'workflow/routing.md'
        path.write_text(path.read_text() + '\n[必要设计方法](absent-design-method.md)\n')
        with self.assertRaisesRegex(AssertionError, 'linked_rule_missing'):
            RULES.check(self.root)

    def test_external_links_and_document_fragments_are_not_file_paths(self):
        path = self.root / 'workflow/routing.md'
        path.write_text(path.read_text() + '\n[外部](https://example.invalid/missing.md) [本页](#路径选择)\n')
        RULES.check(self.root)

    def test_second_progress_checklist_fails(self):
        path = self.root / 'skills/feature-development/assets/templates/implementation-plan.md'
        original = path.read_text()
        for checkbox in ['- [ ] 待办', '* [ ] 待办', '+ [ ] 待办',
                         '  - [ ] 嵌套待办', '1. [ ] 有序待办', '> - [x] 引用中的任务', '- [ ]']:
            with self.subTest(checkbox=checkbox):
                path.write_text(original + '\n' + checkbox + '\n')
                with self.assertRaises(AssertionError):
                    RULES.check(self.root)

    def test_lock_template_protocol_must_match_source(self):
        path = self.root / 'skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml'
        path.write_text(path.read_text().replace('protocol_version: 3', 'protocol_version: 2'))
        with self.assertRaises(AssertionError):
            RULES.check(self.root)

    def test_reduction_flag_needs_a_baseline(self):
        with self.assertRaisesRegex(AssertionError, 'size_baseline_required'):
            RULES.check(self.root, require_smaller=True)

    def test_incomplete_size_baseline_is_rejected(self):
        baseline = Path(self.scratch.name) / 'baseline'
        baseline.mkdir()
        with self.assertRaises(FileNotFoundError):
            RULES.check(self.root, baseline)

    def test_optimized_python_cannot_disable_the_checks(self):
        result = subprocess.run([sys.executable, '-O', str(ROOT / 'scripts/verify-rule-loading.py'),
                                 '--source-root', str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('assertions required', result.stderr)


if __name__ == '__main__':
    unittest.main()
