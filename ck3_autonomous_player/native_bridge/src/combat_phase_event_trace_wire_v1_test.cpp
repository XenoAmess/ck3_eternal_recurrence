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
  drain->exact_boundary_sequence = true;
  drain->same_full_generation_combat = true;
  drain->same_native_date = true;
  drain->same_loaded_event_table = true;
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
  constexpr std::array<std::string_view, 12> required{
      "\"schema_version\":1",
      "\"status\":\"captured\"",
      "\"record_count\":7",
      "\"bounded_capture_complete\":true",
      "\"full_mutable_transition_bundle_complete\":false",
      "\"original_trace_ready\":false",
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "paused_next_day_stable_query",
      "\"event_identity_token\":\"process-local-0x242\"",
      "\"character_id\":101",
      "\"stable_key\":\"phase.\\\"hit\\\"\"",
      "\"rank_native_mirror\":2",
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
  return true;
}

bool InvalidCountsFailClosed() {
  const auto drain = SmallDrain();
  drain->records[0].character_count =
      static_cast<std::uint32_t>(drain->records[0].characters.size() + 1);
  if (!SerializeCombatPhaseEventTraceRingDrainV1(*drain).empty()) {
    return Fail("invalid record count did not fail closed");
  }
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
  return HappyPath() && InvalidCountsFailClosed() &&
                 OversizeFailsClosed()
             ? 0
             : 1;
}
