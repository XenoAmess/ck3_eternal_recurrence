"""Render code-native overlays for the approved player trailer.

Source photographs and screenshots are never rewritten. These transparent
layers are applied by the video editor. A new work directory is required for
each attempt; source, text bounds, previews and all generated files are kept.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont


W, H = 1920, 1080
SUBTITLE_TOP = 860
GOLD = (229, 193, 123, 255)
CREAM = (245, 238, 221, 255)
MUTED = (191, 181, 166, 255)
RUBY = (176, 58, 69, 255)
URL = "https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990"
DEFAULT_WORK = Path("C:/ck3-superman-qiang-promo-20261004/player-visuals-A0004")
DEFAULT_FONT = Path("C:/Windows/Fonts/msyh.ttc")
DEFAULT_BOLD_FONT = Path("C:/Windows/Fonts/msyhbd.ttc")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


class Designer:
    def __init__(self, work: Path, font: Path, bold_font: Path) -> None:
        self.work = work
        self.font_path = font
        self.bold_path = bold_font
        self.bounds: list[dict] = []
        self.fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}
        self.scene = ""

    def font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(self.bold_path if bold else self.font_path), size)
        return self.fonts[key]

    def canvas(self, *, scrim: bool = True) -> Image.Image:
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if scrim:
            horizontal = Image.new("L", (1170, 1))
            horizontal.putdata([round(226 * max(0, 1 - (x / 1170) ** 2.1)) for x in range(1170)])
            vertical = Image.new("L", (1, SUBTITLE_TOP))
            vertical.putdata([255 if y < 740 else round(255 * max(0, 1 - (y - 740) / 120))
                              for y in range(SUBTITLE_TOP)])
            alpha = ImageChops.multiply(horizontal.resize((1170, SUBTITLE_TOP)),
                                        vertical.resize((1170, SUBTITLE_TOP)))
            shade = Image.new("RGBA", (1170, SUBTITLE_TOP), (15, 9, 13, 0))
            shade.putalpha(alpha)
            canvas.alpha_composite(shade)
        return canvas

    def text(self, canvas: Image.Image, text: str, x: int, y: int, size: int,
             *, bold: bool = False, color: tuple = CREAM, max_right: int = 1808,
             center_x: int | None = None) -> None:
        font = self.font(size, bold)
        draw = ImageDraw.Draw(canvas)
        box = draw.textbbox((0, 0), text, font=font)
        if center_x is not None:
            x = round(center_x - (box[2] - box[0]) / 2)
        # Align the visible top, rather than the font's internal ascent offset.
        draw_y = y - box[1]
        final_box = draw.textbbox((x, draw_y), text, font=font)
        if final_box[0] < 80 or final_box[2] > max_right or final_box[1] < 64 or final_box[3] >= SUBTITLE_TOP:
            raise ValueError(f"Unsafe text bounds in {self.scene}: {text!r} {final_box}, max-right={max_right}")
        draw.text((x, draw_y), text, font=font, fill=color)
        self.bounds.append({"scene": self.scene, "text": text, "font_size": size,
                            "bold": bold, "bounds": list(final_box), "maximum_right": max_right})

    def brand(self, canvas: Image.Image, label: str = "超人强") -> None:
        self.text(canvas, label, 112, 96, 25, color=GOLD)
        draw = ImageDraw.Draw(canvas)
        draw.line((112, 146, 172, 146), fill=GOLD, width=2)
        draw.line((184, 146, 350, 146), fill=(229, 193, 123, 65), width=1)

    def tag(self, canvas: Image.Image, text: str = "宣传插画 · 示意") -> None:
        # The owner explicitly removed on-screen source-category labels after
        # watching the first film. Source distinctions remain in provenance.
        return None

    def save(self, canvas: Image.Image, target: Path) -> None:
        if canvas.getbbox() is None:
            raise ValueError(f"Empty overlay: {target}")
        if canvas.getchannel("A").crop((0, SUBTITLE_TOP, W, H)).getbbox() is not None:
            raise ValueError(f"Subtitle region occupied: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target)


def crown(draw: ImageDraw.ImageDraw, x: int, y: int, width: int = 186, color: tuple = GOLD) -> None:
    height = round(width * .46)
    points = [(x, y + height * .25), (x + width * .17, y + height * .45),
              (x + width * .24, y), (x + width * .41, y + height * .44),
              (x + width * .5, y - height * .13), (x + width * .59, y + height * .44),
              (x + width * .76, y), (x + width * .83, y + height * .45),
              (x + width, y + height * .25), (x + width * .89, y + height),
              (x + width * .11, y + height), (x, y + height * .25)]
    draw.line(points, fill=color, width=4, joint="curve")
    draw.line((x + width * .12, y + height * 1.14, x + width * .88, y + height * 1.14), fill=color, width=3)
    radius = 5
    for cx, cy in [(x + width * .24, y), (x + width * .5, y - height * .13), (x + width * .76, y)]:
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)


def invitation(draw: ImageDraw.ImageDraw, cx: int, cy: int, width: int = 412) -> None:
    height = round(width * .60)
    left, top = cx - width / 2, cy - height / 2
    draw.rounded_rectangle((left + 12, top + 12, left + width + 12, top + height + 12), radius=8, fill=(0, 0, 0, 90))
    draw.rounded_rectangle((left, top, left + width, top + height), radius=7,
                           fill=(221, 204, 167, 250), outline=(244, 223, 177, 255), width=2)
    draw.line((left, top, cx, top + height * .61, left + width, top), fill=(158, 126, 80, 220), width=3)
    draw.line((left, top + height, cx - 34, top + height * .55), fill=(172, 143, 104, 160), width=2)
    draw.line((left + width, top + height, cx + 34, top + height * .55), fill=(172, 143, 104, 160), width=2)
    seal_y = top + height * .61
    draw.ellipse((cx - 35, seal_y - 34, cx + 35, seal_y + 34), fill=(132, 21, 36, 255), outline=(179, 48, 58, 255), width=3)
    draw.ellipse((cx - 27, seal_y - 26, cx + 27, seal_y + 26), outline=(215, 93, 86, 180), width=2)
    draw.line((cx - 11, seal_y + 12, cx + 1, seal_y - 11, cx + 13, seal_y + 12), fill=(222, 163, 131, 220), width=3)


def adult_bust(draw: ImageDraw.ImageDraw, cx: int, y: int, *, queen: bool = False) -> None:
    # Deliberately abstract adult courtier silhouettes; this is a graphic symbol,
    # never a portrait of a named game character or a recreation of a game panel.
    color = (232, 198, 137, 215) if not queen else (200, 120, 122, 215)
    if queen:
        draw.ellipse((cx - 72, y + 18, cx + 72, y + 183), fill=(74, 29, 43, 235), outline=color, width=3)
    draw.ellipse((cx - 53, y + 25, cx + 53, y + 157), fill=(23, 16, 22, 240), outline=color, width=3)
    draw.polygon([(cx - 18, y + 158), (cx - 18, y + 190), (cx - 121, y + 223),
                  (cx - 155, y + 310), (cx + 155, y + 310), (cx + 121, y + 223),
                  (cx + 18, y + 190), (cx + 18, y + 158)], fill=(25, 17, 25, 235))
    draw.line([(cx - 18, y + 171), (cx - 18, y + 190), (cx - 121, y + 223),
               (cx - 155, y + 310)], fill=color, width=3, joint="curve")
    draw.line([(cx + 18, y + 171), (cx + 18, y + 190), (cx + 121, y + 223),
               (cx + 155, y + 310)], fill=color, width=3, joint="curve")
    crown(draw, cx - 55, y + 5, width=110, color=color)


def power_flow(*, reverse: bool = False) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    start, end = (1085, 1515) if reverse else (1515, 1085)
    xs = list(range(min(start, end), max(start, end) + 1, 5))
    import math
    points = [(x, 520 + 26 * math.sin((x - 1085) / 430 * math.pi)) for x in xs]
    draw.line(points, fill=(229, 193, 123, 20), width=18, joint="curve")
    draw.line(points, fill=(229, 193, 123, 65), width=8, joint="curve")
    draw.line(points, fill=(246, 214, 151, 230), width=2, joint="curve")
    tip = end
    direction = 1 if reverse else -1
    draw.ellipse((tip - 4, 516, tip + 4, 524), fill=(250, 224, 175, 200))
    for x in [1160, 1270, 1380, 1470]:
        y = 520 + 26 * math.sin((x - 1085) / 430 * math.pi)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(250, 224, 175, 240))
    return canvas


def base_field() -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (16, 9, 16, 255))
    pixels = canvas.load()
    for y in range(H):
        for x in range(W):
            glow = max(0.0, 1 - ((x - 1350) / 1150) ** 2 - ((y - 450) / 780) ** 2)
            grain = ((x * 17 + y * 29 + (x * y) % 31) % 7) - 3
            pixels[x, y] = (int(16 + glow * 21 + grain), int(9 + glow * 5 + grain / 2),
                            int(16 + glow * 9 + grain / 2), 255)
    return canvas.convert("RGB")


def make_scene_overlays(designer: Designer) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for index in range(1, 11):
        scene = f"SQP-{index:02d}"
        designer.scene = scene
        canvas = designer.canvas(scrim=index not in [6, 7, 9])
        designer.brand(canvas)
        draw = ImageDraw.Draw(canvas)
        if index == 1:
            designer.tag(canvas)
            designer.text(canvas, "想变强？", 112, 286, 100, bold=True, max_right=800)
            designer.text(canvas, "先赴个约。", 112, 456, 78, bold=True, color=GOLD, max_right=800)
        elif index == 2:
            designer.tag(canvas)
            designer.text(canvas, "超人强", 104, 264, 128, bold=True, color=GOLD, max_right=780)
            designer.text(canvas, "越超人越强", 112, 437, 59, bold=True, max_right=780)
            designer.text(canvas, "艳遇，也能成为力量争夺。", 112, 578, 31, color=MUTED, max_right=870)
        elif index == 3:
            designer.tag(canvas, "宣传示意")
            designer.text(canvas, "让对方的本事，", 112, 290, 67, bold=True, max_right=870)
            designer.text(canvas, "成为你的筹码。", 112, 393, 67, bold=True, color=GOLD, max_right=870)
        elif index == 4:
            designer.tag(canvas)
            designer.text(canvas, "爱情与野心，", 112, 383, 75, bold=True, max_right=910)
            designer.text(canvas, "这次一起赴约。", 112, 494, 75, bold=True, color=GOLD, max_right=910)
        elif index == 5:
            designer.tag(canvas)
            designer.text(canvas, "对面，", 112, 266, 83, bold=True, max_right=830)
            designer.text(canvas, "更老练呢？", 112, 386, 83, bold=True, max_right=830)
            designer.text(canvas, "谁才是猎物？", 112, 570, 57, bold=True, color=RUBY, max_right=830)
        elif index == 6:
            designer.text(canvas, "赴约前，", 112, 286, 53, bold=True, max_right=444)
            designer.text(canvas, "先看履历。", 112, 372, 53, bold=True, color=GOLD, max_right=444)
            designer.text(canvas, "看起来无害的人，", 112, 520, 25, color=MUTED, max_right=440)
            designer.text(canvas, "也可能藏得很深。", 112, 564, 25, color=MUTED, max_right=440)
        elif index == 7:
            designer.text(canvas, "每个人，", 112, 247, 52, bold=True, max_right=475)
            designer.text(canvas, "都有自己的", 112, 325, 52, bold=True, max_right=475)
            designer.text(canvas, "履历。", 112, 403, 52, bold=True, color=GOLD, max_right=475)
            designer.text(canvas, "你的宫廷，", 112, 559, 27, color=MUTED, max_right=475)
            designer.text(canvas, "多一种养成。", 112, 606, 27, color=MUTED, max_right=475)
        elif index == 8:
            designer.tag(canvas, "宣传示意")
            designer.text(canvas, "下一次，", 112, 330, 83, bold=True, max_right=890)
            designer.text(canvas, "会带来什么？", 112, 458, 83, bold=True, color=GOLD, max_right=890)
            invitation(draw, 1360, 637, width=390)
        elif index == 9:
            designer.text(canvas, "老存档，", 112, 303, 67, bold=True, max_right=700)
            designer.text(canvas, "也能接着玩。", 112, 409, 67, bold=True, color=GOLD, max_right=700)
            designer.text(canvas, "带回你熟悉的宫廷。", 112, 564, 31, color=MUTED, max_right=700)
        else:
            designer.tag(canvas)
            designer.text(canvas, "超人强", 104, 246, 139, bold=True, color=GOLD, max_right=950)
            designer.text(canvas, "越超人越强", 112, 425, 59, bold=True, max_right=950)
            designer.text(canvas, "创意工坊搜索「超人强」", 112, 568, 40, bold=True, max_right=1040)
            designer.text(canvas, "猎手，还是猎物？", 112, 724, 36, color=MUTED, max_right=1040)
        path = designer.work / "overlays" / f"{scene}.png"
        designer.save(canvas, path)
        paths[scene] = path
    return paths


def make_extras(designer: Designer) -> dict[str, Path]:
    extras: dict[str, Path] = {}
    for word in ["外交", "军事", "管理", "谋略", "学识", "勇武", "健康"]:
        designer.scene = f"attribute-{word}"
        canvas = designer.canvas(scrim=False)
        designer.text(canvas, word, 0, 300, 97, bold=True, color=GOLD, center_x=1360)
        ImageDraw.Draw(canvas).line((1260, 431, 1460, 431), fill=(229, 193, 123, 120), width=2)
        path = designer.work / "overlays" / f"attribute-{word}.png"
        designer.save(canvas, path)
        extras[word] = path
    for word in ["外交", "勇武"]:
        designer.scene = f"SQP-03-attribute-{word}"
        canvas = designer.canvas(scrim=False)
        designer.text(canvas, word, 112, 586, 64, bold=True, color=GOLD, max_right=870)
        path = designer.work / "overlays" / f"attribute-{word}-left.png"
        designer.save(canvas, path)
        extras[f"SQP-03-{word}"] = path
    for name, reverse in [("power-to-king", False), ("power-to-queen", True)]:
        path = designer.work / "overlays" / f"{name}.png"
        designer.save(power_flow(reverse=reverse), path)
        extras[name] = path
    # Use separately timed words to keep the first joke and mid-film reversal.
    for name, lines in [
        ("SQP-01-hook", [("想变强？", 286, 100, CREAM)]),
        ("SQP-01-punchline", [("想变强？", 286, 100, CREAM), ("先赴个约。", 456, 78, GOLD)]),
        ("SQP-05-question", [("对面，", 266, 83, CREAM), ("更老练呢？", 386, 83, CREAM)]),
    ]:
        designer.scene = name
        canvas = designer.canvas()
        designer.brand(canvas)
        designer.tag(canvas)
        for word, y, size, color in lines:
            designer.text(canvas, word, 112, y, size, bold=True, color=color, max_right=830)
        path = designer.work / "overlays" / f"{name}.png"
        designer.save(canvas, path)
        extras[name] = path
    designer.scene = "workshop-qr"
    try:
        import qrcode
    except ImportError:
        return extras
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=4)
    qr.add_data(URL)
    qr.make(fit=True)
    native_qr = qr.make_image(fill_color="#201015", back_color="#fff9eb").convert("RGBA")
    native_path = designer.work / "overlays" / "workshop-qr-native.png"
    native_qr.save(native_path)
    canvas = designer.canvas(scrim=False)
    qr_size = (qr.modules_count + 2 * qr.border) * 7
    qr_image = native_qr.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qr_x = 1608 - qr_size // 2
    canvas.alpha_composite(qr_image, (qr_x, 366))
    designer.text(canvas, "立即赴约", 0, 739, 29, bold=True, color=GOLD, center_x=1608)
    path = designer.work / "overlays" / "workshop-qr.png"
    designer.save(canvas, path)
    extras["workshop-qr"] = path
    extras["workshop-qr-native"] = native_path
    save_json(designer.work / "qr-source.json", {"url": URL, "matrix_modules": qr.modules_count,
              "border_modules": qr.border, "native_size": list(native_qr.size),
              "qrcode_version": importlib.metadata.version("qrcode"),
              "display_rect": [qr_x, 366, qr_size, qr_size],
              "render": "Nearest-neighbour; native QR data is preserved without a source URL substitution."})
    return extras


def fit_image(source: Image.Image, rectangle: list[int]) -> tuple[Image.Image, tuple[int, int]]:
    x, y, width, height = rectangle
    factor = min(width / source.width, height / source.height)
    image = source.resize((round(source.width * factor), round(source.height * factor)), Image.Resampling.LANCZOS)
    return image, (x + (width - image.width) // 2, y + (height - image.height) // 2)


def render_contact_sheet(plan: dict, root: Path, designer: Designer) -> Path:
    previews: list[Image.Image] = []
    for scene in plan["scenes"]:
        designer.scene = "preview"
        background = Image.open(scene["background_path"]).convert("RGBA") if scene.get("background_path") else Image.new("RGBA", (W, H), (18, 11, 17, 255))
        if scene.get("background_source"):
            photo = Image.open(root / scene["background_source"]).convert("RGBA")
            if scene.get("source_crop"):
                photo = photo.crop(tuple(scene["source_crop"]))
            photo, position = fit_image(photo, scene["fit_rect"])
            background.alpha_composite(photo, position)
        background.alpha_composite(Image.open(scene["overlay_path"]).convert("RGBA"))
        for extra in scene.get("preview_extra_paths", []):
            background.alpha_composite(Image.open(extra).convert("RGBA"))
        # This is a preview guide only. The final compositor owns real subtitles.
        draw = ImageDraw.Draw(background)
        draw.rectangle((80, 872, 1840, 996), fill=(0, 0, 0, 130))
        font = designer.font(35)
        caption = "字幕安全区：预览占位，不进入成片"
        box = draw.textbbox((0, 0), caption, font=font)
        draw.text(((W - (box[2] - box[0])) / 2, 912 - box[1]), caption, font=font, fill=(183, 173, 163, 255))
        target = designer.work / "previews" / f"{scene['scene_id']}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        background.convert("RGB").save(target, quality=93)
        previews.append(background.convert("RGB").resize((640, 360), Image.Resampling.LANCZOS))
    sheet = Image.new("RGB", (1280, 1980), (18, 11, 17))
    draw = ImageDraw.Draw(sheet)
    font = designer.font(21)
    for index, preview in enumerate(previews):
        x, y = (index % 2) * 640, (index // 2) * 396
        sheet.paste(preview, (x, y + 36))
        draw.text((x + 16, y + 5), f"SQP-{index + 1:02d}", font=font, fill=(229, 193, 123))
    path = designer.work / "contact-sheet.jpg"
    sheet.save(path, quality=95)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--bold-font", type=Path, default=DEFAULT_BOLD_FONT)
    parser.add_argument("--illustration-directory", type=Path,
                        default=Path("promo/superman_qiang/images/revision-20261004"))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--report-directory", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    work = args.work_dir.resolve()
    if (work / "overlays").exists() or (work / "visual-plan.json").exists() or args.plan.exists() or args.report_directory.exists():
        raise FileExistsError("Use a fresh visual attempt, plan path and report directory; earlier outputs are retained.")
    for font in [args.font, args.bold_font]:
        if not font.is_file():
            raise FileNotFoundError(f"Required font is absent: {font}")
    work.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(__file__, work / "compose_player_visuals.py")
    director = root / "promo/superman_qiang/02m/director.json"
    shutil.copyfile(director, work / "director.json")
    designer = Designer(work, args.font, args.bold_font)
    overlays = make_scene_overlays(designer)
    extras = make_extras(designer)
    field = work / "backgrounds" / "court-field.png"
    field.parent.mkdir(parents=True)
    base_field().save(field)
    art = "mod_superman_qiang/thumbnail.png"
    art_wide = "workshop/superman_qiang_media/v3/01_absorption.jpg"
    event = "workshop/superman_qiang_media/v2/04_natural_event.jpg"
    toast = "workshop/superman_qiang_media/v3/05_notification.jpg"
    context = "workshop/superman_qiang_media/v3/05_notification.raw.png"
    illustration_directory = args.illustration_directory.resolve()
    revision_sources = [(illustration_directory / name).relative_to(root).as_posix() for name in [
        "01-royal-study.png", "02-palace-ball.png", "03-knight-yard.png",
        "04-candle-invitation.png", "05-queen-reversal.png"]]
    for source in revision_sources:
        if not (root / source).is_file():
            raise FileNotFoundError(f"The independent illustration is absent: {source}")
    selections = [
        (revision_sources[0], None, [0, 0, W, H], "art"),
        (revision_sources[1], None, [0, 0, W, H], "art"),
        (revision_sources[2], None, [0, 0, W, H], "art"),
        (revision_sources[3], None, [0, 0, W, H], "art"),
        (revision_sources[4], None, [0, 0, W, H], "art"),
        (toast, None, [460, 195, 1350, 626], "genuine-screenshot"),
        (event, None, [560, 165, 1210, 673], "genuine-screenshot"),
        (None, None, None, "schematic"),
        (context, None, [745, 110, 940, 705], "genuine-screenshot"),
        (art, [0, 0, 640, 360], [0, 0, W, H], "art"),
    ]
    scenes = []
    for index, (source, crop, fit, source_kind) in enumerate(selections, start=1):
        scene_id = f"SQP-{index:02d}"
        row = {"scene_id": scene_id, "overlay_path": str(overlays[scene_id]),
               "background_path": str(field), "background_source": source,
               "source_crop": crop, "fit_rect": fit, "source_kind": source_kind,
               "background": {"source_path": str(root / source) if source else str(field),
                              "crop": [crop[0], crop[1], crop[2] - crop[0], crop[3] - crop[1]] if crop else None,
                              "fit": fit or [0, 0, W, H],
                              "mode": "art" if source_kind == "art" else "real-still" if source_kind == "genuine-screenshot" else "graphic",
                              "canvas_path": str(field)},
               "preserve_aspect_ratio": True, "subtitle_safe_top": SUBTITLE_TOP,
               "pan": "Slow 2–4% scale within the ordinary illustration crop; screenshots remain still and complete."
                       if source_kind == "art" else "No screenshot motion, stretched dimensions or fake clicks.",
               "preview_extra_paths": [], "optional_layers": []}
        if index == 1:
            row["optional_layers"] = [{"path": str(extras["SQP-01-hook"]), "replace_base": True,
                                       "timing_fraction": [0.0, 0.76],
                                       "timing": "Before the final '赴个约' punchline."},
                                      {"path": str(extras["SQP-01-punchline"]), "replace_base": True,
                                       "timing_fraction": [0.76, 1.0],
                                       "timing": "Reveal with the final phrase and hold."}]
        elif index == 2:
            row["alternate_genuine_source"] = {"path": event, "fit_rect": [700, 170, 1100, 611],
                "note": "Use an independent labelled still, not as absorption proof; remove large title overlay during this cut."}
        elif index == 3:
            row["optional_layers"] = [{"path": str(extras["SQP-03-外交"]), "word": "外交", "timing_fraction": [0.45, 0.70], "timing": "On '谈判的底气'; one attribute word only, left of the knight's face."},
                                      {"path": str(extras["SQP-03-勇武"]), "word": "勇武", "timing_fraction": [0.72, 1.0], "timing": "On '亲自下场的勇气'; replaces the previous word."}]
            row["preview_extra_paths"] = [str(extras["SQP-03-勇武"])]
        elif index == 5:
            row["optional_layers"] = [{"path": str(extras["SQP-05-question"]), "replace_base": True,
                                       "timing_fraction": [0.0, 0.70],
                                       "timing": "Before final '谁才是猎物' reveal."},
                                     ]
            row["pan"] = "Keep the complete queen image at scale 1.0; no additional crop or zoom may cut the crown near the top edge."
            row["motion_policy"] = {"fixed_scale": 1.0, "preserve_crown": True}
        elif index == 6:
            row["alternate_genuine_source"] = {"path": context, "fit_rect": [745, 110, 940, 705],
                "note": "Establish genuine original context briefly, then cut to the complete cropped notification image; no simulated action."}
            row["genuine_claim_limit"] = "Normal query from an actual adult NPC; net health is zero, so this is not a health-transfer example."
        elif index == 7:
            row["alternate_genuine_source"] = {"path": toast, "fit_rect": [560, 225, 1210, 561],
                "note": "Use a separately labelled normal query still; these are independent captures, not a claimed same-event transfer."}
            row["genuine_claim_limit"] = "The natural event was a tie. It establishes the event atmosphere and recording, not absorption."
        elif index == 8:
            row["optional_layers"] = [{"path": str(extras[word]), "timing_fraction": [i / 7 * .55, (i + 1) / 7 * .55],
                                       "timing": f"With spoken '{word}'; show one category at a time. Prefer actual first-sentence boundaries to this guide."}
                                      for i, word in enumerate(["外交", "军事", "管理", "谋略", "学识", "勇武", "健康"])]
            row["preview_extra_paths"] = [str(extras["健康"])]
        elif index == 10 and "workshop-qr" in extras:
            row["optional_layers"] = [{"path": str(extras["workshop-qr"]), "timing_fraction": [0.0, 1.0], "timing": "Final stable end card; hold through the voice tail and music resolve."}]
            row["preview_extra_paths"] = [str(extras["workshop-qr"])]
        scenes.append(row)
    plan = {"format_version": 1, "kind": "superman_qiang_player_visual_plan",
            "created_at": datetime.now(timezone.utc).isoformat(), "source_director": str(director),
            "source_director_sha256": digest(director), "resolution": [W, H],
            "style": "Ruby, near-black and warm gold; one font family, short text, substantial negative space.",
            "source_policy": "Five independent generated fictional illustrations replace repeated portraits. Source distinctions remain in provenance; the owner explicitly removed on-screen category labels. Screenshot pixels, readings, aspect ratios and provenance remain unchanged. No test fixtures or recreated UI.",
            "category_labels_visible": False,
            "first_five_independent_source_count": len(set(revision_sources)),
            "work_directory": str(work), "subtitle_region": [80, SUBTITLE_TOP, 1760, 180],
            "workshop_url": URL, "fonts": [{"path": str(path), "sha256": digest(path)} for path in [args.font, args.bold_font]],
            "scenes": scenes,
            "extras": {name: str(path) for name, path in extras.items()}}
    save_json(args.plan, plan)
    save_json(work / "visual-plan.json", plan)
    contact_sheet = render_contact_sheet(plan, root, designer)
    save_json(work / "text-bounds.json", designer.bounds)
    validation = {"status": "GREEN", "scope": "Static graphics preparation, not finished-video review or human approval.",
                  "checked_at": datetime.now(timezone.utc).isoformat(), "resolution": [W, H],
                  "overlay_count": len(overlays), "extra_count": len(extras),
                  "font_bounds_checked": len(designer.bounds), "subtitle_clear_top": SUBTITLE_TOP,
                  "python": sys.version, "python_executable": sys.executable,
                  "pillow_version": importlib.metadata.version("Pillow"),
                  "contact_sheet": str(contact_sheet), "contact_sheet_sha256": digest(contact_sheet),
                  "plan_sha256": digest(args.plan),
                  "sources": [{"path": source, "sha256": digest(root / source)} for source in [art, art_wide, event, toast, context, *revision_sources]],
                  "generated_files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
                                      for path in sorted(work.rglob("*")) if path.is_file()]}
    args.report_directory.mkdir(parents=True)
    save_json(args.report_directory / "visual-preparation.json", validation)
    (args.report_directory / "README.md").write_text(
        "# 超人强玩家宣传片视觉准备\n\n"
        "10 个透明 1920×1080 场景层已生成，另有七个属性短词、正反权力光流、开场分段字卡及工坊二维码。"
        "所有文字测量边界，y≥860 的底部字幕区保持透明。\n\n"
        f"[布局计划](../../visual-plan.json)；[生成文件及 SHA-256](visual-preparation.json)。"
        f"原始过程目录 `{work.as_posix()}`；contact sheet 为 `{contact_sheet.as_posix()}`。\n\n"
        "原始艺术图和正常游戏截图没有被改写；实机静帧分别注明，不把平手事件当吸取证据，"
        "不把通知中的零净健康当健康转移证据。预览中底部灰字仅标记字幕安全区，不用于成片。\n\n"
        "本结果只验证静态视觉资产和字框，不代表成片人工审阅或批准。\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": "GREEN", "overlays": len(overlays), "extras": len(extras),
                      "plan": str(args.plan), "contact_sheet": str(contact_sheet)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
