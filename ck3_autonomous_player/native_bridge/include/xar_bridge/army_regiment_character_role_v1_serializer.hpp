#pragma once
#include "xar_bridge/army_regiment_character_role_v1.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyRegimentCharacterRoleV1(
    std::string &out, const ArmyRegimentCharacterRoleV1 &row,
    Number number, JsonString json) {
  out += "{\"source\":"; json(out, row.source);
  out += ",\"status\":"; json(out, row.status);
  out += ",\"army_regiment_id\":" + number(row.army_regiment_id);
  out += ",\"native_carmy_id\":" + number(row.native_carmy_id);
  const auto numeric = [&](std::string_view key, const auto &value) {
    out += ','; json(out, key); out += ':';
    out += value.has_value() ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const auto &value) {
    out += ','; json(out, key); out += ':';
    out += value.has_value() ? (*value ? "true" : "false") : "null";
  };
  numeric("arrg_army_id_140", row.arrg_army_id_140);
  numeric("character_raw_id_148", row.character_raw_id_148);
  numeric("resolved_character_id", row.resolved_character_id);
  numeric("character_magic_1c", row.character_magic_1c);
  boolean("resolution_used_fallback", row.resolution_used_fallback);
  boolean("native_character_predicate", row.native_character_predicate);
  boolean("character_extension_present", row.character_extension_present);
  numeric("extension_army_id_f4", row.extension_army_id_f4);
  numeric("extension_arrg_id_f8", row.extension_arrg_id_f8);
  out += ",\"same_ArRg_instance_after\":";
  out += row.same_ArRg_instance_after ? "true" : "false";
  out += ",\"unavailable_reason\":";
  if (row.unavailable_reason.empty()) out += "null";
  else json(out, row.unavailable_reason);
  out += '}';
}
} // namespace xar::game
