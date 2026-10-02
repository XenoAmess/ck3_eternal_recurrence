"""Pure-file, append-only R0117/a14 admission seal; never grants live GO.

This tool deliberately does not import the candidate, run Git, query the task
bus, inspect a desktop, or create a worker. The later one-shot operator repeats
its own source, screen and process checks before any native launch.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HEAD = "e7c0727b7e851de803f79ce04806feccfa33149d"
ROUND = "R3948"
RUN_ID = "desktop-3fevhd2-1c74096080--vanilla--R0117"
EXECUTION_ID = "2be36b8a-029f-4dc5-a017-ce7d0b3809d7"
BUS_SHA256 = "D6629F52EE098C709C5A85ADBC629F40E8B2724BE9CC1F29FAF48AF215E96121"
DLL_SHA256 = "3438E8725AA06839CA1F2DFAF6D6CC98D41A4F33C02AC0702AC8D48AD241531B"
INJECTOR_SHA256 = "ECBC1B3B24E8A9BF1F85E9CBE195E4A5B8D3E928DB0FC8124ABF4D6D95A4B0D3"
CHECKPOINT_SHA256 = "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6"
RAW_DRIVER_SHA256 = "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722"
SIDECAR_SHA256 = "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7"
GAME_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
PIPE = r"\\.\pipe\xar-g2-robert-1066-seed-66f926d"
ALLOCATOR_STDOUT = Path(r"D:\ck3-research-artifacts\war-h3937-next-admission-20260930\attempt-01\allocator-stdout.json")
ALLOCATOR_STDOUT_SHA256 = "2A2B5DAC1E982485A4E7507E06666DE8530BF7CAF889B4C5157667A4DAB6274E"
ALLOCATOR_COMMAND = ALLOCATOR_STDOUT.with_name("allocator-command.json")
ALLOCATOR_COMMAND_SHA256 = "1D4D6AD98CE2614DEDCA9F4D0075C583E49ED8F903AD0E6BFBD5B7E876C34059"
ALLOCATIONS = Path(r"C:\Users\1\AppData\Local\XarCk3Acceptance\live-run-ids-v1\desktop-3fevhd2-1c74096080\vanilla\allocations.jsonl")
ALLOCATOR_COUNTER = ALLOCATIONS.with_name("counter.json")
ALLOCATOR_STATUSES = ALLOCATIONS.with_name("statuses.jsonl")

CANDIDATE = Path(r"D:\w\h3937_cold_admission")
NO_LAUNCH = Path(r"D:\ck3-research-artifacts\war-h3937-combined-no-launch-20260930\attempt-14")
OUTPUT_ROOT = Path(r"D:\ck3-research-artifacts\war-h3937-r0117-static-seal-20260930")
LIVE_ROOT = Path(r"D:\ck3-research-artifacts\war-h3937-combined-live-20260930")
GAME = Path(r"C:\SteamLibrary\steamapps\common\Crusader Kings III")
PYTHON = Path(r"D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe")

SOURCE_BLOBS = {
    "producer_module": ("h3937_combined_paused_war_scope_run.py", "a33d2a7b8d7c75ce8017cf441050232529984abb"),
    "source_module_.h3937_cold_load_observer": ("h3937_cold_load_observer.py", "7804aca5de8e6e18c04bd8d1936ff3d49d0440a1"),
    "source_module_.h3937_combined_readonly_queries": ("h3937_combined_readonly_queries.py", "558bb791a1a8147ab0f70cf35b22440171e022ab"),
    "source_module_.h3937_target_readonly_queries": ("h3937_target_readonly_queries.py", "77fcbba88d1ac3315a1cccb8dfe98fcf3d1e78d5"),
    "source_module_.h3937_paused_war_scope_run": ("h3937_paused_war_scope_run.py", "c1e7f3818f78ace76c58bc82a029c0bcdd60d1cd"),
    "source_module_.h3937_stationary_route_contact_query_run": ("h3937_stationary_route_contact_query_run.py", "448e455bf1e9e96566062bc5c1c1d7ea64a8af6e"),
    "source_module_.bridge.native_driver": ("bridge/native_driver.py", "5bebf4ee5b6c5e5a593165c83d22d01688905a92"),
    "source_module_.bridge.h3937_date_hold": ("bridge/h3937_date_hold.py", "0f4daea5c8cf27aa2706a58b27a8cdae0aff0296"),
    "source_module_.bridge.service": ("bridge/service.py", "6e7cc4cf831bbcff56f12e04e7fc338f104a4827"),
    "source_module_.bridge.war_contract": ("bridge/war_contract.py", "834b4b519db1188e87ebbc5c21b3cb9fc33ff8ce"),
    "source_module_.bridge.succession_transition_contract": ("bridge/succession_transition_contract.py", "5bb722a5d5e0009da3cfc4256ecef358d00590da"),
    "source_module_.environment": ("environment.py", "80f538981bb88f918f4244fcac3b8ae05084fdd1"),
    "source_module_.native_auto_run": ("native_auto_run.py", "cf45dae4aa7686b1de3be5f49ea554c799d865b0"),
    "source_module_.native_session": ("native_session.py", "e373b3aafede85615d9e90682a760a892f9415d4"),
    "source_module_.runtime": ("runtime.py", "d06863f3629dbe6b974e0115590152a34401c6d4"),
    "source_module_.strategy": ("strategy.py", "377c1efdfd3d93289f966dc889a7db0014544b55"),
}
ENTRY_BLOBS = {
    "ck3_autonomous_player/h3937_cold_observer_once.py": "25fbdf2fb505318cad6c7f166190ca5b7753a689",
    "ck3_autonomous_player/src/xar_autoplayer/h3937_cold_observer_once_enable.py": "fe26e79f92e882ac422c54d15d5cab1cc4561683",
    "tools/codex_task_bus.py": "3e482b49dc9c44c4d88a171866459b4eb5195c8d",
}

# Populate only after independent review of a fresh official a14 package.
# The hashes must include every generated proof listed below. Without this
# second, code-reviewed anchor, self-consistent edited JSON cannot be sealed.
FROZEN_A14_SHA256: dict[str, str] | None = None
FROZEN_A14_PRODUCER: dict[str, tuple[Path, str]] | None = None


def _sha(path: Path) -> str:
    _reject_links(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _reject_links(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink() or getattr(item, "is_junction", lambda: False)():
            raise ValueError(f"linked input ancestor refused: {item}")
        if item.exists():
            stat = item.stat(follow_symlinks=False)
            if getattr(stat, "st_file_attributes", 0) & 0x400:
                raise ValueError(f"reparse input ancestor refused: {item}")
            if item.is_file() and stat.st_nlink != 1:
                raise ValueError(f"hardlinked input refused: {item}")


def _blob(path: Path) -> str:
    _reject_links(path)
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _json(path: Path) -> dict[str, object]:
    _reject_links(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"JSON object required: {path}")
    return value


def _same(actual: object, expected: object, label: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"{label} differs")


def _file(path: Path, digest: str) -> str:
    _reject_links(path)
    actual = _sha(path)
    if actual != digest.upper():
        raise ValueError(f"SHA-256 differs: {path}")
    return actual


def _head(checkout: Path) -> str:
    pointer = checkout / ".git"
    _reject_links(pointer)
    if pointer.is_file():
        value = pointer.read_text(encoding="utf-8").strip()
        if not value.startswith("gitdir: "):
            raise ValueError("invalid Git worktree pointer")
        git_dir = checkout / value[8:]
        _reject_links(git_dir)
        git_dir = git_dir.resolve()
    elif pointer.is_dir():
        _reject_links(pointer)
        git_dir = pointer.resolve()
    else:
        raise ValueError("Git worktree pointer unavailable")
    _reject_links(git_dir / "HEAD")
    head = (git_dir / "HEAD").read_text(encoding="ascii").strip()
    if head.startswith("ref: "):
        ref = head[5:]
        if not ref.startswith("refs/heads/") or ".." in ref:
            raise ValueError("unexpected Git HEAD reference")
        common = git_dir
        common_file = git_dir / "commondir"
        if common_file.is_file():
            _reject_links(common_file)
            common = git_dir / common_file.read_text(encoding="ascii").strip()
            _reject_links(common)
            common = common.resolve()
        loose = common / ref
        if loose.is_file():
            _reject_links(loose)
            head = loose.read_text(encoding="ascii").strip()
        else:
            packed = common / "packed-refs"
            _reject_links(packed)
            matches = [line.split(" ", 1)[0] for line in packed.read_text(encoding="ascii").splitlines()
                       if line.endswith(" " + ref)] if packed.is_file() else []
            if len(matches) != 1:
                raise ValueError("Git HEAD reference unavailable")
            head = matches[0]
    if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
        raise ValueError("Git HEAD malformed")
    return head


def verify(checkout: Path = CANDIDATE, no_launch: Path = NO_LAUNCH) -> dict[str, object]:
    """Read only the exact a14 materials and return a hash-bound seal payload."""
    _reject_links(no_launch)
    _reject_links(checkout)
    checkout = checkout.resolve()
    no_launch = no_launch.resolve()
    if no_launch.name != "attempt-14" or no_launch.parent != NO_LAUNCH.parent.resolve():
        raise ValueError("only the official new attempt-14 path is admissible")
    _same(_head(checkout), HEAD, "candidate HEAD")
    source_root = checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer"
    source_blobs = {}
    for key, (relative, expected) in SOURCE_BLOBS.items():
        path = source_root / relative
        _same(_blob(path), expected, f"source blob {key}")
        source_blobs[key] = expected
    for relative, expected in ENTRY_BLOBS.items():
        _same(_blob(checkout / relative), expected, f"entry/bus blob {relative}")
    _file(checkout / "tools" / "codex_task_bus.py", BUS_SHA256)

    admission_path = no_launch / "admission.json"
    manifest_path = no_launch / "operator-manifest.json"
    identity_path = no_launch / "live-run-identity.json"
    proof_before = {path: _sha(path) for path in (admission_path, manifest_path, identity_path,
                                                  no_launch / "source-validation.json",
                                                  no_launch / "interpreter-probe.json")}
    if FROZEN_A14_SHA256 is None:
        raise ValueError("independently reviewed a14 proof SHA-256 freeze is absent")
    if FROZEN_A14_PRODUCER is None:
        raise ValueError("independently reviewed a14 producer freeze is absent")
    _same(set(FROZEN_A14_PRODUCER), {"operator_script", "command_receipt", "postcheck_receipt"},
          "a14 producer proof set")
    for label, (path, digest) in FROZEN_A14_PRODUCER.items():
        _reject_links(path)
        if not path.resolve().is_relative_to(no_launch.parent.resolve()):
            raise ValueError(f"a14 {label} outside official external proof root")
        _file(path, digest)
    expected_proofs = {
        "admission.json", "operator-manifest.json", "live-run-identity.json",
        "source-validation.json", "interpreter-probe.json",
        "state/native-session/driver-state.json",
        "state/profile/xar-autoplayer-environment.json",
        "state/ordinary-seed-rebind-v1.json",
        "state/preflights/report.json",
    }
    _same(set(FROZEN_A14_SHA256), expected_proofs, "a14 reviewed proof set")
    for relative, digest in FROZEN_A14_SHA256.items():
        if relative == "state/preflights/report.json":
            continue  # Its exact generated subdirectory is checked below.
        _file(no_launch / relative, digest)
    admission, manifest, identity = map(_json, (admission_path, manifest_path, identity_path))
    state = no_launch / "state"
    if (state / "control" / "unsafe-cleanup.json").exists():
        raise ValueError("unsafe native cleanup marker blocks static seal")
    _same(admission.get("schema"), "xar.war.h3937-cold-observer-disabled-no-launch-admission.v1", "admission schema")
    _same(manifest.get("schema"), "xar.war.h3937-cold-observer-disabled-operator-manifest.v1", "manifest schema")
    _same(identity.get("schema"), "xar.ck3-live-run-identity.v1", "identity schema")
    for item, label in ((admission, "admission"), (manifest, "manifest")):
        _same(item.get("candidate_head"), HEAD, f"{label} HEAD")
        _same(item.get("live_run_id"), RUN_ID, f"{label} run")
        _same(item.get("live_run_identity_sha256"), _sha(identity_path), f"{label} allocator SHA")
        _same(item.get("task_bus_cli_sha256"), BUS_SHA256, f"{label} bus source SHA")
        _same(item.get("cold_load_observer_default_off"), True, f"{label} observer default")
        _same(item.get("cold_load_observer_live_enabled"), False, f"{label} observer enabled")
        _same(item.get("ck3_launch_attempted"), False, f"{label} launch")
    _same(admission.get("candidate_checkout_clean"), True, "admission clean assertion")
    _same(manifest.get("candidate_clean"), True, "manifest clean assertion")
    _same(Path(str(manifest.get("candidate_checkout"))).resolve(), checkout, "manifest checkout")
    _same(manifest.get("source_git_blobs"), source_blobs, "six-read source blob map")
    _same(identity.get("run_id"), RUN_ID, "allocator run")
    _same(identity.get("execution_id"), EXECUTION_ID, "allocator execution")
    _same(identity.get("machine_id"), "desktop-3fevhd2-1c74096080", "allocator machine")
    _same(identity.get("mod_key"), "vanilla", "allocator mod")
    _same(identity.get("sequence"), 117, "allocator sequence")
    _file(ALLOCATOR_STDOUT, ALLOCATOR_STDOUT_SHA256)
    _file(ALLOCATOR_COMMAND, ALLOCATOR_COMMAND_SHA256)
    _same(_json(ALLOCATOR_STDOUT), identity, "original allocator stdout")
    allocator_command = _json(ALLOCATOR_COMMAND)
    command_argv = allocator_command.get("argv")
    if (type(command_argv) is not list or len(command_argv) < 5
            or command_argv[2:5] != ["allocate", "--mod", "vanilla"]):
        raise ValueError("original allocator command is not vanilla allocation")
    _same(allocator_command.get("candidate_head"),
          "e7a1849b5455ef5ee31564a9b27f6472fa88770c", "HEAD at R0117 allocation")
    _reject_links(ALLOCATIONS)
    allocations = ALLOCATIONS.read_text(encoding="utf-8").splitlines()
    if len(allocations) < 117:
        raise ValueError("original allocation journal is shorter than R0117")
    allocation = json.loads(allocations[116])
    _same(allocation, identity, "allocation journal R0117")
    counter = _json(ALLOCATOR_COUNTER)
    _same(counter.get("schema"), "xar.ck3-live-run-counter.v1", "allocator counter schema")
    _same(counter.get("last_sequence"), 117, "allocator current sequence")
    _same(counter.get("last_run_id"), RUN_ID, "allocator current run")
    _reject_links(ALLOCATOR_STATUSES)
    if any(RUN_ID in line for line in ALLOCATOR_STATUSES.read_text(encoding="utf-8").splitlines()):
        raise ValueError("R0117 already has a status entry")
    _same(Path(str(manifest.get("python"))).resolve(), PYTHON.resolve(), "interpreter")
    _same(manifest.get("python_version"), "Python 3.14.7", "interpreter version")
    _same(Path(str(admission.get("prepared_state"))).resolve(), state, "admission state")
    _same(Path(str(manifest.get("state_dir"))).resolve(), state, "manifest state")
    _same(manifest.get("bridge_pipe"), PIPE, "bridge pipe")
    _same(Path(str(manifest.get("bridge_dll"))).resolve(), no_launch / "source-verified" / "xar_ck3_bridge.dll", "bridge DLL path")
    _same(Path(str(manifest.get("bridge_injector"))).resolve(), no_launch / "source-verified" / "xar_ck3_bridge_injector.exe", "injector path")
    _same(Path(str(manifest.get("game_dir"))).resolve(), GAME.resolve(), "game path")
    _same(manifest.get("game_exe_sha256"), GAME_SHA256, "game SHA claim")
    _file(GAME / "binaries" / "ck3.exe", GAME_SHA256)
    for item, label in ((admission, "admission"), (manifest, "manifest")):
        for flag in ("screen_lease_acquired", "fresh_steam_offline_proven", "live_authorized", "live_output_created", "date_move_attack_authorized"):
            if flag in item:
                _same(item[flag], False, f"{label} {flag}")
    for flag in ("combined_outer_hard_gate", "combined_inner_hard_gate", "target_inner_hard_gate"):
        _same(admission.get(flag), False, f"admission {flag}")
    for flag in ("outer_hard_gate", "inner_hard_gate", "target_hard_gate"):
        _same(manifest.get(flag), False, f"manifest {flag}")
    for field, value in (("episode_run_id", "native-29829-2bc2d599f7f9"), ("actor", 29829),
                         ("date_raw", 53219928), ("history_index", 3937)):
        _same(admission.get(field), value, f"admission {field}")
    _same(manifest.get("episode_run_id"), "native-29829-2bc2d599f7f9", "manifest episode")
    _same(manifest.get("episode_character_id"), 29829, "manifest actor")
    _same(manifest.get("date_raw"), 53219928, "manifest date")
    _same(manifest.get("history_index"), 3937, "manifest history")
    for path, digest in (
        (no_launch / "source-verified" / "xar_ck3_bridge.dll", DLL_SHA256),
        (no_launch / "source-verified" / "xar_ck3_bridge_injector.exe", INJECTOR_SHA256),
        (no_launch / "source-verified" / "xar_checkpoint.ck3", CHECKPOINT_SHA256),
        (no_launch / "source-verified" / "driver-state.json", RAW_DRIVER_SHA256),
        (no_launch / "source-verified" / "player-child-matrilineal-formal-v1.json", SIDECAR_SHA256),
        (state / "profile" / "save games" / "xar_checkpoint.ck3", CHECKPOINT_SHA256),
        (state / "player-child-matrilineal-formal-v1.json", SIDECAR_SHA256),
    ):
        _file(path, digest)
    for item, key, expected in ((admission, "dll_sha256", DLL_SHA256),
                                (admission, "injector_sha256", INJECTOR_SHA256),
                                (admission, "raw_driver_sha256", RAW_DRIVER_SHA256),
                                (manifest, "bridge_dll_sha256", DLL_SHA256),
                                (manifest, "bridge_injector_sha256", INJECTOR_SHA256),
                                (manifest, "source_checkpoint_sha256", CHECKPOINT_SHA256),
                                (manifest, "source_raw_driver_sha256", RAW_DRIVER_SHA256),
                                (manifest, "source_child_sidecar_sha256", SIDECAR_SHA256)):
        _same(item.get(key), expected, key)
    prepared_driver_sha = str(admission.get("prepared_driver_sha256", ""))
    _same(manifest.get("prepared_driver_sha256"), prepared_driver_sha, "prepared driver claim")
    _file(state / "native-session" / "driver-state.json", prepared_driver_sha)
    prepared_driver = _json(state / "native-session" / "driver-state.json")
    _same(prepared_driver.get("format_version"), 2, "prepared driver format")
    _same(prepared_driver.get("pipe_name"), PIPE, "prepared driver pipe")
    _same(prepared_driver.get("episode_run_id"), "native-29829-2bc2d599f7f9", "prepared driver episode")
    _same(prepared_driver.get("episode_character_id"), 29829, "prepared driver actor")
    prepared_checkpoint = prepared_driver.get("last_checkpoint")
    if type(prepared_checkpoint) is not dict:
        raise ValueError("prepared driver checkpoint unavailable")
    _same(prepared_checkpoint.get("sha256", "").upper(), CHECKPOINT_SHA256, "prepared driver save")
    _same(prepared_checkpoint.get("date_raw"), 53219928, "prepared driver date")
    _same(prepared_checkpoint.get("history_index"), 3937, "prepared driver history")
    environment_sha = str(admission.get("environment_sha256", ""))
    _same(manifest.get("environment_sha256"), environment_sha, "environment claim")
    _file(state / "profile" / "xar-autoplayer-environment.json", environment_sha)
    environment = _json(state / "profile" / "xar-autoplayer-environment.json")
    _same(environment.get("format_version"), 1, "environment format")
    runtime = environment.get("agent_runtime")
    if (type(runtime) is not dict or type(runtime.get("files")) is not list
            or type(runtime.get("file_count")) is not int
            or runtime["file_count"] < 1
            or runtime["file_count"] != len(runtime["files"])):
        raise ValueError("environment runtime inventory malformed")
    rebind_path = state / "ordinary-seed-rebind-v1.json"
    proof_before[rebind_path] = _sha(rebind_path)
    rebind_sha = str(admission.get("official_rebind_receipt_sha256", ""))
    _same(manifest.get("rebind_receipt_sha256"), rebind_sha, "rebind claim")
    _file(rebind_path, rebind_sha)
    rebind = _json(rebind_path)
    _same(rebind.get("schema"), "xar.ck3.ordinary-seed-rebind/v1", "rebind schema")
    _same(rebind.get("ok"), True, "rebind ok")
    _same(rebind.get("status"), "rebound", "rebind status")
    _same(rebind.get("ck3_launch_attempted"), False, "rebind launch")
    _same(rebind.get("desktop_interaction"), False, "rebind desktop")
    _same(rebind.get("pipe_name"), PIPE, "rebind pipe")
    _same(Path(str(rebind.get("state_dir"))).resolve(), state, "rebind state")
    _same(rebind.get("environment", {}).get("target_sha256"), environment_sha, "rebind environment")
    _same(rebind.get("driver_state", {}).get("target_sha256"), prepared_driver_sha, "rebind driver")
    raw_preflight_path = Path(str(admission.get("official_preflight_report")))
    _reject_links(raw_preflight_path)
    _reject_links(state / "preflights")
    preflight_path = raw_preflight_path.resolve()
    if not preflight_path.is_relative_to((state / "preflights").resolve()):
        raise ValueError("preflight outside exact attempt-14 state")
    _file(preflight_path, FROZEN_A14_SHA256["state/preflights/report.json"])
    proof_before[preflight_path] = _sha(preflight_path)
    preflight_sha = str(admission.get("official_preflight_report_sha256", ""))
    _same(manifest.get("preflight_report_sha256"), preflight_sha, "preflight claim")
    _file(preflight_path, preflight_sha)
    preflight = _json(preflight_path)
    _same(preflight.get("format_version"), 1, "preflight format")
    _same(preflight.get("kind"), "ck3_native_one_generation_preflight", "preflight kind")
    _same(Path(str(preflight.get("report_path"))).resolve(), preflight_path, "preflight report path")
    _same(preflight.get("pipe"), PIPE, "preflight pipe")
    _same(preflight.get("ok"), True, "preflight ok")
    _same(preflight.get("status"), "ready", "preflight status")
    _same(preflight.get("ck3_launch_attempted"), False, "preflight launch")
    _same(preflight.get("desktop_interaction"), False, "preflight desktop")
    _same(preflight.get("process_inventory", {}).get("processes"), [], "preflight inventory")
    anchor = preflight.get("resume_anchor")
    if type(anchor) is not dict:
        raise ValueError("preflight anchor unavailable")
    checkpoint, driver = anchor.get("checkpoint"), anchor.get("driver_state")
    if type(checkpoint) is not dict or type(driver) is not dict:
        raise ValueError("preflight anchor malformed")
    _same(checkpoint.get("saved_date_raw"), 53219928, "checkpoint date")
    _same(checkpoint.get("history_index"), 3937, "checkpoint history")
    _same(driver.get("episode_run_id"), "native-29829-2bc2d599f7f9", "driver episode")
    _same(driver.get("episode_character_id"), 29829, "driver actor")
    _same(checkpoint.get("succession_lifecycle"), driver.get("succession_lifecycle"), "lifecycle agreement")
    lifecycle = checkpoint.get("succession_lifecycle")
    if type(lifecycle) is not dict:
        raise ValueError("lifecycle unavailable")
    for field, expected in (("lifecycle", "ordinary_campaign_succession"), ("xar_enabled", "xar_off"),
                            ("pact_contract", "absent_by_fresh_campaign_xar_off_contract"),
                            ("environment_sha256", environment_sha)):
        _same(lifecycle.get(field), expected, f"lifecycle {field}")
    _same(preflight.get("profile", {}).get("environment_sha256"), environment_sha, "preflight environment")
    _same(preflight.get("profile", {}).get("ck3_executable_sha256"), GAME_SHA256, "preflight game")
    for name in ("interpreter-probe.json", "source-validation.json"):
        path = no_launch / name
        if not path.is_file():
            raise ValueError(f"no-launch proof missing: {name}")
    _same(manifest.get("interpreter_probe_sha256"), _sha(no_launch / "interpreter-probe.json"), "interpreter probe")
    _same(admission.get("interpreter_probe_sha256"), _sha(no_launch / "interpreter-probe.json"), "admission interpreter probe")
    source_validation = _json(no_launch / "source-validation.json")
    _same(source_validation.get("schema"), "xar.war.h3937-combined-no-launch-source-validation.v1", "source validation schema")
    _same(source_validation.get("candidate_head"), HEAD, "source validation HEAD")
    _same(source_validation.get("candidate_clean"), True, "source validation clean")
    _same(source_validation.get("live_run_id"), RUN_ID, "source validation run")
    _same(source_validation.get("live_run_identity_sha256"), _sha(identity_path), "source validation allocator")
    _same(source_validation.get("interpreter_probe_sha256"), _sha(no_launch / "interpreter-probe.json"), "source validation interpreter")
    _same(source_validation.get("screen_lease_acquired"), False, "source validation screen")
    _same(source_validation.get("steam_fresh_offline_reviewed"), False, "source validation Steam")
    sources = source_validation.get("source")
    if type(sources) is not dict:
        raise ValueError("source validation asset map unavailable")
    for name, digest in (("xar_checkpoint.ck3", CHECKPOINT_SHA256),
                         ("driver-state.json", RAW_DRIVER_SHA256),
                         ("player-child-matrilineal-formal-v1.json", SIDECAR_SHA256),
                         ("xar_ck3_bridge.dll", DLL_SHA256),
                         ("xar_ck3_bridge_injector.exe", INJECTOR_SHA256)):
        item = sources.get(name)
        if type(item) is not dict:
            raise ValueError(f"source validation missing {name}")
        _same(item.get("sha256"), digest, f"source validation {name}")
    probe = _json(no_launch / "interpreter-probe.json")
    if (type(probe.get("schema")) is not str
            or not probe["schema"].startswith("xar.war.h3937-a14-")
            or not probe["schema"].endswith("-interpreter-dependency-probe.v1")):
        raise ValueError("a14 interpreter probe schema differs")
    _same(probe.get("candidate_head"), HEAD, "interpreter probe HEAD")
    _same(probe.get("environment", {}).get("python"), str(PYTHON), "interpreter probe path")
    _same(probe.get("environment", {}).get("python_version"), "Python 3.14.7", "interpreter probe version")
    if any((LIVE_ROOT / item).exists() for item in ("attempt-14", "go-attempt-14.json", "screen-attempt-14")):
        raise ValueError("a14 live/GO/screen path already exists")
    for key, (relative, expected) in SOURCE_BLOBS.items():
        _same(_blob(source_root / relative), expected, f"source readback {key}")
    for relative, expected in ENTRY_BLOBS.items():
        _same(_blob(checkout / relative), expected, f"entry/bus readback {relative}")
    for path, digest in proof_before.items():
        _file(path, digest)
    for path, digest in FROZEN_A14_PRODUCER.values():
        _file(path, digest)
    _file(ALLOCATOR_STDOUT, ALLOCATOR_STDOUT_SHA256)
    _file(ALLOCATOR_COMMAND, ALLOCATOR_COMMAND_SHA256)
    _same(json.loads(ALLOCATIONS.read_text(encoding="utf-8").splitlines()[116]), identity,
          "allocation journal R0117 readback")
    _same(_json(ALLOCATOR_COUNTER).get("last_run_id"), RUN_ID, "allocator counter readback")
    if any(RUN_ID in line for line in ALLOCATOR_STATUSES.read_text(encoding="utf-8").splitlines()):
        raise ValueError("R0117 status appeared during seal")
    for path, digest in (
        (checkout / "tools" / "codex_task_bus.py", BUS_SHA256),
        (GAME / "binaries" / "ck3.exe", GAME_SHA256),
        (no_launch / "source-verified" / "xar_ck3_bridge.dll", DLL_SHA256),
        (no_launch / "source-verified" / "xar_ck3_bridge_injector.exe", INJECTOR_SHA256),
        (no_launch / "source-verified" / "xar_checkpoint.ck3", CHECKPOINT_SHA256),
        (no_launch / "source-verified" / "driver-state.json", RAW_DRIVER_SHA256),
        (no_launch / "source-verified" / "player-child-matrilineal-formal-v1.json", SIDECAR_SHA256),
        (state / "profile" / "save games" / "xar_checkpoint.ck3", CHECKPOINT_SHA256),
        (state / "player-child-matrilineal-formal-v1.json", SIDECAR_SHA256),
        (state / "native-session" / "driver-state.json", prepared_driver_sha),
        (state / "profile" / "xar-autoplayer-environment.json", environment_sha),
    ):
        _file(path, digest)
    _same(_head(checkout), HEAD, "candidate HEAD readback")
    if (state / "control" / "unsafe-cleanup.json").exists():
        raise ValueError("unsafe native cleanup marker appeared")
    if any((LIVE_ROOT / item).exists() for item in ("attempt-14", "go-attempt-14.json", "screen-attempt-14")):
        raise ValueError("a14 live/GO/screen path appeared")
    return {
        "schema": "xar.war.h3937-r0117-a14-static-seal.v1",
        "status": "STATIC_SEALED", "candidate_head": HEAD,
        "candidate_checkout": str(checkout), "round": ROUND,
        "live_run_id": RUN_ID, "execution_id": EXECUTION_ID,
        "no_launch_dir": str(no_launch), "attempt_id": "attempt-14",
        "admission_sha256": FROZEN_A14_SHA256["admission.json"],
        "operator_manifest_sha256": FROZEN_A14_SHA256["operator-manifest.json"],
        "live_run_identity_sha256": FROZEN_A14_SHA256["live-run-identity.json"],
        "original_allocator_stdout_sha256": ALLOCATOR_STDOUT_SHA256,
        "original_allocator_command_sha256": ALLOCATOR_COMMAND_SHA256,
        "source_validation_sha256": FROZEN_A14_SHA256["source-validation.json"],
        "interpreter_probe_sha256": FROZEN_A14_SHA256["interpreter-probe.json"],
        "official_rebind_receipt_sha256": rebind_sha,
        "official_preflight_report_sha256": preflight_sha,
        "source_git_blobs": source_blobs,
        "seal_scope": "frozen allowlist and reviewed a14 proof bytes",
        "checkout_clean_independently_verified": False,
        "a14_reviewed_proof_sha256": FROZEN_A14_SHA256,
        "a14_reviewed_producer_sha256": {
            label: {"path": str(path), "sha256": digest}
            for label, (path, digest) in FROZEN_A14_PRODUCER.items()},
        "task_bus_source_sha256": BUS_SHA256,
        "dll_sha256": DLL_SHA256, "injector_sha256": INJECTOR_SHA256,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "raw_driver_sha256": RAW_DRIVER_SHA256,
        "prepared_driver_sha256": prepared_driver_sha,
        "sidecar_sha256": SIDECAR_SHA256,
        "environment_sha256": environment_sha,
        "maximum_query_actions_if_later_authorized": 6,
        "screen_lease_acquired": False, "fresh_steam_offline_proven": False,
        "go_created": False, "worker_created": False,
        "ck3_launch_attempted": False, "live_authorized": False,
        "query_actions": 0, "gameplay_actions": 0,
        "date_move_attack_authorized": False,
        "next_gate": "fresh exclusive screen lease, fresh original Steam offline direct review, fresh GO and worker preflight",
    }


def seal_attempt(output: Path, checkout: Path = CANDIDATE,
                 no_launch: Path = NO_LAUNCH) -> dict[str, object]:
    """Consume a new output directory even for STOP; never overwrite evidence."""
    _reject_links(output)
    _reject_links(OUTPUT_ROOT)
    if output.resolve().parent != OUTPUT_ROOT.resolve() or not output.name.startswith("attempt-"):
        raise ValueError("seal output must be a new external attempt directory")
    if any(OUTPUT_ROOT.resolve().is_relative_to(item.resolve()) for item in (checkout, no_launch, LIVE_ROOT)):
        raise ValueError("seal root overlaps candidate, no-launch or live roots")
    output.mkdir(parents=True, exist_ok=False)
    try:
        result = verify(checkout, no_launch)
    except BaseException as error:
        result = {
            "schema": "xar.war.h3937-r0117-a14-static-seal.v1",
            "status": "STOP_INPUTS_INVALID", "candidate_head_expected": HEAD,
            "candidate_checkout": str(checkout), "no_launch_dir": str(no_launch),
            "attempt_id": "attempt-14", "reason": f"{type(error).__name__}: {error}",
            "screen_lease_acquired": False, "go_created": False,
            "worker_created": False, "ck3_launch_attempted": False,
            "live_authorized": False, "query_actions": 0,
            "date_move_attack_authorized": False,
        }
    result["sealed_at_utc"] = datetime.now(timezone.utc).isoformat()
    target = output / "seal.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="new empty external attempt directory")
    args = parser.parse_args()
    result = seal_attempt(args.output)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "STATIC_SEALED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
