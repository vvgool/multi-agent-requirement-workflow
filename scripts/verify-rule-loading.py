#!/usr/bin/env python3
"""Read-only source comparison, not a runtime, token meter or native acceptance.

Use --baseline-root for an independently verified pre-change package. No writes,
dependencies, network, role invocations or assumptions about model tokenization.
"""
import argparse
import json
from pathlib import Path
import re


def section(root, relative, title):
    text = (root / relative).read_bytes().decode("utf-8")
    headings = list(re.finditer(r"(?m)^(#{1,6}) (.+)\n", text))
    matches = [i for i, h in enumerate(headings) if h[2] == title]
    if len(matches) != 1:
        raise ValueError(f"expected unique section: {relative}#{title}")
    i = matches[0]
    end = next((h.start() for h in headings[i + 1:] if len(h[1]) <= len(headings[i][1])), len(text))
    return text[headings[i].start():end].encode("utf-8")


def measure(root, requests):
    total = 0
    for relative, title in requests:
        raw = section(root, relative, title) if title else (root / relative).read_bytes()
        total += len(raw)
    return {"rule_utf8_bytes": total, "selected_reads": len(requests),
            "distinct_files": len({p for p, _ in requests})}


def compare(baseline, candidate):
    contract = "workflow/execution-contract.md"
    layout = "workflow/output-layout.md"
    old_shared = section(baseline, layout, "共享成果与本机现场").decode().split("\n", 1)[1].strip()
    new_shared = section(candidate, contract, "共享文稿边界").decode().split("\n", 1)[1].strip()
    if old_shared != new_shared:
        raise ValueError("shared-document constraints changed rather than moved")
    compatibility = section(candidate, layout, "共享成果与本机现场")
    if b"execution-contract.md#" not in compatibility or "共享文稿边界".encode() not in compatibility:
        raise ValueError("compatibility anchor does not reach canonical document constraints")
    common = [(contract, title) for title in ("接单与授权", "路径与结果", "缓存与证据")]
    result = {}
    for role, skill in [("product", "requirement-analysis"), ("development", "feature-development"),
                        ("testing", "acceptance-testing")]:
        path = f"skills/{skill}/SKILL.md"
        text = (candidate / path).read_text(encoding="utf-8")
        if "../../workflow/output-layout.md#共享成果与本机现场" in text:
            raise ValueError(f"extra shared-document read still present: {path}")
        if "../../workflow/execution-contract.md" not in text:
            raise ValueError(f"required execution contract missing: {path}")
        before = measure(baseline, [(path, None)] + common + [(layout, "共享成果与本机现场")])
        after = measure(candidate, [(path, None)] + common)
        result[role] = {"before": before, "after": after}
    result["coordinator_compatibility"] = {
        "before": measure(baseline, [(layout, "共享成果与本机现场")]),
        "after": measure(candidate, [(layout, "共享成果与本机现场"), (contract, "共享文稿边界")])}
    result["total"] = {side: {key: sum(case[side][key] for case in result.values())
                              for key in ("rule_utf8_bytes", "selected_reads")}
                       for side in ("before", "after")}
    if result["total"]["after"]["rule_utf8_bytes"] >= result["total"]["before"]["rule_utf8_bytes"]:
        raise ValueError("no net rule input reduction including coordinator compatibility")
    result["boundary"] = ("same full stage Skills + mandatory contract sections + shared-document read; "
                          "coordinator compatibility included; business input and other unchanged rules omitted equally; "
                          "selected_reads are file/section reads, NOT host tool calls or tokens")
    result["tokens"] = "no comparable measured tokens"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline_root.resolve(), args.source_root.resolve()), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
