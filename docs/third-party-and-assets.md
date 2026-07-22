# Third-party and asset boundary

- Audit date: 2026-07-22
- Site repository: `nekrasovp/nekrasovp.github.io`
- Site snapshot: `28d786f6b26d329eab3f79154984399f46af6a24`
- Audited path: [`theme/`](https://github.com/nekrasovp/nekrasovp.github.io/tree/28d786f6b26d329eab3f79154984399f46af6a24/theme)
- Decision: no vendored theme file is copied into this repository

This is an engineering provenance and compatibility audit, not a claim that
every historical asset has a complete chain of title.

## Vendored lineage audit

The site snapshot identifies its theme as `pelican-bootstrap3`. The
[authoritative upstream theme at commit `2b80541d…`](https://github.com/getpelican/pelican-themes/tree/2b80541d755cd2d7891672650a52444e4d685e22/pelican-bootstrap3)
has an MIT license attributed to Daan Debie. The vendored directory also
contains separately licensed and separately sourced files:

| Vendored family | Evidence at the snapshot | Upstream terms reviewed | THEME-001 treatment |
| --- | --- | --- | --- |
| `pelican-bootstrap3` templates, local CSS/JS, translations, screenshots | README names the lineage; directory has its own MIT license | [MIT](https://github.com/getpelican/pelican-themes/blob/2b80541d755cd2d7891672650a52444e4d685e22/pelican-bootstrap3/LICENSE) | Do not copy; new templates and presentation will be original |
| Bootstrap 3.3.4 and Normalize CSS | Minified headers identify version and MIT terms | [Bootstrap MIT](https://github.com/twbs/bootstrap/blob/v3.3.4/LICENSE) | Do not bundle or derive the new base from Bootstrap |
| Bootswatch 3.x variants | Headers identify Thomas Park, MIT, Bootstrap base; many files import Google Fonts | [Bootswatch MIT](https://github.com/thomaspark/bootswatch/blob/v3.3.4%2B1/LICENSE) | Do not copy; no remote fonts in the core theme |
| `bootstrap.readable-old.min.css` | Header identifies Bootstrap 3.0.0 under Apache-2.0 | Apache notice-bearing file mixed into otherwise MIT variants | Do not copy |
| Font Awesome 4.7.0 CSS and font files | Header identifies CSS as MIT and font as SIL OFL 1.1 | [Upstream license split](https://github.com/FortAwesome/Font-Awesome/blob/v4.7.0/README.md#license) | Do not copy; no bundled icon font |
| Bootstrap Glyphicon font binaries | Files match the Bootstrap 3 distribution family, but no separate asset notice exists in the vendored root | Upstream Bootstrap distribution reviewed; font-specific provenance is not restated locally | Do not copy |
| jQuery 2.1.1 | Minified header names version and license URL | [MIT](https://github.com/jquery/jquery/blob/2.1.1/MIT-LICENSE.txt) | Do not copy; no jQuery dependency planned |
| Respond.js 1.1.0 and matchMedia polyfill | Header states MIT/GPLv2 and dual MIT/BSD components | [Upstream dual-license statement](https://github.com/scottjehl/Respond/blob/1.1.0/README.md) | Do not copy |
| Shariff 1.23.0 | CSS/JS headers name version and MIT | [MIT](https://github.com/heiseonline/shariff/blob/v1.23.0/LICENSE.txt) | Do not copy; social-share integration is not core theme scope |
| Tipue Search 5.0 and `search.png` | Source headers state MIT, but the vendored tree does not pin a canonical upstream revision or a separate image provenance record | Historical source header only; immutable canonical origin not established in this audit | Do not copy |
| Pygments style sheets | Generated style family is vendored without a pinned generator version | [Pygments BSD-2-Clause](https://github.com/pygments/pygments/blob/6a62df1d1fc77af7e9fc61325ef376297cadffbb/LICENSE) | Do not copy; generate or depend on reviewed styles later |
| Docutils `html4css1.css` | Header states public domain | [Authoritative stylesheet](https://github.com/docutils/docutils/blob/faf7f789806c72847021f5f52227b6f4a628fbc5/docutils/docutils/writers/html4css1/html4css1.css) | Do not copy |
| Unmarked local scripts, custom variants, and raster screenshots | Some files lack a self-contained origin/version statement | Top-level theme MIT may apply, but exact per-file provenance is not strong enough for clean extraction | Do not copy |

The conclusion is not that permissive files are unusable. It is that importing
this mixed historical bundle would add notices, stale code, remote-resource
behavior, and provenance work without helping THEME-001. Original work is the
smaller and safer boundary.

## Tool and fixture license compatibility

| Project | Reviewed license | Boundary |
| --- | --- | --- |
| [Pelican](https://github.com/getpelican/pelican/blob/3c69dc68d25a761911697467c765a16e68915c74/LICENSE) | AGPL-3.0 | Build/runtime tool; not bundled, copied, or redistributed by the theme foundation |
| [Jinja](https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/LICENSE.txt) | BSD-3-Clause | Template engine; not bundled or copied |
| [PLUGIN-003 fixture source](https://github.com/nekrasovp/pelican-jupyter/blob/137e1eb0ea620f1b15fff0ba81725eea23de1b7a/LICENSE.txt) | Apache-2.0 | Immutable fragment is referenced and hashed; no plugin code or fixture is copied in this foundation |

An MIT theme can interoperate with these tools under the stated separation.
If a future distribution bundles or modifies upstream material, its license and
notice obligations must be reassessed for that exact artifact.

## Intake policy for future files

Every proposed third-party file or substantial snippet must record:

- canonical source URL and exact tag or commit;
- original author/copyright notice;
- SPDX license identifier and full license/notice obligations;
- whether the file was modified and how;
- redistribution, font-embedding, trademark, privacy, and network behavior;
- an explicit decision to vendor, generate, depend on, or reject it.

Unlicensed assets, personal-site content, private or company material, and
assets with unclear redistribution rights are rejected. A permissive license
does not waive attribution or notice conditions.

## Core asset policy

- System fonts only; no bundled or remote web fonts.
- No icon font. Prefer accessible text or original, minimal inline SVG reviewed
  as project source.
- No copied legacy screenshots, personal images, or branding.
- No third-party JavaScript by default.
- New fixtures must be generic, versioned, provenance-recorded, and free of
  personal content.
- `THIRD_PARTY.md` or equivalent notices must be added before any approved
  third-party material enters a release artifact.

At this foundation commit, the repository contains no third-party runtime
code, theme asset, font, icon, image, or copied fixture.
