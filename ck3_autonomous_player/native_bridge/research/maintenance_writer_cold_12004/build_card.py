"""Emit existing adapter/consumer argv. This does not admit or execute a watch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import importlib.util as _owner_import
_owner_spec = _owner_import.spec_from_file_location('_writer_owner_binding_v2', Path(__file__).with_name('owner_binding.py'))
owner = _owner_import.module_from_spec(_owner_spec)
_owner_spec.loader.exec_module(owner)

RESEARCH = "ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004"
EXPECTED = ("pid", "created", "generation", "window", "epoch", "character_id",
            "revision", "native_revision", "date")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def make_card(config):
    need(type(config) is dict, "Root config object required")
    repo = Path(config["repo"]).resolve()
    interpreter = Path(config["python"]).resolve()
    need(interpreter.is_file(), "Explicit interpreter missing")
    need(type(config["source_head"]) is str and len(config["source_head"]) == 40
         and all(c in "0123456789abcdef" for c in config["source_head"]),
         "Explicit source commit required")
    actual = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    need(actual == config["source_head"], "Root source commit differs")
    output = Path(config["watch_output_root"]).resolve()
    need(not output.exists(), "Fresh watch directory already exists")
    identity = config["expected"]
    for name in EXPECTED:
        need(type(identity.get(name)) is int and identity[name] > 0,
             "Independent positive Root identity missing: " + name)
    mode=config.get("owner_binding_mode",owner.EPISODE_BOUND)
    episode_args=owner.episode_arguments(mode,identity.get("episode"))
    need(type(identity.get("machine")) is str and identity["machine"].strip(),"Independent Root identity missing: machine")
    if mode==owner.ORDINARY:
        owner.positive(identity.get("game_state_identity_witness"),"independent GameState")
        owner.positive(identity.get("local_player_id"),"independent local player",1<<32)
    need(type(config.get("timeout_ms")) is int and 500 <= config["timeout_ms"] <= 30000,
         "Finite timeout must be 500..30000 ms")
    need(type(config.get("max_slot_hits")) is int and 1 <= config["max_slot_hits"] <= 128,
         "Aggregate slot-hit bound must be 1..128")
    source_pins = []
    for name in ("prepare_writer_admission.py", "consume_writer_actual.py"):
        path = repo / RESEARCH / name
        raw = path.read_bytes()
        source_pins.append({"path": str(path), "bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest()})
    prepare = [str(interpreter), "-B", "-O", str(repo / RESEARCH / "prepare_writer_admission.py"),
               "--enable-ck3-12004-data-watch", "--prepare-only", "--repo", str(repo)]
    for option, key in (("build-dir", "build_dir"), ("machine-execution-gate", "machine_execution_gate"),
                        ("cash-response", "cash_response"), ("before-response", "before_response")):
        path = Path(config[key]).resolve()
        need(path.is_dir() if option == "build-dir" else path.is_file(), "Missing input: " + option)
        prepare += ["--" + option, str(path)]
    prepare += ["--output-root", str(output)]
    for name in EXPECTED:
        prepare += ["--expected-" + name.replace("_", "-"), str(identity[name])]
    prepare += episode_args
    if mode==owner.ORDINARY:
        prepare += ["--expected-game-state",str(identity["game_state_identity_witness"]),
                    "--expected-local-player-id",str(identity["local_player_id"])]
    prepare += ["--expected-machine", identity["machine"], "--timeout-ms", str(config["timeout_ms"]),
                "--max-slot-hits", str(config["max_slot_hits"])]
    consume = [str(interpreter), "-B", "-O", str(repo / RESEARCH / "consume_writer_actual.py"),
               "--repo", str(repo), "--raw", str(output / "writer.raw.ndjson"),
               "--admission", str(output / "ADMISSION.actual.json"),
               "--cash-response", str(Path(config["cash_response"]).resolve()),
               "--before-response", str(Path(config["before_response"]).resolve()),
               "--output", str(output / "ACTUAL-WRITERS.json")]
    return {"schema": "xar.r08.cd-writer-root-argv-card.v1", "source_head": actual,
            "status": "ARGV_ONLY_NOT_RUNTIME_ADMITTED", "source_pins": source_pins,
            "prepare_argv": prepare, "consume_argv": consume,
            "native_argv_source": str(output / "ADMISSION.actual.json") + "#/argv",
            "observer_launches_performed": 0, "sdk_actions_performed": 0,
            "watch_offsets": [0x2C0, 0x2C8, 0x28, 0x30], "target_slots": [2, 3],
            "aggregate_hit_limit": config["max_slot_hits"], "timeout_ms": config["timeout_ms"],
            "unfulfilled_Root_gates": ["new actual capacity and explicit external-debugger admission",
                                      "fresh paired paused snapshot/cash with independent expected identity",
                                      "actual native research plan check --for-observation",
                                      "prepare-only adapter actual success and exact SYSTEM gate",
                                      "Root-held Popen handle; actual ready true and armed_thread_count > 0",
                                      "one original Resume; natural timeout and proven restore/detach before close"],
            "known_producer": False, "maintenance_attribution": "unclosed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    need(not args.output.exists(), "Create-only card exists")
    need(args.config.stat().st_size <= 65536, "Config exceeds 64 KiB")
    card = make_card(json.loads(args.config.read_text(encoding="utf-8-sig")))
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(card, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": card["status"], "observer_launches_performed": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
