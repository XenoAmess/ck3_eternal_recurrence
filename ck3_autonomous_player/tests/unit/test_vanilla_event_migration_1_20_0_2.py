"""Replay the production consumer against reviewed current source semantics.

These are deterministic projection fixtures, not additional live observations.
The legacy scope/option samples remain explicitly 1.19 evidence.
"""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT))

from xar_autoplayer.vanilla_events import (
    CURRENT_CK3_BUILD, CURRENT_CK3_EXE_SHA256,
    ck3_list_vanilla_event_knowledge_v1, query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.source_index import (
    load_vanilla_event_source_index, query_vanilla_event_source_provenance_v1,
)


def scope(type_key, character_id=None):
    return {
        "status": "available", "type_key": type_key,
        "typed_identity": {
            "status": "available" if character_id is not None else "unavailable",
            "kind": "character" if character_id is not None else "opaque",
            "character_id": character_id,
        },
    }


def context(key, scopes, native_indices):
    return {
        "schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "window_match_count": 1,
        "event_definition_key": key, "current_event_instance_id": 23,
        "snapshot_revision": 11, "date_raw": 53367864,
        "root_scope": scope("character", 36403), "saved_scopes": scopes,
        "options": [{
            "rendered_index": rendered, "native_option_index": native,
            "shown": True, "enabled": True, "fallback": False, "cancel": False,
        } for rendered, native in enumerate(native_indices)],
        "provenance": {"backend_id": "ck3-1.20.0.2-native-event-window-v1"},
    }


def test_0110_bounded_choice_uses_new_source_and_both_legacy_scope_shapes():
    for preferred in (False, True):
        scopes = [{"name": "epidemic", "scope": scope("epidemic")}]
        if preferred:
            scopes.append({"name": "new_preferred_capital", "scope": scope("landed_title")})
        frame = context("epidemic_events.0110", scopes, [1, 2])
        result = recommend_registered_vanilla_event_option_v1(
            frame, played_character_id=36403, snapshot_option_count=3,
        )
        assert result["status"] == "recommended"
        assert result["selected_native_option_index"] == 2
        assert result["ck3_build"] == CURRENT_CK3_BUILD
        assert result["ck3_exe_sha256"] == CURRENT_CK3_EXE_SHA256
        assert result["semantic_optimal"] is False
        # The source permits a third rendered option; this work retains the
        # existing reviewed continuation contract instead of inventing a rank.
        frame["options"].insert(0, {
            "rendered_index": 0, "native_option_index": 0,
            "shown": True, "enabled": True, "fallback": False, "cancel": False,
        })
        for index, option in enumerate(frame["options"]):
            option["rendered_index"] = index
        drift = recommend_registered_vanilla_event_option_v1(
            frame, played_character_id=36403, snapshot_option_count=3,
        )
        assert drift["status"] == "blocked"
        assert drift["selected_native_option_index"] is None


def test_current_prison_notice_consumes_authored_roles_and_no_material_claim():
    frame = context("prison_notification.0001", [
        {"name": name, "scope": scope("character", actor)} for name, actor in (
            ("prisoner", 36403), ("this_player", 36403),
            ("imprisoner", 32309), ("bg_override_char", 32309),
        )
    ] + [{"name": "new_memory", "scope": scope("character_memory")}], [0])
    result = recommend_registered_vanilla_event_option_v1(
        frame, played_character_id=36403, snapshot_option_count=1,
    )
    assert result["status"] == "recommended"
    assert result["selected_native_option_index"] == 0
    assert result["choice_effect_profile"] is None
    assert result["ck3_build"] == CURRENT_CK3_BUILD
    wrong_player = deepcopy(frame)
    wrong_player["saved_scopes"][0]["scope"] = scope("character", 38822)
    assert recommend_registered_vanilla_event_option_v1(
        wrong_player, played_character_id=36403, snapshot_option_count=1,
    )["status"] == "blocked"


def test_current_catalog_retains_legacy_live_as_legacy_not_current():
    knowledge = query_vanilla_event_knowledge_v1("epidemic_events.0110", CURRENT_CK3_BUILD)
    assert knowledge["status"] == "available"
    migration = knowledge["analysis"]["migration_1_20_0_2"]
    assert migration["readiness"] == "static-ready"
    assert migration["new_live_evidence"] is False
    assert knowledge["observations"]["legacy_build"] == "1.19.0.6"
    assert "exemplars" not in knowledge["observations"]
    assert query_vanilla_event_knowledge_v1("epidemic_events.0110", "1.19.0.6")[
        "analysis"
    ]["exact_build"]["game_version"] == "1.19.0.6"
    listed = ck3_list_vanilla_event_knowledge_v1(CURRENT_CK3_BUILD)
    assert listed["status"] == "available"
    assert listed["dataset_summary"]["events_with_observations"] == 0
    assert listed["dataset_summary"]["portable_events"] == 0
    assert query_vanilla_event_knowledge_v1("fervor.1002", CURRENT_CK3_BUILD)[
        "unavailable_reason"
    ] == "event_domain_owner_deferred"


def test_current_source_index_tracks_actual_build_and_caller_candidates():
    index = load_vanilla_event_source_index(build=CURRENT_CK3_BUILD)
    assert index["audit"]["registered_event_count"] == 192
    assert index["audit"]["missing_definition_count"] == 0
    source = query_vanilla_event_source_provenance_v1("epidemic_events.0110", CURRENT_CK3_BUILD)
    assert source["status"] == "available"
    assert source["ck3_exe_sha256"] == CURRENT_CK3_EXE_SHA256
    assert source["caller_candidates_are_lexical_only"] is True
    assert source["definition"]["file_sha256"] != query_vanilla_event_source_provenance_v1(
        "epidemic_events.0110", "1.19.0.6"
    )["definition"]["file_sha256"]
    for record in [source["definition"], *source["caller_candidates"]]:
        assert not Path(record["relative_path"]).is_absolute()


def test_birth_single_and_twin_select_native_zero_not_new_rejection_option():
    base = [
        {"name": name, "scope": scope("character", actor)} for name, actor in (
            ("child", 42000), ("father", 36403), ("real_father", 36403), ("mother", 41000),
        )
    ] + [{"name": name, "scope": scope("boolean")} for name in (
        "is_bastard", "is_child_of_concubine", "matrilineal",
    )]
    # Current native 0 has dynamic single/twin text; native 1 is the new
    # suppressed-bastardy alternative. Neither projection submits a command.
    for twin in (False, True):
        for shown in ([0], [0, 1]):
            scopes = deepcopy(base)
            if twin:
                scopes.append({"name": "child_2", "scope": scope("character", 42001)})
            result = recommend_registered_vanilla_event_option_v1(
                context("birth.1003", scopes, shown),
                played_character_id=36403, snapshot_option_count=2,
            )
            assert result["status"] == "recommended"
            assert result["selected_native_option_index"] == 0
            assert result["choice_effect_profile"] is None
            assert result["semantic_optimal"] is False


def test_char_sender_role_is_added_and_distinct_puppet_is_not_guessed():
    scopes = [{"name": name, "scope": scope("character", actor)} for name, actor in (
        ("actor", 41000), ("recipient", 42000),
        ("secondary_actor", 43000), ("secondary_recipient", 44000),
        ("intermediary", 45000), ("imprisoner", 41000),
        ("imprisonment_target", 42000), ("puppet_or_actor", 41000),
    )] + [{"name": name, "scope": scope("boolean")} for name in (
        "hook", "war_for_imprisonment_flavour",
    )]
    frame = context("char_interaction.0232", scopes, [0, 1])
    result = recommend_registered_vanilla_event_option_v1(
        frame, played_character_id=36403, snapshot_option_count=2,
    )
    assert result["status"] == "recommended"
    assert result["selected_native_option_index"] == 1
    different_puppet = deepcopy(frame)
    different_puppet["saved_scopes"][7]["scope"] = scope("character", 46000)
    rejected = recommend_registered_vanilla_event_option_v1(
        different_puppet, played_character_id=36403, snapshot_option_count=2,
    )
    assert rejected["status"] == "blocked"
    assert rejected["selected_native_option_index"] is None


def test_current_char_ack_retains_nullable_secondary_roles():
    for key, hook, snapshot_count in (
        ("char_interaction.0240", True, 1),
        ("char_interaction.0251", False, 1),
        ("char_interaction.0370", False, 2),
    ):
        scopes = [
            {"name": "actor", "scope": scope("character", 41000)},
            {"name": "recipient", "scope": scope("character", 36403)},
            {"name": "puppet_or_actor", "scope": scope("character", 41000)},
        ] + [{"name": name, "scope": {
            "status": "unavailable", "type_key": None,
            "typed_identity": {"status": "unavailable"},
        }} for name in ("secondary_actor", "secondary_recipient", "intermediary")]
        if hook:
            scopes.append({"name": "hook", "scope": scope("boolean")})
        result = recommend_registered_vanilla_event_option_v1(
            context(key, scopes, [0]), played_character_id=36403,
            snapshot_option_count=snapshot_count,
        )
        assert result["status"] == "recommended"
        assert result["selected_native_option_index"] == 0
        assert result["choice_effect_profile"] is None


def test_culture_notification_optional_traditions_keep_non_founder_ack():
    base = [
        {"name": "founder", "scope": scope("character", 41000)},
        {"name": "parent_culture_1", "scope": scope("culture")},
        {"name": "new_culture", "scope": scope("culture")},
        {"name": "parent_1", "scope": scope("culture")},
        {"name": "ethos", "scope": scope("flag")},
    ]
    for additions in ((), ("new_tradition",), ("lost_tradition",),
                      ("new_tradition", "lost_tradition")):
        # Type index 45/name culture_tradition is exact-build static evidence.
        # Its identity remains opaque, as in the current production decoder.
        scopes = deepcopy(base)
        for name in additions:
            opaque = scope("culture_tradition")
            opaque["raw_type_index"] = 45
            scopes.append({"name": name, "scope": opaque})
        result = recommend_registered_vanilla_event_option_v1(
            context("culture_notification.1111", scopes, [1]),
            played_character_id=36403, snapshot_option_count=2,
        )
        assert result["status"] == "recommended"
        assert result["selected_native_option_index"] == 1
        assert result["choice_effect_profile"] is None
        assert result["semantic_optimal"] is False


def test_current_offline_tool_replays_new_contracts_without_material_receipts():
    source = ROOT / "tools" / "replay_vanilla_event_research.py"
    spec = importlib.util.spec_from_file_location("migration_event_replay", source)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    fixtures = json.loads((ROOT / "ck3_autonomous_player/tests/fixtures/vanilla_event_migration_12002_replay.json").read_text(encoding="utf-8"))
    assert fixtures["new_live_evidence"] is False
    data_dir = ROOT / "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data"
    for row in fixtures["cases"]:
        report = replay.replay_bytes(json.dumps(row["bundle"]).encode("utf-8"))
        assert report["policy"]["status"] == "recommended"
        assert report["policy"]["selected_native_option_index"] == row["expected_native_option_index"]
        assert report["material_plan"]["reason"] == row["expected_material_reason"]
        assert report["material_evaluation"]["status"] == "not_evaluated"
        assert report["new_live_evidence"] is False
        assert report["gameplay_commands_submitted"] == 0
        frozen = report["production"]["frozen_data_sha256"]
        for name in ("source_index_1_20_0_2.json", "source_compatibility_1_20_0_2.json"):
            assert frozen[f"data/{name}"] == hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
