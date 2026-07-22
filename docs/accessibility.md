# Accessibility statement

The `0.1.0` candidate is designed around semantic HTML, keyboard operation,
readable contrast, reduced motion, local overflow, and a complete no-JavaScript
light fallback. This statement covers the generic examples, not arbitrary
publisher content or overrides.

## Implemented behavior

- a working skip link and exactly one focusable semantic main target;
- native navigation links and a native color-mode button with synchronized
  accessible name and `aria-pressed` state;
- logical DOM, visual, and keyboard order at narrow widths;
- visible focus indicators and computed WCAG AA contrast gates for shipped
  normal text, controls, notices, code, and meaningful boundaries;
- unconditional light first visit, explicit dark choice, readable light print,
  and no nonessential transition for reduced-motion users;
- headings, landmarks, dates, status notices, figures/captions, and locally
  labeled keyboard-operable wide notebook tables;
- no remote font or third-party runtime dependency.

## Verification

Real Chromium acceptance covers 390x844, 768x1024, and 1440x1000 viewports,
keyboard focus, skip navigation, both palettes, JavaScript disabled, blocked
storage, reduced motion, print, article/archive/taxonomy/404/notebook surfaces,
horizontal overflow, and zero external requests. Representative pages are
scanned with locked development-only axe-core 4.12.1. Browser and axe results
are technical evidence, not a guarantee for changed site content.

## Known limits

- Publisher content, alternative text, headings, tables, colors, overrides,
  embeds, and third-party scripts remain the publisher's responsibility.
- The theme does not sanitize trusted notebook HTML or make inaccessible rich
  output accessible automatically.
- Automated scans cannot replace keyboard, screen-reader, zoom/reflow, or
  cognitive review by people.

Report a reproducible problem with the accessibility issue template. Do not
include personal or sensitive information.
