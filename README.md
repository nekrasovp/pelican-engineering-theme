# pelican-engineering-theme

> Scaffold status: an unreleased installable package exists for build and
> compatibility validation. Final visual design, dark-mode behavior, and a
> published distribution do not exist yet.

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

## Install and use the unreleased scaffold

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

`pip install pelican-engineering-theme` is future release syntax only. It does
not work until a separately authorized PyPI publication has occurred.

## Responsibility boundary

The theme will own presentation: Pelican templates, documented customization
points, and static styling. A notebook reader owns `.ipynb` conversion and
normalized notebook metadata. A consuming site owns content, routes,
configuration, and immutable dependency pins.

The theme may style the versioned notebook HTML contract, but it does not
import a notebook reader, parse or execute notebooks, start kernels, or copy
site-specific content. See the
[PLUGIN-003 HTML fixture contract](docs/contracts/notebook-html-v1.md).

## Compatibility target and evidence

The first implementation targets:

- Python 3.11, 3.12, and 3.13;
- Pelican 4.11 and 4.12;
- ordinary static hosting, including GitHub Pages.

The package workflow executes all six Python/Pelican combinations. Compatibility
is claimed for this scaffold only when that exact-head matrix is green; it is
not a claim that the later visual theme or a release is complete.

## Customization contract

The minimal base exposes the stable template-block names and optional Pelican
credit. CSS custom-property names and the system-font policy are frozen in
[Customization contract v1](docs/contracts/customization-v1.md). The names are
reserved; complete tokens, shell design, and light/dark behavior remain future
work.

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
