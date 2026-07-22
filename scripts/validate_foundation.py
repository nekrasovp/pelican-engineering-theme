#!/usr/bin/env python3
"""Validate the contract-only THEME-001 repository foundation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/decisions/0001-identity-license-and-boundaries.md",
    "docs/contracts/customization-v1.md",
    "docs/contracts/notebook-html-v1.md",
    "docs/third-party-and-assets.md",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/accessibility.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/foundation-docs.yml",
}

FORBIDDEN_IMPLEMENTATION_PATHS = {
    "pyproject.toml",
    "src",
    "templates",
    "static",
    "tests",
}

REQUIRED_TEXT = {
    "README.md": (
        "pelican-engineering-theme",
        "pelican_engineering_theme",
        "Python 3.11, 3.12, and 3.13",
        "Pelican 4.11 and 4.12",
        "No version, tag, GitHub Release, TestPyPI artifact, or PyPI artifact",
    ),
    "docs/decisions/0001-identity-license-and-boundaries.md": (
        "2026-07-22T08:54:24Z",
        "ENGINEERING_THEME_SHOW_PELICAN_CREDIT",
        "system font stacks only",
        "MIT License",
    ),
    "docs/contracts/customization-v1.md": (
        "pelican-engineering-theme-customization-v1",
        "site_footer",
        "--pet-color-bg",
        "--pet-font-mono",
    ),
    "docs/contracts/notebook-html-v1.md": (
        "plugin003-nbconvert-basic-v1",
        "137e1eb0ea620f1b15fff0ba81725eea23de1b7a",
        "b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf",
        "does not import",
    ),
    "docs/third-party-and-assets.md": (
        "28d786f6b26d329eab3f79154984399f46af6a24",
        "no vendored theme file is copied",
        "AGPL-3.0",
        "BSD-3-Clause",
        "Apache-2.0",
    ),
}

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")


def markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.md") if ".git" not in path.parts)


def tracked_text_files(errors: list[str]) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        errors.append(f"cannot list tracked files: {detail or 'git ls-files failed'}")
        return []

    paths: list[Path] = []
    for raw_relative in result.stdout.split(b"\0"):
        if not raw_relative:
            continue
        relative = raw_relative.decode("utf-8", errors="surrogateescape")
        path = ROOT / relative
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"{relative}: cannot read tracked file: {exc}")
            continue
        if b"\0" in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(path)
    return sorted(paths)


def validate_required_files(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")


def validate_scope(errors: list[str]) -> None:
    for relative in sorted(FORBIDDEN_IMPLEMENTATION_PATHS):
        if (ROOT / relative).exists():
            errors.append(f"THEME-001 must not contain implementation path: {relative}")


def validate_required_text(errors: list[str]) -> None:
    for relative, expected_values in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for expected in expected_values:
            if expected not in text:
                errors.append(f"{relative}: missing contract text {expected!r}")


def validate_local_links(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "#")):
                continue
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not target:
                continue
            destination = (path.parent / target).resolve()
            try:
                destination.relative_to(ROOT)
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not destination.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link: {target}")


def validate_privacy(errors: list[str]) -> None:
    for path in tracked_text_files(errors):
        text = path.read_text(encoding="utf-8")
        if EMAIL.search(text):
            errors.append(f"{path.relative_to(ROOT)}: email address is not allowed")


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    validate_scope(errors)
    validate_required_text(errors)
    validate_local_links(errors)
    validate_privacy(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("THEME-001 foundation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
