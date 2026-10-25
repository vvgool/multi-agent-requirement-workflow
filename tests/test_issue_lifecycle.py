"""Template-backed isolated lifecycle protocol checks; never calls remote platforms.

These validate the shipped coordinator gate, not a daemon or native integration.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/issue-tracking'
SPEC = importlib.util.spec_from_file_location('issue_lifecycle', SKILL / 'scripts/lifecycle.py')
L = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(L)


def template(name):
    return yaml.safe_load((SKILL / 'assets/templates' / name).read_text())


def binding(provider='github'):
    repo = 'owner/repo' if provider == 'github' else 'org/subgroup/project'
    return dict(provider=provider, host='example.test', repository=repo, issue_number=7,
                url='https://example.test/' + repo + ('/issues/' if provider == 'github' else '/-/issues/') + '7',
                verified_at='2026-10-22T10:00:00Z')


def context(provider='github'):
    b = binding(provider)
    c = template('close-context.yaml')
    a = template('authorization.yaml')
    a.update(target=b, feature_id='feature-1', baseline_id='b001', scope_description='whole issue',
             operations=['comment', 'close'], event_kinds=sorted(L.EVENTS), close_policy='after_release',
             full_issue_scope=True, scope_evidence=['confirmed-scope'], user_response='批准此目标范围评论和关闭',
             confirmed_at='2026-10-22T10:00:00Z')
    acceptance = dict(status='passed', independent=True, feature_id='feature-1', baseline_id='b001',
                      delivery_id='d002', code_baseline_digest='a' * 64, evidence='independent-test-receipt')
    r = template('release-evidence.yaml')
    r.update(kind='package', status='succeeded', occurred_at='2026-10-22T10:00:00Z', target='registry',
             identity='1.0.0', commit_or_artifact='b' * 64, receipt='release-receipt', receipt_readable=True,
             published=True, public=True, draft=False, coverage=['whole'],
             **{k: acceptance[k] for k in ('feature_id', 'baseline_id', 'delivery_id', 'code_baseline_digest')})
    c.update(binding=b, feature_id='feature-1', baseline_id='b001', scope_description='whole issue',
             scope_ids=['whole'], authorization=a, acceptance=acceptance, release=r,
             approval_valid=True, related_sync_uncertain=False,
             scope_coverage=dict(mode='exclusive', confirmed=True, inspected_at='now', evidence=['latest-scope-read'],
                                 remaining=[], unknown=False, scope_ids=['whole']),
             remote=dict(target=b, state='open', read_at='now', scope_unchanged=True, externally_reopened=False),
             capabilities=['close', 'state_read'])
    for kind, event in [('progress', 'development_ready'), ('acceptance', 'feature_completed'), ('release', 'release_succeeded')]:
        c['required_comments'].append(dict(kind=kind, event_kind=event, target=b, status='synced',
                                          receipt=kind + '-receipt', verified_at='now'))
    return c


class LifecycleChecks(unittest.TestCase):
    def reject(self, check, value, reason):
        with self.assertRaisesRegex(L.Invalid, reason):
            check(value)

    def test_defaults_and_invalid_config_combinations(self):
        self.assertEqual(L.config({}), dict(binding='off', sync='off', close='off'))
        self.assertEqual(L.config(dict(binding='optional', sync='milestones'))['close'], 'off')
        for value, reason in [({'close': True}, 'invalid_close'), ({'extra': 1}, 'unknown_config'),
                              ({'close': 'always'}, 'invalid_close'), ({'sync': 'milestones'}, 'binding_off'),
                              ({'binding': 'optional', 'close': 'after_release'}, 'sync_off')]:
            self.reject(L.config, value, reason)

    def test_provider_identity_and_links(self):
        for provider in ('github', 'gitlab'):
            b = binding(provider)
            self.assertEqual(L.target(b)['issue_number'], 7)
            for field, val, reason in [('url', b['url'].replace('/issues/', '/pull/'), 'identity_conflict'),
                                      ('issue_number', True, 'issue_number'), ('issue_number', 0, 'issue_number'),
                                      ('url', b['url'].replace('https://', 'https://secret@'), 'invalid_issue_url')]:
                broken = dict(b, **{field: val})
                self.reject(L.target, broken, reason)
        self.reject(L.target, dict(binding(), pull_request={'url': 'pr'}), 'not_an_issue')
        b = binding('gitlab')
        self.reject(L.target, dict(b, url=b['url'].replace('/-/issues/', '/-/merge_requests/')), 'identity_conflict')
        self.reject(L.target, dict(b, issue_number=123456), 'identity_conflict')  # global id is not iid
        b['url'] = b['url'].replace('example.test/', 'example.test/prefix/')
        self.reject(L.target, b, 'identity_conflict')
        self.assertTrue(L.target(dict(b, verified_path_prefix='/prefix')))

    def test_full_automatic_close_each_provider(self):
        for provider in ('github', 'gitlab'):
            self.assertEqual(L.close(context(provider))['expected_state'], {'from': 'open', 'to': 'closed'})

    def test_authorization_is_separate_from_policy_binding_approval_release(self):
        c = context()
        for a in (None, {}, {'target': c['binding']}, dict(c['authorization'], operations=['comment'])):
            self.reject(L.close, dict(c, authorization=a), 'authorization|target_object_required|incomplete_target|operation_not_authorized')
        self.reject(L.close, dict(c, policy=dict(binding='optional', sync='milestones', close='off')), 'automatic_close_disabled')
        legacy = dict(target=c['binding'], scope='milestone_comments', user_response='评论', confirmed_at='then')
        x = dict(c, authorization=legacy, operation='comment', event_kind='development_ready', legacy_owner_feature_id='feature-1')
        self.assertTrue(L.authorization(x)['allowed'])
        self.reject(L.authorization, dict(x, operation='close'), 'legacy_authorization')
        self.reject(L.authorization, dict(x, event_kind='release_succeeded'), 'legacy_authorization')
        self.reject(L.authorization, dict(x, historical=True), 'history_authorization')
        self.reject(L.authorization, dict(x, legacy_owner_feature_id='different'), 'feature_ownership')

    def test_scope_baseline_revocation_and_later_revisions(self):
        c = context()
        x = dict(c, operation='close', baseline_id='b002')
        self.reject(L.authorization, x, 'baseline_mismatch')
        x['authorization'] = dict(c['authorization'], include_future_revisions=True)
        self.assertTrue(L.authorization(x)['allowed'])
        self.reject(L.close, dict(c, baseline_id='b002', authorization=x['authorization']), 'acceptance_identity')
        self.reject(L.authorization, dict(x, feature_id='other'), 'feature_mismatch')
        self.reject(L.authorization, dict(x, authorization=dict(x['authorization'], revoked=True)), 'revoked')
        self.reject(L.authorization, dict(x, scope_description='new scope'), 'scope_mismatch')
        self.assertTrue(L.authorization(dict(x, scope_description='new scope', future_scope_covered=True)))
        self.reject(L.close, dict(c, authorization=dict(c['authorization'], full_issue_scope=False)), 'full_scope_authorization')

    def test_release_requires_actual_verified_matching_delivery(self):
        c = context()
        for patch, reason in [({'status': 'partial'}, 'not_succeeded'), ({'status': 'rolled_back'}, 'not_succeeded'),
                               ({'status': 'failed'}, 'not_succeeded'), ({'receipt': None}, 'evidence_missing'),
                               ({'published': False}, 'not_verified'), ({'draft': True}, 'public_final'),
                               ({'public': False}, 'public_final'), ({'delivery_id': 'd001'}, 'delivery_id_mismatch'),
                               ({'baseline_id': 'b000'}, 'baseline_id_mismatch'), ({'coverage': []}, 'scope_incomplete')]:
            self.reject(L.release, dict(c, release=dict(c['release'], **patch)), reason)
        c['release'].update(kind='service', target='prod', environment='prod', runtime_verified=True)
        self.assertTrue(L.release(dict(c, environment='prod')))
        self.reject(L.release, dict(c, environment='staging'), 'environment_not_verified')
        c['release']['runtime_verified'] = False
        self.reject(L.release, dict(c, environment='prod'), 'environment_not_verified')

    def test_closed_scope_and_new_input_pause_close(self):
        c = context()
        for field in ('active_write', 'pending_input', 'unfinished_changes'):
            self.reject(L.close, dict(c, **{field: True}), field + '_prevents_close')
        for patch in ({'remaining': ['another-feature']}, {'unknown': True}, {'confirmed': False},
                      {'scope_ids': ['part']}, {'evidence': []}):
            self.reject(L.close, dict(c, scope_coverage=dict(c['scope_coverage'], **patch)), 'scope_incomplete')
        shared = dict(c, scope_coverage=dict(c['scope_coverage'], mode='shared'))
        self.assertTrue(L.close(shared))
        for patch, reason in [({'scope_unchanged': False}, 'scope_changed'), ({'externally_reopened': True}, 'reopen_conflict'),
                               ({'state': 'closed'}, 'already_closed'), ({'target': binding('gitlab')}, 'identity_not_verified')]:
            self.reject(L.close, dict(c, remote=dict(c['remote'], **patch)), reason)
        self.reject(L.close, dict(c, approval_valid=False), 'approval_not_valid')
        self.reject(L.close, dict(c, acceptance=dict(c['acceptance'], independent=False)), 'independent_acceptance')

    def test_comments_must_finish_before_close_and_capabilities_distinct(self):
        c = context()
        for state in ('pending', 'sending', 'unknown', 'blocked'):
            x = copy.deepcopy(c)
            x['required_comments'][0]['status'] = state
            self.reject(L.close, x, 'summary_not_verified')
        x = copy.deepcopy(c)
        x['required_comments'][-1]['event_kind'] = 'development_ready'
        self.reject(L.close, x, 'summary_event_kind_mismatch')
        self.reject(L.close, dict(c, related_sync_uncertain=True), 'sync_unknown')
        self.reject(L.close, dict(c, required_comments=c['required_comments'][:-1]), 'summaries_missing')
        self.reject(L.close, dict(c, capabilities=['comment', 'state_read']), 'capability_missing')
        x = copy.deepcopy(c)
        x['authorization']['event_kinds'].remove('release_succeeded')
        self.reject(L.close, x, 'event_not_authorized')
        # Failure leaves caller-owned business records untouched.
        before = copy.deepcopy(x)
        self.reject(L.close, x, 'event_not_authorized')
        self.assertEqual(x, before)

    def test_manual_boolean_no_release_is_not_final_completion(self):
        c = context()
        c.update(mode='manual', policy=dict(binding='optional', sync='off', close='off'),
                 release=dict(kind='none', status='not_required'), manual_summary_authorized=True)
        c['authorization']['close_policy'] = 'off'
        self.reject(L.close, c, 'completion_requirements')
        self.reject(L.close, dict(c, manual_summary_authorized=False), 'manual_summary')
        self.reject(L.close, dict(c, mode='automatic'), 'automatic_close_disabled')

    def test_recovery_unknown_does_not_blindly_retry(self):
        x = dict(operation='close', status='sending', target=binding(), remote_target=binding(),
                 original_request_queried=True, remote_state='open')
        self.assertEqual(L.recovery(x)['status'], 'unknown')
        self.assertEqual(L.recovery(dict(x, remote_state='closed')),
                         dict(status='unknown', remote_state='closed', attribution='external_or_unknown'))
        self.assertEqual(L.recovery(dict(x, remote_state='closed', attributable=True,
                                        request_receipt='request-1', readback_verified=True))['status'], 'synced')
        self.assertEqual(L.recovery(dict(x, definitively_not_executed=True, terminal_evidence='terminal'))['status'], 'pending')
        self.assertEqual(L.recovery(dict(x, definitively_not_executed=True))['status'], 'unknown')
        self.assertEqual(L.recovery(dict(x, externally_reopened=True))['status'], 'blocked')
        self.assertEqual(L.recovery(dict(x, permission_denied=True))['status'], 'blocked')
        self.reject(L.recovery, dict(x, original_request_queried=False), 'query_original')
        self.reject(L.recovery, dict(x, remote_target=binding('gitlab')), 'target_conflict')

    def test_comment_pagination_raw_body_dedup_and_recovery(self):
        c = dict(status='pending', identity_verified=True, pages_complete=True, raw_bodies_readable=True,
                 sync_key='key', body_sha256='digest', matches=[], target=binding(),
                 authorization_valid=True, policy_enabled=True)
        self.assertEqual(L.comment(c)['action'], 'persist_sending_then_send_once')
        for field, reason in [('pages_complete', 'pagination_incomplete'), ('raw_bodies_readable', 'raw_body_unavailable'),
                              ('identity_verified', 'target_not_verified'), ('authorization_valid', 'inactive'),
                              ('policy_enabled', 'inactive')]:
            self.reject(L.comment, dict(c, **{field: False}), reason)
        self.assertEqual(L.comment(dict(c, status='unknown'))['action'], 'none')
        self.assertEqual(L.comment(dict(c, status='sending'))['status'], 'unknown')
        self.assertEqual(L.comment(dict(c, status='unknown', definitively_not_executed=True,
                                       terminal_evidence='terminal'))['action'], 'persist_sending_then_send_once')
        m = dict(sync_key='key', body_sha256='digest', target=binding(), receipt='comment-1', readback_verified=True)
        self.assertEqual(L.comment(dict(c, status='unknown', matches=[m]))['status'], 'synced')
        self.reject(L.comment, dict(c, matches=[m, m]), 'multiple_comment_matches')
        self.reject(L.comment, dict(c, matches=[dict(m, body_sha256='externally-edited')]), 'body_or_target_conflict')
        self.assertEqual(L.comment(dict(c, status='synced'))['status'], 'blocked')

    def test_transport_outcomes_preserve_unknown_and_require_readback(self):
        for op in ('comment', 'close'):
            for result, status in [('permission_denied', 'blocked'), ('missing_capability', 'blocked'),
                                   ('timeout', 'unknown'), ('interrupted', 'unknown'), ('readback_failed', 'unknown'),
                                   ('response_incomplete', 'unknown')]:
                self.assertEqual(L.outcome(dict(operation=op, result=result))['status'], status)
            self.assertEqual(L.outcome(dict(operation=op, result='confirmed_not_executed',
                                             terminal_evidence='failure-receipt'))['status'], 'pending')
            v = dict(operation=op, result='verified', same_target=True, readback_verified=True,
                     attributable=True, receipt='request-receipt', remote_state='closed')
            self.assertEqual(L.outcome(v)['status'], 'synced')
            self.reject(L.outcome, dict(v, readback_verified=False), 'not_verified')
        self.reject(L.outcome, dict(v, remote_state='open'), 'close_readback_required')

    def test_stable_operation_key_legacy_bytes_and_history(self):
        x = dict(schema_version=2, feature_id='f', revision=5, event_id='f:r5:s1:feature_completed',
                 binding=binding(), operation='comment')
        comment = L.key(x)
        self.assertEqual(comment, L.key(dict(x, retry_time='later', host_invocation='another')))
        self.assertNotEqual(comment, L.key(dict(x, operation='close')))
        self.assertNotEqual(comment, L.key(dict(x, schema_version=1)))
        self.reject(L.key, dict(x, schema_version=1, operation='close'), 'legacy_record')
        c = dict(context(), operation='comment', event_kind='feature_completed', historical=True, event_id='old',
                 original_occurred_at='then', backfilled_at='now')
        self.reject(L.authorization, c, 'history_authorization')
        c['authorization']['history_event_ids'] = ['old']
        self.assertTrue(L.authorization(c))

    def test_cli_duplicate_keys_and_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'input.json'
            p.write_text('{"close":"off","close":"after_release"}')
            cmd = [sys.executable, str(SKILL / 'scripts/lifecycle.py'), 'config', str(p)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn('duplicate_json_key', r.stdout)
            p.write_text(json.dumps(context()))
            before = p.read_bytes()
            r = subprocess.run(cmd[:2] + ['close', str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(json.loads(r.stdout)['ok'])
            self.assertEqual(p.read_bytes(), before)
            self.assertEqual([x.name for x in Path(tmp).iterdir()], ['input.json'])

    def test_real_phase_mapping_and_snapshot_contract(self):
        if yaml.safe_load((ROOT / 'framework.yaml').read_text())['protocol_version'] == 3:
            text = (ROOT / 'workflow/issue-tracking.md').read_text()
            self.assertIn('默认关闭', text)
            self.assertIn('不创建本地事件流、sync目录', text)
            self.assertIn('未知先查原调用/远端事实', text)
            self.assertIn('配置和本地完成不替代关闭授权', text)
            self.assertIn('旧记录按原包解释', text)
            return
        text = (ROOT / 'workflow/issue-tracking.md').read_text()
        rows = [line for line in text.splitlines() if line.startswith('|')]
        mapping = {event: next(row for row in rows if event in row) for event in L.EVENTS}
        self.assertIn('实际修复开始', mapping['repair_started'])
        self.assertIn('上一交付失败、当前待重验', mapping['repair_started'])
        self.assertIn('测试调用开始', mapping['testing_started'])
        self.assertIn('保留原阶段', mapping['workflow_waiting_user'])
        self.assertIn('独立验收通过', mapping['feature_completed'])
        self.assertIn('已核实发布', mapping['release_succeeded'])
        route = (ROOT / 'workflow/routing.md').read_text()
        self.assertIn('unknown不伪造开始或失败', route)
        self.assertIn('无新事实不新增事件', route)
        self.assertIn('业务事实先', route)
        self.assertIn('平台 state 仅打开/关闭', text)
        comment = (SKILL / 'assets/templates/comment.md').read_text()
        for phrase in ('事件快照', 'stage / execution_status', '发布', '后续', 'sync_key'):
            self.assertIn(phrase, comment)
        for path in (ROOT / 'templates/feature-readme.md', ROOT / 'workflow/output-layout.md'):
            for phrase in ('独立验收', '发布', 'open/closed', '进度', 'unknown'):
                self.assertIn(phrase, path.read_text())

    def test_shipped_templates_and_references_agree(self):
        if yaml.safe_load((ROOT / 'framework.yaml').read_text())['protocol_version'] == 3:
            # Keep historical fixture structures and all corruption checks intact.
            self.assertEqual(template('sync-record.yaml')['schema_version'], 2)
            self.assertIn('remote_state', template('binding.yaml'))
            self.assertEqual(set(template('close-context.yaml')) - set(context()), set())
            text = (SKILL / 'SKILL.md').read_text()
            self.assertIn('不新增绑定/事件/授权/result YAML或同步目录', text)
            self.assertIn('写入结果未知时先查询原调用及远端状态', text)
            self.assertIn('默认关闭', text)
            self.assertIn('历史协议', (SKILL / 'references/lifecycle.md').read_text())
            return
        self.assertEqual(template('sync-record.yaml')['schema_version'], 2)
        self.assertIn('remote_state', template('binding.yaml'))
        self.assertIn('close: "off"', (ROOT / 'workflow/config.md').read_text())
        for path in [ROOT / 'workflow/issue-tracking.md', SKILL / 'SKILL.md', SKILL / 'references/lifecycle.md']:
            text = path.read_text()
            self.assertNotIn('不新建/关闭 Issue', text)
        text = (ROOT / 'workflow/issue-tracking.md').read_text()
        for kind in L.EVENTS:
            self.assertIn(kind, text)
        # Real templates are filled by context(), not replaced with test-only schemas.
        self.assertEqual(set(template('close-context.yaml')) - set(context()), set())


if __name__ == '__main__':
    unittest.main()
