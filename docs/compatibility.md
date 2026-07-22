# Compatibility matrix

The matrix describes the `0.1.0` candidate and is enforced for each exact PR
head. It is not evidence of a PyPI installation or production-site acceptance.

| Python | Pelican 4.11 | Pelican 4.12 |
| --- | --- | --- |
| 3.11 | Required CI cell | Required CI cell |
| 3.12 | Required CI cell | Required CI cell |
| 3.13 | Required CI cell | Required CI cell |

Python 3.11, Python 3.12, and Python 3.13 are all mandatory cells.
The package declares Python `>=3.11` and
`pelican[markdown]>=4.11,<4.13`. Each cell installs the locked development
environment, selects the exact Pelican minor baseline, and runs the complete
non-browser suite. Candidate build/inspection and artifact-only installation
use Python 3.13; the artifact is pure Python (`py3-none-any`).

## Browser and hosting

Chromium acceptance is separate from the matrix and uses the Playwright version
locked in `uv.lock`. Output is static and has no runtime network requirement.
GitHub Pages and ordinary static hosts are supported deployment targets; no
deployment has been performed in this release-preparation task.

## Notebook compatibility

Presentation is compatible with reader metadata value `nbconvert-basic.v1`
and the exact source fixture named in the
[notebook contract](contracts/notebook-html-v1.md). The theme does not claim
compatibility with arbitrary `jp-*` markup, notebook execution, widgets, or an
unversioned reader branch.

## Not claimed

- Python 3.10 or 3.14, Pelican before 4.11 or at/after 4.13;
- a specific Markdown extension beyond Pelican's declared `markdown` extra;
- legacy browsers, dynamic server frameworks, or client-side applications;
- a released PyPI package, consuming-site integration, or 1.0 API stability.
