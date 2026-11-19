"""Test-only SDK contract export; no Driver, Game, pipe, or delivery admission."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate packet field: " + key)
        result[key] = value
    return result


def source_pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-source", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--input-kind", choices=("cpp-producer-original", "declared-software-packet"), required=True)
    args = parser.parse_args()
    root = args.shared_source.resolve(strict=True)
    packet_path = args.packet.resolve(strict=True)
    with packet_path.open("rb") as stream:
        original_bytes = stream.read(256 * 1024 + 1)
    if len(original_bytes) > 256 * 1024:
        raise ValueError("test packet exceeds256KiB")
    frame: object = json.loads(original_bytes, object_pairs_hook=unique_object)
    if (not isinstance(frame, dict) or set(frame) != {"type", "protocol_version", "request_id", "ok", "result"}
            or frame["type"] != "command_result" or type(frame["protocol_version"]) is not int
            or frame["protocol_version"] != 1 or frame["request_id"] != "toast-fixture" or frame["ok"] is not True):
        raise ValueError("original whole successful toast-fixture packet required")

    # Import the actual unchanged contract leaves, without executing the broad
    # bridge/__init__ Driver/Service facade. This deliberately proves only the
    # real normalizer boundary; the separate twelve SDK tests prove that facade.
    sdk = root / "ck3_autonomous_player/src/xar_autoplayer"
    for name, directory in (("xar_autoplayer", sdk), ("xar_autoplayer.bridge", sdk / "bridge")):
        specification = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
        specification.submodule_search_locations = [str(directory)]
        sys.modules[name] = importlib.util.module_from_spec(specification)
    from xar_autoplayer.bridge.gui_window_tree_contract import normalize_current_interface_toast_v1

    sources: list[dict[str, object]] = []
    for leaf in ("gui_window_tree_contract", "frontend_gui_route_contract", "version_identity"):
        module = importlib.import_module("xar_autoplayer.bridge." + leaf)
        expected = (sdk / "bridge" / (leaf + ".py")).resolve(strict=True)
        if module.__file__ is None or Path(module.__file__).resolve(strict=True) != expected:
            raise ValueError("SDK contract import escaped explicit shared source: " + leaf)
        sources.append(source_pin(expected))

    public = normalize_current_interface_toast_v1(frame["result"])
    # These four fields are a declared SOFTWARE Full/public binding, just as in
    # the SDK fixture. They are not inferred from the packet or claimed as Game.
    public["public_revision"] = "3"
    public["game_pid"] = 42
    public["viewer_played_character_id"] = 31254
    public["date_raw"] = 53144328
    normalized = normalize_current_interface_toast_v1(public)
    if packet_path.read_bytes() != original_bytes:
        raise ValueError("original producer packet changed during SDK export")
    provenance = {"schema": "xfm-test-actual-sdk-normalizer-export-v1", "input_kind": args.input_kind,
        "input_sha256": hashlib.sha256(original_bytes).hexdigest(), "input_bytes": len(original_bytes),
        "software_public_binding": True, "driver_service_executed": False, "game_started": False,
        "delivery_confirmed": False, "sdk_sources": sources, "exporter": source_pin(Path(__file__).resolve())}
    print(json.dumps(provenance, ensure_ascii=True, allow_nan=False), file=sys.stderr)
    print(json.dumps(normalized, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
