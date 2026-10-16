#pragma once
#include "xar_bridge/army_county_predicate_trace_v1.hpp"
#include <string>
namespace xar::game {
template<class Number, class JsonString>
inline void AppendCountyPredicateTraceV1(std::string &out,
    const ArmyCountyPredicateTraceV1 &trace, Number number, JsonString quote) {
  out += "{\"schema_version\":1,\"source\":\"same_preview_native_P_returns_12004\",\"status\":\"";
  out += trace.available ? "available" : "unavailable";
  out += "\",\"unavailable_reason\":";
  if (trace.available) out += "null"; else quote(out, trace.unavailable_reason);
  const auto flag = [&](const char *key, bool value) {
    out += ",\"" + std::string(key) + "\":" + (value ? "true" : "false");
  };
  flag("hook_installed", trace.hook_installed);
  flag("scope_entered", trace.scope_entered);
  flag("same_thread", trace.same_thread);
  flag("order_valid", trace.order_valid);
  flag("native_predicate_returned", trace.native_predicate_returned);
  out += ",\"final_condition_passes\":";
  out += trace.final_condition_passes.has_value()
      ? (*trace.final_condition_passes ? "true" : "false") : "null";
  out += ",\"ignored_foreign_calls\":" + number(trace.ignored_foreign_calls);
  out += ",\"ignored_nested_calls\":" + number(trace.ignored_nested_calls);
  out += ",\"stages\":[";
  bool first = true;
  for (const auto &stage : trace.stages) {
    if (!first) out += ',';
    first = false;
    out += "{\"call_count\":" + number(stage.call_count) + ",\"actual_caller_return_rva\":";
    out += stage.actual_caller_return_rva ? number(*stage.actual_caller_return_rva) : "null";
    out += ",\"argument_identity_matched\":";
    out += stage.argument_identity_matched.has_value()
        ? (*stage.argument_identity_matched ? "true" : "false") : "null";
    out += ",\"returned\":";
    out += stage.returned.has_value() ? (*stage.returned ? "true" : "false") : "null";
    out += '}';
  }
  out += "],\"additional_native_predicate_calls\":0,\"neighbor_Q_observed\":false}";
}
}
