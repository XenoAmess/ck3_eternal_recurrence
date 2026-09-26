"""A frozen original knight-kill draw anchors candidate compaction and RNG."""

import json
from pathlib import Path

from xar_autoplayer.simulation.combat_core import DrawState


FIXTURE = (
    Path(__file__).parents[2]
    / "src/xar_autoplayer/simulation/data"
    / "ck3_1_19_0_6_episode01_messina_knight_selector_native_parity.json"
)
WRITEBACK = FIXTURE.with_name("ck3_1_19_0_6_episode01_messina_knight_kill_writeback.json")


def test_original_unweighted_knight_selector_resolves_killer_after_tail_swap():
    native = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert native["trace_response_sha256"] == (
        "D5F0442FF068C4BC78C30622047D2831D3F094A0CF68C0AE2AEB1CC5B0CD2729"
    )
    assert native["selection_mode"] == "native_unweighted_modulo_count"
    assert len(native["source_knight_character_ids"]) == 19
    candidates = native["compacted_candidate_character_ids"]
    assert len(candidates) == native["candidate_count"] == 14
    draw, next_state = DrawState(
        native["selector_counter_before"], native["selector_salt_before"]
    ).draw31()
    assert draw == native["selector_draw31"] == 1_400_813_912
    assert next_state.counter == native["selector_counter_before"] + 1
    assert draw % len(candidates) == native["selected_index"] == 8
    assert candidates[8] == native["selected_character_id"] == 34120
    assert native["battle_event"]["right_character_id"] == 34120


def test_original_kill_refreshes_effective_prowess_without_editing_base_skill():
    writeback = json.loads(WRITEBACK.read_text(encoding="utf-8"))
    assert writeback["trace_response_sha256"] == (
        "D5F0442FF068C4BC78C30622047D2831D3F094A0CF68C0AE2AEB1CC5B0CD2729"
    )
    before, after = writeback["target_before_save"], writeback["target_after_save"]
    assert before["base_skill_values"][-1] == after["base_skill_values"][-1] == 2
    assert writeback["target_at_fire_boundary"]["prowess"] == 4
    assert writeback["target_at_final_boundary"]["prowess"] == 2
    assert after["death_reason"] == "death_battle"
    assert after["killer_character_id"] == 34120
    assert before["regiment_id"] == 65 and after["regiment_id"] is None
    assert writeback["killer_base_prowess_change"] == 0
    assert writeback["killer_prestige_currency_delta"] == "150.0000"
    assert writeback["killer_prestige_accumulated_delta"] == "150.0000"


def test_observed_selector_draw_and_root_rng_candidate_reach_frozen_effect_ast():
    partial_path = FIXTURE.with_name(
        "ck3_1_19_0_6_episode01_messina_knight_kill_effect_partial_v4.json"
    )
    partial = json.loads(partial_path.read_text(encoding="utf-8"))
    assert partial["schema"] == "ck3.native_knight_kill_effect_partial_parity.v2"
    observed = partial["native_observed"]
    replay = partial["frozen_ast_replay"]
    assert partial["first_draw_native_parity"] is True
    assert replay["first_draw_record"]["random31"] == observed["selector_draw31"]
    assert replay["first_draw_record"]["selected_index"] == observed["selected_index"]
    assert replay["selected_character_id"] == observed["selected_character_id"] == 34120
    assert replay["root_alive_after"] is False
    assert replay["root_killer_character_id_in_transition"] == 34120
    assert replay["second_draw_root_rng_candidate"] == 26_436_929
    assert replay["growth_transition_conditional"]["selected_branch"] == "no_op"
    assert partial["root_rng_one_draw_observed"] is True
    assert partial["second_draw_growth_callback_native_bound"] is False
    assert partial["selector_mode_in_native"] == "native_unweighted_modulo_count"
    assert replay["selector_mode_in_projection"] == "positive_total_weighted"
    assert partial["selector_index_equivalence_for_equal_weights"] is True
    assert partial["full_effect_write_set_proven"] is False
