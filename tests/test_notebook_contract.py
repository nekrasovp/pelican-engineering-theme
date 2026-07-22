from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader

import pelican_engineering_theme
from scripts.validate_notebook_contract import (
    EXPECTED_FIXTURE_BYTES,
    EXPECTED_FIXTURE_SHA256,
    INPUT_CONTRACT_ID,
    READER_HTML_CONTRACT,
    REQUIRED_CELL_IDS,
    REQUIRED_TEXT_MARKERS,
    execution_boundary_errors,
    fixture_errors,
    fragment_contract_errors,
    fragment_facts,
)
from tests.site_build import (
    ROOT,
    add_external_notebook_contract_article,
    build_copied_example,
    build_example,
)

THEME = pelican_engineering_theme.get_theme_path()
FIXTURE = (
    ROOT / "tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html"
)
NOTEBOOK = ROOT / "examples/full/content/downloads/theme006-notebook.ipynb"
ARTICLE = ROOT / "examples/full/content/notebook-presentation.md"


def test_external_fixture_intake_lock_and_exact_state_counts() -> None:
    assert fixture_errors(FIXTURE) == []
    assert FIXTURE.stat().st_size == EXPECTED_FIXTURE_BYTES == 4465
    assert EXPECTED_FIXTURE_SHA256 == (
        "b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf"
    )

    facts = fragment_facts(FIXTURE.read_text(encoding="utf-8"))
    assert facts.cell_ids == REQUIRED_CELL_IDS
    assert facts.state_counts == {
        "cells": 7,
        "code_cells": 6,
        "error_outputs": 1,
        "html_outputs": 2,
        "input_areas": 6,
        "markdown_cells": 1,
        "output_areas": 6,
        "png_outputs": 1,
        "stream_outputs": 1,
        "svg_outputs": 1,
        "tables": 1,
        "trusted_scripts": 1,
    }


def test_exact_external_fragment_survives_pelican_round_trip(tmp_path: Path) -> None:
    assert fixture_errors(FIXTURE) == []
    example = tmp_path / "external-contract-roundtrip"
    shutil.copytree(ROOT / "examples/full", example)
    article = add_external_notebook_contract_article(example)
    assert article.read_bytes().endswith(FIXTURE.read_bytes())

    output = build_copied_example(example)
    markup = (output / "external-notebook-contract.html").read_text(encoding="utf-8")
    article_start = '<article class="pet-prose pet-notebook-region">'
    assert markup.count(article_start) == 1
    scoped_content = markup.split(article_start, 1)[1].split("</article>", 1)[0]
    facts = fragment_facts(scoped_content)

    assert facts.cell_ids == REQUIRED_CELL_IDS
    assert facts.state_counts == {
        "cells": 7,
        "code_cells": 6,
        "error_outputs": 1,
        "html_outputs": 2,
        "input_areas": 6,
        "markdown_cells": 1,
        "output_areas": 6,
        "png_outputs": 1,
        "stream_outputs": 1,
        "svg_outputs": 1,
        "tables": 1,
        "trusted_scripts": 1,
    }
    assert facts.document_wrappers == ()
    assert facts.jp_tokens == frozenset()
    for marker in REQUIRED_TEXT_MARKERS:
        assert marker in scoped_content
    assert markup.count("<html") == 1
    assert markup.count("<body") == 1
    assert 'class="pet-prose pet-notebook-region"' in markup
    assert "pet-notebook-source-link" not in markup


def test_fixture_gate_is_fail_closed_for_missing_digest_and_content(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.html"
    assert fixture_errors(missing) == [f"missing fixture: {missing}"]

    original = FIXTURE.read_text(encoding="utf-8")
    digest_drift = tmp_path / "digest-drift.html"
    digest_drift.write_text(original + "\n", encoding="utf-8")
    assert any("SHA-256" in error for error in fixture_errors(digest_drift))

    for marker in (
        'id="cell-id=markdown-contract"',
        "output_stream",
        "output_error",
        "output_png",
        "output_svg",
        "<table>",
        'data-contract="rich"',
    ):
        modified = tmp_path / f"missing-{len(marker)}.html"
        modified.write_text(original.replace(marker, "", 1), encoding="utf-8")
        assert fragment_contract_errors(modified.read_text(encoding="utf-8")), marker


@pytest.mark.parametrize(
    "wrapper",
    ["<html>", "</html>", "<body>", "</body>"],
)
def test_fixture_gate_rejects_nested_document_wrappers(wrapper: str) -> None:
    assert fragment_contract_errors(wrapper + FIXTURE.read_text(encoding="utf-8"))


def test_owned_example_notebook_is_static_generic_and_complete() -> None:
    raw = NOTEBOOK.read_bytes()
    assert len(raw) == 5497
    assert hashlib.sha256(raw).hexdigest() == (
        "80d31e53242e740e8f530162234c79be8e0cfaebab999fcf25cc8ef0254773bc"
    )
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert notebook["metadata"]["pet_provenance"] == (
        "Authored from scratch for pelican-engineering-theme THEME-006"
    )
    assert notebook["metadata"]["pet_input_contract_id"] == INPUT_CONTRACT_ID
    assert notebook["metadata"]["notebook_html_contract"] == READER_HTML_CONTRACT
    assert len(notebook["cells"]) >= 8
    assert any(cell["cell_type"] == "markdown" for cell in notebook["cells"])

    output_types = {
        output["output_type"]
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        for output in cell.get("outputs", [])
    }
    assert output_types >= {"display_data", "error", "execute_result", "stream"}
    serialized = NOTEBOOK.read_text(encoding="utf-8").casefold()
    assert "nekrasovp.github.io" not in serialized
    assert "company" not in serialized


def test_article_and_page_templates_share_exact_notebook_activation() -> None:
    for template_name in ("article.html", "page.html"):
        template = (THEME / f"templates/{template_name}").read_text(encoding="utf-8")
        assert "jupyter_notebook" in template
        assert "notebook_html_contract" in template
        assert "nbconvert-basic.v1" in template
        assert "pet-notebook-document" in template
        assert "pet-notebook-region" in template
        assert 'aria-label="Notebook content"' not in template
        assert 'tabindex="0"' not in template


def test_owned_example_article_builds_every_presentation_state(tmp_path: Path) -> None:
    output = build_example("full", tmp_path)
    markup = (output / "notebook-presentation.html").read_text(encoding="utf-8")
    facts = fragment_facts(markup)

    assert 'class="pet-shell pet-notebook-document"' in markup
    assert 'class="pet-prose pet-notebook-region"' in markup
    assert 'aria-label="Notebook content"' not in markup
    assert facts.state_counts["markdown_cells"] >= 1
    assert facts.state_counts["code_cells"] >= 6
    assert facts.state_counts["stream_outputs"] >= 1
    assert facts.state_counts["error_outputs"] >= 1
    assert facts.state_counts["png_outputs"] >= 1
    assert facts.state_counts["svg_outputs"] >= 1
    assert facts.state_counts["tables"] >= 1
    for marker in (
        'data-pet-dataframe="wide"',
        'data-pet-rich-output="trusted"',
        'class="math"',
        "<figure",
        "<figcaption>",
        'class="plotly-graph-div"',
    ):
        assert marker in markup
    assert "<html" not in ARTICLE.read_text(encoding="utf-8").casefold()
    assert "<body" not in ARTICLE.read_text(encoding="utf-8").casefold()

    copied_notebook = output / "downloads/theme006-notebook.ipynb"
    assert copied_notebook.read_bytes() == NOTEBOOK.read_bytes()
    assert 'class="pet-notebook-source-link"' in markup
    assert 'href="./downloads/theme006-notebook.ipynb"' in markup
    assert "download" in markup

    generic = (output / "long-technical-title.html").read_text(encoding="utf-8")
    assert "pet-notebook-document" not in generic
    assert "pet-notebook-region" not in generic


def render_content_footer(content: SimpleNamespace, *, siteurl: object = "") -> str:
    environment = Environment(loader=FileSystemLoader(THEME / "templates"))
    return environment.get_template("includes/content-footer.html").render(
        pet_content=content,
        SITEURL=siteurl,
    )


def notebook_content(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "jupyter_notebook": True,
        "notebook_html_contract": READER_HTML_CONTRACT,
        "nb_path": "downloads/theme006-notebook.ipynb",
        "related_posts": (),
        "source_url": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_notebook_source_hook_uses_exact_reader_metadata_mapping() -> None:
    rendered = render_content_footer(notebook_content())
    assert rendered.count("pet-notebook-source-link") == 1
    assert 'href="/downloads/theme006-notebook.ipynb"' in rendered
    assert "View or download source notebook" in rendered
    assert "download" in rendered

    absolute = render_content_footer(
        notebook_content(), siteurl="https://example.test/site"
    )
    assert (
        'href="https://example.test/site/downloads/theme006-notebook.ipynb"' in absolute
    )


@pytest.mark.parametrize(
    "unsafe",
    [
        None,
        "",
        "/downloads/notebook.ipynb",
        "//example.test/notebook.ipynb",
        "../private.ipynb",
        "./notebook.ipynb",
        "downloads/../private.ipynb",
        "javascript:alert(1)",
        "data:text/html,unsafe",
        "file:///private.ipynb",
        "https://example.test/notebook.ipynb",
        "downloads\\notebook.ipynb",
        'downloads/notebook.ipynb" onmouseover="alert(1)',
        "downloads/notebook.ipynb<script>alert(1)</script>",
        "downloads/notebook.ipynb\nscript",
    ],
)
def test_notebook_source_hook_omits_unsafe_paths(unsafe: object) -> None:
    rendered = render_content_footer(notebook_content(nb_path=unsafe))
    assert "pet-notebook-source-link" not in rendered
    assert "View or download source notebook" not in rendered


@pytest.mark.parametrize(
    "overrides",
    [
        {"jupyter_notebook": False},
        {"jupyter_notebook": "maybe"},
        {"notebook_html_contract": INPUT_CONTRACT_ID},
        {"notebook_html_contract": "jp-base-template-v1"},
        {"notebook_html_contract": ""},
    ],
)
def test_notebook_source_hook_omits_malformed_marker_or_contract(
    overrides: dict[str, object],
) -> None:
    assert "pet-notebook-source-link" not in render_content_footer(
        notebook_content(**overrides)
    )


@pytest.mark.parametrize(
    "siteurl",
    [
        "javascript:alert(1)",
        "//example.test",
        "http://",
        "https://",
        "https:///missing-authority",
        "https://example.test/#frag",
        "https://example.test?x=.ipynb",
        f"https://user{chr(64)}example.test",
        "https://example.test\\notebooks",
        "https://example.test/%2e%2e/notebooks",
        "https://example.test/unsafe path",
    ],
)
def test_notebook_source_hook_omits_malformed_siteurl(siteurl: str) -> None:
    assert "pet-notebook-source-link" not in render_content_footer(
        notebook_content(), siteurl=siteurl
    )


def test_generic_source_hook_and_non_notebook_article_remain_unchanged() -> None:
    generic = SimpleNamespace(
        jupyter_notebook=False,
        notebook_html_contract="",
        nb_path="",
        related_posts=(),
        source_url="https://example.test/source.txt",
        source_label="Inspect source",
    )
    rendered = render_content_footer(generic)
    assert 'class="pet-source-link"' in rendered
    assert "Inspect source" in rendered
    assert "pet-notebook-source-link" not in rendered


def test_notebook_css_and_local_table_scroller_are_namespaced() -> None:
    css = (THEME / "static/css/scaffold.css").read_text(encoding="utf-8")
    script = (THEME / "static/js/theme.js").read_text(encoding="utf-8")
    for selector in (
        ".pet-prose .highlight",
        ".pet-notebook-document .pet-prose .cell",
        ".pet-notebook-document .pet-notebook-region",
        ".pet-notebook-document .pet-prose .input_area",
        ".pet-notebook-document .pet-prose .output_error",
        ".pet-notebook-document .pet-prose .output_html",
        ".pet-notebook-document .pet-prose .plotly-graph-div",
    ):
        assert selector in css
    assert "overflow-x: auto" in css
    assert 'scroller.dataset.petTableScroller = "true"' in script
    assert 'scroller.setAttribute("role", "region")' in script
    assert 'scroller.setAttribute("tabindex", "0")' in script
    assert '"Scrollable notebook table: "' in script

    for forbidden in (
        ".pet-site-header .cell",
        ".pet-navigation .cell",
        ".pet-site-footer .cell",
    ):
        assert forbidden not in css


def test_no_execution_or_conversion_dependency_enters_theme_paths() -> None:
    scanned_paths = [
        *(ROOT / "src").rglob("*"),
        *(ROOT / ".github/workflows").glob("*.yml"),
        ROOT / "tests/site_build.py",
        ROOT / "examples/full/pelicanconf.py",
        ROOT / "examples/minimal/pelicanconf.py",
        ROOT / "pyproject.toml",
    ]
    assert (
        execution_boundary_errors(path for path in scanned_paths if path.is_file())
        == []
    )


def test_missing_notebook_article_makes_example_gate_red(tmp_path: Path) -> None:
    example = tmp_path / "missing-notebook"
    shutil.copytree(ROOT / "examples/full", example)
    (example / "content/notebook-presentation.md").unlink()
    output = build_copied_example(example)
    assert not (output / "notebook-presentation.html").exists()
