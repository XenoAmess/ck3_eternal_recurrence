#!/usr/bin/env python3
"""Build clean motion plates and publication artwork for Project Causality r12."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/project-causality/2026-09-20-r12/assets"
PLATES = ROOT / "artifacts/project-causality/2026-09-19-r7/architecture-plates"
KEY_ART = ROOT / "images/project_causality/promo/project_causality_key_art.png"
WIDTH = 2560
HEIGHT = 1440
FPS = 30


class AssetBuildError(RuntimeError):
    pass


def run(command: Sequence[str | Path]) -> None:
    print("RUN:", " ".join(str(value) for value in command), flush=True)
    result = subprocess.run([str(value) for value in command], check=False)
    if result.returncode:
        raise AssetBuildError(f"command failed with exit code {result.returncode}")


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise AssetBuildError("no suitable publication font found")


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def draw_end_card(path: Path) -> None:
    base = cover(Image.open(KEY_ART), (WIDTH, HEIGHT))
    base = ImageEnhance.Brightness(base).enhance(0.82)
    overlay = Image.new("RGBA", base.size, (4, 10, 24, 0))
    paint = ImageDraw.Draw(overlay)
    for y in range(HEIGHT):
        alpha = int(72 + 118 * (y / HEIGHT))
        paint.line((0, y, WIDTH, y), fill=(4, 10, 24, alpha))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base)
    gold = (244, 199, 112, 255)
    ivory = (246, 241, 229, 255)
    pale = (206, 218, 231, 255)
    cyan = (105, 215, 226, 255)

    draw.text((150, 110), "PROJECT CAUSALITY", font=font(42, bold=True), fill=gold)
    draw.text((150, 176), "因果律不是口号，而是一条可以运行的链。", font=font(70, bold=True), fill=ivory)
    draw.text((150, 292), "已有 Mod", font=font(46, bold=True), fill=cyan)
    draw.text((150, 354), "接入无人化、可重放的真实 CK3 验收", font=font(40), fill=ivory)
    draw.text((150, 446), "新创作者", font=font(46, bold=True), fill=cyan)
    draw.text((150, 508), "从玩家承诺出发，走完创作、测试、核验与发行", font=font(40), fill=ivory)

    box = (150, 625, 2410, 1195)
    draw.rounded_rectangle(box, radius=36, fill=(5, 13, 31, 205), outline=(244, 199, 112, 170), width=3)
    draw.text((220, 672), "代码与文档", font=font(30, bold=True), fill=gold)
    draw.text((220, 716), "github.com/XenoAmess/ck3_eternal_recurrence", font=font(34), fill=ivory)
    draw.text((220, 785), "Steam 创意工坊 · 9 项已上架", font=font(30, bold=True), fill=gold)
    workshop_items = [
        ("琉焰卿的永恒轮回", "3784706360"),
        ("白绮特供独立版", "3787304042"),
        ("天朝特色361制官员绩效考核", "3792585972"),
        ("牛来", "3790635143"),
        ("XenoAmess 的体验优化", "3798133925"),
        ("自动升级建筑（维护版）", "3800124956"),
        ("重整河山", "3798404599"),
        ("肃清曼荼罗伪信", "3797711947"),
        ("驱策朝贡国", "3801490405"),
    ]
    for index, (name, item_id) in enumerate(workshop_items):
        column = 0 if index < 5 else 1
        row = index if index < 5 else index - 5
        x = 220 + column * 1110
        y = 838 + row * 50
        draw.text((x, y), f"{name}  ·  {item_id}", font=font(29), fill=pale)
    draw.text((150, 1298), "让每一次创造，都为下一次留下可以点燃的余烬。", font=font(40), fill=ivory)
    path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(path, quality=95)


def draw_thumbnail(path: Path) -> None:
    size = (1280, 720)
    base = cover(Image.open(KEY_ART), size)
    base = ImageEnhance.Brightness(base).enhance(0.88).convert("RGBA")
    shade = Image.new("RGBA", size, (3, 8, 20, 0))
    paint = ImageDraw.Draw(shade)
    for x in range(size[0]):
        alpha = int(205 * (1 - x / size[0]) + 45)
        paint.line((x, 0, x, size[1]), fill=(3, 8, 20, min(230, alpha)))
    base = Image.alpha_composite(base, shade)
    draw = ImageDraw.Draw(base)
    draw.text((68, 78), "PROJECT", font=font(42, bold=True), fill=(244, 199, 112, 255))
    draw.text((68, 134), "因果律", font=font(92, bold=True), fill=(250, 247, 238, 255))
    draw.text((72, 254), "一套让 Mod 自己走完", font=font(42, bold=True), fill=(214, 230, 238, 255))
    draw.text((72, 312), "创作 · 测试 · 实机核验 · 发行", font=font(42, bold=True), fill=(103, 220, 228, 255))
    draw.rounded_rectangle((68, 490, 772, 626), radius=24, fill=(5, 13, 31, 205), outline=(244, 199, 112, 170), width=3)
    draw.text((104, 514), "完整体系 + 罗贝尔自主战争实机", font=font(34, bold=True), fill=(250, 247, 238, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(path, quality=95)


def motion_clip(
    ffmpeg: str,
    images: Sequence[Path],
    output: Path,
    *,
    duration: float,
    force: bool,
) -> None:
    if output.is_file() and not force:
        print(f"REUSE: {output}", flush=True)
        return
    for image in images:
        if not image.is_file():
            raise AssetBuildError(f"motion source is missing: {image}")
    output.parent.mkdir(parents=True, exist_ok=True)
    transition = 0.65 if len(images) > 1 else 0.0
    hold = (duration + transition * (len(images) - 1)) / len(images)
    command: list[str | Path] = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for image in images:
        command.extend(["-loop", "1", "-t", f"{hold + 0.2:.6f}", "-i", image])
    filters: list[str] = []
    frames = max(1, int(round((hold + 0.1) * FPS)))
    for index in range(len(images)):
        filters.append(
            f"[{index}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x07111f,"
            "zoompan=z='min(zoom+0.000035,1.018)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"format=yuv420p,setpts=PTS-STARTPTS[v{index}]"
        )
    current = "v0"
    if len(images) > 1:
        for index in range(1, len(images)):
            result = f"x{index}"
            offset = index * (hold - transition)
            filters.append(
                f"[{current}][v{index}]xfade=transition=fade:duration={transition:.3f}:"
                f"offset={offset:.6f}[{result}]"
            )
            current = result
    filters.append(f"[{current}]trim=duration={duration:.6f},setpts=PTS-STARTPTS[out]")
    temporary = output.with_name(f".{output.stem}.partial.mp4")
    temporary.unlink(missing_ok=True)
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-an",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            temporary,
        ]
    )
    run(command)
    temporary.replace(output)


def plate(name: str) -> Path:
    return PLATES / name


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--force", action="store_true")
    result.add_argument("--cta-only", action="store_true")
    result.add_argument("--ffmpeg")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    output = args.output_dir.expanduser().resolve()
    ffmpeg = args.ffmpeg or shutil.which("ffmpeg")
    if not ffmpeg:
        raise AssetBuildError("ffmpeg is required")
    end_card = output / "project-causality-r12-end-card.png"
    thumbnail = output / "project-causality-r12-thumbnail.jpg"
    draw_end_card(end_card)
    draw_thumbnail(thumbnail)
    jobs = {
        "opening-system-motion.mp4": (
            45.0,
            [
                plate("arch-09-system-thesis-01-topology_silhouette.png"),
                plate("arch-09-system-thesis-03-player_products.png"),
                plate("arch-09-system-thesis-04-developer_products.png"),
                plate("arch-09-system-thesis-05-feedback_exit.png"),
            ],
        ),
        "method-pipeline-motion.mp4": (
            125.0,
            [
                plate("arch-10-generation-projection-01-authority.png"),
                plate("arch-10-generation-projection-02-generator.png"),
                plate("arch-10-generation-projection-03-projections.png"),
                plate("arch-07-acceptance-02-offline_lane.png"),
                plate("arch-07-acceptance-03-production_lane.png"),
                plate("arch-06-mcp-construction-02-capability_plane.png"),
                plate("arch-06-mcp-construction-03-planner_executor.png"),
                plate("arch-06-mcp-construction-04-verifier_evidence.png"),
                plate("arch-07-acceptance-04-verdict_lane.png"),
                plate("arch-10-generation-projection-04-delivery_and_return.png"),
            ],
        ),
        "principle-readback-motion.mp4": (
            35.0,
            [
                plate("arch-08-normative-authority-01-normative_order.png"),
                plate("arch-06-state-over-ack-01-ack_is_not_state.png"),
                plate("arch-06-state-over-ack-02-independent_postcondition.png"),
            ],
        ),
        "loop-a-motion.mp4": (
            50.0,
            [
                plate("arch-02-loop-a-01-topology_silhouette.png"),
                plate("arch-02-loop-a-02-definition_and_build.png"),
                plate("arch-02-loop-a-04-reality_to_next_version.png"),
                plate("arch-02-loop-a-05-red_return.png"),
            ],
        ),
        "loop-b-motion.mp4": (
            50.0,
            [
                plate("arch-03-loop-b-01-topology_silhouette.png"),
                plate("arch-03-loop-b-02-blocker_and_research.png"),
                plate("arch-03-loop-b-04-ooda_to_next_blocker.png"),
                plate("arch-03-loop-b-05-failed_postcondition.png"),
            ],
        ),
        "loop-c-motion.mp4": (
            50.0,
            [
                plate("arch-04-loop-c-01-topology_silhouette.png"),
                plate("arch-04-loop-c-02-new_semantics_to_runtime.png"),
                plate("arch-04-loop-c-04-exact_build_certification.png"),
                plate("arch-04-loop-c-05-difference_red_return.png"),
            ],
        ),
        "loop-d-motion.mp4": (
            50.0,
            [
                plate("arch-05-loop-d-01-topology_silhouette.png"),
                plate("arch-05-loop-d-02-green_to_claim.png"),
                plate("arch-05-loop-d-04-delivery_to_feedback.png"),
                plate("arch-05-loop-d-05-hold_and_rebuild.png"),
            ],
        ),
        "cta-motion.mp4": (60.0, [end_card, end_card]),
    }
    selected = {"cta-motion.mp4"} if args.cta_only else set(jobs)
    for name, (duration, images) in jobs.items():
        if name not in selected:
            continue
        motion_clip(ffmpeg, images, output / name, duration=duration, force=args.force)
    print(f"ASSETS: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
