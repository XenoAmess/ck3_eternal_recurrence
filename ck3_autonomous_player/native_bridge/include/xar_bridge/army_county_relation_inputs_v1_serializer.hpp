#pragma once
#include "xar_bridge/army_county_relation_inputs_v1.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendCountyRelationInputsV1(std::string &out,
    const ArmyCountyRelationInputsV1 &value, Number number, JsonString quote) {
  out += "{\"schema_version\":1,\"source\":\"native_original_relation_entry_return_12004\",\"status\":\"";
  out += value.available ? "available" : "unavailable";
  out += "\",\"unavailable_reason\":";
  if (value.available) out += "null"; else quote(out, value.unavailable_reason);
  const auto key = [&](const char *name) { out += ",\"" + std::string(name) + "\":"; };
  const auto flag = [&](const char *name, bool field) {
    key(name); out += field ? "true" : "false";
  };
  const auto optional_bool = [&](const char *name, const auto &field) {
    key(name); out += field.has_value() ? (*field ? "true" : "false") : "null";
  };
  const auto optional_number = [&](const char *name, const auto &field) {
    key(name); out += field.has_value() ? number(*field) : "null";
  };
  const auto identity = [&](const char *name, const auto &field) {
    key(name);
    if (field.has_value() && *field != 0) quote(out, "native:" + number(*field));
    else out += "null";
  };
  key("call_count"); out += number(value.call_count);
  optional_number("actual_bridge_caller_return_rva", value.actual_bridge_caller_return_rva);
  flag("argument_identity_matched", value.argument_identity_matched);
  flag("same_thread", value.same_thread);
  optional_bool("identity_before_after_match", value.identity_before_after_match);
  optional_number("receiver_full_id", value.receiver_full_id);
  optional_number("actor_full_id", value.actor_full_id);
  identity("auxiliary_identity", value.auxiliary_identity);
  optional_bool("returned", value.returned);
  flag("sampled_relation_available", value.sampled_relation_available);
  key("sampled_relation_unavailable_reason");
  if (value.sampled_relation_available) out += "null";
  else quote(out, value.sampled_relation_unavailable_reason);
  identity("sampled_relation_identity", value.sampled_relation_identity);
  optional_number("sampled_relation_full_war_id", value.sampled_relation_full_war_id);
  identity("sampled_selected_war_identity", value.sampled_selected_war_identity);
  optional_bool("sampled_selected_war_used_fallback", value.sampled_selected_war_used_fallback);
  optional_number("sampled_selected_war_byte_358_u8", value.sampled_selected_war_byte_358_u8);
  optional_bool("sampled_direct_war_matches_aux", value.sampled_direct_war_matches_aux);
  optional_bool("sampled_direct_war_gate", value.sampled_direct_war_gate);
  flag("unknown_or_inputs", value.unknown_or_inputs);
  out += '}';
}
} // namespace xar::game
