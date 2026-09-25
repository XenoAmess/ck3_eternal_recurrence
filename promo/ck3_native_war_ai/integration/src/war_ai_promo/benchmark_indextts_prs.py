"""Measure one real IndexTTS-2.5 CUDA synthesis with a pinned source tree."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import wave


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-device", choices=("cpu", "cuda:0"))
    parser.add_argument("--reuse-spk-cond-for-emo", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    model_dir = args.model_dir.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or Path(str(output) + ".json").exists() or not output.parent.is_dir():
        parser.error("output and receipt must be absent; parent directory must exist")
    os.environ.setdefault("HF_HOME", str(model_dir.parent / ".cache" / "huggingface"))
    os.environ.setdefault("TORCH_HOME", str(model_dir.parent / ".cache" / "torch"))
    os.environ.setdefault("NLTK_DATA", str(model_dir.parent / ".cache" / "nltk_data"))
    os.chdir(source)
    sys.path.insert(0, str(source))
    import numpy as np
    import torch
    from indextts.infer_v2_5 import IndexTTS2

    text = "战宽是一千二百六十九，当前参战兵力是二千三百二十四。原版先算战宽比例，再逐日结算伤亡。"
    seed = 20260925
    torch.set_num_threads(8)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.cuda.reset_peak_memory_stats()
    kwargs = dict(cfg_path=str(model_dir / "config.yaml"), model_dir=str(model_dir),
                  device="cuda:0", use_bf16=True, use_cuda_kernel=False,
                  use_deepspeed=False, use_accel=False, use_torch_compile=False, use_qwen_emo=False)
    if args.reference_device is not None:
        kwargs["reference_device"] = args.reference_device
    if args.reuse_spk_cond_for_emo:
        kwargs["reuse_spk_cond_for_emo"] = True
    start = time.perf_counter()
    model = IndexTTS2(**kwargs)
    torch.cuda.synchronize()
    load_end = time.perf_counter()
    print(json.dumps({"event": "model_ready", "model_load_seconds": load_end - start,
                      "source": str(source), "reference_device": args.reference_device,
                      "reuse_spk_cond_for_emo": args.reuse_spk_cond_for_emo}), flush=True)
    model.infer(spk_audio_prompt=str(reference), text=text, lang="ZH", output_path=str(output),
                duration_factor=1.0, verbose=False, max_text_tokens_per_segment=80)
    torch.cuda.synchronize()
    end = time.perf_counter()
    with wave.open(str(output), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
    if duration <= 0:
        raise ValueError("empty generated WAV")
    receipt = {"schema": "ck3-indextts-pr-benchmark.v1", "at_utc": datetime.now(timezone.utc).isoformat(),
               "source": str(source), "model_dir": str(model_dir), "reference": str(reference),
               "reference_sha256": sha(reference), "infer_source_sha256": sha(source / "indextts" / "infer_v2_5.py"),
               "text": text, "seed": seed, "device": "cuda:0", "use_bf16": True,
               "reference_device": args.reference_device or "cuda:0", "reuse_spk_cond_for_emo": args.reuse_spk_cond_for_emo,
               "model_load_seconds": load_end - start, "inference_seconds": end - load_end,
               "wav_duration_seconds": duration, "inference_rtf": (end - load_end) / duration,
               "wav_sha256": sha(output), "wav_bytes": output.stat().st_size,
               "sample_rate": sample_rate, "channels": channels,
               "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
               "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved(),
               "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda}
    Path(str(output) + ".json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "complete", **receipt}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
