#!/usr/bin/env python3
"""Read-only digest of a strict installed workflow package; Python stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

ROOT_FILES = {'framework.yaml', 'AGENTS.md', 'README.md', 'workflow.yaml'}
ROOT_DIRS = {'agents', 'skills', 'workflow', 'templates'}


def digest(root):
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError('package root must be an ordinary directory')
    rows = []
    names = {p.name for p in root.iterdir()}
    missing = (ROOT_FILES | ROOT_DIRS) - names
    extra = names - ROOT_FILES - ROOT_DIRS - {'LICENSE'}
    if missing or extra:
        raise ValueError(f'missing={sorted(missing)}, extra={sorted(extra)}')

    def visit(path):
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            rows.append([path.relative_to(root).as_posix(),
                         hashlib.sha256(path.read_bytes()).hexdigest()])
        elif stat.S_ISDIR(mode):
            for child in path.iterdir():
                visit(child)
        else:
            raise ValueError(f'link or special file rejected: {path}')

    for name in names:
        path = root / name
        mode = path.lstat().st_mode
        expected = stat.S_ISDIR if name in ROOT_DIRS else stat.S_ISREG
        if not expected(mode):
            raise ValueError(f'unexpected package entry type: {path}')
        visit(path)
    # Sort the completed POSIX strings, never Path objects/components.
    rows.sort(key=lambda row: row[0])
    payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return {'file_count': len(rows), 'sha256': hashlib.sha256(payload).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package_root', type=Path)
    parser.add_argument('expected_sha256')
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{64}', args.expected_sha256):
        parser.error('expected_sha256 must be 64 lowercase hex characters')
    try:
        result = digest(args.package_root)
        result['matches_expected'] = result['sha256'] == args.expected_sha256
        print(json.dumps(result, separators=(',', ':')))
        return 0 if result['matches_expected'] else 1
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
