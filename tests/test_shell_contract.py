from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from jinja2 import ChoiceLoader, Environment, FileSystemLoader

import pelican_engineering_theme
from scripts import validate_foundation
from scripts.validate_shell import (
    css_shell_contract_errors,
    document_shell_errors,
    focus_order_errors,
    generated_html_errors,
    runtime_default_errors,
)
from tests.site_build import ROOT, build_copied_example, build_example

THEME = pelican_engineering_theme.get_theme_path()
BASE = THEME / "templates/base.html"
CSS = THEME / "static/css/scaffold.css"
REQUIRED_INCLUDES = {
    "article-metadata.html",
    "brand.html",
    "canonical.html",
    "content-footer.html",
    "content-status.html",
    "feed-discovery.html",
    "footer.html",
    "head-metadata.html",
    "header.html",
    "language-link.html",
    "navigation.html",
    "pagination.html",
    "social-metadata.html",
    "structured-data.html",
    "theme-toggle.html",
    "translations.html",
}

PUBLIC_BLOCKS = (
    "html_head",
    "title",
    "head_meta",
    "canonical",
    "structured_data",
    "head_styles",
    "body_class",
    "body_start",
    "site_header",
    "site_navigation",
    "page_class",
    "hero",
    "content_header",
    "content",
    "content_footer",
    "site_footer",
    "scripts",
    "body_end",
)


def test_base_owns_reusable_includes_and_stable_blocks() -> None:
    includes = THEME / "templates/includes"
    assert {path.name for path in includes.glob("*.html")} == REQUIRED_INCLUDES
    base = BASE.read_text(encoding="utf-8")
    positions = [base.index(f"{{% block {block}") for block in PUBLIC_BLOCKS]
    assert positions == sorted(positions)
    for include in REQUIRED_INCLUDES - {"brand.html", "language-link.html"}:
        assert f"includes/{include}" in "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                *(THEME.glob("templates/*.html")),
                *(includes.glob("*.html")),
            ]
        )


@pytest.mark.parametrize("block", PUBLIC_BLOCKS)
def test_each_documented_block_is_independently_overridable(
    block: str, tmp_path: Path
) -> None:
    marker = f"probe-{block}"
    (tmp_path / "probe.html").write_text(
        '{% extends "base.html" %}'
        f"{{% block {block} %}}{marker}{{% endblock {block} %}}",
        encoding="utf-8",
    )
    environment = Environment(
        loader=ChoiceLoader(
            [
                FileSystemLoader(tmp_path),
                FileSystemLoader(THEME / "templates"),
            ]
        )
    )
    rendered = environment.get_template("probe.html").render(
        DEFAULT_LANG="en",
        SITENAME="Generic Test Site",
        SITEURL="",
        THEME_STATIC_DIR="theme",
    )
    assert marker in rendered


def test_shell_css_has_focus_wrap_and_overflow_contracts() -> None:
    assert css_shell_contract_errors(CSS.read_text(encoding="utf-8")) == []


def test_negative_shell_css_regressions_are_detected() -> None:
    css = CSS.read_text(encoding="utf-8")
    for snippet in (
        ".pet-skip-link:focus {",
        ":focus-visible {",
        "flex-wrap: wrap;",
        "min-width: 0;",
        "overflow-wrap: anywhere;",
    ):
        errors = css_shell_contract_errors(css.replace(snippet, ""))
        assert errors, snippet


def test_negative_skip_link_and_duplicate_shell_regressions_are_detected() -> None:
    valid = (
        "<!doctype html><html><head><title>x</title></head><body>"
        '<a class="pet-skip-link" href="#main-content">Skip</a>'
        '<main id="main-content" tabindex="-1"></main></body></html>'
    )
    assert document_shell_errors(valid) == []
    assert document_shell_errors(valid.replace("pet-skip-link", "missing"))
    assert document_shell_errors(valid.replace("</body>", "<main></main></body>"))
    assert document_shell_errors(valid.replace('tabindex="-1"', ""))


def test_negative_focus_order_regression_is_detected() -> None:
    expected = ["skip", "brand", "overview", "guides", "language", "theme"]
    assert focus_order_errors(expected, expected) == []
    assert focus_order_errors(
        ["brand", "skip", "overview", "guides", "language", "theme"], expected
    )


def test_runtime_defaults_are_generic_and_negative_personal_fixture_fails(
    tmp_path: Path,
) -> None:
    runtime_files = [
        path
        for path in THEME.rglob("*")
        if path.is_file() and path.suffix in {".css", ".html", ".js"}
    ]
    assert runtime_default_errors(runtime_files) == []
    personal = tmp_path / "personal.html"
    personal.write_text('<a href="https://nekrasovp.ru">Personal</a>', encoding="utf-8")
    assert runtime_default_errors([personal])


def test_foundation_markdown_scan_ignores_installed_node_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    dependency_readme = tmp_path / "node_modules/axe-core/README.md"
    dependency_readme.parent.mkdir(parents=True)
    readme.write_text("# Repository documentation\n", encoding="utf-8")
    dependency_readme.write_text("# Installed dependency\n", encoding="utf-8")
    monkeypatch.setattr(validate_foundation, "ROOT", tmp_path)

    assert validate_foundation.markdown_files() == [readme]


def test_empty_optional_settings_render_no_empty_controls(tmp_path: Path) -> None:
    example = tmp_path / "empty-options"
    shutil.copytree(ROOT / "examples/minimal", example)
    with (example / "pelicanconf.py").open("a", encoding="utf-8") as config:
        config.write(
            "\nMENUITEMS = ()\n"
            "ENGINEERING_THEME_NAV = ()\n"
            "ENGINEERING_THEME_LANGUAGE_LINKS = ()\n"
            "ENGINEERING_THEME_FOOTER_TEXT = ''\n"
            "ENGINEERING_THEME_SHOW_PELICAN_CREDIT = False\n"
        )
    output = build_copied_example(example)
    markup = (output / "index.html").read_text(encoding="utf-8")
    assert "<nav" not in markup
    assert "pet-language-link" not in markup
    assert "<footer" not in markup
    assert "pet-site-footer__inner" not in markup
    assert generated_html_errors(output) == []


def test_nonempty_navigation_with_no_valid_links_renders_no_container(
    tmp_path: Path,
) -> None:
    example = tmp_path / "invalid-navigation"
    shutil.copytree(ROOT / "examples/minimal", example)
    with (example / "pelicanconf.py").open("a", encoding="utf-8") as config:
        config.write(
            "\nMENUITEMS = (\n"
            "    ('', '/missing-label/'),\n"
            "    ('Missing URL', ''),\n"
            ")\n"
        )
    output = build_copied_example(example)
    markup = (output / "index.html").read_text(encoding="utf-8")
    assert "<nav" not in markup
    assert "pet-navigation__list" not in markup


def test_navigation_changes_through_config_only(tmp_path: Path) -> None:
    example = tmp_path / "changed-navigation"
    shutil.copytree(ROOT / "examples/full", example)
    config = example / "pelicanconf.py"
    original = config.read_text(encoding="utf-8")
    config.write_text(original.replace('"Guides"', '"Manuals"'), encoding="utf-8")
    output = build_copied_example(example)
    markup = (output / "index.html").read_text(encoding="utf-8")
    assert "Manuals" in markup
    assert '<a href="/guides/">Guides</a>' not in markup


def test_standard_menuitems_is_the_primary_navigation_api(tmp_path: Path) -> None:
    example = tmp_path / "standard-menuitems"
    shutil.copytree(ROOT / "examples/minimal", example)
    with (example / "pelicanconf.py").open("a", encoding="utf-8") as config:
        config.write("\nMENUITEMS = (('Start', '/'), ('Docs', '/docs/'))\n")
    markup = (build_copied_example(example) / "index.html").read_text(encoding="utf-8")
    assert '<a href="/">Start</a>' in markup
    assert '<a href="/docs/">Docs</a>' in markup


def test_extended_navigation_precedence_adds_current_page_metadata(
    tmp_path: Path,
) -> None:
    example = tmp_path / "extended-navigation"
    shutil.copytree(ROOT / "examples/minimal", example)
    with (example / "pelicanconf.py").open("a", encoding="utf-8") as config:
        config.write(
            "\nMENUITEMS = (('Standard', '/standard/'),)\n"
            "ENGINEERING_THEME_NAV = (\n"
            "    {'label': 'Current', 'url': '/current/', 'current': True},\n"
            ")\n"
        )
    markup = (build_copied_example(example) / "index.html").read_text(encoding="utf-8")
    assert "Standard" not in markup
    assert '<a href="/current/" aria-current="page">Current</a>' in markup


def test_all_minimal_and_full_documents_have_one_valid_shell(tmp_path: Path) -> None:
    for example_name in ("minimal", "full"):
        output = build_example(example_name, tmp_path)
        assert generated_html_errors(output) == []


def test_no_checkout_workflow_uses_absolute_shell_helper_with_proof_python() -> None:
    workflow = (ROOT / ".github/workflows/package.yml").read_text(encoding="utf-8")
    build_step = workflow.split(
        "- name: Build both fixtures from the installed wheel outside the checkout",
        maxsplit=1,
    )[1].split("\n  clean-sdist:", maxsplit=1)[0]
    artifact_position = build_step.index('artifact_root="$PWD"')
    loop_position = build_step.index("for example in minimal full")
    validator_position = build_step.index(
        '"${proof_python}" -I "${artifact_root}/scripts/validate_shell.py"'
    )
    assert artifact_position < loop_position < validator_position
