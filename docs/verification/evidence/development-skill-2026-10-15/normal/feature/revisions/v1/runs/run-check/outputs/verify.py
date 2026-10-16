from pathlib import Path
import sys, hashlib, json, platform
from datetime import datetime, timezone
root = Path(__file__).resolve().parents[6]
project = root / "project"
sys.dont_write_bytecode = True
sys.path.insert(0, str(project))
from shipping import shipping_fee
from checkout import checkout_total
rows = []
for n in [0, 1, 9999, 10000, 10001, 10**30]:
    expected = 1000 if n < 10000 else 0
    assert shipping_fee(n) == expected
    rows.append(f"shipping_fee({n})={expected}")
for n in [-1, -10000, -(10**30)]:
    try:
        shipping_fee(n)
    except ValueError:
        rows.append(f"shipping_fee({n}) raises ValueError")
    else:
        raise AssertionError(n)
rows.append("M1-T1 / V1 PASS")
for n in [0, 1, 9999, 10000, 10001, 10**30]:
    expected = n + (1000 if n < 10000 else 0)
    assert checkout_total(n) == expected
    rows.append(f"checkout_total({n})={expected}")
for n in [-1, -10000, -(10**30)]:
    try:
        checkout_total(n)
    except ValueError:
        rows.append(f"checkout_total({n}) raises ValueError")
    else:
        raise AssertionError(n)
for n in range(20001):
    expected = 1000 if n < 10000 else 0
    assert shipping_fee(n) == expected
    assert checkout_total(n) == n + expected
rows.append("M1-T2 / V2 PASS: exhaustive integer regression 0..20000")
files = {}
for name in ["checkout.py", "shipping.py"]:
    data = (project / name).read_bytes()
    compile(data, name, "exec")
    files[name] = hashlib.sha256(data).hexdigest()
baseline = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
result = {"id": "sha256:" + baseline, "files": files, "algorithm": "sha256 of sorted compact JSON path-to-sha256 mapping, UTF-8"}
Path(__file__).with_name("code-baseline.json").write_text(json.dumps(result, indent=2) + "\n")
rows.extend(["M1 / V3 PASS: both source files compile; real import integration passed", "baseline="+result["id"], "environment=" + platform.platform() + " Python " + platform.python_version(), "verified_at=" + datetime.now(timezone.utc).isoformat()])
text = "\n".join(rows) + "\n"
Path(__file__).with_name("verification.log").write_text(text)
print(text)
