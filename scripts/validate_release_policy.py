#!/usr/bin/env python3
"""Fail closed unless release publication remains explicit and protected."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/release.yml"
PYPI_ACTION_SHA = "ba38be9e461d3875417946c167d0b5f3d385a247"
EXACT_TAG_REF = "${{ github.event.release.tag_name }}"
EXACT_RELEASE_SHA = "${{ github.sha }}"


def job_block(text: str, job_name: str) -> str:
    """Return one top-level job mapping block from simple workflow YAML."""
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)"
    )
    match = pattern.search(text)
    return "" if match is None else match.group(0)


def release_policy_errors(text: str) -> list[str]:
    """Return publication-trigger, permission, and immutability errors."""
    errors: list[str] = []
    trigger_match = re.search(r"(?ms)^on:\n(.*?)(?=^permissions:)", text)
    trigger = "" if trigger_match is None else trigger_match.group(1)
    if trigger.strip() != "release:\n    types: [published]":
        errors.append("release workflow trigger must be only release: published")
    for forbidden in (
        "push:",
        "pull_request:",
        "workflow_dispatch:",
        "workflow_run:",
        "schedule:",
        "repository_dispatch:",
    ):
        if forbidden in trigger:
            errors.append(f"automatic or bypass trigger is forbidden: {forbidden}")

    if "\npermissions: {}\n" not in text:
        errors.append("release workflow must default to zero permissions")

    build = job_block(text, "build-candidate")
    attach = job_block(text, "attach-github-release")
    publish = job_block(text, "publish-pypi")
    if not build:
        errors.append("missing build-candidate job")
    if not attach:
        errors.append("missing attach-github-release job")
    if not publish:
        errors.append("missing publish-pypi job")

    required_build = (
        f"ref: {EXACT_TAG_REF}",
        f"PET_EXPECTED_SOURCE_SHA: {EXACT_RELEASE_SHA}",
        'actual_source_sha="$(git rev-parse HEAD)"',
        'test "${actual_source_sha}" = "${PET_EXPECTED_SOURCE_SHA}"',
        "python scripts/release_candidate.py build",
        "python scripts/verify_distribution.py dist",
    )
    for required in required_build:
        if required not in build:
            errors.append(f"build-candidate is missing exact gate: {required}")

    if "name: github-release" not in attach:
        errors.append("GitHub release assets require github-release environment")
    if "contents: write" not in attach or "id-token: write" in attach:
        errors.append("GitHub release job must have contents: write only")
    if "gh release upload" not in attach:
        errors.append("GitHub release job must attach the verified candidate")
    if '--repo "${GITHUB_REPOSITORY}"' not in attach:
        errors.append("GitHub release upload must identify the repository explicitly")

    if "name: pypi" not in publish:
        errors.append("PyPI publication requires pypi environment")
    if "id-token: write" not in publish or "contents: write" in publish:
        errors.append("PyPI job must have id-token: write only")
    if "needs: [build-candidate, attach-github-release]" not in publish:
        errors.append("PyPI publication must wait for build and release attachment")
    pinned_action = f"uses: pypa/gh-action-pypi-publish@{PYPI_ACTION_SHA}"
    if pinned_action not in publish:
        errors.append("PyPI Trusted Publishing action must use the reviewed full SHA")

    forbidden_text = (
        "password:",
        "user:",
        "skip-existing:",
        "--skip-existing",
        "--clobber",
        "gh release create",
        "twine upload",
        "uv publish",
    )
    for forbidden in forbidden_text:
        if forbidden in text:
            errors.append(f"forbidden release bypass or credential path: {forbidden}")
    return errors


def main() -> int:
    errors = release_policy_errors(WORKFLOW.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Release trigger, protected environments, permissions, and OIDC passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
