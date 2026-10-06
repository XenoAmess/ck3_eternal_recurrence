#pragma once
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"
#include <string_view>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyScopedOrderedRefillInputsV1(
    std::string &out, const ArmyScopedOrderedRefillInputsV1 &r,
    Number number, JsonString text) {
  const auto reason = [&](std::string_view key, const std::string &value) {
    out += ','; text(out, key); out += ':';
    if (value.empty()) out += "null"; else text(out, value);
  };
  const auto plain = [&](std::string_view key, auto value) {
    out += ','; text(out, key); out += ':'; out += number(value);
  };
  const auto numeric = [&](std::string_view key, const auto &value) {
    out += ','; text(out, key); out += ':'; out += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    out += ','; text(out, key); out += ':'; out += value ? (*value ? "true" : "false") : "null";
  };
  out += "{\"source\":\"native_scoped_observed_prepared_ordered_refill\",\"status\":"; text(out, r.status);
  reason("unavailable_reason", r.unavailable_reason);
  plain("subject_army_id", r.subject_army_id); plain("subject_carmy_id", r.subject_carmy_id);
  numeric("native_persistent_occurrence_count", r.native_persistent_occurrence_count);
  numeric("native_army_refresh_occurrence_count", r.native_army_refresh_occurrence_count);
  out += ",\"persistent_occurrences\":[";
  bool comma = false;
  for (const auto &entry : r.persistent_occurrences) {
    if (comma) out += ','; comma = true;
    out += "{\"stored_index\":" + number(entry.stored_index);
    plain("persistent_regiment_id", entry.persistent_regiment_id); out += '}';
  }
  out += "],\"army_refresh_occurrence_indices\":["; comma = false;
  for (auto index : r.army_refresh_occurrence_indices) {
    if (comma) out += ','; comma = true; out += number(index);
  }
  out += "],\"persistent_regiments\":["; comma = false;
  for (const auto &persistent : r.persistent_regiments) {
    if (comma) out += ','; comma = true;
    out += "{\"persistent_regiment_id\":" + number(persistent.persistent_regiment_id);
    numeric("prepared_fraction_raw", persistent.prepared_fraction_raw);
    reason("unavailable_reason", persistent.unavailable_reason);
    out += ",\"chunks\":["; bool chunk_comma = false;
    for (const auto &chunk : persistent.chunks) {
      if (chunk_comma) out += ','; chunk_comma = true;
      out += "{\"physical_index\":" + number(chunk.physical_index);
#define XAR_ORDERED_PLAIN(field) plain(#field, chunk.field)
      XAR_ORDERED_PLAIN(current_soldiers); XAR_ORDERED_PLAIN(maximum_soldiers);
      XAR_ORDERED_PLAIN(owner_persistent_regiment_id); XAR_ORDERED_PLAIN(q_ordinal_raw);
      XAR_ORDERED_PLAIN(army_regiment_id_raw); XAR_ORDERED_PLAIN(exclusion_byte_14_raw); XAR_ORDERED_PLAIN(state_raw);
#undef XAR_ORDERED_PLAIN
      reason("context_unavailable_reason", chunk.context_unavailable_reason);
#define XAR_ORDERED_NUMBER(field) numeric(#field, chunk.field)
      XAR_ORDERED_NUMBER(owner_resolved_full_id); XAR_ORDERED_NUMBER(owner_guard_138_raw);
      XAR_ORDERED_NUMBER(owner_definition_magic_38_raw); XAR_ORDERED_NUMBER(origin_province_id);
      XAR_ORDERED_NUMBER(origin_province_788_raw); XAR_ORDERED_NUMBER(origin_province_73c_raw);
      XAR_ORDERED_NUMBER(associated_arrg_resolved_full_id); XAR_ORDERED_NUMBER(associated_arrg_magic_raw);
      XAR_ORDERED_NUMBER(associated_army_raw_full_id); XAR_ORDERED_NUMBER(associated_army_resolved_full_id);
      XAR_ORDERED_NUMBER(army_byte_1d4_raw); XAR_ORDERED_NUMBER(army_byte_1ec_raw);
      XAR_ORDERED_NUMBER(associated_unit_raw_full_id); XAR_ORDERED_NUMBER(associated_unit_resolved_full_id);
      XAR_ORDERED_NUMBER(unit_170_raw); XAR_ORDERED_NUMBER(unit_position_province_magic_raw);
      XAR_ORDERED_NUMBER(unit_position_owner_resolved_full_id); XAR_ORDERED_NUMBER(unit_position_holder_resolved_full_id);
#undef XAR_ORDERED_NUMBER
      boolean("native_army_in_combat", chunk.native_army_in_combat);
      boolean("native_unit_position_eligible", chunk.native_unit_position_eligible); out += '}';
    }
    out += "]}";
  }
  out += "]}";
}
} // namespace xar::game
