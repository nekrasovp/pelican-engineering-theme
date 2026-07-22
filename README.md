# pelican-engineering-theme

> Project-foundation status: contracts and governance only. No installable theme
> package, templates, CSS, release, or published distribution exists yet.

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
| Planned PyPI distribution | `pelican-engineering-theme` |
| Planned Python import | `pelican_engineering_theme` |
| License | MIT |

The live name checks, license reasoning, and five initial product decisions are
recorded in [ADR 0001](docs/decisions/0001-identity-license-and-boundaries.md).
PyPI availability is not a reservation and must be checked again immediately
before any future publication.

## Responsibility boundary

The theme will own presentation: Pelican templates, documented customization
points, and static styling. A notebook reader owns `.ipynb` conversion and
normalized notebook metadata. A consuming site owns content, routes,
configuration, and immutable dependency pins.

The theme may style the versioned notebook HTML contract, but it will not
import a notebook reader, parse or execute notebooks, start kernels, or copy
site-specific content. See the
[PLUGIN-003 HTML fixture contract](docs/contracts/notebook-html-v1.md).

## Planned compatibility

The first implementation targets:

- Python 3.11, 3.12, and 3.13;
- Pelican 4.11 and 4.12;
- ordinary static hosting, including GitHub Pages.

These are targets, not verified support claims. Executable compatibility
evidence belongs to later implementation tasks and must exist before a release.

## Customization contract

Stable template-block names, CSS custom-property names, the optional Pelican
credit, and the system-font policy are frozen in
[Customization contract v1](docs/contracts/customization-v1.md). The names are
reserved now; their implementation is intentionally outside this foundation.

## Non-goals

- no Pavel- or `nekrasovp.ru`-specific content, routes, navigation, analytics,
  dependency pins, or personal assets;
- no notebook conversion, execution, parsing, sanitization, or reader import;
- no bundled Bootstrap, Bootswatch, icon font, web font, or legacy theme asset;
- no mandatory marketing hero, card grid, analytics, comments, or third-party
  JavaScript;
- no package scaffold or publication in this project-foundation change.

## Version policy

The project follows Semantic Versioning:

- `0.1.0`: first documented preview integrated with an example site;
- `0.2.0`: validated against real-site content without importing that content;
- `1.0.0`: stable production configuration and customization contract.

Before `1.0.0`, a breaking contract change requires a minor release and
migration notes; patches remain backward compatible. At and after `1.0.0`,
breaking documented template blocks, settings, CSS tokens, or required markup
requires a major release.

No version, tag, GitHub Release, TestPyPI artifact, or PyPI artifact has been
published.

## Governance

Public issues are enabled for bugs, accessibility problems, and feature
requests. GitHub Discussions are disabled until sustained community demand
justifies an additional support surface. Read [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), and the
[third-party and asset policy](docs/third-party-and-assets.md) before proposing
a change.
