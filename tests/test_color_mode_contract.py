from __future__ import annotations

import re

import pelican_engineering_theme

THEME = pelican_engineering_theme.get_theme_path()
CSS_PATH = THEME / "static/css/scaffold.css"
BASE_PATH = THEME / "templates/base.html"
TOGGLE_PATH = THEME / "templates/includes/theme-toggle.html"
SCRIPT_PATH = THEME / "static/js/theme.js"

PUBLIC_TOKENS = {
    "--pet-color-bg",
    "--pet-color-surface",
    "--pet-color-surface-muted",
    "--pet-color-text",
    "--pet-color-text-muted",
    "--pet-color-border",
    "--pet-color-accent",
    "--pet-color-accent-contrast",
    "--pet-color-link",
    "--pet-color-focus",
    "--pet-font-sans",
    "--pet-font-mono",
    "--pet-line-height-body",
    "--pet-content-width",
    "--pet-space-unit",
    "--pet-radius",
}

INTERNAL_COLOR_TOKENS = {
    "--pet-color-code-bg",
    "--pet-color-code-text",
    "--pet-color-code-border",
    "--pet-color-code-highlight",
    "--pet-color-notice-info-bg",
    "--pet-color-notice-info-border",
    "--pet-color-notice-info-text",
    "--pet-color-notice-success-bg",
    "--pet-color-notice-success-border",
    "--pet-color-notice-success-text",
    "--pet-color-notice-warning-bg",
    "--pet-color-notice-warning-border",
    "--pet-color-notice-warning-text",
    "--pet-color-notice-danger-bg",
    "--pet-color-notice-danger-border",
    "--pet-color-notice-danger-text",
    "--pet-color-shadow",
    "--pet-color-header-backdrop",
}


def _declarations(css: str, selector: str) -> dict[str, str]:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", css, re.S)
    assert match is not None, f"missing selector: {selector}"
    return {
        name: value.strip()
        for name, value in re.findall(
            r"(--pet-[\w-]+)\s*:\s*([^;]+);", match.group("body")
        )
    }


def _rgb(value: str) -> tuple[int, int, int]:
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), value
    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
    )


def _luminance(value: str) -> float:
    channels = []
    for channel in _rgb(value):
        normalized = channel / 255
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(left: str, right: str) -> float:
    high, low = sorted((_luminance(left), _luminance(right)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_public_and_internal_semantic_tokens_exist_in_both_palettes() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    light = _declarations(css, ":root")
    dark = _declarations(css, 'html[data-theme="dark"]')

    assert PUBLIC_TOKENS <= light.keys()
    assert INTERNAL_COLOR_TOKENS <= light.keys()
    assert {
        token for token in PUBLIC_TOKENS | INTERNAL_COLOR_TOKENS if "color" in token
    } <= dark.keys()


def test_contrast_contract_in_both_palettes() -> None:
    """WCAG pairs: normal text 4.5:1; focus and UI boundaries 3:1."""
    css = CSS_PATH.read_text(encoding="utf-8")
    palettes = {
        "light": _declarations(css, ":root"),
        "dark": _declarations(css, 'html[data-theme="dark"]'),
    }
    normal_pairs = {
        "body text": ("--pet-color-text", "--pet-color-bg"),
        "muted text": ("--pet-color-text-muted", "--pet-color-bg"),
        "link text": ("--pet-color-link", "--pet-color-bg"),
        "button text": ("--pet-color-accent-contrast", "--pet-color-accent"),
        "code text": ("--pet-color-code-text", "--pet-color-code-bg"),
        "info notice": ("--pet-color-notice-info-text", "--pet-color-notice-info-bg"),
        "success notice": (
            "--pet-color-notice-success-text",
            "--pet-color-notice-success-bg",
        ),
        "warning notice": (
            "--pet-color-notice-warning-text",
            "--pet-color-notice-warning-bg",
        ),
        "danger notice": (
            "--pet-color-notice-danger-text",
            "--pet-color-notice-danger-bg",
        ),
    }
    ui_pairs = {
        "focus on page": ("--pet-color-focus", "--pet-color-bg"),
        "focus on surface": ("--pet-color-focus", "--pet-color-surface"),
        "border on page": ("--pet-color-border", "--pet-color-bg"),
        "border on surface": ("--pet-color-border", "--pet-color-surface"),
        "code boundary": ("--pet-color-code-border", "--pet-color-code-bg"),
    }

    failures: list[str] = []
    for palette_name, palette in palettes.items():
        for pair_name, (foreground, background) in normal_pairs.items():
            ratio = _contrast(palette[foreground], palette[background])
            if ratio < 4.5:
                failures.append(f"{palette_name} {pair_name}: {ratio:.2f} < 4.5")
        for pair_name, (foreground, background) in ui_pairs.items():
            ratio = _contrast(palette[foreground], palette[background])
            if ratio < 3:
                failures.append(f"{palette_name} {pair_name}: {ratio:.2f} < 3.0")
    assert not failures, "\n".join(failures)


def test_head_loader_precedes_stylesheet_and_uses_exact_storage_contract() -> None:
    base = BASE_PATH.read_text(encoding="utf-8")
    loader_position = base.index("data-pet-theme-loader")
    stylesheet_position = base.index("rel=\"stylesheet\"")

    assert loader_position < stylesheet_position
    assert 'pelican-engineering-theme' in base
    assert '=== "dark"' in base
    assert "prefers-color-scheme" not in base
    assert "localStorage" in base
    assert "try" in base and "catch" in base


def test_toggle_is_a_packaged_button_and_script_is_first_party_only() -> None:
    base = BASE_PATH.read_text(encoding="utf-8")
    toggle = TOGGLE_PATH.read_text(encoding="utf-8")
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "{% include \"includes/theme-toggle.html\" %}" in base
    assert "<button" in toggle
    assert "type=\"button\"" in toggle
    assert "aria-pressed=\"false\"" in toggle
    assert "hidden" in toggle
    assert "checkbox" not in toggle.lower()
    assert "localStorage" in script
    assert '"pelican-engineering-theme"' in script
    assert "matchMedia" not in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "http://" not in script and "https://" not in script

    runtime = base + script
    for forbidden in (
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "google-analytics",
        "googletagmanager",
        "gtag(",
        "analytics.",
    ):
        assert forbidden not in runtime


def test_css_has_explicit_reduced_motion_and_print_light_contracts() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")

    assert "@media (prefers-reduced-motion: no-preference)" in css
    assert "@media print" in css
    print_css = css[css.index("@media print") :]
    assert 'html[data-theme="dark"]' in print_css
    assert "color-scheme: light" in print_css
