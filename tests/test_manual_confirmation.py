"""Approved b002 manual completion contract, using real templates and shipped gate."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_issue_lifecycle import L, SKILL, context, template


TIME = dict(passed='2026-10-22T12:00:00Z', shown='2026-10-22T12:01:00Z', confirmed='2026-10-22T12:02:00Z')


def manual(kind='package', status='unknown', release_required=False):
    c = context()
    c.update(mode='manual', policy=dict(binding='optional', sync='milestones', close='off'), manual_summary_authorized=True)
    c['authorization']['close_policy'] = 'off'
    # Ensure old b001 event sets cannot silently authorize the new fact.
    c['authorization']['event_kinds'] = sorted(set(c['authorization']['event_kinds']) | {'delivery_confirmed'})
    c['release'].update(kind=kind, status=status, published=status == 'succeeded')
    c['completion_requirements'] = dict(feature_id=c['feature_id'], baseline_id=c['baseline_id'],
                                       scope_ids=c['scope_ids'], evidence='approved-current-criteria',
                                       required_acceptance_ids=['AC-local', 'AC-github', 'AC-gitlab'],
                                       release_required=release_required, release_kind=kind)
    c['acceptance'].update(passed_at=TIME['passed'], acceptance_results=[
        dict(id=k, status='passed', evidence=k + '-receipt')
        for k in c['completion_requirements']['required_acceptance_ids']])
    a = c['acceptance']
    cf = template('completion-confirmation.yaml')
    cf.update(feature_id=c['feature_id'], baseline_id=c['baseline_id'], delivery_id=a['delivery_id'],
              code_baseline_digest=a['code_baseline_digest'], target=c['binding'], scope_ids=c['scope_ids'],
              scope_description=c['scope_description'], event_id='f:r5:s100:delivery_confirmed',
              user_response='本次已展示交付完成，可以关闭这个Issue', response_evidence='user-original-response',
              confirmed_at=TIME['confirmed'])
    cf['presentation'] = dict(presented_at=TIME['shown'], evidence='final-delivery-presentation',
                              delivery_summary='已实现并独立验收当前完整交付，未发布不属于本次完成条件',
                              scope_coverage_evidence=['latest-scope-read'], acceptance_results=copy.deepcopy(a['acceptance_results']),
                              feature_id=c['feature_id'], baseline_id=c['baseline_id'], delivery_id=a['delivery_id'],
                              code_baseline_digest=a['code_baseline_digest'], target=c['binding'],
                              scope_ids=c['scope_ids'], scope_description=c['scope_description'],
                              acceptance_evidence=a['evidence'], unresolved_items=[], release_kind=kind,
                              release_status=status, release_required=release_required,
                              release_impact=dict(assessed=True, unresolved=[], evidence=['impact-disclosure']))
    c['completion_confirmation'] = cf
    c['required_comments'] = [dict(
        target=c['binding'], status='synced', receipt='single-complete-summary', verified_at=TIME['confirmed'],
        facts=[dict(kind='progress', event_kind='development_ready', event_id='progress-event', evidence='progress-source'),
               dict(kind='acceptance', event_kind='feature_completed', event_id='test-event', evidence=a['evidence']),
               dict(kind='confirmation', event_kind='delivery_confirmed', event_id=cf['event_id'], evidence=cf['response_evidence'])])]
    if release_required:
        c['required_comments'][0]['facts'].append(dict(kind='release', event_kind='release_succeeded',
                                                     event_id='release-event', evidence=c['release']['receipt']))
    return c


class ManualCompletionChecks(unittest.TestCase):
    def reject(self, value, reason):
        with self.assertRaisesRegex(L.Invalid, reason):
            L.close(value)

    def test_source_framework_tool_service_and_document_without_release(self):
        for kind, status in [('package', 'unknown'), ('package', 'unpublished'), ('service', 'unknown'), ('none', 'not_required')]:
            c = manual(kind, status)
            original = copy.deepcopy(c)
            self.assertTrue(L.close(c)['allowed'])
            self.assertEqual(c, original)  # No fake none or published mutation.

    def test_manual_boolean_or_fake_none_is_not_final_confirmation(self):
        c = manual('none', 'not_required')
        c.pop('completion_confirmation')
        self.reject(c, 'completion_confirmation')
        c['completion_confirmation'] = True
        self.reject(c, 'completion_confirmation')
        c = manual()
        c['release'].update(kind='none', status='not_required')
        self.reject(c, 'release_kind_mismatch')

    def test_product_approval_continue_and_raw_boolean_not_final_evidence(self):
        for kind in ('requirements', 'requirement_approved', 'direction_approved'):
            c = manual()
            c['completion_confirmation']['kind'] = kind
            self.reject(c, 'delivery_completion_required')
        for patch in ({'user_response': None}, {'response_evidence': None}, {'event_id': None}, {'confirmed_at': None}):
            c = manual()
            c['completion_confirmation'].update(patch)
            self.reject(c, 'confirmation_')

    def test_confirmation_after_current_independent_passed_and_display(self):
        for field in ('feature_id', 'baseline_id', 'delivery_id', 'code_baseline_digest', 'scope_description'):
            c = manual()
            c['completion_confirmation'][field] = 'wrong'
            self.reject(c, 'confirmation_.*mismatch')
        for when in ('2026-10-22T11:59:00Z', '2026-10-22T12:00:30Z'):
            c = manual()
            c['completion_confirmation']['confirmed_at'] = when
            self.reject(c, 'confirmation_time_order')
        c = manual()
        c['completion_confirmation']['presentation']['presented_at'] = '2026-10-22T11:59:00Z'
        self.reject(c, 'confirmation_time_order')
        c = manual()
        c['completion_confirmation']['presentation']['delivery_id'] = 'old'
        self.reject(c, 'presentation_.*mismatch')

    def test_current_failed_blocked_missing_platform_or_unresolved_rejected(self):
        for state in ('failed', 'blocked', 'untested'):
            c = manual()
            c['acceptance']['status'] = state
            self.reject(c, 'independent_acceptance')
            c = manual()
            c['acceptance']['acceptance_results'][-1]['status'] = state
            self.reject(c, 'applicable_acceptance_not_passed')
        c = manual()
        c['acceptance']['acceptance_results'].pop()  # GitLab cannot disappear from required scope.
        self.reject(c, 'applicable_acceptance_coverage')
        c = manual()
        c['completion_confirmation']['presentation']['unresolved_items'] = ['remaining work']
        self.reject(c, 'presentation_unresolved')
        for field in ('active_write', 'pending_input', 'unfinished_changes'):
            c = manual()
            c[field] = True
            self.reject(c, field)
        c = manual()
        c['scope_coverage']['remaining'] = ['other feature']
        self.reject(c, 'scope_incomplete')

    def test_failed_partial_rollback_outside_completion_preserves_real_status(self):
        for status in ('failed', 'partial', 'rolled_back', 'revoked'):
            c = manual(status=status)
            self.assertTrue(L.close(c)['allowed'])
            self.assertEqual(c['release']['status'], status)
            c['completion_confirmation']['presentation']['release_impact']['unresolved'] = ['affects this delivery']
            self.reject(c, 'release_impact_unresolved')
            c = manual(status=status, release_required=True)
            self.reject(c, 'release_not_succeeded')

    def test_required_release_and_automatic_not_weakened(self):
        c = manual(status='unknown', release_required=True)
        self.reject(c, 'release_not_succeeded')
        c = manual(status='succeeded', release_required=True)
        self.assertTrue(L.close(c)['allowed'])
        for kind in ('package', 'service'):
            c = manual(kind)
            c.update(mode='automatic', policy=dict(binding='optional', sync='milestones', close='after_release'))
            c['authorization']['close_policy'] = 'after_release'
            self.reject(c, 'release_not_succeeded')
        self.assertTrue(L.close(context())['allowed'])  # Existing after_release successful path preserved.

    def test_target_scope_permissions_and_new_event_not_inherited(self):
        c = manual()
        c['authorization']['operations'] = ['comment']
        self.reject(c, 'operation_not_authorized')
        c = manual()
        c['authorization']['event_kinds'].remove('delivery_confirmed')
        self.reject(c, 'event_not_authorized')
        c = manual()
        c['completion_confirmation']['target']['issue_number'] = 999
        self.reject(c, 'identity_conflict|target_mismatch')
        c = manual()
        c['completion_confirmation']['scope_ids'] = ['part']
        self.reject(c, 'confirmation_scope')
        c = manual()
        c['required_comments'][0]['facts'][-1]['event_id'] = 'old-confirmation'
        self.reject(c, 'confirmation_summary')
        c = manual()
        c['required_comments'][0]['facts'][-1]['evidence'] = 'old-response'
        self.reject(c, 'confirmation_summary')

    def test_confirmation_template_cli_and_display_contents(self):
        c = manual()
        for key in ('delivery_summary', 'scope_coverage_evidence', 'acceptance_results'):
            broken = copy.deepcopy(c)
            broken['completion_confirmation']['presentation'].pop(key)
            self.reject(broken, 'presentation_')
        broken = copy.deepcopy(c)
        broken['completion_confirmation']['event_id'] = 'f:r5:s100:feature_completed'
        self.reject(broken, 'confirmation_event_id')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manual.json'
            path.write_text(json.dumps(c))
            before = path.read_bytes()
            for check in ('confirmation', 'close'):
                result = subprocess.run([sys.executable, '-B', str(SKILL / 'scripts/lifecycle.py'), check, str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(json.loads(result.stdout)['ok'])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_displayed_status_and_required_scope_cannot_be_changed(self):
        for field, value in [('release_status', 'succeeded'), ('release_kind', 'none'), ('release_required', True),
                             ('acceptance_evidence', 'old-test'), ('scope_ids', ['part']), ('evidence', None)]:
            c = manual()
            c['completion_confirmation']['presentation'][field] = value
            self.reject(c, 'presentation_|confirmation_')
        c = manual()
        c['completion_requirements']['baseline_id'] = 'old-baseline'
        self.reject(c, 'completion_requirements_identity')


if __name__ == '__main__':
    unittest.main()
