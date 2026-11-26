"""Exact .3/.4 HUD Decisions opening; no decision-row or product panel action."""
from __future__ import annotations
from .version_identity import CK3_12003, CK3_12004, NativeBuildIdentity, require_exact_native_build

STEP = "activate-ingame-decisions-v1"
CAPABILITY = "game.command.activate-ingame-decisions-v1"
EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"


def result_build(raw: object) -> NativeBuildIdentity:
    if not isinstance(raw, dict):
        raise ValueError("missing exact native result")
    build = require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256"))
    if build not in (CK3_12003, CK3_12004):
        raise ValueError("requires exact .3/.4 native result")
    return build

def opening_snapshot_build(snapshot: dict[str, object]) -> NativeBuildIdentity:
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    if not isinstance(hello, dict):
        raise ValueError("missing exact native hello")
    return require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))


def opening_binding(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("missing paused native snapshot")
    character = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError("missing exact native hello")
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict):
        raise ValueError("missing exact native hello")
    build = opening_snapshot_build(snapshot)
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(character, dict) or character.get("alive") is not True
            or not isinstance(hello, dict) or hello.get("ck3_build_match") is not True
            or hello.get("game_adapter_id") != f"ck3-{build.game_version}-msvc-x64"
            or build not in (CK3_12003, CK3_12004)):
        raise ValueError("requires exact .3/.4 alive paused map")
    values = {"native_revision": snapshot.get("native_revision"),
              "connection_generation": diagnostics.get("connection_generation"),
              "game_pid": hello.get("pid"),
              "played_character_id": character.get("character_id"),
              "date_raw": snapshot.get("date_raw"),
              "episode_run_id": snapshot.get("episode_run_id")}
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id"):
        val = values[key]
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            raise ValueError(f"invalid {key}")
    if isinstance(values["date_raw"], bool) or not isinstance(values["date_raw"], int):
        raise ValueError("invalid native date")
    return values

def normalize_open_result(raw: object, binding: dict[str, object]) -> dict[str, object]:
    result_build(raw)
    if (not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-decisions-open-v1"
            or raw.get("step") != STEP):
        raise ValueError("malformed exact .3/.4 opening result")
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != binding[key]:
            raise ValueError(f"native opening {key} changed")
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
                "gui_owner_binding_verified", "native_after_read"):
        if raw.get(key) is not True:
            raise ValueError(f"opening proof unavailable: {key}")
    for key in ("before_visible", "dispatch_invoked", "native_after_visible", "native_after_tree_complete", "postcondition_verified", "verification_pending"):
        if type(raw.get(key)) is not bool:
            raise ValueError(f"opening lacks actual {key}")
    if raw["dispatch_invoked"]:
        if (raw["before_visible"] is not False or raw.get("topbar_tree_complete") is not True
                or raw.get("receiver_qualified") is not True):
            raise ValueError("native dispatch lacks complete HUD receiver proof")
    elif raw["before_visible"] is not True:
        raise ValueError("Decisions was neither open nor submitted")
    verified = raw["native_after_tree_complete"] and raw["native_after_visible"]
    if raw["postcondition_verified"] != verified:
        raise ValueError("native visibility proof is inconsistent")
    if raw["verification_pending"] != (raw["dispatch_invoked"] and not verified):
        raise ValueError("native pending proof is inconsistent")
    return dict(raw)

def actual_visible_decisions_tree(tree: object) -> bool:
    if not isinstance(tree, dict) or tree.get("scope_root_name") != "decisions_view" or tree.get("truncated") is not False:
        raise ValueError("Decisions census is incomplete or mismatched")
    if tree.get("root_available") is not True:
        return False
    rows = tree.get("widgets")
    if not isinstance(rows, list):
        raise ValueError("Decisions census rows are absent")
    roots = [row for row in rows if isinstance(row, dict) and row.get("child_path") == ""]
    if len(roots) != 1 or roots[0].get("runtime_name") != "decisions_view":
        raise ValueError("actual Decisions root is unverified")
    return roots[0].get("effective_visible") is True


def validate_current_decisions_observation(
    result: dict[str, object], *, expected_revision: int | None,
) -> None:
    """Validate the SDK's fresh read-only proof separately from the native opener ACK."""
    from .gui_window_tree_contract import normalize_gui_window_tree_v1

    result_build(result)
    revision = result.get("queried_revision")
    tree = result.get("later_decisions_tree")
    if (result.get("schema") != "ck3-ingame-decisions-open-v1" or result.get("step") != STEP
            or result.get("status") != "verified_visible"
            or result.get("completion_source") != "observed_already_visible"
            or result.get("read_only") is not True or result.get("dispatch_invoked") is not False
            or result.get("postcondition_verified") is not True
            or result.get("verification_pending") is not False
            or any(key not in result or result[key] is not None
                   for key in ("native_ack", "action_request_id", "action_claim_path"))
            or type(revision) is not int or revision < 0
            or (expected_revision is not None and revision != expected_revision)
            or not isinstance(tree, dict)
            or tree.get("schema") != "ck3-native-gui-window-tree-inspection-v1"
            or tree.get("window_kind") != "decisions" or tree.get("read_only") is not True
            or not actual_visible_decisions_tree(normalize_gui_window_tree_v1(tree, "decisions"))):
        raise ValueError("Decisions requires a complete current visible root without action evidence")
