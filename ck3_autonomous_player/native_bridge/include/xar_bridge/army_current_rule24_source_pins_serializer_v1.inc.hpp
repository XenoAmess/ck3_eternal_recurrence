#pragma once
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_rule24_source_pins_v1.inc.hpp"
template <class Number, class AppendIds, class JsonString>
inline void AppendArmyCurrentRule24SourcePinsV1(
    std::string &out, const ArmyCurrentRule24SourcePinsV1 &p,
    Number number, AppendIds /*append_ids*/, JsonString string) {
  using daily_assault_roster_admission_json_detail::Writer;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Text("status", p.status); w.Text("unavailable_reason", p.unavailable_reason);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source);
  w.Boolean("pins_captured_ready", p.pins_captured_ready);
  w.Boolean("provider_array_borrowed", p.provider_array_borrowed);
  w.Text("rule_receiver_identity", p.rule_receiver_identity);
  w.Text("rule_vtable_identity", p.rule_vtable_identity);
  w.Integer("condition_mode_raw_u8", p.condition_mode_raw_u8);
  w.Text("expected_scope_function_identity", p.expected_scope_function_identity);
  w.Integer("expected_scope_function_rva", p.expected_scope_function_rva);
  w.Text("scope_mask_function_identity", p.scope_mask_function_identity);
  w.Integer("scope_mask_function_rva", p.scope_mask_function_rva);
  w.Text("rule_evaluator_function_identity", p.rule_evaluator_function_identity);
  w.Integer("rule_evaluator_function_rva", p.rule_evaluator_function_rva);
  w.Boolean("vtable_read_ready", p.vtable_read_ready);
  w.Boolean("mode_read_ready", p.mode_read_ready);
  w.Boolean("expected_scope_pin_read_ready", p.expected_scope_pin_read_ready);
  w.Boolean("scope_mask_pin_read_ready", p.scope_mask_pin_read_ready);
  w.Boolean("rule_evaluator_pin_read_ready", p.rule_evaluator_pin_read_ready);
  w.Integer("pin_requested_bytes_u32", p.pin_requested_bytes_u32);
  w.Integer("pin_captured_bytes_u32", p.pin_captured_bytes_u32);
  w.Integer("native_calls_executed", p.native_calls_executed);
  w.Integer("native_writes_executed", p.native_writes_executed);
  out += '}';
}
}
