from pathlib import Path

import pytest

from tests.site_build import build_example


@pytest.mark.parametrize("example_name", ["minimal", "full"])
def test_example_builds(example_name: str, tmp_path: Path) -> None:
    output = build_example(example_name, tmp_path)
    article = (
        "small-technical-note.html"
        if example_name == "minimal"
        else "configurable-shell.html"
    )

    assert (output / "index.html").is_file()
    assert (output / article).is_file()
    assert (output / "theme/css/scaffold.css").is_file()
    assert (output / "theme/js/theme.js").is_file()

    index = (output / "index.html").read_text(encoding="utf-8")
    assert index.index("data-pet-theme-loader") < index.index('rel="stylesheet"')
    assert 'meta name="theme-color" content="#f7f8f3"' in index
    assert "data-pet-theme-toggle" in index
    assert "/theme/js/theme.js" in index
    assert 'class="pet-skip-link" href="#main-content"' in index
    assert 'id="main-content"' in index

    if example_name == "minimal":
        assert "<nav" not in index
        assert "pet-language-link" not in index
        assert "<footer" not in index
    else:
        for configured in (
            "Systems Journal",
            "Overview",
            "Guides",
            "Reference",
            "Français",
            "A generic technical publication example.",
            "Built with Pelican",
        ):
            assert configured in index
        for override in (
            "Child-template metadata override fixture",
            "https://example.test/",
            "pet-fixture-body",
            "pet-fixture-page",
            "Child-template hero override fixture",
            "fixture-script",
        ):
            assert override in index
