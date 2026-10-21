"""Plan one owned Codex registry block. Pure bytes in/out; never writes files.

The setup Skill owns authorization, paths, package identity, pending and receipts.
Use Python 3.11 tomllib or an already available tomli; never install a dependency.
"""
import hashlib
import re

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

BEGIN = b'# requirement-workflow:codex-registry:begin\n'
END = b'# requirement-workflow:codex-registry:end\n'
NAMES = ('requirement_product', 'requirement_development', 'requirement_testing', 'requirement_bug')


class RegistryError(ValueError):
    pass


def _parse(raw):
    if tomllib is None:
        raise RegistryError('toml_parser_unavailable: use an existing reliable TOML parser')
    try:
        return tomllib.loads(raw.decode('utf-8'))
    except (UnicodeError, ValueError) as error:
        raise RegistryError('invalid_toml: ' + str(error)) from error


def _check_unowned(value):
    if isinstance(value, dict):
        if 'agents' in value:
            agents = value['agents']
            if not isinstance(agents, dict):
                raise RegistryError('config_conflict: agents must be a table')
            if agents.get('enabled') is False:
                raise RegistryError('agents_disabled')
            if any(name in agents for name in NAMES):
                raise RegistryError('role_conflict: existing native role declaration')
        for child in value.values():
            _check_unowned(child)
    elif isinstance(value, list):
        for child in value:
            _check_unowned(child)


def _span(raw):
    # Reject marker fragments, noncanonical markers and duplicate ownership claims.
    if raw.count(b'requirement-workflow:codex-registry:') != 2:
        raise RegistryError('adapter_modified: incomplete or duplicate registry markers')
    starts = list(re.finditer(rb'(?m)^' + re.escape(BEGIN), raw))
    ends = list(re.finditer(rb'(?m)^' + re.escape(END), raw))
    if len(starts) != 1 or len(ends) != 1 or ends[0].start() < starts[0].end():
        raise RegistryError('adapter_modified: noncanonical registry markers')
    return starts[0].start(), ends[0].end()


def merge(original, block, *, restore_only=False, previous_sha256=None):
    """Return proposed complete config bytes, preserving all unowned bytes.

    previous_sha256 is the verified receipt's old block digest, required when a
    receipt exists. Without it, caller must prove fresh install or locked clone
    ownership. A differing old block may be replaced only for authorized upgrade.
    restore_only never adds or updates registration. Validate all target hosts
    before mutation; use whole-file before/after in the pending transaction.
    """
    _parse(original)
    if _span(block) != (0, len(block)):
        raise RegistryError('invalid_registry_template')
    expected = _parse(block)
    roles = expected.get('agents', {})
    if set(roles) != set(NAMES) or any(
        roles[n].get('config_file') != 'agents/' + n + '.toml' for n in NAMES
    ):
        raise RegistryError('invalid_registry_template')
    marker_present = b'requirement-workflow:codex-registry:' in original
    if marker_present:
        start, end = _span(original)
        owned = original[start:end]
        if previous_sha256 is not None and hashlib.sha256(owned).hexdigest() != previous_sha256:
            raise RegistryError('adapter_modified: owned digest differs from receipt')
        if owned != block and (restore_only or previous_sha256 is None):
            raise RegistryError('adapter_modified: block differs from locked template')
        remaining = original[:start] + original[end:]
        _check_unowned(_parse(remaining))
        candidate = original[:start] + block + original[end:]
    else:
        if previous_sha256 is not None:
            raise RegistryError('adapter_modified: receipt block missing')
        if restore_only:
            raise RegistryError('host_not_initialized: registry missing')
        _check_unowned(_parse(original))
        candidate = original + (b'\n' if original and not original.endswith(b'\n') else b'') + block
    parsed = _parse(candidate)
    if any(parsed.get('agents', {}).get(n) != roles[n] for n in NAMES):
        raise RegistryError('config_conflict: registry not active at TOML root')
    return candidate


def matches_plan(current, before, after):
    """Pending recovery must match the entire file, not only its owned block."""
    return current == before or current == after
