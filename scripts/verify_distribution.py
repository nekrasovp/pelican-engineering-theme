#!/usr/bin/env python3
"""Verify the identity and required package data in built distributions."""

from __future__ import annotations

import argparse
import email
import hashlib
import tarfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

NAME = "pelican-engineering-theme"
NORMALIZED_NAME = "pelican_engineering_theme"
VERSION = "0.1.0"
PACKAGE = "pelican_engineering_theme"
LICENSE_SHA256 = "36deab88361eb4a1ae20f2d94764a7f734e3902ee79865726be944b0b6d316ab"
EXPECTED_PROJECT_URLS = [
    "Changelog, https://github.com/nekrasovp/pelican-engineering-theme/blob/main/CHANGELOG.md",
    "Documentation, https://github.com/nekrasovp/pelican-engineering-theme/tree/main/docs",
    "Source, https://github.com/nekrasovp/pelican-engineering-theme",
    "Repository, https://github.com/nekrasovp/pelican-engineering-theme",
    "Issues, https://github.com/nekrasovp/pelican-engineering-theme/issues",
]
EXPECTED_CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Framework :: Pelican",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Internet :: WWW/HTTP :: Site Management",
    "Topic :: Text Processing :: Markup :: HTML",
]

REQUIRED_PACKAGE_FILES = {
    f"{PACKAGE}/__init__.py",
    f"{PACKAGE}/theme/templates/404.html",
    f"{PACKAGE}/theme/templates/archives.html",
    f"{PACKAGE}/theme/templates/article.html",
    f"{PACKAGE}/theme/templates/author.html",
    f"{PACKAGE}/theme/templates/authors.html",
    f"{PACKAGE}/theme/templates/base.html",
    f"{PACKAGE}/theme/templates/categories.html",
    f"{PACKAGE}/theme/templates/category.html",
    f"{PACKAGE}/theme/templates/index.html",
    f"{PACKAGE}/theme/templates/page.html",
    f"{PACKAGE}/theme/templates/period_archives.html",
    f"{PACKAGE}/theme/templates/tag.html",
    f"{PACKAGE}/theme/templates/tags.html",
    f"{PACKAGE}/theme/templates/includes/brand.html",
    f"{PACKAGE}/theme/templates/includes/article-metadata.html",
    f"{PACKAGE}/theme/templates/includes/canonical.html",
    f"{PACKAGE}/theme/templates/includes/content-footer.html",
    f"{PACKAGE}/theme/templates/includes/content-status.html",
    f"{PACKAGE}/theme/templates/includes/feed-discovery.html",
    f"{PACKAGE}/theme/templates/includes/footer.html",
    f"{PACKAGE}/theme/templates/includes/head-metadata.html",
    f"{PACKAGE}/theme/templates/includes/header.html",
    f"{PACKAGE}/theme/templates/includes/language-link.html",
    f"{PACKAGE}/theme/templates/includes/navigation.html",
    f"{PACKAGE}/theme/templates/includes/pagination.html",
    f"{PACKAGE}/theme/templates/includes/social-metadata.html",
    f"{PACKAGE}/theme/templates/includes/structured-data.html",
    f"{PACKAGE}/theme/templates/includes/theme-toggle.html",
    f"{PACKAGE}/theme/templates/includes/translations.html",
    f"{PACKAGE}/theme/static/css/scaffold.css",
    f"{PACKAGE}/theme/static/js/theme.js",
}
REQUIRED_SDIST_SUPPORT_FILES = {
    ".github/workflows/browser.yml",
    ".github/workflows/foundation-docs.yml",
    ".github/workflows/package.yml",
    ".github/workflows/release.yml",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSES/Apache-2.0.txt",
    "LICENSES/BSD-3-Clause-nbconvert.txt",
    "MANIFEST.in",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY.md",
    "docs/contracts/customization-v1.md",
    "docs/contracts/notebook-html-v1.md",
    "docs/decisions/0001-identity-license-and-boundaries.md",
    "docs/third-party-and-assets.md",
    "docs/accessibility.md",
    "docs/compatibility.md",
    "docs/configuration.md",
    "docs/customization.md",
    "docs/dependency-updates.md",
    "docs/deployment.md",
    "docs/notebooks.md",
    "docs/release-notes/0.1.0.md",
    "docs/releasing.md",
    "docs/screenshots/README.md",
    "docs/screenshots/archive-light.png",
    "docs/screenshots/article-light.png",
    "docs/screenshots/home-dark.png",
    "docs/screenshots/home-light.png",
    "docs/screenshots/notebook-dark.png",
    "docs/screenshots/provenance.json",
    "docs/versioning.md",
    "examples/minimal/content/hello.md",
    "examples/minimal/pelicanconf.py",
    "examples/full/content/hello.md",
    "examples/full/content/archived-interface.md",
    "examples/full/content/deprecated-protocol.md",
    "examples/full/content/long-technical-title.md",
    "examples/full/content/multilingual-guide-ru.md",
    "examples/full/content/multilingual-guide.md",
    "examples/full/content/notebook-presentation.md",
    "examples/full/content/pages/about.md",
    "examples/full/content/source-provenance.md",
    "examples/full/content/downloads/theme006-notebook.ipynb",
    "examples/full/pelicanconf.py",
    "examples/full/templates/index.html",
    "package-lock.json",
    "package.json",
    "pyproject.toml",
    "scripts/__init__.py",
    "scripts/validate_foundation.py",
    "scripts/validate_notebook_contract.py",
    "scripts/validate_content.py",
    "scripts/validate_shell.py",
    "scripts/capture_readme_screenshots.py",
    "scripts/release_candidate.py",
    "scripts/validate_docs.py",
    "scripts/validate_release_policy.py",
    "scripts/verify_clean_sdist.py",
    "scripts/verify_distribution.py",
    "scripts/verify_external_install.py",
    "scripts/verify_readme_onboarding.py",
    "tests/__init__.py",
    "tests/site_build.py",
    "tests/test_ci_exact_head.py",
    "tests/test_distribution_gate.py",
    "tests/test_color_mode_contract.py",
    "tests/test_content_contract.py",
    "tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html",
    "tests/test_notebook_contract.py",
    "tests/test_browser_acceptance.py",
    "tests/test_example_build.py",
    "tests/test_shell_contract.py",
    "tests/test_theme_package.py",
    "tests/test_release_preparation.py",
}
WHEEL_METADATA_FILES = {
    f"{NORMALIZED_NAME}-{VERSION}.dist-info/METADATA",
    f"{NORMALIZED_NAME}-{VERSION}.dist-info/RECORD",
    f"{NORMALIZED_NAME}-{VERSION}.dist-info/WHEEL",
    f"{NORMALIZED_NAME}-{VERSION}.dist-info/licenses/LICENSE",
    f"{NORMALIZED_NAME}-{VERSION}.dist-info/top_level.txt",
}
SDIST_GENERATED_FILES = {
    "LICENSE",
    "PKG-INFO",
    "setup.cfg",
    f"src/{NORMALIZED_NAME}.egg-info/PKG-INFO",
    f"src/{NORMALIZED_NAME}.egg-info/SOURCES.txt",
    f"src/{NORMALIZED_NAME}.egg-info/dependency_links.txt",
    f"src/{NORMALIZED_NAME}.egg-info/requires.txt",
    f"src/{NORMALIZED_NAME}.egg-info/top_level.txt",
}
EXPECTED_WHEEL_FILES = REQUIRED_PACKAGE_FILES | WHEEL_METADATA_FILES
EXPECTED_SDIST_FILES = (
    REQUIRED_SDIST_SUPPORT_FILES
    | {f"src/{required}" for required in REQUIRED_PACKAGE_FILES}
    | SDIST_GENERATED_FILES
)

assert len(REQUIRED_PACKAGE_FILES) == 32
assert len(REQUIRED_SDIST_SUPPORT_FILES) == 76
assert len(EXPECTED_WHEEL_FILES) == 37
assert len(EXPECTED_SDIST_FILES) == 116

FORBIDDEN_WHEEL_PREFIXES = ("examples/", "node_modules/", "scripts/", "tests/")
FORBIDDEN_WHEEL_FILES = {"package-lock.json", "package.json"}


def package_data_errors(members: Iterable[str], prefix: str = "") -> list[str]:
    """Return missing required package-data errors for an archive inventory."""
    member_set = set(members)
    return [
        f"missing required package file: {prefix}{required}"
        for required in sorted(REQUIRED_PACKAGE_FILES)
        if f"{prefix}{required}" not in member_set
    ]


def package_inventory_errors(members: Iterable[str], prefix: str = "") -> list[str]:
    """Reject every undeclared file from the runtime Python package."""
    package_prefix = f"{prefix}{PACKAGE}/"
    expected = {f"{prefix}{required}" for required in REQUIRED_PACKAGE_FILES}
    actual = {member for member in members if member.startswith(package_prefix)}
    return [
        f"unexpected runtime package file: {member}"
        for member in sorted(actual - expected)
    ]


def wheel_inventory_errors(members: Iterable[str]) -> list[str]:
    """Require equality with the complete runtime-wheel allowlist."""
    actual = set(members)
    missing = [
        f"missing exact wheel file: {member}"
        for member in sorted(EXPECTED_WHEEL_FILES - actual)
    ]
    unexpected = [
        f"unexpected wheel file: {member}"
        for member in sorted(actual - EXPECTED_WHEEL_FILES)
    ]
    return missing + unexpected


def sdist_inventory_errors(members: Iterable[str], prefix: str = "") -> list[str]:
    """Require equality with the complete self-testing-sdist allowlist."""
    actual = set(members)
    expected = {f"{prefix}{required}" for required in EXPECTED_SDIST_FILES}
    missing = [
        f"missing exact sdist file: {member}" for member in sorted(expected - actual)
    ]
    unexpected = [
        f"unexpected sdist file: {member}" for member in sorted(actual - expected)
    ]
    return missing + unexpected


def tar_file_names(members: Iterable[tarfile.TarInfo]) -> list[str]:
    """Return actual file names, excluding normal tar directory entries."""
    return [member.name for member in members if member.isfile()]


def sdist_support_errors(members: Iterable[str], prefix: str = "") -> list[str]:
    """Return missing source-support errors for the self-testing sdist."""
    member_set = set(members)
    return [
        f"missing required sdist support file: {prefix}{required}"
        for required in sorted(REQUIRED_SDIST_SUPPORT_FILES)
        if f"{prefix}{required}" not in member_set
    ]


def wheel_scope_errors(members: Iterable[str]) -> list[str]:
    """Reject source-only tests, helpers, and examples from the runtime wheel."""
    return [
        f"source-only path leaked into wheel: {member}"
        for member in sorted(members)
        if member.startswith(FORBIDDEN_WHEEL_PREFIXES)
        or member in FORBIDDEN_WHEEL_FILES
    ]


def sdist_scope_errors(members: Iterable[str]) -> list[str]:
    """Reject installed Node payloads from the self-testing source archive."""
    return [
        f"installed Node dependency leaked into sdist: {member}"
        for member in sorted(members)
        if "/node_modules/" in member or member.startswith("node_modules/")
    ]


def metadata_errors(raw_metadata: bytes) -> list[str]:
    """Return exact release identity, compatibility, and project-link errors."""
    project_metadata = email.message_from_bytes(raw_metadata)
    expected = {
        "Metadata-Version": "2.4",
        "Name": NAME,
        "Version": VERSION,
        "Summary": (
            "A reusable, accessibility-conscious Pelican theme for technical writers."
        ),
        "License-Expression": "MIT",
        "Requires-Python": ">=3.11",
        "Requires-Dist": "pelican[markdown]<4.13,>=4.11",
        "Description-Content-Type": "text/markdown",
        "Keywords": "pelican,theme,technical-writing,jupyter,accessibility",
    }
    errors = [
        f"metadata {field} is {project_metadata.get(field)!r}, expected {value!r}"
        for field, value in expected.items()
        if project_metadata.get(field) != value
    ]
    if project_metadata.get_all("License-File") != ["LICENSE"]:
        errors.append("metadata License-File must contain only 'LICENSE'")
    if project_metadata.get_all("Project-URL") != EXPECTED_PROJECT_URLS:
        errors.append("metadata Project-URL values do not match the exact public links")
    if project_metadata.get_all("Classifier") != EXPECTED_CLASSIFIERS:
        errors.append("metadata Classifier values do not match the supported contract")
    return errors


def license_errors(raw_license: bytes, archive_path: str) -> list[str]:
    """Return an error unless an archive contains the exact repository license."""
    digest = hashlib.sha256(raw_license).hexdigest()
    if digest == LICENSE_SHA256:
        return []
    return [f"license digest for {archive_path} is {digest}, expected {LICENSE_SHA256}"]


def verify_wheel(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        members = [item.filename for item in archive.infolist() if not item.is_dir()]
        errors.extend(package_data_errors(members))
        errors.extend(package_inventory_errors(members))
        errors.extend(wheel_scope_errors(members))
        errors.extend(wheel_inventory_errors(members))
        metadata_path = f"{NORMALIZED_NAME}-{VERSION}.dist-info/METADATA"
        if metadata_path not in members:
            errors.append(f"missing wheel metadata: {metadata_path}")
        else:
            errors.extend(metadata_errors(archive.read(metadata_path)))
        license_path = f"{NORMALIZED_NAME}-{VERSION}.dist-info/licenses/LICENSE"
        if license_path not in members:
            errors.append(f"missing wheel license: {license_path}")
        else:
            errors.extend(license_errors(archive.read(license_path), license_path))
    return errors


def verify_sdist(path: Path) -> list[str]:
    errors: list[str] = []
    archive_prefix = f"{NORMALIZED_NAME}-{VERSION}/"
    package_prefix = f"{archive_prefix}src/"
    with tarfile.open(path, mode="r:gz") as archive:
        members = tar_file_names(archive.getmembers())
        errors.extend(package_data_errors(members, prefix=package_prefix))
        errors.extend(package_inventory_errors(members, prefix=package_prefix))
        errors.extend(sdist_support_errors(members, prefix=archive_prefix))
        errors.extend(sdist_scope_errors(members))
        errors.extend(sdist_inventory_errors(members, prefix=archive_prefix))
        metadata_path = f"{archive_prefix}PKG-INFO"
        try:
            metadata_member = archive.extractfile(metadata_path)
        except KeyError:
            metadata_member = None
        if metadata_member is None:
            errors.append(f"missing sdist metadata: {metadata_path}")
        else:
            errors.extend(metadata_errors(metadata_member.read()))
        license_path = f"{archive_prefix}LICENSE"
        try:
            license_member = archive.extractfile(license_path)
        except KeyError:
            license_member = None
        if license_member is None:
            errors.append(f"missing sdist license: {license_path}")
        else:
            errors.extend(license_errors(license_member.read(), license_path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()

    wheels = sorted(args.dist.glob("*.whl"))
    sdists = sorted(args.dist.glob("*.tar.gz"))
    errors: list[str] = []
    if len(wheels) != 1:
        errors.append(f"expected one wheel, found {len(wheels)}")
    if len(sdists) != 1:
        errors.append(f"expected one sdist, found {len(sdists)}")
    if len(wheels) == 1:
        errors.extend(verify_wheel(wheels[0]))
    if len(sdists) == 1:
        errors.extend(verify_sdist(sdists[0]))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Verified {wheels[0].name} and {sdists[0].name}")
    print(f"Identity: {NAME} {VERSION}; license: MIT")
    print(f"Required package files: {len(REQUIRED_PACKAGE_FILES)}")
    print(f"Exact wheel archive files: {len(EXPECTED_WHEEL_FILES)}")
    print(f"Exact sdist support files: {len(REQUIRED_SDIST_SUPPORT_FILES)}")
    print(f"Exact sdist archive files: {len(EXPECTED_SDIST_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
