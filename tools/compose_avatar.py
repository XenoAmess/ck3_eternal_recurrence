"""Compose glassfire_avatar_wide.png into a 1592x848 CK3 event-scene DDS.

Source is already composed wide (character right, dark ambience left):
cover-crop to 1592x848, apply a mild gradient darkening on the left text
column, save as DXT1.

(For the old square glassfire_avatar.png, see git history: it needed a
blurred backdrop + sharp right-side paste.)
"""
from PIL import Image
import os

SRC = r"Z:\ck3_mod_rewrite\glassfire_avatar_wide.png"
OUT_DIR = r"Z:\ck3_mod_rewrite\XenoAmess_s_Eternal_Recurrence\gfx\interface\illustrations\event_scenes"
OUT = os.path.join(OUT_DIR, "xar_glassfire_avatar.dds")
W, H = 1592, 848

img = Image.open(SRC).convert("RGB")

# cover-crop to exactly 1592x848
scale = max(W / img.width, H / img.height)
img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
left = (img.width - W) // 2
top = (img.height - H) // 2
canvas = img.crop((left, top, left + W, top + H))

# mild gradient darkening over the left text column (text readability)
text_w = round(W * 0.55)
grad = Image.linear_gradient("L").resize((text_w, 1)).rotate(90, expand=True).resize((text_w, H))
grad = grad.point(lambda v: max(0, 70 - round(v * 70 / 255)))
canvas.paste(Image.new("RGB", (text_w, H), (0, 0, 0)), (0, 0), grad)

os.makedirs(OUT_DIR, exist_ok=True)
canvas.save(OUT, pixel_format="DXT1")
print("wrote", OUT, os.path.getsize(OUT), "bytes")

with open(OUT, "rb") as f:
    head = f.read(128)
print("magic:", head[:4], "fourCC:", head[84:88], "h:", int.from_bytes(head[12:16], "little"), "w:", int.from_bytes(head[16:20], "little"))
