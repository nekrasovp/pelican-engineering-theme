Title: A Configurable Shell
Date: 2026-02-01
Modified: 2026-02-03
Category: Guides
Tags: example
Slug: configurable-shell
Summary: Generic content for the complete optional-configuration fixture.

This page proves that the reusable shell accepts configuration without a theme
fork.

<div class="pet-status-notice" role="status">
  <p>The status-notice style is available to ordinary authored content.</p>
</div>

```python
def configured(value: str) -> str:
    return value.strip()
```
