#include "xar_bridge/combat_phase_event_trace_wire_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
    if (output.size() > kCombatPhaseEventTraceWireMaximumBytesV1) {
      return false;
    }
  }
  output.push_back('"');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendOpaqueToken(std::string &output, std::uintptr_t value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += "\"process-local-0x";
  bool emitted = false;
  for (int shift = static_cast<int>(sizeof(value) * 8U) - 4;
       shift >= 0; shift -= 4) {
    const auto nibble =
        static_cast<unsigned>((value >> shift) & 0x0FU);
    if (nibble != 0 || emitted || shift == 0) {
      output.push_back(hex[nibble]);
      emitted = true;
    }
  }
  output.push_back('"');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendArmyRows(std::string &output,
                    const CombatPhaseEventTraceSideRecordV1 &side) {
  output += '[';
  for (std::uint32_t index = 0; index < side.army_count; ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    const auto &row = side.armies[index];
    output += "{\"army_id\":";
    if (!AppendNumber(output, row.army_id)) return false;
    output += ",\"commander_character_id\":";
    if (!AppendNumber(output, row.commander_character_id)) return false;
    output += ",\"combat_id\":";
    if (!AppendNumber(output, row.combat_id)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendKnightRows(std::string &output,
                      const CombatPhaseEventTraceSideRecordV1 &side) {
  output += '[';
  for (std::uint32_t index = 0; index < side.knight_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = side.knights[index];
    output += "{\"regiment_id\":";
    if (!AppendNumber(output, row.regiment_id)) return false;
    output += ",\"army_id\":";
    if (!AppendNumber(output, row.army_id)) return false;
    output += ",\"character_id\":";
    if (!AppendNumber(output, row.character_id)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendScheduleRows(std::string &output,
                        const CombatPhaseEventTraceSideRecordV1 &side) {
  output += '[';
  for (std::uint32_t index = 0; index < side.scheduled_knight_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = side.scheduled_knights[index];
    output += "{\"event_identity_token\":";
    if (!AppendOpaqueToken(output, row.event_identity)) return false;
    output += ",\"regiment_id\":";
    if (!AppendNumber(output, row.regiment_id)) return false;
    output += ",\"current_character_id\":";
    if (!AppendNumber(output, row.current_character_id)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendSide(std::string &output,
                const CombatPhaseEventTraceSideRecordV1 &side) {
  output += "{\"side_index\":";
  if (!AppendNumber(output, side.side_index)) return false;
  output += ",\"selected_commander_character_id\":";
  if (!AppendNumber(output, side.selected_commander_character_id)) return false;
  output += ",\"current_fighting_total_raw\":";
  if (!AppendNumber(output, side.current_fighting_total_raw)) return false;
  output += ",\"first_fighting_subtotal_raw\":";
  if (!AppendNumber(output, side.first_fighting_subtotal_raw)) return false;
  output += ",\"scheduled_commander_event_identity_token\":";
  if (!AppendOpaqueToken(output, side.scheduled_commander_event_identity)) {
    return false;
  }
  output += ",\"armies\":";
  if (!AppendArmyRows(output, side)) return false;
  output += ",\"knights\":";
  if (!AppendKnightRows(output, side)) return false;
  output += ",\"scheduled_knights\":";
  if (!AppendScheduleRows(output, side)) return false;
  output.push_back('}');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendCharacters(std::string &output,
                      const CombatPhaseEventTraceRingRecordV1 &record) {
  output += '[';
  for (std::uint32_t index = 0; index < record.character_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = record.characters[index];
    output += "{\"character_id\":";
    if (!AppendNumber(output, row.character_id)) return false;
    output += ",\"death_marker_present\":";
    if (!AppendBool(output, row.death_marker_present)) return false;
    output += ",\"martial\":";
    if (!AppendNumber(output, row.martial)) return false;
    output += ",\"learning\":";
    if (!AppendNumber(output, row.learning)) return false;
    output += ",\"prowess\":";
    if (!AppendNumber(output, row.prowess)) return false;
    output += ",\"current_regiment_id\":";
    if (!AppendNumber(output, row.current_regiment_id)) return false;
    output += ",\"current_regiment_back_reference_matches\":";
    if (!AppendBool(output,
                    row.current_regiment_back_reference_matches)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendBattleEvents(std::string &output,
                        const CombatPhaseEventTraceRingRecordV1 &record) {
  output += '[';
  for (std::uint32_t index = 0; index < record.battle_event_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = record.battle_events[index];
    output += "{\"left_character_id\":";
    if (!AppendNumber(output, row.left_character_id)) return false;
    output += ",\"right_character_id\":";
    if (!AppendNumber(output, row.right_character_id)) return false;
    output += ",\"stable_key\":";
    if (!AppendString(output,
                      std::string_view(row.stable_key.data(),
                                       row.stable_key_size))) return false;
    output += ",\"type_raw\":";
    if (!AppendNumber(output, row.type_raw)) return false;
    output += ",\"side_index\":";
    if (!AppendNumber(output, row.side_index)) return false;
    output += ",\"target_right\":";
    if (!AppendBool(output, row.target_right)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool AppendAccolades(std::string &output,
                     const CombatPhaseEventTraceRingRecordV1 &record) {
  output += '[';
  for (std::uint32_t index = 0; index < record.accolade_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = record.accolades[index];
    output += "{\"accolade_id\":";
    if (!AppendNumber(output, row.accolade_id)) return false;
    output += ",\"owner_character_id\":";
    if (!AppendNumber(output, row.owner_character_id)) return false;
    output += ",\"acclaimed_knight_character_id\":";
    if (!AppendNumber(output, row.acclaimed_knight_character_id)) return false;
    output += ",\"glory_raw\":";
    if (!AppendNumber(output, row.glory_raw)) return false;
    output += ",\"rank_native_mirror\":";
    if (!AppendNumber(output, row.rank_native_mirror)) return false;
    output += ",\"participant_link_identity_matches\":";
    if (!AppendBool(output, row.participant_link_identity_matches)) return false;
    output.push_back('}');
  }
  output.push_back(']');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

bool CountsValid(const CombatPhaseEventTraceRingRecordV1 &record) {
  if (record.character_count > record.characters.size() ||
      record.battle_event_count > record.battle_events.size() ||
      record.accolade_count > record.accolades.size()) {
    return false;
  }
  for (const auto &side : record.sides) {
    if (side.army_count > side.armies.size() ||
        side.knight_count > side.knights.size() ||
        side.scheduled_knight_count > side.scheduled_knights.size()) {
      return false;
    }
  }
  return true;
}

bool AppendRecord(std::string &output,
                  const CombatPhaseEventTraceRingRecordV1 &record) {
  if (!CountsValid(record)) return false;
  const auto boundary_index = static_cast<std::size_t>(record.boundary);
  if (boundary_index >= kCombatPhaseEventTraceBoundaryNamesV1.size()) {
    return false;
  }
  output += "{\"boundary\":";
  if (!AppendString(output,
                    kCombatPhaseEventTraceBoundaryNamesV1[boundary_index])) {
    return false;
  }
  output += ",\"capture_failure_flags\":";
  if (!AppendNumber(output, record.capture_failure_flags)) return false;
  output += ",\"managed_daily_sequence_token\":";
  if (!AppendNumber(output, record.managed_daily_sequence_token)) return false;
  output += ",\"combat_id\":";
  if (!AppendNumber(output, record.combat_id)) return false;
  output += ",\"native_date_raw\":";
  if (!AppendNumber(output, record.native_date_raw)) return false;
  output += ",\"phase_raw\":";
  if (!AppendNumber(output, record.phase_raw)) return false;
  output += ",\"phase_day\":";
  if (!AppendNumber(output, record.phase_day)) return false;
  output += ",\"winner_side_raw\":";
  if (!AppendNumber(output, record.winner_side_raw)) return false;
  output += ",\"battle_result_id\":";
  if (!AppendNumber(output, record.battle_result_id)) return false;
  output += ",\"base_advantage_raw\":";
  if (!AppendNumber(output, record.base_advantage_raw)) return false;
  output += ",\"resolved_advantage_raw\":";
  if (!AppendNumber(output, record.resolved_advantage_raw)) return false;
  output += ",\"advantage_rolls_raw\":[";
  if (!AppendNumber(output, record.advantage_rolls_raw[0])) return false;
  output.push_back(',');
  if (!AppendNumber(output, record.advantage_rolls_raw[1])) return false;
  output += "],\"schedule_local_rng\":{";
  output += "\"present\":";
  if (!AppendBool(output, record.schedule_local_rng_present)) return false;
  output += ",\"word0\":";
  if (!AppendNumber(output, record.schedule_local_rng_word0)) return false;
  output += ",\"word1\":";
  if (!AppendNumber(output, record.schedule_local_rng_word1)) return false;
  output += "},\"global_rng\":{\"counter\":";
  if (!AppendNumber(output, record.global_rng_counter)) return false;
  output += ",\"salt\":";
  if (!AppendNumber(output, record.global_rng_salt)) return false;
  output += ",\"owner_thread_token\":";
  if (!AppendNumber(output, record.global_rng_owner_thread_token)) return false;
  output += "},\"sides\":[";
  if (!AppendSide(output, record.sides[0])) return false;
  output.push_back(',');
  if (!AppendSide(output, record.sides[1])) return false;
  output += "],\"characters\":";
  if (!AppendCharacters(output, record)) return false;
  output += ",\"battle_events\":";
  if (!AppendBattleEvents(output, record)) return false;
  output += ",\"accolades\":";
  if (!AppendAccolades(output, record)) return false;
  output += ",\"full_mutable_transition_bundle_complete\":";
  if (!AppendBool(output,
                  record.full_mutable_transition_bundle_complete)) return false;
  output.push_back('}');
  return output.size() <= kCombatPhaseEventTraceWireMaximumBytesV1;
}

} // namespace

std::string SerializeCombatPhaseEventTraceRingDrainV1(
    const CombatPhaseEventTraceRingDrainV1 &drain) {
  if (drain.record_count > drain.records.size()) {
    return {};
  }
  std::string output;
  output.reserve(64U * 1024U);
  output += "{\"schema_version\":1,\"status\":\"";
  output += drain.bounded_capture_complete ? "captured" : "failed";
  output += "\",\"failure_flags\":";
  if (!AppendNumber(output, drain.failure_flags)) return {};
  output += ",\"record_count\":";
  if (!AppendNumber(output, drain.record_count)) return {};
  output += ",\"readiness\":{";
  output += "\"exact_boundary_sequence\":";
  if (!AppendBool(output, drain.exact_boundary_sequence)) return {};
  output += ",\"same_full_generation_combat\":";
  if (!AppendBool(output, drain.same_full_generation_combat)) return {};
  output += ",\"same_native_date\":";
  if (!AppendBool(output, drain.same_native_date)) return {};
  output += ",\"same_loaded_event_table\":";
  if (!AppendBool(output, drain.same_loaded_event_table)) return {};
  output += ",\"side_and_return_site_identity\":";
  if (!AppendBool(output, drain.side_and_return_site_identity)) return {};
  output += ",\"schedule_phase_day_then_single_increment\":";
  if (!AppendBool(output,
                  drain.schedule_phase_day_then_single_increment)) return {};
  output += ",\"bounded_capture_complete\":";
  if (!AppendBool(output, drain.bounded_capture_complete)) return {};
  output += ",\"full_mutable_transition_bundle_complete\":";
  if (!AppendBool(output,
                  drain.full_mutable_transition_bundle_complete)) return {};
  output += ",\"original_trace_ready\":";
  if (!AppendBool(output, drain.production_trace_ready)) return {};
  output += "},\"records\":[";
  for (std::uint32_t index = 0; index < drain.record_count; ++index) {
    if (index != 0) output.push_back(',');
    if (!AppendRecord(output, drain.records[index])) return {};
  }
  output += "]}";
  if (output.size() > kCombatPhaseEventTraceWireMaximumBytesV1) {
    return {};
  }
  return output;
}

} // namespace xar::ck3_11906
