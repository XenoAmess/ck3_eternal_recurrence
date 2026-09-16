"""Select one real, isolated Council final-gate rejection; never invent an ID."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from inspect_council_final_gate_scene import inspect


SCHEMA = "xar.ck3.private.council-four-gate-reject/1.19.0.6-v1"
CANDIDATE_SCHEMA = "xar.ck3.private.council-four-gate-reject-candidate/1.19.0.6-v1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
PRIVATE_FLAGS = {
    "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1": "ON",
}
GATES = {
    "already_councillor": (
        "isolated_already_councillor_rejection_ids", "candidate_already_councillor"
    ),
    "guest": ("isolated_guest_rejection_ids", "candidate_is_guest"),
    "candidate_pending": (
        "isolated_candidate_pending_rejection_ids", "pending_character_interaction"
    ),
    "replacement_fireability_denial": (
        "isolated_replacement_fireability_denial_ids", "incumbent_cannot_be_replaced"
    ),
}


class PositiveSceneMissing(ValueError):
    """A real native query contains no isolated positive for the requested gate."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def select(terminal: Path, expected_sha256: str, gate: str) -> dict[str, object]:
    if gate not in GATES:
        raise ValueError(f"unsupported Council final gate: {gate}")
    scene = inspect(terminal, expected_sha256)
    field, failure = GATES[gate]
    ids = scene[field]
    if not ids:
        raise PositiveSceneMissing(f"{gate}: no isolated native-positive provider row")
    if scene["position_key"] != "councillor_steward":
        raise ValueError("native scene does not contain the steward seat")
    if scene["native_helper_invocations_delta"] != 0 or scene["public_registered_or_advertised"]:
        raise ValueError("scene query was not private and action-free")
    selected_id = ids[0]  # Inspector sorted real, unique full CharacterIDs.
    return {
        "schema": SCHEMA,
        "gate": gate,
        "expected_failure": failure,
        "candidate_character_id": selected_id,
        "isolated_positive_ids": ids,
        "owner_character_id": scene["owner_character_id"],
        "incumbent_character_id": scene["incumbent_character_id"],
        "vacant": scene["vacant"],
        "candidate_count": scene["candidate_count"],
        "snapshot": scene["snapshot"],
        "terminal_sha256": expected_sha256.upper(),
        "typed_action_verified": False,
        "public_registered_or_advertised": False,
    }


def validate_rejection_ack(ack: dict[str, object], plan: dict[str, object]) -> None:
    if (ack.get("status") != "rejected_before_submit"
            or ack.get("failure") != plan["expected_failure"]
            or ack.get("native_helper_invoked") is not False
            or ack.get("verification_pending") is not False
            or ack.get("queue_acceptance_observed") is not False):
        raise ValueError(f"{plan['gate']} did not reject before native helper: {ack!r}")


def read_plan(path: Path, terminal: Path) -> dict[str, object]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        raise ValueError("private Council rejection plan schema differs")
    observed = select(terminal, str(plan.get("terminal_sha256")), str(plan.get("gate")))
    if plan != observed:
        raise ValueError("frozen Council rejection plan differs from exact native scene")
    return plan


def verify_candidate(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    """Bind a naturally positive native query to its game/driver cold-load pair."""
    root = root.resolve()
    manifest = json.loads((root / "council-four-reject-candidate.json").read_text(
        encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("Council private candidate schema differs")
    if manifest.get("status") != "sealed-no-launch" or manifest.get("public_registered_or_advertised") is not False:
        raise ValueError("candidate is unsealed or Council public capability leaked")
    gate = manifest.get("gate")
    if gate not in GATES:
        raise ValueError("candidate has no supported rejection gate")
    plan_path = root / "council-four-reject-plan.json"
    terminal = root / "native-scene-terminal.json"
    plan = read_plan(plan_path, terminal)
    if (manifest.get("gate") != plan["gate"]
            or manifest.get("scene_terminal_sha256") != sha256(terminal)
            or manifest.get("scene_terminal_sha256") != plan["terminal_sha256"]):
        raise ValueError("candidate is not bound to its native positive query")
    save_name = manifest.get("save_name")
    if (not isinstance(save_name, str) or not save_name
            or not all(c.isascii() and (c.isalnum() or c in "_-") for c in save_name)):
        raise ValueError("candidate save name is not an explicit CK3 -loadsave name")
    state = root / "fresh-profile-state"
    source = root / "source-save" / (save_name + ".ck3")
    target = state / "profile" / "save games" / (save_name + ".ck3")
    driver_path = state / "native-session" / "driver-state.json"
    save_hash = manifest.get("source_save_sha256")
    if (not isinstance(save_hash, str) or len(save_hash) != 64
            or sha256(source) != save_hash or sha256(target) != save_hash
            or sha256(driver_path) != manifest.get("driver_state_sha256")):
        raise ValueError("CK3 source/target save and agent driver are not a frozen pair")
    if source.open("rb").read(7) != b"SAV0101":
        raise ValueError("source is not a CK3 SAV0101 checkpoint")
    driver = json.loads(driver_path.read_text(encoding="utf-8"))
    checkpoint = driver.get("last_checkpoint")
    if (driver.get("format_version") != 2
            or driver.get("episode_character_id") != plan["owner_character_id"]
            or not isinstance(checkpoint, dict)
            or str(checkpoint.get("sha256", "")).upper() != save_hash
            or checkpoint.get("date_raw") != plan["snapshot"]["date_raw"]
            or checkpoint.get("episode_character_id") != plan["owner_character_id"]):
        raise ValueError("driver checkpoint does not belong to paused Council scene")
    if manifest.get("game_exe_sha256") != EXE_SHA256:
        raise ValueError("candidate CK3 exact build differs")
    game_dir = Path(str(manifest.get("game_dir", ""))).resolve()
    if sha256(game_dir / "binaries" / "ck3.exe") != EXE_SHA256:
        raise ValueError("operator CK3 executable differs")
    python = Path(str(manifest.get("python", ""))).resolve()
    if sha256(python) != manifest.get("python_exe_sha256"):
        raise ValueError("operator Python differs from sealed candidate")
    for name, key in (("xar_ck3_bridge.dll", "bridge_dll_sha256"),
                      ("xar_ck3_bridge_injector.exe", "injector_sha256")):
        if sha256(root / "candidate-bin" / name) != manifest.get(key):
            raise ValueError(f"candidate native binary differs: {name}")
    cache = (root / "candidate-bin" / "CMakeCache.txt").read_text(
        encoding="utf-8", errors="replace")
    if manifest.get("cmake_options") != PRIVATE_FLAGS or any(
            f"{key}:BOOL={value}" not in cache for key, value in PRIVATE_FLAGS.items()):
        raise ValueError("candidate native action/query flags are not private ON")
    load = json.loads((state / "profile" / "dlc_load.json").read_text(encoding="utf-8-sig"))
    if load != {"enabled_mods": ["mod/xar_autoplayer.mod"], "disabled_dlcs": []}:
        raise ValueError("candidate DLC/mod pair differs from bounded feudal scope")
    descriptor = (state / "profile" / "mod" / "xar_autoplayer.mod").read_text(
        encoding="utf-8-sig")
    mod_root = (state / "profile" / "mod-content" / "xar-production").as_posix()
    if f'path="{mod_root}"' not in descriptor:
        raise ValueError("candidate mod descriptor does not resolve to its own tree")
    if not (root / "source-repo" / "ck3_autonomous_player" / "src").is_dir():
        raise ValueError("candidate Python runtime source tree is absent")
    return manifest, plan
