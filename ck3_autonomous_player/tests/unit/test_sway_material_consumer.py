"""One compound for the original resolved intervention's independent material.

Synthetic source inputs, not game or actual4 native qualification. Root owns
the first execution of this newly authored compound.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xar_autoplayer.sway_formal_consumer import (
    LEDGER_FILE, SCHEMA, consume_sway_following_turn, read_sway_ledger,
)
from xar_autoplayer.sway_material_consumer import record_sway_material_intervention


def test_original_sway_material_consumption_compound(tmp_path: Path):
    # Start was already independently applied and consumed. Material must have
    # its own new following-turn consumption, without repeating that Start.
    original = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": 29829, "target_character_id": 34333,
        "action_id": "sway-original", "post_native_revision": 18,
        "post_date_raw": 53220000, "next_turn_consumed": True,
        "following_native_revision": 6, "following_date_raw": 53220048,
        "native_receipt": {"scheme_instance_id": 134217986,
                           "scheme_instance_generation": 8},
    }
    (tmp_path / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": original,
    }), encoding="utf-8")
    pair = {
        "actor_character_id": 29829, "target_character_id": 34333,
        "date_raw": 53288256, "exact_ck3_build": "1.20.0.4",
        "exe_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
    }
    instance = {"scheme_instance_id": 134217986,
                "scheme_instance_generation": 8, "target_character_id": 34333}
    read = {**pair, "schema": "active-scheme-sway-private-read-v1",
            "active_sway_instances": [instance]}
    absent = {"observed": True, "present": False, "value": None}
    opinion = {**pair, "schema": "xar.ck3.sway-outcome-opinion-v1",
               "available": True, "snapshot_revision": 5,
               "target_opinion_of_actor": -8,
               "scheme_sway_opinion": absent, "sway_blocker_opinion": absent}
    baseline = record_sway_material_intervention(
        tmp_path, sway_read=read, opinion_read=opinion)
    assert baseline["dedicated_benefit_observed"] is False
    assert baseline["scheme_sway_opinion"] == absent
    # A total-opinion improvement alone does not prove a Sway gain.
    total_only = record_sway_material_intervention(
        tmp_path, sway_read={**read, "date_raw": 53288304},
        opinion_read={**opinion, "date_raw": 53288304,
                      "snapshot_revision": 6, "target_opinion_of_actor": 27})
    assert total_only["dedicated_benefit_observed"] is False
    assert total_only["incremental_named_gain_observed"] is False
    # Same known instance and pair; a dedicated absent->25 measurement is
    # material, while a continuing instance still supplies no terminal.
    positive = {**opinion, "date_raw": 53288328, "snapshot_revision": 7,
                "target_opinion_of_actor": 27,
                "scheme_sway_opinion": {"observed": True, "present": True, "value": 25}}
    material = record_sway_material_intervention(
        tmp_path, sway_read={**read, "date_raw": 53288328}, opinion_read=positive)
    assert material["dedicated_benefit_observed"] is True
    assert material["incremental_named_gain_observed"] is True
    assert material["decision"] == "retain_existing_sway"
    assert material["instance_terminal_outcome_observed"] is False
    after = {"paused": True, "map_ready": True, "revision": 9,
             "native_revision": 8, "date_raw": 53288352,
             "played_character": {"character_id": 29829, "alive": True}}
    consumed = consume_sway_following_turn(tmp_path, after)
    assert consumed["next_turn_consumed"] is True
    assert consumed["following_date_raw"] == original["following_date_raw"]
    assert consumed["material_intervention"]["next_turn_consumed"] is True
    assert consumed["material_intervention"]["following_date_raw"] == after["date_raw"]
    assert consume_sway_following_turn(tmp_path, after) is None
    assert read_sway_ledger(tmp_path)["pending"] is None
    # Another target's actual4 eligibility cannot be attached to this action.
    with pytest.raises(ValueError, match="target_character_id"):
        record_sway_material_intervention(
            tmp_path, sway_read=read, opinion_read={**opinion, "target_character_id": 34730})
    gone = record_sway_material_intervention(
        tmp_path, sway_read={**read, "active_sway_instances": [], "date_raw": 53288376},
        opinion_read={**positive, "date_raw": 53288376, "snapshot_revision": 9})
    assert gone["tracked_instance_active"] is False
    assert gone["dedicated_benefit_observed"] is True
    assert gone["instance_terminal_outcome_observed"] is False
    assert gone["decision"] == "observe_tracked_instance_end"
