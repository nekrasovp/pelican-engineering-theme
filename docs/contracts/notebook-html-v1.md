# PLUGIN-003 notebook HTML compatibility contract v1

- Contract ID: `plugin003-nbconvert-basic-v1`
- Status: implemented by the unreleased `0.0.0.dev0` theme
- Reader metadata value: `nbconvert-basic.v1`
- Reader repository: `nekrasovp/pelican-jupyter`
- Reader commit: `137e1eb0ea620f1b15fff0ba81725eea23de1b7a`
- Fixture path: `pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html`
- Fixture SHA-256: `b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf`
- Fixture bytes: `4465`
- Retrieved: 2026-07-22

The immutable [representative PLUGIN-003 fixture](https://github.com/nekrasovp/pelican-jupyter/blob/137e1eb0ea620f1b15fff0ba81725eea23de1b7a/pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html)
is the input presentation contract. Theme contract ID
`plugin003-nbconvert-basic-v1` names the complete commit/path/digest intake.
The real reader metadata value is the distinct string `nbconvert-basic.v1`.
The reader uses `HTMLExporter(template_name="basic")`. The theme does not import
that reader or nbconvert.

The exact external bytes are vendored once at
`tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html` for
source-side regression tests. They are excluded from the runtime wheel. The
reader repository is Apache-2.0, and exact generator `nbconvert==7.17.1` at
official tag `v7.17.1`, commit
`78ed30837a607deab7cf0a12dca072bf3f63417a`, is BSD-3-Clause. The intake,
attribution, modification status, and redistributed license conditions are in
[`THIRD_PARTY.md`](../../THIRD_PARTY.md). The generated external output is not
treated as MIT merely because the theme is MIT.

## Markup covered by v1

The fixture is an embeddable fragment with no `<html>` or `<body>` wrapper. It
covers:

- Markdown cells rooted at `.cell.text_cell` with `.text_cell_render`;
- code cells rooted at `.cell.code_cell` with `.input_area` and prompts;
- stream text and code output wrappers;
- embedded PNG and SVG image output;
- HTML table output;
- committed error output;
- trusted rich HTML, including a representative `<script>` element.

The frozen state ledger is exact: seven cells (one Markdown and six code), six
input areas, six output areas, one stream, one error, one PNG, one SVG, two HTML
outputs, one table, and one trusted script. Seven exact `cell-id=*` values and
content sentinels prevent an internally well-formed but incomplete fragment
from passing.

## Theme activation and presentation

The immutable reader always supplies `jupyter_notebook=True` and
`notebook_html_contract="nbconvert-basic.v1"`. Article and page templates add
`.pet-notebook-document` and a `.pet-notebook-region` namespacing marker only
when both values match. That article marker is not focusable and does not own
horizontal overflow. A genuinely overflowing table is contained by its local
`.output_html` wrapper; the first-party script adds `role="region"`,
`tabindex="0"`, an accessible label, and `data-pet-table-scroller="true"` only
to that wrapper. Keyboard scrolling therefore moves the wide dataframe without
shifting stream, traceback, or other cells. Generic articles receive neither
marker nor notebook behavior.

CSS containment does not depend on JavaScript. In supported Chromium, an
overflowing local output remains natively tabbable and arrow-key scrollable
when scripts are disabled. The first-party script is progressive enhancement
for an explicit role, label, and tabindex; it is not the source of overflow or
the only keyboard path.

Namespaced presentation covers Markdown/text cells, code and Pygments tokens,
input/output prompts, streams, tracebacks, tables/dataframes, PNG and SVG
outputs, trusted rich HTML, figures/captions, math markup, and already-present
Plotly-like containers. It loads no renderer, CDN, service, widget manager, or
remote script. Print uses the theme's light palette and removes the screen
scroll constraint while fitting the owned wide-table example.

The repository-owned hidden example route `notebook-presentation.html` is
built from `examples/full/content/notebook-presentation.md`. Its matching
source notebook at `examples/full/content/downloads/theme006-notebook.ipynb`
was authored from scratch for this repository, contains committed outputs, and
is copied as a static download. The build never imports a notebook reader or
conversion tool.

## Source-notebook metadata hook

The hook consumes the real reader-owned fields; it does not invent a site
path. It appears only when:

- `jupyter_notebook` is true;
- `notebook_html_contract` is exactly `nbconvert-basic.v1`; and
- `nb_path` is a normalized, non-empty POSIX-relative `.ipynb` path.

The theme rejects absolute and protocol-relative paths, dot segments, empty
segments, backslashes, active schemes, percent-encoded ambiguity, whitespace,
quotes, and markup-breakout characters. It combines a valid path only with an
empty/`.` local site prefix or a syntactically safe HTTP(S) `SITEURL`. Missing,
empty, malformed, forged, or unsafe values emit no link or empty wrapper.

The theme makes these states readable, responsive, and keyboard-safe where
content cannot reflow. Horizontal scrolling stays inside the proven local
table-output region. Styling does not depend on a Python import, plugin
installation, or notebook execution.

## Trust and execution boundary

The fixture represents already-committed trusted publication output. The theme
does not execute notebook cells, start a kernel, sanitize rich HTML, or grant
trust to content. It also does not load third-party JavaScript to make outputs
interactive. Whether a consuming site permits embedded interactive JavaScript
is a separate publication-policy decision and is not a v1 support claim.

## Versioning and verification

The identifier is independent of the reader distribution name. The exact
commit, path, and digest form the lock. If reader markup changes materially:

1. add a new side-by-side contract ID and immutable fixture lock;
2. keep v1 support or make the removal a documented breaking theme change;
3. update static selector assertions for Markdown, code, image, SVG, table,
   error, and rich output;
4. perform visual review of every affected state.

`scripts/validate_notebook_contract.py` verifies the exact bytes, digest,
wrapper boundary, classic (not `jp-*`) classes, cell IDs, state counts, and
content sentinels. Omission, digest drift, missing cells/outputs, or nested
documents fail closed. A future markup change requires a new side-by-side
theme input ID, its real reader metadata value, a fresh license intake, and new
visual evidence.
