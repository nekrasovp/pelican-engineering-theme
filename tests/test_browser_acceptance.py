from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from scripts.validate_shell import focus_order_errors
from tests.site_build import build_example

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page

ROOT = Path(__file__).resolve().parents[1]
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
) -> list[dict[str, str | int]]:
    records: list[dict[str, str | int]] = []
    for width, height in ((390, 844), (768, 1024), (1440, 1000)):
        for theme in ("light", "dark"):
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
                ".pet-site-footer", ".pet-site-footer__inner"
              ];
              const failures = [];
              if (document.documentElement.scrollWidth > window.innerWidth + 1) {
                failures.push(`document:${document.documentElement.scrollWidth}`);
              }
              for (const selector of selectors) {
                for (const element of document.querySelectorAll(selector)) {
                  const box = element.getBoundingClientRect();
                  if (box.width > 0 && (box.left < -1 || box.right > innerWidth + 1)) {
                    failures.push(`${selector}:${box.left}:${box.right}`);
                  }
                }
              }
              return failures;
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
    context: BrowserContext, url: str, fixture: str
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
    assert violations == [], [
        {"id": violation["id"], "impact": violation["impact"]}
        for violation in violations
    ]
    return {
        "fixture": fixture,
        "url_path": "/" if fixture == "full" else "/small-technical-note.html",
        "engine": "axe-core",
        "engine_version": "4.12.1",
        "license": "MPL-2.0",
        "violations": 0,
        "passes": len(cast(list[object], result["passes"])),
        "incomplete": len(cast(list[object], result["incomplete"])),
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
    full_output = build_example("full", tmp_path)
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
                accessibility: list[dict[str, Any]] = []
                for fixture, url in (
                    ("minimal", f"{minimal_url}/small-technical-note.html"),
                    ("full", full_url),
                ):
                    context = context_with_storage(
                        browser, viewport={"width": 390, "height": 844}
                    )
                    try:
                        accessibility.append(accessibility_case(context, url, fixture))
                    finally:
                        context.close()
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
        "accessibility": accessibility,
        "timing": timing,
        "screenshots": screenshots,
    }
    (artifact_root / "browser-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
