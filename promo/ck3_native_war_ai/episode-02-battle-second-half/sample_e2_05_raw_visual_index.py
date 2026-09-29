"""Extract sparse E2-05 review stills with source frame PTS and frozen provenance.

This is only a navigation aid; it never certifies a clean span or event fact.
Wait for the managed CK3/cash screen session to release before running it.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import shutil
import struct
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


SHOWINFO_FRAME = re.compile(r"\bn:\s*(\d+)\b.*?\bpts_time:([0-9]+(?:\.[0-9]+)?)")
ATTEMPT_NAME = re.compile(r"episode02-e2-05-a02-visual-index-20260929-a\d{2}\Z")
EXTERNAL_PARENT = Path("D:/workspace/ck3_native_war_ai_promo_work")
EXPECTED_LINK_SHA256 = "213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C"
EXPECTED_RAW_SHA256 = "7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F"
EXPECTED_FFPROBE_SHA256 = "06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def file_identity(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def write_new_json(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def validate_output_directory(output: Path, external_parent: Path, protected: list[Path]) -> None:
    if not output.is_absolute():
        raise ValueError("output must be an absolute external attempt path")
    parent = output.parent.resolve(strict=True)
    external = external_parent.resolve(strict=True)
    if parent != external or not ATTEMPT_NAME.fullmatch(output.name):
        raise ValueError("output must be a new named child of the external promo work root")
    if output.exists():
        raise ValueError("output already exists; do not overwrite an attempt")
    for source in protected:
        root = source.resolve(strict=True)
        if output == root or root in output.parents:
            raise ValueError(f"output is inside a protected source tree: {root}")


def unique_showinfo_pts(stderr_bytes: bytes) -> Decimal:
    records = []
    for line in stderr_bytes.decode("utf-8", errors="replace").splitlines():
        if "showinfo" not in line:
            continue
        match = SHOWINFO_FRAME.search(line)
        if match:
            records.append((int(match.group(1)), Decimal(match.group(2))))
    if len(records) != 1 or records[0][0] != 0:
        raise ValueError(f"expected exactly one showinfo n:0 output frame, got {records}")
    return records[0][1]


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])


def pinned_source(path: Path, row: dict, stat: dict) -> None:
    if path != Path(row["path"]).resolve(strict=True):
        raise ValueError(f"source path differs from frozen link: {path}")
    current = path.stat()
    if current.st_size != row["bytes"] or current.st_size != stat["bytes"]:
        raise ValueError(f"source size differs from frozen link: {path}")
    if current.st_mtime_ns != stat["mtime_ns"]:
        raise ValueError(f"source mtime differs from frozen link: {path}")


def stat_snapshot(path: Path) -> dict[str, int] | None:
    try:
        current = path.stat()
    except OSError:
        return None
    return {"bytes": current.st_size, "mtime_ns": current.st_mtime_ns}


def probe_video_pts(path: Path) -> tuple[list[Decimal], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    strings = [frame["best_effort_timestamp_time"] for frame in data["frames"]
               if frame.get("media_type", "video") == "video"
               and frame.get("best_effort_timestamp_time")]
    values = [Decimal(value) for value in strings]
    if not values or any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("frozen ffprobe video PTS is missing or nonmonotonic")
    return values, strings


def match_probe_pts(value: Decimal, values: list[Decimal], strings: list[str]) -> str:
    index = bisect.bisect_left(values, value)
    candidates = [candidate for candidate in (index - 1, index) if 0 <= candidate < len(values)]
    best = min(candidates, key=lambda candidate: abs(values[candidate] - value))
    if abs(values[best] - value) > Decimal("0.001"):
        raise ValueError(f"FFmpeg PTS {value} has no exact frozen ffprobe match")
    return strings[best]


def seek_text(value: Decimal) -> str:
    """Canonicalize the frozen probe's six-decimal PTS without context rounding."""
    if not value.is_finite() or value < 0 or value >= 600:
        raise ValueError("seek must be a finite source second in [0, 600)")
    number = value.as_tuple()
    if number.exponent < -6 or number.exponent > 2 or len(number.digits) > 9:
        raise ValueError("seek exceeds six fractional digits or source PTS width")
    if value.is_zero():
        return "0"
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    if len(result) > 10:
        raise ValueError("seek text exceeds frozen PTS width")
    return result


def seek_label(value: Decimal) -> str:
    whole, dot, fraction = seek_text(value).partition(".")
    return whole.zfill(3) + (f"p{fraction}" if dot else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postrun-links", required=True, type=Path)
    parser.add_argument("--postrun-links-sha256", required=True)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--ffprobe-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seek", action="append", required=True, type=Decimal,
                        help="repeat for each requested exact source PTS in seconds")
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg not found")
    try:
        seek_texts = [seek_text(value) for value in args.seek]
    except ValueError as exc:
        parser.error(str(exc))
    if len(set(seek_texts)) != len(seek_texts):
        parser.error("seek values must have distinct canonical PTS and filenames")

    links_path = args.postrun_links.resolve(strict=True)
    if args.postrun_links_sha256.upper() != EXPECTED_LINK_SHA256 or \
            sha256(links_path) != EXPECTED_LINK_SHA256:
        raise ValueError("postrun link bytes do not match the E2-05 a02 frozen SHA-256")
    links = json.loads(links_path.read_text(encoding="utf-8"))
    if links.get("result") != "MEDIA_PTS_CANDIDATE_UNREVIEWED":
        raise ValueError("unexpected frozen postrun link status")
    if links["raw_from_prior_full_sha_audit"]["sha256"] != EXPECTED_RAW_SHA256 or \
            links["ffprobe_from_prior_full_sha_audit"]["sha256"] != EXPECTED_FFPROBE_SHA256:
        raise ValueError("postrun link does not bind the exact E2-05 a02 raw and ffprobe")
    raw = args.raw.resolve(strict=True)
    probe = args.ffprobe_json.resolve(strict=True)
    validate_output_directory(args.output, EXTERNAL_PARENT,
                              [raw, raw.parents[2], probe, links_path.parent,
                               Path(__file__).resolve().parents[3]])
    pinned_source(raw, links["raw_from_prior_full_sha_audit"], links["raw_stat_during_link_audit"])
    pinned_source(probe, links["ffprobe_from_prior_full_sha_audit"],
                  links["ffprobe_stat_during_link_audit"])
    if sha256(probe) != links["ffprobe_from_prior_full_sha_audit"]["sha256"]:
        raise ValueError("frozen ffprobe content changed")
    if links["video_pts_summary"]["missing_pts_count"] != 0 or \
            links["video_pts_summary"]["nonmonotonic_count"] != 0 or \
            links["video_pts_summary"]["gap_count"] != 0:
        raise ValueError("frozen PTS audit is not continuous")
    pts_values, pts_strings = probe_video_pts(probe)

    args.output.mkdir(parents=True)
    intent = {
        "schema": "xar.war-promo.e2-05-sparse-visual-intent/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SPARSE_VISUAL_CANDIDATE_UNREVIEWED",
        "postrun_links": file_identity(links_path),
        "raw": links["raw_from_prior_full_sha_audit"],
        "raw_rehashed_by_sampler": False,
        "ffprobe": links["ffprobe_from_prior_full_sha_audit"],
        "requested_seek_seconds": [seek_text(value) for value in args.seek],
        "full_speed_human_review": False,
        "clean_spans_certified": False,
    }
    write_new_json(args.output / "intent.json", intent)
    samples = []
    for second in args.seek:
        label = seek_label(second)
        still = args.output / f"seek-{label}.png"
        stdout_path = args.output / f"seek-{label}.ffmpeg.stdout.bin"
        stderr_path = args.output / f"seek-{label}.ffmpeg.stderr.bin"
        step_intent_path = args.output / f"seek-{label}.intent.json"
        step_exit_path = args.output / f"seek-{label}.exit.json"
        argv = [ffmpeg, "-hide_banner", "-loglevel", "info", "-nostdin", "-n",
                "-threads", "1", "-filter_threads", "1", "-ss", seek_text(second),
                "-copyts", "-i", str(raw), "-map", "0:v:0", "-an",
                # FFmpeg may decode one extra frame before -frames:v stops the
                # output. Select the first frame before showinfo so its log
                # names exactly the frame written to the PNG.
                "-vf", r"select=eq(n\,0),showinfo", "-frames:v", "1", "-compression_level", "1",
                str(still)]
        write_new_json(step_intent_path, {
            "schema": "xar.war-promo.e2-05-sparse-seek-intent/v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "requested_seek_seconds": seek_text(second),
            "argv": argv,
            "raw_frozen_identity": links["raw_from_prior_full_sha_audit"],
            "raw_rehash_performed": False,
        })
        exit_code = None
        measured = None
        matched = None
        dimensions = None
        errors = []
        raw_before = stat_snapshot(raw)
        # The exact byte streams exist even if launch or validation fails.
        with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
            try:
                pinned_source(raw, links["raw_from_prior_full_sha_audit"],
                              links["raw_stat_during_link_audit"])
                completed = subprocess.run(argv, stdout=stdout_stream, stderr=stderr_stream,
                                           check=False)
                exit_code = completed.returncode
            except BaseException as exc:
                errors.append(f"launch_or_source_before: {type(exc).__name__}: {exc}")
        raw_after = stat_snapshot(raw)
        try:
            pinned_source(raw, links["raw_from_prior_full_sha_audit"],
                          links["raw_stat_during_link_audit"])
        except Exception as exc:
            errors.append(f"source_after: {type(exc).__name__}: {exc}")
        if exit_code is None or exit_code != 0 or not still.is_file():
            errors.append(f"ffmpeg_exit_or_png_missing: exit_code={exit_code}, png={still.is_file()}")
        if not errors:
            try:
                measured = unique_showinfo_pts(stderr_path.read_bytes())
                if abs(measured - second) > Decimal("0.5"):
                    raise ValueError(f"seek {second} decoded distant frame {measured}")
                matched = match_probe_pts(measured, pts_values, pts_strings)
                dimensions = png_dimensions(still)
                if dimensions != (2560, 1440):
                    raise ValueError(f"PNG geometry {dimensions} differs from raw")
            except Exception as exc:
                errors.append(f"pts_or_png: {type(exc).__name__}: {exc}")
        step_exit = {
            "schema": "xar.war-promo.e2-05-sparse-seek-exit/v1",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "result": "RED_PARTIAL_PRESERVED" if errors else "SPARSE_SAMPLE_UNREVIEWED",
            "requested_seek_seconds": seek_text(second),
            "ffmpeg_exit_code": exit_code,
            "raw_stat_before": raw_before,
            "raw_stat_after": raw_after,
            "ffmpeg_stdout": file_identity(stdout_path),
            "ffmpeg_stderr": file_identity(stderr_path),
            "png_or_partial": file_identity(still) if still.is_file() else None,
            "png_dimensions": dimensions,
            "ffmpeg_showinfo_pts_seconds": str(measured) if measured is not None else None,
            "frozen_ffprobe_frame_pts_seconds": matched,
            "errors": errors,
            "argv": argv,
        }
        write_new_json(step_exit_path, step_exit)
        if errors:
            raise RuntimeError(f"seek {second} RED; exact logs and partial preserved at {step_exit_path}")
        samples.append({
            "requested_seek_seconds": seek_text(second),
            "ffmpeg_showinfo_pts_seconds": str(measured),
            "frozen_ffprobe_frame_pts_seconds": matched,
            "still": file_identity(still),
            "png_width": dimensions[0],
            "png_height": dimensions[1],
            "seek_intent": file_identity(step_intent_path),
            "seek_exit": file_identity(step_exit_path),
            "ffmpeg_stdout": file_identity(stdout_path),
            "ffmpeg_stderr": file_identity(stderr_path),
            "ffmpeg_exit_code": exit_code,
            "argv": argv,
        })
    final_errors = []
    for label, source, row, snapshot in (
        ("raw", raw, links["raw_from_prior_full_sha_audit"], links["raw_stat_during_link_audit"]),
        ("ffprobe", probe, links["ffprobe_from_prior_full_sha_audit"],
         links["ffprobe_stat_during_link_audit"]),
    ):
        try:
            pinned_source(source, row, snapshot)
        except Exception as exc:
            final_errors.append(f"{label}: {type(exc).__name__}: {exc}")
    write_new_json(args.output / "final-source-audit.json", {
        "schema": "xar.war-promo.e2-05-sparse-final-source-audit/v1",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "RED_SOURCE_DRIFT" if final_errors else "STABLE_STAT_ONLY",
        "raw": stat_snapshot(raw),
        "ffprobe": stat_snapshot(probe),
        "raw_rehash_performed": False,
        "errors": final_errors,
    })
    if final_errors:
        raise RuntimeError("source stat drift after final seek; partial attempt preserved")
    index = {**intent, "schema": "xar.war-promo.e2-05-sparse-visual-index/v1",
             "completed_at_utc": datetime.now(timezone.utc).isoformat(),
             "final_source_audit": file_identity(args.output / "final-source-audit.json"),
             "samples": samples}
    write_new_json(args.output / "sample-index.json", index)
    print(args.output / "sample-index.json")


if __name__ == "__main__":
    main()
