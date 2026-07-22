# Version policy

The project follows Semantic Versioning with an explicit pre-1.0 contract.

| Version | Meaning |
| --- | --- |
| `0.1.0` | First documented candidate/example contract |
| `0.2.0` | Planned validation against real-site content without bundling it |
| `1.0.0` | Stable configuration/customization contract after production use |

Before `1.0.0`, a breaking change to a documented setting, the 18 public Jinja
blocks, a public CSS token, color-mode storage behavior, supported matrix, or
notebook markup contract requires a minor release and migration notes. Patch
releases may fix defects and add compatible optional behavior; they must not
replace already published files under the same version.

At and after `1.0.0`, those breaking changes require a major release. Internal
selectors, private tokens, fixture implementation, and undocumented markup are
not stable API, but changes still require browser/accessibility review.

Every release must come from one immutable tag/commit, use unique artifacts,
and record SHA-256 provenance. A broken published pre-1.0 version is yanked and
followed by a new patch; artifacts are never overwritten.
