"""Validate and project the same-query request guardian's signed raw skills.

The native query supplies the complete role and frame binding. These observed
request-role values remain separate from the effect's selected educator scope.
"""
from __future__ import annotations

from copy import deepcopy


PROFILE_KEY = "request_guardian_skill_inputs_v1"
_SKILLS = {"diplomacy", "martial", "stewardship", "intrigue", "learning"}
_PROFILE_KEYS = {
    "schema", "role_source", "child_character_id", "character_id",
    "owning_native_revision", "binding_status", "unavailable_reason", "skills",
}
_VALUE_KEYS = {"available", "value", "unavailable_reason"}


def _reason(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 512


def validate_request_guardian_skill_inputs_v1(
    profile: object, normalized_context: dict[str, object],
) -> None:
    """Validate an optional .4 education leaf without changing native readiness."""
    context = normalized_context
    if (context["exact_build"] != "1.20.0.4"
            or context["interaction_key"] != "educate_child_interaction"
            or context["status"] != "available"):
        raise ValueError("request guardian skill profile requires an available .4 education context")
    if not isinstance(profile, dict) or set(profile) != _PROFILE_KEYS:
        raise ValueError("request guardian skill profile is not closed")
    if (profile["schema"] != PROFILE_KEY
            or profile["role_source"] != "request_guardian_secondary_actor"):
        raise ValueError("request guardian skill source is mismatched")
    revision = profile["owning_native_revision"]
    if (type(revision) is not int or not 0 <= revision <= 2**64 - 1
            or revision != context["snapshot_revision"]):
        raise ValueError("request guardian skill profile native revision is mismatched")
    roles = context["effective_roles"]
    for key, role in (("child_character_id", "secondary_recipient_id"),
                      ("character_id", "secondary_actor_id")):
        full_id = profile[key]
        if full_id is not None and (type(full_id) is not int or not 0 <= full_id <= 2**32 - 2):
            raise ValueError("request guardian skill full ID is malformed")
        if type(full_id) is not type(roles[role]) or full_id != roles[role]:
            raise ValueError("request guardian skill profile final role is mismatched")
    binding = profile["binding_status"]
    if binding not in {"resolved", "known_null", "unavailable"}:
        raise ValueError("request guardian skill binding status is malformed")
    if binding == "resolved":
        if (any(profile[key] is None or profile[key] == 0
                for key in ("child_character_id", "character_id"))
                or profile["unavailable_reason"] is not None):
            raise ValueError("resolved request guardian skills lack complete role IDs")
    elif binding == "known_null":
        if (profile["character_id"] is not None
                or profile["unavailable_reason"] != "request_guardian_role_known_null"):
            raise ValueError("known-null request guardian skill binding is inconsistent")
    elif not _reason(profile["unavailable_reason"]):
        raise ValueError("unavailable request guardian skills require a reason")
    skills = profile["skills"]
    if not isinstance(skills, dict) or set(skills) != _SKILLS:
        raise ValueError("request guardian skill inventory is not closed")
    for key, field in skills.items():
        if (not isinstance(field, dict) or set(field) != _VALUE_KEYS
                or type(field["available"]) is not bool):
            raise ValueError("request guardian skill value is malformed")
        if field["available"]:
            if (binding != "resolved" or type(field["value"]) is not int
                    or not -(2**31) <= field["value"] <= 2**31 - 1
                    or field["unavailable_reason"] is not None):
                raise ValueError("available request guardian skill lacks a signed raw value")
        elif field["value"] is not None or not _reason(field["unavailable_reason"]):
            raise ValueError("unavailable request guardian skill is inconsistent")
    if skills["martial"] != {
            "available": False, "value": None,
            "unavailable_reason": "actual4_martial_name_enum_unqualified"}:
        raise ValueError("request guardian martial name and enum remain unqualified")


def project_request_guardian_focus_skills_v1(
    needs_row: dict[str, object], normalized_context: dict[str, object],
) -> dict[str, object]:
    """Keep actual-focus and learning operands independently useful to the caller."""
    profile = normalized_context.get(PROFILE_KEY)
    focus = needs_row["focus_management"]
    focus_key = focus["current_key"]
    family_frame = needs_row["frame"]
    join_reason = None
    if not isinstance(profile, dict):
        join_reason = "request_guardian_skill_profile_not_observed"
    elif (type(profile["child_character_id"]) is not type(needs_row["raw_character_id"])
          or profile["child_character_id"] != needs_row["raw_character_id"]):
        join_reason = "request_guardian_skill_child_mismatch"
    elif not isinstance(family_frame, dict):
        join_reason = "family_education_focus_frame_not_observed"
    elif any(type(family_frame.get(source)) is not type(normalized_context[target])
             or family_frame.get(source) != normalized_context[target]
             for source, target in (("native_revision", "snapshot_revision"),
                                    ("date_raw", "date_raw"),
                                    ("played_character_id", "player_character_id"))):
        join_reason = "family_education_focus_frame_mismatch"
    missing = {"available": False, "value": None, "unavailable_reason": join_reason}
    skills = profile["skills"] if join_reason is None else None
    learning = deepcopy(profile["skills"]["learning"] if isinstance(profile, dict) else {
        "available": False, "value": None,
        "unavailable_reason": "request_guardian_skill_profile_not_observed"})
    if join_reason is not None:
        focused = deepcopy(missing)
    elif focus["state"] == "education_focus_present":
        skill_key = focus_key.removeprefix("education_")
        focused = deepcopy(skills[skill_key] if skills is not None else missing)
    else:
        focused = {"available": False, "value": None, "unavailable_reason": {
            "known_absent": "education_focus_known_absent",
            "other_focus_present": "current_focus_is_not_education",
            "unknown": "education_focus_not_observed",
        }[focus["state"]]}
    return {
        "schema": "request_guardian_focus_skill_inputs_v1",
        "child_character_id": profile["child_character_id"] if isinstance(profile, dict) else None,
        "focus_child_character_id": needs_row["raw_character_id"],
        "character_id": profile["character_id"] if isinstance(profile, dict) else None,
        "owning_native_revision": profile["owning_native_revision"] if isinstance(profile, dict) else None,
        "role_source": "request_guardian_secondary_actor",
        "binding_status": profile["binding_status"] if isinstance(profile, dict) else "unavailable",
        "focus_management": deepcopy(focus), "focus_key": focus_key,
        "family_focus_frame": deepcopy(family_frame),
        "focus_projection_join_available": join_reason is None,
        "focus_projection_unavailable_reason": join_reason,
        "focus_skill": focused, "learning_skill": learning,
        "raw_profile": deepcopy(profile),
        "effect_educator_selection_observed": False,
    }
