"""Recognize a current education focus without claiming age or LIFE legality."""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.version_identity import CK3_12004


LIFESTYLE_BINDING_ERRORS = frozenset({
    "native_lifestyle_current_state_current_lifestyle_getter_failed",
    "native_lifestyle_current_state_current_lifestyle_key_read_failed",
})
EDUCATION_FOCUS_KEYS = frozenset({
    "education_diplomacy", "education_martial", "education_stewardship",
    "education_intrigue", "education_learning",
})
SOURCE_REVIEW = {
    "definition_path": "common/focuses/00_education_focuses.txt",
    "definition_sha256": "f24d82c5d6d349bcd60f481ef10ccf711550f2738d2efa4f3b7829047e70ec5d",
    "definition_type": "education",
    "reader": "ck3_12004_child_current_focus_readonly.hpp",
    "reader_sha256": "22d6c72bbf2823ae7932d51d764f3a1585cd74bf035a1bbd6e811de9656657e6",
}


def education_focus_frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        **{key: snapshot.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
            "paused", "map_ready",
        )},
        "player_character_id": played.get("character_id") if isinstance(played, Mapping) else None,
        "actor_alive": played.get("alive") if isinstance(played, Mapping) else None,
    }


def qualify_current_education_focus(
    query: object, frame: object, *, expected_revision: object,
) -> dict[str, object] | None:
    """The independently available focus fact does not need target legality.

    A missing requested education definition does not erase the already read
    current focus. It also never supplies permission to change that focus.
    """
    if not isinstance(query, Mapping) or not isinstance(frame, Mapping):
        return None
    actor, native = frame.get("player_character_id"), frame.get("native_revision")
    episode, date = frame.get("episode_run_id"), frame.get("date_raw")
    if (type(actor) is not int or actor <= 0 or type(native) is not int or native <= 0
            or type(expected_revision) is not int or expected_revision <= 0
            or frame.get("revision") != expected_revision
            or frame.get("snapshot_id") != f"native:{native}"
            or not isinstance(episode, str) or not episode.startswith(f"native-{actor}-")
            or type(date) is not int or date < 0
            or frame.get("paused") is not True or frame.get("map_ready") is not True
            or frame.get("actor_alive") is not True):
        return None
    context, source, focus = query.get("source_context"), query.get("source_frame"), query.get("current_focus")
    expected_source = {
        "snapshot_id": frame["snapshot_id"], "episode_run_id": episode,
        "native_revision": native, "date_raw": date,
        "controller_full_id": actor, "paused": True,
    }
    if (query.get("schema") != "child-education-focus-private-12004-v1"
            or query.get("kind") != "query" or query.get("status") not in {"available", "unavailable"}
            or type(query.get("child_full_id")) is not int
            or query.get("child_full_id") != actor or query.get("target_key") != "education_stewardship"
            or query.get("source_public_revision") != expected_revision
            or source != expected_source or not isinstance(context, Mapping)
            or context != {**expected_source, "public_revision": expected_revision,
                           "exact_ck3_build": CK3_12004.game_version,
                           "exe_sha256": CK3_12004.executable_sha256}
            or not isinstance(query.get("request_id"), str) or not query["request_id"]
            or not isinstance(focus, Mapping) or focus.get("available") is not True
            or focus.get("unavailable_reason") is not None
            or focus.get("presence") != "present" or not isinstance(focus.get("key"), str)
            or focus["key"] not in EDUCATION_FOCUS_KEYS):
        return None
    return {
        "status": "adult_lifestyle_not_applicable_current_education_focus",
        "current_focus_key": focus["key"], "source_frame": dict(frame),
        "source_review": dict(SOURCE_REVIEW),
        "age_observed": False, "lifestyle_action_legal": None,
    }
