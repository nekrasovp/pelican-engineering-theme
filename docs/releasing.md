# Release process

This is the reusable release procedure. Repository text never authorizes a
release by itself; every release still requires a fresh explicit owner
decision. The workflow publishes packages only and never deploys a consuming
site.

## One-time protected setup

Create these GitHub environments only during an authorized publication task:

| Environment | Required protection | Job permission |
| --- | --- | --- |
| `github-release` | Required owner approval, admin bypass disabled, selected tag pattern `v*` | `contents: write` only |
| `pypi` | Required owner approval, admin bypass disabled, selected tag pattern `v*` | `id-token: write` only |

Configure the PyPI Trusted Publisher with owner `nekrasovp`, repository
`pelican-engineering-theme`, workflow `release.yml`, and environment `pypi`.
Do not add a username, password, API token, or environment secret. PyPI matches
the workflow/environment OIDC claims, and GitHub withholds an environment job
until its protection rules pass. See the official
[PyPI Trusted Publishing guide](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
and [GitHub environment protection reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

No stored PyPI token is permitted.

## Authorized release sequence

1. Recheck the PyPI project/name, Trusted Publisher, environment protections,
   branch/tag rules, workflow action pins, and default branch source.
2. Review one exact GREEN candidate head and its local/hosted wheel, sdist,
   source SHA, SHA-256 hashes, inventories, installed-artifact builds,
   screenshots, axe, and no-network evidence.
3. Merge only after the exact pull-request head is GREEN and explicitly
   approved for release. Rerun the same gates on the exact merge SHA.
4. Create one immutable `v0.1.0` tag at that reviewed commit.
5. Draft release notes from [`0.1.0.md`](release-notes/0.1.0.md), verify the tag
   target, then explicitly publish the GitHub Release.
6. The `release: published` event checks out the tag, proves
   `actual source SHA == github.sha`, rebuilds twice, verifies inventories and
   candidate provenance, and uploads assets without `--clobber` behind the
   `github-release` environment.
7. After that environment succeeds, the separate `pypi` environment may issue
   a short-lived OIDC credential to the pinned PyPA action. PyPI rejects reuse
   of an existing version; the workflow does not enable `skip-existing`.
8. Download the public files, compare SHA-256 with the approved candidate,
   install from PyPI in a clean environment, build the generic example, and
   only then record released-version validation.

The release workflow has no `push`, `pull_request`, schedule, dispatch, or
workflow-chain trigger. Publishing a GitHub Release is the separate explicit
release action. Both external publication jobs additionally require protected
environment approval.

## Failure handling

Never overwrite a release asset or package file. If GitHub asset attachment
fails, stop before PyPI. If PyPI publication fails, diagnose without a retry
that changes bytes. If a published version is defective, yank it and prepare a
new patch version; do not replace `0.1.0` artifacts.
