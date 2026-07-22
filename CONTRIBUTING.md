# Contributing

This repository contains an unreleased theme package. The color-mode foundation
is implemented; a reusable site shell and real-site integration belong to later
reviewed changes.

## Start with an issue

Use the public issue templates for a reproducible bug, accessibility problem,
or feature request. GitHub Discussions are intentionally disabled. Do not put
secrets, private company material, personal data, or embargoed vulnerability
details in an issue.

For security-sensitive reports, follow [SECURITY.md](SECURITY.md).

## Change requirements

A proposed change must:

- keep the theme reusable and free of site-specific content or configuration;
- preserve the theme/reader/site responsibility boundary in [README.md](README.md);
- identify breaking changes to documented blocks, settings, CSS tokens, or
  notebook markup and apply the version policy;
- include provenance and license evidence before adding any third-party code,
  font, icon, image, fixture, or other asset;
- avoid remote fonts and bundled icon fonts in the core theme;
- avoid importing or executing a notebook reader.

Run the locked validation before submitting a change:

```sh
uv sync --locked --all-groups
uv run --locked --all-groups pytest
uv run --locked --all-groups ruff check .
uv run --locked --all-groups mypy
uv run --locked --all-groups python scripts/validate_foundation.py
uv build
uv run --locked --all-groups python scripts/verify_distribution.py dist
```

Then run `scripts/verify_external_install.py` against the built wheel. These
checks do not imply that a package or release is available from PyPI.

Color-mode changes also require the isolated real-browser proof:

```sh
uv run --locked --all-groups playwright install chromium
PET_RUN_BROWSER=1 uv run --locked --all-groups \
  pytest -m browser tests/test_browser_acceptance.py
```

Chromium is a development/CI dependency and must not become a theme runtime
dependency. Review the generated screenshots at their original resolution;
browser-green remains executor evidence rather than user visual acceptance.
