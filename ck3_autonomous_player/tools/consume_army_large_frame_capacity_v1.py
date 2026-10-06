"""One Windows transport qualification scene; invoke only with the owned fixture.

This file has not been run. It uses the production named-pipe server, decoder,
driver ingest, and request/result cache. It does not normalize Army rows or
simulate a CK3 state snapshot, and it does not connect to the game pipe.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


PAYLOAD_BYTES = 33_445_694
LIMIT_BYTES = 64 * 1024 * 1024
REQUEST_ID = "r0050-army-large-frame-33445694"
STEP = "query-army-strengths-v1"
EXPECTED_ARMY_ROW = {
    "status": "available",
    "army_id": 218104048,
    "native_carmy_id": 218105048,
    "scope_role": "player",
    "war_ids": [],
    "regiment_count": 3,
    "current_soldiers": 1200,
    "maximum_soldiers": 1500,
    "ai_base_power_raw": 180000000,
    "ai_base_power_scale": 100000,
    "unavailable_reason": None,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    require(os.name == "nt", "the actual Windows transport fixture requires Windows")
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.native_driver import (
        MAXIMUM_FRAME_BYTES,
        NativeHeadlessGameplayDriver,
        NativeNamedPipeServer,
    )

    args.output_dir.mkdir(parents=True, exist_ok=False)
    pipe_name = rf"\\.\pipe\xar-army-large-frame-fixture-{uuid.uuid4().hex}"
    writer_receipt_path = args.output_dir / "native-writer-receipt.json"
    report: dict[str, object] = {
        "status": "RED",
        "scene": "historical_army_response_33445694_bytes",
        "new_scene_count": 1,
        "synthetic_payload": True,
        "expected_payload_bytes": PAYLOAD_BYTES,
        "expected_limit_bytes": LIMIT_BYTES,
        "pipe_name": pipe_name,
        "native_exe": str(args.native_exe.resolve()),
        "projection_root": str(args.projection_root.resolve()),
        "normalization_provenance": "No Army normalization invoked; production transport JSON decode -> NativeHeadlessGameplayDriver._ingest -> NativeProtocolState.wait_for_command_result",
        "qualification_boundary": "Synthetic historical-sized transport fixture only; no CK3 query, paused snapshot, typed Army normalization, or live gameplay claim",
    }
    driver = None
    peer = None
    try:
        require(MAXIMUM_FRAME_BYTES == LIMIT_BYTES, "consumer is not using the paired 64 MiB source")
        endpoint = NativeNamedPipeServer(pipe_name)
        driver = NativeHeadlessGameplayDriver(pipe_name, endpoint=endpoint)
        argv = [
            str(args.native_exe.resolve()),
            "--pipe-name", pipe_name,
            "--receipt", str(writer_receipt_path.resolve()),
        ]
        report["native_argv"] = argv
        peer = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + 20.0
        while not driver.state.diagnostics().get("connected"):
            require(peer.poll() is None, "native peer exited before its hello was ingested")
            require(time.monotonic() < deadline, "production driver did not ingest fixture hello")
            time.sleep(0.01)
        # The genuine driver hello callback sends an ordinary ping. Wait for its
        # real pong so the native peer will distinguish the final consumed ping.
        while driver.state.diagnostics().get("last_pong") is None:
            require(peer.poll() is None, "native peer exited before answering hello ping")
            require(time.monotonic() < deadline, "production driver hello ping did not receive pong")
            time.sleep(0.01)
        request = {
            "type": "execute_step",
            "protocol_version": 1,
            "request_id": REQUEST_ID,
            "step": STEP,
            "expected_revision": 1,
        }
        write_json(args.output_dir / "consumer-request.json", request)
        driver.endpoint.send(request)
        frame = driver.state.wait_for_command_result(REQUEST_ID, 20.0)
        require(isinstance(frame, dict), "large command_result did not reach the production driver cache")
        require(set(frame) == {"type", "protocol_version", "request_id", "ok", "result", "source_payload"}, "decoded command_result keys changed")
        require(frame["type"] == "command_result" and frame["protocol_version"] == 1 and frame["request_id"] == REQUEST_ID and frame["ok"] is True, "decoded command_result identity changed")
        result = frame["result"]
        require(result == {
            "step": STEP, "accepted": True, "status": "available",
            "query_sequence": 1, "army_strengths": [EXPECTED_ARMY_ROW],
        }, "meaningful Army result changed during transport")
        source_payload = frame["source_payload"]
        require(isinstance(source_payload, str), "bulk source_payload is not a string")
        require(source_payload.count("x") == len(source_payload), "bulk source_payload bytes changed")
        envelope = {key: value for key, value in frame.items() if key != "source_payload"}
        envelope_bytes = len(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        # The original compact envelope gains one unique field; its ASCII value
        # contributes exactly one UTF-8 byte for each x, without a huge disk read.
        payload_bytes = envelope_bytes + len(',"source_payload":""') + len(source_payload)
        require(payload_bytes == PAYLOAD_BYTES, "decoded compact frame length differs from historical length")
        driver.endpoint.send({
            "type": "ping", "protocol_version": 1,
            "request_id": "army-large-frame-consumed",
        })
        stdout, stderr = peer.communicate(timeout=10.0)
        (args.output_dir / "native-stdout.txt").write_text(stdout, encoding="utf-8")
        (args.output_dir / "native-stderr.txt").write_text(stderr, encoding="utf-8")
        report["native_exit_code"] = peer.returncode
        require(peer.returncode == 0, "native fixture did not exit successfully")
        native_receipt = json.loads(writer_receipt_path.read_text(encoding="utf-8"))
        diagnostic = native_receipt["write_diagnostic"]
        require(native_receipt["payload_bytes"] == PAYLOAD_BYTES and native_receipt["source_payload_bytes"] == len(source_payload), "native byte accounting disagrees with decoded bytes")
        require(native_receipt["prefix_bytes"] + native_receipt["source_payload_bytes"] + native_receipt["suffix_bytes"] == PAYLOAD_BYTES, "native exact-length construction disagrees")
        require(diagnostic == {
            "query_sequence": 1, "payload_bytes": PAYLOAD_BYTES,
            "limit_bytes": LIMIT_BYTES, "stage": "complete",
            "success": True, "windows_error": None,
        }, "production Army writer did not report complete 64 MiB transport")
        report.update({
            "status": "GREEN", "payload_bytes": payload_bytes,
            "source_payload_bytes": len(source_payload),
            "army_strengths": result["army_strengths"],
            "native_write_diagnostic": diagnostic,
            "production_endpoint": "NativeNamedPipeServer",
            "production_decoder": "NativeNamedPipeServer._read_connection/_read_exact + UTF-8 + json.loads",
            "production_driver": "NativeHeadlessGameplayDriver._ingest/NativeProtocolState.wait_for_command_result",
        })
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if driver is not None:
            driver.close()
        if peer is not None and peer.poll() is None:
            peer.terminate()
            try:
                stdout, stderr = peer.communicate(timeout=5.0)
            except subprocess.TimeoutExpired:
                peer.kill()
                stdout, stderr = peer.communicate(timeout=5.0)
            (args.output_dir / "native-stdout.txt").write_text(stdout, encoding="utf-8")
            (args.output_dir / "native-stderr.txt").write_text(stderr, encoding="utf-8")
            report["native_exit_code"] = peer.returncode
        elif peer is not None and "native_exit_code" not in report:
            stdout, stderr = peer.communicate(timeout=5.0)
            (args.output_dir / "native-stdout.txt").write_text(stdout, encoding="utf-8")
            (args.output_dir / "native-stderr.txt").write_text(stderr, encoding="utf-8")
            report["native_exit_code"] = peer.returncode
        write_json(args.output_dir / "consumer-report.json", report)
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
