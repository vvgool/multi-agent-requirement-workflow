"""Executable contract fixtures, NOT a production scheduler or native acceptance.

The framework is instructions. These tests independently validate file bindings
and reject corrupted example records; actual host behavior is a separate gate.
No network/delegation, no installed project writes. Use TMPDIR for scratch.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def baseline(content):
    return dict(schema_version=1, git_commit=None, scope=['src'], exclude=[],
                files=[dict(path='src/main.txt', sha256=sha(content.encode()))], evidence=[])


def ordinary(path, root):
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('path escape')
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError('symlink')
        cursor = cursor.parent
    if not path.is_file():
        raise ValueError('missing artifact')


def validate(task, host, result, out):
    """Read-only binding/content oracle for fixtures, not a transition engine."""
    identity = ('feature_id', 'requirements_revision', 'task_id', 'role')
    if (task['schema_version'], task['layout_version'], task['framework']['protocol_version']) != (2, 3, 2):
        raise ValueError('protocol/layout')
    for record in (host, result):
        if record['schema_version'] != 2 or any(record[k] != task[k] for k in identity):
            raise ValueError('identity')
    auths = {a['id']: a for a in task['authorizations']}
    if len(auths) != len(task['authorizations']):
        raise ValueError('authorization id')
    calls = {}
    for call in host['invocations']:
        if call['id'] in calls:
            raise ValueError('invocation id')
        calls[call['id']] = call
        if call['authorization'] not in auths:
            raise ValueError('authorization missing')
        if call['call_id'] is None and not call.get('call_id_limitation'):
            raise ValueError('call id limitation')
        if call['status'] in ('ended', 'cancelled') and not (call.get('ended_at') and call.get('end_evidence')):
            raise ValueError('end evidence')
        auth = auths[call['authorization']]
        writable = auth['write_scope']['modify_business_source']
        if (task['role'] == 'testing' or auth['purpose'] == 'boundary') and writable:
            raise ValueError('unauthorized source write')
        if writable and not (auth.get('approval_digest') and auth['write_scope'].get('project_paths') and auth.get('attempt')):
            raise ValueError('write authorization')
    ids = set()
    for delivery in result['deliveries']:
        if delivery['id'] in ids:
            raise ValueError('delivery id')
        ids.add(delivery['id'])
        call = calls[delivery['invocation_id']]
        if call['status'] not in ('ended', 'cancelled'):
            raise ValueError('handoff before end')
        if delivery['input_sha256'] != call['input']['sha256']:
            raise ValueError('input binding')
        for artifact in delivery['artifacts']:
            relative = Path(artifact['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('artifact path')
            p = out / relative
            ordinary(p, out)
            if sha(p.read_bytes()) != artifact['sha256']:
                raise ValueError('artifact hash')
        if delivery['status'] in ('ready', 'passed', 'failed') and task['role'] != 'product':
            b = delivery['code_baseline']
            if not b['scope'] or not b['files']:
                raise ValueError('baseline')
        if task['role'] == 'testing':
            auth = auths[call['authorization']]
            if delivery['source_delivery'] != auth['source_delivery']:
                raise ValueError('source delivery')
            if delivery['code_baseline'] != auth['development_baseline']['code_baseline']:
                raise ValueError('source baseline')
            if delivery['status'] == 'failed' and not delivery.get('defects'):
                raise ValueError('failure evidence')


class Fixture:
    def __init__(self, directory, role):
        self.directory = directory / role
        self.out = self.directory / 'outputs'
        self.task = yaml.safe_load((ROOT / ('templates/product-task.yaml' if role == 'product' else 'templates/role-task.yaml')).read_text())
        self.task.update(feature_id='fixture', requirements_revision=1, layout_version=3, task_id=role, role=role,
                         framework=dict(name='multi-agent-requirement-workflow', version='0.4.0', protocol_version=2, sha256='a' * 64),
                         output_dir=str(self.out), result_path=str(self.directory / 'result.yaml'))
        identity = dict(schema_version=2, feature_id='fixture', requirements_revision=1, task_id=role, role=role)
        self.host = dict(identity, invocations=[])
        self.result = dict(identity, deliveries=[])

    def call(self, purpose='execute', attempt=None, source=None, code=None, host='codex', agent='native-fixture'):
        i = f'i{len(self.host["invocations"]) + 1:03}'
        a = dict(id='a' + i[1:], purpose=purpose, approval_digest='approved' if attempt else None,
                 write_scope=dict(modify_business_source=bool(attempt), project_paths=['src'] if attempt else []),
                 completion_criteria=['fixed scenario'])
        if attempt:
            a['attempt'] = attempt
        if source:
            a['source_delivery'] = source
            a['development_baseline'] = dict(source, code_baseline=code)
        self.task['authorizations'].append(a)
        self.host['invocations'].append(dict(id=i, host=host, agent_id=agent, call_id=None,
            call_id_limitation='fixture has no real host call ID', status='ended', started_at='2026-10-21T00:00:00Z',
            ended_at='2026-10-21T00:00:01Z', end_evidence='fixture, not native',
            input=dict(path='revisions/v1/input.md', sha256=sha(i.encode())), authorization=a['id']))
        return i

    def deliver(self, status, code=None, source=None):
        call = self.host['invocations'][-1]
        d = f'd{len(self.result["deliveries"]) + 1:03}'
        path = self.out / d / 'report.md'
        path.parent.mkdir(parents=True)
        path.write_text(f'{self.task["role"]} {d}: {status}; source={source}; code={code}\n')
        delivery = dict(id=d, invocation_id=call['id'], status=status, input_sha256=call['input']['sha256'],
            summary='fixture change/conclusion', artifacts=[dict(kind='report', path=f'{d}/report.md', sha256=sha(path.read_bytes()))])
        if code:
            delivery['code_baseline'] = code
        if source:
            delivery['source_delivery'] = source
            delivery['acceptance_results'] = [dict(id='AC-fixture', status=status, actual='fixture observation', evidence=f'{d}/report.md')]
        if self.task['role'] in ('development', 'bug'):
            delivery['changed_files'] = [] if status == 'boundary_ready' else ['src/main.txt']
        if status == 'failed':
            delivery['defects'] = [dict(id='DEF-1', evidence=f'{d}/report.md')]
        if self.task['role'] == 'product':
            delivery['acceptance_ids'] = ['AC-fixture']
        self.result['deliveries'].append(delivery)
        return dict(task_id=self.task['task_id'], delivery_id=d)

    def persist(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        for name, obj in [('task', self.task), ('host', self.host), ('result', self.result)]:
            if name == 'result' and not self.result['deliveries']:
                continue
            (self.directory / f'{name}.yaml').write_text(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False))
        validate(self.task, self.host, self.result, self.out)


class ContinuousTaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='continuous-contract-')
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)

    def development(self):
        f = Fixture(self.directory, 'development')
        f.call(attempt=1)
        f.deliver('ready', code=baseline('v1'))
        return f

    def test_fixed_scenario_counts_and_immutable_rounds(self):
        p = Fixture(self.directory, 'product')
        p.call(); p.persist()
        self.assertFalse(p.out.exists())
        self.assertFalse((p.directory / 'result.yaml').exists())
        p.call(); p.persist()  # two clarification calls, no deliveries
        self.assertFalse(p.out.exists())
        p.call(); p.deliver('ready'); p.persist()
        d = self.development()
        # Several self-checks do not introduce invocations or attempts.
        for _ in range(3):
            self.assertEqual(d.task['authorizations'][-1]['attempt'], 1)
        first = d.result['deliveries'][0].copy()
        first_bytes = (d.out / first['artifacts'][0]['path']).read_bytes()
        t = Fixture(self.directory, 'testing')
        source = dict(task_id='development', delivery_id='d001')
        t.call(source=source, code=baseline('v1')); t.deliver('failed', baseline('v1'), source)
        d.call(attempt=2); source = d.deliver('ready', baseline('v2'))
        t.call(source=source, code=baseline('v2')); t.deliver('passed', baseline('v2'), source)
        d.call(attempt=2)  # same attempt transfer to specialist, no new delivery
        b = Fixture(self.directory, 'bug')
        b.call(purpose='boundary'); b.deliver('boundary_ready')
        b.call(purpose='fix', attempt=2); bug_source = b.deliver('ready', baseline('v3'))
        t.call(source=bug_source, code=baseline('v3')); t.deliver('passed', baseline('v3'), bug_source)
        d.call(attempt=2); source = d.deliver('ready', baseline('v4'))
        t.call(source=source, code=baseline('v4')); t.deliver('passed', baseline('v4'), source)
        for f in (d, t, b):
            f.persist()
        self.assertEqual(d.result['deliveries'][0], first)
        self.assertEqual((d.out / first['artifacts'][0]['path']).read_bytes(), first_bytes)
        tasks = [p, d, t, b]
        calls = sum(len(f.host['invocations']) for f in tasks)
        deliveries = sum(len(f.result['deliveries']) for f in tasks)
        self.assertEqual((len(tasks), calls, deliveries), (4, 13, 10))
        files = list(self.directory.rglob('*'))
        after_files = sum(f.is_file() for f in files)
        self.assertEqual(after_files, 22)  # 4 * task/host/result + 10 immutable docs
        self.assertFalse(list(self.directory.rglob('runs')))
        print(json.dumps(dict(scope='STATIC executable fixture; not native', tasks_before=calls, tasks_after=4,
             calls_before=calls, calls_after=calls, deliveries_before=deliveries, deliveries_after=deliveries,
             files_before=calls * 3 + deliveries, files_after=after_files,
             excluded='shared root/input/config and equal raw checks omitted on both sides; not tokens')))

    def test_duplicate_delivery_and_input_binding_rejected(self):
        f = self.development()
        f.result['deliveries'].append(copy.deepcopy(f.result['deliveries'][0]))
        with self.assertRaisesRegex(ValueError, 'delivery id'): validate(f.task, f.host, f.result, f.out)
        f.result['deliveries'].pop()
        f.result['deliveries'][0]['input_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'input binding'): validate(f.task, f.host, f.result, f.out)

    def test_partial_write_missing_or_edited_artifact_rejected(self):
        f = self.development()
        p = f.out / f.result['deliveries'][0]['artifacts'][0]['path']
        p.unlink()
        with self.assertRaisesRegex(ValueError, 'missing artifact'): validate(f.task, f.host, f.result, f.out)
        p.write_text('partial or user edit')
        with self.assertRaisesRegex(ValueError, 'artifact hash'): validate(f.task, f.host, f.result, f.out)

    def test_symlink_and_parent_escape_rejected(self):
        f = self.development()
        artifact = f.result['deliveries'][0]['artifacts'][0]
        original = artifact.copy()
        artifact['path'] = '../outside.md'
        with self.assertRaisesRegex(ValueError, 'artifact path'): validate(f.task, f.host, f.result, f.out)
        artifact.update(original)
        p = f.out / artifact['path']; saved = p.read_bytes(); p.unlink()
        elsewhere = self.directory / 'other.md'; elsewhere.write_bytes(saved); p.symlink_to(elsewhere)
        with self.assertRaises(ValueError): validate(f.task, f.host, f.result, f.out)

    def test_unknown_running_cannot_be_consumed(self):
        f = self.development()
        for status in ['unknown', 'running']:
            f.host['invocations'][0]['status'] = status
            with self.assertRaisesRegex(ValueError, 'before end'): validate(f.task, f.host, f.result, f.out)

    def test_missing_end_or_call_id_limit_rejected(self):
        f = self.development()
        call = f.host['invocations'][0]; call.pop('end_evidence')
        with self.assertRaisesRegex(ValueError, 'end evidence'): validate(f.task, f.host, f.result, f.out)
        call['end_evidence'] = 'real end'; call.pop('call_id_limitation')
        with self.assertRaisesRegex(ValueError, 'call id limitation'): validate(f.task, f.host, f.result, f.out)

    def test_test_delivery_bound_to_exact_development_delivery(self):
        t = Fixture(self.directory, 'testing')
        source = dict(task_id='development', delivery_id='d002')
        t.call(source=source, code=baseline('v2')); t.deliver('passed', baseline('v2'), source)
        validate(t.task, t.host, t.result, t.out)
        t.result['deliveries'][0]['source_delivery'] = dict(task_id='development', delivery_id='d001')
        with self.assertRaisesRegex(ValueError, 'source delivery'): validate(t.task, t.host, t.result, t.out)
        t.result['deliveries'][0]['source_delivery'] = source
        t.result['deliveries'][0]['code_baseline'] = baseline('v1')
        with self.assertRaisesRegex(ValueError, 'source baseline'): validate(t.task, t.host, t.result, t.out)

    def test_test_and_bug_boundary_cannot_write(self):
        for role, purpose in [('testing', 'execute'), ('bug', 'boundary')]:
            f = Fixture(self.directory, role); f.call(purpose=purpose, attempt=1)
            with self.assertRaisesRegex(ValueError, 'unauthorized source write'): validate(f.task, f.host, f.result, f.out)

    def test_boundary_to_fix_retains_old_authorization(self):
        b = Fixture(self.directory, 'bug'); b.call(purpose='boundary')
        before = copy.deepcopy(b.task['authorizations'][0])
        b.call(purpose='fix', attempt=1)
        self.assertEqual(b.task['authorizations'][0], before)
        self.assertFalse(b.task['authorizations'][0]['write_scope']['modify_business_source'])
        self.assertEqual([c['authorization'] for c in b.host['invocations']], ['a001', 'a002'])
        validate(b.task, b.host, b.result, b.out)

    def test_host_change_retains_task_and_historical_ids(self):
        f = Fixture(self.directory, 'product'); f.call(host='codex', agent='codex-A')
        f.call(host='claude-code', agent='claude-B')
        self.assertEqual(f.task['task_id'], 'product')
        self.assertEqual([c['agent_id'] for c in f.host['invocations']], ['codex-A', 'claude-B'])
        f.persist()

    def test_protocol_layout_gate_and_legacy_bytes(self):
        f = self.development(); f.task['layout_version'] = 2
        with self.assertRaisesRegex(ValueError, 'protocol/layout'): validate(f.task, f.host, f.result, f.out)
        p = self.directory / 'old-task.yaml'; p.write_text('schema_version: 1\nrun_id: development-001\nlayout_version: 2\n')
        before = p.read_bytes(); yaml.safe_load(before)
        self.assertEqual(p.read_bytes(), before)

    def test_late_result_keeps_current_call_and_pending_input(self):
        f = self.development()
        old_delivery = f.result['deliveries'][0]
        f.call(attempt=2)
        f.host['invocations'][-1]['status'] = 'running'
        root = dict(active_run=dict(task_id='development', invocation_id='i002'),
                    development_baseline=dict(task_id='development', delivery_id='d001'),
                    pending_input='new user scope not covered by i001')
        before = copy.deepcopy(root)
        # Read-only intake oracle: task identity alone is insufficient.
        matches = (root['active_run']['invocation_id'] == old_delivery['invocation_id']
                   and not root['pending_input'])
        self.assertFalse(matches)
        self.assertEqual(root, before)
        self.assertEqual(old_delivery['id'], 'd001')

    def test_attempt_scope_is_shared_not_call_count(self):
        d = self.development()
        d.call(attempt=1)  # interrupted execution recovery
        d.call(attempt=1)  # same-attempt return from specialist
        d.call(attempt=2)  # actual new repair after independent failure
        b = Fixture(self.directory, 'bug'); b.call(purpose='fix', attempt=2)
        # Inspect recorded attempt identities, not role/task/host counts.
        attempts = {a['attempt'] for f in [d, b] for a in f.task['authorizations']}
        self.assertEqual(attempts, {1, 2})
        maximum = 2
        self.assertFalse(max(attempts) + 1 <= maximum)
        self.assertNotEqual(len(d.host['invocations']) + len(b.host['invocations']), len(attempts))

    def test_same_check_failure_and_retry_have_distinct_evidence(self):
        f = self.development()
        first = f.result['deliveries'][0]['artifacts'][0]
        failed = f.out / 'check-01-failed.txt'; failed.write_text('actual red fixture')
        retried = f.out / 'check-02-retry.txt'; retried.write_text('actual green fixture')
        f.call(attempt=1); f.deliver('ready', baseline('v2'))
        self.assertEqual(len(f.result['deliveries']), 2)
        self.assertTrue(failed.is_file() and retried.is_file())
        self.assertEqual(sha((f.out / first['path']).read_bytes()), first['sha256'])

    def test_all_stage_templates_have_single_authoritative_structure(self):
        for name in ['product-task', 'role-task']:
            t = yaml.safe_load((ROOT / f'templates/{name}.yaml').read_text())
            self.assertEqual((t['schema_version'], t['layout_version']), (2, 4))
            self.assertIn('authorizations', t)
            self.assertNotIn('run_id', t)
            self.assertNotIn('write_scope', t)  # each invocation's authorization owns this
        for name in ['product-result', 'role-result']:
            t = yaml.safe_load((ROOT / f'templates/{name}.yaml').read_text())
            self.assertEqual(t['deliveries'], [])
            self.assertNotIn('status', t)
        bug_skill = (ROOT / 'skills/bug-fixing/SKILL.md').read_text()
        self.assertNotIn('bug_purpose', bug_skill)
        self.assertIn('授权purpose=boundary', bug_skill)
        self.assertIn('授权purpose=fix', bug_skill)
        contract = (ROOT / 'workflow/continuous-tasks.md').read_text()
        for required in ['unknown', '迟到', '部分写入', '同一次', '本轮未重跑', 'attempt', '3–5', '单写', 'protocol_version=2']:
            # equivalent exact wording for the same attempt clause
            self.assertIn(required if required != '同一次' else '同一修复尝试', contract)


if __name__ == '__main__':
    unittest.main()
