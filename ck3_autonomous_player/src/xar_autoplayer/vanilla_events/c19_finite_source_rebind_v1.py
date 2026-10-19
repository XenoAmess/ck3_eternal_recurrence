"""Two exact source-knowledge exceptions for a future C19 composition.

No implicit-type or letter default is enabled generally. The observed native
character root is authoritative for this knowledge shape; null/opaque roles
never provide an identity. This module grants no executable event contract.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from .builds import SUPPORTED_CK3_EXE_SHA256
from .reviewed_letter_source_rebind_v1 import _checked_source, _identity, _opaque, _positive, _scope


POLICY = "c19-two-exact-source-knowledge-shapes-12004-v1"
REVIEWS = {
    "coming_of_age.0004": {
        "source_relative": "events/education_and_childhood/coming_of_age_events.txt",
        "source_sha256": "fb2c0e3d52b9f625ebd128195c3bf622d656c49ef1aba91fb13c93569998a4ba",
        "definition_sha256": "e35e1c26f89b5b0adeba4c9ad0ddd3f12bb6f2ba836fb6c359bd1ad2de248215",
        "option_catalogue_sha256": "c2726c0e89e3ea49a9e6a8ca84eb63fd793b0d61133fbe30136aed632553890c",
        "declared_types": (), "gui": "gui/event_windows/character_event.gui",
    },
    "pam_decision_events.0018": {
        "source_relative": "events/dlc/pam/pam_decision_events.txt",
        "source_sha256": "8282ca575f87e165771eb51608a296911eaa27ab93228ee48649917665484b78",
        "definition_sha256": "7ecc2a0f34290ff8377d5ebbd76ae29c908e1e19be9c85e05a9b7d6da6c22878",
        "option_catalogue_sha256": "cfb4f2399de9aa3d91f15ad15d58a518f23fa01c31d1c4b9de529d86d596e4d9",
        "declared_types": ("letter_event",), "gui": "gui/event_windows/letter_event.gui",
    },
}
GUI_SOURCES = {
    "gui/event_windows/character_event.gui": "b0c3efdd81d08e4682c6bdfa9c4fff76351083359b642e9420b8b9d389c6f2e9",
    "gui/event_windows/letter_event.gui": "eb141a50868cd0f32cb9327630a895024edaa9e7580ab4520be88032bfc4ee8c",
    "gui/shared/event_windows.gui": "6756fed934b15e20f2e9460a891c5b40f0012e6f8f51ac6ae45a018fd9a82639",
}


def c19_finite_source_rebind_shape_v1(capture, facts, current):
    """Reuse exact source with fresh observed roles, without changing defaults."""
    from .event_offline_analysis import _fingerprint, _scalars

    key = current.get("event_definition_key")
    if key not in REVIEWS:
        raise ValueError("event has no finite C19 source review")
    review, source = REVIEWS[key], facts.get("binding", {})
    if (current.get("ck3_build") != "1.20.0.4"
            or current.get("required_ck3_exe_sha256") != SUPPORTED_CK3_EXE_SHA256["1.20.0.4"]
            or current.get("native_backend_id") != "ck3-1.20.0.4-native-event-window-v1"
            or current.get("native_option_count") != 1
            or any(source.get(k) != current.get(k) for k in (
                "event_definition_key", "ck3_build", "required_ck3_exe_sha256",
                "native_backend_id", "native_option_count"))
            or source.get("source_sha256") != review["source_sha256"]
            or source.get("option_catalogue_sha256") != review["option_catalogue_sha256"]
            or facts.get("source_relative") != review["source_relative"]
            or not isinstance(facts.get("definition"), str)
            or hashlib.sha256(facts["definition"].encode()).hexdigest() != review["definition_sha256"]
            or tuple(_scalars(facts["definition"], "type")) != review["declared_types"]
            or _fingerprint(facts.get("options")) != review["option_catalogue_sha256"]):
        raise ValueError("finite C19 source/build/definition/options differ")
    context, frame = capture.get("window_context", {}), capture.get("binding", {})
    if not isinstance(context, dict) or not isinstance(frame, dict):
        raise ValueError("finite C19 native frame unavailable")
    provenance, readiness = context.get("provenance", {}), context.get("readiness", {})
    if not isinstance(provenance, dict) or not isinstance(readiness, dict):
        raise ValueError("finite C19 native provenance/readiness unavailable")
    instance, actor = context.get("current_event_instance_id"), frame.get("actor_character_id")
    if (context.get("schema") != "current-event-window-context-v1"
            or type(context.get("schema_version")) is not int or context.get("schema_version") != 1
            or context.get("status") != "available" or type(context.get("window_match_count")) is not int
            or context.get("window_match_count") != 1
            or context.get("event_definition_key") != key or capture.get("event_definition_key") != key
            or not _positive(context.get("calculated_event_id"))
            or context.get("calculated_event_id") != current.get("calculated_event_id")
            or not _positive(current.get("calculated_event_id")) or not _positive(instance)
            or not _positive(capture.get("current_event_instance_id"))
            or capture.get("current_event_instance_id") != instance or not _positive(actor)
            or frame.get("paused") is not True or frame.get("map_ready") is not True
            or any(not _positive(frame.get(k)) for k in ("revision", "native_revision", "bridge_pid", "connection_generation"))
            or frame.get("snapshot_id") != "native:" + str(frame["native_revision"])
            or not _positive(context.get("snapshot_revision")) or context.get("snapshot_revision") != frame["native_revision"]
            or type(frame.get("date_raw")) is not int or type(context.get("date_raw")) is not int
            or context.get("date_raw") != frame["date_raw"]
            or not isinstance(frame.get("episode_run_id"), str) or not frame["episode_run_id"]
            or any(readiness.get(k) is not True for k in ("event_definition_identity_ready", "root_scope_ready",
                                                        "saved_scopes_ready", "option_presentation_ready"))
            or provenance.get("backend_id") != current["native_backend_id"]
            or provenance.get("root") != "module+0x5C6A520->+0x10"
            or provenance.get("idler_vtable_rva") != "0x44BC418" or provenance.get("manager_offset") != "+0x28"):
        raise ValueError("finite C19 fresh native frame/provider differs")
    if _identity({"scope": context.get("root_scope")}, "character", 4, "character_id") != actor:
        raise ValueError("finite C19 native root differs from current actor")
    native, selection = context.get("options"), capture.get("selection", {})
    if (type(capture.get("snapshot_option_count")) is not int or capture["snapshot_option_count"] != 1
            or not isinstance(selection, dict) or not isinstance(native, list) or len(native) != 1 or not isinstance(native[0], dict)
            or type(native[0].get("native_option_index")) is not int or native[0]["native_option_index"] != 0
            or type(native[0].get("rendered_index")) is not int or native[0]["rendered_index"] != 0
            or native[0].get("shown") is not True or type(native[0].get("enabled")) is not bool
            or type(selection.get("native_option_index")) is not int or selection["native_option_index"] != 0
            or type(selection.get("rendered_index")) is not int or selection["rendered_index"] != 0
            or type(selection.get("option_number")) is not int or selection["option_number"] != 1
            or selection.get("enabled") is not native[0]["enabled"]):
        raise ValueError("finite C19 actual first option shape differs")
    relative, path = PurePosixPath(review["source_relative"]), Path(facts["source_path"]).resolve()
    if len(path.parents) < len(relative.parts):
        raise ValueError("finite C19 source has no game root")
    game_root = path.parents[len(relative.parts) - 1]
    if path != (game_root / relative).resolve():
        raise ValueError("finite C19 source location differs")
    _checked_source(path, review["source_sha256"])
    gui = {k: GUI_SOURCES[k] for k in (review["gui"], "gui/shared/event_windows.gui")}
    for name, sha in gui.items():
        _checked_source(game_root / name, sha)
    saved = context.get("saved_scopes")
    if (not isinstance(saved, list) or any(not isinstance(row, dict) or not isinstance(row.get("name"), str)
            or not _positive(row.get("name_identifier")) for row in saved)):
        raise ValueError("finite C19 native role names unavailable")
    roles = {row["name"]: row for row in saved}
    if len(roles) != len(saved):
        raise ValueError("finite C19 roles duplicated")
    gaps = []
    if key == "coming_of_age.0004":
        if set(roles) != {"friend", "victim", "educated_child", "relative", "new_memory", "education_memory"}:
            raise ValueError("finite coming-of-age actual role shape differs")
        ids = {name + "_character_id": _identity(roles[name], "character", 4, "character_id")
               for name in ("friend", "victim", "educated_child", "relative")}
        if ids["educated_child_character_id"] != actor or ids["relative_character_id"] != actor:
            raise ValueError("finite coming-of-age child/relative differ from current root")
        for name in ("new_memory", "education_memory"):
            _opaque(roles[name], "character_memory", 34)
            gaps.append({"role": name, "type_key": "character_memory", "typed_identity_verified": False})
    else:
        if set(roles) != {"puppeteer", "hof_scope"}:
            raise ValueError("finite PAM letter actual role shape differs")
        ids = {"hof_scope_character_id": _identity(roles["hof_scope"], "character", 4, "character_id")}
        null = _scope(roles["puppeteer"], "character", 4).get("typed_identity")
        if not isinstance(null, dict) or null.get("status") != "unavailable" or null.get("reason") != "character_scope_is_null":
            raise ValueError("finite PAM puppeteer differs from observed null character")
        gaps.append({"role": "puppeteer", "type_key": "character", "typed_identity_verified": False,
                     "identity_status": "null"})
    return {"source_rebind_policy": POLICY, "actor_character_id": actor,
            "source_declared_type": review["declared_types"][0] if review["declared_types"] else None,
            "source_type_inferred_from_scalar": False, "current_role_identities": ids, "scope_identity_gaps": gaps,
            "knowledge_scope": "exact_source_and_current_native_character_scope_shapes_only",
            "gui_source_sha256": gui, "loaded_gui_bytes_verified": False,
            "execution_contract_qualified": False, "semantic_decision_ready": False}
