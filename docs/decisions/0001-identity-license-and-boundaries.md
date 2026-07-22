# ADR 0001: Project identity, license, and initial boundaries

- Status: accepted
- Decision date: 2026-07-22
- Evidence retrieval date: 2026-07-22
- Scope: THEME-001 only

## Context

The project needs a public, reusable identity before package scaffolding. Its
name must not imply ownership by Pelican upstream, and its legal boundary must
not silently inherit the current personal site's vendored theme bundle.

## Availability evidence

The checks below ran before the repository was created, at
`2026-07-22T08:54:24Z`.

| Surface | Read-only check | Result |
| --- | --- | --- |
| GitHub repository | `GET /repos/nekrasovp/pelican-engineering-theme` while authenticated as owner | HTTP 404; the owner's repository listing also contained no exact-name match |
| PyPI project JSON | `https://pypi.org/pypi/pelican-engineering-theme/json` | HTTP 404 |
| PyPI normalized Simple API | `https://pypi.org/simple/pelican-engineering-theme/` | HTTP 404 |

The matching GitHub name was therefore available to the authenticated owner,
and no normalized PyPI project existed at retrieval time. A PyPI 404 does not
reserve the name. Publication remains out of scope and requires a fresh check.

## Decision

1. The final public theme name is `pelican-engineering-theme`.
2. The GitHub owner is `nekrasovp`.
3. The repository uses the MIT License, with the generated copyright notice
   retained in [LICENSE](../../LICENSE).
4. “Built with Pelican” credit is optional and off by default. The reserved
   setting is `ENGINEERING_THEME_SHOW_PELICAN_CREDIT`; authors may also replace
   the stable `site_footer` block.
5. The core theme uses system font stacks only. It will not bundle or remotely
   load a web font. Sites may override documented font tokens at their own
   policy and licensing boundary.

The final identity is:

| Surface | Name |
| --- | --- |
| Repository | `nekrasovp/pelican-engineering-theme` |
| Planned distribution | `pelican-engineering-theme` |
| Planned import package | `pelican_engineering_theme` |

One-sentence description: **A reusable, accessibility-conscious Pelican theme
for technical writers who publish long-form articles, code, and trusted static
notebook output.**

## License reasoning

The new repository is a clean-room project foundation. No templates, CSS,
JavaScript, images, fonts, icons, or personal content were copied from the
vendored site theme. The separate
[lineage and asset audit](../third-party-and-assets.md) records why even
permissively licensed legacy files are not imported by default.

Pelican is an AGPL-3.0 build tool and is not bundled in this repository. Jinja
is BSD-3-Clause and is likewise not bundled; using its public template language
does not copy its implementation. The PLUGIN-003 reference fixture is produced
by an Apache-2.0 project and is referenced by immutable path and hash, not
copied in this foundation. These boundaries allow this repository's original
work to remain MIT while preserving upstream terms if a future reviewed change
adds third-party material.

## Responsibility boundary

- Theme: presentation, documented Jinja customization points, and static CSS.
- Notebook reader: `.ipynb` conversion, metadata normalization, deterministic
  failure behavior, and the versioned HTML fragment.
- Consuming site: content, routes, configuration, publication policy, and
  immutable dependency pins.

The theme may style the frozen HTML fragment. It must not import the reader,
parse a notebook, execute cells, start a kernel, or claim that trusted rich
output is sanitized.

## Compatibility and release policy

The initial target is Python 3.11–3.13 and Pelican 4.11/4.12. It is not a
support claim until later executable matrices are green.

Semantic milestones are `0.1.0` for the example-site preview, `0.2.0` for
real-site validation, and `1.0.0` for a stable production contract. Before
`1.0.0`, breaking changes require a minor version and migration notes; patches
must be backward compatible.

## Governance

Public issues are enabled with bug, accessibility, and feature templates.
Discussions are disabled until there is sustained community demand. Private
vulnerability reporting is the security channel. There is no private contact
information or maintainer outreach in this repository.

## Consequences

- THEME-002 may scaffold the package under the selected names.
- The names of documented blocks and CSS tokens in
  [Customization contract v1](../contracts/customization-v1.md) are public API.
- The notebook fixture identifier in
  [Notebook HTML contract v1](../contracts/notebook-html-v1.md) can evolve
  independently of the reader package name.
- No PyPI ownership, release readiness, or upstream Pelican endorsement is
  claimed.

## Rollback

Before a first PyPI release, the repository and package may be renamed through
a new ADR. After publication, the name must not be silently reused; use a
deprecation release and documented redirects.
