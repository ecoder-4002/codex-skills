# Remotion motion patterns for reference reconstruction

Read this only after the Phase 1 static master and layer pack have been explicitly approved, or when the user has explicitly requested one-shot execution.

## Controlled entrance progress

Use a dedicated progress function for a motion family instead of forcing every layer through the same easing:

```tsx
const revealProgress = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, Math.max(start + 1, end)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.4, 0, 0.2, 1),
  });
```

Tune against exact source frames. A plausible curve is not evidence of a correct curve.

## Pivoted independent reveal

Keep each object in its own wrapper and express the pivot in composition coordinates:

```tsx
<Interactive.Div
  name="Left building"
  style={{position: "absolute", inset: 0, clipPath: slotClip}}
>
  <div
    style={{
      position: "absolute",
      inset: 0,
      translate: `0px ${interpolate(progress, [0, 1], [risePx, 0])}px`,
      rotate: `${interpolate(progress, [0, 1], [startDegrees, 0]) + wobble}deg`,
      transformOrigin: `${pivotX}px ${pivotY}px`,
    }}
  >
    <Img src={staticFile(asset)} style={{position: "absolute", inset: 0}} />
  </div>
</Interactive.Div>
```

For a pair that fans outward, use adjacent inner pivots near the shared slot. Give each layer its own rotation sign, rise distance, and optionally timing.

## Slot reveal

When objects emerge from a platform, distinguish three depths:

1. hidden below the slot;
2. visible above the platform edge;
3. allowed to cover the platform in the final collage.

A fixed outer clip can hide the translated object early. If the final subject extends lower, animate the clip boundary only near the end of the entrance. Validate that this does not create a one-frame flash.

## Finite damped wobble

Use deterministic finite settlement, not CSS animation or perpetual oscillation:

```tsx
const dampedWobble = (
  frame: number,
  start: number,
  duration: number,
  amplitude: number,
) => {
  if (frame <= start || frame >= start + duration) return 0;
  const t = (frame - start) / duration;
  return amplitude * Math.sin(t * Math.PI * 3) * Math.pow(1 - t, 2);
};
```

Useful starting range for a subtle photographic collage at 30fps:

- amplitude: roughly 0.8–1.8 degrees;
- duration: 12–18 frames;
- paired layers: opposite signs and a 0–2 frame response delay.

These are starting values only. Use them only when the reference shows settlement, and tune against the source.

## Controllable props

For each independent hero layer, prefer props for:

```text
asset
start / end
risePx
startRotation
pivotX / pivotY
wobbleDegrees
```

Shared props may cover wobble duration or a response delay. Keep defaults inline on the `Composition` so Studio can write edits back to code.
