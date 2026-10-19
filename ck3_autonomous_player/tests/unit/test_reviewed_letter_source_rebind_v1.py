"""Portable SYNTHETIC sources/frames; no game install, RPC or live qualification."""
import copy
import hashlib
from pathlib import Path

import pytest

from xar_autoplayer.vanilla_events import event_offline_analysis as offline
from xar_autoplayer.vanilla_events import reviewed_letter_source_rebind_v1 as letters


def scope(name, kind, raw, identity=None):
    return {"name": name, "name_identifier": 1, "scope": {
        "status": "available", "raw_type_index": raw, "type_key": kind, "subtype": 0,
        "typed_identity": ({"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}
                           if identity is None else {"status": "available", "kind": kind,
                                                    kind + "_id": identity})}}


@pytest.fixture(params=sorted(letters.KEYS))
def case(request, tmp_path, monkeypatch):
    key = request.param
    count = 3 if key == "faction_demand.0101" else 1
    reviewed = copy.deepcopy(letters.REVIEWS)
    record = reviewed[key]
    source = tmp_path / "game" / record["source_relative"]
    source.parent.mkdir(parents=True)
    definition = key + " = {\n type = letter_event\n" + "".join(
        f" option = {{\n name = synthetic.option{i}\n }}\n" for i in range(count)) + "}\n"
    source.write_bytes(definition.encode())
    options = [{"native_option_index": i, "source_name_keys": [f"synthetic.option{i}"],
                "source_option": body} for i, body in enumerate(offline._blocks(definition, "option"))]
    record.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  definition_sha256=hashlib.sha256(definition.encode()).hexdigest(),
                  option_catalogue_sha256=offline._fingerprint(options))
    monkeypatch.setattr(letters, "REVIEWS", reviewed)
    guis = {}
    for rel in letters.GUI_SOURCES:
        path = tmp_path / "game" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SYNTHETIC installed GUI source")
        guis[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(letters, "GUI_SOURCES", guis)
    frame = {"snapshot_id": "native:9", "native_revision": 9, "revision": 4,
             "date_raw": 1000, "actor_character_id": 101, "paused": True,
             "map_ready": True, "episode_run_id": "SYNTHETIC", "bridge_pid": 7,
             "connection_generation": 2}
    roles = ([scope("faction", "faction", 25, 11), scope("faction_leader", "character", 4, 201),
              scope("faction_target", "character", 4, 101)] if count == 3 else [
        scope("host", "character", 4, 301), scope("root_scope", "character", 4, 301),
        scope("ec_reporter", "character", 4, 401), scope("activity", "activity", 6),
        scope("province", "province", 8), scope("activity_location", "province", 8),
        scope("ec_council", "activity", 6), scope("ec_council_faith", "faith", 13),
        scope("ec_letter_tenet_1", "tenet", 40), scope("ec_letter_tenet_2", "tenet", 40),
        scope("ec_letter_doctrine_1", "doctrine", 39)])
    if key == "sway_ongoing.1003":
        roles = [scope("owner", "character", 4, 101), scope("target", "character", 4, 201),
                 scope("compliment_receiver", "character", 4, 201), scope("friend", "character", 4, 301),
                 scope("scheme", "scheme", 9), scope("artifact", "artifact", 31),
                 scope("evaluated_compliment_type", "flag", 3), scope("compliment_outcome", "flag", 3)]
    shown = [0, 2] if count == 3 else [0]
    context = {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "window_match_count": 1, "event_definition_key": key,
        "calculated_event_id": 20001, "current_event_instance_id": 3,
        "snapshot_revision": 9, "date_raw": 1000,
        "root_scope": scope("root", "character", 4, 101)["scope"], "saved_scopes": roles,
        "readiness": {name: True for name in ["event_definition_identity_ready", "root_scope_ready",
                                              "saved_scopes_ready", "option_presentation_ready"]},
        "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1",
                       "root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC418",
                       "manager_offset": "+0x28"},
        "options": [{"native_option_index": i, "rendered_index": j, "shown": True,
                     "enabled": True} for j, i in enumerate(shown)]}
    capture = {"event_definition_key": key, "current_event_instance_id": 3,
        "snapshot_option_count": count, "binding": frame, "window_context": context,
        "selection": {"native_option_index": 0, "rendered_index": 0, "option_number": 1, "enabled": True}}
    binding = offline._native_binding(capture)
    binding.update(calculated_event_id=10001, source_sha256=record["source_sha256"],
                   option_catalogue_sha256=record["option_catalogue_sha256"])
    fp = offline._fingerprint(binding)
    facts = {"binding": binding, "fingerprint": fp, "source_path": str(source),
             "source_relative": record["source_relative"], "definition": definition, "options": options}
    state = tmp_path / "state"
    fact_pin = offline.write_immutable(state / "evidence/event-source-registry/facts" / (fp + ".json"), facts)
    entry = {"schema": offline.SCHEMA, "fingerprint": fp, "binding": binding,
             "source_path": str(source), "source_facts": fact_pin,
             "classification": "offline-source-reviewed-user-first-rendered-policy"}
    offline.write_immutable(state / "evidence/event-source-registry" / (fp + ".json"), entry)
    return capture, facts, state, source, tmp_path / "game"


def test_cold_ID_reuses_only_source_knowledge_with_current_roles(case):
    capture, facts, state, _, _ = case
    known, audit = offline.load_source_reviewed_event_v1(state, capture)
    assert known is not None and audit["binding_mode"] == "reviewed_letter_source_rebound"
    assert audit["registry_contract_accepted"] is False and audit["material_effects_verified"] is False
    assert audit["execution_contract_qualified"] is False and audit["semantic_decision_ready"] is False
    assert audit["loaded_gui_bytes_verified"] is False
    assert known["binding"]["calculated_event_id"] == 10001
    assert audit["fresh_binding"]["calculated_event_id"] == 20001
    if facts["binding"]["event_definition_key"] == "sway_ongoing.1003":
        assert len(audit["scope_identity_gaps"]) == 4
        assert audit["current_role_identities"] == {"owner_character_id": 101, "target_character_id": 201,
                "compliment_receiver_character_id": 201, "friend_character_id": 301}
        assert audit["source_rebind_policy"] == letters.SWAY_POLICY
    elif facts["binding"]["native_option_count"] == 1:
        assert len(audit["scope_identity_gaps"]) == 8
        assert audit["current_role_identities"]["ec_reporter_character_id"] == 401
    else:
        assert audit["scope_identity_gaps"] == []
        assert audit["current_role_identities"]["faction_target_character_id"] == 101


@pytest.mark.parametrize("change", ["source", "GUI", "root", "duplicate", "role_type", "role_identity", "frame", "provider"])
def test_source_GUI_frame_or_role_drift_remains_unknown(case, change):
    capture, _, state, source, game = case
    if change == "source":
        source.write_bytes(source.read_bytes() + b"\n# changed source")
    elif change == "GUI":
        p = game / "gui/event_windows/letter_event.gui"
        p.write_bytes(p.read_bytes() + b"\nchanged")
    elif change == "root":
        capture["window_context"]["root_scope"]["typed_identity"]["character_id"] = 999
    elif change == "duplicate":
        capture["window_context"]["saved_scopes"].append(copy.deepcopy(capture["window_context"]["saved_scopes"][0]))
    elif change == "role_type":
        capture["window_context"]["saved_scopes"][0]["scope"]["raw_type_index"] = 99
    elif change == "role_identity":
        roles = {v["name"]: v for v in capture["window_context"]["saved_scopes"]}
        target = roles.get("faction_target", roles.get("host", roles.get("owner")))
        target["scope"]["typed_identity"]["character_id"] = 999
    elif change == "frame":
        capture["binding"]["native_revision"] += 1
    else:
        capture["window_context"]["provenance"]["idler_vtable_rva"] = "0x1"
    known, audit = offline.load_source_reviewed_event_v1(state, capture)
    assert known is None and audit["status"] == "unknown"


def test_review_checks_definition_catalogue_and_keeps_other_letters_closed(case):
    capture, facts, _, _, _ = case
    current = offline._native_binding(capture)
    for field in ("definition", "options"):
        changed = copy.deepcopy(facts)
        changed[field] = "different" if field == "definition" else []
        with pytest.raises(ValueError):
            letters.reviewed_letter_source_rebind_shape_v1(capture, changed, current)
    current["event_definition_key"] = "another_letter.0001"
    with pytest.raises(ValueError):
        letters.reviewed_letter_source_rebind_shape_v1(capture, facts, current)


def test_sway_current_roles_are_fresh_and_opaque_payloads_stay_unknown(case):
    capture, _, state, _, _ = case
    if capture["event_definition_key"] != "sway_ongoing.1003":
        pytest.skip("sway-specific role semantics")
    roles = {row["name"]: row for row in capture["window_context"]["saved_scopes"]}
    roles["target"]["scope"]["typed_identity"]["character_id"] = 501
    roles["compliment_receiver"]["scope"]["typed_identity"]["character_id"] = 601
    _, audit = offline.load_source_reviewed_event_v1(state, capture)
    assert audit["current_role_identities"]["target_character_id"] == 501
    assert audit["current_role_identities"]["compliment_receiver_character_id"] == 601
    assert {v["role"] for v in audit["scope_identity_gaps"]} == {
        "scheme", "artifact", "evaluated_compliment_type", "compliment_outcome"}
    assert all(v["typed_identity_verified"] is False for v in audit["scope_identity_gaps"])
    assert audit["execution_contract_qualified"] is False


def test_sway_required_roles_and_native_build_remain_strict(case):
    capture, facts, state, _, _ = case
    if capture["event_definition_key"] != "sway_ongoing.1003":
        pytest.skip("sway-specific negative shapes")
    for change in ("missing_target", "unknown_role", "receiver_untyped", "receiver_self", "scheme_type",
                   "fabricated_scheme", "flag_type", "fabricated_flag", "build", "backend", "exe", "option"):
        changed = copy.deepcopy(capture)
        context = changed["window_context"]
        roles = {row["name"]: row for row in context["saved_scopes"]}
        if change == "missing_target":
            context["saved_scopes"].remove(roles["target"])
        elif change == "unknown_role":
            context["saved_scopes"].append(scope("unknown", "character", 4, 1))
        elif change == "receiver_untyped":
            roles["compliment_receiver"]["scope"]["typed_identity"] = {"status": "unavailable"}
        elif change == "receiver_self":
            roles["compliment_receiver"]["scope"]["typed_identity"]["character_id"] = 101
        elif change in ("scheme_type", "flag_type"):
            roles["scheme" if change == "scheme_type" else "compliment_outcome"]["scope"]["raw_type_index"] = 99
        elif change in ("fabricated_scheme", "fabricated_flag"):
            name = "scheme" if change == "fabricated_scheme" else "compliment_outcome"
            roles[name]["scope"]["typed_identity"] = {"status": "available", "kind": "scheme", "scheme_id": 99}
        elif change == "backend":
            context["provenance"]["backend_id"] = "other"
        elif change == "option":
            context["options"][0]["native_option_index"] = 1
        else:
            current = offline._native_binding(changed)
            current["ck3_build" if change == "build" else "required_ck3_exe_sha256"] = "other"
            with pytest.raises(ValueError):
                letters.reviewed_letter_source_rebind_shape_v1(changed, facts, current)
            continue
        known, audit = offline.load_source_reviewed_event_v1(state, changed)
        assert known is None and audit["status"] == "unknown", change
