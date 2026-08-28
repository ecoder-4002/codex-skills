# Layer decomposition

Read this during Phase 1 when turning a reference clip into a clean static master and independently controllable assets. Phase 1 ends with a user-visible review package and must not silently continue into Remotion.

## Evidence hierarchy

Use multiple settled frames when compression, subtitles, or moving overlays contaminate a single frame. The final frame is composition evidence, not automatically a clean source asset.

Separate:

- persistent background texture;
- supporting geometry;
- context fields such as circles or panels;
- hero objects;
- logos or labels that move independently;
- perspective-ground text;
- subtitles, watermarks, cursors, and player chrome.

Only exclude overlays that are not part of the requested motion design.

## Full-canvas layers

Default each animation layer to the full composition dimensions with transparency outside the subject. Benefits:

- exact final-state registration;
- pivots expressed directly in composition coordinates;
- no repeated crop-offset arithmetic;
- simpler layer replacement in Remotion.

Keep cropped versions only as optional overlays or export conveniences.

## Split criteria

Create separate assets when any of these differ:

- entrance direction or start frame;
- rotation direction or pivot;
- reveal mask;
- z-order during motion;
- settlement or wobble;
- user-requested editability.

Allow a small overlap along a real architectural seam when two rotating photographic layers must meet cleanly. Render the intended foreground piece last. If opposite rotations expose a wedge, move both pivots toward the shared hinge before widening masks.

## Reconstruct supporting geometry

Do not flatten depth cues into generic rectangles. Measure the actual silhouette and shading.

Common examples:

- a “black base” may be a lower-wider trapezoid with a vertical charcoal-to-black gradient;
- a faint gray circle may sit behind the hero and remain partially occluded;
- outlined text may be projected onto a ground plane, with a narrow upper edge and a flared lower edge.

Prefer vector or procedurally drawn geometry for these shapes so their perspective and depth remain controllable.

## Manifest fields

Record at least:

```json
{
  "file": "03a_left_building.png",
  "role": "left evidence object",
  "zOrder": 4,
  "pivot": [1050, 815],
  "sourceRect": [560, 210, 1120, 835],
  "motion": "rise + counterclockwise reveal + damped settle"
}
```

Also record canvas size, fps, reference duration, excluded overlays, and the observed information order.

## Visual QA

Composite all final-state layers and compare against the clean master. Investigate:

- halos caused by difference masks;
- duplicated pixels in overlap zones;
- missing antialiased edges;
- hard vertical seams;
- geometry that hides subject pixels at the final pose;
- contamination from captions or watermarks.

## Phase 1 acceptance package

Before pausing for user review, provide all of the following:

- labeled first/settled/final reference frames;
- the complete clean static master;
- a layer-pack preview that separates every control unit;
- the manifest with z-order and anchors/pivots;
- paths to editable sources;
- any unresolved masking, reconstruction, or source-quality concern.

Use status `STATIC_REVIEW_REQUIRED`. Corrections remain in Phase 1 until the user explicitly approves proceeding to Remotion.
