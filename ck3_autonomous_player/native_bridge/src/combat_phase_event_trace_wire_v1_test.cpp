#include "xar_bridge/combat_phase_event_trace_wire_v1.hpp"

#include <cstring>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

bool Fail(std::string_view reason) {
  std::cerr << reason << '\n';
  return false;
}

bool Has(std::string_view source, std::string_view token) {
  return source.find(token) != std::string_view::npos;
}

std::unique_ptr<CombatPhaseEventTraceRingDrainV1> SmallDrain() {
  auto drain = std::make_unique<CombatPhaseEventTraceRingDrainV1>();
  drain->record_count = 7;
  drain->outgoing_damage_count = 2;
  drain->outgoing_damage_raw = {310'000, 280'000};
  drain->outgoing_damage_pair_complete = true;
  drain->post_counter_attack_count = 2;
  drain->post_counter_attack_raw = {10'333'333, 6'222'222};
  drain->post_counter_attack_pair_complete = true;
  drain->effect_root_count = 1;
  drain->effect_roots[0] = {1, 11, 0x3BA, 1234, 2708350930U,
                             0, 2708350931U, 0};
  drain->effect_node_call_count = 3;
  drain->effect_node_draw_count = 1;
  drain->effect_node_draws[0] = {1, 11, 2, 2, 0x3BB, 0x3BA,
                                 5678, 0x44782B0, 2708350930U, 0,
                                 2708350931U, 0};
  drain->knight_select_count = 1;
  drain->knight_selects[0] = {1, 11, 14, 8, 0x111, 0x222,
                              612212889U, 0, 612212890U, 0};
  drain->exact_boundary_sequence = true;
  drain->same_full_generation_combat = true;
  drain->same_native_date = false;
  drain->expected_one_day_date_split = true;
  drain->same_loaded_event_table = true;
  drain->loaded_event_row_objects_available = true;
  for (std::size_t index = 0;
       index < drain->loaded_event_row_objects.size(); ++index) {
    drain->loaded_event_row_objects[index] = 0x1000 + index;
  }
  drain->loaded_event_row_objects[0] = 0x142;
  drain->loaded_event_row_objects[10] = 0x243;
  drain->loaded_event_row_objects[11] = 0x242;
  drain->side_and_return_site_identity = true;
  drain->schedule_phase_day_then_single_increment = true;
  drain->bounded_capture_complete = true;
  drain->full_mutable_transition_bundle_complete = false;
  drain->production_trace_ready = false;
  for (std::uint32_t index = 0; index < drain->record_count; ++index) {
    auto &record = drain->records[index];
    record.boundary = static_cast<CombatPhaseEventTraceBoundaryV1>(index);
    record.managed_daily_sequence_token = 77;
    record.combat_id = 0x01000001;
    record.native_date_raw = 53'175'816;
    record.phase_raw = 1;
    record.phase_day = index < 2 ? 4 : 5;
    record.winner_side_raw = -1;
    record.battle_result_id = 0x01000002;
    record.base_advantage_raw = 300'000;
    record.resolved_advantage_raw = 600'000;
    record.advantage_rolls_raw = {2, 5};
    record.schedule_local_rng_present = index < 2;
    record.schedule_local_rng_word0 = 100 + index;
    record.schedule_local_rng_word1 = index;
    record.global_rng_counter = 900 + index;
    record.global_rng_salt = 0x12345678;
    record.global_rng_owner_thread_token = 44;
    for (std::size_t side_index = 0; side_index < 2; ++side_index) {
      auto &side = record.sides[side_index];
      side.side_index = static_cast<std::int32_t>(side_index);
      side.selected_commander_character_id =
          side_index == 0 ? 101 : 201;
      side.current_fighting_total_raw =
          side_index == 0 ? 1'000'000 : 1'100'000;
      side.first_fighting_subtotal_raw = 500'000;
      side.scheduled_commander_event_identity = 0x00000142;
      side.army_count = 1;
      side.armies[0] = {side_index == 0 ? 11 : 21,
                        side_index == 0 ? 101 : 201,
                        record.combat_id};
      side.regiment_count = 2;
      side.regiments[0] = {side_index == 0 ? 32 : 42,
                           side_index == 0 ? 11 : 21,
                           0, false, false,
                           500'000, 0, 0, false, 0,
                           80'000, 60'000};
      side.regiments[1] = {side_index == 0 ? 31 : 41,
                           side_index == 0 ? 11 : 21,
                           0, true, true,
                           1'000'000, 900'000, 50'000, true, 50'000,
                           200'000, 150'000};
      side.hard_owner_count = 1;
      side.hard_owners[0] = {side_index == 0 ? 101 : 201,
                             50'000};
      side.knight_count = 1;
      side.knights[0] = {side_index == 0 ? 31 : 41,
                         side_index == 0 ? 11 : 21,
                         side_index == 0 ? 101 : 201};
      side.scheduled_knight_count = 1;
      side.scheduled_knights[0] = {
          0x00000242 + side_index,
          side_index == 0 ? 31 : 41,
          side_index == 0 ? 101 : 201};
    }
    record.character_count = 2;
    record.characters[0].character_id = 101;
    record.characters[0].prowess = 15 + static_cast<std::int32_t>(index);
    record.characters[0].current_regiment_id = 31;
    record.characters[0].current_regiment_back_reference_matches = true;
    record.characters[1].character_id = 201;
    record.characters[1].prowess = 18;
    record.characters[1].current_regiment_id = 41;
    record.characters[1].current_regiment_back_reference_matches = true;
    record.battle_event_count = index < 3 ? 0 : 1;
    if (record.battle_event_count != 0) {
      auto &battle = record.battle_events[0];
      battle.left_character_id = 101;
      battle.right_character_id = 201;
      battle.type_raw = 2;
      battle.side_index = 0;
      battle.target_right = true;
      constexpr std::string_view key = "phase.\"hit\"";
      battle.stable_key_size = static_cast<std::uint16_t>(key.size());
      std::memcpy(battle.stable_key.data(), key.data(), key.size());
    }
    record.accolade_count = 1;
    record.accolades[0].accolade_id = 51;
    record.accolades[0].owner_character_id = 901;
    record.accolades[0].acclaimed_knight_character_id = 101;
    record.accolades[0].glory_raw = 600'000;
    record.accolades[0].rank_native_mirror = 2;
    record.accolades[0].participant_link_identity_matches = true;
  }
  return drain;
}

bool HappyPath() {
  const auto drain = SmallDrain();
  const auto json = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  constexpr std::array<std::string_view, 44> required{
      "\"schema_version\":1",
      "\"status\":\"captured\"",
      "\"record_count\":7",
      "\"outgoing_damage\":{",
      "\"source\":\"native_main_tick_before_casualty\"",
      "\"side0_raw\":310000",
      "\"side1_raw\":280000",
      "\"outgoing_damage_pair_complete\":true",
      "\"post_counter_attack\":{",
      "\"source\":\"native_r14_after_0x23cae70_before_damage_scaling\"",
      "\"side0_raw\":10333333",
      "\"side1_raw\":6222222",
      "\"post_counter_attack_pair_complete\":true",
      "\"effect_roots\":[",
      "\"effect_node_call_count\":3",
      "\"effect_node_draws\":[",
      "\"call_index\":2",
      "\"depth\":2",
      "\"parent_node_identity_token\":\"process-local-0x3BA\"",
      "\"node_vtable_rva\":71795376",
      "\"knight_selects\":[",
      "\"node_identity_token\":\"process-local-0x3BA\"",
      "\"node_hash\":1234",
      "\"counter_before\":2708350930",
      "\"counter_after\":2708350931",
      "\"same_native_date\":false",
       "\"expected_one_day_date_split\":true",
       "\"loaded_event_row_identity_map_available\":true",
      "\"bounded_capture_complete\":true",
      "\"full_mutable_transition_bundle_complete\":false",
      "\"original_trace_ready\":false",
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "paused_next_day_stable_query",
       "\"event_identity_token\":\"process-local-0x242\"",
       "\"native_event_load_index\":11",
       "\"scheduled_commander_native_event_load_index\":0",
      "\"character_id\":101",
      "\"stable_key\":\"phase.\\\"hit\\\"\"",
      "\"rank_native_mirror\":2",
      "\"regiments\":[",
      "\"bucket\":\"levy\"",
      "\"current_fighting_raw\":900000",
      "\"hard_casualties_raw\":null",
      "\"participant_hard_ledger\":[",
  };
  if (json.empty() || json.size() >
                          kCombatPhaseEventTraceWireMaximumBytesV1) {
    return Fail("happy trace did not serialize within wire limit");
  }
  for (const auto token : required) {
    if (!Has(json, token)) {
      return Fail("happy trace missing required wire token");
    }
  }
  if (Has(json, "\"combat\":") || Has(json, "\"side\":") ||
       Has(json, "\"character\":")) {
    return Fail("wire exposed a reusable native object address field");
  }
  if (Has(json, "\"runtime_random_list_weights\":")) {
    return Fail("default wire unexpectedly changed for optional capture");
  }
  return true;
}

bool OptionalRuntimeWeights() {
  const auto drain = SmallDrain();
  drain->runtime_random_list_weights_requested = true;
  drain->random_list_weight_count = 1;
  auto &row = drain->random_list_weights[0];
  row.side_index = 1;
  row.native_event_load_index = 11;
  row.effect_node_identity = 0x3BA;
  row.entry_count = 3;
  row.pick_count = 1;
  row.weights[0] = 40;
  row.weights[1] = 30;
  row.weights[2] = 15;
  row.entry_node_identities[0] = 0x3BB;
  row.entry_node_identities[1] = 0x3BC;
  row.entry_node_identities[2] = 0x3BD;
  row.selected_entry_count = 1;
  row.selected_entry_identities[0] = 0x3BC;
  row.child_counter_before = 2708350930U;
  row.child_counter_after = 2708350931U;
  const auto json = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  constexpr std::array<std::string_view, 7> required{
      "\"runtime_random_list_weights\":{\"status\":\"captured\",\"count\":1",
      "\"side_index\":1,\"native_event_load_index\":11",
      "\"entry_count\":3,\"pick_count\":1",
      "\"weights\":[40,30,15]",
      "\"weights_bytes_hex\":\"280000001E0000000F000000\"",
      "\"selected_entry_identity_tokens\":[\"process-local-0x3BC\"]",
      "\"child_counter_after\":2708350931",
  };
  for (const auto token : required) {
    if (!Has(json, token)) {
      return Fail("optional runtime weight wire missing token");
    }
  }
  row.entry_count = static_cast<std::uint32_t>(row.weights.size() + 1);
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid runtime weight entry count was admitted");
  }
  row.entry_count = 3;
  drain->random_list_weight_count =
      static_cast<std::uint32_t>(drain->random_list_weights.size() + 1);
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid runtime weight record count was admitted");
  }
  return true;
}

bool InvalidCountsFailClosed() {
  const auto drain = SmallDrain();
  drain->records[0].sides[0].regiment_count =
      static_cast<std::uint32_t>(
          drain->records[0].sides[0].regiments.size() + 1);
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid record count did not fail closed");
  }
  drain->records[0].sides[0].regiment_count = 2;
  drain->outgoing_damage_count = 3;
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid outgoing damage count did not fail closed");
  }
  drain->outgoing_damage_count = 2;
  drain->effect_node_draw_count =
      static_cast<std::uint32_t>(drain->effect_node_draws.size() + 1);
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid nested effect draw count did not fail closed");
  }
  return true;
}

bool MissingRowMapStaysExplicitlyUnknown() {
  const auto drain = SmallDrain();
  drain->loaded_event_row_objects_available = false;
  const auto json = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(json, "\"loaded_event_row_identity_map_available\":false") ||
      !Has(json, "\"native_event_load_index\":null") ||
      !Has(json, "\"scheduled_commander_native_event_load_index\":null")) {
    return Fail("missing event-object map was silently resolved");
  }
  return true;
}

bool OptionalJoinWidthWire() {
  auto drain = SmallDrain();
  const auto ordinary = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (Has(ordinary, "runtime_join_width"))
    return Fail("default wire unexpectedly contains join-width probe");
  drain->runtime_join_width_requested = true;
  drain->join_width_count = 3;
  for (std::uint32_t i = 0; i < 3; ++i) {
    auto &row = drain->join_widths[i];
    row.boundary = i;
    row.thread_id = 42;
    row.native_date_raw = 53'175'840;
    row.combat_id = 0x01000001;
    row.army_id = 22;
    row.side_index = i == 0 ? -1 : 0;
    row.phase_day = 5;
    row.base_width = i == 0 ? 4 : 6;
    row.final_width = i == 0 ? 5 : 7;
    row.outgoing_width_argument = i == 2 ? 7 : -1;
    row.side_fighting_total_raw = {1'300'000, 1'100'000};
  }
  const auto json = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(json, "\"runtime_join_width\":{\"status\":\"captured\",\"count\":3") ||
      !Has(json, "\"first_failure_code\":0") ||
      !Has(json, "\"outgoing_width_argument\":7") ||
      !Has(json, "\"side_fighting_total_raw\":[1300000,1100000]"))
    return Fail("join-width optional wire lost bounded numbers");
  drain->failure_flags |= trace_capture_failure_join_width;
  drain->join_width_first_failure_code = join_width_failure_side_backpointer;
  const auto failed = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(failed, "\"runtime_join_width\":{\"status\":\"failed\",\"count\":3") ||
      !Has(failed, "\"first_failure_code\":6"))
    return Fail("join-width failure predicate was not preserved");
  drain->join_width_count = 4;
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty())
    return Fail("join-width overflow did not fail closed");
  return true;
}

bool OptionalJoinFullEntryWire() {
  auto drain = SmallDrain();
  const auto ordinary = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (Has(ordinary, "runtime_join_full_entries"))
    return Fail("default wire unexpectedly contains full-entry probe");
  drain->runtime_join_width_requested = true;
  drain->runtime_join_full_entries_requested = true;
  drain->join_full_entry_count = 2;
  for (std::uint32_t i = 0; i < 2; ++i) {
    auto &record = drain->join_full_entries[i];
    record.boundary = i;
    record.thread_id = 42;
    record.native_date_raw = 53'175'840;
    record.combat_id = 0x01000001;
    record.incoming_army_id = 22;
    record.joined_side_index = i == 0 ? -1 : 0;
    record.incoming_regiment_count = 1;
    record.incoming_regiments[0] = {43, 30};
    auto &side = record.sides[0];
    side.cached_fighting_total_raw = i == 0 ? 1'200'000 : 4'000'000;
    side.entry_current_sum_raw = i == 0 ? 1'000'000 : 4'000'000;
    side.cache_minus_entry_raw = i == 0 ? 200'000 : 0;
    side.army_count = i == 0 ? 1 : 2;
    side.army_ids[0] = 11;
    side.army_ids[1] = 22;
    side.entry_count = 1;
    side.entries[0] = {31, 11, 1, 0, 1'000'000, 1'000'000, 0,
                       200'000, 150'000};
  }
  const auto json = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(json, "\"runtime_join_full_entries\":{\"status\":\"captured\",\"count\":2") ||
      !Has(json, "\"cache_minus_entry_raw\":200000") ||
      !Has(json, "\"army_ids\":[11,22]") ||
      !Has(json, "\"incoming_regiments\":[[43,30]]") ||
      !Has(json, "\"joined_side_index\":-1") ||
      !Has(json, "\"joined_side_index\":0"))
    return Fail("full-entry optional wire lost bounded values");
  drain->failure_flags |= trace_capture_failure_join_full_entry;
  drain->join_full_entry_first_failure_code =
      join_full_entry_failure_duplicate;
  const auto failed = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(failed, "\"runtime_join_full_entries\":{\"status\":\"failed\",\"count\":2") ||
      !Has(failed, "\"first_failure_code\":7"))
    return Fail("full-entry failure status was not preserved");
  drain->join_full_entry_count = 3;
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty())
    return Fail("full-entry boundary overflow did not fail closed");
  return true;
}

bool OptionalCounterOutputWire() {
  auto drain = SmallDrain();
  const auto ordinary = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (ordinary.empty() || Has(ordinary, "runtime_counter_output"))
    return Fail("default trace leaked counter-output field");
  drain->runtime_counter_output_requested = true;
  drain->counter_output_count = 2;
  drain->counter_output_pair_complete = true;
  drain->counter_output_hook_calls = 2;
  drain->counter_output_target_calls = 2;
  for (std::size_t index = 0; index < 2; ++index) {
    auto &row = drain->counter_outputs[index];
    row.side_index = static_cast<std::int32_t>(index);
    row.countered_entry_count = 18;
    row.countering_entry_count = 14;
    row.context_raw = 125'000;
    row.readout.class_count = 2;
    row.readout.capacity = 2;
    row.readout.retention_raw[0] = 87'500;
    row.readout.retention_raw[1] = 100'000;
  }
  const auto included = SerializeCombatPhaseEventTraceRingDrainV1(*drain);
  if (!Has(included, "\"runtime_counter_output\"") ||
      !Has(included, "\"hook_calls\":2,\"target_calls\":2,\"first_failure_gate\":0") ||
      !Has(included, "\"retention_raw\":[87500,100000]") ||
      !Has(included, "\"runtime_counter_output_pair_complete\":true")) {
    return Fail("opt-in counter-output wire is incomplete");
  }
  drain->counter_outputs[1].readout.capacity = 1;
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty())
    return Fail("invalid counter-output capacity serialized");
  return true;
}

bool OversizeFailsClosed() {
  auto drain = std::make_unique<CombatPhaseEventTraceRingDrainV1>();
  drain->record_count = 7;
  for (std::uint32_t record_index = 0;
       record_index < drain->record_count; ++record_index) {
    auto &record = drain->records[record_index];
    record.boundary =
        static_cast<CombatPhaseEventTraceBoundaryV1>(record_index);
    record.character_count =
        static_cast<std::uint32_t>(record.characters.size());
    for (std::uint32_t index = 0; index < record.character_count; ++index) {
      record.characters[index].character_id =
          static_cast<std::int32_t>(index + 1);
    }
  }
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("oversize trace did not fail before protocol framing");
  }
  return true;
}

} // namespace

int main() {
  return HappyPath() && OptionalRuntimeWeights() && OptionalJoinWidthWire() &&
         OptionalJoinFullEntryWire() &&
         OptionalCounterOutputWire() &&
         InvalidCountsFailClosed() &&
                 MissingRowMapStaysExplicitlyUnknown() &&
                 OversizeFailsClosed()
             ? 0
             : 1;
}
