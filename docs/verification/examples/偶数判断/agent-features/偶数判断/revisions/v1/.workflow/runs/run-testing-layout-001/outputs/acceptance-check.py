from parity import is_even
import ast
from pathlib import Path

# Expected values independently derived from the approved acceptance criteria.
for value, expected in [(0, True), (2, True), (-2, True), (1, False), (-1, False), (10 ** 300, True), (-(10 ** 300 + 1), False)]:
    actual = is_even(value)
    assert type(actual) is bool and actual is expected, (value, expected, actual)
    print("AC-001", repr(value), "=>", repr(actual), "PASS")
for value in [True, False, 1.0, "2", None, [], {}, 2j]:
    try:
        is_even(value)
    except TypeError:
        print("AC-002", repr(value), "=> TypeError PASS")
    else:
        raise AssertionError((value, "expected TypeError"))
source = Path("parity.py").read_text()
tree = ast.parse(source)
assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
assert [n.name for n in tree.body if isinstance(n, ast.FunctionDef)] == ["is_even"]
assert all(isinstance(n, (ast.Expr, ast.FunctionDef)) for n in tree.body)
print("AC-003 static source inspection: pure function, no imports, CLI, network or third-party dependency PASS")
print("Independent acceptance: PASS")
