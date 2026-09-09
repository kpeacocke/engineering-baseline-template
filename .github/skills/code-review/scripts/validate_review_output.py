#!/usr/bin/env python3
"""Validate the structural output contract produced by the code-review skill."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADINGS = [
    "## Decision",
    "## Risk summary",
    "## Findings",
    "## Verification evidence",
    "## Most important thing you may be missing",
    "## Three high-leverage things you did not ask for",
]
ACTION_HEADINGS = ["## Changes made", "## Residual risk"]
DECISIONS = {"APPROVE", "APPROVE WITH FOLLOW-UPS", "REQUEST CHANGES", "INCOMPLETE"}


def validate(path: Path, action_mode: bool = False) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read review output: {exc}"]

    errors: list[str] = []
    positions: list[int] = []
    for heading in HEADINGS + (ACTION_HEADINGS if action_mode else []):
        pos = text.find(heading)
        if pos < 0:
            errors.append(f"missing section: {heading}")
        positions.append(pos)
    if not errors and positions != sorted(positions):
        errors.append("sections are not in required order")

    m = re.search(r"(?ms)^## Decision\s*\n+\s*\*\*(.+?)\*\*", text)
    if not m or m.group(1).strip() not in DECISIONS:
        errors.append("Decision must contain one allowed merge decision in bold")

    findings = re.search(r"(?ms)^## Findings\s*\n(.*?)(?=^## Verification evidence)", text)
    if findings and "No material findings" not in findings.group(1):
        for term in ["Severity:", "Confidence:", "Evidence:", "Impact:", "Fix:", "Verify:"]:
            if term not in findings.group(1):
                errors.append(f"finding missing required field: {term}")

    follow = re.search(
        r"(?ms)^## Three high-leverage things you did not ask for\s*\n(.*?)(?=^## Changes made|^## Residual risk|\Z)",
        text,
    )
    if follow:
        items = re.findall(r"(?m)^([123])\.\s+", follow.group(1))
        if items != ["1", "2", "3"]:
            errors.append(f"follow-up section must contain exactly ranked items 1,2,3; got {items}")
        offers = re.findall(r"(?mi)\b(?:I can|can execute|can add|can run|can build|can do)\b", follow.group(1))
        if len(offers) < 3:
            errors.append("each high-leverage follow-up must include an execution offer")

    evidence = re.search(r"(?ms)^## Verification evidence\s*\n(.*?)(?=^## Most important thing)", text)
    if evidence:
        if "exit" not in evidence.group(1).casefold() and "not run" not in evidence.group(1).casefold():
            errors.append("verification evidence must record exit/status or explicitly state checks not run")

    return errors


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate Markdown produced by the code-review skill against its output contract."
    )
    p.add_argument("path", type=Path, help="review-output Markdown file to validate")
    p.add_argument(
        "--action-mode",
        action="store_true",
        help="also require the action-mode Changes made and Residual risk sections",
    )
    return p


def main() -> int:
    args = parser().parse_args()
    errors = validate(args.path, args.action_mode)
    if errors:
        print(f"FAIL: {args.path}")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"PASS: {args.path}")
    print(f"  required_sections={len(HEADINGS) + (len(ACTION_HEADINGS) if args.action_mode else 0)}")
    print("  decision=valid")
    print("  followups=exactly-3")
    print("  evidence=status-recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
