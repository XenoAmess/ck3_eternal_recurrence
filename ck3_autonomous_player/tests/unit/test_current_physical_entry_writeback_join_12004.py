"""AUTHORED_NOTRUN: retained Native67 input through the new current Entry join.

The original whole packet is consumed once by registered MCP/Service/Driver.
Current control rows are synthetic inputs to the production normalizer and
adapter; their physical addresses are not a native current-row qualification.
No native producer or earlier registered compound is replayed.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_battle_current_condition import Q, _army, _entry, _raw_frame, _side
from test_battle_current_refresh import _counter
from test_physical_entry_writeback_registered_mcp_12004 import (
    ATTACKER, DATE_RAW, DEFENDER, ENTRY_PROVINCE, LINKED, NATIVE_REVISION,
    PUBLIC_REVISION, REGIMENT, TARGET, TOOL, WHOLE_BASENAME,
    _WholePacketEndpoint, _paused_snapshot,
)
from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_knight_entry_refresh import associate_current_knight_entries
from xar_autoplayer.simulation.battle_current_next_day import NextMainTickContext
from xar_autoplayer.simulation.battle_current_refresh import DynamicRefreshContext
from xar_autoplayer.simulation.combat_core import DrawState


WIRE_ENV = "CK3_CURRENT_PHYSICAL_ENTRY_WRITEBACK_12004_WIRE_DIR"
STORED_FIELDS = (
    "effective_max_size", "effective_siege_raw", "effective_damage_raw",
    "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw",
)
STORED_STATS = dict(zip(STORED_FIELDS, (100, 0, 1234567, 7654321, 0, 0)))


def _synthetic_current_context(physical_entry_identity, regiment_id=REGIMENT):
    """Create one valid current MAA row per independent synthetic frame."""
    raw = _raw_frame(1)
    own = _army(0x02000001, ATTACKER, 707)
    enemy = _army(0x02000002, DEFENDER, 808)
    row = _entry(regiment_id, own, bucket="men_at_arms", index=0,
                 current=300000, damage=STORED_STATS["effective_damage_raw"],
                 toughness=STORED_STATS["effective_toughness_raw"])
    row["knight_character_id_raw"] = LINKED
    row["physical_entry_identity"] = hex(physical_entry_identity)
    raw["attacker"] = _side(0, [own], [], [row], [(707, 0)])
    raw["defender"] = _side(1, [enemy], [
        _entry(0x06000005, enemy, bucket="levy", index=0,
               current=1000000, damage=Q, toughness=2 * Q),
    ], [], [(808, 0)])
    raw.update({
        "snapshot_revision": NATIVE_REVISION, "observed_date_raw": DATE_RAW,
        "subject_public_cunit_id": ATTACKER, "subject_native_carmy_id": own["native_carmy_id"],
        "selected_public_cunit_id": ATTACKER, "selected_native_carmy_id": own["native_carmy_id"],
        "selected_owner_character_id": 707,
        "province_id": TARGET, "combat_province_id": TARGET,
        "affected_public_cunit_ids_in_stored_order": [ATTACKER],
    })
    raw["legality"]["retreat_elapsed_baseline_date_raw"] = DATE_RAW
    raw["legality"]["earliest_day_gate_date_raw"] = DATE_RAW + 15 * 24
    raw["current_loss_inputs_v1"]["source_target_province_id"] = TARGET
    for index, owner in enumerate((707, 808)):
        raw["current_loss_inputs_v1"]["sides"][index]["primary_participant_character_id"] = owner
    _counter(raw, Q)
    if regiment_id < 0:
        # This separate signed-ID representation case does not supply the
        # unrelated optional active-counter family or claim its qualification.
        raw.pop("active_counter_inputs_v1")
    untouched = deepcopy(raw)
    frame = normalize_battle_control_snapshot_v1(
        raw, expected_subject_public_cunit_id=ATTACKER,
        expected_observed_date_raw=DATE_RAW, expected_snapshot_revision=NATIVE_REVISION,
    )
    assert raw == untouched
    condition = adapt_current_battle_condition(frame)
    context = NextMainTickContext(
        condition=condition, draw_state=DrawState(11, 17),
        scope_kind="synthetic_current_control_observation", refresh_mode="fresh_observed",
        conditional_assumptions=(), simulated_main_ticks=0,
        origin_observed_frame={"snapshot_revision": NATIVE_REVISION, "observed_date_raw": DATE_RAW},
        derived_side_totals=(), roll_cadence_interval=None,
        roll_cadence_interval_source=None, roll_cadence_advanced=False,
    )
    refreshed = DynamicRefreshContext(context, {"missing_inputs": condition.missing_inputs}, ())
    return raw, frame, refreshed


def test_current_physical_entry_writeback_join_12004():
    from mcp import Client

    packet = json.loads((Path(os.environ[WIRE_ENV]) / WHOLE_BASENAME).read_bytes())
    original = deepcopy(packet)
    step = query_combat_simulation_inputs_step(TARGET, ENTRY_PROVINCE, [ATTACKER], [DEFENDER])
    assert packet["type"] == "command_result" and packet["ok"] is True
    assert packet["result"]["step"] == step
    assert packet["result"]["accepted"] is True and packet["result"]["query_sequence"] == 1
    endpoint = _WholePacketEndpoint(step, packet)
    driver = NativeHeadlessGameplayDriver(endpoint=endpoint, episode_projection="native_campaign")
    hello = {
        "type": "hello", "protocol_version": 1, "pid": 1,
        "capabilities": ["game.state.snapshot", QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
        "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
    }
    assert driver.state.ingest(hello) == "hello"
    snapshot = _paused_snapshot(hello)
    raw_writeback = packet["result"]["combat_simulation_inputs"][
        "knight_stat_consumption_v1"]["events"][0]["physical_entry_writeback"]
    raw_identity = raw_writeback["entry_identity"]
    seed_identity = int(raw_identity, 0) if isinstance(raw_identity, str) else raw_identity
    raw, frame, refreshed = _synthetic_current_context(seed_identity)
    snapshot["battle_control_snapshot_v1"] = deepcopy(frame)

    async def exercise():
        with patch.object(driver, "take_snapshot", side_effect=lambda **kwargs: deepcopy(snapshot)):
            async with Client(create_server(driver)) as client:
                assert TOOL in {tool.name for tool in (await client.list_tools()).tools}
                response = await client.call_tool(TOOL, {
                    "target_province_id": TARGET, "attacker_entry_province_id": ENTRY_PROVINCE,
                    "attacker_army_ids": [ATTACKER], "defender_army_ids": [DEFENDER],
                    "expected_revision": PUBLIC_REVISION,
                })
                assert response.is_error is False, response.content
                actual = response.structured_content
                assert actual["queried_snapshot_id"] == snapshot["snapshot_id"]
                assert actual["queried_revision"] == PUBLIC_REVISION
                assert actual["queried_native_revision"] == NATIVE_REVISION
                projection = actual["knight_stat_consumption_projection_v1"]
                assert projection["physical_entry_associated_event_count"] == 1
                assert len(projection["events"]) == 2
                writer, scratch = projection["events"]
                assert writer["sequence"] == 1 and writer["entry_association_proven"] is True
                assert scratch["sequence"] == 2 and scratch["origin"] == "bridge_query_scratch"
                assert scratch["entry_association_proven"] is False
                assert scratch["physical_entry_writeback"] is None
                assert writer["projected_effectiveness_raw"] == 95000
                assert writer["projected_output"]["damage_raw"] == 28500000
                assert writer["projected_output"]["toughness_raw"] == 2850000
                for key in ("full_person_ready", "full_entry_ready"):
                    assert projection[key] is False
                assert writer["physical_entry_writeback"]["entry_identity"] == seed_identity
                return actual, projection, raw, frame, refreshed

    try:
        actual, projection, raw, frame, refreshed = asyncio.run(exercise())
        writer, scratch = projection["events"]
        physical_identity = writer["physical_entry_writeback"]["entry_identity"]
        expected_identities = [physical_identity]
        assert [row["physical_entry_identity"] for row in raw["attacker"]["men_at_arms_entries"]] == [
            hex(value) for value in expected_identities]
        assert [row["physical_entry_identity"] for row in frame["attacker"]["men_at_arms_entries"]] == expected_identities
        entries = refreshed.condition.sides[0].entries
        assert [row.physical_entry_identity for row in entries] == expected_identities
        assert [row.source_entry["physical_entry_identity"] for row in entries] == expected_identities
        assert {row.state.regiment_id for row in entries} == {REGIMENT}
        assert {row.knight_character_id_raw for row in entries} == {LINKED}
        assert {row.native_carmy_id for row in entries} == {0x02000001}
        assert {row.public_cunit_id for row in entries} == {ATTACKER}
        condition_before, projection_before = deepcopy(refreshed.condition), deepcopy(projection)
        join_kwargs = {
            "current_combat_armies": actual["combat_simulation_inputs"]["armies"],
            "combat_query_source": {"native_revision": NATIVE_REVISION, "date_raw": DATE_RAW},
            "control_query_source": {"native_revision": NATIVE_REVISION, "date_raw": DATE_RAW},
        }
        joined = associate_current_knight_entries(
            refreshed, **join_kwargs,
            current_knight_stat_consumption_projection=projection,
        )
        assert joined.refreshed is refreshed and joined.condition is refreshed.condition
        assert joined.condition == condition_before and projection == projection_before
        current_rows = joined.ledger["sides"][0]["entries_in_native_order"]
        assert len(current_rows) == 1
        for index, row in enumerate(current_rows):
            assert row["identity"]["bucket_index"] == index
            assert row["identity"]["regiment_id"] == REGIMENT
            assert row["knight_identity"]["raw"] == LINKED
            assert row["stored_combat_entry_attributes"] == STORED_STATS
            assert row["current_knight_evaluation"]["status"] == "available"
            association = row["physical_entry_writeback_association"]
            assert association["physical_entry_identity"] == expected_identities[index]
            assert association["historical_record_is_current_cache"] is False
            assert association["stored_stats_replaced"] is False
        matched = current_rows[0]["physical_entry_writeback_association"]
        assert matched["status"] == "physical_entry_writeback_observed"
        records = matched["matching_events_in_capture_order"]
        assert len(records) == 1 and records[0]["sequence"] == writer["sequence"] == 1
        assert records[0]["observed_date_raw"] == writer["observed_date_raw"] == DATE_RAW
        assert records[0]["thread_id"] == writer["thread_id"]
        assert records[0]["consumed_contexts"] == writer["consumed_contexts"]
        assert records[0]["physical_entry_writeback"] == writer["physical_entry_writeback"]
        assert records[0]["projected_output"] == writer["projected_output"]
        assert records[0]["physical_entry_field_matches"] == writer["physical_entry_field_matches"]
        assert records[0]["capture_date_matches_current_frame"] is True
        assert records[0]["writer_province_matches_current_frame"] is True
        assert set(records[0]["query_source_coordinate_checks"].values()) == {True}
        assert records[0]["historical_record_is_current_cache"] is False
        assert matched["current_cache_matches_writeback"] is False
        assert len(matched["current_cache_field_matches"]) == 6
        assert set(matched["current_cache_field_matches"].values()) == {False}
        assert scratch["sequence"] not in [row["sequence"] for row in records]
        assert joined.ledger["current_physical_entry_writeback_association_v1"] is not None
        assert actual["current_physical_entry_writeback_association_v1"] == joined.ledger[
            "current_physical_entry_writeback_association_v1"]
        for claim in ("fresh_condition_modified", "full_person_ready", "full_entry_ready"):
            assert actual["current_physical_entry_writeback_association_v1"][claim] is False
        assert joined.ledger["fresh_condition_modified"] is False
        assert joined.ledger["person_state_used_to_replace_stored_stats"] is False
        assert [dict((key, row.source_entry[key]) for key in STORED_FIELDS)
                for row in joined.condition.sides[0].entries] == [STORED_STATS]

        # A second valid current frame has the same logical Regiment/Knight
        # but a different physical Entry. It is not a second MCP/native input.
        alternate_raw, alternate_frame, alternate = _synthetic_current_context(physical_identity + 0x60)
        alternate_before = deepcopy(alternate.condition)
        alternate_joined = associate_current_knight_entries(
            alternate, **join_kwargs, current_knight_stat_consumption_projection=projection,
        )
        assert len(alternate_raw["attacker"]["men_at_arms_entries"]) == 1
        assert len(alternate_frame["attacker"]["men_at_arms_entries"]) == 1
        assert alternate_joined.condition is alternate.condition
        assert alternate_joined.condition == alternate_before
        alternate_row = alternate_joined.ledger["sides"][0]["entries_in_native_order"][0]
        assert alternate_row["identity"]["regiment_id"] == current_rows[0]["identity"]["regiment_id"] == REGIMENT
        assert alternate_row["knight_identity"] == current_rows[0]["knight_identity"]
        assert alternate_row["current_knight_evaluation"]["status"] == "available"
        assert alternate_row["stored_combat_entry_attributes"] == STORED_STATS
        unrelated = alternate_row["physical_entry_writeback_association"]
        assert unrelated["physical_entry_identity"] == physical_identity + 0x60
        assert unrelated["status"] == "no_matching_physical_entry_writeback"
        assert unrelated["matching_events_in_capture_order"] == []
        assert unrelated["current_cache_matches_writeback"] is None
        assert unrelated["current_cache_field_matches"] is None
        assert unrelated["historical_record_is_current_cache"] is False
        assert unrelated["stored_stats_replaced"] is False

        # Synthetic representation input only: the retained native whole and
        # its actual Service projection keep their original full Regiment ID.
        high_bit_full_id = 0x86000004
        signed_regiment = high_bit_full_id - (1 << 32)
        synthetic_projection = deepcopy(projection)
        for event in synthetic_projection["events"]:
            event["regiment_id"] = high_bit_full_id
            if event["physical_entry_writeback"] is not None:
                event["physical_entry_writeback"]["regiment_id"] = high_bit_full_id
        high_raw, high_frame, high_context = _synthetic_current_context(physical_identity, signed_regiment)
        assert high_raw["attacker"]["men_at_arms_entries"][0]["regiment_id"] == signed_regiment < 0
        assert high_frame["attacker"]["men_at_arms_entries"][0]["regiment_id"] == signed_regiment
        assert high_context.condition.sides[0].entries[0].state.regiment_id == signed_regiment
        high_before, synthetic_before = deepcopy(high_context.condition), deepcopy(synthetic_projection)
        high_joined = associate_current_knight_entries(
            high_context, **join_kwargs, current_knight_stat_consumption_projection=synthetic_projection,
        )
        high_row = high_joined.ledger["sides"][0]["entries_in_native_order"][0]
        assert high_row["identity"]["regiment_id"] == signed_regiment
        assert high_row["stored_combat_entry_attributes"] == STORED_STATS
        high_association = high_row["physical_entry_writeback_association"]
        assert high_association["status"] == "physical_entry_writeback_observed"
        high_records = high_association["matching_events_in_capture_order"]
        assert [event["sequence"] for event in high_records] == [1]
        assert high_records[0]["regiment_id"] == high_bit_full_id
        assert high_records[0]["physical_entry_writeback"]["regiment_id"] == high_bit_full_id
        assert (high_row["identity"]["regiment_id"] & 0xFFFFFFFF) == high_bit_full_id
        assert high_association["historical_record_is_current_cache"] is False
        assert high_association["stored_stats_replaced"] is False
        assert high_joined.condition is high_context.condition and high_joined.condition == high_before
        assert synthetic_projection == synthetic_before and projection == projection_before
        assert len(endpoint.requests) == len(endpoint.delivered) == 1
        assert packet == original and endpoint.packet == original
        assert driver.state._command_results == {}
        assert actual["monte_carlo_ready"] is False
        print(json.dumps({
            "status": "GREEN", "retained_whole_packets": 1, "registered_mcp_calls": 1,
            "service_projection_consumed": True, "service_current_join_consumed": True,
            "synthetic_current_frames": 3, "synthetic_current_rows_per_frame": 1,
            "current_row_native_qualification_claimed": False,
            "same_logical_regiment_and_knight": True, "distinct_physical_entries": 2,
            "matched_current_rows": 1, "unmatched_current_rows": 1,
            "synthetic_high_bit_full_id_joined": True, "signed_current_regiment_preserved": True,
            "matched_writer_sequences": [1], "query_scratch_association_granted": False,
            "current_cache_field_comparisons": 6, "stored_current_stats_unchanged": True,
            "historical_record_is_current_cache": False,
            "native_payload_rewritten": False, "native_producer_replayed": False,
            "full_person_ready": False, "full_entry_ready": False,
            "actual_model_write_performed": False, "new_g2_credit": 0,
        }))
    finally:
        driver.close()
