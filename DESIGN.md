# Timbre design system

Editorial, print-quiet, atmospheric. The canvas is off-white, the ink is warm
near-black, and the only colour in the system arrives as soft pastel gradient
orbs drifting behind the content. No saturated action colour, no dark developer
chrome, no heavy display type.

The rules below are the contract. Every value in the interface comes from a
token here, never from an inline hex.

---

## Overview

The base canvas is off-white `{colors.canvas}` (#f5f5f5) holding warm near-black
ink `{colors.ink}` (#0c0a09). The brand voltage is **photographic, not
chromatic**: soft pastel atmospheric gradient orbs (mint, peach, lavender, sky,
rose) drift through the page as the only "colour" moments.

Type pairs a **light display serif at weight 300** with **Inter** for body,
navigation and captions. The display weight at 300 is the editorial signature:
never bold, never heavy.

CTAs are subtle. A near-black ink pill (`{component.button-primary}`) is the
primary, a transparent outline (`{component.button-outline}`) is the secondary.
The system trusts atmosphere and modest type weights to carry the brand.

**Key characteristics**

- Off-white canvas, warm near-black ink. No saturated CTA colour.
- Single primary action: ink pill at `{rounded.pill}`.
- Display runs the serif at weight 300.
- Body runs Inter at 400 with +0.15 to 0.18px tracking.
- Five gradient orb tokens, used as atmospheric decoration only.
- Soft pill geometry for CTAs, `{rounded.xl}` for cards.
- 96px section rhythm.

---

## Colours

### Brand and accent

| Token | Value | Use |
|---|---|---|
| `{colors.primary}` | #292524 | Primary action, warm near-black pill. Used scarcely. |
| `{colors.primary-active}` | #0c0a09 | Press state. |

### Surface

| Token | Value | Use |
|---|---|---|
| `{colors.canvas}` | #f5f5f5 | Off-white page floor. |
| `{colors.canvas-soft}` | #fafafa | Lighter band for alternating sections. |
| `{colors.canvas-deep}` | #0c0a09 | Rare dark hero. |
| `{colors.surface-card}` | #ffffff | Pure white card. |
| `{colors.surface-strong}` | #f0efed | Badges, icon plates. |
| `{colors.surface-dark}` | #0c0a09 | Dark hero or CTA band. |
| `{colors.surface-dark-elevated}` | #1c1917 | Cards on dark canvas. |

### Hairlines

| Token | Value | Use |
|---|---|---|
| `{colors.hairline}` | #e7e5e4 | Default 1px divider. |
| `{colors.hairline-soft}` | #f0efed | Lighter divider. |
| `{colors.hairline-strong}` | #d6d3d1 | Stronger panel outline. |

### Text

| Token | Value | Use |
|---|---|---|
| `{colors.ink}` | #0c0a09 | Display, primary text. |
| `{colors.body}` | #4e4e4e | Running text. |
| `{colors.body-strong}` | #292524 | Emphasis. |
| `{colors.muted}` | #777169 | Sub-titles. |
| `{colors.muted-soft}` | #a8a29e | Disabled text. |
| `{colors.on-primary}` | #ffffff | Text on the ink pill. |
| `{colors.on-dark}` | #ffffff | Text on dark surfaces. |
| `{colors.on-dark-soft}` | #a8a29e | Muted text on dark. |

### Atmospheric gradient stops

| Token | Value |
|---|---|
| `{colors.gradient-mint}` | #a7e5d3 |
| `{colors.gradient-peach}` | #f4c5a8 |
| `{colors.gradient-lavender}` | #c8b8e0 |
| `{colors.gradient-sky}` | #a8c8e8 |
| `{colors.gradient-rose}` | #e8b8c4 |

These appear only as soft radial blooms behind content. Never as button fills,
never as text colours, never as a card surface.

### Semantic

| Token | Value | Use |
|---|---|---|
| `{colors.semantic-success}` | #16a34a | Confirmation. |
| `{colors.semantic-error}` | #dc2626 | Validation errors. |

---

## Typography

Display uses a light serif at weight 300. **EB Garamond** is the open-source
substitute used here; the reference system licenses Waldenburg Light. Body,
navigation, captions and buttons run **Inter**.

Fallbacks: `'Times New Roman', serif` for the display face, `sans-serif` for
Inter.

| Token | Size | Weight | Line height | Tracking | Use |
|---|---|---|---|---|---|
| `{typography.display-mega}` | 64px | 300 | 1.05 | -1.92px | Hero h1 |
| `{typography.display-xl}` | 48px | 300 | 1.08 | -0.96px | Subsidiary heroes |
| `{typography.display-lg}` | 36px | 300 | 1.17 | -0.36px | Section heads |
| `{typography.display-md}` | 32px | 300 | 1.13 | -0.32px | Sub-section heads |
| `{typography.display-sm}` | 24px | 300 | 1.2 | 0 | Card group titles |
| `{typography.title-md}` | 20px | 500 | 1.35 | 0 | Component titles, Inter |
| `{typography.title-sm}` | 18px | 500 | 1.44 | 0.18px | List labels |
| `{typography.body-md}` | 16px | 400 | 1.5 | 0.16px | Default body, Inter |
| `{typography.body-strong}` | 16px | 500 | 1.5 | 0.16px | Emphasised body |
| `{typography.body-sm}` | 15px | 400 | 1.47 | 0.15px | Footer body |
| `{typography.caption}` | 14px | 400 | 1.5 | 0 | Captions |
| `{typography.caption-uppercase}` | 12px | 600 | 1.4 | 0.96px | Section labels, badges |
| `{typography.button}` | 15px | 500 | 1.0 | 0 | CTA pill |
| `{typography.nav-link}` | 15px | 500 | 1.4 | 0 | Navigation |

**Principles**

- Display weight stays at 300. Bolding it shifts the voice from editorial to
  consumer marketing.
- Body carries +0.15 to 0.18px tracking, slightly looser than Inter's default.
- Display carries negative tracking, -0.32px to -1.92px depending on size.
- Body never drops to 300 to match the display face. It stays at 400 or 500 for
  legibility.

---

## Layout

**Spacing.** Base unit 4px. Tokens: `{spacing.xxs}` 4 · `{spacing.xs}` 8 ·
`{spacing.sm}` 12 · `{spacing.base}` 16 · `{spacing.md}` 20 · `{spacing.lg}` 24 ·
`{spacing.xl}` 32 · `{spacing.xxl}` 48 · `{spacing.section}` 96.

**Grid.** Max content width 1200px. Editorial body on a 12-column grid. Feature
grids run 2-up for splits and 3-up for benefits.

**Whitespace.** Print-magazine pacing. 96px between bands; cards inside a band
sit close, 16 to 24px apart. Orbs take generous room without competing with
copy.

---

## Elevation

Hairline plus a single soft drop. Cards float on the off-white canvas through a
1px hairline and one shadow tier. Depth beyond that comes from atmosphere, not
from stacking shadows.

| Level | Treatment |
|---|---|
| Flat | `{colors.canvas}` |
| Card | `{colors.surface-card}` |
| Border | 1px `{colors.hairline}` |
| Soft drop | `0 4px 16px rgba(0, 0, 0, 0.04)` |
| Gradient orb | Radial gradient from one `{colors.gradient-*}` stop |

---

## Shapes

| Token | Value | Use |
|---|---|---|
| `{rounded.none}` | 0px | Reserved |
| `{rounded.xs}` | 4px | Inline tags |
| `{rounded.sm}` | 6px | Compact rows |
| `{rounded.md}` | 8px | Form inputs |
| `{rounded.lg}` | 12px | Compact cards |
| `{rounded.xl}` | 16px | Feature cards |
| `{rounded.xxl}` | 24px | Gradient orb cards |
| `{rounded.pill}` | 9999px | CTAs, badges |
| `{rounded.full}` | 9999px | Icon circles, avatars |

---

## Components

**`button-primary`** — Ink pill. Background `{colors.primary}`, text
`{colors.on-primary}`, `{typography.button}`, padding 10 × 20px, height 40px,
`{rounded.pill}`. Press state uses `{colors.primary-active}`.

**`button-outline`** — Transparent pill, 1px `{colors.hairline-strong}` border,
text `{colors.ink}`.

**`button-tertiary-text`** — Inline ink text link.

**`hero-band`** — `{colors.canvas}`, display headline in
`{typography.display-mega}`, subhead in `{typography.body-md}`, atmospheric orb
behind the headline.

**`gradient-orb-card`** — Soft radial orb behind centred copy. Background
`{colors.canvas-soft}`, `{rounded.xxl}`, padding 32px. One gradient token per
variant.

**`feature-card`** — `{colors.surface-card}`, `{rounded.xl}`, padding 24px, 1px
hairline border.

**`badge-pill`** — `{colors.surface-strong}`, `{typography.caption-uppercase}`,
`{rounded.pill}`, padding 4 × 10px.

**`text-input`** — `{colors.surface-card}`, `{rounded.md}`, padding 12 × 16px,
height 44px, 1px `{colors.hairline-strong}`. Focus thickens the border to 2px
ink.

**`voice-icon-circular`** — `{colors.surface-strong}`, `{rounded.full}`, 32px.

**`cta-band`** — Pre-footer. `{colors.canvas}`, centred headline in
`{typography.display-lg}`, one ink pill. 96px padding.

**`footer`** — `{colors.canvas}`, text `{colors.body}`,
`{typography.body-sm}`.

---

## Applied to Timbre

This app is a local tool rather than a marketing site, so the system maps as
follows. The editorial calm carries over; the marketing furniture does not.

| Surface here | Pattern | Notes |
|---|---|---|
| Page header | `hero-band` | Display serif wordmark, one line of body copy, an orb behind it |
| Dropzone | `gradient-orb-card` | The one place an orb sits behind interactive content, because it is the primary action |
| Language chips | `badge-pill` | Selected state inverts to ink, unselected keeps `{colors.surface-strong}` |
| Model and format selects | `text-input` | Same 8px radius and hairline border |
| Job progress rows | `feature-card` | Hairline separated, progress bar in ink rather than a status colour |
| Transcribe button | `button-primary` | The only ink pill on the page |
| Cancel, Start over | `button-tertiary-text` | Never competes with the primary |
| Error banner | `{colors.semantic-error}` on `{colors.surface-card}` | Semantic colour is the one exception to the no-colour rule |
| Footer | `footer` | One line, muted |

**Orb placement.** Two orbs total: one behind the header, one behind the
dropzone. More than that turns atmosphere into decoration for its own sake.

**Progress bars** fill with `{colors.ink}`, not a status colour. Completion is
communicated by the label, not by turning something green.

---

## Do's and don'ts

**Do**

- Reserve the ink pill for the primary action, one per view.
- Keep display copy at weight 300.
- Track body text at +0.15 to 0.18px.
- Use orbs as atmosphere only.
- Use the pill shape for every CTA and badge.

**Don't**

- Don't introduce a saturated brand colour. The ink pill is the only CTA colour.
- Don't bold display copy.
- Don't use gradient orbs as button fills, text colours, or component
  backgrounds.
- Don't use square corners on a CTA.
- Don't drop body Inter to 300 to match the display face.

---

## Responsive behaviour

| Name | Width | Changes |
|---|---|---|
| Mobile | < 640px | Hero 64 → 32px; cards 1-up; orbs shrink |
| Tablet | 640–1024px | Hero 48px; cards 2-up |
| Desktop | 1024–1280px | Hero 64px; cards 3-up |
| Wide | > 1280px | Content caps at 1200px |

Touch targets: the primary pill is 40px tall, padded to clear AAA. Icon circles
are 32px inside a padded row that yields a 48px tap zone.

Orbs shrink at every breakpoint but never disappear.

---

## Known gaps

- Waldenburg is licensed. EB Garamond at 300 is the substitute (no 300 cut exists on Google Fonts, so
400 ships and carries the same intent) used here.
- Animation timings (orb drift, hero entrance) are out of scope.
- Validation states beyond focus are not specified.
