from pathlib import Path
import re

feature = Path(__file__).resolve().parents[6]
formal = feature / "revisions/v1/documents/development.md"
run = Path(__file__).resolve().parent.parent
candidate = run.parent / "run-development-layout-001/outputs/development.md"
for doc in [formal, candidate]:
    links = list(dict.fromkeys(re.findall(r"\]\(([^)]+)\)", doc.read_text())))
    assert len(links) == 3, (doc, links)
    for link in links:
        assert not Path(link).is_absolute(), link
        target = (doc.parent / link).resolve(strict=True)
        assert target.is_file(), target
        target.read_bytes()
        print("READABLE", doc, link, "=>", target)
print("B-001 regression: PASS; 3 formal and 3 candidate links readable")
