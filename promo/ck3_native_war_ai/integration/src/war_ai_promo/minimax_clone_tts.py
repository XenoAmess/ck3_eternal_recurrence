"""Private-attempt MiniMax voice clone and cue-by-cue TTS for promo samples.

The API key is read only from MINIMAX_API_KEY and never enters argv or receipts.
All network request/response material remains outside the repository.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import subprocess
import urllib.error
import urllib.request


BASE = "https://api.minimax.cn/v1"
VOICE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{6,254}[A-Za-z0-9]$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def binding(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.resolve().as_posix(), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def api_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY is absent")
    return key


def request_json(path: str, body: bytes, content_type: str, key: str,
                 response_path: Path) -> dict:
    request = urllib.request.Request(
        BASE + path, data=body, method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            status, payload = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, payload = error.code, error.read()
    # The raw service response is retained privately; the Authorization header is not.
    write_new(response_path, {"http_status": status, "body": payload.decode("utf-8", "replace")})
    if status != 200:
        raise RuntimeError(f"MiniMax HTTP {status}; see private response receipt")
    value = json.loads(payload)
    if value.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError("MiniMax business status nonzero; see private response receipt")
    return value


def source_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(result.stdout)["format"]["duration"])


def clone(args: argparse.Namespace) -> None:
    key = api_key()
    source = args.source.resolve(strict=True)
    if not VOICE_ID.fullmatch(args.voice_id):
        raise ValueError("MiniMax voice_id must be 8–256 allowed characters")
    if source.suffix.lower() not in {".mp3", ".m4a", ".wav"}:
        raise ValueError("MiniMax clone source must be mp3, m4a, or wav")
    seconds = source_duration(source)
    if not 10 <= seconds <= 300 or source.stat().st_size > 20_000_000:
        raise ValueError("MiniMax clone source outside official duration or byte limits")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source_info = binding(source)
    write_new(output / "request.json", {
        "created_at_utc": now(), "source": source_info,
        "source_duration_seconds": seconds, "voice_id": args.voice_id,
        "upload": {"purpose": "voice_clone"},
        "clone": {"need_noise_reduction": False, "need_volume_normalization": False,
                  "clone_prompt": "omitted", "text_validation": "omitted",
                  "preview_text": "omitted"},
    })
    boundary = "xar-" + secrets.token_hex(16)
    media = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nvoice_clone\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"reference{source.suffix.lower()}\"\r\n"
        f"Content-Type: {media}\r\n\r\n").encode("ascii") + source.read_bytes() + (
        f"\r\n--{boundary}--\r\n").encode("ascii")
    uploaded = request_json("/files/upload", body,
                            f"multipart/form-data; boundary={boundary}", key,
                            output / "upload-response.json")
    file_id = uploaded.get("file", {}).get("file_id")
    if not isinstance(file_id, int) or uploaded["file"].get("purpose") != "voice_clone":
        raise ValueError("MiniMax upload lacked valid voice_clone file_id")
    payload = {"file_id": file_id, "voice_id": args.voice_id,
               "need_noise_reduction": False, "need_volume_normalization": False}
    write_new(output / "clone-request.json", payload)
    cloned = request_json("/voice_clone", json.dumps(payload).encode("utf-8"),
                          "application/json", key, output / "clone-response.json")
    write_new(output / "clone-receipt.json", {
        "state": "cloned-ready-for-official-tts-call", "finished_at_utc": now(),
        "source": source_info, "source_duration_seconds": seconds,
        "file_id": file_id, "voice_id": args.voice_id,
        "clone_response": {"base_resp": cloned["base_resp"],
                           "demo_audio_provided": bool(cloned.get("demo_audio"))},
    })
    print(json.dumps({"state": "cloned", "voice_id": args.voice_id,
                      "source_sha256": source_info["sha256"]}))


def synthesize(args: argparse.Namespace) -> None:
    key = api_key()
    clone_receipt = json.loads(args.clone_receipt.read_text(encoding="utf-8"))
    if clone_receipt.get("state") != "cloned-ready-for-official-tts-call":
        raise ValueError("No completed clone receipt")
    script_path = args.script.resolve(strict=True)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    cues = script["cues"]
    if not cues or len({cue["id"] for cue in cues}) != len(cues):
        raise ValueError("Expected unique nonempty cues")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    profile = {"model": "speech-2.8-hd", "speed": 0.95, "vol": 1,
               "pitch": 0, "emotion": "calm", "language_boost": "Chinese",
               "sample_rate": 32000, "bitrate": 128000,
               "format": "mp3", "channel": 1, "stream": False,
               "output_format": "hex"}
    write_new(output / "request.json", {
        "created_at_utc": now(), "script": binding(script_path),
        "clone_receipt": binding(args.clone_receipt),
        "voice_id": clone_receipt["voice_id"], "profile": profile,
        "cue_ids": [cue["id"] for cue in cues]})
    receipts = []
    for cue in cues:
        cue_id, speech = cue["id"], cue["narration"]
        if not re.fullmatch(r"[A-Za-z0-9-]+", cue_id) or not speech.strip():
            raise ValueError("Unsafe cue ID or empty narration")
        payload = {
            "model": profile["model"], "text": speech, "stream": False,
            "voice_setting": {"voice_id": clone_receipt["voice_id"],
                              "speed": profile["speed"], "vol": profile["vol"],
                              "pitch": profile["pitch"], "emotion": profile["emotion"]},
            "audio_setting": {"sample_rate": profile["sample_rate"],
                              "bitrate": profile["bitrate"], "format": "mp3", "channel": 1},
            "language_boost": "Chinese", "subtitle_enable": False,
            "output_format": "hex",
        }
        write_new(output / f"{cue_id}.request.json", payload)
        response = request_json("/t2a_v2", json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                "application/json", key, output / f"{cue_id}.response.json")
        data = response.get("data")
        if not isinstance(data, dict) or data.get("status") != 2 or not data.get("audio"):
            raise ValueError(f"MiniMax returned incomplete audio for {cue_id}")
        audio = bytes.fromhex(data["audio"])
        target = output / f"{cue_id}.mp3"
        with target.open("xb") as stream:
            stream.write(audio)
        receipt = {"id": cue_id, "text_sha256": hashlib.sha256(speech.encode("utf-8")).hexdigest(),
                   "audio": binding(target), "duration_seconds": source_duration(target),
                   "model": profile["model"], "voice_id": clone_receipt["voice_id"],
                   "profile": profile, "trace_id": response.get("trace_id"),
                   "extra_info": response.get("extra_info"), "completed_at_utc": now()}
        write_new(output / f"{cue_id}.receipt.json", receipt)
        receipts.append(receipt)
        print(json.dumps({"done": cue_id, "duration": receipt["duration_seconds"]}), flush=True)
    write_new(output / "completed.json", {
        "state": "synthesized", "cues": receipts, "profile": profile,
        "total_speech_seconds": sum(item["duration_seconds"] for item in receipts),
        "completed_at_utc": now()})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    clone_parser = sub.add_parser("clone")
    clone_parser.add_argument("--source", type=Path, required=True)
    clone_parser.add_argument("--voice-id", required=True)
    clone_parser.add_argument("--output-dir", type=Path, required=True)
    synth_parser = sub.add_parser("synthesize")
    synth_parser.add_argument("--clone-receipt", type=Path, required=True)
    synth_parser.add_argument("--script", type=Path, required=True)
    synth_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    {"clone": clone, "synthesize": synthesize}[args.command](args)


if __name__ == "__main__":
    main()
