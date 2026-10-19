"""Two reviewed .4 letters: reuse source knowledge, never an execution contract.

Current native role IDs are retained; opaque activity/faith/tenet payloads stay
unknown. Source and GUI file hashes prove installed source, not loaded GUI bytes.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path, PurePosixPath

from .builds import SUPPORTED_CK3_EXE_SHA256


KEYS = frozenset({"faction_demand.0101", "ecumenical_council_events.0082"})
POLICY = "two-reviewed-letter-source-shapes-12004-v1"
GUI_SOURCES = {
    "gui/event_windows/letter_event.gui":
        "eb141a50868cd0f32cb9327630a895024edaa9e7580ab4520be88032bfc4ee8c",
    "gui/shared/event_windows.gui":
        "6756fed934b15e20f2e9460a891c5b40f0012e6f8f51ac6ae45a018fd9a82639",
}
REVIEWS = {
    "faction_demand.0101": {
        "source_relative": "events/factions/faction_demands.txt", "count": 3,
        "source_sha256": "eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd",
        "definition_sha256": "940aad8858ceca76b47fee049055d68a8f98a23f4044761b59561942cb8b75f7",
        "option_catalogue_sha256": "fe3f9e729592133fed0faaa4b4b57b0051183a1450bcdb85d37627700f017ea6",
    },
    "ecumenical_council_events.0082": {
        "source_relative": "events/activities/ecumenical_council_activity/pam_ecumenical_council_events.txt",
        "count": 1,
        "source_sha256": "194d12e1fe54b015d6f89ef15c4d435e80ea6b3bf4c453623d2240de29c4a559",
        "definition_sha256": "27b9f85792a014009245ae2733a361f0154536590bdb3f45b67cdced3a662df9",
        "option_catalogue_sha256": "80ad6cd429d44d7a785575f7417d3a8bb06c4a51b574ebc8f8cbb0acf9fe771a",
    },
}


def _positive(value):
    return type(value) is int and value > 0


@lru_cache(maxsize=16)
def _file_sha(path, stamp):
    del stamp  # Cache key includes both size and mtime, like the source loader.
    if Path(path).stat().st_size > 2 * 1024 * 1024:
        raise ValueError("reviewed letter source/GUI exceeds bound")
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _checked_source(path, expected):
    info = path.stat()
    if _file_sha(str(path), (info.st_size, info.st_mtime_ns)) != expected:
        raise ValueError("reviewed letter source/GUI SHA differs")


def _scope(row, kind, raw):
    value = row.get("scope") if isinstance(row, dict) else None
    if (not isinstance(value, dict) or value.get("status") != "available"
            or value.get("type_key") != kind
            or type(value.get("raw_type_index")) is not int
            or value["raw_type_index"] != raw
            or type(value.get("subtype")) is not int or value["subtype"] != 0):
        raise ValueError("reviewed letter role type shape differs")
    return value


def _identity(row, kind, raw, field):
    value = _scope(row, kind, raw).get("typed_identity")
    if (not isinstance(value, dict) or value.get("status") != "available"
            or value.get("kind") != kind or not _positive(value.get(field))):
        raise ValueError("reviewed letter current role identity unavailable")
    return value[field]


def _opaque(row, kind, raw):
    value = _scope(row, kind, raw).get("typed_identity")
    if (not isinstance(value, dict) or value.get("status") != "unavailable"
            or value.get("reason") != "generic_scope_payload_identity_not_closed"):
        raise ValueError("reviewed letter opaque role representation differs")


def reviewed_letter_source_rebind_shape_v1(capture, facts, current):
    """Validate exact source plus the fresh observed role *shape* of two keys.

    This is deliberately independent of old timeline contracts and old role IDs.
    A council letter has no mutating option: unknown non-character payload IDs
    remain explicit and are never used to evaluate doctrine, faith or benefit.
    """
    from .event_offline_analysis import _fingerprint, _source_rebind_root_shape

    key = current.get("event_definition_key")
    if key not in KEYS:
        raise ValueError("letter key has no finite source-rebind review")
    review = REVIEWS[key]
    source = facts.get("binding", {})
    if (current.get("ck3_build") != "1.20.0.4"
            or current.get("required_ck3_exe_sha256") != SUPPORTED_CK3_EXE_SHA256["1.20.0.4"]
            or current.get("native_backend_id") != "ck3-1.20.0.4-native-event-window-v1"
            or current.get("native_option_count") != review["count"]
            or any(source.get(k) != current.get(k) for k in (
                "event_definition_key", "ck3_build", "required_ck3_exe_sha256",
                "native_backend_id", "native_option_count"))
            or source.get("source_sha256") != review["source_sha256"]
            or source.get("option_catalogue_sha256") != review["option_catalogue_sha256"]
            or facts.get("source_relative") != review["source_relative"]
            or not isinstance(facts.get("definition"), str)
            or hashlib.sha256(facts["definition"].encode()).hexdigest() != review["definition_sha256"]
            or _fingerprint(facts.get("options")) != review["option_catalogue_sha256"]):
        raise ValueError("reviewed letter build/definition/source/catalogue differs")
    shape = _source_rebind_root_shape(capture, facts, current, source_event_type="letter_event")
    context, frame = capture["window_context"], capture["binding"]
    provenance = context.get("provenance", {})
    if (context.get("schema_version") != 1 or context.get("window_match_count") != 1
            or frame.get("paused") is not True or frame.get("map_ready") is not True
            or not _positive(frame.get("revision")) or not _positive(frame.get("native_revision"))
            or frame.get("snapshot_id") != "native:" + str(frame["native_revision"])
            or not isinstance(frame.get("episode_run_id"), str) or not frame["episode_run_id"]
            or not _positive(frame.get("bridge_pid")) or not _positive(frame.get("connection_generation"))
            or provenance.get("root") != "module+0x5C6A520->+0x10"
            or provenance.get("idler_vtable_rva") != "0x44BC418"
            or provenance.get("manager_offset") != "+0x28"):
        raise ValueError("reviewed letter current native frame/provider differs")
    relative = PurePosixPath(review["source_relative"])
    source_path = Path(facts["source_path"]).resolve()
    if len(source_path.parents) < len(relative.parts):
        raise ValueError("reviewed letter source path has no expected game root")
    game_root = source_path.parents[len(relative.parts) - 1]
    if source_path != (game_root / relative).resolve():
        raise ValueError("reviewed letter source location differs")
    _checked_source(source_path, review["source_sha256"])
    for gui_relative, expected in GUI_SOURCES.items():
        _checked_source(game_root / gui_relative, expected)
    native = context["options"]
    ordered = sorted(native, key=lambda row: row["rendered_index"])
    shown_indexes = [row["native_option_index"] for row in ordered]
    if (any(row.get("shown") is not True or type(row.get("enabled")) is not bool for row in ordered)
            or [row["rendered_index"] for row in ordered] != list(range(len(ordered)))
            or shown_indexes not in ([[0, 2], [0, 1, 2]] if key == "faction_demand.0101" else [[0]])):
        raise ValueError("reviewed letter actual displayed option shape differs")
    saved = context.get("saved_scopes")
    if (not isinstance(saved, list) or any(not isinstance(row, dict)
            or not isinstance(row.get("name"), str) or not _positive(row.get("name_identifier")) for row in saved)):
        raise ValueError("reviewed letter saved role names unavailable")
    roles = {row["name"]: row for row in saved}
    if len(roles) != len(saved):
        raise ValueError("reviewed letter saved role names duplicated")
    actor = frame["actor_character_id"]
    gaps = []
    if key == "faction_demand.0101":
        if set(roles) != {"faction", "faction_leader", "faction_target"}:
            raise ValueError("reviewed liberty saved roles differ")
        ids = {
            "faction_id": _identity(roles["faction"], "faction", 25, "faction_id"),
            "faction_leader_character_id": _identity(roles["faction_leader"], "character", 4, "character_id"),
            "faction_target_character_id": _identity(roles["faction_target"], "character", 4, "character_id"),
        }
        if ids["faction_target_character_id"] != actor or ids["faction_leader_character_id"] == actor:
            raise ValueError("reviewed liberty current target/leader semantics differ")
    else:
        required = {"activity", "host", "province", "activity_location", "root_scope",
                    "ec_council", "ec_council_faith", "ec_reporter"}
        optional = {"ec_letter_tenet_1", "ec_letter_tenet_2", "ec_letter_doctrine_1"}
        if not required <= set(roles) <= required | optional:
            raise ValueError("reviewed council saved roles differ")
        ids = {name + "_character_id": _identity(roles[name], "character", 4, "character_id")
               for name in ("host", "root_scope", "ec_reporter")}
        if ids["host_character_id"] != ids["root_scope_character_id"]:
            raise ValueError("reviewed council current host/root role shape differs")
        opaque = {"activity": ("activity", 6), "province": ("province", 8),
                  "activity_location": ("province", 8), "ec_council": ("activity", 6),
                  "ec_council_faith": ("faith", 13), "ec_letter_tenet_1": ("tenet", 40),
                  "ec_letter_tenet_2": ("tenet", 40), "ec_letter_doctrine_1": ("doctrine", 39)}
        for name, (kind, raw) in opaque.items():
            if name in roles:
                _opaque(roles[name], kind, raw)
                gaps.append({"role": name, "type_key": kind, "typed_identity_verified": False})
    return {**shape, "source_rebind_policy": POLICY, "reviewed_letter_key": key,
            "knowledge_scope": "exact_definition_source_and_current_native_role_type_shape_only",
            "current_role_identities": ids, "scope_identity_gaps": gaps,
            "gui_source_sha256": dict(GUI_SOURCES), "loaded_gui_bytes_verified": False,
            "execution_contract_qualified": False, "semantic_decision_ready": False}
