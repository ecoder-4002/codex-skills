# 1080 x 1440 co-created visual system

Use this file as a quality boundary and a direction-board vocabulary, not as a preselected house style. Do not lock typography, palette, contrast rhythm, or page skeleton before checkpoint 3. After the user chooses or mixes a direction, keep that series consistent through margins, typography, palette, rules, attribution, and page markers.

## Cover

Every cover direction must satisfy these quality requirements:

- canvas: 1080 x 1440;
- deliberate background and contrast treatment selected for the direction;
- oversized editorial headline with immediate phone-scale readability;
- a disciplined editorial grid;
- restrained accent use;
- large whitespace and very little explanatory copy;
- one obvious protagonist: product, logo, UI, person, company, institution, or key object.

Keep the headline to 2-3 lines when possible. Do not turn the lower half into a feature checklist unless the checklist itself is the news. Prefer one dominant protagonist or visual metaphor and one short tension-setting line.

## Content pages

- After checkpoint 3, keep the same canvas, margins, selected type system, selected palette, rule weight, attribution, and page-marker position.
- Alternate among three archetypes instead of repeating `headline / visual box / source / body` on every page:
  1. **Evidence page**: let an official image, screenshot, document crop, quote, or captured artifact dominate; keep interpretation compact.
  2. **Explanation page**: let one number, comparison, mechanism, or diagram dominate; support it with short prose.
  3. **Statement page**: use a decisive headline, ample whitespace, and one short argument or conclusion; do not add a visual box merely to fill space.
- Use a related visual for roughly 45-60% only when the page is evidence-led. Explanation and statement pages may use a different ratio when it creates a clearer reading sequence.
- Use 80-160 Chinese characters by default and never exceed 180.
- Keep body type large enough for a phone; split pages instead of shrinking below comfortable reading size.
- Use at most one small keyword label or data callout.
- Derive page rhythm from the story. Do not assume dark cover + light body + dark conclusion. Use inversion only when it marks a meaningful editorial turn selected in the visual contract.

## Typography

- Use no more than two Chinese type families in one direction or final series.
- Explore at least two genuinely different typography voices across the direction boards when appropriate: serif-led editorial, sans-led rational, or a restrained hybrid.
- If using Songti, keep it to short display text; never use it for dense body paragraphs.
- If using a sans-led direction, preserve a visible headline/body weight contrast.
- Do not set headlines, body, labels, English, and numerals in one medium-weight font. Hierarchy must come from family or weight as well as size.
- Keep Chinese headline tracking near natural spacing; avoid exaggerated letter spacing. Use 1.45-1.58 line height for body copy.

## Palette

- Propose palettes from the story, available imagery, and desired editorial tone; do not preselect one account accent before checkpoint 3.
- Keep one dominant accent per direction and final series. Tints of the same hue are allowed.
- Let product or company brand colors live inside sourced imagery unless the brand color is itself editorially necessary.
- Make palette candidates meaningfully different in temperature, contrast, or emphasis—not merely nearby hex values.
- Use warning red only when warning, safety, conflict, or material risk is central to the verified story or the user explicitly chooses it.

## Account attribution

- Resolve `account_attribution` from the user's instruction or project config. When configured, typeset its exact value on every page, including the cover.
- Keep it in one fixed safe-area position across the series, normally bottom-left opposite the page marker.
- Use deterministic text rendering, never image-model text.
- Keep it clearly legible at phone scale but subordinate to the story hierarchy.
- Maintain sufficient contrast over both light and photographic backgrounds; use a restrained backing strip or text color change when necessary.
- When no attribution is configured, omit it consistently. Never invent a handle or render a placeholder such as `@账号名`.
- Do not replace a configured account attribution with a topic label, publication-style masthead, or brand slogan.

## Subject rules

- Product story: official product visual, interface, logo, or device.
- Person story: the person only when central to that page.
- Company story: company identity, product, or location.
- Legal or policy story: parties, institution, or generic context without readable fictional documents.
- Unreleased product: use abstract or conceptual visual and label it as such.

## Avoid

- PowerPoint bullet pages;
- card grids and excessive UI panels;
- repeating the same vertical skeleton on every content page;
- turning a short action list into four or more bordered cards by default;
- flowcharts, arrow webs, and icon collections;
- decorative portraits repeated across unrelated pages;
- invented documentary scenes or unreleased products presented as real;
- long Chinese text generated inside the image model;
- missing, misspelled, clipped, or low-contrast configured account attribution;
- gradients, glow, cyberpunk styling, and filler decoration.
