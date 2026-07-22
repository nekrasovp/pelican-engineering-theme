# Notebook guide

The theme presents trusted static notebook HTML. It does not read `.ipynb`,
run cells, start a kernel, sanitize output, or install a reader.

## Reader contract

A reader must produce the frozen classic nbconvert basic fragment and expose:

```text
jupyter_notebook = true
notebook_html_contract = nbconvert-basic.v1
```

Only that pair activates `.pet-notebook-document` and
`.pet-notebook-region`. The exact source commit, fixture digest, cell/output
ledger, licenses, and change procedure are in the
[notebook HTML contract](contracts/notebook-html-v1.md).

## Source notebook link

If a reader copies the original notebook, it may also supply a normalized
POSIX-relative path:

```text
Nb_Path: downloads/example-notebook.ipynb
```

The control appears only for the proven notebook marker/contract and a safe
`.ipynb` path. Absolute paths, protocols, backslashes, dot segments, encoded
ambiguity, whitespace, and markup-breakout characters are rejected.

## Supported static output

The candidate styles Markdown/text cells, input and output prompts, Pygments
code, streams, tracebacks, dataframes, PNG, SVG, rich HTML, math markup,
figures/captions, and already-present embedded-output containers. Wide tables
scroll locally and receive progressive keyboard semantics without making the
whole article a scroll region.

No MathJax, widget manager, Plotly runtime, CDN, service, or notebook converter
is added. Interactive output works only if a consuming site's separately
reviewed trust/runtime policy supplies what it needs.

## Security and reproducibility

Treat embedded rich HTML and scripts as executable publication content. Review
committed outputs, never execute notebooks in the theme build, keep conversion
in a separately pinned reader, and fail when expected notebook sources or
routes are missing. The generic example notebook is authored from scratch and
contains committed outputs; CI proves that builds do not execute it.
