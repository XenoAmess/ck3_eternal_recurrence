"""Offline empirical UI-resolution review of completed unknown-choice receipts.

This module does not choose an option, call the Game, or infer business effects.
Only a separately verified disappearance of the original window plus later
game-date progress can elevate a runtime GUI source to observed UI recovery.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdefABCDEF" for c in value)


def _stable_rva(value: object) -> bool:
    return (type(value) is int and 0 < value <= 2**64 - 1) or (
        isinstance(value, str) and bool(value))


def bound_backend_sha256(state_dir: Path, snapshot: dict) -> str | None:
    """Use this attempt's immutable launch receipt, never a guessed DLL hash."""
    try:
        diagnostics = snapshot.get("diagnostics")
        if not isinstance(diagnostics, dict):
            return None
        game_pid = diagnostics.get("bridge_pid")
        if type(game_pid) is not int or game_pid <= 0:
            return None
        launch = json.loads((Path(state_dir).parent /
                             "ROOT-ACTUAL-GAME-LAUNCH.json").read_text(encoding="utf-8"))
        if (not isinstance(launch, dict) or launch.get("pid") != game_pid
                or not _sha256(launch.get("dll_sha256"))):
            return None
        return launch["dll_sha256"].lower()
    except (OSError, ValueError, TypeError):
        return None


def stable_source_key(dto: dict, *, backend_sha256: str | None) -> dict | None:
    """Hash only build/widget/callback facts; exclude tokens, pointers and rects."""
    stable = (dto.get("stable_source_identity") or dto.get("source_identity")) if isinstance(dto, dict) else None
    if not isinstance(stable, dict) or not _sha256(backend_sha256):
        return None
    required = ("game_exe_sha256", "native_adapter_id", "root_runtime_name",
                "root_type", "root_vtable_module_rva")
    if (not _sha256(stable.get("game_exe_sha256"))
            or any(not isinstance(stable.get(k), str) or not stable[k]
                   for k in required[1:4])
            or not _stable_rva(stable.get("root_vtable_module_rva"))
            or (stable.get("backend_sha256") is not None
                and (not _sha256(stable["backend_sha256"])
                     or stable["backend_sha256"].lower() != backend_sha256.lower()))):
        return None
    choices = dto.get("choices")
    catalogue = stable.get("choice_catalogue")
    if not isinstance(choices, list) or not isinstance(catalogue, list):
        return None
    actual = {str(row.get("choice_id")): row for row in choices
              if isinstance(row, dict) and row.get("choice_id") is not None}
    if len(actual) != len(choices) or len(catalogue) != len(choices):
        return None
    normalized = []
    for index, row in enumerate(catalogue):
        if not isinstance(row, dict):
            return None
        # Native serializes the two arrays in the same order; older fixtures
        # also carry a catalogue choice_id.  Never infer an arbitrary match.
        shown = (actual.get(str(row["choice_id"])) if "choice_id" in row
                 else choices[index])
        if not isinstance(shown, dict):
            return None
        callbacks = row.get("callback_identities")
        if (not isinstance(row.get("runtime_name"), str) or not row["runtime_name"]
                or not _stable_rva(row.get("widget_vtable_module_rva"))
                or not isinstance(callbacks, list) or not callbacks):
            return None
        callback_rows = []
        for callback in callbacks:
            if (not isinstance(callback, dict)
                    or not _stable_rva(callback.get("vtable_module_rva"))
                    or not _stable_rva(callback.get("function_module_rva"))):
                return None
            callback_rows.append({"vtable_module_rva": callback["vtable_module_rva"],
                                  "function_module_rva": callback["function_module_rva"]})
        callback_rows.sort(key=lambda row: json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        normalized.append({"runtime_name": row["runtime_name"],
                           "widget_vtable_module_rva": row["widget_vtable_module_rva"],
                            "role": row.get("role", shown.get("role")),
                            "label": shown.get("label"),
                           "callback_identities": callback_rows})
    normalized.sort(key=lambda row: json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    source = {"game_exe_sha256": stable["game_exe_sha256"].lower(),
              "backend_sha256": backend_sha256.lower(),
              "native_adapter_id": stable["native_adapter_id"],
              "root_runtime_name": stable["root_runtime_name"],
              "root_type": stable["root_type"],
              "root_vtable_module_rva": stable["root_vtable_module_rva"],
              "choice_catalogue": normalized}
    encoded = json.dumps(source, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return {"source_key": hashlib.sha256(encoded).hexdigest(), "stable_source": source}


def _progress_frame(progress: dict | None) -> dict | None:
    """Read the claimed frame from the exact immutable artifact, not a caller copy."""
    if not isinstance(progress, dict) or not _sha256(progress.get("source_sha256")):
        return None
    path = Path(progress.get("source_path", ""))
    if not path.is_file() or path.name == "driver-state.json":
        return None
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != progress["source_sha256"].lower():
        return None
    source = json.loads(raw)
    value = source
    pointer = progress.get("json_pointer")
    if not isinstance(pointer, list):
        return None
    for key in pointer:
        if not isinstance(value, dict) or not isinstance(key, str) or key not in value:
            return None
        value = value[key]
    if not isinstance(value, dict):
        return None
    frame = dict(value)
    if "game_pid" not in frame:
        launch_path = Path(progress.get("game_launch_receipt_path", ""))
        launch_sha = progress.get("game_launch_receipt_sha256")
        if (not _sha256(launch_sha) or not launch_path.is_file()
                or not path.resolve().is_relative_to(launch_path.parent.resolve())):
            return None
        launch_raw = launch_path.read_bytes()
        if hashlib.sha256(launch_raw).hexdigest() != launch_sha.lower():
            return None
        launch = json.loads(launch_raw)
        if not isinstance(launch, dict) or type(launch.get("pid")) is not int:
            return None
        frame["game_pid"] = launch["pid"]
    if isinstance(source, dict):
        frame["_source_ended_at_utc"] = source.get("ended_at_utc")
    return frame


def analyze_completed_incident(
    before: dict, after: dict, *, backend_sha256: str | None,
    later_progress: dict | None = None,
) -> dict:
    """Return unresolved or a source-bound observed-UI recovery fact only."""
    result = {"status": "unresolved", "known_recovery_source": None,
              "business_effect_known": False, "semantic_optimal": False,
              "reason": "incomplete_evidence"}
    if (not isinstance(before, dict) or not isinstance(after, dict)
            or before.get("incident_id") != after.get("incident_id")):
        return {**result, "reason": "incident_pair_mismatch"}
    dto = before.get("native_window")
    frame = before.get("frame_binding")
    selection = before.get("selection")
    if not isinstance(dto, dict) or not isinstance(frame, dict) or not isinstance(selection, dict):
        return {**result, "reason": "original_window_or_binding_missing"}
    source = stable_source_key(dto, backend_sha256=backend_sha256)
    if source is None:
        return {**result, "reason": "stable_build_widget_callback_source_unavailable"}
    receipt = after.get("action_receipt")
    post = receipt.get("mandatory_choice_postcondition") if isinstance(receipt, dict) else None
    old_gone = bool(
        after.get("original_blocking_window_advanced_verified") is True
        and isinstance(receipt, dict) and receipt.get("accepted") is True
        and isinstance(post, dict) and post.get("verified") is True
        and post.get("old_window_id") == dto.get("window_id")
        and post.get("old_instance") == dto.get("window_instance_id")
        and post.get("selected_choice_id") == selection.get("choice_id")
        and post.get("old_window_no_longer_blocking") is True)
    if not old_gone:
        return {**result, **source, "reason": "original_window_disappearance_unverified"}
    later = _progress_frame(later_progress)
    if (not isinstance(later, dict)
            or any(later.get(key) != frame.get(key) for key in (
                "game_pid", "connection_generation", "episode_run_id", "actor_character_id"))
            or type(later.get("date_raw")) is not int
            or later["date_raw"] <= frame.get("date_raw", -1)
            or type(later.get("native_revision")) is not int
            or later["native_revision"] <= frame.get("native_revision", -1)):
        return {**result, **source, "reason": "later_same_game_date_progress_unverified"}
    if (isinstance(after.get("captured_at_utc"), str)
            and isinstance(later.get("_source_ended_at_utc"), str)
            and later["_source_ended_at_utc"] <= after["captured_at_utc"]):
        return {**result, **source, "reason": "later_response_precedes_original_selection"}
    return {"status": "known_ui_recovery_observed",
            "known_recovery_source": "observed-UI",
            "business_effect_known": False, "semantic_optimal": False,
            "incident_id": before["incident_id"],
            "selected_choice_id": selection.get("choice_id"),
            "source_key": source["source_key"],
            "stable_source": source["stable_source"],
            "original_window_instance": dto.get("window_instance_id"),
            "date_raw_before": frame["date_raw"],
            "date_raw_after": later["date_raw"],
            "later_source_path": later_progress["source_path"],
            "later_source_sha256": later_progress["source_sha256"]}


def lookup_observed_ui_recovery(
    dto: dict, *, backend_sha256: str | None, review_root: Path,
) -> dict | None:
    """Recheck immutable old evidence before labelling a fresh source known."""
    source = stable_source_key(dto, backend_sha256=backend_sha256)
    if source is None:
        return None
    directory = Path(review_root) / "known-ui-recovery" / source["source_key"]
    if not directory.is_dir():
        return None
    for review_path in sorted(directory.glob("*.json")):
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
            if (not isinstance(review, dict)
                    or review.get("status") != "known_ui_recovery_observed"
                    or review.get("known_recovery_source") != "observed-UI"
                    or review.get("business_effect_known") is not False
                    or review.get("semantic_optimal") is not False
                    or review.get("source_key") != source["source_key"]
                    or review.get("stable_source") != source["stable_source"]):
                continue
            before_path = Path(review["before_path"])
            after_path = Path(review["after_path"])
            if (before_path.parent != after_path.parent
                    or before_path.parent.name != "unknown-mandatory-choices"
                    or before_path.parent.parent.name != "evidence"
                    or before_path.parent.parent.parent.name != "state"):
                continue
            attempt = before_path.parents[3]
            launch_path = attempt / "ROOT-ACTUAL-GAME-LAUNCH.json"
            launch_raw = launch_path.read_bytes()
            launch = json.loads(launch_raw)
            if (not isinstance(launch, dict)
                    or not _sha256(launch.get("dll_sha256"))
                    or launch["dll_sha256"].lower() != backend_sha256.lower()):
                continue
            before_raw, after_raw = before_path.read_bytes(), after_path.read_bytes()
            if (hashlib.sha256(before_raw).hexdigest() != review["before_sha256"].lower()
                    or hashlib.sha256(after_raw).hexdigest() != review["after_sha256"].lower()):
                continue
            before, after = json.loads(before_raw), json.loads(after_raw)
            if (not isinstance(before, dict)
                    or not isinstance(before.get("frame_binding"), dict)
                    or launch.get("pid") != before["frame_binding"].get("game_pid")):
                continue
            progress = {
                "source_path": review["later_source_path"],
                "source_sha256": review["later_source_sha256"],
                "json_pointer": ["result", "structured_content"],
                "game_launch_receipt_path": str(launch_path),
                "game_launch_receipt_sha256": hashlib.sha256(launch_raw).hexdigest(),
            }
            checked = analyze_completed_incident(
                before, after, backend_sha256=backend_sha256,
                later_progress=progress)
            if (checked.get("status") == "known_ui_recovery_observed"
                    and checked.get("source_key") == source["source_key"]
                    and checked.get("selected_choice_id") == review.get("selected_choice_id")):
                return {"known_recovery_source": "observed-UI",
                        "source_key": source["source_key"],
                        "review_path": str(review_path),
                        "observed_choice_id": review.get("selected_choice_id"),
                        "business_effect_known": False,
                        "semantic_optimal": False}
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            continue
    return None
