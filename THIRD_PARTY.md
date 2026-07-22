# Third-party notices for source fixtures

The runtime theme wheel contains no third-party fixture, notebook, conversion
tool, font, image library, or JavaScript. The self-testing source distribution
contains one unmodified external HTML regression fixture under the notices
below.

## PLUGIN-003 generated notebook fragment

- Theme intake contract: `plugin003-nbconvert-basic-v1`.
- Reader metadata value: `nbconvert-basic.v1`.
- Source repository: `nekrasovp/pelican-jupyter`.
- Source commit: `137e1eb0ea620f1b15fff0ba81725eea23de1b7a`.
- Source path:
  `pelican_jupyter/tests/fixtures/nbconvert-basic.v1/representative.fragment.html`.
- File introduction commit:
  `fe7444e17bb56e1ae1bda6163996e76b92c09cfb`.
- Vendored path:
  `tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html`.
- Bytes: `4465`.
- SHA-256:
  `b174322b567e4931cfa98bed76a38665876b99bc046df2cc6a30c0d83eb8cbaf`.
- Modification status: copied byte-for-byte; unmodified.

The reader repository and its repository-authored synthetic source notebook are
licensed under Apache-2.0. The applicable license is reproduced in
[`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt). Copyright and attribution
remain with the repository authors and contributors.

The exact generator lock was `nbconvert==7.17.1`. Official tag `v7.17.1`
resolves to commit `78ed30837a607deab7cf0a12dca072bf3f63417a`. Its
`basic/index.html.j2` extends `classic/base.html.j2`; the fixture contains the
resulting classic cell, prompt, input, and output structure. nbconvert is
BSD-3-Clause, with copyright held by the IPython and Jupyter Development Teams.
The applicable notice and conditions are reproduced in
[`LICENSES/BSD-3-Clause-nbconvert.txt`](LICENSES/BSD-3-Clause-nbconvert.txt).

The generated fragment is not relicensed as MIT. It is kept only as an exact,
source-side interoperability fixture. The MIT theme styles compatible markup;
it does not copy nbconvert templates or ship this fixture in the runtime wheel.
The upstream authors, Jupyter, IPython, nbconvert, and Pelican have not endorsed
this theme.

## Repository-owned THEME-006 example

`examples/full/content/downloads/theme006-notebook.ipynb` and the matching
`examples/full/content/notebook-presentation.md` presentation fixture were
authored from scratch for this repository under its MIT license. Their names,
text, table, one-pixel raster, SVG, rich HTML, figure, math, and static
Plotly-like container are generic. They contain committed outputs and are never
converted or executed by the theme, tests, or workflows. The notebook is
`5497` bytes with SHA-256
`80d31e53242e740e8f530162234c79be8e0cfaebab999fcf25cc8ef0254773bc`.
