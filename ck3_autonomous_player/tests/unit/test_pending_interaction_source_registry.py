"""Synthetic offline catalogue -> same-SDK known lookup; no game installation."""
import copy
import hashlib
import json

import pytest

from xar_autoplayer.interaction_offline_analysis import analyze_batch, block
from test_pending_interaction_left_fallback import fixture, planned, reply, ACTIONS
from xar_autoplayer import pending_interaction_fallback as fallback
from xar_autoplayer import strategy
from xar_autoplayer.pending_interaction_source_registry import load_source_reviewed_interaction_v1


@pytest.fixture
def catalogued(fixture, tmp_path, monkeypatch):
    snapshot, context, _ = fixture
    context["definition"].update(canonical_key="synthetic_unknown_interaction", deterministic_key_hash=12)
    state = tmp_path / "state"
    game = tmp_path / "synthetic-game"
    source = game / "common/character_interactions/synthetic.txt"
    source.parent.mkdir(parents=True)
    source.write_text('synthetic_unknown_interaction = {\n category = interaction_category_religion\n'
                      ' on_accept = { scope:recipient = { add_stress = 10 } }\n'
                      ' on_decline = { # ignored } brace\n scope:recipient = { add_piety = -5 } }\n}\n',
                      encoding="utf-8")
    gui = game / fallback.GUI_LEFT_REPLY["source"]
    gui.parent.mkdir(parents=True)
    gui.write_bytes(b'SYNTHETIC GUI left Reject before right Accept; no screen input')
    monkeypatch.setitem(fallback.GUI_LEFT_REPLY, "sha256", hashlib.sha256(gui.read_bytes()).hexdigest())
    ticket = fallback.capture_pending_interaction_before_v1(state, planned(fixture))
    fallback.capture_pending_interaction_after_v1(ticket, outcome={"result": reply(fixture)})
    manifest = tmp_path / "batch.json"
    manifest.write_text(json.dumps({"completed_control_sequence": 123,
        "new_incidents": fallback.collect_completed_interaction_incidents_v1(state)}), encoding="utf-8")
    return fixture, state, game, manifest, tmp_path / "review", source, gui


def test_unknown_catalogue_then_same_process_known_without_reconnect(catalogued):
    fixture, state, game, manifest, output, source, gui = catalogued
    before = strategy.choose_one_life_turn(fixture[2], snapshot=fixture[0], action_steps=ACTIONS,
                                          pending_interaction_registry_state_dir=state)
    assert before["decision"]["registry_known"] is False
    report = analyze_batch(manifest, game, output, publish_state_dir=state)
    assert report["entries"][0]["known_next_same_key"] is True
    after = strategy.choose_one_life_turn(fixture[2], snapshot=fixture[0], action_steps=ACTIONS,
                                         pending_interaction_registry_state_dir=state)
    assert after["selected_step"] == before["selected_step"] == "reject-pending-character-interaction"
    assert after["decision"]["classification"] == "offline-source-reviewed-user-left-policy"
    capture = after["unhandled_interaction_fallback"]
    assert capture["registry_known"] is True and capture["offline_followup_required"] is False
    assert capture["offline_registry_audit"]["material_effects_verified"] is False
    facts = json.loads(open(report["entries"][0]["source_facts"]["path"], "rb").read())
    assert "add_stress = 10" in facts["on_accept"]
    assert "add_piety = -5" in facts["on_decline"]
    assert facts["category"] == ["interaction_category_religion"]


def test_different_batches_and_output_dirs_publish_same_fingerprint_idempotently(catalogued, tmp_path):
    fixture, state, game, manifest, output, source, gui = catalogued
    first = analyze_batch(manifest, game, output, publish_state_dir=state)
    first_entry = first["entries"][0]
    from pathlib import Path
    published_path = Path(first_entry["published"]["path"])
    original_bytes = published_path.read_bytes()
    original_stamp = published_path.stat().st_mtime_ns
    entry = json.loads(original_bytes)
    canonical = first_entry["canonical_source_facts"]
    assert Path(canonical["path"]).parent == state / "evidence/interaction-source-registry/facts"
    assert entry["source_facts"] == canonical
    assert first_entry["source_facts"]["path"] != canonical["path"]

    # A distinct synthetic request, incident and completed batch; same definition/build/source.
    fixture[0]["pending_character_interaction"]["instance_id"] += 1
    fixture[1]["pending_interaction_id"] += 1
    ticket = fallback.capture_pending_interaction_before_v1(state, planned(fixture))
    fallback.capture_pending_interaction_after_v1(ticket, outcome={"result": reply(fixture)})
    previous = json.loads(manifest.read_bytes())["new_incidents"]
    second_manifest = tmp_path / "batch-next.json"
    second_manifest.write_text(json.dumps({"completed_control_sequence": 124,
        "new_incidents": fallback.collect_completed_interaction_incidents_v1(
            state, [row["incident_id"] for row in previous])}), encoding="utf-8")
    second_output = tmp_path / "review-next"
    second = analyze_batch(second_manifest, game, second_output, publish_state_dir=state)
    second_entry = second["entries"][0]
    assert second_entry["fingerprint"] == first_entry["fingerprint"]
    assert second_entry["canonical_source_facts"] == canonical
    assert second_entry["source_facts"]["path"] != first_entry["source_facts"]["path"]
    assert published_path.read_bytes() == original_bytes
    assert published_path.stat().st_mtime_ns == original_stamp
    assert second_entry["published"] == first_entry["published"]
    known = strategy.choose_one_life_turn(fixture[2], snapshot=fixture[0], action_steps=ACTIONS,
                                         pending_interaction_registry_state_dir=state)
    assert known["decision"]["classification"] == "offline-source-reviewed-user-left-policy"
    assert known["unhandled_interaction_fallback"]["offline_followup_required"] is False


def test_unpublished_catalogue_keeps_local_source_facts(catalogued):
    fixture, state, game, manifest, output, source, gui = catalogued
    report = analyze_batch(manifest, game, output)
    row = report["entries"][0]
    from pathlib import Path
    entry = json.loads(Path(row["candidate"]["path"]).read_bytes())
    assert entry["source_facts"] == row["source_facts"]
    assert row["canonical_source_facts"] is None and row["published"] is None
    assert not (state / "evidence/interaction-source-registry").exists()


@pytest.mark.parametrize("mutation", ["build", "exe_sha", "hash", "gui_sha", "source_file", "facts_file"])
def test_review_binding_mismatch_remains_unknown(catalogued, mutation):
    fixture, state, game, manifest, output, source, gui = catalogued
    report = analyze_batch(manifest, game, output, publish_state_dir=state)
    # Populate fingerprint memo, then ensure changed underlying material invalidates it.
    assert load_source_reviewed_interaction_v1(state, fixture[1], fallback.GUI_LEFT_REPLY)[0] is not None
    context, gui_binding = copy.deepcopy(fixture[1]), copy.deepcopy(fallback.GUI_LEFT_REPLY)
    if mutation == "build":
        context["build"]["version"] = "1.20.0.5"
    elif mutation == "exe_sha":
        context["build"]["exe_sha256"] = "DIFFERENT-SYNTHETIC-EXE"
    elif mutation == "hash":
        context["definition"]["deterministic_key_hash"] += 1
    elif mutation == "gui_sha":
        gui_binding["sha256"] = "0" * 64
    elif mutation == "source_file":
        source.write_bytes(source.read_bytes() + b'\n# changed source\n')
    else:
        path = report["entries"][0]["canonical_source_facts"]["path"]
        from pathlib import Path
        Path(path).write_bytes(b'{}')
    known, audit = load_source_reviewed_interaction_v1(state, context, gui_binding)
    assert known is None and audit["status"] == "unknown"


def test_missing_original_definition_stays_unknown_without_fake_entry(catalogued):
    fixture, state, game, manifest, output, source, gui = catalogued
    source.unlink()
    report = analyze_batch(manifest, game, output, publish_state_dir=state)
    assert report["entries"] == [] and report["unresolved"][0]["status"] == "unknown"
    assert not list((state / "evidence/interaction-source-registry").glob("*.json"))


def test_offline_incident_sha_mismatch_rejected(catalogued):
    fixture, state, game, manifest, output, source, gui = catalogued
    batch = json.loads(manifest.read_bytes())
    batch["new_incidents"][0]["before_sha256"] = "0" * 64
    manifest.write_text(json.dumps(batch), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA/identity"):
        analyze_batch(manifest, game, output, publish_state_dir=state)


def test_combined_batch_keeps_event_registry_work_separate(catalogued):
    fixture, state, game, manifest, output, source, gui = catalogued
    batch = json.loads(manifest.read_bytes())
    batch["new_incidents"].append({"kind": "active_event", "incident_id": "synthetic-event"})
    manifest.write_text(json.dumps(batch), encoding="utf-8")
    report = analyze_batch(manifest, game, output, publish_state_dir=state)
    assert len(report["entries"]) == 1


def test_ck3_source_block_preserves_scopes_and_ignores_string_comment_braces():
    source = 'x = {\n on_decline = { # }\n log = "quoted }"\n scope:recipient = { add_stress = 10 }\n }\n}'
    decline = block(block(source, "x"), "on_decline")
    assert decline.endswith("}") and "scope:recipient = { add_stress = 10 }" in decline
