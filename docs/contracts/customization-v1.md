# Customization contract v1

- Contract ID: `pelican-engineering-theme-customization-v1`
- Status: implemented by the unreleased `0.0.0.dev0` package
- Applies from: first `0.1.x` preview that implements the theme

This document freezes the initial public names established in THEME-001,
records their compatible THEME-003 color-mode implementation, and adds the
THEME-004 reusable shell, configuration, and generic component contracts.

## Stable template blocks

The base template will expose these blocks in document order:

| Block | Intended extension point |
| --- | --- |
| `html_head` | Entire contents of `<head>` while preserving required defaults through `super()` |
| `title` | Text content of the document title |
| `head_meta` | Additional metadata and link elements |
| `canonical` | Optional canonical link |
| `structured_data` | Optional structured-data script elements |
| `head_styles` | Site-owned stylesheets or inline critical styles |
| `body_class` | Classes on `<body>`; retain defaults through `super()` |
| `body_start` | First content inside `<body>` |
| `site_header` | Site identity and header shell |
| `site_navigation` | Primary navigation |
| `page_class` | Classes on the semantic `<main>`; retain defaults through `super()` |
| `hero` | Optional page-level hero before the content header |
| `content_header` | Title, dates, status, and provenance for the current content |
| `content` | Main article, page, listing, archive, or taxonomy body |
| `content_footer` | Content-local footer and source links |
| `site_footer` | Site-wide footer, including optional credits |
| `scripts` | Site-owned scripts after required theme behavior |
| `body_end` | Final content before `</body>` |

Removing or renaming a listed block, changing its documented purpose so an
existing override no longer works, or making `super()` unsafe is a breaking
change. Undocumented internal blocks are not public API.

The packaged includes own head metadata, header, brand, navigation, language
links, theme toggle, and footer markup. They are internal composition units;
sites should use settings or the stable blocks rather than copy an include.

To override one block without copying the document shell, add a directory to
Pelican's standard `THEME_TEMPLATES_OVERRIDES` setting and explicitly extend the
packaged theme template:

```jinja2
{% extends "!theme/index.html" %}
{% block hero %}<p>Site-owned introduction.</p>{% endblock hero %}
```

## Shell configuration

Standard Pelican settings are primary where they already express the needed
contract:

| Setting | Contract |
| --- | --- |
| `SITENAME` | Default brand label and document title |
| `SITEURL` | Default brand-home prefix and packaged asset prefix |
| `DEFAULT_LANG` | `<html lang>` value, defaulting to `en` |
| `MENUITEMS` | Primary navigation as Pelican `(label, URL)` tuples |

Theme-specific settings cover behavior without a standard Pelican equivalent:

| Setting | Default | Contract |
| --- | --- | --- |
| `ENGINEERING_THEME_BRAND_LABEL` | `SITENAME` | Brand label; an explicit empty value falls back to `SITENAME` |
| `ENGINEERING_THEME_BRAND_URL` | `SITEURL + '/'` | Brand destination |
| `ENGINEERING_THEME_NAV` | empty | Optional mappings with `label`, `url`, and optional `current`; a non-empty value replaces `MENUITEMS` and `current: true` emits `aria-current="page"` |
| `ENGINEERING_THEME_LANGUAGE_LINKS` | empty | Sequence of mappings with `label`, `url`, and optional `lang`/`hreflang` |
| `ENGINEERING_THEME_FOOTER_TEXT` | empty | Escaped plain-text footer content |
| `ENGINEERING_THEME_SHOW_PELICAN_CREDIT` | `False` | Optional “Built with Pelican” link |

`MENUITEMS` is deliberately the primary navigation API. The namespaced
`ENGINEERING_THEME_NAV` exists only for the current-page metadata that standard
two-item Pelican tuples cannot carry. The plural language-link setting follows
the plan even when a site supplies only one alternate language. Empty settings,
invalid navigation entries, and invalid language-link entries emit no empty
control or container.

## Generic shell and content classes

The additive THEME-004 component contract exposes these reusable selectors:

| Selector | Role |
| --- | --- |
| `.pet-container` | Centered responsive container using `--pet-content-width` |
| `.pet-button` | Accessible button treatment for link or button controls |
| `.pet-prose` | Restrained long-form reading measure and edge spacing |
| `.pet-status-notice` | Informational notice; `data-status` accepts `success`, `warning`, or `danger` |

Shell implementation classes remain internal. The header and navigation use
wrapping flex layout rather than a hamburger or Bootstrap dependency. The skip
link is the first default focus target and moves focus to
`main#main-content[tabindex="-1"]`.

## Stable CSS token namespace

Public custom properties use the `--pet-` prefix. The first implementation
will define these tokens on `:root` and provide dark-palette values under
`html[data-theme="dark"]` where color-specific:

| Token | Meaning |
| --- | --- |
| `--pet-color-bg` | Page background |
| `--pet-color-surface` | Primary raised or grouped surface |
| `--pet-color-surface-muted` | Secondary surface |
| `--pet-color-text` | Primary text |
| `--pet-color-text-muted` | Secondary text |
| `--pet-color-border` | Dividers and quiet borders |
| `--pet-color-accent` | Accent fill or emphasis |
| `--pet-color-accent-contrast` | Text or icon color on the accent |
| `--pet-color-link` | Inline link color |
| `--pet-color-focus` | Visible keyboard focus indicator |
| `--pet-font-sans` | System sans-serif stack |
| `--pet-font-mono` | System monospace stack |
| `--pet-line-height-body` | Default reading line height |
| `--pet-content-width` | Maximum prose measure |
| `--pet-space-unit` | Base spacing unit |
| `--pet-radius` | Default restrained corner radius |

Public token names describe roles rather than literal colors or personal brand
names. A rename or semantic repurposing is breaking; changing a default value
is allowed only when contrast, visual regression, and release review pass.
Selectors and class names are not stable unless a later document explicitly
adds them to the public API.

## Palette and persistence behavior

`:root` always defines the complete light palette. Color-specific dark values
exist only under `html[data-theme="dark"]`. The theme does not use
`prefers-color-scheme` to select a palette: a first visit is light even when the
operating system preference is dark.

The persistence contract is exact:

| Field | Contract |
| --- | --- |
| Storage API | `localStorage` |
| Key | `pelican-engineering-theme` |
| Values written | `light` or `dark` only |
| Dark condition | Stored value is exactly `dark` |
| Missing, invalid, or unavailable storage | Light, without an uncaught exception |

A small inline loader runs in `<head>` before the stylesheet. It applies only a
stored exact `dark` value, updates the initial `theme-color`, and otherwise
leaves the CSS light default unchanged. The packaged first-party
`theme/js/theme.js` owns later button interaction, DOM state, persistence, and
`theme-color` updates. No runtime network request or third-party JavaScript is
used.

The reusable internal include `templates/includes/theme-toggle.html` contains a
native button rather than a hidden checkbox. JavaScript reveals it only after
initialization and maintains its accessible name and `aria-pressed` state.
Therefore JavaScript-disabled output remains a complete light-only page without
an inert control.

`color-scheme` follows the active screen palette. Motion is added only inside
`prefers-reduced-motion: no-preference`; reduced-motion users receive no toggle
transition. Print overrides both screen palettes with black text on a white
background and hides the interactive control.

## Internal semantic roles

The implementation also defines non-public semantic roles for code background,
text, border, and highlight; info, success, warning, and danger notice
background/border/text states; surface shadow; and header backdrop. Their
current `--pet-*` spelling is an implementation detail. Consumers should rely
only on the public table above until a later contract promotes another name.

## Contrast gate

Automated assertions compute WCAG contrast from the shipped hexadecimal token
values in both light and dark palettes. Normal and meaningful text must be at
least 4.5:1 for these pairs:

- primary text / page background;
- muted text / page background;
- link text / page background;
- accent-contrast button text / accent fill;
- code text / code background;
- info, success, warning, and danger notice text / matching notice background.

Focus and meaningful UI boundaries must be at least 3:1 for these pairs:

- focus / page background;
- focus / primary surface;
- border / page background;
- border / primary surface;
- code border / code background.

Changing a tested token value requires the same computed gate and browser
review. Passing the gate is not a substitute for user visual acceptance.

## Fonts and icons

The defaults use local system font stacks through `--pet-font-sans` and
`--pet-font-mono`. Core CSS must not fetch Google Fonts or another remote font,
and the package must not bundle a font or icon font. A consuming site may
override tokens and assumes the resulting privacy, performance, and license
obligations.

## Pelican credit

`ENGINEERING_THEME_SHOW_PELICAN_CREDIT` is a boolean setting with a default of
`False`. When true, the theme will render a quiet “Built with Pelican” link in
`site_footer`. The credit is optional; removing it through the setting does not
require a template override.

## Versioning

Before `1.0.0`, a breaking change to this contract requires a minor version and
migration notes. After `1.0.0`, it requires a major version. Patch releases may
add tokens or blocks but may not break documented overrides.
