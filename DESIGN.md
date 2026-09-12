---
name: Astrolabe
description: An observatory's working atlas, with readable evidence and five connected altitudes.
tags: [ClaudeAI]
colors:
  paper: "#f4f5f1"
  surface: "#fff"
  raised: "#e9ece7"
  ink: "#182c32"
  muted: "#53676b"
  line: "#ccd5d1"
  brass: "#826222"
  accent: "#146578"
  hathi: "#64548b"
  skoll: "#146578"
  good: "#237051"
  warn: "#836118"
  critical: "#b0413a"
  none: "#5c6b6d"
  gate: "#87969c"
  forge: "#b38b41"
  flow: "#438878"
  dark-paper: "#102329"
  dark-surface: "#162d34"
  dark-raised: "#203a41"
  dark-ink: "#e3ede7"
  dark-muted: "#a5b9bb"
  dark-line: "#365057"
  dark-brass: "#ddbd78"
  dark-accent: "#87c7cd"
  dark-hathi: "#bdafe0"
  dark-skoll: "#87c7cd"
  dark-good: "#83c9ab"
  dark-warn: "#dec07c"
  dark-critical: "#f49a8e"
  dark-none: "#a0afb2"
  dark-gate: "#78969f"
  dark-forge: "#d7b372"
  dark-flow: "#7cbfa8"
typography:
  display:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "36px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  headline:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.55
    letterSpacing: "-0.025em"
  title:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "16px"
    fontWeight: 700
  body:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "16px"
    lineHeight: 1.55
  label:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "12px"
  action:
    fontFamily: 'Manrope, "Avenir Next", sans-serif'
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.55
rounded:
  compact: "3px"
  stage: "4px"
  field: "5px"
  control: "6px"
  altitude: "7px"
  plate: "8px"
  circular: "50%"
spacing:
  inline: "8px"
  controls: "12px"
  group: "24px"
  columns: "32px"
  plate: "40px"
components:
  button-primary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    typography: "{typography.action}"
    rounded: "{rounded.field}"
    padding: "10px 14px"
  button-primary-hover:
    backgroundColor: "{colors.raised}"
  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "11px 13px"
    width: "100%"
  altitude-navigation:
    textColor: "{colors.ink}"
    rounded: "{rounded.altitude}"
    padding: "15px 12px"
  altitude-navigation-active:
    backgroundColor: "{colors.raised}"
  domain-row:
    textColor: "{colors.ink}"
    padding: "20px 6px"
    width: "100%"
  domain-row-hover:
    backgroundColor: "{colors.raised}"
  stage-selector:
    textColor: "{colors.ink}"
    rounded: "{rounded.stage}"
    padding: "0 4px"
---

# Design System: Astrolabe

## Overview

**Creative North Star: "An observatory's working atlas"**

Open plates, aligned evidence, and quiet instrument-like controls make a dense interface readable. Mineral white and deep petroleum provide equivalent light and dark working environments. The celestial layer belongs to orientation, while the interface keeps text, comparison, and action in the foreground.

**Key Characteristics:**

- Open layouts with hairline divisions and restrained tonal layering.
- Manrope typography with tabular numerals for comparable quantities.
- Persistent five-altitude orientation and clear selected states.
- Brief transitions and a reduced-motion presentation.

This record is extracted from `atlas.css` and the component markup in `app.js`. Frontmatter values are normative; the extension sidecar records behavior and preview snippets. Dark-prefixed colors describe the overrides of the same CSS custom properties under the dark theme. Space and radius names describe observed values, not an additional CSS variable system.

## Colors

### Primary

Blue-green accent identifies links, active navigation codes, text selection, and keyboard focus. Skoll uses the same source color through a distinct semantic variable.

### Secondary

Brass marks the compass and brand instrument. Hathi violet distinguishes the other domain wing. Condition colors communicate recorded status; gate, forge, and flow identify work stages. Preserve these separate meanings even where their hues resemble one another.

### Neutral

Paper is the working background, surface supports inputs and overlays, and raised marks selection or emphasis. Ink carries primary text; muted carries supporting labels; line separates aligned regions. Both themes retain these roles.

**The Evidence Label Rule.** Pair status dots and colored work distributions with labels or counts; color alone does not explain the evidence.

## Typography

Manrope with Avenir Next and sans-serif fallbacks carries the interface. The circular brand mark alone uses Georgia. Display headings are medium-weight and tightly tracked; domain titles and action labels carry stronger weight. Supporting labels stay small without turning the entire interface into caption text.

Use the frontmatter hierarchy. Task titles use (14px) type with (1.65) line height; search fields use (13px). Major readouts use (32px), and fleet/metric tallies use (28px), both at weight (500). Comparable codes, counts, and readings use tabular numerals. At the (800px) breakpoint, display headings become (30px). Data notes have a maximum measure of (90ch).

## Layout

The desktop altitude rail is (216px), paired with an open workspace capped at (1700px). Default workspace padding is (32px 36px 56px). The domain matrix has two equal columns separated by (32px); work columns use three equal tracks with a (22px) gap. Task lists scroll within a (62vh) maximum height, with a cue shown when the list overflows.

At widths up to (1200px), the rail becomes (174px) and workspace padding becomes (28px 24px). At (800px), the rail becomes a sticky horizontal navigation strip, long navigation subtitles disappear, and the workspace uses (26px 20px 40px) padding. At (520px), domain and task columns stack, with workspace padding of (24px 18px 36px). From (1700px), horizontal workspace padding becomes (56px).

## Elevation & Depth

The system uses no box shadows. Depth comes from paper/surface/raised tones, borders, and overlay stacking. The drawer backdrop uses `#06161a88`; the search backdrop uses `#06161abb`. These are overlay treatments, not replacement theme backgrounds.

Panel entry uses a (220ms ease-out) arrival from opacity (0.3) and a (5px) downward offset. Drawer translation uses (180ms ease). Reduced-motion settings remove animation and transitions and hide the ambient layer. The celestial canvas is limited to the compass altitude.

## Shapes

Small radii soften controls without turning every content row into a card. Fields and primary actions share the field radius; altitude controls are slightly rounder; bounded plates use the plate radius. Domain and task rows use open, square-edged bottom dividers. Circular marks are reserved for the compass, brand instrument, and evidence dots.

## Components

### Buttons

Primary actions use raised fill, ink text, a line-colored border, and a minimum height of (42px). Their hover fill remains raised. Ghost actions share the same dimensions and acquire raised fill on hover. Keyboard focus uses an accent outline (3px) offset by (4px); disabled buttons have opacity (0.45) and the default cursor.

### Inputs / Fields

Search uses a surface background, line border, muted placeholder, and accent caret. The compact search wrapper is capped at (280px) until responsive layouts release that cap. Search has no additional hover color shift in the source. Preserve the visible focus outline and an accessible label.

### Navigation

The altitude control pairs a tabular code with a bold name and a muted subtitle. Current selection adds raised fill and a line border, and changes the code to accent. Mark the current altitude with `aria-current="page"`; retain keyboard focus across rerenders. The mobile strip keeps all five codes and names visible.

### Domain rows

Whole-row buttons combine identity, a two-line description, status evidence, and task scope. Hover and selection add raised fill. An inline arrow supports the affordance. Keep supporting text and evidence labels legible; use generic sample content in design previews.

### Stage selector

Three equal controls pair a large count with a small stage label. Hover adds raised fill. Selection uses an accent outline (1px) and `aria-pressed`; clicking an already selected stage clears that filter. The selected outline also remains (1px) when focused because the source selected-state selector overrides the global focus width; the focus offset remains (4px).

### Contextual instruments

An open shelf uses complete rows: three records on desktop, two at or below (800px), one at or below (520px). Explicit expansion reveals the remaining records; never clip a row to suggest more content. Focus-level marks describe routes, not measured scores. Wing/domain scope sits beside the heading. A source workspace replaces the viewport while retaining a return action and related focus routes. Its isolated capture preserves the source dashboard's visual language; the surrounding controls follow the Astrolabe theme. Capture and runtime limitations remain visible.

### Project planning

Date and project selectors are compact field variants with paper fill, (4px) radius, and (9px) padding. Open project rows pair a proportional Gate/Forge/Flow strip with visible stage names and exact counts, using the existing stage-color tokens. Project evidence follows wing, domain, and date scope; labels distinguish subsequent board filters. Connected editing uses the existing drawer and compact fields, with explicit submission and inline errors. Public read-only and local connected status are visibly distinguished.

The sidecar includes five self-contained visual previews of the incumbent primitives. They represent static states and CSS interaction; application navigation and filtering remain in `app.js`. The instrument and planning extensions reuse those primitives without changing the token system.

## Do's and Don'ts

- Do preserve the same semantic color roles across light and dark themes.
- Do align comparable quantities and use tabular numerals.
- Do keep keyboard focus, current navigation, and selected filters visibly identifiable.
- Do respect reduced-motion settings and responsive stacking.
- Don't replace open rows with a repeated grid of elevated cards.
- Don't use decorative color or motion to imply evidence the interface does not contain.
- Don't place personal records, task titles, or access material in design examples.

## Backlinks

[[The Astrolabe]] · [[Axis Mundi]]
