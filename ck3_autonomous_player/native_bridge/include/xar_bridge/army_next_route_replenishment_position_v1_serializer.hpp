#pragma once
#include "xar_bridge/army_next_route_replenishment_position_inputs_v1.hpp"

namespace xar::game {
template <class Number, class String>
void AppendArmyNextRouteReplenishmentPositionInputsV1(
    std::string &out, const ArmyNextRouteReplenishmentPositionInputsV1 &v,
    Number number, String string) {
  out += "{\"source\":\"native_current_next_route_replenishment_position_12004\",\"status\":";
  string(out, v.status);
  out += ",\"unavailable_reason\":";
  if (v.unavailable_reason.empty()) out += "null"; else string(out, v.unavailable_reason);
  out += ",\"unit_full_id\":" + number(v.unit_full_id);
  out += ",\"route_read_status\":"; string(out, v.route_read_status);
  auto scalar = [&](const char *name, const auto &value) {
    out += ",\""; out += name; out += "\":";
    if (value) out += number(*value); else out += "null";
  };
  auto boolean = [&](const char *name, const auto &value) {
    out += ",\""; out += name; out += "\":";
    out += value ? (*value ? "true" : "false") : "null";
  };
  scalar("route_source_count", v.route_source_count);
  out += ",\"route_province_ids\":[";
  bool comma = false;
  for (auto id : v.route_province_ids) {
    if (comma) out += ',';
    comma = true; out += number(id);
  }
  out += ']';
  scalar("current_province_id", v.current_province_id);
  scalar("first_target_province_id", v.first_target_province_id);
  scalar("first_target_province_magic_raw", v.first_target_province_magic_raw);
  scalar("owner_requested_full_id", v.owner_requested_full_id);
  scalar("owner_resolved_full_id", v.owner_resolved_full_id);
  boolean("owner_used_fallback", v.owner_used_fallback);
  scalar("holder_requested_full_id", v.holder_requested_full_id);
  scalar("holder_resolved_full_id", v.holder_resolved_full_id);
  boolean("holder_used_fallback", v.holder_used_fallback);
  boolean("native_owner_holder_eligible", v.native_owner_holder_eligible);
  boolean("native_first_target_position_eligible", v.native_first_target_position_eligible);
  out += '}';
}
} // namespace xar::game
