# Customization guide

Start with settings and public CSS tokens. Override a template block only when
configuration and CSS cannot express the required presentation.

## Override public tokens

Load a site-owned stylesheet after `theme/css/scaffold.css` and override roles,
not internal selectors:

```css
:root {
  --pet-color-accent: #a8e84f;
  --pet-content-width: 72rem;
  --pet-radius: 0.2rem;
}

html[data-theme="dark"] {
  --pet-color-accent: #b8f35d;
}
```

Re-run contrast, print, narrow viewport, and both-palette checks after a color
change. The exact public token list and persistence rules are frozen in the
[customization contract](contracts/customization-v1.md).

## Extend a public block

Put site-owned templates outside the installed package and use Pelican's theme
override loader. A child template can extend the installed template namespace:

```jinja2
{% extends "!theme/index.html" %}

{% block hero %}
  <section aria-labelledby="site-introduction">
    <h1 id="site-introduction">A site-owned introduction</h1>
  </section>
{% endblock hero %}
```

The stable block order is: `html_head`, `title`, `head_meta`, `canonical`,
`structured_data`, `head_styles`, `body_class`, `body_start`, `site_header`,
`site_navigation`, `page_class`, `hero`, `content_header`, `content`,
`content_footer`, `site_footer`, `scripts`, and `body_end`.

Replacing an entire template couples a site to internal markup. Prefer a
small block override, keep DOM and keyboard order aligned, and preserve the
skip target and exactly one semantic main element.

## Add site assets

Use Pelican `STATIC_PATHS` for publisher-owned images, CSS, or JavaScript. The
core package intentionally contains no remote fonts, icon fonts, analytics, or
third-party runtime scripts. A site that adds them owns privacy, performance,
accessibility, security, and license review.

## Breaking changes

Public settings, the 18 blocks, public CSS tokens, color-mode storage, and the
notebook HTML contract are versioned. Before `1.0.0`, a breaking change needs a
minor release plus migration notes; see [the version policy](versioning.md).
