"""
Crops the animated social icons down to their actual artwork.

The originals (from Anmol-Baranwal/Cool-GIFs-For-GitHub) are 1080x1080 canvases
with a comparatively small logo floating in the middle of a lot of transparent
padding. Embed one at height="44" and you get a ~10 px glyph surrounded by 34 px
of nothing — the icons look broken and the row spaces itself out oddly, because
the padding still occupies layout width.

So: take the union of every frame's alpha bounding box, crop to it, scale to a
common height, and write the result into assets/social/. Side benefits — the
files drop from ~1.2 MB total to ~100 KB, and nothing is hotlinked.

Outputs:
  assets/social/linkedin.gif
  assets/social/x.gif
  assets/social/discord.gif
  assets/social/email.png     (already a still, just cropped + scaled)

Run:  python tools/make_social.py      (needs Pillow + network)
"""
import io
import os
import urllib.request

from PIL import Image, ImageSequence

BASE = "https://user-images.githubusercontent.com/74038190/"

SOURCES = {
    "linkedin.gif": BASE + "235294012-0a55e343-37ad-4b0f-924f-c8431d9d2483.gif",
    "x.gif":        BASE + "235294011-b8074c31-9097-4a65-a594-4151b58743a8.gif",
    "discord.gif":  BASE + "235294015-47144047-25ab-417c-af1b-6746820a20ff.gif",
    "email.png":    BASE + "216122065-2f028bae-25d6-4a3c-bc9f-175394ed5011.png",
}

OUT = "assets/social"
HEIGHT = 96      # rendered at 48 in the README, so it stays sharp on retina
PAD = 0.06       # a little breathing room, as a fraction of the crop
TRANSPARENT = 255  # palette slot reserved for transparency


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-asset-builder"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return Image.open(io.BytesIO(r.read()))


def frames_of(im):
    return [f.convert("RGBA") for f in ImageSequence.Iterator(im)]


def union_bbox(frames):
    """Bounding box of every non-transparent pixel across all frames."""
    box = None
    for f in frames:
        b = f.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()
        if not b:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                    max(box[2], b[2]), max(box[3], b[3]))
    return box


def square(box, w, h):
    """Grow the crop to a padded square so every icon shares one scale."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = max(x1 - x0, y1 - y0) / 2 * (1 + PAD)
    half = min(half, cx, cy, w - cx, h - cy)
    return (round(cx - half), round(cy - half), round(cx + half), round(cy + half))


def to_gif_frame(rgba):
    """RGBA -> palette frame with one reserved transparent index.

    Only FASTOCTREE/libimagequant accept RGBA, and neither reserves an index for
    us, so quantise the colours and then stamp the transparent pixels in by hand.
    Without this the icons carry a halo of whatever colour happened to land in
    slot 0.
    """
    p = rgba.convert("RGB").quantize(colors=TRANSPARENT, method=Image.MEDIANCUT)
    holes = rgba.getchannel("A").point(lambda a: 255 if a < 128 else 0)
    p.paste(TRANSPARENT, (0, 0), holes)
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, url in SOURCES.items():
        src = fetch(url)
        w, h = src.size
        frames = frames_of(src)

        box = union_bbox(frames)
        if not box:                      # fully opaque source — nothing to crop
            box = (0, 0, w, h)
        box = square(box, w, h)

        out = [f.crop(box).resize((HEIGHT, HEIGHT), Image.LANCZOS) for f in frames]
        path = os.path.join(OUT, name)

        if name.endswith(".png") or len(out) == 1:
            out[0].save(path, optimize=True)
        else:
            pal = [to_gif_frame(f) for f in out]
            pal[0].save(path, save_all=True, append_images=pal[1:], loop=0,
                        duration=src.info.get("duration", 60), disposal=2,
                        transparency=TRANSPARENT, optimize=True)

        print(f"wrote {path}  crop {box[2]-box[0]}px of {w}px  "
              f"{len(out)} frame(s)  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
