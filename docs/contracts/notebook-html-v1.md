# PLUGIN-003 notebook HTML compatibility contract v1

- Contract ID: `plugin003-nbconvert-basic-v1`
- Status: frozen input contract; theme implementation pending
- Reader repository: `nekrasovp/pelican-jupyter`
- Reader commit: `137e1eb0ea620f1b15fff0ba81725eea23de1b7a`
- Fixture path: `pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html`
- Fixture SHA-256: `b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf`
- Retrieved: 2026-07-22

The immutable [representative PLUGIN-003 fixture](https://github.com/nekrasovp/pelican-jupyter/blob/137e1eb0ea620f1b15fff0ba81725eea23de1b7a/pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html)
is the input presentation contract. The reader uses
`HTMLExporter(template_name="basic")`; the theme does not import that reader or
nbconvert.

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

The theme will make these states readable, responsive, keyboard-safe where
interactive content exists, and horizontally scrollable where content cannot
reflow. Styling must not depend on a Python import, plugin installation, or
notebook execution.

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

Future theme tests may vendor a reviewed fixture copy with its Apache-2.0
provenance and required notices, or fetch a pre-verified immutable test input.
This foundation copies no plugin source or fixture content.
