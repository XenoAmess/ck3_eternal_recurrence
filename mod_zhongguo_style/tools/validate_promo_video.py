#!/usr/bin/env python3
"""Validate the ZhongGuo 361 promo project and optional rendered media."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402


class ValidationError(promo.PromoError):
    """Promo validation failed."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValidationError(f"could not read {label}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"{label} root must be an object: {path}")
    return payload


def _validate_release_source_records(chapters: list[promo.shared.Chapter]) -> None:
    """Require immutable, absolute source records in a release manifest.

    Draft manifests deliberately keep repository-relative paths convenient for
    authors.  A captured release manifest lives beside preserved process
    artifacts, so every referenced visual/evidence file must instead carry an
    absolute path plus the exact byte count and SHA-256 checked by the loader.
    """

    for chapter in chapters:
        records: list[tuple[str, Any]] = []
        if "source" in chapter.raw:
            records.append(("source", chapter.raw["source"]))
        for index, record in enumerate(chapter.raw.get("evidence_sources", [])):
            records.append((f"evidence_sources[{index}]", record))
        for label, record in records:
            context = f"chapter {chapter.chapter_id} {label}"
            if not isinstance(record, dict):
                raise ValidationError(
                    f"release {context} must be an object with path/bytes/sha256"
                )
            raw_path = record.get("path")
            if not isinstance(raw_path, str) or not Path(
                os.path.expandvars(os.path.expanduser(raw_path))
            ).is_absolute():
                raise ValidationError(f"release {context} path must be absolute")
            raw_bytes = record.get("bytes")
            if isinstance(raw_bytes, bool) or not isinstance(raw_bytes, int) or raw_bytes < 0:
                raise ValidationError(
                    f"release {context} must declare a non-negative byte count"
                )
            raw_sha256 = record.get("sha256")
            if (
                not isinstance(raw_sha256, str)
                or len(raw_sha256) != 64
                or any(character not in "0123456789abcdefABCDEF" for character in raw_sha256)
            ):
                raise ValidationError(
                    f"release {context} must declare a 64-character SHA-256"
                )


def validate_project(
    manifest_path: Path, *, stage: str
) -> tuple[dict[str, Any], list[promo.shared.Chapter]]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest, chapters = promo.load_manifest(manifest_path)
    ffmpeg = promo.shared.find_program(None, "ffmpeg")
    ffprobe = promo.shared.find_program(None, "ffprobe", sibling_of=ffmpeg)
    fonts = promo.shared.find_fonts()
    promo.shared.preflight_video_sources(chapters, ffprobe)
    promo.prepare_subtitle_layouts(chapters, fonts)

    if promo.shared.EDGE_TTS_VERSION != "7.2.8":
        raise ValidationError(
            f"edge-tts 7.2.8 is required, got {promo.shared.EDGE_TTS_VERSION!r}"
        )
    if chapters[0].promo_type != "title_card":
        raise ValidationError(
            "the first chapter must be a generated title card so CK3 loading footage "
            "cannot become the opening"
        )
    placeholder_count = int(manifest["_placeholder_count"])
    if stage == "release" and placeholder_count:
        raise ValidationError(
            f"release validation forbids placeholders; {placeholder_count} remain"
        )
    if (
        stage == "release"
        and manifest.get("project_status") != "captured_release_candidate"
    ):
        raise ValidationError(
            "release validation requires project_status='captured_release_candidate'"
        )
    if stage == "release":
        if not isinstance(manifest.get("release_manifest_provenance"), dict):
            raise ValidationError(
                "release validation requires GREEN capture projection provenance"
            )
        missing_live = [
            chapter.chapter_id
            for chapter in chapters
            if chapter.promo_type != "title_card"
            and chapter.material_status != "captured"
        ]
        if missing_live:
            raise ValidationError(
                "release chapters without captured live material: "
                + ", ".join(missing_live)
            )
        _validate_release_source_records(chapters)

    capture_ids = [
        chapter.raw["capture"]["id"]
        for chapter in chapters
        if isinstance(chapter.raw.get("capture"), dict)
    ]
    if len(capture_ids) != len(set(capture_ids)):
        raise ValidationError("capture ids are not unique")
    for chapter in chapters:
        if chapter.material_status == "placeholder":
            shot = chapter.raw["capture"]["shot"]
            if "待" not in chapter.status_zh and "PLACEHOLDER" not in chapter.status_en.upper():
                raise ValidationError(
                    f"placeholder {chapter.chapter_id} lacks a visible pending status"
                )
            if len(shot) < 12:
                raise ValidationError(
                    f"placeholder {chapter.chapter_id} needs a concrete capture shot"
                )

    print(
        "PROJECT GREEN: "
        f"stage={stage}; chapters={len(chapters)}; captures={len(capture_ids)}; "
        f"placeholders={placeholder_count}; "
        f"estimated={manifest['_estimated_duration_seconds']:.1f}s; "
        f"topics={len(promo.REQUIRED_TOPICS)}; voice={promo.VOICE}"
    )
    return manifest, chapters


def _validate_ass(path: Path, sidecar: dict[str, Any]) -> None:
    if not path.is_file():
        raise ValidationError(f"subtitle ASS is missing: {path}")
    text = path.read_text(encoding="utf-8-sig")
    required = (
        "Style: ChinesePrimary",
        "Style: EnglishSecondary",
        "Dialogue: 0",
        "Dialogue: 1",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise ValidationError(
            "bilingual ASS is missing required structures: " + ", ".join(missing)
        )
    recorded = sidecar.get("subtitles")
    if not isinstance(recorded, dict):
        raise ValidationError("sidecar subtitles block is missing")
    if recorded.get("sha256") != promo.shared._sha256(path):
        raise ValidationError("sidecar subtitle SHA-256 does not match ASS")


def validate_media(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    chapters: list[promo.shared.Chapter],
    video_path: Path,
    sidecar_path: Path | None,
    stage: str,
) -> tuple[dict[str, Any], Path]:
    video_path = video_path.expanduser().resolve()
    if not video_path.is_file():
        raise ValidationError(f"video does not exist: {video_path}")
    sidecar_path = (
        sidecar_path.expanduser().resolve()
        if sidecar_path is not None
        else video_path.with_suffix(".video.json")
    )
    if not sidecar_path.is_file():
        raise ValidationError(f"video sidecar does not exist: {sidecar_path}")
    sidecar = _read_json(sidecar_path, "video sidecar")
    if sidecar.get("kind") != promo.KIND:
        raise ValidationError(f"unexpected sidecar kind: {sidecar.get('kind')!r}")
    manifest_block = sidecar.get("manifest")
    if not isinstance(manifest_block, dict):
        raise ValidationError("sidecar manifest block is missing")
    if manifest_block.get("sha256") != promo.shared._sha256(manifest_path.resolve()):
        raise ValidationError("sidecar was built from a different manifest")
    language = sidecar.get("language")
    if not isinstance(language, dict) or language.get("voice") != promo.VOICE:
        raise ValidationError("sidecar does not bind the required Xiaoxiao voice")
    if language.get("primary") != "Simplified Chinese narration and visual hierarchy":
        raise ValidationError("sidecar primary language is not Simplified Chinese")
    if language.get("subtitles") != [
        "Simplified Chinese primary",
        "English secondary",
    ]:
        raise ValidationError("sidecar does not record both subtitle languages")
    if sidecar.get("placeholder_count") != manifest["_placeholder_count"]:
        raise ValidationError("sidecar placeholder count does not match manifest")
    if stage == "release" and sidecar.get("placeholder_count") != 0:
        raise ValidationError("release sidecar still contains placeholders")
    if stage == "release" and sidecar.get("readiness") != "rendered_candidate":
        raise ValidationError("release sidecar is not a rendered candidate")
    chapter_rows = sidecar.get("chapters")
    if not isinstance(chapter_rows, list) or len(chapter_rows) != len(chapters):
        raise ValidationError("sidecar chapter count does not match manifest")

    ffmpeg = promo.shared.find_program(None, "ffmpeg")
    ffprobe = promo.shared.find_program(None, "ffprobe", sibling_of=ffmpeg)
    probe = promo.shared.probe_media(ffprobe, video_path)
    info = promo.shared.validate_encoded_media(probe, video_path)
    duration = float(info["duration"])
    if duration >= promo.MAX_DURATION_SECONDS:
        raise ValidationError(
            f"video is {duration:.3f}s; it must be shorter than 1200s"
        )
    audio = info["audio"]
    audio_language = (audio.get("tags") or {}).get("language")
    if audio_language not in {"zho", "chi"}:
        raise ValidationError(
            f"audio language tag is {audio_language!r}, expected zho/chi"
        )
    video_block = sidecar.get("video")
    if not isinstance(video_block, dict):
        raise ValidationError("sidecar video block is missing")
    if video_block.get("sha256") != promo.shared._sha256(video_path):
        raise ValidationError("sidecar video SHA-256 does not match the MP4")
    subtitle_block = sidecar.get("subtitles")
    if not isinstance(subtitle_block, dict):
        raise ValidationError("sidecar subtitles block is missing")
    ass_path = Path(str(subtitle_block.get("path", "")))
    _validate_ass(ass_path, sidecar)

    print(
        "MEDIA GREEN: "
        f"stage={stage}; duration={duration:.3f}s; "
        f"geometry={info['video'].get('width')}x{info['video'].get('height')}; "
        f"video={info['video'].get('codec_name')}/{info['video'].get('pix_fmt')}; "
        f"audio={audio.get('codec_name')}/{audio.get('sample_rate')}Hz/{audio_language}; "
        "subtitles=burned zh-CN+en"
    )
    return info, ffmpeg


def extract_samples(
    *, video_path: Path, duration: float, ffmpeg: Path, sample_directory: Path
) -> list[Path]:
    sample_directory = sample_directory.expanduser().resolve()
    if sample_directory.exists():
        raise ValidationError(
            f"sample directory already exists; choose a new path so prior QA is preserved: "
            f"{sample_directory}"
        )
    sample_directory.mkdir(parents=True)
    times = [
        max(0.2, duration * 0.03),
        duration * 0.25,
        duration * 0.50,
        duration * 0.75,
        max(0.2, duration - 0.5),
    ]
    outputs: list[Path] = []
    for index, timestamp in enumerate(times, start=1):
        output = sample_directory / f"sample-{index:02d}-{timestamp:08.3f}s.png"
        promo.shared.run_checked(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp:.6f}",
                "-i",
                video_path,
                "-frames:v",
                "1",
                output,
            ],
            cwd=None,
            action=f"extracting promo QA sample {index}",
        )
        outputs.append(output)
    print(f"SAMPLES: {sample_directory} ({len(outputs)} preserved PNG files)")
    return outputs


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--stage", choices=("draft", "release"), default="draft")
    result.add_argument("--video", type=Path)
    result.add_argument("--sidecar", type=Path)
    result.add_argument("--sample-dir", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest, chapters = validate_project(args.manifest, stage=args.stage)
        if args.sidecar is not None and args.video is None:
            raise ValidationError("--sidecar requires --video")
        if args.sample_dir is not None and args.video is None:
            raise ValidationError("--sample-dir requires --video")
        if args.video is not None:
            info, ffmpeg = validate_media(
                manifest_path=args.manifest.expanduser().resolve(),
                manifest=manifest,
                chapters=chapters,
                video_path=args.video,
                sidecar_path=args.sidecar,
                stage=args.stage,
            )
            if args.sample_dir is not None:
                extract_samples(
                    video_path=args.video.expanduser().resolve(),
                    duration=float(info["duration"]),
                    ffmpeg=ffmpeg,
                    sample_directory=args.sample_dir,
                )
    except ValidationError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    except promo.shared.ShowcaseError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
