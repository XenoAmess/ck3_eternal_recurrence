"""Compose glassfire_avatar.png into a 1592x848 CK3 event-scene DDS.

Backdrop: lightly blurred cover-crop of the art filling the wide canvas.
Foreground: the square avatar at full height on the right (portrait area).
Left text column: smooth gradient darkening (dark at left edge -> clear at
the avatar), so text stays readable without a dead black void.
"""
from PIL import Image, ImageFilter, ImageEnhance
import os

SRC = r"Z:\ck3_mod_rewrite\glassfire_avatar.png"
OUT_DIR = r"Z:\ck3_mod_rewrite\XenoAmess_s_Eternal_Recurrence\gfx\interface\illustrations\event_scenes"
OUT = os.path.join(OUT_DIR, "xar_glassfire_avatar.dds")
W, H = 1592, 848

img = Image.open(SRC).convert("RGB")

# lightly blurred wide backdrop (cover-crop), keep most brightness
scale = max(W / img.width, H / img.height)
bg = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
left = (bg.width - W) // 2
top = (bg.height - H) // 2
bg = bg.crop((left, top, left + W, top + H))
bg = bg.filter(ImageFilter.GaussianBlur(5))
bg = ImageEnhance.Brightness(bg).enhance(0.8)

# smooth horizontal gradient darkening over the text column (left -> avatar edge)
grad = Image.linear_gradient("L").resize((W - H, 1)).rotate(90, expand=True).resize((W - H, H))
# linear_gradient gives 0 at top -> 255 at bottom; after rotate: 0 left -> 255 right
# remap to: 150 (dark) at left edge -> 0 (clear) where the avatar starts
grad = grad.point(lambda v: max(0, 150 - round(v * 150 / 255)))
canvas = bg.copy()
canvas.paste(Image.new("RGB", (W - H, H), (0, 0, 0)), (0, 0), grad)

# sharp avatar on the RIGHT, full height
fg = img.resize((H, H), Image.LANCZOS)
canvas.paste(fg, (W - H, 0))

os.makedirs(OUT_DIR, exist_ok=True)
canvas.save(OUT, pixel_format="DXT1")
print("wrote", OUT, os.path.getsize(OUT), "bytes")

# verify DDS header
with open(OUT, "rb") as f:
    head = f.read(128)
print("magic:", head[:4], "fourCC:", head[84:88], "h:", int.from_bytes(head[12:16], "little"), "w:", int.from_bytes(head[16:20], "little"))
