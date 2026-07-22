from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from scripts.validate_shell import focus_order_errors
from tests.site_build import (
    ROOT,
    add_external_notebook_contract_article,
    build_copied_example,
    build_example,
)

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page

STORAGE_KEY = "pelican-engineering-theme"
LIGHT_BG = "rgb(247, 248, 243)"
DARK_BG = "rgb(16, 23, 18)"
AXE_PATH = ROOT / "node_modules/axe-core/axe.min.js"

pytestmark = pytest.mark.browser


def actual_checkout_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    source_sha = result.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{40}", source_sha), source_sha
    return source_sha


def verified_checkout_sha() -> tuple[str, str | None]:
    actual = actual_checkout_sha()
    expected = os.environ.get("PET_EXPECTED_SOURCE_SHA")
    if expected is not None:
        assert re.fullmatch(r"[0-9a-f]{40}", expected), expected
        assert actual == expected, (
            f"actual checkout {actual} does not match expected PR head {expected}"
        )
    return actual, expected


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def start_server(root: Path) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    handler = partial(QuietHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = cast(tuple[str, int], server.server_address)
    return server, thread, f"http://{host}:{port}"


def context_with_storage(
    browser: Browser,
    *,
    stored: str | None = None,
    blocked: bool = False,
    **options: Any,
) -> BrowserContext:
    context = browser.new_context(**options)
    if blocked:
        context.add_init_script(
            """
            Object.defineProperty(window, "localStorage", {
              configurable: true,
              get: function () { throw new Error("storage blocked"); }
            });
            """
        )
    elif stored is not None:
        context.add_init_script(
            f"localStorage.setItem({json.dumps(STORAGE_KEY)}, {json.dumps(stored)});"
        )
    return context


def background(page: Page) -> str:
    return cast(
        str,
        page.evaluate("() => getComputedStyle(document.body).backgroundColor"),
    )


def assert_light(page: Page) -> None:
    assert page.locator("html").get_attribute("data-theme") is None
    assert background(page) == LIGHT_BG


def assert_dark(page: Page) -> None:
    assert page.locator("html").get_attribute("data-theme") == "dark"
    assert background(page) == DARK_BG


def rgb_components(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)", value)
    assert match is not None, value
    red, green, blue = (int(component) for component in match.groups())
    return red, green, blue


def contrast_ratio(foreground: str, background_color: str) -> float:
    def luminance(color: str) -> float:
        channels = []
        for component in rgb_components(color):
            normalized = component / 255
            channels.append(
                normalized / 12.92
                if normalized <= 0.04045
                else ((normalized + 0.055) / 1.055) ** 2.4
            )
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    light, dark = sorted(
        (luminance(foreground), luminance(background_color)), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


def open_page(context: BrowserContext, url: str) -> Page:
    page = context.new_page()
    page.goto(url, wait_until="networkidle")
    return page


def storage_cases(browser: Browser, base_url: str) -> list[str]:
    cases: list[str] = []
    for name, stored, expected_dark in (
        ("missing storage", None, False),
        ("stored light", "light", False),
        ("stored dark", "dark", True),
        ("invalid storage", "sepia", False),
    ):
        context = context_with_storage(
            browser, stored=stored, viewport={"width": 768, "height": 1024}
        )
        try:
            page = open_page(context, base_url)
            assert_dark(page) if expected_dark else assert_light(page)
            cases.append(name)
        finally:
            context.close()

    os_dark = context_with_storage(
        browser,
        color_scheme="dark",
        viewport={"width": 768, "height": 1024},
    )
    try:
        assert_light(open_page(os_dark, base_url))
        cases.append("OS dark with missing storage remains light")
    finally:
        os_dark.close()
    return cases


def blocked_storage_case(browser: Browser, base_url: str) -> str:
    context = context_with_storage(
        browser, blocked=True, viewport={"width": 768, "height": 1024}
    )
    errors: list[str] = []
    try:
        page = context.new_page()
        page.on("pageerror", lambda exception: errors.append(str(exception)))
        page.goto(base_url, wait_until="networkidle")
        assert_light(page)
        button = page.get_by_role("button", name="Use dark theme")
        assert button.is_visible()
        button.click()
        assert_dark(page)
        assert not errors
    finally:
        context.close()
    return "blocked localStorage remains exception-safe"


def persistence_and_keyboard_cases(browser: Browser, base_url: str) -> list[str]:
    context = context_with_storage(browser, viewport={"width": 768, "height": 1024})
    try:
        page = open_page(context, base_url)
        assert page.get_by_role("button", name="Use dark theme").is_visible()
        button = page.locator("[data-pet-theme-toggle]")
        button.focus()
        page.keyboard.press("Enter")
        assert_dark(page)
        assert button.get_attribute("aria-pressed") == "true"
        assert button.get_attribute("aria-label") == "Use light theme"
        assert (
            page.locator('[name="theme-color"]').get_attribute("content") == "#101712"
        )
        assert page.evaluate(f"() => localStorage.getItem('{STORAGE_KEY}')") == "dark"

        page.reload(wait_until="networkidle")
        assert_dark(page)
        page.goto(f"{base_url}/small-technical-note.html", wait_until="networkidle")
        assert_dark(page)

        assert page.get_by_role("button", name="Use light theme").is_visible()
        button = page.locator("[data-pet-theme-toggle]")
        button.focus()
        page.keyboard.press("Space")
        assert_light(page)
        assert button.get_attribute("aria-pressed") == "false"
        assert button.get_attribute("aria-label") == "Use dark theme"
        assert (
            page.locator('[name="theme-color"]').get_attribute("content") == "#f7f8f3"
        )
        assert page.evaluate(f"() => localStorage.getItem('{STORAGE_KEY}')") == "light"
        page.reload(wait_until="networkidle")
        assert_light(page)
    finally:
        context.close()
    return [
        "native button Enter and Space with accessible name and aria-pressed",
        "dark then light persist across reload and navigation",
        "theme-color follows both choices",
    ]


def fallback_motion_print_cases(browser: Browser, base_url: str) -> list[str]:
    no_js = browser.new_context(
        java_script_enabled=False,
        color_scheme="dark",
        viewport={"width": 768, "height": 1024},
    )
    try:
        page = open_page(no_js, base_url)
        assert_light(page)
        assert not page.locator("[data-pet-theme-toggle]").is_visible()
        assert (
            page.locator('[name="theme-color"]').get_attribute("content") == "#f7f8f3"
        )
    finally:
        no_js.close()

    reduced = browser.new_context(
        reduced_motion="reduce", viewport={"width": 768, "height": 1024}
    )
    try:
        page = open_page(reduced, base_url)
        duration = page.locator("[data-pet-theme-toggle]").evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )
        assert duration == "0s"
    finally:
        reduced.close()

    printing = context_with_storage(
        browser, stored="dark", viewport={"width": 768, "height": 1024}
    )
    try:
        page = open_page(printing, base_url)
        assert_dark(page)
        page.emulate_media(media="print")
        print_state = cast(
            dict[str, str],
            page.evaluate(
                """
                () => ({
                  scheme: getComputedStyle(document.documentElement).colorScheme,
                  background: getComputedStyle(document.body).backgroundColor,
                  color: getComputedStyle(document.body).color,
                  token: getComputedStyle(document.documentElement)
                    .getPropertyValue("--pet-color-bg").trim()
                })
                """
            ),
        )
        assert print_state == {
            "scheme": "light",
            "background": "rgb(255, 255, 255)",
            "color": "rgb(0, 0, 0)",
            "token": "#ffffff",
        }
    finally:
        printing.close()
    return [
        "JavaScript disabled keeps light fallback and hides control",
        "reduced motion removes transition",
        "print forces readable light colors",
    ]


def flash_timing_case(browser: Browser, base_url: str) -> tuple[str, dict[str, float]]:
    context = context_with_storage(
        browser, stored="dark", viewport={"width": 768, "height": 1024}
    )
    try:
        page = open_page(context, base_url)
        page.wait_for_timeout(100)
        assert_dark(page)
        timing = cast(
            dict[str, float | None],
            page.evaluate(
                """
                () => ({
                  applied: performance.getEntriesByName("pet-theme-applied")[0]
                    ?.startTime ?? null,
                  paint: performance.getEntriesByName("first-paint")[0]
                    ?.startTime ?? null
                })
                """
            ),
        )
        assert timing["applied"] is not None
        assert timing["paint"] is not None
        assert timing["applied"] <= timing["paint"]
        return (
            "stored dark applied before first paint",
            {"applied_ms": timing["applied"], "first_paint_ms": timing["paint"]},
        )
    finally:
        context.close()


def capture_screenshots(
    browser: Browser,
    base_url: str,
    artifact_root: Path,
    *,
    page_path: str,
    prefix: str,
    themes: tuple[str, ...] = ("light", "dark"),
) -> list[dict[str, str | int]]:
    records: list[dict[str, str | int]] = []
    for width, height in ((390, 844), (768, 1024), (1440, 1000)):
        for theme in themes:
            context = context_with_storage(
                browser,
                stored=theme,
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                reduced_motion="reduce",
            )
            try:
                page = open_page(context, f"{base_url}/{page_path}")
                assert_dark(page) if theme == "dark" else assert_light(page)
                filename = f"{prefix}{theme}-{width}x{height}.png"
                target = artifact_root / filename
                page.screenshot(path=str(target), animations="disabled")
                records.append(
                    {
                        "bytes": target.stat().st_size,
                        "file": target.name,
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "theme": theme,
                        "viewport_width": width,
                        "viewport_height": height,
                    }
                )
            finally:
                context.close()
    return records


def overflowing_elements(page: Page) -> list[str]:
    """Return visible shell elements outside the horizontal viewport."""
    return cast(
        list[str],
        page.evaluate(
            """
            () => {
              const selectors = [
                ".pet-site-header", ".pet-site-header__inner",
                ".pet-navigation", ".pet-navigation__list",
                ".pet-site-footer", ".pet-site-footer__inner",
                ".pet-main", ".pet-prose", ".pet-entry-list",
                ".pet-content-status", ".pet-pagination", "table"
              ];
              const failures = [];
              if (document.documentElement.scrollWidth > window.innerWidth + 1) {
                failures.push(`document:${document.documentElement.scrollWidth}`);
              }
              for (const selector of selectors) {
                for (const element of document.querySelectorAll(selector)) {
                  const box = element.getBoundingClientRect();
                  const region = element.closest(".output_html");
                  const containedByScroller = region
                    && region.scrollWidth > region.clientWidth + 1
                    && region.getBoundingClientRect().left >= -1
                    && region.getBoundingClientRect().right <= innerWidth + 1;
                  if (box.width > 0
                      && (box.left < -1 || box.right > innerWidth + 1)
                      && !containedByScroller) {
                    failures.push(`${selector}:${box.left}:${box.right}`);
                  }
                }
              }
              return failures;
            }
            """
        ),
    )


def notebook_cell_left_edges(page: Page) -> dict[str, float]:
    """Return stable left edges for cells neighboring the wide output."""
    return cast(
        dict[str, float],
        page.evaluate(
            """
            () => {
              const left = selector => document
                .querySelector(selector)
                .getBoundingClientRect().left;
              return {
                error: left("#theme006-error"),
                stream: left("#theme006-stream")
              };
            }
            """
        ),
    )


def shell_layout_cases(browser: Browser, minimal_url: str, full_url: str) -> list[str]:
    cases: list[str] = []
    for width, height in ((390, 844), (768, 1024), (1440, 1000)):
        for fixture, url in (
            ("minimal", f"{minimal_url}/small-technical-note.html"),
            ("full", full_url),
        ):
            context = context_with_storage(
                browser,
                viewport={"width": width, "height": height},
                reduced_motion="reduce",
            )
            try:
                page = open_page(context, url)
                assert overflowing_elements(page) == []
                if fixture == "full":
                    assert page.locator(".pet-navigation").is_visible()
                    assert page.locator(".pet-site-footer").is_visible()
                cases.append(f"{fixture} shell fits {width}x{height}")
            finally:
                context.close()

    regression = context_with_storage(browser, viewport={"width": 390, "height": 844})
    try:
        page = open_page(regression, full_url)
        page.add_style_tag(content=".pet-navigation { min-width: 1000px !important; }")
        assert overflowing_elements(page)
        cases.append("overflow detector rejects an injected navigation regression")
    finally:
        regression.close()
    return cases


def content_surface_cases(browser: Browser, full_url: str) -> list[str]:
    """Exercise content templates and narrow-layout contracts in Chromium."""
    routes = (
        ("index", ""),
        ("article", "long-technical-title.html"),
        ("page", "pages/about.html"),
        ("taxonomy", "category/guides.html"),
        ("archive", "archives.html"),
        ("404", "404.html"),
    )
    cases: list[str] = []
    for width, height in ((390, 844), (768, 1024), (1440, 1000)):
        for label, path in routes:
            context = context_with_storage(
                browser,
                viewport={"width": width, "height": height},
                reduced_motion="reduce",
            )
            try:
                page = open_page(context, f"{full_url}/{path}")
                assert overflowing_elements(page) == []
                cases.append(f"{label} content fits {width}x{height}")
            finally:
                context.close()

    context = context_with_storage(browser, viewport={"width": 768, "height": 1024})
    try:
        russian = open_page(context, f"{full_url}/multilingual-guide-ru.html")
        assert russian.locator("html").get_attribute("lang") == "ru"
        assert russian.locator('[aria-label="Translations"]').is_visible()
        cases.append("Russian article language and translation navigation are exposed")

        updated = open_page(context, f"{full_url}/configurable-shell.html")
        labels = updated.locator(".pet-content-metadata dt").all_text_contents()
        assert "Published" in labels and "Updated" in labels
        cases.append("published and updated dates have distinct visible labels")

        archived = open_page(context, f"{full_url}/archived-interface.html")
        archive_color = archived.locator(".pet-content-status--archive").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        deprecated = open_page(context, f"{full_url}/deprecated-protocol.html")
        deprecated_color = deprecated.locator(
            ".pet-content-status--deprecated"
        ).evaluate("element => getComputedStyle(element).backgroundColor")
        assert archive_color != deprecated_color
        cases.append("archive and deprecated statuses are visibly distinct")

        first = open_page(context, full_url)
        assert first.locator('.pet-pagination a[rel="prev"]').count() == 0
        assert first.locator('.pet-pagination a[rel="next"]').count() == 1
        middle = open_page(context, f"{full_url}/index2.html")
        assert middle.locator('.pet-pagination a[rel="prev"]').count() == 1
        assert middle.locator('.pet-pagination a[rel="next"]').count() == 1
        last = open_page(context, f"{full_url}/index3.html")
        assert last.locator('.pet-pagination a[rel="prev"]').count() == 1
        assert last.locator('.pet-pagination a[rel="next"]').count() == 0
        cases.append("pagination exposes correct first, middle, and last boundaries")
    finally:
        context.close()
    return cases


def notebook_surface_cases(
    browser: Browser, full_url: str
) -> tuple[list[str], dict[str, str | float]]:
    """Exercise frozen notebook presentation and its local table scroller."""
    path = f"{full_url}/notebook-presentation.html"
    cases: list[str] = []
    visual: dict[str, str | float] = {}
    for width, height in ((390, 844), (768, 1024), (1440, 1000)):
        context = context_with_storage(
            browser,
            viewport={"width": width, "height": height},
            reduced_motion="reduce",
        )
        try:
            page = open_page(context, path)
            assert overflowing_elements(page) == []
            assert page.locator(".pet-notebook-region").count() == 1
            cases.append(f"notebook content fits {width}x{height}")
        finally:
            context.close()

    keyboard = context_with_storage(
        browser, viewport={"width": 390, "height": 844}, reduced_motion="reduce"
    )
    try:
        page = open_page(keyboard, path)
        region = page.locator(".pet-notebook-region")
        assert region.get_attribute("role") is None
        assert region.get_attribute("aria-label") is None
        assert region.get_attribute("tabindex") is None
        region_dimensions = cast(
            dict[str, int],
            region.evaluate(
                """
                element => ({
                  client: element.clientWidth,
                  scroll: element.scrollWidth,
                  scrollLeft: element.scrollLeft
                })
                """
            ),
        )
        assert region_dimensions == {
            "client": region_dimensions["client"],
            "scroll": region_dimensions["client"],
            "scrollLeft": 0,
        }

        table_scroller = page.locator('[data-pet-table-scroller="true"]')
        assert table_scroller.count() == 1
        assert table_scroller.get_attribute("role") == "region"
        assert table_scroller.get_attribute("tabindex") == "0"
        assert table_scroller.get_attribute("aria-label") == (
            "Scrollable notebook table: Wide static build matrix"
        )
        table_dimensions = cast(
            dict[str, int],
            table_scroller.evaluate(
                """
                element => ({
                  client: element.clientWidth,
                  scroll: element.scrollWidth
                })
                """
            ),
        )
        assert table_dimensions["scroll"] > table_dimensions["client"]
        edges_before = notebook_cell_left_edges(page)
        assert all(edge >= 0 for edge in edges_before.values())
        table_scroller.focus()
        assert page.evaluate(
            "() => document.activeElement.dataset.petTableScroller === 'true'"
        )
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(100)
        assert cast(int, table_scroller.evaluate("element => element.scrollLeft")) > 0
        assert cast(int, region.evaluate("element => element.scrollLeft")) == 0
        edges_after = notebook_cell_left_edges(page)
        assert edges_after == edges_before
        cases.append("keyboard moves only the labelled local table scroller at 390px")

        assert page.locator(".cell").count() >= 9
        assert page.locator(".output_stream").count() >= 1
        assert page.locator(".output_error").count() >= 1
        assert page.locator('[data-pet-dataframe="wide"]').count() == 1
        assert page.locator(".output_png").count() >= 1
        assert page.locator(".output_svg").count() >= 1
        assert page.locator('[data-pet-rich-output="trusted"]').count() == 1
        assert page.locator(".math").count() == 1
        assert page.locator("figure figcaption").count() == 1
        assert page.locator(".plotly-graph-div").count() == 1
        source = page.get_by_role("link", name="View or download source notebook")
        assert source.get_attribute("href") == "./downloads/theme006-notebook.ipynb"
        assert source.get_attribute("download") == ""
        cases.append("notebook states and safe source download remain present")
    finally:
        keyboard.close()

    no_javascript = context_with_storage(
        browser,
        viewport={"width": 390, "height": 844},
        reduced_motion="reduce",
        java_script_enabled=False,
    )
    try:
        page = open_page(no_javascript, path)
        assert overflowing_elements(page) == []
        region = page.locator(".pet-notebook-region")
        native_scroller = page.locator("#theme006-dataframe .output_html")
        assert native_scroller.get_attribute("data-pet-table-scroller") is None
        assert native_scroller.get_attribute("tabindex") is None
        native_dimensions = cast(
            dict[str, int],
            native_scroller.evaluate(
                """
                element => ({
                  client: element.clientWidth,
                  scroll: element.scrollWidth
                })
                """
            ),
        )
        assert native_dimensions["scroll"] > native_dimensions["client"]
        edges_before = notebook_cell_left_edges(page)
        reached_scroller = False
        for _ in range(40):
            page.keyboard.press("Tab")
            reached_scroller = cast(
                bool,
                native_scroller.evaluate(
                    "element => document.activeElement === element"
                ),
            )
            if reached_scroller:
                break
        assert reached_scroller
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(100)
        native_scroll_left = cast(
            int, native_scroller.evaluate("element => element.scrollLeft")
        )
        assert native_scroll_left > 0
        assert cast(int, region.evaluate("element => element.scrollLeft")) == 0
        edges_after = notebook_cell_left_edges(page)
        assert edges_after == edges_before
        visual.update(
            {
                "no_javascript_keyboard_scroll": "passed",
                "no_javascript_table_scroll_left": float(native_scroll_left),
            }
        )
        cases.append(
            "no-JavaScript Chromium natively focuses and scrolls only the local table"
        )
    finally:
        no_javascript.close()

    exact_context = context_with_storage(
        browser, viewport={"width": 390, "height": 844}, reduced_motion="reduce"
    )
    try:
        external_requests: list[str] = []
        page = exact_context.new_page()
        page.on(
            "request",
            lambda request: (
                external_requests.append(request.url)
                if not request.url.startswith(
                    ("http://127.0.0.1:", "http://localhost:")
                )
                else None
            ),
        )
        page.goto(
            f"{full_url}/external-notebook-contract.html",
            wait_until="networkidle",
        )
        expected_ids = {
            "cell-id=code-contract",
            "cell-id=error-contract",
            "cell-id=markdown-contract",
            "cell-id=png-contract",
            "cell-id=rich-contract",
            "cell-id=svg-contract",
            "cell-id=table-contract",
        }
        actual_ids = set(
            cast(
                list[str],
                page.locator('[id^="cell-id="]').evaluate_all(
                    "elements => elements.map(element => element.id)"
                ),
            )
        )
        assert actual_ids == expected_ids
        assert page.locator(".cell").count() == 7
        assert page.locator(".code_cell").count() == 6
        assert page.locator(".text_cell").count() == 1
        assert page.locator(".input_area").count() == 6
        assert page.locator(".output_area").count() == 6
        assert page.locator(".output_stream").count() == 1
        assert page.locator(".output_error").count() == 1
        assert page.locator(".output_png").count() == 1
        assert page.locator(".output_svg").count() == 1
        assert page.locator(".output_html").count() == 2
        assert overflowing_elements(page) == []
        assert external_requests == []
        cases.append("exact vendored fragment survives browser layout with all states")
    finally:
        exact_context.close()

    dark_context = context_with_storage(
        browser,
        stored="dark",
        viewport={"width": 1440, "height": 1000},
        reduced_motion="reduce",
    )
    try:
        page = open_page(dark_context, path)
        error_pre = page.locator(".output_error pre")
        error_color = cast(
            str, error_pre.evaluate("element => getComputedStyle(element).color")
        )
        error_background = cast(
            str,
            page.locator(".output_error").evaluate(
                "element => getComputedStyle(element).backgroundColor"
            ),
        )
        error_contrast = contrast_ratio(error_color, error_background)
        assert error_contrast >= 4.5
        image_background = cast(
            str,
            page.locator(".output_svg").evaluate(
                "element => getComputedStyle(element).backgroundColor"
            ),
        )
        assert image_background == "rgb(255, 255, 255)"
        assert page.locator('.output_svg circle[fill="currentColor"]').count() == 3
        assert page.locator('figure rect[fill="currentColor"]').count() == 3
        visual.update(
            {
                "error_background": error_background,
                "error_color": error_color,
                "error_contrast": round(error_contrast, 2),
                "image_mat_background": image_background,
            }
        )
        cases.append("dark error and SVG/image treatments retain readable contrast")
    finally:
        dark_context.close()

    printing = context_with_storage(
        browser,
        stored="dark",
        viewport={"width": 1440, "height": 1000},
        reduced_motion="reduce",
    )
    try:
        page = open_page(printing, path)
        page.emulate_media(media="print")
        print_state = cast(
            dict[str, str],
            page.evaluate(
                """
                () => ({
                  background: getComputedStyle(document.body).backgroundColor,
                  codeBackground: getComputedStyle(
                    document.querySelector("#theme006-stream .input_area")
                  ).backgroundColor,
                  codeColor: getComputedStyle(
                    document.querySelector("#theme006-stream .input_area pre")
                  ).color,
                  overflow: getComputedStyle(
                    document.querySelector(".pet-notebook-region")
                  ).overflowX,
                  stringColor: getComputedStyle(
                    document.querySelector("#theme006-stream .s1")
                  ).color,
                  tableMinWidth: getComputedStyle(
                    document.querySelector('[data-pet-dataframe="wide"]')
                  ).minWidth
                })
                """
            ),
        )
        assert print_state == {
            "background": "rgb(255, 255, 255)",
            "codeBackground": "rgb(242, 242, 242)",
            "codeColor": "rgb(0, 0, 0)",
            "overflow": "visible",
            "stringColor": "rgb(20, 83, 35)",
            "tableMinWidth": "0px",
        }
        print_code_contrast = contrast_ratio(
            print_state["codeColor"], print_state["codeBackground"]
        )
        print_string_contrast = contrast_ratio(
            print_state["stringColor"], print_state["codeBackground"]
        )
        assert print_code_contrast >= 4.5
        assert print_string_contrast >= 4.5
        visual.update(
            {
                "print_code_background": print_state["codeBackground"],
                "print_code_color": print_state["codeColor"],
                "print_code_contrast": round(print_code_contrast, 2),
                "print_string_color": print_state["stringColor"],
                "print_string_contrast": round(print_string_contrast, 2),
            }
        )
        cases.append("print media fits wide data and keeps normal/string code readable")
    finally:
        printing.close()

    assert len(cases) == 9
    return cases, visual


def capture_print_screenshot(
    browser: Browser, base_url: str, artifact_root: Path
) -> dict[str, str | int]:
    context = context_with_storage(
        browser,
        stored="dark",
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=1,
        reduced_motion="reduce",
    )
    try:
        page = open_page(context, f"{base_url}/notebook-presentation.html")
        page.emulate_media(media="print")
        target = artifact_root / "notebook-print-1440x1000.png"
        page.screenshot(path=str(target), animations="disabled", full_page=True)
        return {
            "bytes": target.stat().st_size,
            "file": target.name,
            "media": "print",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "theme_before_emulation": "dark",
            "viewport_height": 1000,
            "viewport_width": 1440,
        }
    finally:
        context.close()


def capture_notebook_state_screenshots(
    browser: Browser, base_url: str, artifact_root: Path
) -> list[dict[str, str | int]]:
    records: list[dict[str, str | int]] = []
    for theme in ("light", "dark"):
        context = context_with_storage(
            browser,
            stored=theme,
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            reduced_motion="reduce",
        )
        try:
            page = open_page(context, f"{base_url}/notebook-presentation.html")
            dataframe = page.locator("#theme006-dataframe")
            dataframe.scroll_into_view_if_needed()
            page.evaluate("window.scrollBy(0, -220)")
            region = page.locator(".pet-notebook-region")
            table_scroller = page.locator('[data-pet-table-scroller="true"]')
            table_scroll_left = cast(
                int,
                table_scroller.evaluate(
                    """
                    element => {
                      element.scrollLeft = Math.min(180, element.scrollWidth);
                      return element.scrollLeft;
                    }
                    """
                ),
            )
            region_scroll_left = cast(
                int, region.evaluate("element => element.scrollLeft")
            )
            assert table_scroll_left > 0
            assert region_scroll_left == 0
            filename = f"notebook-states-{theme}-390x844.png"
            target = artifact_root / filename
            page.screenshot(path=str(target), animations="disabled")
            records.append(
                {
                    "bytes": target.stat().st_size,
                    "capture": "error-and-wide-dataframe",
                    "file": target.name,
                    "region_scroll_left": region_scroll_left,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "table_scroll_left": table_scroll_left,
                    "theme": theme,
                    "viewport_height": 844,
                    "viewport_width": 390,
                }
            )
        finally:
            context.close()
    return records


def focus_and_skip_cases(browser: Browser, full_url: str) -> list[str]:
    expected = [
        "skip",
        "brand",
        "Overview",
        "Guides",
        "Reference",
        "Français",
        "theme",
    ]
    context = context_with_storage(browser, viewport={"width": 390, "height": 844})
    try:
        page = open_page(context, full_url)
        actual: list[str] = []
        for _index in range(len(expected)):
            page.keyboard.press("Tab")
            actual.append(
                cast(
                    str,
                    page.evaluate(
                        """
                        () => {
                          const element = document.activeElement;
                          if (element.classList.contains("pet-skip-link")) {
                            return "skip";
                          }
                          if (element.classList.contains("pet-brand")) return "brand";
                          if (element.matches("[data-pet-theme-toggle]")) {
                            return "theme";
                          }
                          return element.textContent.trim();
                        }
                        """
                    ),
                )
            )
        assert focus_order_errors(actual, expected) == []

        visual_order = cast(
            list[str],
            page.evaluate(
                """
                () => {
                  const elements = [
                    ["brand", document.querySelector(".pet-brand")],
                    ...Array.from(document.querySelectorAll(".pet-navigation a"))
                      .map(element => [element.textContent.trim(), element]),
                    ["Français", document.querySelector(".pet-language-link")],
                    ["theme", document.querySelector("[data-pet-theme-toggle]")]
                  ];
                  return elements
                    .map(([label, element]) => {
                      const box = element.getBoundingClientRect();
                      return {label, top: Math.round(box.top), left: box.left};
                    })
                    .sort((left, right) => (
                      left.top - right.top || left.left - right.left
                    ))
                    .map(item => item.label);
                }
                """
            ),
        )
        assert visual_order == expected[1:]

        page = open_page(context, full_url)
        page.keyboard.press("Tab")
        assert page.locator(".pet-skip-link:focus").count() == 1
        page.keyboard.press("Enter")
        page.wait_for_function("location.hash === '#main-content'")
        assert page.evaluate("() => document.activeElement.id") == "main-content"
    finally:
        context.close()
    return [
        "keyboard and visual order align for brand, navigation, language, and theme",
        "skip link moves focus to the semantic main target",
    ]


def accessibility_case(
    context: BrowserContext, url: str, fixture: str, url_path: str
) -> dict[str, Any]:
    external_requests: list[str] = []
    page = context.new_page()
    page.on(
        "request",
        lambda request: (
            external_requests.append(request.url)
            if not request.url.startswith(("http://127.0.0.1:", "http://localhost:"))
            else None
        ),
    )
    page.goto(url, wait_until="networkidle")
    assert external_requests == []
    page.add_script_tag(path=str(AXE_PATH))
    result = cast(
        dict[str, Any],
        page.evaluate(
            """
            async () => await axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
              }
            })
            """
        ),
    )
    violations = cast(list[dict[str, Any]], result["violations"])
    incomplete = cast(list[dict[str, Any]], result["incomplete"])
    assert violations == [], [
        {"id": violation["id"], "impact": violation["impact"]}
        for violation in violations
    ]
    assert incomplete == [], [
        {"id": item["id"], "impact": item["impact"]} for item in incomplete
    ]
    return {
        "fixture": fixture,
        "url_path": url_path,
        "viewport": page.viewport_size,
        "theme": page.locator("html").get_attribute("data-theme") or "light",
        "engine": "axe-core",
        "engine_version": "4.12.1",
        "license": "MPL-2.0",
        "violations": 0,
        "passes": len(cast(list[object], result["passes"])),
        "incomplete": 0,
        "external_runtime_requests": external_requests,
    }


@pytest.mark.skipif(
    os.environ.get("PET_RUN_BROWSER") != "1",
    reason="set PET_RUN_BROWSER=1 for real Chromium acceptance",
)
def test_theme_color_mode_in_real_chromium(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    source_sha, expected_source_sha = verified_checkout_sha()
    artifact_root = Path(
        os.environ.get("PET_SCREENSHOT_DIR", tmp_path / "browser-artifacts")
    ).resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    assert AXE_PATH.is_file(), "run npm ci before browser acceptance"
    minimal_output = build_example("minimal", tmp_path)
    full_example = tmp_path / "full"
    shutil.copytree(ROOT / "examples/full", full_example)
    add_external_notebook_contract_article(full_example)
    full_output = build_copied_example(full_example)
    minimal_server, minimal_thread, minimal_url = start_server(minimal_output)
    full_server, full_thread, full_url = start_server(full_output)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                browser_version = browser.version
                predecessor_cases = storage_cases(browser, minimal_url)
                predecessor_cases.append(blocked_storage_case(browser, minimal_url))
                predecessor_cases.extend(
                    persistence_and_keyboard_cases(browser, minimal_url)
                )
                predecessor_cases.extend(
                    fallback_motion_print_cases(browser, minimal_url)
                )
                timing_name, timing = flash_timing_case(browser, minimal_url)
                predecessor_cases.append(timing_name)
                assert len(predecessor_cases) == 13
                cases = list(predecessor_cases)
                layout_cases = shell_layout_cases(browser, minimal_url, full_url)
                cases.extend(layout_cases)
                cases.extend(focus_and_skip_cases(browser, full_url))
                theme004_predecessor_cases = list(cases)
                assert len(theme004_predecessor_cases) == 22
                content_cases = content_surface_cases(browser, full_url)
                cases.extend(content_cases)
                theme005_predecessor_cases = list(cases)
                assert len(theme005_predecessor_cases) == 44
                notebook_cases, notebook_visual = notebook_surface_cases(
                    browser, full_url
                )
                cases.extend(notebook_cases)
                screenshots = capture_screenshots(
                    browser,
                    minimal_url,
                    artifact_root,
                    page_path="small-technical-note.html",
                    prefix="",
                )
                screenshots.extend(
                    capture_screenshots(
                        browser,
                        full_url,
                        artifact_root,
                        page_path="",
                        prefix="full-",
                    )
                )
                theme004_predecessor_screenshots = list(screenshots)
                for label, path in (
                    ("content-index", ""),
                    ("content-article", "long-technical-title.html"),
                    ("content-page", "pages/about.html"),
                    ("content-taxonomy", "category/guides.html"),
                    ("content-archive", "archives.html"),
                    ("content-404", "404.html"),
                    ("content-archived-status", "archived-interface.html"),
                    ("content-deprecated-status", "deprecated-protocol.html"),
                ):
                    screenshots.extend(
                        capture_screenshots(
                            browser,
                            full_url,
                            artifact_root,
                            page_path=path,
                            prefix=f"{label}-",
                            themes=("light",),
                        )
                    )
                theme005_predecessor_screenshots = list(screenshots)
                assert len(theme005_predecessor_screenshots) == 36
                screenshots.extend(
                    capture_screenshots(
                        browser,
                        full_url,
                        artifact_root,
                        page_path="notebook-presentation.html",
                        prefix="notebook-",
                    )
                )
                notebook_state_screenshots = capture_notebook_state_screenshots(
                    browser, full_url, artifact_root
                )
                screenshots.extend(notebook_state_screenshots)
                print_screenshot = capture_print_screenshot(
                    browser, full_url, artifact_root
                )
                screenshots.append(print_screenshot)
                assert len(screenshots) == 45
                accessibility: list[dict[str, Any]] = []
                for fixture, url, url_path in (
                    (
                        "minimal",
                        f"{minimal_url}/small-technical-note.html",
                        "/small-technical-note.html",
                    ),
                    ("full", full_url, "/"),
                    (
                        "full-article",
                        f"{full_url}/long-technical-title.html",
                        "/long-technical-title.html",
                    ),
                    ("full-page", f"{full_url}/pages/about.html", "/pages/about.html"),
                    (
                        "full-taxonomy",
                        f"{full_url}/category/guides.html",
                        "/category/guides.html",
                    ),
                    ("full-archive", f"{full_url}/archives.html", "/archives.html"),
                    ("full-404", f"{full_url}/404.html", "/404.html"),
                    (
                        "full-notebook",
                        f"{full_url}/notebook-presentation.html",
                        "/notebook-presentation.html",
                    ),
                ):
                    width = 1440 if fixture == "full-notebook" else 390
                    height = 1000 if fixture == "full-notebook" else 844
                    context = context_with_storage(
                        browser, viewport={"width": width, "height": height}
                    )
                    try:
                        accessibility.append(
                            accessibility_case(context, url, fixture, url_path)
                        )
                    finally:
                        context.close()
                dark_notebook = context_with_storage(
                    browser,
                    stored="dark",
                    viewport={"width": 1440, "height": 1000},
                )
                try:
                    accessibility.append(
                        accessibility_case(
                            dark_notebook,
                            f"{full_url}/notebook-presentation.html",
                            "full-notebook-dark",
                            "/notebook-presentation.html",
                        )
                    )
                finally:
                    dark_notebook.close()
            finally:
                browser.close()
    finally:
        for server, thread in (
            (minimal_server, minimal_thread),
            (full_server, full_thread),
        ):
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    report = {
        "engine": "Chromium",
        "engine_version": browser_version,
        "source_sha": source_sha,
        "expected_source_sha": expected_source_sha,
        "cases": cases,
        "case_count": len(cases),
        "theme003_predecessor_case_count": len(predecessor_cases),
        "theme003_predecessor_cases": predecessor_cases,
        "theme004_predecessor_case_count": len(theme004_predecessor_cases),
        "theme004_predecessor_cases": theme004_predecessor_cases,
        "theme005_content_case_count": len(content_cases),
        "theme005_content_cases": content_cases,
        "theme005_predecessor_case_count": len(theme005_predecessor_cases),
        "theme005_predecessor_cases": theme005_predecessor_cases,
        "theme004_predecessor_screenshots": theme004_predecessor_screenshots,
        "theme005_predecessor_screenshots": theme005_predecessor_screenshots,
        "notebook_case_count": len(notebook_cases),
        "notebook_cases": notebook_cases,
        "notebook_visual": notebook_visual,
        "notebook_state_screenshots": notebook_state_screenshots,
        "print_screenshot": print_screenshot,
        "accessibility": accessibility,
        "timing": timing,
        "screenshots": screenshots,
    }
    (artifact_root / "browser-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
