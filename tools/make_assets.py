"""
Generates the custom image assets used by README.md.

  assets/header.png        1600x420  dark-mode banner
  assets/header-light.png  1600x420  light-mode banner
  assets/rule.png          1600x12   accent divider (one file, both themes)

Nothing here is a third-party badge service — the whole point is that the
banner is drawn for this profile and lives in this repo.

Composition of the banner:
  - flat near-black (or near-white) ground with a fine dot matrix
  - two soft glows, mint low-left and violet behind the grid
  - right side: a contribution-grid motif that dissolves toward the wordmark
  - left: letter-spaced heavy wordmark, mono role line, dim affiliation
  - corner ticks top-left / bottom-right

Run:  python tools/make_assets.py
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 420

FONT_DIR = "C:/Windows/Fonts/"
HEAVY = ["seguibl.ttf", "bahnschrift.ttf", "arialbd.ttf", "segoeuib.ttf"]
MONO = ["consola.ttf", "cour.ttf"]

NAME = "NAKUL FALSWAL"
ROLE = "AI ENGINEER  \u00b7  SECURITY TINKERER  \u00b7  BUILDER"
ORG = "BML MUNJAL UNIVERSITY"

THEMES = {
    "assets/header.png": dict(
        bg=(13, 17, 23),      # GitHub dark canvas — blends seamlessly
        ink=(233, 238, 245),
        role=(196, 208, 222),
        dim=(110, 122, 138),
        mint=(0, 229, 160),
        violet=(124, 92, 255),
        empty=(22, 27, 34),
        dot=(255, 255, 255, 26),
        glow=(0.13, 0.15),
    ),
    "assets/header-light.png": dict(
        bg=(255, 255, 255),   # GitHub light canvas
        ink=(13, 17, 23),
        role=(55, 65, 81),
        dim=(122, 133, 148),
        mint=(0, 160, 112),
        violet=(94, 62, 226),
        empty=(224, 228, 234),
        dot=(0, 0, 0, 24),
        glow=(0.10, 0.10),
    ),
}

# Divider accent runs mint -> violet regardless of page theme.
RULE_A = (0, 200, 140)
RULE_B = (112, 84, 245)


def pick(cands, size):
    for c in cands:
        p = os.path.join(FONT_DIR, c)
        if os.path.exists(p):
            return ImageFont.truetype(p, size), c
    return ImageFont.load_default(), "default"


def tracked(draw, xy, text, font, fill, track=0):
    """Draw text with manual letter-spacing (PIL has no tracking)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track
    return x


def glow_blob(center, radii, color, strength, blur=190):
    """A properly-blurred radial glow at full canvas size.

    Built at full res and Gaussian-blurred — the small-mask-then-upscale trick
    bands badly and leaves a visible blocky edge.
    """
    cx, cy = center
    rx, ry = radii
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    mask = mask.point(lambda a: int(a * strength))
    layer = Image.new("RGBA", (W, H), color + (0,))
    layer.putalpha(mask)
    return layer


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def hramp(x_start, x_end):
    """Smooth 0->255 horizontal ramp as an L mask (no hard threshold)."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    span = max(1, x_end - x_start)
    for x in range(W):
        d.line([(x, 0), (x, H)], fill=int(255 * smoothstep((x - x_start) / span)))
    return m


def build_header(path, t):
    img = Image.new("RGB", (W, H), t["bg"]).convert("RGBA")

    # --- glows: keep the left side flat so the wordmark pops ---------------
    g1, g2 = t["glow"]
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow.alpha_composite(glow_blob((250, 300), (300, 150), t["mint"], g1))
    glow.alpha_composite(glow_blob((1260, 190), (330, 220), t["violet"], g2))
    img = Image.alpha_composite(img, glow)

    # --- dot matrix --------------------------------------------------------
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for y in range(14, H, 22):
        for x in range(14, W, 22):
            dd.ellipse([x, y, x + 1, y + 1], fill=t["dot"])
    img = Image.alpha_composite(img, dots)

    # --- contribution-grid motif, right side, fading left -----------------
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    CELL, GAP = 17, 5
    cols, rows = 26, 7
    gx0 = W - (cols * (CELL + GAP)) - 70
    gy0 = (H - rows * (CELL + GAP)) // 2
    seed = 1337  # deterministic, so the banner is reproducible
    for c in range(cols):
        for r in range(rows):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            lvl = (seed >> 16) % 100
            if lvl < 34:
                col, a = t["empty"], 200
            elif lvl < 60:
                col, a = t["mint"], 60
            elif lvl < 80:
                col, a = t["mint"], 130
            elif lvl < 93:
                col, a = t["mint"], 215
            else:
                col, a = t["violet"], 200
            x = gx0 + c * (CELL + GAP)
            y = gy0 + r * (CELL + GAP)
            gd.rounded_rectangle([x, y, x + CELL, y + CELL], radius=4, fill=col + (a,))
    grid.putalpha(Image.composite(grid.getchannel("A"), Image.new("L", (W, H), 0),
                                  hramp(gx0 - 250, gx0 + 210)))
    img = Image.alpha_composite(img, grid)

    d = ImageDraw.Draw(img)
    f_name, used_name = pick(HEAVY, 92)
    f_mono, used_mono = pick(MONO, 25)
    f_small, _ = pick(MONO, 19)

    X = 78
    tracked(d, (X, 118), NAME, f_name, t["ink"], track=3.5)

    # accent hairline
    d.rectangle([X + 2, 232, X + 120, 236], fill=t["mint"])
    d.rectangle([X + 130, 232, X + 160, 236], fill=t["violet"])

    tracked(d, (X, 262), ">", f_mono, t["mint"])
    tracked(d, (X + 26, 262), ROLE, f_mono, t["role"], track=0.6)
    tracked(d, (X + 2, 318), ORG, f_small, t["dim"], track=1.4)

    # corner ticks — small craft detail
    d.rectangle([0, 0, 5, 74], fill=t["mint"])
    d.rectangle([0, 0, 74, 5], fill=t["mint"])
    d.rectangle([W - 6, H - 75, W - 1, H - 1], fill=t["violet"])
    d.rectangle([W - 75, H - 6, W - 1, H - 1], fill=t["violet"])

    img.convert("RGB").save(path, optimize=True)
    return used_name, used_mono


def build_rule(path, h=12):
    """Thin mint->violet divider on transparency, so one file serves both themes."""
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    px = img.load()
    y0, y1 = h // 2 - 1, h // 2
    edge = 150  # fade-in / fade-out length
    for x in range(W):
        u = x / (W - 1)
        r = int(RULE_A[0] + (RULE_B[0] - RULE_A[0]) * u)
        g = int(RULE_A[1] + (RULE_B[1] - RULE_A[1]) * u)
        b = int(RULE_A[2] + (RULE_B[2] - RULE_A[2]) * u)
        a = int(190 * min(smoothstep(x / edge), smoothstep((W - 1 - x) / edge)))
        for y in (y0, y1):
            px[x, y] = (r, g, b, a)

    # three nodes so the rule reads as drawn rather than as a CSS border
    d = ImageDraw.Draw(img)
    for u in (0.2, 0.5, 0.8):
        x = int(u * (W - 1))
        r = int(RULE_A[0] + (RULE_B[0] - RULE_A[0]) * u)
        g = int(RULE_A[1] + (RULE_B[1] - RULE_A[1]) * u)
        b = int(RULE_A[2] + (RULE_B[2] - RULE_A[2]) * u)
        d.rectangle([x - 2, y0 - 2, x + 2, y1 + 2], fill=(r, g, b, 235))
    img.save(path, optimize=True)


os.makedirs("assets", exist_ok=True)
for path, theme in THEMES.items():
    n, m = build_header(path, theme)
    print(f"wrote {path}  {W}x{H}  {os.path.getsize(path):,} bytes")
build_rule("assets/rule.png")
print(f"wrote assets/rule.png  {W}x12  {os.path.getsize('assets/rule.png'):,} bytes")
print(f"  fonts: {n} / {m}")
