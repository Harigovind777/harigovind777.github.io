# harigovind777.github.io

My portfolio — [harigovind777.github.io](https://harigovind777.github.io)

Hand-written HTML, CSS and JavaScript. No framework, no build step, no
dependencies; the only network request beyond the page itself is the webfont.

## Notes

The shape in the hero is a **gyroid** — the level set of
`sin x·cos y + sin y·cos z + sin z·cos x = 0` — computed live on a canvas
rather than shipped as an image. It's the scaffold geometry from my thesis.

Two things make it cheap enough to animate:

- `x` depends only on the column and `y` only on the row, and `z` is constant
  across a frame, so the sines and cosines collapse into two lookup tables.
  That's two multiplies and two adds per pixel instead of six trig calls.
- Rendering pauses when the hero scrolls out of view or the tab is hidden.

The slice degenerates into parallel stripes outside `z ≈ 0.60–0.95`, so `z`
oscillates strictly inside that band and most of the motion comes from drifting
the sampling phase instead.

## Assets

Skill stamps are generated, not drawn — `assets/build_stamps.py` renders each
hanko seal with eroded edges and dry-ink specks, then quantizes to 48 colours.

```bash
cd assets && python3 build_stamps.py
```

Respects `prefers-reduced-motion`: the gyroid renders one static frame, petals
are removed, and reveal animations are disabled.
