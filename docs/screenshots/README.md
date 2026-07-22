# Screenshot provenance

The five README screenshots are generated from scratch from `examples/full`
and the first-party theme in this repository. They contain only generic example
content. No legacy-site screenshot, personal asset, remote font, or external
runtime response is copied into them.

Run the locked local capture after building the final render inputs:

```sh
uv sync --locked --all-groups
uv run --locked --all-groups playwright install chromium
uv run --locked --all-groups python -m scripts.capture_readme_screenshots
uv run --locked --all-groups python scripts/validate_docs.py
```

[`provenance.json`](provenance.json) records an aggregate SHA-256 over every
theme/example/capture input, the exact route, selected theme, viewport, browser
tool version, file size, and screenshot SHA-256. Validation rejects a missing
or extra capture, modified bytes, stale input tree, wrong route/theme/viewport,
and malformed source evidence. Hosted browser evidence independently rebuilds
the same generic surfaces and retains exact-head/no-network checks.

Screenshots are documentation and technical review evidence only. They do not
claim visual acceptance for a consuming site.
