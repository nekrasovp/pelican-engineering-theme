from __future__ import annotations

import json
import shutil
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

import pelican_engineering_theme
from scripts.validate_content import (
    ContentContractParser,
    generated_content_errors,
    head_metadata_errors,
    json_ld_errors,
)
from tests.site_build import ROOT, build_copied_example, build_example

THEME = pelican_engineering_theme.get_theme_path()

REQUIRED_FULL_OUTPUTS = {
    "404.html",
    "archives.html",
    "authors.html",
    "categories.html",
    "index.html",
    "index2.html",
    "index3.html",
    "tags.html",
    "archived-interface.html",
    "configurable-shell.html",
    "deprecated-protocol.html",
    "long-technical-title.html",
    "multilingual-guide.html",
    "multilingual-guide-ru.html",
    "source-provenance.html",
    "pages/about.html",
    "author/example-editors.html",
    "author/example-editors2.html",
    "author/example-editors3.html",
    "category/guides.html",
    "category/guides2.html",
    "category/reference.html",
    "tag/example.html",
    "tag/example2.html",
    "tag/lifecycle.html",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.links.append(dict(attrs))


def configure_absolute_metadata(example: Path) -> None:
    config = example / "pelicanconf.py"
    original = config.read_text(encoding="utf-8")
    config.write_text(
        original.replace('SITEURL = ""', 'SITEURL = "https://example.test"')
        .replace("RELATIVE_URLS = True", "RELATIVE_URLS = False")
        + "\nFEED_ALL_ATOM = 'feeds/all.atom.xml'\n"
        + "FEED_ALL_RSS = 'feeds/all.rss.xml'\n"
        + "CATEGORY_FEED_ATOM = 'feeds/categories/{slug}.atom.xml'\n"
        + "CATEGORY_FEED_RSS = 'feeds/categories/{slug}.rss.xml'\n"
        + "TAG_FEED_ATOM = 'feeds/tags/{slug}.atom.xml'\n"
        + "TAG_FEED_RSS = 'feeds/tags/{slug}.rss.xml'\n"
        + "AUTHOR_FEED_ATOM = 'feeds/authors/{slug}.atom.xml'\n"
        + "AUTHOR_FEED_RSS = 'feeds/authors/{slug}.rss.xml'\n"
        + "TRANSLATION_FEED_ATOM = 'feeds/languages/{lang}.atom.xml'\n"
        + "TRANSLATION_FEED_RSS = 'feeds/languages/{lang}.rss.xml'\n",
        encoding="utf-8",
    )


def json_schemas(markup: str) -> list[dict[str, object]]:
    parser = ContentContractParser()
    parser.feed(markup)
    return [json.loads(raw) for raw in parser.json_scripts]


def test_full_fixture_generates_every_content_surface(tmp_path: Path) -> None:
    output = build_example("full", tmp_path)
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*.html")
    }
    assert REQUIRED_FULL_OUTPUTS <= actual
    assert generated_content_errors(output) == []

    first = (output / "index.html").read_text(encoding="utf-8")
    middle = (output / "index2.html").read_text(encoding="utf-8")
    last = (output / "index3.html").read_text(encoding="utf-8")
    assert 'rel="prev"' not in first and 'rel="next"' in first
    assert 'rel="prev"' in middle and 'rel="next"' in middle
    assert 'rel="prev"' in last and 'rel="next"' not in last

    english = (output / "multilingual-guide.html").read_text(encoding="utf-8")
    russian = (output / "multilingual-guide-ru.html").read_text(encoding="utf-8")
    assert '<html lang="en">' in english
    assert '<html lang="ru">' in russian
    assert 'hreflang="ru" lang="ru"' in english
    assert 'hreflang="en" lang="en"' in russian

    updated = (output / "configurable-shell.html").read_text(encoding="utf-8")
    assert "<dt>Published</dt>" in updated
    assert "<dt>Updated</dt>" in updated
    assert updated.count("<time ") >= 2

    archived = (output / "archived-interface.html").read_text(encoding="utf-8")
    deprecated = (output / "deprecated-protocol.html").read_text(encoding="utf-8")
    assert 'data-content-status="archive" role="note"' in archived
    assert 'data-content-status="deprecated" role="note"' in deprecated
    assert "pet-content-status--deprecated" not in archived
    assert "pet-content-status--archive" not in deprecated

    long_form = (output / "long-technical-title.html").read_text(encoding="utf-8")
    for markup in ("<table>", "<blockquote>", "<figure>", "<figcaption>", "footnote"):
        assert markup in long_form
    assert "class=\"highlight\"" in long_form

    source = (output / "source-provenance.html").read_text(encoding="utf-8")
    assert 'class="pet-source-link"' in source
    error_page = (output / "404.html").read_text(encoding="utf-8")
    assert 'rel="canonical"' not in error_page
    assert 'property="og:' not in error_page
    assert 'application/ld+json' not in error_page


def test_absolute_canonical_feeds_and_structured_data(tmp_path: Path) -> None:
    example = tmp_path / "absolute"
    shutil.copytree(ROOT / "examples/full", example)
    configure_absolute_metadata(example)
    output = build_copied_example(example)
    assert generated_content_errors(output) == []

    expected_canonicals = {
        "index.html": "https://example.test/index.html",
        "archives.html": "https://example.test/archives.html",
        "categories.html": "https://example.test/categories.html",
        "tags.html": "https://example.test/tags.html",
        "authors.html": "https://example.test/authors.html",
        "category/guides.html": "https://example.test/category/guides.html",
        "tag/example.html": "https://example.test/tag/example.html",
        "author/example-editors.html": "https://example.test/author/example-editors.html",
        "configurable-shell.html": "https://example.test/configurable-shell.html",
        "pages/about.html": "https://example.test/pages/about.html",
    }
    for relative, expected in expected_canonicals.items():
        parser = ContentContractParser()
        parser.feed((output / relative).read_text(encoding="utf-8"))
        assert parser.canonical_urls == [expected], relative

    error_parser = ContentContractParser()
    error_parser.feed((output / "404.html").read_text(encoding="utf-8"))
    assert error_parser.canonical_urls == []
    assert error_parser.feed_urls == [
        "https://example.test/feeds/all.atom.xml",
        "https://example.test/feeds/all.rss.xml",
    ]

    category_parser = ContentContractParser()
    category_parser.feed(
        (output / "category/guides.html").read_text(encoding="utf-8")
    )
    assert "https://example.test/feeds/categories/guides.atom.xml" in (
        category_parser.feed_urls
    )
    assert "https://example.test/feeds/categories/guides.rss.xml" in (
        category_parser.feed_urls
    )

    index_schemas = json_schemas((output / "index.html").read_text(encoding="utf-8"))
    assert {schema["@type"] for schema in index_schemas} == {"Person", "WebSite"}
    article_markup = (output / "configurable-shell.html").read_text(encoding="utf-8")
    article_schemas = json_schemas(article_markup)
    assert [schema["@type"] for schema in article_schemas] == ["TechArticle"]
    assert article_schemas[0]["url"] == (
        "https://example.test/configurable-shell.html"
    )


def test_empty_taxonomies_and_optional_values_omit_containers(tmp_path: Path) -> None:
    example = tmp_path / "empty"
    shutil.copytree(ROOT / "examples/minimal", example)
    (example / "content/hello.md").unlink()
    pages = example / "content/pages"
    pages.mkdir()
    (pages / "only.md").write_text(
        "Title: Only Page\nSlug: only\n\nNo article taxonomies are present.\n",
        encoding="utf-8",
    )
    output = build_copied_example(example)
    assert generated_content_errors(output) == []
    for relative, forbidden in (
        ("index.html", "pet-entry-list"),
        ("archives.html", "pet-archive-list"),
        ("categories.html", "pet-taxonomy-list"),
        ("tags.html", "pet-taxonomy-list"),
        ("authors.html", "pet-taxonomy-list"),
    ):
        assert forbidden not in (output / relative).read_text(encoding="utf-8")

    environment = Environment(loader=FileSystemLoader(THEME / "templates"))
    empty = SimpleNamespace(
        archive_notice="",
        deprecated_warning="",
        related_posts=(),
        source_url="",
        translations=(),
    )
    for include in ("content-status.html", "content-footer.html", "translations.html"):
        rendered = environment.get_template(f"includes/{include}").render(
            pet_content=empty,
            SITEURL="",
        )
        assert rendered.strip() == ""


def test_malformed_metadata_omits_broken_head_and_schema(tmp_path: Path) -> None:
    example = tmp_path / "malformed"
    shutil.copytree(ROOT / "examples/minimal", example)
    config = example / "pelicanconf.py"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nSITEURL = 'javascript:alert(1)'\n"
        + "FEED_ALL_ATOM = ''\n"
        + "FEED_ALL_RSS = None\n"
        + "ENGINEERING_THEME_JSON_LD_PERSON = {'name': 'Incomplete'}\n"
        + "ENGINEERING_THEME_JSON_LD_WEBSITE = {'url': 'https://example.test'}\n"
        + "ENGINEERING_THEME_ENABLE_ARTICLE_JSON_LD = True\n"
        + "ENGINEERING_THEME_ARTICLE_SCHEMA_TYPE = 'NewsArticle'\n",
        encoding="utf-8",
    )
    output = build_copied_example(example)
    for path in output.rglob("*.html"):
        markup = path.read_text(encoding="utf-8")
        assert 'rel="canonical"' not in markup
        assert 'property="og:' not in markup
        assert 'name="twitter:' not in markup
        assert 'application/ld+json' not in markup
        assert head_metadata_errors(markup) == []
        assert json_ld_errors(markup) == []

    environment = Environment(loader=FileSystemLoader(THEME / "templates"))
    malformed_feeds = environment.get_template(
        "includes/feed-discovery.html"
    ).render(
        pet_siteurl_valid=True,
        pet_siteurl="https://example.test",
        pet_content=None,
        SITENAME="Fixture",
        FEED_ALL_ATOM=True,
        FEED_ALL_RSS={"bad": "value"},
    )
    assert 'rel="alternate"' not in malformed_feeds

    malformed_image = environment.get_template(
        "includes/social-metadata.html"
    ).render(
        pet_content=None,
        pet_document_title="Complete title",
        pet_canonical_url="https://example.test/article.html",
        ENGINEERING_THEME_SOCIAL_IMAGE="javascript:alert(1)",
    )
    assert 'property="og:title"' in malformed_image
    assert 'property="og:image"' not in malformed_image
    assert 'name="twitter:image"' not in malformed_image


def test_json_ld_and_attribute_breakout_are_escaped(tmp_path: Path) -> None:
    example = tmp_path / "breakout"
    shutil.copytree(ROOT / "examples/full", example)
    configure_absolute_metadata(example)
    article = example / "content/hello.md"
    original = article.read_text(encoding="utf-8")
    article.write_text(
        original.replace(
            "Title: A Configurable Shell",
            'Title: Closing </script><script data-injected="true"> Hazard',
        ),
        encoding="utf-8",
    )
    output = build_copied_example(example)
    markup = (output / "configurable-shell.html").read_text(encoding="utf-8")
    assert '<script data-injected="true">' not in markup
    assert "\\u003c/script\\u003e" in markup
    assert json_ld_errors(markup) == []

    environment = Environment(loader=FileSystemLoader(THEME / "templates"))
    malicious = SimpleNamespace(
        related_posts=(),
        source_url='https://example.test/\" onmouseover=\"alert(1)',
        source_label='Source <unsafe>',
    )
    footer = environment.get_template("includes/content-footer.html").render(
        pet_content=malicious,
        SITEURL="",
    )
    assert 'onmouseover="alert(1)' not in footer
    assert "&#34; onmouseover=&#34;alert(1)" in footer
    parser = LinkParser()
    parser.feed(footer)
    assert len(parser.links) == 1
    assert set(parser.links[0]) == {"href"}


def test_site_and_taxonomy_titles_escape_tag_breakout(tmp_path: Path) -> None:
    example = tmp_path / "taxonomy-breakout"
    shutil.copytree(ROOT / "examples/full", example)
    config = example / "pelicanconf.py"
    config.write_text(
        config.read_text(encoding="utf-8")
        + '\nSITENAME = \'Fixture </h1><script data-site-breakout="true">\'\n',
        encoding="utf-8",
    )
    article = example / "content/hello.md"
    original = article.read_text(encoding="utf-8")
    article.write_text(
        original.replace(
            "Category: Guides\nTags: example",
            'Category: Guide </h1><script data-category-breakout="true">\n'
            'Tags: Tag </h1><script data-tag-breakout="true">\n'
            'Author: Writer </h1><script data-author-breakout="true">',
        ),
        encoding="utf-8",
    )

    output = build_copied_example(example)
    direct_pages = [
        output / relative
        for relative in (
            "index.html",
            "archives.html",
            "categories.html",
            "tags.html",
            "authors.html",
            "404.html",
        )
    ]
    direct_markup = "\n".join(
        path.read_text(encoding="utf-8") for path in direct_pages
    )
    assert '<script data-site-breakout="true">' not in direct_markup
    assert "&lt;/h1&gt;&lt;script data-site-breakout=&#34;true&#34;&gt;" in (
        direct_markup
    )

    for taxonomy, marker in (
        ("category", "category-breakout"),
        ("tag", "tag-breakout"),
        ("author", "author-breakout"),
    ):
        detail_pages = list((output / taxonomy).glob("*.html"))
        detail_markup = "\n".join(
            path.read_text(encoding="utf-8") for path in detail_pages
        )
        assert f'<script data-{marker}="true">' not in detail_markup
        assert f"&lt;/h1&gt;&lt;script data-{marker}=&#34;true&#34;&gt;" in (
            detail_markup
        )


def test_related_posts_and_safe_source_hooks_render_without_services() -> None:
    environment = Environment(loader=FileSystemLoader(THEME / "templates"))
    content = SimpleNamespace(
        related_posts=(
            SimpleNamespace(title="A related note", url="related-note.html"),
        ),
        source_url="https://example.test/source.txt",
        source_label="Source record",
    )
    rendered = environment.get_template("includes/content-footer.html").render(
        pet_content=content,
        SITEURL="",
    )
    assert 'class="pet-related-posts"' in rendered
    assert 'href="/related-note.html"' in rendered
    assert 'class="pet-source-link"' in rendered
    assert "analytics" not in rendered.lower()
    assert "script" not in rendered.lower()

    protocol_relative = SimpleNamespace(
        related_posts=(),
        source_url="//evil.example/collector",
        source_label="Unsafe external service",
    )
    omitted = environment.get_template("includes/content-footer.html").render(
        pet_content=protocol_relative,
        SITEURL="",
    )
    assert omitted.strip() == ""
