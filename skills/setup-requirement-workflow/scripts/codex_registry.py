"""Plan one owned Codex registry block. Pure bytes in/out; never writes files."""
import hashlib, re

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


def _req(ok, err):
    if not ok:
        raise RegistryError(err)


def _parse(raw):
    _req(tomllib is not None, 'toml_parser_unavailable: use an existing reliable TOML parser')
    try:
        return tomllib.loads(raw.decode('utf-8'))
    except (UnicodeError, ValueError) as err:
        raise RegistryError('invalid_toml: ' + str(err)) from err


def _check_unowned(v):
    if isinstance(v, dict):
        if 'agents' in v:
            ag = v['agents']
            _req(isinstance(ag, dict), 'config_conflict: agents must be a table')
            _req(ag.get('enabled') is not False, 'agents_disabled')
            _req(not any(n in ag for n in NAMES), 'role_conflict: existing native role declaration')
        for c in v.values():
            _check_unowned(c)
    elif isinstance(v, list):
        for c in v:
            _check_unowned(c)


def _span(raw):
    _req(raw.count(b'requirement-workflow:codex-registry:') == 2, 'adapter_modified: incomplete or duplicate registry markers')
    s = list(re.finditer(rb'(?m)^' + re.escape(BEGIN), raw))
    e = list(re.finditer(rb'(?m)^' + re.escape(END), raw))
    _req(len(s) == 1 and len(e) == 1 and e[0].start() >= s[0].end(), 'adapter_modified: noncanonical registry markers')
    return s[0].start(), e[0].end()


def merge(original, block, *, restore_only=False, previous_sha256=None):
    _parse(original)
    _req(_span(block) == (0, len(block)), 'invalid_registry_template')
    roles = _parse(block).get('agents', {})
    _req(set(roles) == set(NAMES) and all(roles[n].get('config_file') == f'agents/{n}.toml' for n in NAMES), 'invalid_registry_template')
    if b'requirement-workflow:codex-registry:' in original:
        s, e = _span(original)
        owned = original[s:e]
        _req(previous_sha256 is None or hashlib.sha256(owned).hexdigest() == previous_sha256, 'adapter_modified: owned digest differs from receipt')
        _req(owned == block or (not restore_only and previous_sha256 is not None), 'adapter_modified: block differs from locked template')
        _check_unowned(_parse(original[:s] + original[e:]))
        cand = original[:s] + block + original[e:]
    else:
        _req(previous_sha256 is None, 'adapter_modified: receipt block missing')
        _req(not restore_only, 'host_not_initialized: registry missing')
        _check_unowned(_parse(original))
        cand = original + (b'\n' if original and not original.endswith(b'\n') else b'') + block
    parsed = _parse(cand)
    _req(all(parsed.get('agents', {}).get(n) == roles[n] for n in NAMES), 'config_conflict: registry not active at TOML root')
    return cand


def matches_plan(current, before, after):
    return current == before or current == after
