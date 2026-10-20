"""A10 closed WAL and pure-vanilla environment migration; RAM only.

Root supplies exact source pins after Source27 qualification. This builder
publishes nothing and never starts a Game, SDK, Task or native command.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import TypeAlias, TypedDict

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]

sys.dont_write_bytecode = True
MACHINE = "xenoamess-full-tower-eb9d2c1186"
INDEX_PIN = (7036, "d0d13ae2cf51838092e1ae8c7b3a5bcb141bdd84313d56015ba12003f6cabfee")
SEED_PIN = (9054, "c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8")
OLD_ENV = "dbcb5ea688435677d945cef9fc9c73c31d01d229ec060c3a951e53701bf33b57"
BASE27_PIN = (398331, "c93cc3e4d4d4996a7787d0f4b095ae67b8e4d145e725f2d7e288c8010b64a8fe")
MODULES = (
    "bridge.driver_state_wal_v1", "bridge.native_driver",
    "checkpoint_environment_rebinder", "ordinary_seed_rebinder",
    "cold_checkpoint_validator", "bridge.succession_transition_contract", "environment",
)


class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str


class MigrationInput(TypedDict):
    schema: str
    machine_id: str
    execution_owner: str
    root_direct_execution_release: bool
    observed_at_utc: str
    sdk_root: str
    sdk_files: dict[str, ExactRef]
    source27_anchor: ExactRef
    sdk_base: ExactRef
    closure_index: ExactRef
    quiescence: ExactRef
    source_base: ExactRef
    source_wal: ExactRef
    source_identity: dict[str, list[str]]
    original_seed: ExactRef
    source_manifest: ExactRef
    target_manifest: ExactRef
    target_settings: ExactRef
    source_save_identity: list[str]
    target_driver_path: str
    target_seed_path: str
    receipt_path: str


def require(ok: object, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def future(path: str | Path, raw: bytes) -> ExactRef:
    return {"path": str(Path(path).resolve()), "bytes": len(raw), "sha256": digest(raw)}


def identity(path: Path) -> list[str]:
    st = path.stat()
    return [str(value) for value in (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)]


def read_exact(item: ExactRef, limit: int = 65536) -> bytes:
    path = Path(item["path"]).resolve(strict=True)
    require(path.is_file() and 0 < path.stat().st_size <= limit, "bounded input file")
    raw = path.read_bytes()
    require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "input pin changed")
    return raw


def checked(item: ExactRef, limit: int = 65536) -> JSONObject:
    return json.loads(read_exact(item, limit))


def load_sdk(plan: MigrationInput) -> tuple[dict[str, ModuleType], dict[str, ExactRef]]:
    root = Path(plan["sdk_root"]).resolve(strict=True)
    require((plan["sdk_base"]["bytes"], plan["sdk_base"]["sha256"]) == BASE27_PIN,
            "actual Root Source27 BASE pin")
    base = checked(plan["sdk_base"], 524288)
    require(base["machine_id"] == MACHINE and base["status"] == "FINAL_SOURCE_FROZEN"
            and base["source_root"] == str(root)
            and base["business_source_commit"] == "4b0f3771b51d65af2cd6d576116535237aac7ef0"
            and base["source27_canonical_anchor"] == plan["source27_anchor"]
            and base["runtime_admitted"] is False, "actual Source27 compact BASE")
    rows = {row["relative"]: row for row in base["files"]}
    require(len(rows) == 1462 and sum(row["bytes"] for row in rows.values()) == 59255805,
            "Source27 complete SDK rows")
    sources = {}
    for relative in MODULES:
        item = plan["sdk_files"][relative]
        path = root / "xar_autoplayer" / (relative.replace(".", "/") + ".py")
        require(Path(item["path"]).resolve(strict=True) == path.resolve(strict=True),
                "SDK module root differs")
        row = rows["xar_autoplayer/" + relative.replace(".", "/") + ".py"]
        require((item["bytes"], item["sha256"]) == (row["bytes"], row["sha256"]),
                "SDK consumer does not match Source27 BASE")
        read_exact(item, 4194304)
        sources[relative] = item
    old = list(sys.path)
    sys.path.insert(0, str(root))
    try:
        for name, module in tuple(sys.modules.items()):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                origin = getattr(module, "__file__", None)
                require(origin is not None and Path(origin).resolve().is_relative_to(root),
                        "fresh Source27 Python process required")
        loaded = {name: importlib.import_module("xar_autoplayer." + name) for name in MODULES}
        for name, module in loaded.items():
            expected = Path(sources[name]["path"]).resolve(strict=True)
            require(Path(module.__file__).resolve() == expected
                    and Path(module.__spec__.origin).resolve() == expected,
                    "SDK imported module origin differs")
            read_exact(sources[name], 4194304)
    finally:
        sys.path[:] = old
    return loaded, sources


def compose_environment_migration(plan: MigrationInput) -> tuple[bytes, bytes, JSONObject, JSONObject]:
    require(set(plan) == set(MigrationInput.__annotations__), "exact migration input fields")
    require(plan["schema"] == "xar.C23-A10-environment-migration-input/v1"
            and plan["machine_id"] == MACHINE and plan["execution_owner"] == "Root"
            and plan["root_direct_execution_release"] is True, "Root migration release")
    at = datetime.fromisoformat(plan["observed_at_utc"].replace("Z", "+00:00"))
    require(-10 <= (datetime.now(timezone.utc) - at).total_seconds() <= 600, "fresh input UTC")
    index = checked(plan["closure_index"], 16384)
    require((plan["closure_index"]["bytes"], plan["closure_index"]["sha256"]) == INDEX_PIN
            and index["machine_id"] == MACHINE and index["next_sequence"] == 10521
            and index["SDK_actual_exits"] == [1, 0] and index["Game_actual_exit"] == 1
            and index["Game_forced"] is True and index["unknown_AUTO"] == 10519
            and index["saved_cycles"] == 4753 and index["settled_cycles"] == 4760
            and index["screen_release_sequence"] == 7681, "actual A09 closed authority")
    quiescence = checked(plan["quiescence"], 16384)
    require(quiescence["schema"] == "xar.C23-A10-quiescent-preparation/v1"
            and quiescence["machine_id"] == MACHINE
            and quiescence["game_processes"] == quiescence["sdk_processes"] == []
            and quiescence["supervisor_task_registered"] is False
            and quiescence["evidence_refs"], "actual fresh cold quiescence")
    q_at = datetime.fromisoformat(quiescence["observed_at_utc"].replace("Z", "+00:00"))
    require(-10 <= (datetime.now(timezone.utc) - q_at).total_seconds() <= 600,
            "quiescence evidence expired")
    for item in quiescence["evidence_refs"]:
        checked(item, 65536)
    checked(plan["source27_anchor"])
    require((plan["original_seed"]["bytes"], plan["original_seed"]["sha256"]) == SEED_PIN,
            "original saved seed pin")
    original_raw = read_exact(plan["original_seed"], 16384)
    original = json.loads(original_raw)
    source_manifest = checked(plan["source_manifest"], 32768)
    target_manifest = checked(plan["target_manifest"], 32768)
    require(source_manifest["machine_id"] == target_manifest["machine_id"] == MACHINE
            and source_manifest["schema"] == target_manifest["schema"]
            == "root.ck3.vanilla-isolated-environment/v1"
            and source_manifest["environment_sha256"] == OLD_ENV
            and target_manifest["environment_sha256"] != OLD_ENV, "explicit new vanilla environment")
    require(target_manifest["display"]["mode"] == "windowed"
            and target_manifest["display"]["resolution"] == [1280, 720]
            and target_manifest["load_profile"]["enabled_mods"] == [], "windowed vanilla target")
    expected_manifest = copy.deepcopy(source_manifest)
    expected_manifest["display"].update(mode="windowed", resolution=[1280, 720])
    expected_manifest["load_profile"]["pdx_settings_prepared_sha256"] = (
        target_manifest["load_profile"]["pdx_settings_prepared_sha256"])
    expected_manifest["load_profile"]["pdx_settings_contract"] = (
        target_manifest["load_profile"]["pdx_settings_contract"])
    expected_manifest["environment_sha256"] = target_manifest["environment_sha256"]
    expected_manifest["prepared_at"] = target_manifest["prepared_at"]
    require(target_manifest == expected_manifest, "only display/settings/digest/time migration")
    modules, sdk_sources = load_sdk(plan)
    environment = modules["environment"]
    require(environment._contract_digest(source_manifest) == OLD_ENV
            and environment._contract_digest(target_manifest)
            == target_manifest["environment_sha256"], "original environment digest algorithm")
    target_settings = read_exact(plan["target_settings"], 65536)
    require(Path(plan["target_settings"]["path"]).name == "pdx_settings.txt"
            and digest(target_settings)
            == target_manifest["load_profile"]["pdx_settings_prepared_sha256"],
            "target actual settings pin")
    settings_contract = environment.settings_contract(
        target_settings.decode("utf-8-sig"), display_mode="windowed",
        screen_edge_scroll_mode=environment.MANAGED_SCREEN_EDGE_SCROLL_MODE)
    require(settings_contract == target_manifest["load_profile"]["pdx_settings_contract"],
            "target exact settings semantic contract")
    base = Path(plan["source_base"]["path"]).resolve(strict=True)
    journal = Path(plan["source_wal"]["path"]).resolve(strict=True)
    require(base.name == "driver-state.json" and journal.parent == base.parent
            and journal.name == "driver-state.wal-v1.json", "exact closed pair")
    before = {"base": identity(base), "wal": identity(journal)}
    require(before == plan["source_identity"], "source pair identity changed")
    base_raw = read_exact(plan["source_base"], 41943040)
    wal_raw = read_exact(plan["source_wal"], 8388608)
    require(before == {"base": identity(base), "wal": identity(journal)}, "pair changed while reading")
    wal = modules["bridge.driver_state_wal_v1"]
    rebinder = modules["checkpoint_environment_rebinder"]
    replace = modules["ordinary_seed_rebinder"]._replace_lifecycle_anchors
    consumer = modules["bridge.native_driver"].load_native_driver_state_for_resume_payload
    cold = modules["cold_checkpoint_validator"].validate_cold_start_checkpoint_payload_for_pipe
    payload, status = wal.replay(base_raw, wal_raw)
    require(status == "replayed", "active sealed pair required")
    old_binding = rebinder._checkpoint_binding(payload)
    require(old_binding["environment_sha256"] == OLD_ENV
            and payload["last_checkpoint"] == original["actual_saved_checkpoint"],
            "original SAVE binding changed")
    pipe = payload["pipe_name"]
    require(consumer(payload, pipe) is not None, "original Driver consumer rejected")
    profile = Path(source_manifest["profile_dir"]).resolve(strict=True)
    save = profile / "save games" / "xar_checkpoint.ck3"
    require(identity(save) == plan["source_save_identity"], "original SAVE identity changed")
    spec = SimpleNamespace(profile_dir=profile)
    before_validation = cold(spec, pipe, payload)
    target_binding = {**old_binding, "environment_sha256": target_manifest["environment_sha256"]}
    rebound = replace(payload, target_binding)
    require(rebinder._checkpoint_binding(rebound) == target_binding
            and consumer(rebound, pipe) is not None, "target three-anchor consumer rejected")
    after_validation = cold(spec, pipe, rebound)
    require(identity(save) == plan["source_save_identity"], "SAVE changed during validation")
    normalized = copy.deepcopy(after_validation)
    normalized["succession_lifecycle"] = old_binding
    require(normalized == before_validation, "cold checkpoint semantics changed")
    target_bytes = wal.full_state_bytes(rebound)
    original_full_size = len(wal.full_state_bytes(payload))
    require(len(target_bytes) == original_full_size <= 41943040, "compact Driver size drift")
    seed = copy.deepcopy(original)
    seed["actual_saved_checkpoint"] = rebound["last_checkpoint"]
    seed_bytes = encoded(seed)
    require(encoded(original) == original_raw and len(seed_bytes) == len(original_raw),
            "derived seed must retain exact compact shape")
    for path in (plan["target_driver_path"], plan["target_seed_path"], plan["receipt_path"]):
        require(not Path(path).exists() and not Path(path).is_symlink(), "create-only target consumed")
    target_driver = future(plan["target_driver_path"], target_bytes)
    target_seed = future(plan["target_seed_path"], seed_bytes)
    receipt = {
        "schema": "xar.C23-A10-environment-migration/v1", "machine_id": MACHINE,
        "observed_at_utc": plan["observed_at_utc"], "reviewer": "/root",
        "status": "RAM_QUALIFIED_PENDING_ACTUAL_TARGET_MOD_ABSENCE",
        "source_pair": {"base": plan["source_base"], "wal": plan["source_wal"],
                        "identity": before},
        "source27_anchor": plan["source27_anchor"],
        "source27_export": checked(plan["sdk_base"], 524288)["immutable_source_export"],
        "sdk_base": plan["sdk_base"],
        "SDK_sources": sdk_sources,
        "quiescence": plan["quiescence"], "staged_target_settings": plan["target_settings"],
        "pending_apply_actual_target_settings": True,
        "target_settings_contract": settings_contract,
        "actual_A09_closure": plan["closure_index"], "original_seed": plan["original_seed"],
        "source_manifest": plan["source_manifest"], "target_manifest": plan["target_manifest"],
        "source_lifecycle": old_binding, "target_lifecycle": target_binding,
        "original_checkpoint": payload["last_checkpoint"],
        "target_checkpoint": rebound["last_checkpoint"],
        "target_driver": target_driver, "derived_seed": target_seed,
        "persisted_history_rows": len(payload["command_history"]),
        "history_or_actions_reconstructed": False, "SAVE_bytes_modified": False,
        "source_validation": before_validation, "target_validation": after_validation,
        "source_save_identity": plan["source_save_identity"],
        "method": "original WAL replay and pure rebind helpers; old v2 not written",
        "materialize_closed_directory_called": False, "outputs_written": 0,
        "rollback_cycles": 7, "rollback_days": 1, "unknown10519_credit": 0,
        "actual_next_sequence": 10521, "historical_helper_next_sequence": 10481,
        "actual_target_Game_mod_absence_verified": False, "Game_Task_RPC_calls": 0,
    }
    receipt_bytes = encoded(receipt)
    require(len(receipt_bytes) <= 16384, "small migration receipt exceeded")
    small_allocation = ((len(seed_bytes) + 4095) // 4096) * 4096
    receipt_allocation = ((len(receipt_bytes) + 4095) // 4096) * 4096
    quote = {
        "schema": "xar.C23-A10-environment-migration-quote/v1", "machine_id": MACHINE,
        "status": "RAM_READY_ROOT_CREATE_ONLY_WRITE_REQUIRED",
        "target_driver": target_driver, "derived_seed": target_seed,
        "receipt": future(plan["receipt_path"], receipt_bytes),
        "new_driver_allocation": ((len(target_bytes) + 4095) // 4096) * 4096,
        "small_allocation": small_allocation + receipt_allocation,
        "no_intermediate_v2_written": True, "actual_source_stat": before,
        "future_pre_gate": "actual new PID startup evidence + original binder == target checkpoint",
    }
    return target_bytes, seed_bytes, receipt, quote
