"""
Builds the animated hero used beside the intro text in README.md.

Source: the Octocat GIF from Anmol-Baranwal/Cool-GIFs-For-GitHub (originally a
myoctocat.com build, hosted on GitHub's own user-images CDN). Credited in
SETUP.md. We re-host a processed copy rather than hotlinking because the
original is 896x896 / 95 frames / 6.1 MB — far too heavy for a README.

What this does:
  1. downscale to 380 px (it is displayed at ~330)
  2. keep every 3rd frame (95 -> 32) and triple the frame delay to match
  3. flood-fill the white studio background away from the four corners, so the
     silhouette can be recomposited — a global "near-white -> transparent" key
     would punch holes through the Octocat's eyes
  4. composite the soft-edged silhouette onto the exact banner backgrounds, and
     emit one GIF per colour scheme

Result: assets/hero.gif (dark) + assets/hero-light.gif (light), both fully
opaque, so there is no 1-bit GIF transparency fringe to fight.

Run:  python tools/make_hero.py        (expects .assets/hero-src.gif)
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageSequence

SRC = ".assets/hero-src.gif"
SIZE = 380
STEP = 3            # frame decimation
KEY_THRESH = 44     # how much of the anti-aliased white ramp to eat
EDGE_BLUR = 0.7     # softens the key so the recomposite has no jaggies
SENTINEL = (255, 0, 253)  # not present in the artwork

OUTPUTS = {
    "assets/hero.gif": (13, 17, 23),        # GitHub dark canvas
    "assets/hero-light.gif": (255, 255, 255),  # GitHub light canvas
}


def silhouette(frame):
    """Return (rgb, alpha) with the outer white background keyed out."""
    rgb = frame.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    keyed = rgb.copy()
    for seed in ((0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1)):
        if keyed.getpixel(seed) != SENTINEL:
            ImageDraw.floodfill(keyed, seed, SENTINEL, thresh=KEY_THRESH)

    # outside = 255 where the flood reached; invert to get the subject
    px = keyed.load()
    outside = Image.new("L", (SIZE, SIZE), 0)
    op = outside.load()
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x, y] == SENTINEL:
                op[x, y] = 255
    alpha = outside.filter(ImageFilter.GaussianBlur(EDGE_BLUR)).point(lambda v: 255 - v)
    return rgb, alpha


def main():
    src = Image.open(SRC)
    base_delay = src.info.get("duration", 40)
    frames = [f.copy() for i, f in enumerate(ImageSequence.Iterator(src)) if i % STEP == 0]

    print(f"source {src.size} {getattr(src, 'n_frames', 1)} frames -> keeping {len(frames)}")
    cut = [silhouette(f) for f in frames]

    os.makedirs("assets", exist_ok=True)
    for path, bg in OUTPUTS.items():
        out = []
        for rgb, alpha in cut:
            plate = Image.new("RGB", (SIZE, SIZE), bg)
            plate.paste(rgb, (0, 0), alpha)
            out.append(plate.convert("P", palette=Image.ADAPTIVE, colors=160))
        out[0].save(
            path,
            save_all=True,
            append_images=out[1:],
            duration=base_delay * STEP,
            loop=0,
            optimize=True,
        )
        print(f"wrote {path}  {SIZE}x{SIZE}  {len(out)} frames  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
