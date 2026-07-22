from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_foundation import (
    EXACT_HEAD_EXPRESSION,
    ROOT,
    ci_exact_head_errors,
)
from tests import test_browser_acceptance as browser_acceptance


def write_workflow(directory: Path, name: str, checkout_ref: str | None) -> None:
    ref = (
        ""
        if checkout_ref is None
        else f"\n        with:\n          ref: {checkout_ref}"
    )
    (directory / name).write_text(
        "name: fixture\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Check out repository\n"
        "        uses: actions/checkout@0123456789abcdef0123456789abcdef01234567"
        f"{ref}\n",
        encoding="utf-8",
    )


def test_all_pr_workflow_checkouts_use_the_exact_head() -> None:
    assert ci_exact_head_errors(ROOT / ".github/workflows") == []


def test_gate_rejects_default_synthetic_merge_checkout(tmp_path: Path) -> None:
    write_workflow(tmp_path, "default.yml", None)

    errors = ci_exact_head_errors(tmp_path)

    assert len(errors) == 1
    assert "actions/checkout must use exact ref" in errors[0]
    assert "found None" in errors[0]


def test_gate_rejects_mismatched_exact_head_expression(tmp_path: Path) -> None:
    write_workflow(tmp_path, "exact.yml", EXACT_HEAD_EXPRESSION)
    write_workflow(tmp_path, "mismatch.yml", "${{ github.sha }}")

    errors = ci_exact_head_errors(tmp_path)

    assert len(errors) == 1
    assert "mismatch.yml" in errors[0]
    assert "found '${{ github.sha }}'" in errors[0]


def test_browser_source_sha_rejects_expected_actual_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = "a" * 40
    expected = "b" * 40
    monkeypatch.setattr(browser_acceptance, "actual_checkout_sha", lambda: actual)
    monkeypatch.setenv("PET_EXPECTED_SOURCE_SHA", expected)

    with pytest.raises(AssertionError, match="does not match expected PR head"):
        browser_acceptance.verified_checkout_sha()


def test_browser_source_sha_records_verified_actual_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = "a" * 40
    monkeypatch.setattr(browser_acceptance, "actual_checkout_sha", lambda: actual)
    monkeypatch.setenv("PET_EXPECTED_SOURCE_SHA", actual)

    assert browser_acceptance.verified_checkout_sha() == (actual, actual)
