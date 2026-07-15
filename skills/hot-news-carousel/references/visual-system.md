# 1080 x 1440 visual system

## Cover

Use this editorial system as the directional baseline; it does not depend on a separate reference image:

- canvas: 1080 x 1440;
- warm off-white background;
- oversized black headline with immediate phone-scale readability;
- thin black horizontal rules and a disciplined editorial grid;
- one restrained accent color, normally derived from the subject;
- large whitespace and very little explanatory copy;
- one obvious protagonist: product, logo, UI, person, company, institution, or key object.

Do not turn the lower half into a feature checklist unless the checklist itself is the news. Prefer one meaningful visual and one short tension-setting line.

## Content pages

- Keep the same canvas, margins, type family, accent, rule weight, and page-marker position.
- Use a related image or visual for roughly 45-60% of the page.
- Reserve roughly 40-55% for headline and 2-3 short natural paragraphs.
- Use 80-160 Chinese characters by default and never exceed 180.
- Keep body type large enough for a phone; split pages instead of shrinking below comfortable reading size.
- Use at most one small keyword label or data callout.

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
- flowcharts, arrow webs, and icon collections;
- decorative portraits repeated across unrelated pages;
- invented documentary scenes or unreleased products presented as real;
- long Chinese text generated inside the image model;
- missing, misspelled, clipped, or low-contrast configured account attribution;
- gradients, glow, cyberpunk styling, and filler decoration.
