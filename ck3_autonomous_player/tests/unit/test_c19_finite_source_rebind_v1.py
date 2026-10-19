"""Synthetic portable fixtures and an unapplied, exact-base loader candidate."""
import copy
import hashlib
import json
from pathlib import Path
import types

import pytest

from xar_autoplayer.vanilla_events import event_offline_analysis as original
from xar_autoplayer.vanilla_events import c19_finite_source_rebind_v1 as finite


ROOT = Path(__file__).resolve().parents[3]
HUNKS = ROOT / "docs/ck3-native-ai/evidence/g2-m2-c19-finite-source-rebind-hunks-2026-10-20.json"


def candidate_loader():
    patch = json.loads(HUNKS.read_bytes())
    raw = (ROOT / patch["source_path"]).read_bytes()
    text = raw.decode()
    if hashlib.sha256(raw).hexdigest() == patch["candidate_sha256"]:
        for edit in reversed(patch["edits"]):
            assert text.count(edit["after"]) == 1
            text = text.replace(edit["after"], edit["before"], 1)
    assert hashlib.sha256(text.encode()).hexdigest() == patch["base_sha256"]
    baseline = types.ModuleType("xar_autoplayer.vanilla_events._c19_frozen_baseline")
    baseline.__package__ = original.__package__
    exec(compile(text, str(ROOT / patch["source_path"]) + " [frozen baseline]", "exec"), baseline.__dict__)
    for edit in patch["edits"]:
        assert text.count(edit["before"]) == 1
        text = text.replace(edit["before"], edit["after"], 1)
    assert hashlib.sha256(text.encode()).hexdigest() == patch["candidate_sha256"]
    module = types.ModuleType("xar_autoplayer.vanilla_events._c19_memory_candidate")
    module.__package__ = original.__package__
    exec(compile(text, str(ROOT / patch["source_path"]) + " [C19 memory candidate]", "exec"), module.__dict__)
    module._baseline_loader = baseline
    return module, patch, text, raw


def scope(name, kind="character", raw=4, identity=None, null=False):
    typed = ({"status": "unavailable", "reason": "character_scope_is_null"} if null else
             {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"} if identity is None else
             {"status": "available", "kind": kind, kind + "_id": identity})
    return {"name": name, "name_identifier": 1, "scope": {
        "status": "available", "raw_type_index": raw, "type_key": kind, "subtype": 0, "typed_identity": typed}}


def publish(state, facts):
    fp = original._fingerprint(facts["binding"])
    facts["fingerprint"] = fp
    facts_pin = original.write_immutable(state / "evidence/event-source-registry/facts" / (fp + ".json"), facts)
    original.write_immutable(state / "evidence/event-source-registry" / (fp + ".json"), {
        "schema": original.SCHEMA, "fingerprint": fp, "binding": facts["binding"],
        "source_path": facts["source_path"], "source_facts": facts_pin,
        "classification": "offline-source-reviewed-user-first-rendered-policy"})


@pytest.fixture(params=sorted(finite.REVIEWS))
def case(request, tmp_path, monkeypatch):
    key = request.param
    review = copy.deepcopy(finite.REVIEWS)
    row = review[key]
    source = tmp_path / "game" / row["source_relative"]
    source.parent.mkdir(parents=True)
    definition = key + " = {\n" + (" type = letter_event\n" if key.startswith("pam_") else "")
    definition += " option = {\n name = synthetic.ack\n }\n}\n"
    source.write_bytes(definition.encode())
    options = [{"native_option_index": 0, "source_name_keys": ["synthetic.ack"],
                "source_option": original._blocks(definition, "option")[0]}]
    row.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               definition_sha256=hashlib.sha256(definition.encode()).hexdigest(),
               option_catalogue_sha256=original._fingerprint(options))
    monkeypatch.setattr(finite, "REVIEWS", review)
    guis = {}
    for rel in finite.GUI_SOURCES:
        p = tmp_path / "game" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"SYNTHETIC installed GUI source")
        guis[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(finite, "GUI_SOURCES", guis)
    roles = ([scope("friend", identity=201), scope("victim", identity=301),
              scope("educated_child", identity=101), scope("relative", identity=101),
              scope("new_memory", "character_memory", 34), scope("education_memory", "character_memory", 34)]
             if key == "coming_of_age.0004" else [scope("puppeteer", null=True), scope("hof_scope", identity=401)])
    frame = {"snapshot_id": "native:9", "native_revision": 9, "revision": 4, "date_raw": 1000,
             "actor_character_id": 101, "paused": True, "map_ready": True, "episode_run_id": "SYNTHETIC",
             "bridge_pid": 7, "connection_generation": 2}
    context = {"schema": "current-event-window-context-v1", "schema_version": 1, "status": "available",
               "window_match_count": 1, "event_definition_key": key, "calculated_event_id": 20001,
               "current_event_instance_id": 3, "snapshot_revision": 9, "date_raw": 1000,
               "root_scope": scope("root", identity=101)["scope"], "saved_scopes": roles,
               "readiness": {k: True for k in ("event_definition_identity_ready", "root_scope_ready",
                                             "saved_scopes_ready", "option_presentation_ready")},
               "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1", "root": "module+0x5C6A520->+0x10",
                              "idler_vtable_rva": "0x44BC418", "manager_offset": "+0x28"},
               "options": [{"native_option_index": 0, "rendered_index": 0, "shown": True, "enabled": True}]}
    capture = {"event_definition_key": key, "current_event_instance_id": 3, "snapshot_option_count": 1,
               "binding": frame, "window_context": context, "selection": {
                   "native_option_index": 0, "rendered_index": 0, "option_number": 1, "enabled": True}}
    binding = original._native_binding(capture)
    binding.update(calculated_event_id=10001, source_sha256=row["source_sha256"],
                   option_catalogue_sha256=row["option_catalogue_sha256"])
    facts = {"binding": binding, "definition": definition, "options": options,
             "source_relative": row["source_relative"], "source_path": str(source)}
    state = tmp_path / "state"
    publish(state, facts)
    return capture, facts, state, source, tmp_path / "game", candidate_loader()[0]


def test_exact_base_hunks_roundtrip_without_writing_frozen_sources():
    _, patch, text, raw = candidate_loader()
    for edit in reversed(patch["edits"]):
        assert text.count(edit["after"]) == 1
        text = text.replace(edit["after"], edit["before"], 1)
    assert hashlib.sha256(text.encode()).hexdigest() == patch["base_sha256"]
    assert (ROOT / patch["source_path"]).read_bytes() == raw


def test_same_qualification_accepts_already_composed_bytes_without_double_patch(monkeypatch):
    _, patch, candidate, _ = candidate_loader()
    path = ROOT / patch["source_path"]
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: candidate.encode() if p == path else read(p))
    _, _, again, raw = candidate_loader()
    assert again == candidate and raw == candidate.encode()


def test_only_two_keys_gain_source_knowledge_and_keep_role_gaps(case):
    cap, _, state, _, _, loader = case
    old, baseline = loader._baseline_loader.load_source_reviewed_event_v1(state, cap)
    assert old is None and baseline["status"] == "unknown"
    known, audit = loader.load_source_reviewed_event_v1(state, cap)
    assert known and audit["binding_mode"] == "c19_finite_source_rebound"
    assert known["binding"]["calculated_event_id"] == 10001
    assert audit["fresh_binding"]["calculated_event_id"] == 20001
    assert audit["source_rebind_policy"] == finite.POLICY
    assert audit["registry_contract_accepted"] is False and audit["material_effects_verified"] is False
    assert audit["execution_contract_qualified"] is False and audit["semantic_decision_ready"] is False
    assert audit["loaded_gui_bytes_verified"] is False
    shape = audit["root_scope_shape"]
    assert shape["actor_character_id"] == 101 and shape["source_type_inferred_from_scalar"] is False
    if cap["event_definition_key"] == "coming_of_age.0004":
        assert shape["source_declared_type"] is None and len(audit["scope_identity_gaps"]) == 2
        assert audit["current_role_identities"]["educated_child_character_id"] == 101
    else:
        assert shape["source_declared_type"] == "letter_event"
        assert audit["current_role_identities"] == {"hof_scope_character_id": 401}
        assert audit["scope_identity_gaps"] == [{"role": "puppeteer", "type_key": "character",
                                                "typed_identity_verified": False, "identity_status": "null"}]


def test_fresh_native_roles_are_used_instead_of_old_payloads(case):
    cap, _, state, _, _, loader = case
    cap["binding"]["actor_character_id"] = 701
    cap["window_context"]["root_scope"]["typed_identity"]["character_id"] = 701
    roles = {v["name"]: v for v in cap["window_context"]["saved_scopes"]}
    if "educated_child" in roles:
        for name, identity in (("educated_child", 701), ("relative", 701), ("friend", 801), ("victim", 901)):
            roles[name]["scope"]["typed_identity"]["character_id"] = identity
    else:
        roles["hof_scope"]["scope"]["typed_identity"]["character_id"] = 801
    known, audit = loader.load_source_reviewed_event_v1(state, cap)
    assert known and audit["root_scope_shape"]["actor_character_id"] == 701
    assert 101 not in audit["current_role_identities"].values()
    assert "puppeteer_character_id" not in audit["current_role_identities"]


def test_source_GUI_frame_and_native_role_drift_stays_unknown(case):
    capture, _, state, source, game, loader = case
    for change in ("source", "GUI", "root", "frame", "provider", "readiness", "duplicate", "missing", "extra",
                   "role_type", "role_identity", "fabricated_identity", "option", "selection_bool", "count_bool", "episode",
                   "schema_version_bool", "schema_version_float"):
        cap = copy.deepcopy(capture)
        c = cap["window_context"]
        roles = {v["name"]: v for v in c["saved_scopes"]}
        restore = None
        if change in ("source", "GUI"):
            p = source if change == "source" else game / "gui/shared/event_windows.gui"
            restore = p, p.read_bytes()
            p.write_bytes(restore[1] + b"\nchanged")
        elif change == "root":
            c["root_scope"]["typed_identity"]["character_id"] = 999
        elif change == "frame":
            cap["binding"] = None
        elif change == "provider":
            c["provenance"]["root"] = "other"
        elif change == "readiness":
            c["readiness"]["root_scope_ready"] = False
        elif change == "duplicate":
            c["saved_scopes"].append(copy.deepcopy(c["saved_scopes"][0]))
        elif change == "missing":
            c["saved_scopes"].pop()
        elif change == "extra":
            c["saved_scopes"].append(scope("unknown_role", identity=999))
        elif change == "role_type":
            c["saved_scopes"][0]["scope"]["raw_type_index"] = 99
        elif change == "role_identity":
            name = "educated_child" if "educated_child" in roles else "hof_scope"
            roles[name]["scope"]["typed_identity"] = {"status": "unavailable"}
        elif change == "fabricated_identity":
            name = "new_memory" if "new_memory" in roles else "puppeteer"
            roles[name]["scope"]["typed_identity"] = {"status": "available", "kind": "character", "character_id": 101}
        elif change == "option":
            c["options"][0]["native_option_index"] = 1
        elif change == "selection_bool":
            cap["selection"]["native_option_index"] = False
        elif change == "count_bool":
            cap["snapshot_option_count"] = True
        elif change in ("schema_version_bool", "schema_version_float"):
            c["schema_version"] = True if change == "schema_version_bool" else 1.0
        else:
            cap["binding"]["episode_run_id"] = ""
        try:
            known, audit = loader.load_source_reviewed_event_v1(state, cap)
            assert known is None and audit["status"] == "unknown", change
        finally:
            if restore:
                restore[0].write_bytes(restore[1])


def test_review_drift_and_other_default_types_are_not_admitted(case):
    cap, facts, state, source, _, loader = case
    current = original._native_binding(cap)
    for field in ("definition", "options", "source_relative"):
        changed = copy.deepcopy(facts)
        changed[field] = [] if field == "options" else "different"
        with pytest.raises(ValueError):
            finite.c19_finite_source_rebind_shape_v1(cap, changed, current)
    for field in ("ck3_build", "required_ck3_exe_sha256", "native_backend_id", "event_definition_key"):
        changed = dict(current, **{field: "other"})
        with pytest.raises(ValueError):
            finite.c19_finite_source_rebind_shape_v1(cap, facts, changed)
    # An unrelated default-type/letter event with valid source/entry hashes must
    # still hit the old generic rejection rather than either finite exception.
    other = copy.deepcopy(cap)
    other_key = "unreviewed_source.0001"
    other["event_definition_key"] = other_key
    other["window_context"]["event_definition_key"] = other_key
    foreign = copy.deepcopy(facts)
    foreign["definition"] = foreign["definition"].replace(cap["event_definition_key"], other_key)
    source.write_bytes(foreign["definition"].encode())
    foreign["binding"]["event_definition_key"] = other_key
    foreign["binding"]["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    foreign_state = state.parent / "foreign-state"
    publish(foreign_state, foreign)
    known, audit = loader.load_source_reviewed_event_v1(foreign_state, other)
    assert known is None and audit["status"] == "unknown"
