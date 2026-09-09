#!/usr/bin/env python3
"""Deterministic contract checks for the code-review Agent Skill.

This is intentionally stricter than the Agent Skills frontmatter spec. It checks
that the behavioural guardrails this skill depends on have not been accidentally
removed during edits.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "### Review-only mode",
    "### Action mode",
    "## Phase 1 — Build a change and risk map",
    "## Phase 2 — Review in three passes",
    "## Phase 3 — Prove or dismiss suspected findings",
    "## Phase 4 — Execute repository-native verification",
    "## Mandatory blind-spot pass",
    "## Output contract",
]

REQUIRED_PHRASES = [
    "Evidence beats intuition",
    "Severity is impact, not confidence",
    "Most important thing you may be missing",
    "Three high-leverage things you did not ask for",
    "exactly three concrete follow-ups",
    "Do not fake execution",
    "Do not report speculative bugs as findings",
    "regression test",
    "REQUEST CHANGES",
    "APPROVE WITH FOLLOW-UPS",
    "INCOMPLETE",
]

REQUIRED_CHECK_TERMS = [
    "authorisation",
    "injection",
    "idempotency",
    "concurrency",
    "rollback",
    "supply chain",
    "observability",
    "migration",
]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("SKILL.md frontmatter is not closed")
    return text[4:end], text[end + 5 :]


def scalar(frontmatter: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
    if not match:
        raise AssertionError(f"missing frontmatter key: {key}")
    return match.group(1).strip().strip('"\'')


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill = skill_dir / "SKILL.md"
    ref = skill_dir / "references" / "review-checks.md"

    try:
        text = skill.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        name = scalar(frontmatter, "name")
        description = scalar(frontmatter, "description")

        if name != skill_dir.name:
            errors.append(f"name '{name}' must match parent directory '{skill_dir.name}'")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append("name violates Agent Skills naming rules")
        if len(name) > 64:
            errors.append("name exceeds 64 characters")
        if not 1 <= len(description) <= 1024:
            errors.append(f"description length {len(description)} is outside 1..1024")
        if len(text.splitlines()) >= 500:
            errors.append(f"SKILL.md has {len(text.splitlines())} lines; keep it under 500")
        if len(body.split()) >= 5000:
            errors.append(f"SKILL.md body has about {len(body.split())} whitespace tokens; keep it under 5000")

        for heading in REQUIRED_HEADINGS:
            if heading not in body:
                errors.append(f"missing required section heading: {heading}")

        for phrase in REQUIRED_PHRASES:
            if phrase.casefold() not in body.casefold():
                errors.append(f"missing behavioural contract phrase: {phrase}")

        if not ref.exists():
            errors.append("missing progressive-disclosure reference: references/review-checks.md")
        else:
            ref_text = ref.read_text(encoding="utf-8").casefold()
            for term in REQUIRED_CHECK_TERMS:
                if term not in ref_text:
                    errors.append(f"review-checks.md missing domain term: {term}")

        # Guard against accidental pre-approval of arbitrary shell execution.
        if re.search(r"(?m)^allowed-tools:.*(?:bash|shell)", frontmatter, re.I):
            errors.append("do not pre-approve bash/shell in this skill")

        # Avoid review instructions that equate test pass with correctness.
        if re.search(r"tests? pass(?:es|ed)?[,;:]?\s*(?:therefore|so)\s+(?:the )?(?:code|change)\s+is\s+(?:correct|safe)", body, re.I):
            errors.append("skill contains a test-pass-implies-correctness anti-pattern")
    except Exception as exc:  # validator should return a useful failure, not crash
        errors.append(str(exc))

    return errors


def main() -> int:
    skill_dir = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    errors = validate(skill_dir)
    if errors:
        print(f"FAIL: {skill_dir}")
        for error in errors:
            print(f"  - {error}")
        return 1
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    print(f"PASS: {skill_dir}")
    print(f"  lines={len(skill_text.splitlines())}")
    print(f"  words={len(skill_text.split())}")
    print("  frontmatter=valid-by-contract")
    print(f"  required_sections={len(REQUIRED_HEADINGS)}")
    print(f"  behavioural_contracts={len(REQUIRED_PHRASES)}")
    print(f"  domain_checks={len(REQUIRED_CHECK_TERMS)}")
    print("  shell_preapproval=absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
