Title: A Deliberately Long Technical Article Title That Exercises Narrow Viewports Without Sacrificing Meaning or Link Clarity
Date: 2026-02-08
Category: Guides
Tags: example, layout
Slug: long-technical-title
Summary: Tables, figures, footnotes, quotations, and code exercise long-form presentation.

Long-form technical writing combines several structures that must remain
readable without a remote stylesheet.

| Stage | Input | Output | Failure mode |
| --- | --- | --- | --- |
| Parse | immutable bytes | syntax tree | invalid encoding |
| Validate | syntax tree | typed model | incomplete contract |
| Publish | typed model | static document | missing route |

> A build is reproducible only when its inputs, environment, and expected
> outputs are explicit.

<figure>
  <svg role="img" aria-labelledby="fixture-figure-title fixture-figure-description" viewBox="0 0 320 120">
    <title id="fixture-figure-title">Three-stage publishing flow</title>
    <desc id="fixture-figure-description">Parse leads to validate, which leads to publish.</desc>
    <rect x="4" y="32" width="88" height="48" fill="currentColor" opacity="0.16"></rect>
    <rect x="116" y="32" width="88" height="48" fill="currentColor" opacity="0.16"></rect>
    <rect x="228" y="32" width="88" height="48" fill="currentColor" opacity="0.16"></rect>
  </svg>
  <figcaption>A generic inline figure with a programmatic name and caption.</figcaption>
</figure>

The final assertion is linked to recorded evidence.[^evidence]

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BuildEvidence:
    source_sha: str
    pages: tuple[str, ...]

    def matches(self, expected_sha: str) -> bool:
        return self.source_sha == expected_sha and bool(self.pages)
```

[^evidence]: The fixture uses a footnote to verify readable reference links and notes.
