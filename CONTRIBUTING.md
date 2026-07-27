# Contributing

The `0.1.0` package is the first public distribution. Contributions must
preserve the generic theme boundary and must not imply that a production site
or a consuming site's visual design has been accepted.

## Before opening a change

Use the public issue templates for reproducible bugs, accessibility problems,
or feature requests. Do not put secrets, personal data, private company
material, or embargoed vulnerability details in an issue. Follow
[SECURITY.md](SECURITY.md) for sensitive reports.

A change must:

- keep content, routes, analytics, publisher identity, and deployment outside
  the package;
- preserve the from-scratch/no-copy and third-party intake policy;
- preserve exact-source, privacy, deterministic-build, and no-runtime-network
  gates;
- identify changes to public settings, blocks, CSS tokens, or notebook markup
  and apply the [version policy](docs/versioning.md);
- never import or execute a notebook reader;
- add provenance and license evidence before any third-party asset or fixture.

## Locked validation

```sh
uv sync --locked --all-groups
uv run --locked --all-groups pytest
uv run --locked --all-groups ruff check .
uv run --locked --all-groups mypy
uv run --locked --all-groups python scripts/validate_foundation.py
uv run --locked --all-groups python scripts/validate_docs.py --external
uv run --locked --all-groups python scripts/validate_release_policy.py
uv build
uv run --locked --all-groups python scripts/verify_distribution.py dist
```

Run `scripts/verify_external_install.py` against the built wheel and
`scripts/verify_readme_onboarding.py` separately against the wheel and sdist.
These checks prove exact local/CI artifacts; post-release verification
separately compares the public PyPI files with the reviewed hashes.

Presentation changes also require:

```sh
npm ci --ignore-scripts
uv run --locked --all-groups playwright install chromium
PET_RUN_BROWSER=1 uv run --locked --all-groups \
  pytest -m browser tests/test_browser_acceptance.py
```

Review screenshots at original resolution. Browser-green and axe-green are
technical evidence, not user visual acceptance.

## Dependency and release changes

Follow [the dependency-update policy](docs/dependency-updates.md); never loosen
an exact action pin or archive inventory casually. Release workflow changes
must retain negative policy tests. Publication remains a separate manual,
protected-environment action documented in [the release guide](docs/releasing.md).
