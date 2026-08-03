# -*- coding: utf-8 -*-
"""Generate extension icons: a gesture stroke (down-then-right) with an arrow.

Drawn once at 512 and downsampled, so the small sizes stay clean.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "icons"
OUT.mkdir(parents=True, exist_ok=True)

S = 512
BLUE = (47, 129, 247, 255)
WHITE = (255, 255, 255, 255)

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# rounded square background
d.rounded_rectangle([0, 0, S - 1, S - 1], radius=112, fill=BLUE)

# the stroke: down, then right
w = 46
pts = [(160, 118), (160, 330), (330, 330)]
d.line(pts, fill=WHITE, width=w, joint="curve")

# round the free end of the vertical segment
r = w // 2
d.ellipse([160 - r, 118 - r, 160 + r, 118 + r], fill=WHITE)

# arrow head pointing right
tip_x, y = 410, 330
h = 62
d.polygon([(tip_x, y), (tip_x - 84, y - h), (tip_x - 84, y + h)], fill=WHITE)

for size in (16, 32, 48, 128):
    img.resize((size, size), Image.LANCZOS).save(OUT / f"icon{size}.png")
    print(f"icon{size}.png")

# a 512 master for the store listing
img.save(OUT / "icon512.png")
print("icon512.png")
