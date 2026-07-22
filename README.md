# pelican-engineering-theme

> Status: the unreleased installable package includes the semantic color-mode
> foundation, reusable core shell, generic Pelican content surfaces, and the
> frozen PLUGIN-003 notebook presentation contract. Real-site integration and
> a published distribution do not exist yet.

A reusable, accessibility-conscious Pelican theme for technical writers who
publish long-form articles, code, and trusted static notebook output.

## Target users

- Pelican publishers who want a restrained technical-writing presentation;
- maintainers who need documented customization points instead of a
  site-specific theme fork;
- sites that render static notebook fragments produced by a separate reader.

## Project identity

| Surface | Decision |
| --- | --- |
| GitHub owner/repository | `nekrasovp/pelican-engineering-theme` |
| Distribution | `pelican-engineering-theme` |
| Python import | `pelican_engineering_theme` |
| License | MIT |

The live name checks, license reasoning, and five initial product decisions are
recorded in [ADR 0001](docs/decisions/0001-identity-license-and-boundaries.md).
PyPI availability is not a reservation and must be checked again immediately
before any future publication. This package is not published on PyPI.

## Install and use the unreleased theme

Build the wheel from a trusted checkout, then install that exact local artifact:

```sh
uv build
uv venv .venv
uv pip install --python .venv/bin/python \
  dist/pelican_engineering_theme-0.0.0.dev0-py3-none-any.whl
```

Point Pelican at the installed filesystem resource from `pelicanconf.py`:

```python
from pelican_engineering_theme import get_theme_path

THEME = str(get_theme_path())
```

The repository's generic example can be built after a locked development sync:

```sh
uv sync --locked --all-groups
cd examples/minimal
uv run --locked --all-groups pelican content -s pelicanconf.py -o output
```

`examples/full` exercises every optional shell setting and a child template
that extends `!theme/index.html`. It also generates article and page content,
archives, category/tag/author list and detail pages, three pagination boundary
pages, an English/Russian translation pair, and the packaged 404. Both examples
are built from the installed wheel outside the checkout in CI.

`pip install pelican-engineering-theme` is future release syntax only. It does
not work until a separately authorized PyPI publication has occurred.

## Responsibility boundary

The theme owns presentation: Pelican templates, documented customization
points, and static styling. A notebook reader owns `.ipynb` conversion and
normalized notebook metadata. A consuming site owns content, routes,
configuration, and immutable dependency pins.

The theme may style the versioned notebook HTML contract, but it does not
import a notebook reader, parse or execute notebooks, start kernels, or copy
site-specific content. See the
[PLUGIN-003 HTML fixture contract](docs/contracts/notebook-html-v1.md).

## Static notebook presentation

Notebook mode activates only when reader-owned metadata contains both
`jupyter_notebook=True` and
`notebook_html_contract="nbconvert-basic.v1"`. The article/page marker scopes
notebook presentation without making the whole document a scroll container.
When an HTML table actually overflows, the first-party theme script labels and
focuses only that local output scroller. This keeps wide dataframes inside the
viewport without shifting neighboring cells or changing generic article,
header, navigation, and footer layout. With JavaScript disabled, the CSS
containment and Chromium's native focusable-scroll-region behavior preserve
the same local keyboard operation; only the explicit semantic enhancement and
theme persistence/toggling degrade.

The theme styles the frozen classic `cell`, `text_cell`, `code_cell`,
`input_area`, prompt, and output classes, plus ordinary Markdown/Pygments code.
It supports committed stream, error, table/dataframe, PNG, SVG, rich HTML,
figure/caption, math, and static embedded-output containers in light, dark, and
print modes. It adds no math renderer, kernel, reader, notebook conversion,
widget manager, CDN, or remote runtime request.

When the reader is configured to copy a notebook, it supplies a safe
POSIX-relative `nb_path`. The theme then shows “View or download source
notebook.” Without a proven notebook marker, exact reader contract, and valid
relative `.ipynb` path, the control is omitted completely. Absolute,
protocol-relative, active-scheme, dot-segment, and breakout values are
rejected.

## Compatibility target and evidence

The first implementation targets:

- Python 3.11, 3.12, and 3.13;
- Pelican 4.11 and 4.12;
- ordinary static hosting, including GitHub Pages.

The package workflow executes all six Python/Pelican combinations. Compatibility
is claimed for the unreleased package only when that exact-head matrix is green;
it is not a claim that a later site shell, real-site integration, or release is
complete.

## Color-mode contract

Light is the unconditional first-visit default, including when the operating
system prefers dark colors. Dark is applied only after the user explicitly
selects it and the exact value `dark` is stored under
`pelican-engineering-theme`. The only values written are `light` and `dark`.
Missing, invalid, or unavailable storage safely resolves to light.

The head contains a small first-party pre-paint loader before the stylesheet,
and interaction lives in the packaged `theme/js/theme.js`. The reusable toggle
include renders a native button with an accessible name and `aria-pressed`
state. With JavaScript disabled the button remains hidden and the complete
light CSS fallback remains usable. Print always uses a readable light palette.
No palette decision uses `prefers-color-scheme`.

## Reusable shell configuration

The shell uses standard Pelican `MENUITEMS` tuples for primary navigation:

```python
MENUITEMS = (("Home", "/"), ("Guides", "/guides/"))
ENGINEERING_THEME_LANGUAGE_LINKS = (
    {"label": "Français", "url": "/fr/", "lang": "fr"},
)
ENGINEERING_THEME_FOOTER_TEXT = "A technical publication."
```

Brand label/URL, language links, footer text, and the optional Pelican credit
are settings. A non-empty `ENGINEERING_THEME_NAV` may replace `MENUITEMS` only
when mappings need `current: true` and `aria-current="page"`. Empty optional
settings render no empty navigation, language control, or footer. The header
wraps at narrow widths without Bootstrap, third-party JavaScript, or a
hamburger requirement; a working skip link targets the semantic main element.

## Content, metadata, and feed configuration

The content templates use standard Pelican objects and settings. Production
canonical and feed discovery URLs are assembled from an absolute `SITEURL` and
the current Pelican route. Standard relative feed paths are supported for the
site-wide, category, tag, author, and translation Atom/RSS settings. Invalid,
external, or non-string feed paths produce no discovery tag. Keep
`RELATIVE_URLS = False` when absolute canonical and discovery metadata is
required.

Open Graph and Twitter card tags are enabled by default but appear only when a
non-empty title and absolute canonical URL exist. They use no account handle or
production identifier. Optional settings are:

```python
ENGINEERING_THEME_ENABLE_SOCIAL_METADATA = True
ENGINEERING_THEME_META_DESCRIPTION = "A generic technical publication."
ENGINEERING_THEME_SOCIAL_IMAGE = "https://example.test/static/preview.png"
```

Person and WebSite JSON-LD are explicit mappings and are emitted only on the
first index page when both `name` and an absolute HTTP(S) `url` are present.
Article JSON-LD is opt-in and derives its headline, date, language, canonical
URL, and author from the current Pelican article:

```python
ENGINEERING_THEME_JSON_LD_PERSON = {
    "name": "Example Editor",
    "url": "https://example.test/about/",
}
ENGINEERING_THEME_JSON_LD_WEBSITE = {
    "name": "Generic Systems Journal",
    "url": "https://example.test/",
}
ENGINEERING_THEME_ENABLE_ARTICLE_JSON_LD = True
ENGINEERING_THEME_ARTICLE_SCHEMA_TYPE = "TechArticle"  # or "Article"
```

Incomplete or unsupported schema settings emit no JSON-LD. Values are encoded
with Jinja's HTML-safe JSON serializer, including closing-tag hazards.

Use underscore-named Pelican content metadata for optional status and
provenance hooks:

```text
Archive_Notice: Retained for historical reference.
Deprecated_Warning: Do not use this approach for new work.
Source_Url: https://example.test/source.txt
Source_Label: Inspect the source record
```

`article.related_posts`, when supplied by a site or plugin as ordinary Pelican
content objects, produces related-post navigation. Missing, empty, malformed,
or unsafe values produce no control or empty container. No related-post plugin,
comments, analytics, tag cloud, social widget, remote font, or runtime service
is required.

## Packaged 404

The wheel owns a generic `templates/404.html`. Pelican resolves it through the
installed theme loader without copying the template into site content:

```python
TEMPLATE_PAGES = {"404.html": "404.html"}
```

The installed-wheel fixture proves that this creates `output/404.html`. The 404
inherits the one semantic shell and deliberately emits no canonical, Open
Graph, Twitter, or JSON-LD identity for the missing route.

## Customization contract

The base continues to expose exactly 18 stable template-block names, including
title, metadata,
canonical, structured data, body/page classes, hero, content, and scripts. It
also provides generic container, button, prose, and status-notice classes. All
public CSS custom properties are implemented with light values on
`:root` and color-specific dark values on `html[data-theme="dark"]`. Names,
semantics, storage behavior, tested contrast pairs, and the system-font policy
are documented in
[Customization contract v1](docs/contracts/customization-v1.md). Selectors and
internal tokens are not public API.

## Exact distribution inventories

Distribution verification requires equality with complete allowlists. The
wheel contains 32 runtime package files plus five locked distribution-metadata
files (37 total). The sdist contains an exact 52-file source/testing support
subset, the 32 runtime source files, and eight locked generated/root metadata
files (92 total). A missing or undeclared archive member fails closed.

## Browser evidence

Real Chromium acceptance is isolated from the six-cell Python/Pelican matrix.
The browser binary is a development and CI tool, not a runtime dependency:

```sh
uv sync --locked --all-groups
npm ci --ignore-scripts
uv run --locked --all-groups playwright install chromium
PET_RUN_BROWSER=1 uv run --locked --all-groups \
  pytest -m browser tests/test_browser_acceptance.py
```

The browser workflow retains every predecessor color-mode and shell case, then
adds representative index, article, page, taxonomy, archive, and 404 checks at
390×844, 768×1024, and 1440×1000. It uploads deterministic screenshots together
with a machine-readable exact-head report covering axe-core, focus/skip,
overflow, no-network, and pre-paint timing evidence. axe-core is an exact,
development-only dependency installed from `package-lock.json`; it is not
bundled in the wheel or source archive. Green automation is evidence for review,
not user visual acceptance.

## Non-goals

- no content, routes, navigation, analytics, dependency pins, or personal
  assets specific to an individual publisher or consuming site;
- no notebook conversion, execution, parsing, sanitization, or reader import;
- no bundled Bootstrap, Bootswatch, icon font, web font, or legacy theme asset;
- no mandatory marketing hero, card grid, analytics, comments, or third-party
  JavaScript;
- no PyPI/TestPyPI publication, tag, release, or production-site integration.

## Version policy

The project follows Semantic Versioning:

- `0.1.0`: first documented preview integrated with an example site;
- `0.2.0`: validated against real-site content without importing that content;
- `1.0.0`: stable production configuration and customization contract.

Before `1.0.0`, a breaking contract change requires a minor release and
migration notes; patches remain backward compatible. At and after `1.0.0`,
breaking documented template blocks, settings, CSS tokens, or required markup
requires a major release.

The package metadata uses the deliberately unreleased internal version
`0.0.0.dev0`. No tag, GitHub Release, TestPyPI artifact, or PyPI artifact has
been published.

## Governance

Public issues are enabled for bugs, accessibility problems, and feature
requests. GitHub Discussions are disabled until sustained community demand
justifies an additional support surface. Read [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), and the
[third-party and asset policy](docs/third-party-and-assets.md) before proposing
a change.
