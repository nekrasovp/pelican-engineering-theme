from pathlib import Path

from pelican_engineering_theme import get_theme_path

AUTHOR = "Example Editors"
DEFAULT_AUTHOR = AUTHOR
DEFAULT_LANG = "en"
PATH = "content"
SITENAME = "Generic Systems Journal"
SITEURL = ""
THEME = str(get_theme_path())
THEME_TEMPLATES_OVERRIDES = [str(Path(__file__).parent / "templates")]
TIMEZONE = "UTC"

ARTICLE_URL = "{slug}.html"
ARTICLE_SAVE_AS = "{slug}.html"
PAGE_URL = "pages/{slug}.html"
PAGE_SAVE_AS = "pages/{slug}.html"
RELATIVE_URLS = True
DEFAULT_PAGINATION = 2
TEMPLATE_PAGES = {"404.html": "404.html"}

ENGINEERING_THEME_BRAND_LABEL = "Systems Journal"
ENGINEERING_THEME_BRAND_URL = "/"
MENUITEMS = (
    ("Overview", "/"),
    ("Guides", "/guides/"),
    ("Reference", "/reference/"),
)
ENGINEERING_THEME_LANGUAGE_LINKS = (
    {"label": "Français", "url": "/fr/", "lang": "fr"},
)
ENGINEERING_THEME_FOOTER_TEXT = "A generic technical publication example."
ENGINEERING_THEME_SHOW_PELICAN_CREDIT = True
ENGINEERING_THEME_JSON_LD_PERSON = {
    "name": "Example Editor",
    "url": "https://example.test/about/",
}
ENGINEERING_THEME_JSON_LD_WEBSITE = {
    "name": "Generic Systems Journal",
    "url": "https://example.test/",
}
ENGINEERING_THEME_ENABLE_ARTICLE_JSON_LD = True
ENGINEERING_THEME_ARTICLE_SCHEMA_TYPE = "TechArticle"

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
TAG_FEED_ATOM = None
TAG_FEED_RSS = None
