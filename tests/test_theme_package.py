from __future__ import annotations

from importlib.metadata import metadata, version
from pathlib import Path

import pelican_engineering_theme

REQUIRED_THEME_FILES = {
    "templates/archives.html",
    "templates/article.html",
    "templates/author.html",
    "templates/authors.html",
    "templates/base.html",
    "templates/categories.html",
    "templates/category.html",
    "templates/index.html",
    "templates/page.html",
    "templates/period_archives.html",
    "templates/tag.html",
    "templates/tags.html",
    "templates/includes/theme-toggle.html",
    "static/css/scaffold.css",
    "static/js/theme.js",
}

PUBLIC_BLOCKS = (
    "html_head",
    "head_meta",
    "head_styles",
    "body_start",
    "site_header",
    "site_navigation",
    "content_header",
    "content",
    "content_footer",
    "site_footer",
    "scripts",
    "body_end",
)


def test_distribution_identity() -> None:
    project_metadata = metadata("pelican-engineering-theme")

    assert project_metadata["Name"] == "pelican-engineering-theme"
    assert project_metadata["License-Expression"] == "MIT"
    assert version("pelican-engineering-theme") == "0.0.0.dev0"
    assert pelican_engineering_theme.__version__ == "0.0.0.dev0"


def test_get_theme_path_returns_complete_filesystem_theme() -> None:
    theme_path = pelican_engineering_theme.get_theme_path()

    assert isinstance(theme_path, Path)
    assert theme_path.is_dir()
    assert {
        str(path.relative_to(theme_path))
        for path in theme_path.rglob("*")
        if path.is_file()
    } >= REQUIRED_THEME_FILES


def test_base_exposes_reserved_blocks_in_contract_order() -> None:
    base_path = pelican_engineering_theme.get_theme_path() / "templates/base.html"
    base = base_path.read_text(encoding="utf-8")

    positions = [base.index(f"{{% block {block}") for block in PUBLIC_BLOCKS]
    assert positions == sorted(positions)


def test_scaffold_asset_respects_runtime_asset_boundary() -> None:
    theme_path = pelican_engineering_theme.get_theme_path()
    packaged_files = [path for path in theme_path.rglob("*") if path.is_file()]

    assert {
        str(path.relative_to(theme_path))
        for path in packaged_files
        if path.suffix.lower() == ".js"
    } == {"static/js/theme.js"}
    assert not any(
        path.suffix.lower() in {".woff", ".woff2", ".ttf", ".otf", ".eot"}
        for path in packaged_files
    )
    css = (theme_path / "static/css/scaffold.css").read_text(encoding="utf-8")
    javascript = (theme_path / "static/js/theme.js").read_text(encoding="utf-8")
    assert "@import" not in css
    assert "http://" not in css
    assert "https://" not in css
    assert "http://" not in javascript
    assert "https://" not in javascript
