"""Compose glassfire_avatar.png into a 1592x848 CK3 event-scene DDS.

Backdrop: blurred/darkened crop of the art filling the wide canvas.
Foreground: the square avatar at full height on the left (narrator spot).
"""
from PIL import Image, ImageFilter, ImageEnhance
import os

SRC = r"Z:\ck3_mod_rewrite\glassfire_avatar.png"
OUT_DIR = r"Z:\ck3_mod_rewrite\XenoAmess_s_Eternal_Recurrence\gfx\interface\illustrations\event_scenes"
OUT = os.path.join(OUT_DIR, "xar_glassfire_avatar.dds")
W, H = 1592, 848

img = Image.open(SRC).convert("RGB")

# blurred wide backdrop (cover-crop then blur + darken)
scale = max(W / img.width, H / img.height)
bg = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
left = (bg.width - W) // 2
top = (bg.height - H) // 2
bg = bg.crop((left, top, left + W, top + H))
bg = bg.filter(ImageFilter.GaussianBlur(12))
bg = ImageEnhance.Brightness(bg).enhance(0.45)

# sharp avatar on the RIGHT (character_event window: text column sits left,
# the right half is the "portrait" area), full height
fg = img.resize((H, H), Image.LANCZOS)
canvas = bg.copy()
canvas.paste(fg, (W - H, 0))

# darken the left text column a bit more for readability
dim = Image.new("RGB", (W - H, H), (0, 0, 0))
mask = Image.new("L", (W - H, H), 90)
canvas.paste(dim, (0, 0), mask)

os.makedirs(OUT_DIR, exist_ok=True)
canvas.save(OUT, pixel_format="DXT1")
print("wrote", OUT, os.path.getsize(OUT), "bytes")

# verify DDS header
with open(OUT, "rb") as f:
    head = f.read(128)
print("magic:", head[:4], "fourCC:", head[84:88], "h:", int.from_bytes(head[12:16], "little"), "w:", int.from_bytes(head[16:20], "little"))
