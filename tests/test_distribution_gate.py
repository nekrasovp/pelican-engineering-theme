from __future__ import annotations

from scripts.verify_distribution import (
    REQUIRED_PACKAGE_FILES,
    REQUIRED_SDIST_SUPPORT_FILES,
    package_data_errors,
    sdist_support_errors,
)


def test_gate_rejects_omitted_required_template() -> None:
    members = REQUIRED_PACKAGE_FILES - {
        "pelican_engineering_theme/theme/templates/base.html"
    }

    assert package_data_errors(members) == [
        "missing required package file: "
        "pelican_engineering_theme/theme/templates/base.html"
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
    members = REQUIRED_SDIST_SUPPORT_FILES - {
        "docs/contracts/customization-v1.md"
    }

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
