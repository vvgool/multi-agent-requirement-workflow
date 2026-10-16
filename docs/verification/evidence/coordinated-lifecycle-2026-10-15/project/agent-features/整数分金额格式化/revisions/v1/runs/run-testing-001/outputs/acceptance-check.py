import ast, json, random, sys
from pathlib import Path
p = Path(sys.argv[1])
sys.path.insert(0, str(p))
from amount import format_amount
results = []
def check(name, values):
    for value, expected in values:
        actual = format_amount(value)
        assert type(actual) is str and actual == expected, (name, actual, expected)
    results.append({"id": name, "status": "passed", "cases": len(values)})
def rejects(name, values, error):
    for value in values:
        try: format_amount(value)
        except error: pass
        else: raise AssertionError((name, type(value).__name__))
    results.append({"id": name, "status": "passed", "cases": len(values)})
check("AC-001", [(0,"0.00"),(1,"0.01"),(105,"1.05"),(10000,"100.00")])
check("AC-002", [(99,"0.99"),(100,"1.00"),(101,"1.01"),(123456789,"1234567.89")])
check("AC-003", [(9007199254740993,"90071992547409.93"),(10**100+1,"1"+"0"*98+".01")])
rejects("AC-004", [-1,-100,-10**100], ValueError)
rejects("AC-005", ["105",1.05,1.0,-1.0,None,True,False], TypeError)
source=(p/"amount.py").read_text(); tree=ast.parse(source)
assert not any(isinstance(n,(ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
assert not any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) for n in ast.walk(tree))
assert not any(isinstance(n, ast.Constant) and isinstance(n.value,float) for n in ast.walk(tree))
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {"float","eval","exec","open","__import__"} for n in ast.walk(tree))
assert callable(format_amount) and format_amount(105)=="1.05"
results.append({"id":"AC-006","status":"passed","actual":"-I -S stdlib-only interpreter, explicit local import and AST constraints passed"})
# Oracle uses a decimal digit string, independent of implementation divmod/chunks.
rng=random.Random(20261015); cases=[]
for digits in range(1,1001):
    text=str(rng.randrange(1,10))+"".join(str(rng.randrange(10)) for _ in range(digits-1))
    padded=text.zfill(3); cases.append((int(text),padded[:-2]+"."+padded[-2:]))
for exponent in [2,9,11,18,20,27,29,100,1000]:
    for offset in [-1,0,1]:
        value=10**exponent+offset; padded=str(value).zfill(3)
        cases.append((value,padded[:-2]+"."+padded[-2:]))
cases.extend([(10**5000+1,"1"+"0"*4998+".01"),(10**5000-1,"9"*4998+".99")])
check("REG-001", cases)
rejects("REG-002", [b"105",[],{},set(),object(),complex(1,0),float("nan"),float("inf")], TypeError)
print(json.dumps({"python":sys.version,"site_disabled":sys.flags.no_site,"isolated":sys.flags.isolated,"bytecode_disabled":sys.dont_write_bytecode,"results":results},indent=2))
