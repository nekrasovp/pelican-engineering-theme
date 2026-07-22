from __future__ import annotations

from scripts.verify_distribution import REQUIRED_PACKAGE_FILES, package_data_errors


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
