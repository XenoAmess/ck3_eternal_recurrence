"""Synthesize a frozen war-film script with the Project Causality IndexTTS profile.

Each invocation owns a new, retained attempt directory. A later attempt may
import verified completed cues from an earlier attempt without rewriting it.
"""

from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import wave


PROFILE = {
    "provider": "IndexTTS-2.5",
    "mode": "natural-reference-emotion",
    "language": "ZH",
    "duration_factor": 0.90,
    "interval_silence_ms": 100,
    "text_normalization": True,
    "use_bf16": True,
    "use_qwen_emo": False,
    "use_cuda_kernel": False,
    "use_torch_compile": False,
}


def binding(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 * 1024 * 1024):
            digest.update(data)
    return {"path": path.resolve().as_posix(), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def write_new(path: Path, value: dict | list) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def probe_wav(path: Path) -> dict:
    with wave.open(str(path), "rb") as stream:
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError(f"Expected mono PCM16: {path}")
        rate, frames = stream.getframerate(), stream.getnframes()
        pcm = array("h")
        pcm.frombytes(stream.readframes(frames))
    if rate != 22050 or frames == 0 or not pcm:
        raise ValueError(f"Expected nonempty 22.05 kHz IndexTTS WAV: {path}")
    if sys.byteorder != "little":
        pcm.byteswap()
    peak = max(abs(sample) for sample in pcm)
    if peak < 32:
        raise ValueError(f"Generated audio is nearly silent: {path}")
    return {"sample_rate": rate, "channels": 1, "frames": frames,
            "duration_seconds": frames / rate, "peak_pcm16": peak}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--index-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reuse-from", type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    args.inputs = args.inputs.resolve()
    args.reference = args.reference.resolve()
    args.index_root = args.index_root.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.reuse_from:
        args.reuse_from = args.reuse_from.resolve()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    for path in (args.inputs, args.reference, args.index_root / "checkpoints/config.yaml"):
        if not path.is_file():
            raise FileNotFoundError(path)
    source = json.loads(args.inputs.read_text(encoding="utf-8"))
    cues = source["cues"][:args.limit]
    if not cues or len({cue["id"] for cue in cues}) != len(cues):
        raise ValueError("Expected nonempty unique cue IDs")
    if any(not cue["zh"].strip() or not cue["id"].startswith("V3-") for cue in cues):
        raise ValueError("Missing narration or wrong script version")
    revision = subprocess.check_output(["git", "-C", str(args.index_root), "rev-parse", "HEAD"], text=True).strip()
    reference = binding(args.reference)
    identity = {"profile": PROFILE, "model_revision": revision,
                "model_config": binding(args.index_root / "checkpoints/config.yaml"),
                "reference": reference, "inputs": binding(args.inputs)}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_new(args.output_dir / "request.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), **identity,
        "cue_ids": [cue["id"] for cue in cues],
        "reuse_from": args.reuse_from.as_posix() if args.reuse_from else None,
        "state": "started"})
    pending = []
    for cue in cues:
        target = args.output_dir / (cue["id"] + ".wav")
        expected = {"id": cue["id"], "text_sha256": hashlib.sha256(cue["zh"].encode("utf-8")).hexdigest(),
                    "reference_sha256": reference["sha256"], "model_revision": revision, "profile": PROFILE}
        write_new(args.output_dir / (cue["id"] + ".request.json"), expected)
        former = args.reuse_from / (cue["id"] + ".wav") if args.reuse_from else None
        former_receipt = args.reuse_from / (cue["id"] + ".receipt.json") if args.reuse_from else None
        if former and former.is_file() and former_receipt.is_file():
            receipt = json.loads(former_receipt.read_text(encoding="utf-8"))
            if any(receipt.get(key) != value for key, value in expected.items()):
                raise ValueError(f"Previous attempt does not match current request: {cue['id']}")
            if receipt["audio"]["sha256"] != binding(former)["sha256"]:
                raise ValueError(f"Previous audio changed: {cue['id']}")
            shutil.copyfile(former, target)
            write_new(args.output_dir / (cue["id"] + ".receipt.json"),
                      {**expected, "audio": binding(target), "wave": probe_wav(target),
                       "reused_from": binding(former)})
            print(f"REUSE {cue['id']}", flush=True)
        else:
            pending.append((cue, target, expected))
    if pending:
        sys.path.insert(0, str(args.index_root))
        IndexTTS2 = importlib.import_module("indextts.infer_v2_5").IndexTTS2
        print(f"LOAD INDEXTTS {revision} on CUDA for {len(pending)} cues", flush=True)
        started = time.perf_counter()
        tts = IndexTTS2(cfg_path=str(args.index_root / "checkpoints/config.yaml"),
                        model_dir=str(args.index_root / "checkpoints"),
                        device="cuda:0", use_bf16=True, use_cuda_kernel=False,
                        use_deepspeed=False, use_accel=False, use_torch_compile=False,
                        use_qwen_emo=False)
        print(f"MODEL READY {time.perf_counter() - started:.1f}s", flush=True)
        for position, (cue, target, expected) in enumerate(pending, 1):
            partial = args.output_dir / (cue["id"] + ".partial.wav")
            if partial.exists():
                raise FileExistsError(partial)
            print(f"SYNTH {position}/{len(pending)} {cue['id']}", flush=True)
            began = time.perf_counter()
            try:
                tts.infer(spk_audio_prompt=str(args.reference), text=cue["zh"],
                          lang="ZH", output_path=str(partial), verbose=False,
                          duration_factor=0.90, interval_silence=100,
                          text_normalization=True)
                info = probe_wav(partial)
                os.replace(partial, target)
                write_new(args.output_dir / (cue["id"] + ".receipt.json"),
                          {**expected, "audio": binding(target), "wave": info,
                           "inference_seconds": time.perf_counter() - began,
                           "completed_at_utc": datetime.now(timezone.utc).isoformat()})
                print(f"DONE {cue['id']} {info['duration_seconds']:.3f}s speech", flush=True)
            except Exception as error:
                write_new(args.output_dir / (cue["id"] + ".failure.json"),
                          {"type": type(error).__name__, "detail": str(error),
                           "partial": binding(partial) if partial.exists() else None})
                raise
    outputs = [json.loads((args.output_dir / (cue["id"] + ".receipt.json")).read_text(encoding="utf-8"))
               for cue in cues]
    write_new(args.output_dir / "completed.json", {
        "state": "synthesized", "identity": identity, "cues": outputs,
        "total_speech_seconds": sum(item["wave"]["duration_seconds"] for item in outputs),
        "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    print(f"COMPLETE {len(outputs)} cues", flush=True)


if __name__ == "__main__":
    main()
