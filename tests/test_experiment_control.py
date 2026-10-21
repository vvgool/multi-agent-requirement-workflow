#!/usr/bin/env python3
"""Offline regression cases; all fixture writes stay under --scratch-root."""
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from experiment_control import Rejected, compare, prepare
from package_digest import digest

SCRATCH_ROOT = None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


class ControlTests(unittest.TestCase):
    def setUp(self):
        if SCRATCH_ROOT is None:
            self.skipTest('Use this script with --scratch-root for explicitly authorized fixture writes')
        self.directory = tempfile.TemporaryDirectory(prefix='control-', dir=SCRATCH_ROOT)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.package = self.root / 'package'
        self.package.mkdir()
        files = {name: (name + '\n').encode() for name in
                 ['framework.yaml', 'AGENTS.md', 'README.md', 'workflow.yaml', 'LICENSE']}
        files.update({'agents/a.txt': b'A', 'agents/a/b.txt': b'B', 'skills/s': b'S',
                      'workflow/w': b'W', 'templates/t': b'T'})
        for name, data in files.items():
            p = self.package / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        # Independent manifest construction: explicit strings, not Path ordering.
        rows = [[name, sha(data)] for name, data in files.items()]
        rows.sort(key=lambda row: row[0])
        self.package_sha = sha(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode())
        self.prompt = self.root / 'prompt.txt'
        self.prompt.write_bytes(b'Fixed\nbody\n')
        self.expected_bindings = {
            'model': {'id': 'test/model', 'provider_id': 'offline', 'variant': 'fixed'},
            'role': 'requirement-development',
            'task': {'feature_id': 'fixture', 'revision': 4, 'run_id': 'development-001'},
            'approval': {'digest': sha(b'explicit approval')},
            'authorization': {'project_root': str(self.root), 'project_paths': ['label.py'],
                              'temporary_paths': [str(self.root / 'scratch')]}}
        self.policy = {'fields': ['workspace', 'task_file'],
                       'roots': [{'path': str(self.root / 'left'), 'label': 'project'},
                                 {'path': str(self.root / 'right'), 'label': 'project'}]}
        protected = {}
        for name in ['lock', 'task', 'approval', 'authorization']:
            path = self.root / (name + '.protected')
            path.write_bytes((name + '\n').encode())
            protected[name] = {'path': str(path), 'sha256': sha(path.read_bytes())}
        self.spec = {'schema_version': 1, 'package': {'root': str(self.package), 'sha256': self.package_sha},
                     'prompt': {'path': str(self.prompt), 'sha256': sha(self.prompt.read_bytes())},
                     'bindings': self.expected_bindings, 'protected_files': protected,
                     'path_policy': self.policy}
        self.actual = {'schema_version': 1, 'bindings': copy.deepcopy(self.expected_bindings),
                       'paths': {'workspace': str(self.root / 'left'),
                                 'task_file': str(self.root / 'left' / 'task.json')}}
        self.spec_path = self.root / 'spec.json'
        self.actual_path = self.root / 'actual.json'
        self.save()

    def save(self):
        write_json(self.spec_path, self.spec)
        write_json(self.actual_path, self.actual)

    def payload(self):
        return prepare(str(self.spec_path), str(self.actual_path))

    def assert_gate_closed(self, reason=None):
        calls = []
        def simulated_entry():
            payload = self.payload()
            calls.append(payload)
        with self.assertRaises(Rejected) as caught:
            simulated_entry()
        if reason:
            self.assertEqual(str(caught.exception), reason)
        self.assertEqual(calls, [])

    def body(self, payload, data):
        payload['body_base64'] = base64.b64encode(data).decode('ascii')
        payload['body_sha256'] = sha(data)
        return payload

    def test_posix_order_differs_from_path_component_order(self):
        paths = [p for p in self.package.rglob('*') if p.is_file()]
        wrong = [[p.relative_to(self.package).as_posix(), sha(p.read_bytes())] for p in sorted(paths)]
        wrong_sha = sha(json.dumps(wrong, ensure_ascii=False, separators=(',', ':')).encode())
        self.assertNotEqual(wrong_sha, self.package_sha)
        self.assertEqual(digest(self.package), {'file_count': 10, 'sha256': self.package_sha})
        self.assertEqual(digest(self.package), digest(self.package))

    def test_complete_gate_enters_once_without_network_and_payload_is_exact(self):
        calls = []
        with patch.object(socket, 'socket', side_effect=AssertionError('no network')):
            payload = self.payload()
            calls.append(payload)
        self.assertEqual(len(calls), 1)
        self.assertEqual(base64.b64decode(payload['body_base64']), self.prompt.read_bytes())
        self.assertEqual(payload['body_sha256'], self.spec['prompt']['sha256'])
        self.assertEqual(payload, self.payload())

    def test_package_content_change_is_blocked(self):
        (self.package / 'agents/a.txt').write_bytes(b'changed')
        self.assert_gate_closed('package_digest_mismatch')

    def test_package_extra_file_is_blocked(self):
        (self.package / 'agents/extra').write_bytes(b'extra')
        self.assert_gate_closed('package_digest_mismatch')

    def test_package_unknown_root_and_empty_extra_directory_are_blocked(self):
        p = self.package / 'extra'
        p.mkdir()
        self.assert_gate_closed('package_structure_invalid')
        p.rmdir()
        p.write_bytes(b'unknown')
        self.assert_gate_closed('package_structure_invalid')

    def test_package_missing_root_and_subtree_are_blocked(self):
        p = self.package / 'AGENTS.md'; old = p.read_bytes(); p.unlink()
        self.assert_gate_closed('package_structure_invalid')
        p.write_bytes(old)
        p = self.package / 'templates/t'; p.unlink(); p.parent.rmdir()
        self.assert_gate_closed('package_structure_invalid')

    def test_package_link_special_and_wrong_root_type_are_blocked(self):
        p = self.package / 'agents/a.txt'; p.unlink(); p.symlink_to(self.prompt)
        self.assert_gate_closed('package_structure_invalid')
        p.unlink(); os.mkfifo(p)
        self.assert_gate_closed('package_structure_invalid')
        self.spec['package']['root'] = str(self.prompt); self.save()
        self.assert_gate_closed('package_structure_invalid')

    def test_protected_objects_never_get_terminal_lf_exception(self):
        for name, item in self.spec['protected_files'].items():
            with self.subTest(name=name):
                p = Path(item['path']); old = p.read_bytes()
                p.write_bytes(old + b'\n')
                self.assert_gate_closed('protected_' + name + '_mismatch')
                p.write_bytes(old)

    def test_each_missing_binding_or_manifest_field_blocks(self):
        for field in ['model', 'role', 'task', 'approval', 'authorization']:
            with self.subTest(binding=field):
                original = self.actual['bindings'].pop(field); self.save()
                self.assert_gate_closed('invalid_bindings')
                self.actual['bindings'][field] = original
        self.save()
        for field in list(self.spec):
            with self.subTest(spec=field):
                original = self.spec.pop(field); self.save()
                self.assert_gate_closed('invalid_spec')
                self.spec[field] = original
        self.save()

    def test_model_role_task_approval_and_scope_differences_block(self):
        changes = [('model', 'id', 'other'), ('model', 'provider_id', 'other'),
                   ('model', 'variant', 'other'), ('task', 'feature_id', 'other'),
                   ('task', 'revision', 5), ('task', 'run_id', 'other'),
                   ('approval', 'digest', sha(b'other')),
                   ('authorization', 'project_paths', ['other.py']),
                   ('authorization', 'temporary_paths', [str(self.root / 'other')])]
        for category, field, value in changes:
            with self.subTest(category=category, field=field):
                self.actual['bindings'] = copy.deepcopy(self.expected_bindings)
                self.actual['bindings'][category][field] = value; self.save()
                self.assert_gate_closed('bindings_mismatch')
        self.actual['bindings'] = copy.deepcopy(self.expected_bindings)
        self.actual['bindings']['role'] += '\n'; self.save()
        self.assert_gate_closed('bindings_mismatch')

    def test_wrong_prompt_sha_and_source_change_block_without_using_old_payload(self):
        prior = self.payload()
        self.prompt.write_bytes(self.prompt.read_bytes() + b'\n')
        self.assert_gate_closed('prompt_digest_mismatch')
        self.assertNotEqual(base64.b64decode(prior['body_base64']), self.prompt.read_bytes())
        self.spec['prompt']['sha256'] = sha(self.prompt.read_bytes()); self.save()
        refreshed = self.payload()
        self.assertNotEqual(prior, refreshed)
        self.assertEqual(base64.b64decode(refreshed['body_base64']), self.prompt.read_bytes())

    def test_missing_unreadable_type_and_link_input_files_block(self):
        self.prompt.unlink(); self.assert_gate_closed('file_unreadable')
        self.prompt.mkdir(); self.assert_gate_closed('file_not_regular')
        self.prompt.rmdir(); self.prompt.symlink_to(self.actual_path)
        self.assert_gate_closed('path_link')

    def test_duplicate_json_keys_and_invalid_types_block(self):
        self.actual_path.write_bytes(b'{"schema_version":1,"schema_version":1}')
        self.assert_gate_closed('duplicate_json_key')
        self.actual['bindings']['task']['revision'] = True; self.save()
        self.assert_gate_closed('invalid_task')
        self.actual['bindings']['task']['revision'] = 4
        self.actual['bindings']['model']['variant'] = ''; self.save()
        self.assert_gate_closed('invalid_model')

    def test_declared_path_fields_and_single_lf_bidirectional(self):
        a = self.payload(); b = copy.deepcopy(a)
        b['paths'] = {k: v.replace('/left', '/right') for k, v in b['paths'].items()}
        self.body(a, b'fixed body'); self.body(b, b'fixed body\n')
        for x, y in [(a, b), (b, a)]:
            self.assertEqual(compare(x, y, self.policy), {'equivalent': True, 'reason': 'single_terminal_lf'})
        self.body(b, b'fixed body')
        self.assertTrue(compare(a, b, self.policy)['equivalent'])

    def test_whitespace_and_body_differences_are_never_normalized(self):
        a = self.body(self.payload(), b'A\nB')
        for bad in [b'A\nB\n\n', b'A\nB\r\n', b'A\nB ', b' A\nB', b'A B',
                    b'A\r\nB', b'A\nB\xc2\xa0', b'A\nC']:
            with self.subTest(body=bad):
                b = self.body(copy.deepcopy(a), bad)
                self.assertFalse(compare(a, b, self.policy)['equivalent'])
                self.assertFalse(compare(b, a, self.policy)['equivalent'])
        self.body(a, b'A\n')
        b = self.body(copy.deepcopy(a), b'A\n\n')
        self.assertFalse(compare(a, b, self.policy)['equivalent'])
        self.body(a, b'A\r'); self.body(b, b'A\r\n')
        self.assertFalse(compare(a, b, self.policy)['equivalent'])

    def test_body_paths_are_not_globally_replaced(self):
        a = self.body(self.payload(), str(self.root / 'left').encode())
        b = self.body(copy.deepcopy(a), str(self.root / 'right').encode())
        b['paths'] = {k: v.replace('/left', '/right') for k, v in b['paths'].items()}
        self.assertFalse(compare(a, b, self.policy)['equivalent'])

    def test_protected_envelope_fields_are_strict_even_with_allowed_body_lf(self):
        a = self.body(self.payload(), b'body')
        for field in ['bindings', 'protected_sha256', 'package_sha256']:
            b = self.body(copy.deepcopy(a), b'body\n')
            if field == 'bindings': b['bindings']['task']['run_id'] += '\n'
            elif field == 'protected_sha256': b[field]['approval'] = sha(b'other')
            else: b[field] = sha(b'other')
            self.assertEqual(compare(a, b, self.policy), {'equivalent': False, 'reason': field + '_difference'})

    def test_undeclared_unknown_overlapping_and_traversal_paths_reject(self):
        a = self.payload()
        for path in [str(self.root / 'unknown'), str(self.root / 'leftover'),
                     str(self.root / 'left') + '/../right', str(self.root / 'left') + '//file']:
            b = copy.deepcopy(a); b['paths']['workspace'] = path
            with self.subTest(path=path), self.assertRaises(Rejected): compare(a, b, self.policy)
        b = copy.deepcopy(a); b['paths']['extra'] = str(self.root / 'left')
        with self.assertRaisesRegex(Rejected, 'undeclared_or_missing'): compare(a, b, self.policy)
        for extra in [self.policy['roots'][0], {'path': str(self.root / 'left' / 'nested'), 'label': 'project'}]:
            p = copy.deepcopy(self.policy); p['roots'].append(extra)
            with self.assertRaisesRegex(Rejected, 'overlapping'): compare(a, a, p)
        bad = copy.deepcopy(self.policy); bad['fields'].append('workspace')
        with self.assertRaisesRegex(Rejected, 'duplicate_path_field'): compare(a, a, bad)

    def test_path_symlink_escape_and_source_link_parent_are_rejected(self):
        (self.root / 'left').mkdir(); (self.root / 'right').mkdir()
        (self.root / 'left' / 'escape').symlink_to(self.root / 'right', target_is_directory=True)
        self.actual['paths']['task_file'] = str(self.root / 'left' / 'escape' / 'file'); self.save()
        self.assert_gate_closed('path_link')

    def test_invalid_envelope_digest_and_unknown_fields_reject(self):
        a = self.payload(); b = copy.deepcopy(a); b['body_base64'] = 'not base64!'
        with self.assertRaisesRegex(Rejected, 'invalid_body_base64'): compare(a, b, self.policy)
        b = copy.deepcopy(a); b['body_sha256'] = sha(b'other')
        with self.assertRaisesRegex(Rejected, 'body_digest_mismatch'): compare(a, b, self.policy)
        b = copy.deepcopy(a); b['extra'] = 1
        with self.assertRaisesRegex(Rejected, 'invalid_envelope'): compare(a, b, self.policy)

    def test_cli_emits_payload_only_after_preflight_and_clear_failure_without_body(self):
        command = [sys.executable, '-B', str(SCRIPTS / 'experiment_control.py'), 'prepare',
                   '--spec', str(self.spec_path), '--actual', str(self.actual_path)]
        valid = subprocess.run(command, capture_output=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout), self.payload())
        self.prompt.write_bytes(b'SECRET_CHANGED_BODY')
        invalid = subprocess.run(command, capture_output=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, b'')
        self.assertEqual(json.loads(invalid.stderr), {'accepted': False, 'reason': 'prompt_digest_mismatch'})
        self.assertNotIn(b'SECRET', invalid.stderr)

    def test_cli_compare_reports_difference_offset_without_body(self):
        a = self.body(self.payload(), b'A secret'); b = self.body(copy.deepcopy(a), b'B secret')
        left = self.root / 'left.json'; right = self.root / 'right.json'; policy = self.root / 'policy.json'
        for p, value in [(left, a), (right, b), (policy, self.policy)]: write_json(p, value)
        r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'experiment_control.py'), 'compare',
                            '--policy', str(policy), '--left', str(left), '--right', str(right)], capture_output=True)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout), {'equivalent': False, 'reason': 'body_difference', 'byte_offset': 0})
        self.assertNotIn(b'secret', r.stdout + r.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch-root', type=Path, required=True)
    args, remainder = parser.parse_known_args()
    SCRATCH_ROOT = args.scratch_root
    if not SCRATCH_ROOT.is_dir() or SCRATCH_ROOT.is_symlink():
        parser.error('--scratch-root must be an existing ordinary authorized directory')
    unittest.main(argv=[sys.argv[0]] + remainder)
