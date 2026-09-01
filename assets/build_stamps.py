"""Individual hanko skill stamps for the portfolio.

Same pressed-ink treatment as the GitHub profile stamps, emitted one file per
skill so each can be animated independently on hover.

    python3 build_stamps.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 4
S = lambda v: int(round(v * SS))
DIA = 150

FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
HIRA_GO = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"

VERMILLION = (196, 46, 38)
PAPER = (252, 249, 244)
GLOSS = (208, 84, 74)

# (slug, latin lines, japanese gloss) -- web first, then python/ML, then mobile
STAMPS = [
    ("javascript", ["JAVA", "SCRIPT"], "動"),
    ("typescript", ["TYPE", "SCRIPT"], "型"),
    ("nodejs", ["NODE", "JS"], "節"),
    ("express", ["EXPRESS"], "速"),
    ("htmlcss", ["HTML", "CSS"], "頁"),
    ("python", ["PYTHON"], "蛇"),
    ("django", ["DJANGO"], "枠"),
    ("flask", ["FLASK"], "瓶"),
    ("pytorch", ["PY", "TORCH"], "炬"),
    ("sklearn", ["SCIKIT", "LEARN"], "学"),
    ("numpy", ["NUM", "PY"], "数"),
    ("pandas", ["PANDAS"], "表"),
    ("flutter", ["FLUTTER"], "羽"),
    ("dart", ["DART"], "矢"),
]


def font(path, px, index=0):
    try:
        return ImageFont.truetype(path, px, index=index)
    except Exception:
        return ImageFont.truetype(path, px)


def ink_mask(size, seed):
    rng = np.random.default_rng(seed)
    n = size
    yy, xx = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    noise = rng.normal(0, 1, (n // 6, n // 6))
    noise = np.array(Image.fromarray(
        ((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)
    ).resize((n, n), Image.BICUBIC), dtype=float) / 255.0
    a = np.clip((0.985 - r) * 26, 0, 1)
    a *= np.clip(0.55 + 0.95 * noise, 0, 1)
    a[r > 0.93] *= np.clip(noise[r > 0.93] * 2.1, 0, 1)
    a[(noise < 0.10) & (r < 0.9)] *= 0.25
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L")


def stamp(lines, gloss, seed):
    d_px = S(DIA)
    canvas = int(d_px * 1.10)
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    o = (canvas - d_px) // 2
    dr.ellipse([o, o, o + d_px, o + d_px], fill=VERMILLION + (255,))
    ring = S(7)
    dr.ellipse([o + ring, o + ring, o + d_px - ring, o + d_px - ring],
               outline=PAPER + (255,), width=max(1, S(1.6)))

    fg = font(HIRA_GO, S(66))
    gw = dr.textlength(gloss, font=fg)
    bb = fg.getbbox(gloss)
    dr.text((canvas / 2 - gw / 2, canvas / 2 - (bb[3] + bb[1]) / 2),
            gloss, font=fg, fill=GLOSS + (255,))

    limit = d_px * 0.66
    size = S(30)
    while size > S(9):
        f = font(FUTURA, size, index=0)
        if max(dr.textlength(l, font=f) for l in lines) <= limit:
            break
        size -= S(0.7)
    f = font(FUTURA, size, index=0)
    lh = size * 1.06
    y = canvas / 2 - (lh * len(lines)) / 2 - S(1)
    for line in lines:
        w = dr.textlength(line, font=f)
        dr.text((canvas / 2 - w / 2, y), line, font=f, fill=PAPER + (255,))
        y += lh

    alpha = img.getchannel("A")
    mask = ink_mask(canvas, seed)
    img.putalpha(Image.fromarray(
        (np.array(alpha, float) * np.array(mask, float) / 255).astype(np.uint8), "L"))
    return img


out_dir = "stamps"
os.makedirs(out_dir, exist_ok=True)
total = 0
for i, (slug, lines, gloss) in enumerate(STAMPS):
    st = stamp(lines, gloss, seed=211 + i * 13).resize((DIA, DIA), Image.LANCZOS)
    st = st.quantize(colors=48, method=Image.FASTOCTREE)
    p = f"{out_dir}/{slug}.png"
    st.save(p, optimize=True)
    total += os.path.getsize(p)
print(f"{len(STAMPS)} stamps, {total/1024:.0f}KB total")
