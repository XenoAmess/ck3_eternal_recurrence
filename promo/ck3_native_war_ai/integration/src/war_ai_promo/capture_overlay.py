"""Label a prepared V3 context clip without changing its timeline or claim scope."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from PIL import Image, ImageDraw
from xar_promo.media import probe_and_write_bound_media
from xar_promo.process import CommandSpec, run_command

from .common import binding, font, write_new


CASE_LABELS = {
    "CASE-W": ("CASE-W · 原版战时观察", "玩家宣战后；地图画面不证明目标重算或局部门槛原因"),
    "CASE-C": ("CASE-C · 同一战争续行", "观察窗口未采到接战；画面不表示战斗或和平终局"),
}


def label_capture_clip(prepared: dict, *, case_id: str, cue_id: str, output_root: Path,
                       ffmpeg: str, ffprobe: str) -> dict:
    """Return a separate hash-bound clip/receipt; keep the prepared clip intact."""
    if case_id not in CASE_LABELS or prepared.get("schema") != "ck3-war-ai.prepared-capture-clip.v2":
        raise ValueError("Only a reviewed CASE-W/C prepared clip can receive a V3 context label")
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=False)
    source = Path(prepared["media"]["path"])
    if binding(source)["sha256"] != prepared["media"]["sha256"]:
        raise ValueError("Prepared source clip changed before V3 overlay")
    label_png = output_root / "case-label.png"
    image = Image.new("RGBA", (2560, 1440), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((42, 127, 1590, 267), radius=5,
                           fill=(30, 23, 18, 232), outline=(215, 175, 105, 255), width=3)
    title, limit = CASE_LABELS[case_id]
    draw.text((71, 145), f"{title}  ·  {cue_id}", font=font(48, True), fill=(249, 233, 200, 255))
    draw.text((72, 210), limit, font=font(31), fill=(223, 200, 162, 255))
    image.save(label_png, format="PNG")
    output = output_root / "labelled.mp4"
    argv = [str(ffmpeg), "-nostdin", "-n", "-hide_banner", "-loglevel", "warning",
            "-i", str(source), "-loop", "1", "-i", str(label_png),
            "-filter_complex", "[0:v][1:v]overlay=x=0:y=0:shortest=1:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-an", "-frames:v", str(prepared["selection"]["expected_frame_count"]),
            "-fps_mode", "passthrough", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-movflags", "+faststart", str(output)]
    run_command(CommandSpec.create(argv, label=f"label V3 {cue_id} context", partial_artifacts=[output]),
                audit_directory=output_root / "encode")
    probe = probe_and_write_bound_media(ffprobe, output, output_path=output_root / "labelled.bound-probe.json",
                                        audit_directory=output_root / "probe")
    if (len(probe.probe.video_streams) != 1 or probe.probe.audio_streams
            or (probe.probe.video_streams[0].width, probe.probe.video_streams[0].height) != (2560, 1440)
            or abs(probe.probe.require_duration() - prepared["duration_seconds"]) > .002):
        raise ValueError("V3 labelled clip changed media dimensions, stream count, or duration")
    receipt_path = output_root / "labelled-receipt.json"
    receipt = {**prepared, "schema": "ck3-war-ai.labeled-capture-clip.v1",
               "status": "labelled-context-not-causal-approval",
               "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "cue_id": cue_id, "case_id": case_id, "evidence_role": "context",
               "label_text": [title, limit], "label_artifact": binding(label_png),
               "original_prepared_media": prepared["media"],
               "original_prepared_receipt": prepared["receipt"],
               "media": binding(output), "labelled_bound_probe": binding(output_root / "labelled.bound-probe.json"),
               "native_ai_causality_verified": False, "human_1x_review_performed": False,
               "signoff_granted": False}
    write_new(receipt_path, receipt)
    return {**receipt, "receipt": binding(receipt_path)}
