#!/usr/bin/env python3
"""Validate generated metadata and JSON-LD content contracts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from scripts.validate_shell import document_shell_errors

SCHEMA_REQUIRED_FIELDS = {
    "Person": {"@context", "@type", "name", "url"},
    "WebSite": {"@context", "@type", "name", "url"},
    "Article": {
        "@context",
        "@type",
        "author",
        "datePublished",
        "headline",
        "inLanguage",
        "url",
    },
    "TechArticle": {
        "@context",
        "@type",
        "author",
        "datePublished",
        "headline",
        "inLanguage",
        "url",
    },
}


class ContentContractParser(HTMLParser):
    """Collect content-head and JSON-LD facts from generated HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical_urls: list[str] = []
        self.feed_urls: list[str] = []
        self.meta_properties: Counter[str] = Counter()
        self.meta_names: Counter[str] = Counter()
        self.json_scripts: list[str] = []
        self._json_chunks: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonical_urls.append(attributes.get("href") or "")
        if (
            tag == "link"
            and attributes.get("rel") == "alternate"
            and attributes.get("type")
            in {"application/atom+xml", "application/rss+xml"}
        ):
            self.feed_urls.append(attributes.get("href") or "")
        if tag == "meta" and attributes.get("property"):
            self.meta_properties[attributes["property"] or ""] += 1
        if tag == "meta" and attributes.get("name"):
            self.meta_names[attributes["name"] or ""] += 1
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._json_chunks = []

    def handle_data(self, data: str) -> None:
        if self._json_chunks is not None:
            self._json_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_chunks is not None:
            self.json_scripts.append("".join(self._json_chunks))
            self._json_chunks = None


def _is_absolute_http_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("https://", "http://"))


def json_ld_errors(markup: str) -> list[str]:
    """Return JSON syntax and focused schema-contract errors."""
    parser = ContentContractParser()
    parser.feed(markup)
    errors: list[str] = []
    for index, raw_json in enumerate(parser.json_scripts):
        try:
            schema = json.loads(raw_json)
        except json.JSONDecodeError as error:
            errors.append(f"JSON-LD script {index} is invalid: {error.msg}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"JSON-LD script {index} must contain an object")
            continue
        schema_type = schema.get("@type")
        if schema_type not in SCHEMA_REQUIRED_FIELDS:
            errors.append(
                f"JSON-LD script {index} has unsupported @type {schema_type!r}"
            )
            continue
        missing = SCHEMA_REQUIRED_FIELDS[schema_type] - schema.keys()
        if missing:
            errors.append(
                f"JSON-LD {schema_type} is missing fields: {sorted(missing)!r}"
            )
        if schema.get("@context") != "https://schema.org":
            errors.append(f"JSON-LD {schema_type} has an invalid @context")
        if not _is_absolute_http_url(schema.get("url")):
            errors.append(f"JSON-LD {schema_type} must have an absolute HTTP URL")
        if schema_type in {"Article", "TechArticle"}:
            author = schema.get("author")
            if not isinstance(author, dict) or not author.get("name"):
                errors.append(f"JSON-LD {schema_type} must have a named author")
    if parser._json_chunks is not None:
        errors.append("JSON-LD script is missing its closing tag")
    return errors


def head_metadata_errors(markup: str) -> list[str]:
    """Return canonical, feed, Open Graph, and Twitter contract errors."""
    parser = ContentContractParser()
    parser.feed(markup)
    errors: list[str] = []
    if len(parser.canonical_urls) > 1:
        errors.append(
            f"expected at most one canonical URL, found {parser.canonical_urls}"
        )
    for url in [*parser.canonical_urls, *parser.feed_urls]:
        if not _is_absolute_http_url(url):
            errors.append(f"discovery URL is not absolute HTTP: {url!r}")
    if parser.meta_properties["og:type"]:
        for required in ("og:type", "og:title", "og:url"):
            if parser.meta_properties[required] != 1:
                errors.append(f"Open Graph field {required} must appear exactly once")
        for required in ("twitter:card", "twitter:title"):
            if parser.meta_names[required] != 1:
                errors.append(f"Twitter field {required} must appear exactly once")
    elif any(name.startswith("twitter:") for name in parser.meta_names):
        errors.append(
            "Twitter metadata must not appear without complete Open Graph data"
        )
    return errors


def generated_content_errors(output: Path) -> list[str]:
    """Validate every generated HTML document below an output directory."""
    html_files = sorted(output.rglob("*.html"))
    if not html_files:
        return [f"no generated HTML files below {output}"]
    errors: list[str] = []
    for path in html_files:
        markup = path.read_text(encoding="utf-8")
        relative = path.relative_to(output)
        for error in [
            *document_shell_errors(markup),
            *head_metadata_errors(markup),
            *json_ld_errors(markup),
        ]:
            errors.append(f"{relative}: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outputs", nargs="+", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    for output in args.outputs:
        errors.extend(generated_content_errors(output))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated generated content in {len(args.outputs)} output tree(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
