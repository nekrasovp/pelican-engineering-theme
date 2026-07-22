#!/usr/bin/env python3
"""Validate the immutable PLUGIN-003 notebook fragment presentation input."""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

INPUT_CONTRACT_ID = "plugin003-nbconvert-basic-v1"
READER_HTML_CONTRACT = "nbconvert-basic.v1"
READER_COMMIT = "137e1eb0ea620f1b15fff0ba81725eea23de1b7a"
READER_FIXTURE_PATH = (
    "pelican_jupyter/tests/fixtures/nbconvert-basic.v1/"
    "representative.fragment.html"
)
EXPECTED_FIXTURE_SHA256 = (
    "b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf"
)
EXPECTED_FIXTURE_BYTES = 4465
NBCONVERT_TAG = "v7.17.1"
NBCONVERT_COMMIT = "78ed30837a607deab7cf0a12dca072bf3f63417a"

REQUIRED_CELL_IDS = frozenset(
    {
        "cell-id=markdown-contract",
        "cell-id=code-contract",
        "cell-id=png-contract",
        "cell-id=svg-contract",
        "cell-id=table-contract",
        "cell-id=error-contract",
        "cell-id=rich-contract",
    }
)
EXPECTED_STATE_COUNTS = {
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
REQUIRED_TEXT_MARKERS = (
    "Generic notebook contract",
    "committed-code-output",
    "SyntheticError: committed error output",
    'data-contract="rich"',
    "generic-rich-output",
)


@dataclass(frozen=True)
class FragmentFacts:
    """Contract-relevant facts collected without evaluating trusted markup."""

    cell_ids: frozenset[str]
    class_counts: Counter[str]
    state_counts: dict[str, int]
    document_wrappers: tuple[str, ...]
    jp_tokens: frozenset[str]


class _FragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.class_counts: Counter[str] = Counter()
        self.cell_ids: set[str] = set()
        self.tag_counts: Counter[str] = Counter()
        self.document_wrappers: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        normalized_tag = tag.casefold()
        self.tag_counts[normalized_tag] += 1
        if normalized_tag in {"html", "body"}:
            self.document_wrappers.append(normalized_tag)
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id and element_id.startswith("cell-id="):
            self.cell_ids.add(element_id)
        for token in (attributes.get("class") or "").split():
            self.class_counts[token] += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in {"html", "body"}:
            self.document_wrappers.append(f"/{normalized_tag}")


def fragment_facts(markup: str) -> FragmentFacts:
    """Return exact class/state counts without sanitizing or running the fragment."""
    parser = _FragmentParser()
    parser.feed(markup)
    parser.close()
    classes = parser.class_counts
    states = {
        "cells": classes["cell"],
        "code_cells": classes["code_cell"],
        "error_outputs": classes["output_error"],
        "html_outputs": classes["output_html"],
        "input_areas": classes["input_area"],
        "markdown_cells": classes["text_cell"],
        "output_areas": classes["output_area"],
        "png_outputs": classes["output_png"],
        "stream_outputs": classes["output_stream"],
        "svg_outputs": classes["output_svg"],
        "tables": parser.tag_counts["table"],
        "trusted_scripts": parser.tag_counts["script"],
    }
    return FragmentFacts(
        cell_ids=frozenset(parser.cell_ids),
        class_counts=classes,
        state_counts=states,
        document_wrappers=tuple(parser.document_wrappers),
        jp_tokens=frozenset(
            token for token in classes if token.casefold().startswith("jp-")
        ),
    )


def fragment_contract_errors(markup: str) -> list[str]:
    """Return fail-closed errors for the frozen raw fragment contract."""
    facts = fragment_facts(markup)
    errors: list[str] = []
    if facts.document_wrappers:
        errors.append(
            "fragment contains nested document wrappers: "
            f"{list(facts.document_wrappers)!r}"
        )
    if facts.jp_tokens:
        errors.append(
            f"fragment contains unsupported jp-* classes: {facts.jp_tokens!r}"
        )
    if facts.cell_ids != REQUIRED_CELL_IDS:
        errors.append(
            "fixture cell IDs differ: "
            f"found {sorted(facts.cell_ids)!r}, expected {sorted(REQUIRED_CELL_IDS)!r}"
        )
    if facts.state_counts != EXPECTED_STATE_COUNTS:
        errors.append(
            "fixture state counts differ: "
            f"found {facts.state_counts!r}, expected {EXPECTED_STATE_COUNTS!r}"
        )
    for marker in REQUIRED_TEXT_MARKERS:
        if marker not in markup:
            errors.append(f"fixture is missing content marker: {marker!r}")
    return errors


def fixture_errors(path: Path) -> list[str]:
    """Verify source bytes, digest, UTF-8, and every frozen content state."""
    if not path.is_file():
        return [f"missing fixture: {path}"]
    raw = path.read_bytes()
    errors: list[str] = []
    if len(raw) != EXPECTED_FIXTURE_BYTES:
        errors.append(
            f"fixture bytes are {len(raw)}, expected {EXPECTED_FIXTURE_BYTES}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_FIXTURE_SHA256:
        errors.append(
            f"fixture SHA-256 is {digest}, expected {EXPECTED_FIXTURE_SHA256}"
        )
    try:
        markup = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        errors.append(f"fixture is not UTF-8: {error}")
    else:
        errors.extend(fragment_contract_errors(markup))
    return errors


def execution_boundary_errors(paths: Iterable[Path]) -> list[str]:
    """Reject conversion/execution machinery from runtime and build entrypoints."""
    forbidden = (
        "executepreprocessor",
        "execute_notebook",
        "html" + "exporter",
        "import nb" + "convert",
        "from nb" + "convert",
        "jupyter nb" + "convert",
        "nb" + "client",
        "start_kernel",
        "--execute",
    )
    errors: list[str] = []
    for path in paths:
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8").casefold()
        except UnicodeDecodeError:
            continue
        for marker in forbidden:
            if marker in text:
                errors.append(f"{path}: forbidden notebook machinery {marker!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    errors = fixture_errors(args.fixture)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"Verified {INPUT_CONTRACT_ID} ({READER_HTML_CONTRACT}): "
        f"{EXPECTED_FIXTURE_BYTES} bytes, "
        f"SHA-256 {EXPECTED_FIXTURE_SHA256}, {len(REQUIRED_CELL_IDS)} cells"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
