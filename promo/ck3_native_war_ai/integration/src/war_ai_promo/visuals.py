"""The film's illustrated map, candidate cards, thresholds and peace ledgers."""
from pathlib import Path
import math

from PIL import Image, ImageDraw
from xar_promo.process import CommandSpec, run_command

from .common import font, lines

BG = "#101C29"
PANEL = "#1B2B3A"
INK = "#EBE8DA"
MUTED = "#A1B2BB"
GOLD = "#D7B574"
RED = "#D18176"
BLUE = "#77ACD4"
GREEN = "#8EC9AA"


def text(draw, xy, value, size=44, fill=INK, bold=False, width=None):
    wrapped = lines(value, size, width, bold) if width else [value]
    for i, line in enumerate(wrapped):
        draw.text((xy[0], xy[1] + i * size * 1.35), line, font=font(size, bold), fill=fill)


def box(draw, bounds, color=PANEL, outline=None):
    draw.rounded_rectangle(bounds, radius=22, fill=color, outline=outline, width=3)


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


def make_frame(row, destination, phase):
    from .teaching_visuals import make_teaching_frame
    return make_teaching_frame(row, destination, phase)


def render_visual(row, destination, ffmpeg, workdir):
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
    if row["chapter_id"] == "help":
        from .help_visuals import make_help_frame
        frame_maker = make_help_frame
    for n, path in enumerate(images):
        frame_maker(row, path, n)
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
    plan = {"kind": "authored-teaching-visual", "cue_id": row["id"],
            "shot_id": row["shot_id"], "duration_seconds": duration,
            "states": [str(path) for path in images], "transition": "fade",
            "transition_seconds": fade, "state_offsets_seconds": [0, offset1, offset2],
            "resolution": [2560, 1440], "fps": 30, "subtitle_safe_top": 1120,
            "evidence_scope": "Teaching diagrams; no live state or human approval inferred."}
    (folder / "visual-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(ffmpeg), "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"] + inputs + [
        "-filter_complex_threads", "1", "-filter_complex", ";".join(filters),
        "-map", "[v]", "-an", "-t", f"{duration:.6f}", "-r", "30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-threads", "4", str(destination)]
    run_command(CommandSpec.create(argv, label=f"war-teaching-{row['id']}", partial_artifacts=[destination]),
                audit_directory=Path(workdir) / "audit" / "illustrations" / row["id"])
    return destination
