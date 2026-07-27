# Example deployment

Deployment belongs to the consuming Pelican site. The theme package emits
ordinary static files and performs no deployment itself.

## Production configuration

Keep development settings in `pelicanconf.py` and add a site-owned
`publishconf.py`:

```python
from pelicanconf import *  # noqa: F403

SITEURL = "https://docs.example.test"
RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
FEED_ALL_ATOM = "feeds/all.atom.xml"
```

Build with an exact locked site dependency on the published theme version. For
an unreleased future change, use only a separately verified artifact digest:

```sh
python -I -m pelican content -s publishconf.py -o output
test -f output/index.html
test -f output/theme/css/scaffold.css
```

Upload only `output/` to the static host. Configure the host separately for
HTTPS, custom domains, cache behavior, redirects, and rollback.

## GitHub Pages shape

A consuming repository may build with GitHub Actions, upload `output/` as the
Pages artifact, and deploy it through a protected `github-pages` environment.
Pin actions to full SHAs, use a locked site environment, validate routes/links
before deployment, retain the previous complete artifact, and smoke-test the
live canonical host afterward.

This repository does not include a Pages workflow because it is a theme, not a
site. No Pages setting, DNS record, domain, deployment, or production content
was changed while preparing `0.1.0`.
