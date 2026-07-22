# Dependency-update policy

Runtime dependencies stay minimal. Build, test, browser, accessibility, and
GitHub Actions dependencies are reviewed separately from runtime behavior.

## Update procedure

1. Classify the update as runtime, build backend, Python development, Node
   development, browser, or GitHub Action.
2. Read upstream release/security notes and confirm license compatibility.
3. Update the narrow declaration and regenerate `uv.lock` or
   `package-lock.json`; never hand-edit a generated lock.
4. Pin GitHub Actions to full commit SHAs and retain the human-readable version
   comment. Resolve a moving upstream tag before review.
5. Run the six-cell matrix, exact wheel/sdist inventories, both artifact-only
   installs, clean-sdist tests, docs/release-policy gates, and all existing
   unit/static checks.
6. For render/browser changes, rerun Chromium, axe, no-network, print, and
   screenshot provenance review.
7. Record any compatibility or contract effect in the changelog.

Do not widen Python/Pelican ranges from resolver success alone. A new supported
cell needs hosted evidence; removal is a documented breaking change. Never add
a runtime notebook converter, remote font, analytics client, or third-party
JavaScript as a transitive convenience.

Dependabot or another bot may propose updates later, but automation cannot
merge, publish, deploy, or weaken the protected release environments.
