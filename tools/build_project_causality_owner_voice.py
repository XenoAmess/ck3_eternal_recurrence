#!/usr/bin/env python3
"""Replace the r9 Project Causality narration with an authorized IndexTTS voice.

The r9 picture lock is already frame-accurate and contains burned bilingual
subtitles.  This builder reconstructs its final editorial timeline from the
source sidecars, synthesizes every complete narration cue with one IndexTTS
speaker reference, preserves the four chapter-gate sound effects, and remuxes
the new audio while copying the H.264 video stream unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
R9_DIR = ROOT / "artifacts/project-causality/2026-09-19-r9"
DEFAULT_PICTURE = R9_DIR / "project-causality-r9-nomusic-picture-lock.mp4"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/project-causality/2026-09-19-r10-owner-voice"
R7_SIDECAR = (
    ROOT
    / "artifacts/project-causality/2026-09-19-r7/project-causality-r7-nomusic-picture-lock.video.json"
)
VALUE_SIDECAR = (
    ROOT / "artifacts/project-causality/2026-09-19-r8/work/value-showcase.video.json"
)
GATE_SIDECAR = (
    ROOT
    / "artifacts/project-causality/2026-09-19-r8/work/chapter-gates-showcase.video.json"
)
AGENT_SIDECAR = R9_DIR / "work/agent-showcase.video.json"

FPS = 30
TOTAL_FRAMES = 61643
TOTAL_SECONDS = TOTAL_FRAMES / FPS
TOLERANCE = 0.002


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceSlice:
    label: str
    sidecar: Path
    source_start: float
    source_end: float
    output_start: float
    kind: str


@dataclass(frozen=True)
class Cue:
    index: int
    cue_id: str
    text: str
    start: float
    end: float
    narration_delay: float
    sound_effect: Path | None
    source_label: str

    @property
    def duration(self) -> float:
        return self.end - self.start


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"JSON root must be an object: {path}")
    return value


def run(command: Sequence[str | Path], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("RUN:", " ".join(str(item) for item in command), flush=True)
    result = subprocess.run(
        [str(item) for item in command],
        check=False,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        detail = result.stderr.strip() if capture else ""
        raise BuildError(
            f"command failed with exit code {result.returncode}"
            + (f": {detail}" if detail else "")
        )
    return result


def probe_duration(ffprobe: str, path: Path) -> float:
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            path,
        ],
        capture=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise BuildError(f"invalid media duration for {path}: {result.stdout!r}") from exc


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug[:80] or "cue"


def source_slices() -> list[SourceSlice]:
    # Direct expansion of the r8/r9 assembly edits.  Every boundary is also a
    # chapter boundary in the corresponding source sidecar.
    rows = [
        ("r7-prologue", R7_SIDECAR, 0.0, 154.13333333333333, "r7"),
        ("creator-value", VALUE_SIDECAR, 0.0, 180.0, "showcase"),
        ("spell-gate", GATE_SIDECAR, 0.0, 20.0, "gate"),
        ("r7-spell-products-and-coa", R7_SIDECAR, 174.13333333333333, 594.0333333333333, "r7"),
        ("fresh-robert-agent", AGENT_SIDECAR, 0.0, 420.0, "showcase"),
        ("method-gate", GATE_SIDECAR, 20.0, 40.0, "gate"),
        ("r7-method", R7_SIDECAR, 689.2666666666667, 1046.2, "r7"),
        ("principle-gate", GATE_SIDECAR, 40.0, 60.0, "gate"),
        ("r7-principle", R7_SIDECAR, 1066.2, 1265.7333333333333, "r7"),
        ("vision-gate", GATE_SIDECAR, 60.0, 80.0, "gate"),
        ("r7-vision-close", R7_SIDECAR, 1285.7333333333333, 1530.0, "r7"),
    ]
    cursor = 0.0
    result: list[SourceSlice] = []
    for label, sidecar, source_start, source_end, kind in rows:
        result.append(
            SourceSlice(
                label=label,
                sidecar=sidecar,
                source_start=source_start,
                source_end=source_end,
                output_start=cursor,
                kind=kind,
            )
        )
        cursor += source_end - source_start
    if abs(cursor - TOTAL_SECONDS) > TOLERANCE:
        raise BuildError(f"source slices total {cursor:.6f}s; expected {TOTAL_SECONDS:.6f}s")
    return result


def chapter_times(chapter: dict[str, Any], kind: str) -> tuple[float, float]:
    if kind == "r7":
        return float(chapter["new_start_seconds"]), float(chapter["new_end_seconds"])
    return float(chapter["start_seconds"]), float(chapter["end_seconds"])


def narration_text_path(chapter: dict[str, Any], kind: str) -> Path:
    if kind == "r7":
        segment = Path(str(chapter["source_segment"]))
        return segment.parent / "narration.en.txt"
    narration = chapter.get("narration")
    if not isinstance(narration, dict) or not isinstance(narration.get("path"), str):
        raise BuildError(f"chapter {chapter.get('id')} lacks narration metadata")
    return Path(narration["path"]).parent / "narration.en.txt"


def chapter_sound_effect(chapter: dict[str, Any], kind: str) -> Path | None:
    if kind != "gate":
        return None
    for source in chapter.get("sources", []):
        if isinstance(source, dict) and source.get("role") == "sound-effect":
            path = Path(str(source.get("path", "")))
            if path.is_file():
                return path
    raise BuildError(f"gate chapter {chapter.get('id')} lacks its sound effect")


def materialize_cues() -> list[Cue]:
    cues: list[Cue] = []
    for source_slice in source_slices():
        payload = load_json(source_slice.sidecar)
        chapters = payload.get("chapters")
        if not isinstance(chapters, list):
            raise BuildError(f"sidecar has no chapter list: {source_slice.sidecar}")
        selected: list[tuple[float, float, dict[str, Any]]] = []
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            start, end = chapter_times(chapter, source_slice.kind)
            if start >= source_slice.source_start - TOLERANCE and end <= source_slice.source_end + TOLERANCE:
                selected.append((start, end, chapter))
            elif start < source_slice.source_end - TOLERANCE and end > source_slice.source_start + TOLERANCE:
                raise BuildError(
                    f"slice {source_slice.label} cuts through chapter {chapter.get('id')}: "
                    f"{start:.6f}-{end:.6f}"
                )
        selected.sort(key=lambda row: row[0])
        if not selected:
            raise BuildError(f"slice {source_slice.label} selected no chapters")
        if abs(selected[0][0] - source_slice.source_start) > TOLERANCE:
            raise BuildError(f"slice {source_slice.label} does not begin on a chapter boundary")
        if abs(selected[-1][1] - source_slice.source_end) > TOLERANCE:
            raise BuildError(f"slice {source_slice.label} does not end on a chapter boundary")
        local_cursor = source_slice.source_start
        for start, end, chapter in selected:
            if abs(start - local_cursor) > TOLERANCE:
                raise BuildError(f"gap in source slice {source_slice.label} at {local_cursor:.6f}s")
            text_path = narration_text_path(chapter, source_slice.kind)
            if not text_path.is_file():
                raise BuildError(f"narration text is missing: {text_path}")
            text = text_path.read_text(encoding="utf-8-sig").strip()
            if not text:
                raise BuildError(f"narration text is empty: {text_path}")
            output_start = source_slice.output_start + start - source_slice.source_start
            output_end = source_slice.output_start + end - source_slice.source_start
            cues.append(
                Cue(
                    index=len(cues),
                    cue_id=str(chapter.get("id", f"cue-{len(cues):03d}")),
                    text=text,
                    start=output_start,
                    end=output_end,
                    narration_delay=12.0 if source_slice.kind == "gate" else 0.0,
                    sound_effect=chapter_sound_effect(chapter, source_slice.kind),
                    source_label=source_slice.label,
                )
            )
            local_cursor = end

    for previous, current in zip(cues, cues[1:]):
        if abs(previous.end - current.start) > TOLERANCE:
            raise BuildError(
                f"final cue timeline is not contiguous: {previous.cue_id} ends "
                f"{previous.end:.6f}, {current.cue_id} starts {current.start:.6f}"
            )
    if not cues or abs(cues[0].start) > TOLERANCE or abs(cues[-1].end - TOTAL_SECONDS) > TOLERANCE:
        raise BuildError("final cue timeline does not cover the complete r9 frame range")
    return cues


def overlay_narration_manifest(
    cues: Sequence[Cue], *, manifest_path: Path, source_label: str
) -> list[Cue]:
    """Replace one source slice's cue ids/text without changing the old timeline.

    R11 rebuilds the picture from clean manifests, but its natural-voice cache
    deliberately retains the stable 98-slot numbering established by R10.
    This overlay lets revised narration be synthesized into those same slots
    without remuxing the obsolete R9 picture lock.
    """

    payload = load_json(manifest_path)
    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise BuildError(f"narration manifest has no chapters: {manifest_path}")
    replacements: list[tuple[str, str]] = []
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            raise BuildError(f"narration manifest chapter {index} is not an object")
        cue_id = chapter.get("id")
        text = chapter.get("narration_en")
        if not isinstance(cue_id, str) or not cue_id.strip():
            raise BuildError(f"narration manifest chapter {index} lacks an id")
        if not isinstance(text, str) or not text.strip():
            raise BuildError(f"narration manifest chapter {cue_id} lacks narration_en")
        replacements.append((cue_id.strip(), text.strip()))

    positions = [index for index, cue in enumerate(cues) if cue.source_label == source_label]
    if len(positions) != len(replacements):
        raise BuildError(
            f"narration overlay has {len(replacements)} chapters but source slice "
            f"{source_label} has {len(positions)} slots"
        )
    result = list(cues)
    for position, (cue_id, text) in zip(positions, replacements):
        old = result[position]
        result[position] = Cue(
            index=old.index,
            cue_id=cue_id,
            text=text,
            start=old.start,
            end=old.end,
            narration_delay=old.narration_delay,
            sound_effect=old.sound_effect,
            source_label=old.source_label,
        )
    return result


def git_revision(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def synthesize_cues(
    cues: Iterable[Cue],
    *,
    index_repo: Path,
    model_dir: Path,
    voice_reference: Path,
    generated_dir: Path,
    force: bool,
) -> None:
    cues = list(cues)
    reference_hash = sha256(voice_reference)
    model_revision = git_revision(index_repo)
    pending: list[tuple[Cue, Path, Path, str]] = []
    for cue in cues:
        stem = f"{cue.index:03d}-{safe_slug(cue.cue_id)}"
        wav = generated_dir / f"{stem}.wav"
        metadata = generated_dir / f"{stem}.json"
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "format": 1,
                    "text": cue.text,
                    "reference_sha256": reference_hash,
                    "model_revision": model_revision,
                    "mode": "natural-reference-emotion",
                    "language": "ZH",
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest().upper()
        cached = False
        if not force and wav.is_file() and metadata.is_file():
            try:
                cache = load_json(metadata)
                cached = cache.get("fingerprint") == fingerprint and cache.get("wav_sha256") == sha256(wav)
            except BuildError:
                cached = False
        if cached:
            print(f"REUSE TTS {cue.index + 1:02d}/{len(cues)}: {cue.cue_id}", flush=True)
        else:
            pending.append((cue, wav, metadata, fingerprint))

    if not pending:
        return
    sys.path.insert(0, str(index_repo))
    try:
        module = importlib.import_module("indextts.infer_v2_5")
        IndexTTS2 = module.IndexTTS2
    except Exception as exc:
        raise BuildError(f"cannot import IndexTTS 2.5 from {index_repo}: {exc}") from exc

    print(f"LOAD INDEXTTS: {model_dir}", flush=True)
    tts = IndexTTS2(
        cfg_path=str(model_dir / "config.yaml"),
        model_dir=str(model_dir),
        use_bf16=True,
        use_cuda_kernel=False,
        use_torch_compile=False,
        use_qwen_emo=False,
    )
    for position, (cue, wav, metadata, fingerprint) in enumerate(pending, start=1):
        print(
            f"SYNTH {position:02d}/{len(pending)} (timeline {cue.index + 1:02d}/{len(cues)}): "
            f"{cue.cue_id}",
            flush=True,
        )
        temporary = wav.with_name(f".{wav.stem}.{os.getpid()}.partial.wav")
        temporary.unlink(missing_ok=True)
        tts.infer(
            spk_audio_prompt=str(voice_reference),
            text=cue.text,
            lang="ZH",
            output_path=str(temporary),
            verbose=False,
            text_normalization=True,
        )
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise BuildError(f"IndexTTS produced no audio for {cue.cue_id}")
        os.replace(temporary, wav)
        payload = {
            "format_version": 1,
            "fingerprint": fingerprint,
            "cue_id": cue.cue_id,
            "provider": "IndexTTS-2.5",
            "mode": "natural-reference-emotion",
            "model_revision": model_revision,
            "reference_sha256": reference_hash,
            "text_sha256": hashlib.sha256(cue.text.encode("utf-8")).hexdigest().upper(),
            "wav_sha256": sha256(wav),
        }
        metadata.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_audio_track(
    cues: Sequence[Cue],
    *,
    ffmpeg: str,
    ffprobe: str,
    generated_dir: Path,
    slots_dir: Path,
    work_dir: Path,
    force: bool,
) -> tuple[Path, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    slot_paths: list[Path] = []
    for cue in cues:
        stem = f"{cue.index:03d}-{safe_slug(cue.cue_id)}"
        narration = generated_dir / f"{stem}.wav"
        slot = slots_dir / f"{cue.index:03d}.wav"
        narration_duration = probe_duration(ffprobe, narration)
        available = cue.duration - cue.narration_delay - 0.25
        if available <= 0:
            raise BuildError(f"cue {cue.cue_id} has no room for narration")
        tempo = max(1.0, narration_duration / available)
        if tempo > 1.65:
            raise BuildError(
                f"cue {cue.cue_id} requires excessive speed-up {tempo:.3f}x "
                f"({narration_duration:.3f}s into {available:.3f}s)"
            )
        rows.append(
            {
                "index": cue.index,
                "id": cue.cue_id,
                "start_seconds": round(cue.start, 6),
                "end_seconds": round(cue.end, 6),
                "slot_seconds": round(cue.duration, 6),
                "narration_seconds": round(narration_duration, 6),
                "narration_delay_seconds": cue.narration_delay,
                "fit_tempo": round(tempo, 6),
                "source": cue.source_label,
            }
        )
        slot_paths.append(slot)
        if slot.is_file() and not force and slot.stat().st_mtime_ns >= narration.stat().st_mtime_ns:
            print(f"REUSE SLOT {cue.index + 1:02d}/{len(cues)}: {cue.cue_id}", flush=True)
            continue

        voice_filters: list[str] = []
        if tempo > 1.001:
            voice_filters.append(
                f"rubberband=tempo={tempo:.8f}:pitch=1:formant=preserved:"
                "transients=smooth:detector=soft:pitchq=quality"
            )
        voice_filters.extend(
            [
                "volume=-2dB",
                "aresample=48000",
                "aformat=sample_fmts=s16:channel_layouts=stereo",
            ]
        )
        if cue.narration_delay > 0:
            voice_filters.append(f"adelay={int(round(cue.narration_delay * 1000))}:all=1")
        voice_filters.extend(["apad", f"atrim=duration={cue.duration:.8f}", "asetpts=PTS-STARTPTS"])

        temporary = slot.with_name(f".{slot.stem}.{os.getpid()}.partial.wav")
        temporary.unlink(missing_ok=True)
        command: list[str | Path] = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", narration]
        if cue.sound_effect is None:
            command.extend(
                [
                    "-af",
                    ",".join(voice_filters),
                    "-t",
                    f"{cue.duration:.8f}",
                    "-c:a",
                    "pcm_s16le",
                    temporary,
                ]
            )
        else:
            command.extend(["-i", cue.sound_effect])
            graph = (
                f"[0:a]{','.join(voice_filters)}[voice];"
                f"[1:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,"
                f"apad,atrim=duration={cue.duration:.8f},asetpts=PTS-STARTPTS[fx];"
                f"[voice][fx]amix=inputs=2:duration=longest:normalize=0,"
                f"alimiter=limit=0.95,atrim=duration={cue.duration:.8f}[a]"
            )
            command.extend(
                [
                    "-filter_complex",
                    graph,
                    "-map",
                    "[a]",
                    "-t",
                    f"{cue.duration:.8f}",
                    "-c:a",
                    "pcm_s16le",
                    temporary,
                ]
            )
        run(command)
        os.replace(temporary, slot)

    concat = work_dir / "owner-voice-slots.ffconcat"
    concat.write_text(
        "ffconcat version 1.0\n"
        + "".join(f"file '{path.resolve().as_posix()}'\n" for path in slot_paths),
        encoding="utf-8",
    )
    raw_track = work_dir / "project-causality-owner-voice-raw.wav"
    normalized_track = work_dir / "project-causality-owner-voice-master.wav"
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat,
            "-t",
            f"{TOTAL_SECONDS:.8f}",
            "-c:a",
            "pcm_s16le",
            raw_track,
        ]
    )
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            raw_track,
            "-af",
            "loudnorm=I=-16:LRA=7:TP=-1.5,aresample=48000",
            "-t",
            f"{TOTAL_SECONDS:.8f}",
            "-c:a",
            "pcm_s24le",
            normalized_track,
        ]
    )
    return normalized_track, rows


def remux(
    *,
    ffmpeg: str,
    ffprobe: str,
    picture: Path,
    audio_track: Path,
    output: Path,
) -> dict[str, Any]:
    temporary = output.with_name(f".{output.stem}.{os.getpid()}.partial.mp4")
    temporary.unlink(missing_ok=True)
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            picture,
            "-i",
            audio_track,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-metadata:s:a:0",
            "language=zho",
            "-t",
            f"{TOTAL_SECONDS:.8f}",
            "-movflags",
            "+faststart",
            temporary,
        ]
    )
    os.replace(temporary, output)
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            output,
        ],
        capture=True,
    )
    payload = json.loads(result.stdout)
    video = next(row for row in payload["streams"] if row.get("codec_type") == "video")
    audio = next(row for row in payload["streams"] if row.get("codec_type") == "audio")
    frames = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    if frames != TOTAL_FRAMES:
        raise BuildError(f"final video has {frames} frames; expected {TOTAL_FRAMES}")
    if (video.get("width"), video.get("height")) != (2560, 1440):
        raise BuildError("final video geometry changed")
    if video.get("codec_name") != "h264" or audio.get("codec_name") != "aac":
        raise BuildError("final codecs are not H.264/AAC")
    return {
        "duration_seconds": float(payload["format"]["duration"]),
        "frames": frames,
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("avg_frame_rate"),
        "video_codec": video.get("codec_name"),
        "video_profile": video.get("profile"),
        "pixel_format": video.get("pix_fmt"),
        "audio_codec": audio.get("codec_name"),
        "sample_rate": int(audio.get("sample_rate", 0)),
        "channels": audio.get("channels"),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--index-repo", type=Path, required=True)
    result.add_argument("--model-dir", type=Path)
    result.add_argument("--voice-reference", type=Path, required=True)
    result.add_argument("--picture", type=Path, default=DEFAULT_PICTURE)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    result.add_argument("--output", type=Path)
    result.add_argument("--force", action="store_true")
    result.add_argument("--plan-only", action="store_true")
    result.add_argument(
        "--narration-manifest",
        type=Path,
        help="overlay cue ids and narration_en for the fresh Robert source slice",
    )
    result.add_argument(
        "--synthesize-only",
        action="store_true",
        help="update the natural WAV cache without rebuilding the obsolete R10 picture lock",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.index_repo = args.index_repo.expanduser().resolve()
    args.model_dir = (args.model_dir or args.index_repo / "checkpoints").expanduser().resolve()
    args.voice_reference = args.voice_reference.expanduser().resolve()
    args.narration_manifest = (
        args.narration_manifest.expanduser().resolve()
        if args.narration_manifest
        else None
    )
    args.picture = args.picture.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.output = (args.output or args.output_dir / "project-causality-r10-owner-voice-nomusic.mp4").expanduser().resolve()

    for path, label in [
        (args.index_repo / "indextts/infer_v2_5.py", "IndexTTS 2.5 source"),
        (args.model_dir / "config.yaml", "IndexTTS model config"),
        (args.voice_reference, "authorized voice reference"),
        (args.picture, "r9 picture lock"),
        (R7_SIDECAR, "r7 chapter sidecar"),
        (VALUE_SIDECAR, "value-showcase sidecar"),
        (GATE_SIDECAR, "chapter-gate sidecar"),
        (AGENT_SIDECAR, "r9 agent sidecar"),
    ]:
        if not path.is_file():
            raise BuildError(f"{label} is missing: {path}")

    cues = materialize_cues()
    if args.narration_manifest is not None:
        if not args.narration_manifest.is_file():
            raise BuildError(f"narration manifest is missing: {args.narration_manifest}")
        cues = overlay_narration_manifest(
            cues,
            manifest_path=args.narration_manifest,
            source_label="fresh-robert-agent",
        )
    print(
        f"PLAN: {len(cues)} complete cues, {TOTAL_FRAMES} frames, "
        f"{TOTAL_SECONDS:.6f}s",
        flush=True,
    )
    if args.plan_only:
        return 0

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise BuildError("ffmpeg and ffprobe are required")
    generated_dir = args.output_dir / "work/generated-cues"
    slots_dir = args.output_dir / "work/audio-slots-rubberband"
    work_dir = args.output_dir / "work"
    generated_dir.mkdir(parents=True, exist_ok=True)
    slots_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    synthesize_cues(
        cues,
        index_repo=args.index_repo,
        model_dir=args.model_dir,
        voice_reference=args.voice_reference,
        generated_dir=generated_dir,
        force=args.force,
    )
    if args.synthesize_only:
        print(f"SYNTHESIS CACHE: {generated_dir}", flush=True)
        return 0
    track, cue_rows = render_audio_track(
        cues,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        generated_dir=generated_dir,
        slots_dir=slots_dir,
        work_dir=work_dir,
        force=args.force,
    )
    media = remux(
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        picture=args.picture,
        audio_track=track,
        output=args.output,
    )
    sidecar = args.output.with_suffix(".video.json")
    sidecar_payload = {
        "schema": "project-causality-owner-voice-video.v1",
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "status": "owner-voice-non-music-review-candidate",
        "publication_authorized": False,
        "picture_source": {
            "path": str(args.picture),
            "sha256": sha256(args.picture),
            "video_stream_copied": True,
        },
        "narration": {
            "provider": "IndexTTS-2.5",
            "mode": "natural-reference-emotion",
            "model_revision": git_revision(args.index_repo),
            "authorized_reference_sha256": sha256(args.voice_reference),
            "reference_path_private": True,
            "cue_count": len(cues),
            "master_track": str(track),
            "master_track_sha256": sha256(track),
            "target_integrated_loudness_lufs": -16,
            "target_true_peak_dbfs": -1.5,
        },
        "music": {"included": False, "suno_operated": False},
        "video": {
            "path": str(args.output),
            "sha256": sha256(args.output),
            "bytes": args.output.stat().st_size,
            **media,
        },
        "cues": cue_rows,
    }
    sidecar.write_text(json.dumps(sidecar_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VIDEO: {args.output}", flush=True)
    print(f"SIDECAR: {sidecar}", flush=True)
    print(f"SHA256: {sidecar_payload['video']['sha256']}", flush=True)
    print(f"DURATION: {media['duration_seconds']:.3f}s", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
