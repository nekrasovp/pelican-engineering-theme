#!/usr/bin/env python3
"""Validate generated document shells and reusable runtime boundaries."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
from html.parser import HTMLParser
from pathlib import Path

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

CSS_SHELL_CONTRACT = {
    "skip link base style": ".pet-skip-link {",
    "skip link visible focus style": ".pet-skip-link:focus {",
    "keyboard focus indicator": ":focus-visible {",
    "wrapping header": "flex-wrap: wrap;",
    "narrow-content protection": "min-width: 0;",
    "long-label protection": "overflow-wrap: anywhere;",
    "responsive shell query": "@media (max-width: 32rem)",
}

FORBIDDEN_RUNTIME_DEFAULTS = {
    "nekrasovp.ru",
    "nekrasovp.github.io",
    "7581719+nekrasovp",
    "google-analytics",
    "googletagmanager",
    "bootstrap",
}


class ShellParser(HTMLParser):
    """Collect strict-enough structural facts from a generated HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.declarations: list[str] = []
        self.counts: Counter[str] = Counter()
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.skip_links = 0
        self.main_target = 0

    def handle_decl(self, decl: str) -> None:
        self.declarations.append(decl.lower())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counts[tag] += 1
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.errors.append(f"duplicate id: {element_id}")
            self.ids.add(element_id)
        classes = set((attributes.get("class") or "").split())
        if tag == "a" and "pet-skip-link" in classes:
            self.skip_links += 1
            if attributes.get("href") != "#main-content":
                self.errors.append("skip link must target #main-content")
        if tag == "main" and element_id == "main-content":
            self.main_target += 1
            if attributes.get("tabindex") != "-1":
                self.errors.append("main-content must have tabindex=-1")
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            self.errors.append(f"void element has closing tag: {tag}")
            return
        if not self.stack:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        expected = self.stack.pop()
        if expected != tag:
            self.errors.append(f"closing tag {tag} does not match {expected}")


def document_shell_errors(markup: str) -> list[str]:
    """Return generated-shell parse and structure errors."""
    parser = ShellParser()
    parser.feed(markup)
    parser.close()
    errors = list(parser.errors)
    if parser.stack:
        errors.append(f"unclosed elements: {parser.stack}")
    if parser.declarations != ["doctype html"]:
        errors.append(f"expected one HTML5 doctype, found {parser.declarations}")
    for tag in ("html", "head", "body", "main"):
        if parser.counts[tag] != 1:
            errors.append(f"expected one {tag} element, found {parser.counts[tag]}")
    if parser.skip_links != 1:
        errors.append(f"expected one skip link, found {parser.skip_links}")
    if parser.main_target != 1:
        errors.append(f"expected one main-content target, found {parser.main_target}")
    return errors


def generated_html_errors(output: Path) -> list[str]:
    """Validate every generated HTML document below an output directory."""
    html_files = sorted(output.rglob("*.html"))
    if not html_files:
        return [f"no generated HTML files below {output}"]
    errors: list[str] = []
    for path in html_files:
        for error in document_shell_errors(path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(output)}: {error}")
    return errors


def css_shell_contract_errors(css: str) -> list[str]:
    """Return missing focus, wrapping, and narrow-viewport safeguards."""
    return [
        f"missing {name}: {snippet}"
        for name, snippet in CSS_SHELL_CONTRACT.items()
        if snippet not in css
    ]


def focus_order_errors(actual: list[str], expected: list[str]) -> list[str]:
    """Return an error when keyboard focus does not follow document order."""
    if actual == expected:
        return []
    return [f"focus order is {actual!r}, expected {expected!r}"]


def runtime_default_errors(paths: Iterable[Path]) -> list[str]:
    """Reject personal defaults, frameworks, and remote runtime assets."""
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in sorted(FORBIDDEN_RUNTIME_DEFAULTS):
            if forbidden in text:
                errors.append(f"{path}: forbidden runtime default {forbidden!r}")
        if "@import" in text or "url(http" in text:
            errors.append(f"{path}: remote CSS asset is forbidden")
        if '<script src="http' in text or "<script src='http" in text:
            errors.append(f"{path}: remote runtime script is forbidden")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outputs", nargs="+", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    for output in args.outputs:
        errors.extend(generated_html_errors(output))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated generated HTML shells in {len(args.outputs)} output tree(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
