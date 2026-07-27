# Changelog

All notable changes are recorded here. The project follows the pre-1.0 rules
in [the version policy](docs/versioning.md) and intends to follow
[Semantic Versioning](https://semver.org/).

## Unreleased

- No changes yet.

## 0.1.0 - 2026-07-27

First public package release. The immutable GitHub and PyPI artifacts are built
from the same reviewed tag through protected environments and OIDC.

### Added

- The from-scratch MIT package identity, public responsibility boundary, and
  installable `src` layout with `get_theme_path()`.
- Default-light/explicit-dark color mode, accessible toggle, print palette,
  public design tokens, and 18 stable Jinja extension blocks.
- Reusable shell, content, archive, taxonomy, pagination, translation, status,
  provenance, related-post, canonical, feed, social metadata, structured-data,
  and generic 404 presentation.
- Namespaced Markdown, code, and frozen `nbconvert-basic.v1` notebook output
  presentation without conversion or execution.
- Minimal/full generic examples, committed-output notebook fixture, exact
  wheel/sdist allowlists, installed-artifact builds, Chromium screenshots,
  axe-core scans, keyboard/overflow checks, and zero-runtime-network gates.
- Complete configuration, customization, notebook, accessibility,
  compatibility, versioning, dependency, deployment, contribution, release,
  and `0.1.0` release documentation.
- README-derived clean onboarding for both exact artifacts,
  screenshot provenance validation, deterministic double-build evidence, and
  negative tests for publication gating and wrong/stale source claims.
- A release-event-only workflow for GitHub Release assets and PyPI Trusted
  Publishing behind protected environments.

### Contract status

This is the first preview contract. Before `1.0.0`, documented breaking
changes require a minor release and migration notes; patches remain compatible.
