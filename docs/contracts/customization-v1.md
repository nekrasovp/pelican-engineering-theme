# Customization contract v1

- Contract ID: `pelican-engineering-theme-customization-v1`
- Status: names reserved; implementation pending
- Applies from: first `0.1.x` preview that implements the theme

This document freezes the initial public names without adding templates or CSS
in THEME-001.

## Stable template blocks

The base template will expose these blocks in document order:

| Block | Intended extension point |
| --- | --- |
| `html_head` | Entire contents of `<head>` while preserving required defaults through `super()` |
| `head_meta` | Additional metadata and link elements |
| `head_styles` | Site-owned stylesheets or inline critical styles |
| `body_start` | First content inside `<body>` |
| `site_header` | Site identity and header shell |
| `site_navigation` | Primary navigation |
| `content_header` | Title, dates, status, and provenance for the current content |
| `content` | Main article, page, listing, archive, or taxonomy body |
| `content_footer` | Content-local footer and source links |
| `site_footer` | Site-wide footer, including optional credits |
| `scripts` | Site-owned scripts after required theme behavior |
| `body_end` | Final content before `</body>` |

Removing or renaming a listed block, changing its documented purpose so an
existing override no longer works, or making `super()` unsafe is a breaking
change. Undocumented internal blocks are not public API.

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
