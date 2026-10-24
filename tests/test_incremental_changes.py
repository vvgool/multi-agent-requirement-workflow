"""Read-only contract oracles + file fixtures, NOT a scheduler/native acceptance.

Fixtures use real layout4 templates. Assertions reject inconsistent records; no
function here dispatches an agent or mutates production state. No new CLI.
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


def ordinary(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('path escape')
    p = root / p
    cursor = p
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError('symlink')
        cursor = cursor.parent
    if not p.is_file():
        raise ValueError('missing file')
    return p


def read_record(root, relative):
    return yaml.safe_load(ordinary(root, relative).read_bytes())


def validate_review(root, status):
    """Re-read immutable approval/manifest/text/source/config, never trust IDs alone."""
    bid = status['content_baseline']
    prefix = f'revisions/v1/.workflow/reviews/{bid}'
    approval = read_record(root, prefix + '/approval.yaml')
    manifest_path = ordinary(root, prefix + '/review-manifest.yaml')
    manifest = yaml.safe_load(manifest_path.read_bytes())
    if (approval.get('type', 'requirements') not in ('requirements', 'bug_boundary')
            or approval.get('type', 'requirements') != manifest.get('type', 'requirements')):
        raise ValueError('approval type')
    if approval != status['approval']:
        raise ValueError('approval record')
    if (approval['baseline_id'], approval['review_digest']) != (bid, sha(manifest_path.read_bytes())):
        raise ValueError('approval digest')
    if (manifest['feature_id'], manifest['revision'], manifest['baseline_id']) != ('incremental-fixture', 1, bid):
        raise ValueError('review identity')
    for record in manifest['files'] + manifest['sources'] + [manifest['effective_config']]:
        if sha(ordinary(root, record['path']).read_bytes()) != record['sha256']:
            raise ValueError('review content')
    body = ordinary(root, manifest['files'][0]['path']).read_bytes()
    if ordinary(root, manifest['display_path']).read_bytes() != body:
        raise ValueError('formal conflict')
    if manifest.get('type', 'requirements') not in ('requirements', 'bug_boundary'):
        raise ValueError('review source type')
    role, verdict, artifact_kind = ('bug', 'boundary_ready', 'bug_boundary') if manifest.get('type') == 'bug_boundary' else ('product', 'ready', 'requirements')
    ref = manifest.get('source_delivery', {})
    if ref.get('task_id') != role:
        raise ValueError('review source role')
    prefix = f'revisions/v1/.workflow/tasks/{role}'
    task = read_record(root, prefix + '/task.yaml')
    result = read_record(root, prefix + '/result.yaml')
    host = read_record(root, prefix + '/host.yaml')
    identity = dict(schema_version=2, feature_id=manifest['feature_id'], requirements_revision=manifest['revision'], task_id=role, role=role)
    if any(any(record.get(k) != v for k, v in identity.items()) for record in (task, result, host)):
        raise ValueError('review source identity')
    matches = [d for d in result['deliveries'] if d['id'] == ref.get('delivery_id')]
    if len(matches) != 1 or matches[0]['status'] != verdict:
        raise ValueError('review source delivery/status')
    delivery = matches[0]
    calls = [c for c in host['invocations'] if c['id'] == delivery['invocation_id']]
    if len(calls) != 1 or calls[0]['status'] != 'ended' or not calls[0].get('end_evidence'):
        raise ValueError('review source call')
    call = calls[0]
    if len([a for a in task['authorizations'] if a['id'] == call['authorization']]) != 1:
        raise ValueError('review source authorization')
    raw = ordinary(root, call['input']['path']).read_bytes()
    if (delivery['input_sha256'] != call['input']['sha256']
            or sum(sha(raw[:i]) == delivery['input_sha256'] for i in range(len(raw) + 1)) != 1):
        raise ValueError('review source input prefix')
    artifacts = [a for a in delivery['artifacts'] if a.get('kind') == artifact_kind]
    if len(artifacts) != 1:
        raise ValueError('review source artifact')
    artifact = artifacts[0]
    candidate = ordinary(root, task['output_dir'] + '/' + artifact['path']).read_bytes()
    if sha(candidate) != artifact['sha256'] or candidate != body:
        raise ValueError('review source content')
    if status['pending_inputs']:
        raise ValueError('pending scope input')
    return approval


def validate_dispatch(root, status, task, host, invocation_id, *, new_scope=False):
    """Judge a proposed record; no scheduling or state transitions are implemented."""
    if (task['framework']['version'], task['framework']['protocol_version'], task['schema_version'], task['layout_version']) != ('0.5.0', 2, 2, 4):
        raise ValueError('protocol/layout binding')
    call = next(c for c in host['invocations'] if c['id'] == invocation_id)
    index = host['invocations'].index(call)
    if any(c['status'] in ('unknown', 'running') for c in host['invocations'][:index]):
        raise ValueError('previous active call')
    if any(not c.get('end_evidence') for c in host['invocations'][:index]):
        raise ValueError('missing end evidence')
    auth = next(a for a in task['authorizations'] if a['id'] == call['authorization'])
    if status['pending_inputs']:
        raise ValueError('pending scope input')
    approval = validate_review(root, status)
    manifest = read_record(root, f'revisions/v1/.workflow/reviews/{approval["baseline_id"]}/review-manifest.yaml')
    if auth.get('effective_config', task['effective_config']) != manifest['effective_config']:
        raise ValueError('call configuration binding')
    if (auth['baseline_id'], auth['approval_digest']) != (approval['baseline_id'], approval['review_digest']):
        raise ValueError('old write approval')
    if auth.get('attempt', status['development_attempt']) != status['development_attempt']:
        raise ValueError('attempt identity')
    if (status['development_attempt'] > status['max_development_attempts']
            or (new_scope and status['development_attempt'] == status['max_development_attempts'])):
        raise ValueError('attempt limit')
    raw = ordinary(root, call['input']['path']).read_bytes()
    # Each historical input digest must identify exactly one append-only prefix.
    if sum(sha(raw[:i]) == call['input']['sha256'] for i in range(len(raw) + 1)) != 1:
        raise ValueError('input prefix')
    return auth


def validate_handoff(root, status, task, host, result, delivery, *, recovery=None):
    if delivery not in result['deliveries']:
        raise ValueError('uncommitted delivery')
    auth = validate_dispatch(root, status, task, host, delivery['invocation_id'])
    call = next(c for c in host['invocations'] if c['id'] == delivery['invocation_id'])
    if call['status'] != 'ended' or not call.get('end_evidence'):
        raise ValueError('handoff before end')
    active = status['active_run']
    binding = dict(task_id=task['task_id'], invocation_id=call['id'])
    if (host['invocations'][-1]['id'] != call['id'] or result['deliveries'][-1] != delivery
            or (active and any(active.get(k) != v for k, v in binding.items()))):
        raise ValueError('late invocation')
    # Existing formal artifact indexes are receipts, not a new consumption ledger.
    receipts = status.get('artifacts', [])
    consumed = any(any(
        entry.get('task_id') == task['task_id'] and entry.get('delivery_id') == delivery['id']
        and entry.get('kind') == artifact.get('kind') and entry.get('sha256') == artifact['sha256']
        for entry in receipts) for artifact in delivery['artifacts'])
    expected_recovery = dict(binding, delivery_id=delivery['id'], baseline_id=delivery['baseline_id'],
        approval_digest=delivery['approval_digest'], input_sha256=delivery['input_sha256'],
        end_evidence=call['end_evidence'])
    if not active and not consumed and recovery != expected_recovery:
        raise ValueError('no current handoff or verified recovery')
    if (delivery['baseline_id'], delivery['approval_digest']) != (auth['baseline_id'], auth['approval_digest']):
        raise ValueError('delivery baseline')
    if delivery['input_sha256'] != call['input']['sha256']:
        raise ValueError('delivery input')
    for artifact in delivery['artifacts']:
        p = ordinary(root / task['output_dir'], artifact['path'])
        if sha(p.read_bytes()) != artifact['sha256']:
            raise ValueError('artifact digest')
    if task['role'] == 'testing':
        source = status['development_baseline']
        if delivery['source_delivery'] != {k: source[k] for k in ['task_id', 'delivery_id']}:
            raise ValueError('old source delivery')
        if delivery['code_baseline'] != source['code_baseline']:
            raise ValueError('old code baseline')
        if (source['baseline_id'], source['approval_digest']) != (auth['baseline_id'], auth['approval_digest']):
            raise ValueError('old development approval')
        if delivery['status'] == 'passed' and (delivery['acceptance_ids'] != status['acceptance_ids'] or delivery.get('defects')):
            raise ValueError('incomplete acceptance')
    return 'already_consumed' if consumed else 'advance'


class Records:
    """Explicit synthetic writer used only to arrange file evidence for the oracle."""
    def __init__(self, root):
        self.root = root
        self.status = dict(content_baseline=None, approval=None, pending_inputs=[], active_run=None,
                           development_attempt=1, max_development_attempts=3, acceptance_ids=['AC-1'])
        self.tasks, self.hosts, self.results = {}, {}, {}
        self.input = 'revisions/v1/input.md'
        self.write(self.input, 'original requirement\n')
        self.config = 'revisions/v1/.workflow/snapshots/config.yaml'
        self.write(self.config, 'provider: local\n')
        for role in ['product', 'development', 'testing']:
            task = yaml.safe_load((ROOT / f'templates/{"product-task" if role == "product" else "role-task"}.yaml').read_bytes())
            task.update(feature_id='incremental-fixture', requirements_revision=1, task_id=role, role=role,
                        framework=dict(name='multi-agent-requirement-workflow', version='0.5.0', protocol_version=2, sha256='a' * 64),
                        output_dir=f'revisions/v1/.workflow/tasks/{role}/outputs',
                        effective_config=dict(path=self.config, sha256=sha(ordinary(self.root, self.config).read_bytes())))
            self.tasks[role] = task
            identity = {k: task[k] for k in ['schema_version', 'feature_id', 'requirements_revision', 'task_id', 'role']}
            self.hosts[role] = dict(identity, invocations=[])
            self.results[role] = dict(identity, deliveries=[])

    def write(self, path, body):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
        return dict(path=path, sha256=sha(p.read_bytes()))

    def record(self, path, obj):
        return self.write(path, yaml.safe_dump(obj, allow_unicode=True, sort_keys=False))

    def review(self, bid, sources=None, kind='requirements'):
        role = 'bug' if kind == 'bug-boundary' else 'product'
        if role not in self.tasks:
            task = copy.deepcopy(self.tasks['development'])
            task.update(task_id=role, role=role, authorizations=[], output_dir=f'revisions/v1/.workflow/tasks/{role}/outputs')
            self.tasks[role] = task
            identity = {k: task[k] for k in ['schema_version', 'feature_id', 'requirements_revision', 'task_id', 'role']}
            self.hosts[role] = dict(identity, invocations=[])
            self.results[role] = dict(identity, deliveries=[])
        prefix = f'revisions/v1/.workflow/reviews/{bid}'
        body = self.write(prefix + f'/{kind}.md', f'{bid}: ' + ', '.join(self.status['acceptance_ids']) + '\n')
        display = f'revisions/v1/documents/{kind}.md'
        self.write(display, ordinary(self.root, body['path']).read_text())
        # A real candidate record precedes its review; synthetic, never human evidence.
        task, host, result = self.tasks[role], self.hosts[role], self.results[role]
        iid, did = f'i{len(host["invocations"]) + 1:03}', f'd{len(result["deliveries"]) + 1:03}'
        auth = dict(id='a' + iid[1:], baseline_id=None, approval_digest=None,
                    source_baseline_id=self.status['content_baseline'], purpose='candidate', write_scope=task['output_dir'])
        task['authorizations'].append(auth)
        input_ref = dict(path=self.input, sha256=sha(ordinary(self.root, self.input).read_bytes()))
        host['invocations'].append(dict(id=iid, authorization=auth['id'], status='ended', end_evidence='synthetic candidate ended', input=input_ref))
        artifact = self.write(task['output_dir'] + f'/{did}/{kind}.md', ordinary(self.root, body['path']).read_text())
        result['deliveries'].append(dict(id=did, invocation_id=iid, status='boundary_ready' if role == 'bug' else 'ready',
            input_sha256=input_ref['sha256'], artifacts=[dict(kind='bug_boundary' if role == 'bug' else 'requirements',
            path=f'{did}/{kind}.md', sha256=artifact['sha256'])]))
        for name, record in [('task', task), ('host', host), ('result', result)]:
            self.record(f'revisions/v1/.workflow/tasks/{role}/{name}.yaml', record)
        manifest = dict(feature_id='incremental-fixture', revision=1, baseline_id=bid, files=[body],
                        display_path=display, sources=sources or [],
                        effective_config=dict(path=self.config, sha256=sha(ordinary(self.root, self.config).read_bytes())),
                        source_delivery=dict(task_id=role, delivery_id=did))
        if kind == 'bug-boundary':
            manifest['type'] = 'bug_boundary'
        m = self.record(prefix + '/review-manifest.yaml', manifest)
        a = dict(feature_id='incremental-fixture', revision=1, baseline_id=bid, review_digest=m['sha256'],
                 user_response=f'合成控制器明确批准 {bid}', confirmed_at='2026-10-22T00:00:00Z', source_session=None,
                 test_controller_synthetic=True, human_approval=False)
        if kind == 'bug-boundary':
            a['type'] = 'bug_boundary'
        self.record(prefix + '/approval.yaml', a)
        self.status.update(content_baseline=bid, approval=a, pending_inputs=[])

    def call(self, role):
        task, host = self.tasks[role], self.hosts[role]
        i = f'i{len(host["invocations"]) + 1:03}'
        a = dict(id='a' + i[1:], baseline_id=self.status['content_baseline'],
                 approval_digest=self.status['approval']['review_digest'], purpose='execute',
                 write_scope=dict(modify_business_source=role == 'development'), completion_criteria=['current acceptance'])
        if role == 'development':
            a['attempt'] = self.status['development_attempt']
        task['authorizations'].append(a)
        host['invocations'].append(dict(id=i, authorization=a['id'], status='ended', end_evidence='synthetic fixture only',
            input=dict(path=self.input, sha256=sha(ordinary(self.root, self.input).read_bytes()))))
        self.status['active_run'] = dict(task_id=role, invocation_id=i)
        return i

    def deliver(self, role, verdict):
        task, result, host = self.tasks[role], self.results[role], self.hosts[role]
        call = host['invocations'][-1]
        a = task['authorizations'][-1]
        did = f'd{len(result["deliveries"]) + 1:03}'
        relative = f'{did}/report.md'
        path = task['output_dir'] + '/' + relative
        artifact = self.write(path, f'{role}/{did}/{a["baseline_id"]}: {verdict}\n')
        delivery = dict(id=did, invocation_id=call['id'], baseline_id=a['baseline_id'], approval_digest=a['approval_digest'],
                        status=verdict, input_sha256=call['input']['sha256'], artifacts=[dict(artifact, kind='test_report' if role == 'testing' else 'development_record', path=relative)])
        if role == 'development':
            delivery['code_baseline'] = dict(scope=['src'], files=[dict(path='src/app.txt', sha256=sha(a['baseline_id'].encode()))])
            self.status['development_baseline'] = dict(task_id=role, delivery_id=did, baseline_id=a['baseline_id'],
                approval_digest=a['approval_digest'], code_baseline=delivery['code_baseline'])
        if role == 'testing':
            source = self.status['development_baseline']
            delivery.update(source_delivery={k: source[k] for k in ['task_id', 'delivery_id']},
                            code_baseline=source['code_baseline'], acceptance_ids=self.status['acceptance_ids'][:])
            if verdict == 'failed':
                delivery['defects'] = ['synthetic independent failure']
        result['deliveries'].append(delivery)
        return delivery

    def persist(self):
        self.record('status.yaml', self.status)
        for role, task in self.tasks.items():
            prefix = f'revisions/v1/.workflow/tasks/{role}'
            self.record(prefix + '/task.yaml', task)
            self.record(prefix + '/host.yaml', self.hosts[role])
            self.record(prefix + '/result.yaml', self.results[role])


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='incremental-contract-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.f = Records(self.root)
        self.f.review('b001')
        self.f.call('development')
        self.f.deliver('development', 'ready')

    def check(self, role='development', index=-1):
        f = self.f
        validate_handoff(self.root, f.status, f.tasks[role], f.hosts[role], f.results[role], f.results[role]['deliveries'][index])

    def test_three_increments_failure_retry_counts_and_old_bytes(self):
        f = self.f
        original = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file() and 'documents' not in p.parts}
        for n in [2, 3, 4]:
            with (self.root / f.input).open('a') as out:
                out.write(f'input-{n}: add related scope\n')
            f.status['pending_inputs'] = [f'input-{n}']
            f.status['acceptance_ids'].append(f'AC-{n}')
            f.review(f'b{n:03}')
            f.call('development'); f.deliver('development', 'ready'); self.check()
        f.call('testing'); failed = f.deliver('testing', 'failed'); self.check('testing')
        frozen_failed = copy.deepcopy(failed)
        f.status['development_attempt'] = 2  # real repair after independent failure
        f.call('development'); f.deliver('development', 'ready'); self.check()
        f.call('testing'); f.deliver('testing', 'passed'); self.check('testing')
        f.persist()
        for path, raw in original.items():
            if path != Path(f.input) and path.name not in ('task.yaml', 'host.yaml', 'result.yaml'):
                self.assertEqual((self.root / path).read_bytes(), raw)
        self.assertEqual(f.results['testing']['deliveries'][0], frozen_failed)
        self.assertEqual(len(list((self.root / 'revisions').iterdir())), 1)
        self.assertEqual(len(list((self.root / 'revisions/v1/.workflow/tasks').iterdir())), 3)
        self.assertFalse(list(self.root.rglob('status.snapshot.yaml')))
        self.assertFalse(list(self.root.rglob('runs')))
        files = [p for p in self.root.rglob('*') if p.is_file()]
        # 1 status + input/config/current doc + 3*3 task/host/result + 4*3 review + 11 actual docs.
        self.assertEqual(len(files), 36)
        print(json.dumps(dict(scope='STATIC synthetic files; NOT native/human approval', revisions=1,
            tasks=3, baselines=4, invocations=11, deliveries=11, review_files=12,
            immutable_delivery_docs=11, persistent_files=len(files), attempts=2)))

    def test_missing_review_source_rejected(self):
        # Remove the real candidate to prove a manifest reference is insufficient.
        prefix = 'revisions/v1/.workflow/tasks/product'
        self.f.record(prefix + '/task.yaml', self.f.tasks['product'])
        self.f.record(prefix + '/host.yaml', self.f.hosts['product'])
        self.f.record(prefix + '/result.yaml', dict(self.f.results['product'], deliveries=[]))
        with self.assertRaisesRegex(ValueError, 'review source'):
            validate_review(self.root, self.f.status)

    def test_same_baseline_old_delivery_without_active_call_rejected(self):
        f = self.f
        f.call('development'); f.deliver('development', 'ready')
        f.status['active_run'] = None
        with self.assertRaisesRegex(ValueError, 'late invocation|current handoff'):
            self.check(index=0)

    def test_standalone_bug_review_without_product_task(self):
        f = self.f
        # A standalone entry has no product task or records at all.
        for records in (f.tasks, f.hosts, f.results):
            del records['product']
        import shutil
        shutil.rmtree(self.root / 'revisions/v1/.workflow/tasks/product')
        f.review('b002', kind='bug-boundary')
        validate_review(self.root, f.status)
        self.assertFalse((self.root / 'revisions/v1/.workflow/tasks/product').exists())
        manifest = read_record(self.root, 'revisions/v1/.workflow/reviews/b002/review-manifest.yaml')
        self.assertEqual(manifest['source_delivery'], dict(task_id='bug', delivery_id='d001'))
        self.assertNotIn('product_delivery', manifest)

    def test_review_source_role_status_identity_input_and_content_rejected(self):
        f = self.f
        f.review('b002', kind='bug-boundary')
        prefix = 'revisions/v1/.workflow/tasks/bug'
        original = copy.deepcopy(f.results['bug'])
        for mutation in ['role', 'status', 'identity', 'input', 'artifact', 'delivery', 'artifact_kind']:
            with self.subTest(mutation=mutation):
                result = copy.deepcopy(original)
                delivery = result['deliveries'][0]
                if mutation == 'role': result['role'] = 'product'
                if mutation == 'status': delivery['status'] = 'ready'
                if mutation == 'identity': result['feature_id'] = 'another-feature'
                if mutation == 'input': delivery['input_sha256'] = '0' * 64
                if mutation == 'artifact': delivery['artifacts'][0]['sha256'] = '0' * 64
                if mutation == 'delivery': delivery['id'] = 'd999'
                if mutation == 'artifact_kind': delivery['artifacts'][0]['kind'] = 'requirements'
                f.record(prefix + '/result.yaml', result)
                with self.assertRaisesRegex(ValueError, 'review source'):
                    validate_review(self.root, f.status)
        f.record(prefix + '/result.yaml', original)
        a = original['deliveries'][0]['artifacts'][0]
        ordinary(self.root, f.tasks['bug']['output_dir'] + '/' + a['path']).write_text('drift')
        with self.assertRaisesRegex(ValueError, 'review source content'):
            validate_review(self.root, f.status)

    def test_current_handoff_and_consumed_repeat_are_distinct(self):
        f = self.f
        d = f.results['development']['deliveries'][0]
        evidence = f.write(f.tasks['development']['output_dir'] + '/d001/check.log', 'real fixture evidence')
        d['artifacts'].append(dict(kind='evidence', path='d001/check.log', sha256=evidence['sha256']))
        args = (self.root, f.status, f.tasks['development'], f.hosts['development'], f.results['development'], d)
        self.assertEqual(validate_handoff(*args), 'advance')
        # Root indexes formal documents; internal evidence need not be duplicated there.
        f.status['artifacts'] = [dict(task_id='development', delivery_id=d['id'], **d['artifacts'][0])]
        f.status['active_run'] = None
        before = copy.deepcopy(f.status)
        self.assertEqual(validate_handoff(*args), 'already_consumed')
        self.assertEqual(f.status, before)
        f.status['artifacts'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'current handoff'):
            validate_handoff(*args)

    def test_consumed_old_delivery_cannot_advance_later_same_baseline(self):
        f = self.f
        d = f.results['development']['deliveries'][0]
        f.status['artifacts'] = [dict(task_id='development', delivery_id=d['id'], **a) for a in d['artifacts']]
        f.call('development'); f.deliver('development', 'ready')
        f.status['active_run'] = None
        with self.assertRaisesRegex(ValueError, 'late invocation'):
            self.check(index=0)

    def test_interrupted_handoff_requires_exact_recovery_evidence(self):
        f = self.f
        d = f.results['development']['deliveries'][0]
        call = f.hosts['development']['invocations'][0]
        f.status['active_run'] = None
        recovery = dict(task_id='development', invocation_id=call['id'], delivery_id=d['id'],
            baseline_id=d['baseline_id'], approval_digest=d['approval_digest'],
            input_sha256=d['input_sha256'], end_evidence=call['end_evidence'])
        args = (self.root, f.status, f.tasks['development'], f.hosts['development'], f.results['development'], d)
        with self.assertRaisesRegex(ValueError, 'current handoff'):
            validate_handoff(*args)
        self.assertEqual(validate_handoff(*args, recovery=recovery), 'advance')
        for field in recovery:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'current handoff'):
                validate_handoff(*args, recovery=dict(recovery, **{field: 'wrong'}))
        f.call('development')
        with self.assertRaisesRegex(ValueError, 'late invocation'):
            validate_handoff(*args, recovery=recovery)

    def test_old_approval_cannot_authorize_new_scope(self):
        self.f.review('b002')
        with self.assertRaisesRegex(ValueError, 'old write approval'): self.check()

    def test_old_passed_cannot_complete_new_baseline(self):
        f = self.f
        f.call('testing'); f.deliver('testing', 'passed')
        f.review('b002')
        with self.assertRaisesRegex(ValueError, 'old write approval'): self.check('testing')

    def test_unknown_or_running_reinvoke_rejected(self):
        for state in ['unknown', 'running']:
            f = copy.deepcopy(self.f)
            f.hosts['development']['invocations'][0]['status'] = state
            i = f.call('development')
            with self.assertRaisesRegex(ValueError, 'previous active call'):
                validate_dispatch(self.root, f.status, f.tasks['development'], f.hosts['development'], i)

    def test_new_input_or_late_ready_never_clears_state(self):
        f = self.f
        f.status.update(pending_inputs=['unhandled new scope'], active_run=dict(invocation_id='i002'))
        before = copy.deepcopy(f.status)
        with self.assertRaisesRegex(ValueError, 'pending scope'): self.check()
        self.assertEqual(f.status, before)
        f.status['pending_inputs'] = []
        with self.assertRaisesRegex(ValueError, 'late invocation'): self.check()

    def test_approval_or_manifest_content_tamper_rejected(self):
        path = self.root / 'revisions/v1/.workflow/reviews/b001/requirements.md'
        path.write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'review content'): self.check()

    def test_formal_user_edit_and_interrupted_approval_rejected(self):
        path = self.root / 'revisions/v1/documents/requirements.md'
        raw = path.read_bytes(); path.write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'formal conflict'): self.check()
        path.write_bytes(raw)
        (self.root / 'revisions/v1/.workflow/reviews/b001/approval.yaml').unlink()
        with self.assertRaisesRegex(ValueError, 'missing file'): self.check()

    def test_source_snapshot_change_and_boundary_review(self):
        f = self.f
        source = f.write('revisions/v1/.workflow/sources/remote-001.md', 'external original')
        f.review('b002', sources=[source], kind='bug-boundary')
        validate_review(self.root, f.status)
        ordinary(self.root, source['path']).write_text('remote overwrite')
        with self.assertRaisesRegex(ValueError, 'review content'): validate_review(self.root, f.status)

    def test_old_development_or_partial_acceptance_rejected(self):
        f = self.f; f.call('testing'); d = f.deliver('testing', 'passed')
        d['source_delivery']['delivery_id'] = 'd999'
        with self.assertRaisesRegex(ValueError, 'old source delivery'): self.check('testing')
        d['source_delivery']['delivery_id'] = 'd001'
        d['acceptance_ids'] = []
        with self.assertRaisesRegex(ValueError, 'incomplete acceptance'): self.check('testing')

    def test_limit_never_resets_on_review(self):
        f = self.f
        f.status['development_attempt'] = 3
        f.review('b002')
        self.assertEqual((f.status['development_attempt'], f.status['max_development_attempts']), (3, 3))
        i = f.call('development')
        with self.assertRaisesRegex(ValueError, 'attempt limit'):
            validate_dispatch(self.root, f.status, f.tasks['development'], f.hosts['development'], i, new_scope=True)

    def test_input_prefix_history_edit_and_delivery_baseline_rejected(self):
        f = self.f
        with (self.root / f.input).open('a') as out: out.write('handled processing marker\n')
        self.check()  # append-only marker does not cause endless reruns
        ordinary(self.root, f.input).write_text('rewrote historical input')
        with self.assertRaisesRegex(ValueError, 'input prefix'): self.check()

    def test_legacy_layout_never_adopted(self):
        f = self.f; f.tasks['development']['layout_version'] = 3
        before = copy.deepcopy(f.tasks['development'])
        with self.assertRaisesRegex(ValueError, 'protocol/layout'): self.check()
        self.assertEqual(f.tasks['development'], before)

    def test_archive_symlink_rejected(self):
        p = self.root / 'revisions/v1/.workflow/reviews/b001/requirements.md'
        other = self.root / 'outside.md'; other.write_bytes(p.read_bytes()); p.unlink(); p.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.check()

    def test_new_configuration_is_bound_only_to_new_authorization(self):
        f = self.f
        original_config = copy.deepcopy(f.tasks['development']['effective_config'])
        original_auth = copy.deepcopy(f.tasks['development']['authorizations'][0])
        f.config = 'revisions/v1/.workflow/snapshots/config-002.yaml'
        new_config = f.write(f.config, 'provider: local\nsource: new\n')
        f.review('b002')
        i = f.call('development')
        with self.assertRaisesRegex(ValueError, 'call configuration binding'):
            validate_dispatch(self.root, f.status, f.tasks['development'], f.hosts['development'], i)
        f.tasks['development']['authorizations'][-1]['effective_config'] = new_config
        validate_dispatch(self.root, f.status, f.tasks['development'], f.hosts['development'], i)
        self.assertEqual(f.tasks['development']['effective_config'], original_config)
        self.assertEqual(f.tasks['development']['authorizations'][0], original_auth)

    def test_installed_entry_rule_lookup_survives_clone(self):
        import re
        import shutil
        entry = (ROOT / 'skills/setup-requirement-workflow/assets/templates/project-entry-light.md').read_text()
        package_sha = 'a' * 64
        fresh = self.root / 'fresh-project'
        cache_relative = f'.agents/requirement-workflow-cache/{package_sha}'
        fresh.mkdir()
        (fresh / 'AGENTS.md').write_text(entry)
        (fresh / 'workflow.lock.yaml').write_text(yaml.safe_dump(dict(package=dict(sha256=package_sha))))
        # Materialize real rule bytes only in the locked cache, not at project root.
        for relative in ['workflow/package.md', 'workflow/bootstrap.md']:
            dest = fresh / cache_relative / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / relative).read_bytes())
        clone = self.root / 'relocated-clone'
        shutil.copytree(fresh, clone, ignore=shutil.ignore_patterns('.agents'))
        self.assertFalse((clone / '.agents').exists())
        shutil.copytree(fresh / '.agents', clone / '.agents')
        for project in [fresh, clone]:
            text = (project / 'AGENTS.md').read_text()
            links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)
            self.assertFalse([x for x in links if x.startswith('workflow/')],
                             'installed entry must not resolve package rules at project root')
            self.assertIn('以下路径均相对于已核验的锁定缓存根', text)
            if yaml.safe_load((ROOT / 'framework.yaml').read_bytes())['protocol_version'] == 3:
                self.assertLess(text.index('独立一次性'), text.index('需要上述框架能力时'))
                self.assertIn('无需读取workflow.lock.yaml、检查缓存', text)
                self.assertIn('已有旧任务仍按原锁原包续接', text)
            lock = yaml.safe_load((project / 'workflow.lock.yaml').read_bytes())
            cache = project / '.agents/requirement-workflow-cache' / lock['package']['sha256']
            for relative in ['workflow/package.md', 'workflow/bootstrap.md']:
                self.assertIn('`' + relative + '`', text)
                self.assertEqual((cache / relative).read_bytes(), (ROOT / relative).read_bytes())
                self.assertFalse((project / relative).exists())

    def test_approval_type_matches_review_kind(self):
        f = self.f
        for kind in ['requirements', 'bug-boundary']:
            f.review('b002' if kind == 'requirements' else 'b003', kind=kind)
            bid = f.status['content_baseline']
            original = copy.deepcopy(f.status['approval'])
            for value in [None, 'requirements', 'bug_boundary', 'unknown']:
                with self.subTest(kind=kind, approval_type=value):
                    approval = copy.deepcopy(original)
                    approval.pop('type', None)
                    if value is not None: approval['type'] = value
                    f.record(f'revisions/v1/.workflow/reviews/{bid}/approval.yaml', approval)
                    f.status['approval'] = approval
                    allowed = value == 'bug_boundary' if kind == 'bug-boundary' else value in (None, 'requirements')
                    if allowed:
                        validate_review(self.root, f.status)
                    else:
                        with self.assertRaisesRegex(ValueError, 'approval type'):
                            validate_review(self.root, f.status)

    def test_standalone_routes_in_all_increment_stages(self):
        if yaml.safe_load((ROOT / 'framework.yaml').read_text())['protocol_version'] == 3:
            route = (ROOT / 'workflow/routing.md').read_text()
            revisions = (ROOT / 'workflow/revisions.md').read_text()
            execution = (ROOT / 'workflow/execution-contract.md').read_text()
            self.assertIn('目标明确的小修由当前会话直接定位', route)
            self.assertIn('无需先建文档、清单、原生任务或派其他角色', route)
            self.assertNotIn('接单先读当前事项的任务文档', route)
            self.assertIn('角色不是强制阶段链', route)
            self.assertIn('补充、修改验收、修复、重试、普通继续与完成后续改', revisions)
            self.assertIn('只有独立目标才新建事项', revisions)
            self.assertIn('未知不等于结束', execution)
            self.assertIn('旧锁/旧任务', revisions)
            return
        contract = (ROOT / 'workflow/incremental-changes.md').read_text()
        rows = [line for line in contract.splitlines() if line.startswith('| 同目标未完成')]
        for stage in ['draft', 'requirement_review', 'development', 'testing']:
            with self.subTest(stage=stage):
                row = next(row for row in rows if stage in row)
                self.assertIn('原product', row)
                self.assertIn('独立Bug', row)
                self.assertIn('原bug boundary', row)
        self.assertIn('workflow_kind=bugfix', contract)
        self.assertIn('bugfix.mode=standalone', contract)
        self.assertIn('unknown/查询不可靠保持blocked', contract)
        self.assertIn('真实ended或cancelled及结束证据', contract)

    def test_templates_and_reachable_instructions_agree(self):
        for name in ['status', 'role-task', 'product-task']:
            self.assertEqual(yaml.safe_load((ROOT / f'templates/{name}.yaml').read_bytes())['layout_version'], 4)
        framework = yaml.safe_load((ROOT / 'framework.yaml').read_bytes())
        if framework['protocol_version'] == 3:
            self.assertEqual(framework['version'], '0.6.0')
            lock = yaml.safe_load((ROOT / 'skills/setup-requirement-workflow/assets/templates/workflow.lock.yaml').read_bytes())
            self.assertEqual(lock['package']['protocol_version'], framework['protocol_version'])
            template = (ROOT / 'templates/task.md').read_text()
            for phrase in ('目标与范围', '- [ ]', '验证与未决项'):
                self.assertIn(phrase, template)
            for field in ('baseline_id', 'invocation_id', 'delivery_id', 'revision'):
                self.assertNotIn(field, template)
            contract = (ROOT / 'workflow/incremental-changes.md').read_text()
            self.assertIn('不建立baseline_id', contract)
            self.assertIn('不套用本条删改旧记录', contract)
            return
        self.assertEqual(yaml.safe_load((ROOT / 'framework.yaml').read_bytes())['version'], '0.5.0')
        for path in ['workflow/revisions.md', 'workflow/routing.md', 'workflow/documents.md',
                     'workflow/output-layout.md', 'workflow/handoff.md', 'workflow/execution-contract.md',
                     'workflow/bugfix.md', 'agents/coordinator-agent.md', 'skills/requirement-analysis/SKILL.md']:
            text = (ROOT / path).read_text()
            self.assertTrue('incremental-changes.md' in text or '修订规则' in text, path)
        contract = (ROOT / 'workflow/incremental-changes.md').read_text()
        for phrase in ['未知组合blocked', '不重用', '迟到', '本轮未重跑', 'source_baseline_id', '上限', '独立目标',
                       '未占用编号', '显示真实稿链接', '旧pending_review', '归属未知', '不复制task/host/result']:
            self.assertIn(phrase, contract)


if __name__ == '__main__':
    unittest.main()
