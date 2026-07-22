from pelican_engineering_theme import get_theme_path

AUTHOR = "Theme Example"
DEFAULT_AUTHOR = AUTHOR
DEFAULT_LANG = "en"
PATH = "content"
SITENAME = "Engineering Theme Example"
SITEURL = ""
THEME = str(get_theme_path())
TIMEZONE = "UTC"

ARTICLE_URL = "{slug}.html"
ARTICLE_SAVE_AS = "{slug}.html"
PAGE_URL = "pages/{slug}.html"
PAGE_SAVE_AS = "pages/{slug}.html"
RELATIVE_URLS = True

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
