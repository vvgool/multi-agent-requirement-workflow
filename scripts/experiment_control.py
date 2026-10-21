#!/usr/bin/env python3
"""Offline fixed-prompt preparation/comparison. Never sends a model request."""
import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from package_digest import digest

PROTECTED = {'lock', 'task', 'approval', 'authorization'}
HEX = re.compile(r'[0-9a-f]{64}\Z')
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')


class Rejected(ValueError):
    """A failed local precondition; messages contain categories, not input data."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def keys(value, expected, reason):
    require(type(value) is dict and set(value) == set(expected), reason)


def text(value):
    return type(value) is str and bool(value)


def checksum(value):
    require(type(value) is str and HEX.fullmatch(value), 'invalid_sha256')
    return value


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def absolute(value):
    require(text(value) and value.startswith('/') and not value.startswith('//'), 'invalid_absolute_path')
    require(not any(p in {'.', '..'} for p in value.split('/')) and '\x00' not in value, 'path_traversal')
    p = Path(value)
    require(str(p) == value, 'noncanonical_path')
    # Never resolve() away a link. Nonexistent suffixes are allowed for declared output paths.
    for part in [*reversed(p.parents), p]:
        if os.path.lexists(part):
            require(not stat.S_ISLNK(part.lstat().st_mode), 'path_link')
    return p


def read_bytes(path):
    p = absolute(path)
    try:
        require(stat.S_ISREG(p.lstat().st_mode), 'file_not_regular')
        return p.read_bytes()
    except OSError as error:
        raise Rejected('file_unreadable') from error


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate_json_key')
        out[key] = value
    return out


def read_json(path):
    try:
        return json.loads(read_bytes(path), object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(Rejected('invalid_json_number')))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Rejected('invalid_json') from error


def bindings(value):
    keys(value, {'model', 'role', 'task', 'approval', 'authorization'}, 'invalid_bindings')
    model = value['model']
    keys(model, {'id', 'provider_id', 'variant'}, 'invalid_model')
    require(all(text(v) for v in model.values()), 'invalid_model')
    require(text(value['role']), 'invalid_role')
    task = value['task']
    keys(task, {'feature_id', 'revision', 'run_id'}, 'invalid_task')
    require(text(task['feature_id']) and text(task['run_id']) and
            type(task['revision']) is int and task['revision'] > 0, 'invalid_task')
    keys(value['approval'], {'digest'}, 'invalid_approval')
    checksum(value['approval']['digest'])
    scope = value['authorization']
    keys(scope, {'project_root', 'project_paths', 'temporary_paths'}, 'invalid_authorization')
    absolute(scope['project_root'])
    for name in ['project_paths', 'temporary_paths']:
        require(type(scope[name]) is list and all(type(p) is str for p in scope[name]), 'invalid_authorization')
        require(len(scope[name]) == len(set(scope[name])), 'invalid_authorization')
    require(scope['project_paths'] or scope['temporary_paths'], 'empty_authorization')
    for path in scope['project_paths']:
        require(text(path) and not path.startswith('/') and
                all(part not in {'.', '..'} for part in path.split('/')) and '\x00' not in path,
                'invalid_authorization_path')
    for path in scope['temporary_paths']:
        absolute(path)
    return value


def policy(value):
    keys(value, {'fields', 'roots'}, 'invalid_path_policy')
    fields = value['fields']
    require(type(fields) is list and fields and all(type(f) is str and NAME.fullmatch(f) for f in fields),
            'invalid_path_fields')
    require(len(fields) == len(set(fields)), 'duplicate_path_field')
    require(type(value['roots']) is list and value['roots'], 'missing_path_roots')
    roots = []
    for item in value['roots']:
        keys(item, {'path', 'label'}, 'invalid_path_root')
        require(type(item['label']) is str and NAME.fullmatch(item['label']), 'invalid_path_label')
        root = absolute(item['path'])
        require(root != Path('/'), 'unbounded_path_root')
        for previous, _ in roots:
            require(root != previous and root not in previous.parents and previous not in root.parents,
                    'overlapping_path_roots')
        roots.append((root, item['label']))
    return fields, roots


def mapped_paths(value, declared):
    fields, roots = declared
    keys(value, fields, 'undeclared_or_missing_path_field')
    result = {}
    for field in fields:
        path = absolute(value[field])
        matches = [(label, path.relative_to(root).as_posix()) for root, label in roots
                   if path == root or root in path.parents]
        require(len(matches) == 1, 'path_outside_policy')
        result[field] = matches[0]
    return result


def prepare(spec_path, actual_path):
    """Fresh verification on every call; trusted spec pins bytes, not runtime activation."""
    spec = read_json(spec_path)
    keys(spec, {'schema_version', 'package', 'prompt', 'bindings', 'protected_files', 'path_policy'}, 'invalid_spec')
    require(type(spec['schema_version']) is int and spec['schema_version'] == 1, 'invalid_schema')
    declared = policy(spec['path_policy'])
    expected = bindings(spec['bindings'])
    actual = read_json(actual_path)
    keys(actual, {'schema_version', 'bindings', 'paths'}, 'invalid_actual')
    require(type(actual['schema_version']) is int and actual['schema_version'] == 1, 'invalid_schema')
    observed = bindings(actual['bindings'])
    require(canonical(observed) == canonical(expected), 'bindings_mismatch')
    mapped_paths(actual['paths'], declared)
    keys(spec['protected_files'], PROTECTED, 'invalid_protected_files')
    verified = {}
    for name in sorted(PROTECTED):
        item = spec['protected_files'][name]
        keys(item, {'path', 'sha256'}, 'invalid_protected_file')
        require(sha(read_bytes(item['path'])) == checksum(item['sha256']), 'protected_' + name + '_mismatch')
        verified[name] = item['sha256']
    keys(spec['package'], {'root', 'sha256'}, 'invalid_package')
    root = absolute(spec['package']['root'])
    expected_sha = checksum(spec['package']['sha256'])
    try:
        package = digest(root)
    except (OSError, ValueError) as error:
        raise Rejected('package_structure_invalid') from error
    require(package['sha256'] == expected_sha, 'package_digest_mismatch')
    keys(spec['prompt'], {'path', 'sha256'}, 'invalid_prompt')
    body = read_bytes(spec['prompt']['path'])
    require(sha(body) == checksum(spec['prompt']['sha256']), 'prompt_digest_mismatch')
    return {'schema_version': 1, 'kind': 'fixed_prompt', 'bindings': observed,
            'protected_sha256': verified, 'package_sha256': expected_sha,
            'paths': actual['paths'], 'body_base64': base64.b64encode(body).decode('ascii'),
            'body_sha256': sha(body)}


def envelope(value, declared):
    keys(value, {'schema_version', 'kind', 'bindings', 'protected_sha256', 'package_sha256',
                 'paths', 'body_base64', 'body_sha256'}, 'invalid_envelope')
    require(type(value['schema_version']) is int and value['schema_version'] == 1 and
            value['kind'] == 'fixed_prompt', 'invalid_envelope')
    bindings(value['bindings'])
    keys(value['protected_sha256'], PROTECTED, 'invalid_protected_files')
    for item in value['protected_sha256'].values():
        checksum(item)
    checksum(value['package_sha256'])
    require(type(value['body_base64']) is str, 'invalid_body_base64')
    try:
        body = base64.b64decode(value['body_base64'], validate=True)
    except (ValueError, binascii.Error) as error:
        raise Rejected('invalid_body_base64') from error
    require(sha(body) == checksum(value['body_sha256']), 'body_digest_mismatch')
    return mapped_paths(value['paths'], declared), body


def compare(left, right, path_policy):
    """Only path fields map; all protected values are compared before prompt bytes."""
    declared = policy(path_policy)
    left_paths, a = envelope(left, declared)
    right_paths, b = envelope(right, declared)
    for key in ['bindings', 'protected_sha256', 'package_sha256']:
        if canonical(left[key]) != canonical(right[key]):
            return {'equivalent': False, 'reason': key + '_difference'}
    if left_paths != right_paths:
        return {'equivalent': False, 'reason': 'path_field_difference'}
    if a == b:
        return {'equivalent': True, 'reason': 'exact_after_declared_paths'}
    short, long = (a, b) if len(a) < len(b) else (b, a)
    if long == short + b'\n' and not short.endswith((b'\n', b'\r')):
        return {'equivalent': True, 'reason': 'single_terminal_lf'}
    offset = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return {'equivalent': False, 'reason': 'body_difference', 'byte_offset': offset}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Read and verify files; print a payload, never execute it')
    p.add_argument('--spec', required=True)
    p.add_argument('--actual', required=True)
    p = commands.add_parser('compare', help='Compare fixed-prompt envelopes under a predeclared path policy')
    p.add_argument('--policy', required=True)
    p.add_argument('--left', required=True)
    p.add_argument('--right', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.spec, args.actual)
        else:
            result = compare(read_json(args.left), read_json(args.right), read_json(args.policy))
        print(canonical(result))
        return 0 if result.get('equivalent', True) else 1
    except (Rejected, OSError, TypeError, ValueError) as error:
        reason = str(error) if isinstance(error, Rejected) else 'invalid_or_unreadable_input'
        print(canonical({'accepted': False, 'reason': reason}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
