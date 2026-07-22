#!/usr/bin/env python3
"""Validate documentation links and exact screenshot provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs/screenshots"
PROVENANCE = SCREENSHOT_DIR / "provenance.json"
LINK = re.compile(r"(!?)\[[^\]]*\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "dist",
    "node_modules",
    "output",
}
RENDER_INPUTS = (
    ROOT / "src/pelican_engineering_theme",
    ROOT / "examples/full",
    ROOT / "scripts/capture_readme_screenshots.py",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
    ROOT / "package.json",
    ROOT / "package-lock.json",
)
EXPECTED_CAPTURES: dict[str, tuple[str, str, int, int]] = {
    "home-light.png": ("/", "light", 1440, 1000),
    "home-dark.png": ("/", "dark", 1440, 1000),
    "article-light.png": ("/configurable-shell.html", "light", 1440, 1000),
    "archive-light.png": ("/archives.html", "light", 1440, 1000),
    "notebook-dark.png": ("/notebook-presentation.html", "dark", 1440, 1000),
}


def markdown_files() -> list[Path]:
    """Return repository Markdown files outside generated/dependency trees."""
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.parts)
    )


def github_anchor(value: str) -> str:
    """Approximate GitHub's stable ASCII heading anchor algorithm."""
    value = re.sub(r"`([^`]*)`", r"\1", value).strip().lower()
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s]+", "-", value)


def anchors(path: Path) -> set[str]:
    """Return unique heading anchors, including duplicate suffixes."""
    counts: dict[str, int] = {}
    result: set[str] = set()
    for heading in HEADING.findall(path.read_text(encoding="utf-8")):
        base = github_anchor(heading)
        index = counts.get(base, 0)
        counts[base] = index + 1
        result.add(base if index == 0 else f"{base}-{index}")
    return result


def split_target(raw: str) -> tuple[str, str]:
    """Return URL/path and fragment, excluding an optional Markdown title."""
    target = raw.strip().strip("<>")
    if ' "' in target:
        target = target.split(' "', 1)[0]
    path, separator, fragment = target.partition("#")
    return path, fragment if separator else ""


def local_link_errors() -> tuple[list[str], set[str]]:
    """Validate every local file, image, and Markdown fragment."""
    errors: list[str] = []
    external: set[str] = set()
    for document in markdown_files():
        text = document.read_text(encoding="utf-8")
        for image_marker, raw_target in LINK.findall(text):
            target, fragment = split_target(raw_target)
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme != "https" or not parsed.netloc or parsed.username:
                    errors.append(
                        f"{document.relative_to(ROOT)}: external link must be "
                        f"credential-free HTTPS: {target}"
                    )
                else:
                    external.add(target)
                continue
            if target.startswith("mailto:"):
                errors.append(
                    f"{document.relative_to(ROOT)}: mailto links are forbidden"
                )
                continue

            decoded = unquote(target)
            destination = document if not decoded else document.parent / decoded
            destination = destination.resolve()
            try:
                destination.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"{document.relative_to(ROOT)}: link escapes repository: {target}"
                )
                continue
            if not destination.exists():
                errors.append(
                    f"{document.relative_to(ROOT)}: broken local link: {target}"
                )
                continue
            if image_marker and not destination.is_file():
                errors.append(
                    f"{document.relative_to(ROOT)}: image is not a file: {target}"
                )
            if fragment and destination.suffix.lower() == ".md":
                decoded_fragment = unquote(fragment).lower()
                if decoded_fragment not in anchors(destination):
                    errors.append(
                        f"{document.relative_to(ROOT)}: missing Markdown anchor "
                        f"{fragment!r} in {destination.relative_to(ROOT)}"
                    )
    return errors, external


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_input_files() -> list[Path]:
    """Return the exact non-circular input set for committed captures."""
    result: set[Path] = set()
    for input_path in RENDER_INPUTS:
        if input_path.is_file():
            result.add(input_path)
        elif input_path.is_dir():
            result.update(
                path
                for path in input_path.rglob("*")
                if path.is_file() and "output" not in path.parts
            )
    return sorted(result)


def render_tree_sha256() -> str:
    """Hash each render input's path and bytes in deterministic order."""
    digest = hashlib.sha256()
    for path in render_input_files():
        relative = str(path.relative_to(ROOT)).encode()
        digest.update(relative + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\n")
    return digest.hexdigest()


def screenshot_provenance_errors(
    manifest: dict[str, Any], screenshot_dir: Path = SCREENSHOT_DIR
) -> list[str]:
    """Return stale input, wrong-source, and screenshot byte errors."""
    errors: list[str] = []
    expected_values: dict[str, object] = {
        "schema_version": 1,
        "source_kind": "first-party-generic-example",
        "candidate_only": True,
        "runtime_network_requests": 0,
        "source_tree_sha256": render_tree_sha256(),
    }
    for key, expected in expected_values.items():
        if manifest.get(key) != expected:
            errors.append(
                f"screenshot provenance {key} is {manifest.get(key)!r}, "
                f"expected {expected!r}"
            )

    raw_captures = manifest.get("captures")
    if not isinstance(raw_captures, list):
        errors.append("screenshot provenance captures must be a list")
        raw_captures = []
    by_name = {
        item.get("file"): item for item in raw_captures if isinstance(item, dict)
    }
    if set(by_name) != set(EXPECTED_CAPTURES):
        errors.append(
            f"screenshot names are {sorted(str(name) for name in by_name)!r}, "
            f"expected {sorted(EXPECTED_CAPTURES)!r}"
        )
    for name, (route, theme, width, height) in EXPECTED_CAPTURES.items():
        record = by_name.get(name)
        if not isinstance(record, dict):
            continue
        expected_record = {
            "route": route,
            "theme": theme,
            "viewport": {"width": width, "height": height},
        }
        for key, expected in expected_record.items():
            if record.get(key) != expected:
                errors.append(
                    f"{name}: {key} is {record.get(key)!r}, expected {expected!r}"
                )
        path = screenshot_dir / name
        if not path.is_file():
            errors.append(f"missing screenshot: {name}")
            continue
        if record.get("bytes") != path.stat().st_size:
            errors.append(f"{name}: byte size does not match provenance")
        if record.get("sha256") != sha256_file(path):
            errors.append(f"{name}: SHA-256 does not match provenance")
    extra = sorted(
        path.name
        for path in screenshot_dir.glob("*.png")
        if path.name not in EXPECTED_CAPTURES
    )
    if extra:
        errors.append(f"unexpected screenshot files: {extra!r}")
    return errors


def load_manifest(path: Path = PROVENANCE) -> dict[str, Any]:
    """Load one JSON object manifest."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("screenshot provenance must be a JSON object")
    return {str(key): value for key, value in raw.items()}


def external_status(url: str) -> tuple[str, str | None]:
    """Check one external documentation target with a bounded request."""
    headers = {"User-Agent": "pelican-engineering-theme-docs-check/0.1.0"}
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if 200 <= response.status < 400:
                    return url, None
                return url, f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405}:
                continue
            return url, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if method == "HEAD":
                continue
            return url, str(exc)
    return url, "request failed"


def validate_external_links(urls: set[str]) -> list[str]:
    """Return errors for unreachable external documentation links."""
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for url, error in executor.map(external_status, sorted(urls)):
            if error is not None:
                errors.append(f"external documentation link failed: {url}: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external", action="store_true")
    args = parser.parse_args()
    errors, external = local_link_errors()
    if not PROVENANCE.is_file():
        errors.append("missing screenshot provenance: docs/screenshots/provenance.json")
    else:
        try:
            errors.extend(screenshot_provenance_errors(load_manifest()))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid screenshot provenance: {exc}")
    if args.external:
        errors.extend(validate_external_links(external))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    scope = "local, anchor, image, screenshot provenance"
    if args.external:
        scope += ", and external reachability"
    print(f"Documentation validation passed: {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
