#pragma once
#include "xar_bridge/army_ordered_besieging_refill_inputs_v1.hpp"
#include "xar_bridge/army_ordered_refill_persistent_v1_serializer.hpp"

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyOrderedBesiegingRefillInputsV1(
    std::string &out, const ArmyOrderedBesiegingRefillInputsV1 &r,
    Number number, JsonString text) {
  const auto plain = [&](std::string_view key, auto value) {
    out += ','; text(out, key); out += ':'; out += number(value);
  };
  out += "{\"source\":\"native_ordered_besieging_refill_scope\",\"status\":"; text(out, r.status);
  out += ",\"unavailable_reason\":";
  if (r.unavailable_reason.empty()) out += "null"; else text(out, r.unavailable_reason);
  plain("subject_army_id", r.subject_army_id); plain("subject_carmy_id", r.subject_carmy_id);
  plain("province_id", r.province_id);
  out += ",\"refresh_membership_ready\":"; out += r.refresh_membership_ready ? "true" : "false";
  out += ",\"native_persistent_occurrence_count\":";
  out += r.native_persistent_occurrence_count ? number(*r.native_persistent_occurrence_count) : "null";
  out += ",\"native_army_refresh_occurrence_count\":";
  out += r.native_army_refresh_occurrence_count ? number(*r.native_army_refresh_occurrence_count) : "null";
  out += ",\"target_army_regiment_ids\":["; bool comma = false;
  for (auto id : r.target_army_regiment_ids) { if (comma) out += ','; comma = true; out += number(id); }
  out += "],\"persistent_occurrences\":["; comma = false;
  for (const auto &entry : r.persistent_occurrences) {
    if (comma) out += ','; comma = true;
    out += "{\"stored_index\":" + number(entry.stored_index);
    plain("persistent_regiment_id", entry.persistent_regiment_id); out += '}';
  }
  out += "],\"persistent_regiments\":["; comma = false;
  for (const auto &entry : r.persistent_regiments) {
    if (comma) out += ','; comma = true; AppendArmyOrderedRefillPersistentV1(out, entry, number, text);
  }
  out += "],\"refresh_occurrences\":["; comma = false;
  for (const auto &entry : r.refresh_occurrences) {
    if (comma) out += ','; comma = true;
    out += "{\"manager_stored_index\":" + number(entry.manager_stored_index);
    plain("raw_carmy_id", entry.raw_carmy_id); plain("resolved_carmy_id", entry.resolved_carmy_id);
    out += ",\"army_used_fallback\":"; out += entry.army_used_fallback ? "true" : "false";
    plain("native_regiment_occurrence_count", entry.native_regiment_occurrence_count);
    out += ",\"regiments\":["; bool reg_comma = false;
    for (const auto &regiment : entry.regiments) {
      if (reg_comma) out += ','; reg_comma = true;
      out += "{\"stored_index\":" + number(regiment.stored_index);
      plain("raw_army_regiment_id", regiment.raw_army_regiment_id);
      plain("army_regiment_id", regiment.army_regiment_id); out += '}';
    }
    out += "]}";
  }
  out += "]}";
}
} // namespace xar::game
