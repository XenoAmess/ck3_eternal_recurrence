#!/usr/bin/env python3
"""Prime the reviewed Phase2 narration into the content-addressed TTS cache.

This is the only Phase2 command allowed to contact Edge TTS.  It validates the
fresh, cut-specific media preflight before any cache write.  The final builder
remains offline-only and can therefore never synthesize a missing cue silently.
``--validate-only`` computes the exact cache plan but performs no synthesis and
writes no cache or receipt bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402

ensure_promo_toolchain()

from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    build_narration_request,
    load_phase2_project_config,
)
from xar_promo.tts import TtsCache  # noqa: E402
from xar_promo.tts.edge import EdgeTtsProvider  # noqa: E402

from build_phase2_promo_video import (  # noqa: E402
    DEFAULT_EDGE_TTS_VERSION,
    _default_font,
    _require_ready_authoring,
    load_media_preflight_binding,
    select_cut,
)


KIND = "zg361_phase2_tts_cache_prime_receipt"


class CachePrimeError(RuntimeError):
    """The reviewed narration cache could not be honestly prepared."""


def _file_record(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def plan_or_prime(args: argparse.Namespace) -> dict[str, object]:
    config_path = args.project_config.expanduser().resolve()
    cut = select_cut(config_path, args.cut)
    config = load_phase2_project_config(config_path)
    _require_ready_authoring(config)
    media = load_media_preflight_binding(
        args.media_preflight_report,
        args.expected_media_preflight_sha256,
        project_config=config,
        project_config_path=config_path,
        edge_tts_version=args.edge_tts_version,
        ffmpeg=args.ffmpeg,
        ffprobe=args.ffprobe,
        zh_font_file=args.zh_font_file,
        en_font_file=args.en_font_file,
    )
    cache = TtsCache(args.tts_cache.expanduser().resolve())
    provider = EdgeTtsProvider(tool_version=args.edge_tts_version)
    if provider.identity.tool_version != DEFAULT_EDGE_TTS_VERSION:
        raise CachePrimeError(
            f"edge-tts {DEFAULT_EDGE_TTS_VERSION} is required; "
            f"got {provider.identity.tool_version}"
        )

    requests: list[tuple[str, str, object]] = []
    for chapter in config.chapters:
        for cue in chapter.cues:
            requests.append(
                (
                    chapter.chapter_id,
                    cue.cue_id,
                    build_narration_request(
                        cue.narration[config.narration_locale]
                    ),
                )
            )
    if not requests:
        raise CachePrimeError("ready Phase2 project contains no narration requests")

    rows: list[dict[str, object]] = []
    for chapter_id, cue_id, request in requests:
        fingerprint = cache.fingerprint(request, provider.identity)  # type: ignore[arg-type]
        row: dict[str, object] = {
            "chapter_id": chapter_id,
            "cue_id": cue_id,
            "fingerprint": fingerprint,
            "text_sha256": hashlib.sha256(request.text.encode("utf-8")).hexdigest().upper(),  # type: ignore[attr-defined]
        }
        if args.validate_only:
            existing = cache.lookup(request, provider.identity)  # type: ignore[arg-type]
            row["cache_state"] = "valid-hit" if existing is not None else "missing"
        else:
            entry = cache.get_or_create(
                request,  # type: ignore[arg-type]
                provider,
                offline=False,
                max_attempts=args.max_attempts,
                retry_backoff_seconds=args.retry_backoff_seconds,
            )
            row.update(
                {
                    "cache_state": "valid-hit" if entry.cache_hit else "synthesized",
                    "media": _file_record(entry.media_path),
                    "metadata": _file_record(entry.metadata_path),
                    "validation": entry.validation,
                }
            )
        rows.append(row)

    media.verify_unchanged()
    return {
        "schema_version": 1,
        "kind": KIND,
        "result": "GREEN",
        "cut_id": cut.cut_id,
        "project_config": _file_record(config_path),
        "media_preflight": media.to_mapping(),
        "tts_cache_root": str(args.tts_cache.expanduser().resolve()),
        "provider": {
            "id": provider.identity.provider_id,
            "tool_version": provider.identity.tool_version,
            "voice": requests[0][2].voice,  # type: ignore[attr-defined]
        },
        "entries": rows,
        "execution_attestation": {
            "validate_only": bool(args.validate_only),
            "network_synthesis_allowed": not args.validate_only,
            "synthesis_performed": (
                False
                if args.validate_only
                else any(row["cache_state"] == "synthesized" for row in rows)
            ),
            "ck3_started": False,
            "ffmpeg_started": False,
            "candidate_generated": False,
            "receipt_written": False,
        },
    }


def _write_new(path: Path, payload: Mapping[str, object]) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    if not resolved.parent.is_dir():
        raise CachePrimeError(f"receipt parent does not exist: {resolved.parent}")
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        with resolved.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise CachePrimeError(f"refusing to overwrite cache-prime receipt: {resolved}") from exc
    return _file_record(resolved)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--cut", required=True)
    result.add_argument("--project-config", type=Path, required=True)
    result.add_argument("--media-preflight-report", type=Path, required=True)
    result.add_argument("--expected-media-preflight-sha256", required=True)
    result.add_argument("--tts-cache", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--edge-tts-version", default=DEFAULT_EDGE_TTS_VERSION)
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    result.add_argument("--zh-font-file", type=Path, default=_default_font("msyh.ttc"))
    result.add_argument("--en-font-file", type=Path, default=_default_font("segoeui.ttf"))
    result.add_argument("--max-attempts", type=int, default=3)
    result.add_argument("--retry-backoff-seconds", type=float, default=1.0)
    result.add_argument("--validate-only", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = plan_or_prime(args)
        if args.validate_only:
            print(json.dumps(payload, ensure_ascii=False))
            return 0
        payload["execution_attestation"]["receipt_written"] = True
        receipt = _write_new(args.output, payload)
    except Exception as exc:
        print(f"PHASE2 TTS CACHE PRIME: RED\nERROR: {exc}", file=sys.stderr)
        return 2
    print("PHASE2 TTS CACHE PRIME: GREEN")
    print(f"RECEIPT: {receipt['path']} sha256={receipt['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
