#pragma once

#include "battle_reinforcement_arrival_admission_12003.hpp"

namespace xar::game {
namespace arrival_admission_serializer_12003_detail {

inline void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20U) {
      out += "\\u00"; out += hex[(c >> 4U) & 0xFU]; out += hex[c & 0xFU];
    } else out += static_cast<char>(c);
  }
  out += '"';
}

inline void OptionalId(std::string &out, const std::optional<std::int32_t> &value) {
  out += value ? std::to_string(*value) : "null";
}

inline void Ids(std::string &out, const std::vector<std::int32_t> &values) {
  out += '[';
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (i != 0) out += ',';
    out += std::to_string(values[i]);
  }
  out += ']';
}

inline std::string_view Status(ArrivalAdmission12003Status value) noexcept {
  switch (value) {
  case ArrivalAdmission12003Status::available: return "available";
  case ArrivalAdmission12003Status::not_applicable: return "not_applicable";
  case ArrivalAdmission12003Status::requires_paused: return "requires_paused";
  case ArrivalAdmission12003Status::subject_cunit_not_found: return "subject_cunit_not_found";
  case ArrivalAdmission12003Status::target_province_not_found: return "target_province_not_found";
  case ArrivalAdmission12003Status::state_changed: return "state_changed";
  case ArrivalAdmission12003Status::unavailable: return "unavailable";
  }
  return "unavailable";
}

} // namespace arrival_admission_serializer_12003_detail

inline std::string SerializeBattleReinforcementArrivalAdmission12003(
    const BattleReinforcementArrivalAdmission12003Snapshot &s) {
  using namespace arrival_admission_serializer_12003_detail;
  std::string out = "{\"schema\":";
  String(out, s.schema);
  out += ",\"schema_version\":" + std::to_string(s.schema_version) + ",\"status\":";
  String(out, Status(s.status));
  out += ",\"unavailable_reason\":";
  if (s.unavailable_reason.empty()) out += "null";
  else String(out, s.unavailable_reason);
  out += ",\"snapshot_revision\":" + std::to_string(s.snapshot_revision) +
         ",\"observed_date_raw\":" + std::to_string(s.observed_date_raw) +
         ",\"subject\":{\"public_cunit_id\":" + std::to_string(s.subject.public_cunit_id) +
         ",\"native_carmy_id\":";
  OptionalId(out, s.subject.native_carmy_id);
  out += ",\"owner_character_id\":";
  OptionalId(out, s.subject.owner_character_id);
  out += ",\"current_province_id\":";
  OptionalId(out, s.subject.current_province_id);
  out += ",\"active_combat_id\":";
  OptionalId(out, s.subject.active_combat_id);
  out += "},\"target\":{\"province_id\":";
  OptionalId(out, s.target.province_id);
  out += ",\"provenance\":";
  String(out, s.target.provenance);
  out += "},\"eligibility_now\":";
  String(out, s.eligibility_now);
  out += ",\"raw_gates\":";
  if (!s.raw_gates) out += "null";
  else {
    const auto &g = *s.raw_gates;
    out += "{\"province_contact_gate_enabled\":";
    out += g.province_contact_gate_enabled ? "true" : "false";
    out += ",\"contact_game_mode_allows_contact\":";
    out += g.contact_game_mode_allows_contact ? "true" : "false";
    out += ",\"unit_contact_state_raw\":" + std::to_string(g.unit_contact_state_raw) +
           ",\"unit_retreat_state_raw\":" + std::to_string(g.unit_retreat_state_raw) +
           ",\"army_empty_for_contact\":";
    out += g.army_empty_for_contact ? "true" : "false";
    out += '}';
  }
  out += ",\"current_target_combat_ids_in_stored_order\":";
  Ids(out, s.current_target_combat_ids_in_stored_order);
  out += ",\"current_target_compatible_combat_ids_in_stored_order\":";
  Ids(out, s.current_target_compatible_combat_ids_in_stored_order);
  out += ",\"contact_if_now_selected_combat_id\":";
  OptionalId(out, s.contact_if_now_selected_combat_id);
  out += ",\"selected_combat_stored_index\":";
  OptionalId(out, s.selected_combat_stored_index);
  out += ",\"join_side\":";
  String(out, s.join_side);
  out += ",\"current_attacker_public_cunit_ids_in_stored_order\":";
  Ids(out, s.current_attacker_public_cunit_ids_in_stored_order);
  out += ",\"current_defender_public_cunit_ids_in_stored_order\":";
  Ids(out, s.current_defender_public_cunit_ids_in_stored_order);
  out += ",\"subject_current_participation_verified\":";
  out += s.subject_current_participation_verified ? "true" : "false";
  out += ",\"temporal_semantics\":";
  String(out, s.temporal_semantics);
  out += ",\"future_binding\":";
  out += s.future_binding ? "true}" : "false}";
  return out;
}

} // namespace xar::game
