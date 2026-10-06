#pragma once
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"
#include "xar_bridge/army_ordered_refill_persistent_v1_serializer.hpp"
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
    AppendArmyOrderedRefillPersistentV1(out, persistent, number, text);
  }
  out += "]}";
}
} // namespace xar::game
