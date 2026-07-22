# Configuration reference

This reference describes the `0.1.0` candidate. Standard Pelican settings are
preferred; theme-specific settings are optional and namespaced.

## Minimal configuration

```python
from pelican_engineering_theme import get_theme_path

SITENAME = "Engineering Notes"
SITEURL = ""
PATH = "content"
DEFAULT_LANG = "en"
THEME = str(get_theme_path())
RELATIVE_URLS = True
```

Use an absolute HTTPS `SITEURL` and `RELATIVE_URLS = False` for deployment.

## Standard Pelican settings consumed

| Setting | Theme behavior |
| --- | --- |
| `SITENAME` | Document title, index heading, and fallback brand label |
| `SITEURL` | Canonical, asset, content, feed, and fallback brand URL prefix |
| `DEFAULT_LANG` | Fallback `<html lang>` and content language |
| `MENUITEMS` | Primary navigation as `(label, URL)` tuples |
| `DEFAULT_PAGINATION` | Enables the previous/next pagination control |
| `TEMPLATE_PAGES` | Use `{"404.html": "404.html"}` for the packaged 404 |
| `THEME_STATIC_DIR` | Pelican-owned theme asset output directory |
| `FEED_ALL_ATOM`, `FEED_ALL_RSS` | Site-wide discovery links |
| `CATEGORY_FEED_ATOM`, `CATEGORY_FEED_RSS` | Category discovery links with `{slug}` |
| `TAG_FEED_ATOM`, `TAG_FEED_RSS` | Tag discovery links with `{slug}` |
| `AUTHOR_FEED_ATOM`, `AUTHOR_FEED_RSS` | Author discovery links with `{slug}` |
| `TRANSLATION_FEED_ATOM`, `TRANSLATION_FEED_RSS` | Language discovery links with `{lang}` |

Feed values must be non-empty local paths. External, active-scheme, malformed,
or non-string values are omitted. Absolute discovery links require an absolute
HTTP(S) `SITEURL`.

## Theme settings

| Setting | Default | Contract |
| --- | --- | --- |
| `ENGINEERING_THEME_BRAND_LABEL` | `SITENAME` | Escaped brand label |
| `ENGINEERING_THEME_BRAND_URL` | `SITEURL + '/'` | Brand destination |
| `ENGINEERING_THEME_NAV` | empty | Mappings with `label`, `url`, optional `current`; non-empty replaces `MENUITEMS` |
| `ENGINEERING_THEME_LANGUAGE_LINKS` | empty | Mappings with `label`, `url`, optional `lang`/`hreflang` |
| `ENGINEERING_THEME_FOOTER_TEXT` | empty | Escaped plain-text footer |
| `ENGINEERING_THEME_SHOW_PELICAN_CREDIT` | `False` | Shows the optional Pelican credit |
| `ENGINEERING_THEME_ENABLE_SOCIAL_METADATA` | `True` | Enables complete OG/Twitter groups when canonical data exists |
| `ENGINEERING_THEME_META_DESCRIPTION` | empty | Site fallback description |
| `ENGINEERING_THEME_SOCIAL_IMAGE` | empty | Absolute HTTP(S) preview image |
| `ENGINEERING_THEME_JSON_LD_PERSON` | empty | Mapping requiring `name` and absolute HTTP(S) `url` |
| `ENGINEERING_THEME_JSON_LD_WEBSITE` | empty | Mapping requiring `name` and absolute HTTP(S) `url` |
| `ENGINEERING_THEME_ENABLE_ARTICLE_JSON_LD` | `False` | Enables complete article schema only |
| `ENGINEERING_THEME_ARTICLE_SCHEMA_TYPE` | `Article` | Exact allowlist: `Article` or `TechArticle` |

Empty or malformed optional settings emit no empty control or incomplete
metadata group.

## Content metadata

Pelican's `Title`, `Date`, `Modified`, `Author`, `Category`, `Tags`, `Lang`,
`Slug`, `Summary`, `Status`, and translation fields work normally. These
optional metadata fields activate theme hooks:

| Source field | Normalized attribute | Purpose |
| --- | --- | --- |
| `Archive_Notice` | `archive_notice` | Historical-content notice |
| `Deprecated_Warning` | `deprecated_warning` | Do-not-use warning |
| `Source_Url` | `source_url` | Absolute HTTP(S) provenance link |
| `Source_Label` | `source_label` | Optional provenance link label |
| `Jupyter_Notebook` | `jupyter_notebook` | Must be true for notebook mode |
| `Notebook_Html_Contract` | `notebook_html_contract` | Must equal `nbconvert-basic.v1` |
| `Nb_Path` | `nb_path` | Safe POSIX-relative `.ipynb` download path |

Unsafe values fail closed. The theme does not sanitize rich output; the site
must decide which generated HTML is trusted.

## Full example

[`examples/full/pelicanconf.py`](../examples/full/pelicanconf.py) exercises the
settings above, all standard template types, pagination, translation, status,
provenance, structured data, and notebook presentation without site-specific
content.
