"""Create a clearly synthetic six-chapter native run and exercise the real assembler.

This never opens CK3 or a desktop recorder. Its short generated media cannot be
used as episode footage, card legibility evidence, or human review evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from war_ai_promo.assemble_episode_two import assemble  # noqa: E402
from war_ai_promo.episode_two_second_half import CHAPTER_CARDS, CHAPTER_IDS, _replay_primary  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def new_json(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def command(root: Path, name: str, argv: list[str]) -> None:
    logs = root / "commands" / name
    logs.mkdir(parents=True, exist_ok=False)
    new_json(logs / "argv.json", {"argv": argv, "synthetic": True})
    with (logs / "stdout.txt").open("xb") as stdout, (logs / "stderr.txt").open("xb") as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError(f"{name} failed: exit {result.returncode}; see {logs}")


def preserve(root: Path, manifest: Path, artifact_id: str, source: Path, role: str) -> None:
    command(root, "preserve-" + artifact_id,
            [sys.executable, "-m", "xar_promo", "preserve", "--run-manifest", str(manifest),
             "--artifact-id", artifact_id, "--collection", "raw", "--role", role, str(source)])


def frame(path: Path, chapter: str, labels: list[str]) -> None:
    image = Image.new("RGB", (2560, 1440), (29, 25, 23))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 68)
    small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 47)
    draw.text((110, 110), f"SYNTHETIC TECHNICAL SMOKE · {chapter}", font=font,
              fill=(248, 219, 173))
    draw.text((110, 230), "合成测试素材；没有游戏录像、真实计算卡或人工审片", font=small,
              fill=(235, 218, 194))
    for index, label in enumerate(labels):
        draw.text((110, 360 + 170 * index), label, font=small, fill=(220, 203, 176))
    with path.open("xb") as stream:
        image.save(stream, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-directory", type=Path, required=True)
    parser.add_argument("--project-directory", type=Path, required=True)
    parser.add_argument("--selected-version", required=True)
    parser.add_argument("--selected-wheel-sha256", required=True)
    args = parser.parse_args()
    if not args.attempt_directory.is_absolute():
        raise ValueError("Synthetic attempt must use an absolute external path")
    root = args.attempt_directory.resolve()
    if root.is_relative_to(SRC.parents[3]):
        raise ValueError("Synthetic attempt must be outside the project worktree")
    if root.exists():
        raise FileExistsError(f"Synthetic attempt already exists: {root}")
    project = args.project_directory.resolve(strict=True)
    config = project / "project" / "promo-project.json"
    cards_dir = project / "cards"
    card_index = cards_dir / "calculation-cards.json"
    cards = json.loads(card_index.read_text(encoding="utf-8"))
    replay_by_card = {row["id"]: row["replay"] for row in cards["cards"]}
    root.mkdir(parents=True, exist_ok=False)
    (root / "commands").mkdir()
    media = root / "synthetic-source-media"
    media.mkdir()
    run = root / "native-run"
    command(root, "start-run", [sys.executable, "-m", "xar_promo", "start-run",
             "--run-id", "episode02-synthetic-" + uuid4().hex,
             "--run-directory", str(run), str(config)])
    manifest = run / "run-manifest.json"
    snapshot = run / json.loads(manifest.read_text(encoding="utf-8"))["project_config"]["path"]
    script = media / "synthetic-narration.md"
    title = ["开场", "追击", "骑士", "增援", "终局", "收束"]
    chapters = []
    with script.open("x", encoding="utf-8", newline="\n") as stream:
        for index, chapter in enumerate(CHAPTER_IDS):
            zh = f"这是第{index + 1}章合成技术样本。"
            stream.write(f"## 00:00–00:01 {title[index]}\n\n**旁白**：{zh}\n\n"
                         "**录制缺口**：此文件全部为合成技术测试。\n\n")
            chapters.append({"id": chapter, "title": title[index], "zh": zh,
                             "en": f"Synthetic technical sample chapter {index + 1}.",
                             "speech_duration_seconds": 1.0, "duration_seconds": 1.5,
                             "audio_artifact_id": f"audio.{chapter}",
                             "reel_artifact_id": f"reel.{chapter}",
                             "reel_receipt_artifact_id": f"reel-receipt.{chapter}"})
    preserve(root, manifest, "episode02-narration-script", script, "synthetic-script")
    preserve(root, manifest, "episode02-card-index", card_index, "source-card-index")
    card_sha = {}
    card_bytes = {}
    for card_id in replay_by_card:
        path = cards_dir / f"{card_id.lower()}-calculation.svg"
        preserve(root, manifest, f"episode02-card-{card_id}", path, "source-card")
        card_sha[card_id] = sha(path)
        card_bytes[card_id] = path.stat().st_size
    source_save = media / "synthetic-cold-load-save.ck3"
    with source_save.open("xb") as stream:
        stream.write(b"SYNTHETIC TEST BYTES -- NOT A CK3 SAVE\n")
    preserve(root, manifest, "synthetic-cold-load-save", source_save, "synthetic-test-source")
    music = media / "synthetic-theme.wav"
    command(root, "make-music", ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-f", "lavfi", "-i", "sine=frequency=220:duration=2", "-ar", "48000", "-ac", "2",
             str(music)])
    preserve(root, manifest, "episode02-synthetic-theme", music, "synthetic-theme")
    audio = media / "synthetic-voice.wav"
    command(root, "make-audio", ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-ar", "48000", "-ac", "2",
             str(audio)])
    for row in chapters:
        chapter = row["id"]
        labels = [f"{card_id} · 历史研究 {replay_by_card[card_id]} · 非当前录制"
                  for card_id in CHAPTER_CARDS.get(chapter, ())]
        picture = media / f"{chapter}.png"
        frame(picture, chapter, labels)
        reel = media / f"{chapter}.mp4"
        command(root, "make-reel-" + chapter,
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                 "-loop", "1", "-framerate", "30", "-i", str(picture), "-t", "1.5",
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "36", "-pix_fmt", "yuv420p",
                 "-an", str(reel)])
        preserve(root, manifest, f"audio.{chapter}", audio, "synthetic-voice")
        preserve(root, manifest, f"reel.{chapter}", reel, "synthetic-reel")
        preserve(root, manifest, f"raw.{chapter}", reel, "synthetic-raw-video")
        control = media / f"control-{chapter}.json"
        new_json(control, {"schema": "synthetic.control.v1", "chapter": chapter})
        preserve(root, manifest, f"control.{chapter}", control, "synthetic-control")
        clean = media / f"clean-{chapter}.json"
        new_json(clean, {"schema": "synthetic.clean-span.v1", "chapter": chapter})
        preserve(root, manifest, f"clean.{chapter}", clean, "synthetic-clean-span")
        label = media / f"source-label-{chapter}.json"
        new_json(label, {"schema": "synthetic.source-label.v1", "chapter": chapter})
        preserve(root, manifest, f"source-label.{chapter}", label, "synthetic-source-label")
        card_rows = {}
        for card_id in CHAPTER_CARDS.get(chapter, ()):
            replay = replay_by_card[card_id]
            label_text = f"{card_id} · 历史研究 {replay} · 非当前录制"
            audit = media / f"card-label-{card_id}.json"
            new_json(audit, {"schema": "ck3-war-ai.episode02.card-label-audit.v1",
                             "status": "visible", "card_id": card_id, "reel_sha256": sha(reel),
                             "label_text": label_text, "synthetic": True})
            preserve(root, manifest, f"card-label.{card_id}", audit, "synthetic-visible-label")
            card_rows[card_id] = {"sha256": card_sha[card_id], "replay": replay,
                                  "primary_receipt_sha256": _replay_primary(cards["replays"][replay]),
                                  "evidence_mode": "historical_research_card",
                                  "visible_label_text": label_text,
                                  "visible_label_audit_artifact_id": f"card-label.{card_id}"}
            source = cards["replays"][replay]
            if "source_save_sha256" in source:
                card_rows[card_id]["indexed_cold_load_save_sha256"] = source["source_save_sha256"]
            if "source_day27_checkpoint_sha256" in source:
                card_rows[card_id]["indexed_midrun_checkpoint_save_sha256"] = source[
                    "source_day27_checkpoint_sha256"]
        span = {"attempt_id": "SYNTHETIC-" + chapter,
                "cold_load_save_artifact_id": "synthetic-cold-load-save",
                "cold_load_save_sha256": sha(source_save), "cold_load_save_bytes": source_save.stat().st_size,
                "raw_video_artifact_id": f"raw.{chapter}",
                "raw_video_sha256": sha(reel), "raw_video_bytes": reel.stat().st_size,
                "raw_video_width": 2560, "raw_video_height": 1440,
                "upscaled_to_reel": False, "resampled_to_reel": False,
                "control_artifact_id": f"control.{chapter}",
                "control_sha256": sha(control), "control_bytes": control.stat().st_size,
                "clean_span_receipt_artifact_id": f"clean.{chapter}",
                "label_audit_artifact_id": f"source-label.{chapter}"}
        receipt = media / f"reel-receipt-{chapter}.json"
        new_json(receipt, {"schema": "ck3-war-ai.episode02.chapter-reel.v1",
                           "chapter_id": chapter, "media_sha256": sha(reel),
                           "media_bytes": reel.stat().st_size, "duration_seconds": 1.5,
                           "reel_width": 2560, "reel_height": 1440,
                           "cards": card_rows, "capture_spans": [span],
                           "different_attempts_explicitly_labelled": True,
                           "synthetic": True})
        preserve(root, manifest, f"reel-receipt.{chapter}", receipt, "synthetic-reel-receipt")
        row.update({"audio_sha256": sha(audio), "audio_bytes": audio.stat().st_size,
                    "reel_sha256": sha(reel), "reel_bytes": reel.stat().st_size,
                    "reel_receipt_sha256": sha(receipt),
                    "reel_receipt_bytes": receipt.stat().st_size})
    production = media / "production-inputs.json"
    new_json(production, {"schema": "ck3-war-ai.episode02.production-inputs.v1",
                          "human_signoff": "not-provided", "synthetic": True,
                          "project_config_sha256": sha(snapshot),
                          "project_config_bytes": snapshot.stat().st_size,
                          "narration_script_sha256": sha(script), "narration_script_bytes": script.stat().st_size,
                          "card_index_sha256": sha(card_index), "card_index_bytes": card_index.stat().st_size,
                          "card_sha256": card_sha, "card_bytes": card_bytes,
                          "replay_by_card": replay_by_card,
                          "music_artifact_id": "episode02-synthetic-theme",
                          "music_sha256": sha(music), "music_bytes": music.stat().st_size,
                          "chapters": chapters})
    preserve(root, manifest, "episode02-production-inputs-v1", production, "synthetic-production-inputs")
    result = assemble(manifest, root / "assembly", selected_version=args.selected_version,
                      selected_wheel_sha256=args.selected_wheel_sha256, synthetic_smoke=True)
    print(json.dumps({"state": result["state"], "output": result["final"],
                      "attempt": str(root)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
