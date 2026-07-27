#!/usr/bin/env python3
"""Validate foundation contracts, package scope, privacy, and runtime boundaries."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXACT_HEAD_EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"

REQUIRED_FILES = {
    ".gitignore",
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
    ".github/workflows/package.yml",
    ".github/workflows/browser.yml",
    ".github/workflows/release.yml",
    "package.json",
    "package-lock.json",
    "pyproject.toml",
    "uv.lock",
    "src/pelican_engineering_theme/__init__.py",
    "src/pelican_engineering_theme/theme/templates/base.html",
    "src/pelican_engineering_theme/theme/templates/includes/brand.html",
    "src/pelican_engineering_theme/theme/templates/includes/footer.html",
    "src/pelican_engineering_theme/theme/templates/includes/head-metadata.html",
    "src/pelican_engineering_theme/theme/templates/includes/header.html",
    "src/pelican_engineering_theme/theme/templates/includes/language-link.html",
    "src/pelican_engineering_theme/theme/templates/includes/navigation.html",
    "src/pelican_engineering_theme/theme/templates/includes/theme-toggle.html",
    "src/pelican_engineering_theme/theme/static/css/scaffold.css",
    "src/pelican_engineering_theme/theme/static/js/theme.js",
    "examples/minimal/pelicanconf.py",
    "examples/minimal/content/hello.md",
    "examples/full/pelicanconf.py",
    "examples/full/content/hello.md",
    "examples/full/templates/index.html",
    "docs/configuration.md",
    "docs/customization.md",
    "docs/notebooks.md",
    "docs/accessibility.md",
    "docs/compatibility.md",
    "docs/versioning.md",
    "docs/dependency-updates.md",
    "docs/deployment.md",
    "docs/releasing.md",
    "docs/release-notes/0.1.0.md",
    "docs/screenshots/README.md",
    "docs/screenshots/provenance.json",
    "scripts/capture_readme_screenshots.py",
    "scripts/release_candidate.py",
    "scripts/validate_docs.py",
    "scripts/validate_release_policy.py",
    "scripts/verify_readme_onboarding.py",
    "scripts/validate_shell.py",
    "tests/site_build.py",
    "tests/__init__.py",
    "tests/test_example_build.py",
    "tests/test_distribution_gate.py",
    "tests/test_color_mode_contract.py",
    "tests/test_browser_acceptance.py",
    "tests/test_ci_exact_head.py",
    "tests/test_shell_contract.py",
}

FORBIDDEN_ROOT_IMPLEMENTATION_PATHS = {
    "content",
    "pelicanconf.py",
    "publishconf.py",
    "templates",
    "static",
    "theme",
}

FORBIDDEN_THEME_ASSET_SUFFIXES = {
    ".eot",
    ".otf",
    ".ttf",
    ".woff",
    ".woff2",
}

ALLOWED_THEME_JAVASCRIPT = {
    "src/pelican_engineering_theme/theme/static/js/theme.js",
}

REQUIRED_TEXT = {
    "README.md": (
        "pelican-engineering-theme",
        "pelican_engineering_theme",
        "Python 3.11-3.13",
        "Pelican 4.11 and 4.12",
        "0.1.0",
        "pip install",
        "exact wheel or sdist",
    ),
    "docs/releasing.md": (
        "github-release",
        "pypi",
        "admin bypass disabled",
        "release: published",
        "No stored PyPI token",
    ),
    "docs/compatibility.md": (
        "Python 3.11",
        "Pelican 4.11",
        "Pelican 4.12",
        "not evidence of a PyPI installation",
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
        'html[data-theme="dark"]',
        "localStorage",
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

FORBIDDEN_RUNTIME_TEXT = (
    "EventSource",
    "WebSocket",
    "XMLHttpRequest",
    "analytics.",
    "fetch(",
    "google-analytics",
    "googletagmanager",
    "gtag(",
    "sendBeacon",
)

PULL_REQUEST_TRIGGER = re.compile(r"(?m)^  pull_request\s*:")
CHECKOUT_USE = re.compile(r"^\s*(?:-\s*)?uses:\s*actions/checkout@")
STEP_START = re.compile(r"^(\s*)-\s+")
CHECKOUT_REF = re.compile(r"^\s*ref:\s*(.*?)\s*$")
EXPECTED_SOURCE_SHA = re.compile(r"^\s*PET_EXPECTED_SOURCE_SHA:\s*(.*?)\s*$")


def markdown_files() -> list[Path]:
    excluded = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "dist",
        "node_modules",
    }
    return sorted(
        path for path in ROOT.rglob("*.md") if not excluded.intersection(path.parts)
    )


def repository_text_files(errors: list[str]) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
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
    for relative in sorted(FORBIDDEN_ROOT_IMPLEMENTATION_PATHS):
        if (ROOT / relative).exists():
            errors.append(
                f"site-owned or non-src implementation path is forbidden: {relative}"
            )

    theme_root = ROOT / "src/pelican_engineering_theme/theme"
    if theme_root.is_dir():
        javascript: set[str] = set()
        for path in theme_root.rglob("*"):
            relative = str(path.relative_to(ROOT))
            if path.is_file() and path.suffix.lower() == ".js":
                javascript.add(relative)
            if path.is_file() and path.suffix.lower() in FORBIDDEN_THEME_ASSET_SUFFIXES:
                errors.append(
                    f"forbidden bundled runtime asset: {path.relative_to(ROOT)}"
                )
        if javascript != ALLOWED_THEME_JAVASCRIPT:
            errors.append(
                "first-party theme JavaScript must contain only "
                f"{sorted(ALLOWED_THEME_JAVASCRIPT)}, found {sorted(javascript)}"
            )


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
                errors.append(
                    f"{path.relative_to(ROOT)}: link escapes repository: {target}"
                )
                continue
            if not destination.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link: {target}")


def validate_privacy(errors: list[str]) -> None:
    for path in repository_text_files(errors):
        text = path.read_text(encoding="utf-8")
        if EMAIL.search(text):
            errors.append(f"{path.relative_to(ROOT)}: email address is not allowed")


def validate_runtime_boundaries(errors: list[str]) -> None:
    theme_root = ROOT / "src/pelican_engineering_theme/theme"
    css = theme_root / "static/css/scaffold.css"
    script = theme_root / "static/js/theme.js"
    base = theme_root / "templates/base.html"
    if css.is_file():
        css_text = css.read_text(encoding="utf-8")
        for forbidden in ("@import", "http://", "https://"):
            if forbidden in css_text:
                errors.append(f"{css.relative_to(ROOT)}: forbidden text {forbidden!r}")
    if script.is_file() and base.is_file():
        runtime = script.read_text(encoding="utf-8") + base.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_RUNTIME_TEXT:
            if forbidden in runtime:
                errors.append(
                    f"theme runtime contains forbidden network/analytics text "
                    f"{forbidden!r}"
                )


def checkout_refs(workflow_text: str) -> list[tuple[int, str | None]]:
    """Return each checkout step's line number and explicit ref, if present."""
    lines = workflow_text.splitlines()
    checkouts: list[tuple[int, str | None]] = []
    for index, line in enumerate(lines):
        if not CHECKOUT_USE.match(line):
            continue

        uses_indent = len(line) - len(line.lstrip())
        step_start: int | None = None
        step_indent: int | None = None
        for candidate in range(index, -1, -1):
            match = STEP_START.match(lines[candidate])
            if match is None:
                continue
            candidate_indent = len(match.group(1))
            if candidate_indent <= uses_indent:
                step_start = candidate
                step_indent = candidate_indent
                break

        if step_start is None or step_indent is None:
            checkouts.append((index + 1, None))
            continue

        step_end = len(lines)
        for candidate in range(step_start + 1, len(lines)):
            candidate_line = lines[candidate]
            if not candidate_line.strip():
                continue
            match = STEP_START.match(candidate_line)
            candidate_indent = len(candidate_line) - len(candidate_line.lstrip())
            if (match is not None and candidate_indent <= step_indent) or (
                candidate_indent < step_indent
            ):
                step_end = candidate
                break

        refs = [
            match.group(1)
            for candidate_line in lines[step_start:step_end]
            if (match := CHECKOUT_REF.match(candidate_line)) is not None
        ]
        checkouts.append((index + 1, refs[0] if len(refs) == 1 else None))
    return checkouts


def ci_exact_head_errors(workflow_dir: Path) -> list[str]:
    """Validate immutable exact-head evidence across every PR workflow checkout."""
    errors: list[str] = []
    workflow_paths = sorted({*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")})
    for path in workflow_paths:
        text = path.read_text(encoding="utf-8")
        if PULL_REQUEST_TRIGGER.search(text) is None:
            continue

        for line_number, ref in checkout_refs(text):
            if ref != EXACT_HEAD_EXPRESSION:
                errors.append(
                    f"{path.name}:{line_number}: actions/checkout must use exact ref "
                    f"{EXACT_HEAD_EXPRESSION!r}, found {ref!r}"
                )

        expected_values = [
            match.group(1)
            for line in text.splitlines()
            if (match := EXPECTED_SOURCE_SHA.match(line)) is not None
        ]
        if path.name == "browser.yml" and expected_values != [EXACT_HEAD_EXPRESSION]:
            errors.append(
                "browser.yml: PET_EXPECTED_SOURCE_SHA must use the same exact-head "
                f"expression {EXACT_HEAD_EXPRESSION!r}, found {expected_values!r}"
            )
    return errors


def validate_ci_exact_head(errors: list[str]) -> None:
    errors.extend(ci_exact_head_errors(ROOT / ".github/workflows"))


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    validate_scope(errors)
    validate_required_text(errors)
    validate_local_links(errors)
    validate_privacy(errors)
    validate_runtime_boundaries(errors)
    validate_ci_exact_head(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Foundation, package scope, privacy, and runtime validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
