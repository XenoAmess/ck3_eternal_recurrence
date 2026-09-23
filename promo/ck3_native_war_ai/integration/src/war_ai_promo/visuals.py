"""The film's illustrated map, candidate cards, thresholds and peace ledgers."""
from pathlib import Path
import math
import random

from PIL import Image, ImageDraw
from xar_promo.process import CommandSpec, run_command

from .common import font, lines

BG = "#211813"
PANEL = "#35291F"
INK = "#F0E5CF"
MUTED = "#BBA98D"
GOLD = "#CBA56A"
RED = "#CA7962"
BLUE = "#9AAEAB"  # Muted opposing-faction accent, not a blue dashboard field.
GREEN = "#ABB582"
PAPER = "#D9C39B"
PAPER_INK = "#3E2C20"
FAINT_RULE = "#61503C"

# Older teaching/help layouts share these drawing helpers. Translate their
# panel fills at the visual boundary without editing frozen mechanism copy.
PANEL_FILLS = {
    "#152635":"#2A241C", "#263540":"#453724", "#1B2E3D":"#342C22",
    "#1C303C":"#30281F", "#1B303C":"#382B20", "#263B46":"#443522",
    "#27323B":"#3C2C21", "#26313A":"#3D2E23", "#223341":"#3A2A1E",
    "#32404B":"#423C31", "#244B42":"#394331", "#26343F":"#362D24",
}


def heraldic_mark(draw, xy, size=32, color=GOLD, fill=None):
    """Original geometric shield, not a CK3 coat-of-arms asset."""
    x, y = xy
    points = [(x-size*.48,y-size*.5),(x+size*.48,y-size*.5),
              (x+size*.43,y+size*.12),(x,y+size*.58),(x-size*.43,y+size*.12)]
    draw.polygon(points, fill=fill or PANEL, outline=color, width=2)
    draw.line((x,y-size*.31,x,y+size*.25),fill=color,width=2)
    draw.line((x-size*.22,y-size*.07,x+size*.22,y-size*.07),fill=color,width=2)


def make_canvas(size=(2560, 1440)):
    """A quiet, deterministic paper/wood field; subtitle area stays untextured."""
    image = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(image)
    rng = random.Random(119006)
    for _ in range(6500):
        x, y = rng.randrange(size[0]), rng.randrange(min(1118,size[1]))
        draw.point((x,y),fill=(40+rng.randrange(6),30+rng.randrange(4),23+rng.randrange(3)))
    draw.line((64,30,size[0]-64,30),fill=FAINT_RULE,width=1)
    for x, sign in ((64,1),(size[0]-64,-1)):
        draw.line((x,30,x+sign*110,30),fill=GOLD,width=2)
        draw.line((x,30,x,110),fill=FAINT_RULE,width=1)
    return image


def text(draw, xy, value, size=44, fill=INK, bold=False, width=None):
    wrapped = lines(value, size, width, bold) if width else [value]
    for i, line in enumerate(wrapped):
        draw.text((xy[0], xy[1] + i * size * 1.35), line, font=font(size, bold), fill=fill)


def box(draw, bounds, color=PANEL, outline=None):
    color = PANEL_FILLS.get(color,color)
    outline = FAINT_RULE if outline == "#3A4C59" else outline
    x,y,right,bottom = bounds
    # Narrow, square framing reads as a folio or map note, not a dashboard tile.
    draw.rounded_rectangle(bounds, radius=4, fill=color, outline=outline, width=2)
    if outline and right-x>150 and bottom-y>90:
        draw.line((x+12,y+8,right-12,y+8),fill=outline,width=1)
        for cx, direction in ((x+8,1),(right-8,-1)):
            draw.line((cx,bottom-8,cx+direction*12,bottom-8),fill=outline,width=1)


def arrow(draw, a, b, color=GOLD, width=7):
    draw.line([a, b], fill=color, width=width)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    tip = [b] + [(b[0] - 25 * math.cos(angle + d), b[1] - 25 * math.sin(angle + d)) for d in (-.5, .5)]
    draw.polygon(tip, fill=color)


def castle(draw, x, y, color):
    draw.rectangle((x - 32, y - 24, x + 32, y + 36), fill=color)
    for dx in (-38, 22):
        draw.rectangle((x + dx, y - 44, x + dx + 16, y + 36), fill=color)
    draw.rectangle((x - 10, y + 5, x + 10, y + 36), fill=BG)
    draw.line((x-37,y+39,x+37,y+39),fill=GOLD,width=2)
    draw.line((x,y-25,x,y-64),fill=GOLD,width=2)
    draw.polygon([(x+2,y-63),(x+25,y-58),(x+2,y-47)],fill=color)


def make_frame(row, destination, phase):
    from .teaching_visuals import make_teaching_frame
    return make_teaching_frame(row, destination, phase)


def render_visual(row, destination, ffmpeg, workdir, *, v3_ledger=None, v3_assets=None):
    """Three teaching states, short dissolves, exact cue duration; preserve PNGs."""
    import json
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    duration = float(row["duration_seconds"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Visual duration must be positive and finite")
    folder = Path(workdir) / "drawings" / row["id"]
    folder.mkdir(parents=True, exist_ok=False)
    images = [folder / f"state-{n}.png" for n in range(3)]
    frame_maker = make_frame
    v3 = str(row["id"]).startswith("V3-")
    if v3:
        if v3_ledger is None or v3_assets is None or row.get("shot_id") != "S3-" + row["id"][-2:]:
            raise ValueError("V3 requires its exact evidence ledger and preserved frame bindings")
        from .v3_visuals import make_v3_frame
        def frame_maker(cue, path, phase):
            return make_v3_frame(cue, path, phase, ledger_path=v3_ledger, assets=v3_assets)
    elif row["chapter_id"] == "help":
        from .help_visuals import make_help_frame
        frame_maker = make_help_frame
    receipts = []
    for n, path in enumerate(images):
        receipt = frame_maker(row, path, n)
        if v3 and receipt is not None:
            receipts.append(receipt)
    fade = min(.45, duration / 12)
    length = (duration + 2 * fade) / 3
    offset1 = length - fade
    offset2 = 2 * (length - fade)
    inputs = []
    filters = []
    for n, path in enumerate(images):
        inputs += ["-loop", "1", "-framerate", "30", "-i", str(path)]
        filters.append(f"[{n}:v]trim=duration={length:.6f},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{n}]")
    filters.extend([
        f"[s0][s1]xfade=transition=fade:duration={fade:.6f}:offset={offset1:.6f}[ab]",
        f"[ab][s2]xfade=transition=fade:duration={fade:.6f}:offset={offset2:.6f},format=yuv420p[v]",
    ])
    plan = {"kind": "evidence-scoped-v3-visual" if v3 else "authored-teaching-visual", "cue_id": row["id"],
            "shot_id": row["shot_id"], "duration_seconds": duration,
            "states": [str(path) for path in images], "transition": "fade",
            "transition_seconds": fade, "state_offsets_seconds": [0, offset1, offset2],
            "resolution": [2560, 1440], "fps": 30, "subtitle_safe_top": 1120,
            "evidence_scope": "V3 ledger-scoped rule or case-context visual; no causal or human approval inferred." if v3 else "Teaching diagrams; no live state or human approval inferred."}
    plan["visual_style"] = "war-folio-v3; hash-bound original CK3 frame context or sourced paper diagram" if v3 else "war-folio-v3; original procedural art; no CK3 asset or live provenance"
    if v3:
        plan["frame_receipts"] = receipts
    (folder / "visual-plan.json").write_bytes((json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(ffmpeg), "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"] + inputs + [
        "-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
        "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-threads", "4", str(destination)]
    run_command(CommandSpec.create(argv, label=f"war-teaching-{row['id']}", partial_artifacts=[destination]),
                audit_directory=Path(workdir) / "audit" / "illustrations" / row["id"])
    return destination
