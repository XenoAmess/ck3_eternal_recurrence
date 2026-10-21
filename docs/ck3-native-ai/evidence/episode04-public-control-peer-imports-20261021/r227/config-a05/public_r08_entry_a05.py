"""Use the existing public entry and explicitly frozen postload peers."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys

BASE = Path("C:/ck3-e04-resume-20261020-a01/r15-complete-episode04-1030-a01")
ORIGINAL = BASE / "live-scene-a01"
SCENE = BASE / "live-scene-r08-a02"
TOOLS = ORIGINAL / "source-a01/tools"
PEERS = ORIGINAL / "hot-postload-a01/tools"
READY = ORIGINAL / "source-a01/overrides/episode04_ready_t0_12004.py"
READY_SHA = "a2669df1257543af4aeff81e254c502bebc9da391ef04ef7f32e0268e83f36ba"
NAME = "xar_autoplayer.bridge.episode04_ready_t0_12004"


def main() -> None:
    raw = READY.read_bytes()
    if len(raw) != 20534 or hashlib.sha256(raw).hexdigest() != READY_SHA:
        raise ValueError("Explicit ordinary consumer changed")
    sys.path.insert(0, str(PEERS))
    sys.path.insert(1, str(TOOLS))
    sys.path.insert(2, "D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src")
    sys.path.insert(3, "D:/workspace/ck3_eternal_recurrence/tools")
    live_id = importlib.import_module("ck3_live_run_id")
    if live_id.__file__ is None or Path(live_id.__file__).resolve() != TOOLS / "ck3_live_run_id.py":
        raise ValueError("Actual machine module is outside the frozen C source")
    allocated_module = importlib.import_module("ck3_mod_acceptance_allocate")
    if allocated_module.__file__ is None or Path(allocated_module.__file__).resolve() != TOOLS / "ck3_mod_acceptance_allocate.py":
        raise ValueError("Actual allocator is outside the frozen C source")
    unrun_module = importlib.import_module("ck3_mod_acceptance_unrun")
    if unrun_module.__file__ is None or Path(unrun_module.__file__).resolve() != TOOLS / "ck3_mod_acceptance_unrun.py":
        raise ValueError("Actual unused-run helper is outside the frozen C source")
    importlib.import_module("xar_autoplayer.bridge")
    spec = importlib.util.spec_from_file_location(NAME, READY)
    if spec is None or spec.loader is None:
        raise ValueError("Explicit ordinary consumer loader unavailable")
    consumer = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = consumer
    spec.loader.exec_module(consumer)
    if consumer.__file__ is None or Path(consumer.__file__).resolve() != READY.resolve():
        raise ValueError("Actual ordinary consumer differs")
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"
    if mode != "--help":
        destination = SCENE / "ops-a01/public-bindings"
        destination.mkdir(parents=True, exist_ok=True)
        with (destination / (mode + "-" + str(os.getpid()) + ".json")).open("x", encoding="utf-8", newline="\n") as stream:
            json.dump({"machine_id": "desktop-3fevhd2-1c74096080", "actual_consumer_file": consumer.__file__,
                       "bytes": len(raw), "sha256": READY_SHA, "D_host_native_driver_replaced": False,
                       "public_peer_root": str(PEERS)}, stream, indent=2)
            stream.write("\n")
    entry = TOOLS / "ck3_mod_acceptance.py"
    sys.argv[0] = str(entry)
    runpy.run_path(str(entry), run_name="__main__")


if __name__ == "__main__":
    main()
