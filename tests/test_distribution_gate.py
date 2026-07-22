from __future__ import annotations

import tarfile

import pytest

from scripts.verify_distribution import (
    EXPECTED_SDIST_FILES,
    EXPECTED_WHEEL_FILES,
    REQUIRED_PACKAGE_FILES,
    REQUIRED_SDIST_SUPPORT_FILES,
    package_data_errors,
    package_inventory_errors,
    sdist_inventory_errors,
    sdist_scope_errors,
    sdist_support_errors,
    tar_file_names,
    wheel_inventory_errors,
    wheel_scope_errors,
)

NEW_PACKAGE_FILES = (
    "pelican_engineering_theme/theme/templates/includes/article-metadata.html",
    "pelican_engineering_theme/theme/templates/includes/brand.html",
    "pelican_engineering_theme/theme/templates/includes/footer.html",
    "pelican_engineering_theme/theme/templates/includes/head-metadata.html",
    "pelican_engineering_theme/theme/templates/includes/header.html",
    "pelican_engineering_theme/theme/templates/includes/language-link.html",
    "pelican_engineering_theme/theme/templates/includes/navigation.html",
    "pelican_engineering_theme/theme/templates/includes/canonical.html",
    "pelican_engineering_theme/theme/templates/includes/content-footer.html",
    "pelican_engineering_theme/theme/templates/includes/content-status.html",
    "pelican_engineering_theme/theme/templates/includes/feed-discovery.html",
    "pelican_engineering_theme/theme/templates/includes/pagination.html",
    "pelican_engineering_theme/theme/templates/includes/social-metadata.html",
    "pelican_engineering_theme/theme/templates/includes/structured-data.html",
    "pelican_engineering_theme/theme/templates/includes/translations.html",
)

NEW_SDIST_SUPPORT_FILES = (
    ".github/workflows/browser.yml",
    ".github/workflows/foundation-docs.yml",
    ".github/workflows/package.yml",
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
    "LICENSES/Apache-2.0.txt",
    "LICENSES/BSD-3-Clause-nbconvert.txt",
    "examples/full/pelicanconf.py",
    "examples/full/templates/index.html",
    "package-lock.json",
    "package.json",
    "scripts/validate_shell.py",
    "scripts/validate_content.py",
    "scripts/validate_notebook_contract.py",
    "THIRD_PARTY.md",
    "tests/site_build.py",
    "tests/test_shell_contract.py",
    "tests/test_content_contract.py",
    "tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html",
    "tests/test_notebook_contract.py",
)


def test_gate_rejects_omitted_required_template() -> None:
    members = REQUIRED_PACKAGE_FILES - {
        "pelican_engineering_theme/theme/templates/base.html"
    }

    assert package_data_errors(members) == [
        "missing required package file: "
        "pelican_engineering_theme/theme/templates/base.html"
    ]


def test_gate_rejects_omitted_packaged_404_template() -> None:
    required = "pelican_engineering_theme/theme/templates/404.html"
    members = REQUIRED_PACKAGE_FILES - {required}

    assert package_data_errors(members) == [
        f"missing required package file: {required}"
    ]


def test_gate_rejects_omitted_required_static_asset() -> None:
    members = REQUIRED_PACKAGE_FILES - {
        "pelican_engineering_theme/theme/static/css/scaffold.css"
    }

    assert package_data_errors(members) == [
        "missing required package file: "
        "pelican_engineering_theme/theme/static/css/scaffold.css"
    ]


def test_gate_rejects_omitted_required_theme_script() -> None:
    members = REQUIRED_PACKAGE_FILES - {
        "pelican_engineering_theme/theme/static/js/theme.js"
    }

    assert package_data_errors(members) == [
        "missing required package file: "
        "pelican_engineering_theme/theme/static/js/theme.js"
    ]


def test_gate_rejects_omitted_required_theme_toggle_include() -> None:
    members = REQUIRED_PACKAGE_FILES - {
        "pelican_engineering_theme/theme/templates/includes/theme-toggle.html"
    }

    assert package_data_errors(members) == [
        "missing required package file: "
        "pelican_engineering_theme/theme/templates/includes/theme-toggle.html"
    ]


@pytest.mark.parametrize("required", NEW_PACKAGE_FILES)
def test_gate_rejects_each_omitted_reusable_shell_include(required: str) -> None:
    members = REQUIRED_PACKAGE_FILES - {required}

    assert package_data_errors(members) == [
        f"missing required package file: {required}"
    ]


def test_wheel_gate_rejects_source_only_payload() -> None:
    assert wheel_scope_errors(
        {"pelican_engineering_theme/__init__.py", "tests/test_shell_contract.py"}
    ) == ["source-only path leaked into wheel: tests/test_shell_contract.py"]


def test_exact_package_inventory_rejects_internal_test_payload() -> None:
    members = REQUIRED_PACKAGE_FILES | {
        "pelican_engineering_theme/tests/test_internal.py"
    }
    assert package_inventory_errors(members) == [
        "unexpected runtime package file: "
        "pelican_engineering_theme/tests/test_internal.py"
    ]


def test_exact_wheel_archive_rejects_arbitrary_top_level_payload() -> None:
    members = EXPECTED_WHEEL_FILES | {"undeclared-build-note.txt"}
    assert wheel_inventory_errors(members) == [
        "unexpected wheel file: undeclared-build-note.txt"
    ]


def test_exact_wheel_archive_rejects_missing_generated_metadata() -> None:
    required = "pelican_engineering_theme-0.0.0.dev0.dist-info/WHEEL"
    assert wheel_inventory_errors(EXPECTED_WHEEL_FILES - {required}) == [
        f"missing exact wheel file: {required}"
    ]


def test_exact_sdist_archive_rejects_arbitrary_source_payload() -> None:
    prefix = "pelican_engineering_theme-0.0.0.dev0/"
    members = {f"{prefix}{member}" for member in EXPECTED_SDIST_FILES}
    members.add(f"{prefix}scratch/undeclared.txt")
    assert sdist_inventory_errors(members, prefix=prefix) == [
        f"unexpected sdist file: {prefix}scratch/undeclared.txt"
    ]


def test_exact_sdist_archive_rejects_missing_generated_metadata() -> None:
    prefix = "pelican_engineering_theme-0.0.0.dev0/"
    required = "src/pelican_engineering_theme.egg-info/SOURCES.txt"
    members = {f"{prefix}{member}" for member in EXPECTED_SDIST_FILES - {required}}
    assert sdist_inventory_errors(members, prefix=prefix) == [
        f"missing exact sdist file: {prefix}{required}"
    ]


def test_tar_inventory_ignores_directories_but_keeps_actual_files() -> None:
    directory = tarfile.TarInfo("archive/src/pelican_engineering_theme/theme")
    directory.type = tarfile.DIRTYPE
    declared = tarfile.TarInfo(
        "archive/src/pelican_engineering_theme/theme/templates/base.html"
    )
    declared.type = tarfile.REGTYPE

    assert tar_file_names([directory, declared]) == [declared.name]
    assert package_inventory_errors([declared.name], prefix="archive/src/") == []


def test_wheel_gate_rejects_node_manifest_payload() -> None:
    assert wheel_scope_errors({"package-lock.json", "package.json"}) == [
        "source-only path leaked into wheel: package-lock.json",
        "source-only path leaked into wheel: package.json",
    ]


def test_sdist_gate_rejects_installed_axe_payload() -> None:
    assert sdist_scope_errors(
        {"pelican_engineering_theme-0.0.0.dev0/node_modules/axe-core/axe.min.js"}
    ) == [
        "installed Node dependency leaked into sdist: "
        "pelican_engineering_theme-0.0.0.dev0/node_modules/axe-core/axe.min.js"
    ]


def test_gate_rejects_omitted_sdist_script() -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {"scripts/verify_distribution.py"}

    assert sdist_support_errors(members) == [
        "missing required sdist support file: scripts/verify_distribution.py"
    ]


def test_gate_rejects_omitted_sdist_example() -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {"examples/minimal/pelicanconf.py"}

    assert sdist_support_errors(members) == [
        "missing required sdist support file: examples/minimal/pelicanconf.py"
    ]


def test_gate_rejects_omitted_customization_contract() -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {"docs/contracts/customization-v1.md"}

    assert sdist_support_errors(members) == [
        "missing required sdist support file: docs/contracts/customization-v1.md"
    ]


def test_gate_rejects_omitted_sdist_test_package() -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {"tests/__init__.py"}

    assert sdist_support_errors(members) == [
        "missing required sdist support file: tests/__init__.py"
    ]


def test_gate_rejects_omitted_exact_head_regression_test() -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {"tests/test_ci_exact_head.py"}

    assert sdist_support_errors(members) == [
        "missing required sdist support file: tests/test_ci_exact_head.py"
    ]


@pytest.mark.parametrize("required", NEW_SDIST_SUPPORT_FILES)
def test_gate_rejects_each_new_sdist_support_file(required: str) -> None:
    members = REQUIRED_SDIST_SUPPORT_FILES - {required}

    assert sdist_support_errors(members) == [
        f"missing required sdist support file: {required}"
    ]
