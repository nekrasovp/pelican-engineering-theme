#!/usr/bin/env python3
"""Capture first-party generic README screenshots and exact provenance."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Page, sync_playwright

from scripts.validate_docs import (
    EXPECTED_CAPTURES,
    SCREENSHOT_DIR,
    render_tree_sha256,
    sha256_file,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def build_full_example(target: Path) -> Path:
    """Copy and build the generic full example without checkout path leakage."""
    example = target / "full"
    shutil.copytree(REPOSITORY_ROOT / "examples/full", example)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pelican",
            "content",
            "-s",
            "pelicanconf.py",
            "-o",
            "output",
        ],
        cwd=example,
        env=environment,
        check=True,
    )
    return example / "output"


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve generated files without noisy request logging."""

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def select_theme(page: Page, theme: str) -> None:
    """Apply the documented explicit color-mode storage contract."""
    if theme == "dark":
        page.evaluate("localStorage.setItem('pelican-engineering-theme', 'dark')")
    else:
        page.evaluate("localStorage.removeItem('pelican-engineering-theme')")
    page.reload(wait_until="networkidle")
    expected = "dark" if theme == "dark" else None
    actual = page.locator("html").get_attribute("data-theme")
    if actual != expected:
        raise RuntimeError(f"theme selection failed: {actual!r} != {expected!r}")


def capture(output_dir: Path) -> dict[str, object]:
    """Build the full example, capture required routes, and return provenance."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pet-readme-capture-") as raw_temp:
        site_output = build_full_example(Path(raw_temp))
        handler = partial(QuietHandler, directory=str(site_output))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        records: list[dict[str, object]] = []
        external_requests: list[str] = []
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                browser_version = browser.version
                for name, (route, theme, width, height) in EXPECTED_CAPTURES.items():
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        reduced_motion="reduce",
                    )
                    page = context.new_page()

                    def record_request(url: str) -> None:
                        parsed = urlsplit(url)
                        if (
                            parsed.scheme in {"http", "https"}
                            and parsed.netloc != urlsplit(origin).netloc
                        ):
                            external_requests.append(url)

                    page.on("request", lambda request: record_request(request.url))
                    response = page.goto(origin + route, wait_until="networkidle")
                    if response is None or not response.ok:
                        raise RuntimeError(f"capture route failed: {route}")
                    select_theme(page, theme)
                    page.locator("main#main-content").wait_for(state="visible")
                    page.evaluate("window.scrollTo(0, 0)")
                    target = output_dir / name
                    page.screenshot(
                        path=str(target), full_page=False, animations="disabled"
                    )
                    records.append(
                        {
                            "file": name,
                            "route": route,
                            "theme": theme,
                            "viewport": {"width": width, "height": height},
                            "bytes": target.stat().st_size,
                            "sha256": sha256_file(target),
                        }
                    )
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        if external_requests:
            raise RuntimeError(f"capture made external requests: {external_requests!r}")

    return {
        "schema_version": 1,
        "source_kind": "first-party-generic-example",
        "candidate_only": True,
        "runtime_network_requests": 0,
        "source_tree_sha256": render_tree_sha256(),
        "capture_tool": (
            f"playwright {version('playwright')} / Chromium {browser_version}"
        ),
        "captures": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=SCREENSHOT_DIR)
    args = parser.parse_args()
    manifest = capture(args.output)
    provenance = args.output / "provenance.json"
    provenance.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Captured {len(EXPECTED_CAPTURES)} generic screenshots in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
