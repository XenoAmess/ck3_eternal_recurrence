#include "xar_bridge/knight_stat_consumption_12004.hpp"

#include <ostream>
#include <sstream>
#include <string_view>

namespace xar::ck3_12004 {
namespace {

void String(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 15];
    else out << static_cast<char>(c);
  }
  out << '"';
}

void Reason(std::ostream &out, std::string_view value) {
  if (value.empty()) out << "null";
  else String(out, value);
}

template <typename Value>
void Number(std::ostream &out, const std::optional<Value> &value) {
  if (value) out << +*value;
  else out << "null";
}

template <typename Value>
void Raw64(std::ostream &out, Value value) { out << '"' << value << '"'; }
template <typename Value>
void Raw64(std::ostream &out, const std::optional<Value> &value) {
  if (value) Raw64(out, *value);
  else out << "null";
}

void Pointer(std::ostream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}
void Pointer(std::ostream &out, const std::optional<std::uintptr_t> &value) {
  if (value) Pointer(out, *value);
  else out << "null";
}

void Boolean(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}

void Pc(std::ostream &out, const PersonFollowing2922680Pc &pc) {
  out << "{\"ready\":" << (pc.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, pc.reason);
  out << ",\"admitted\":"; Boolean(out, pc.admitted);
  out << ",\"identity\":"; Pointer(out, pc.identity);
  out << ",\"count_i32\":"; Number(out, pc.count_i32);
  out << ",\"weight_q100000\":"; Raw64(out, pc.weight_q100000);
  out << ",\"properties\":";
  if (!pc.properties) out << "null";
  else {
    out << "{\"keys_u16\":";
    if (!pc.properties->keys_u16) out << "null";
    else {
      out << '[';
      for (std::size_t index = 0; index < pc.properties->keys_u16->size(); ++index) {
        if (index != 0) out << ',';
        out << (*pc.properties->keys_u16)[index];
      }
      out << ']';
    }
    out << ",\"values_q64\":";
    if (!pc.properties->values_q64) out << "null";
    else {
      out << '[';
      for (std::size_t index = 0; index < pc.properties->values_q64->size(); ++index) {
        if (index != 0) out << ',';
        Raw64(out, (*pc.properties->values_q64)[index]);
      }
      out << ']';
    }
    out << '}';
  }
  out << '}';
}

void Context(std::ostream &out, const KnightConsumedContext12004 &context) {
  out << "{\"property_key\":" << context.property_key << ",\"caller_return_rva\":";
  Raw64(out, context.caller_return_rva);
  out << ",\"selected_character_id\":"; Number(out, context.selected_character_id);
  out << ",\"selected_character_identity\":"; Pointer(out, context.selected_character_identity);
  out << ",\"context_identity\":"; Pointer(out, context.context_identity);
  out << ",\"operand_raw\":"; Raw64(out, context.operand_raw);
  out << ",\"consumed_pc\":"; Pc(out, context.consumed_pc);
  out << ",\"preparation_capture_sequence\":"; Raw64(out, context.preparation_capture_sequence);
  out << ",\"preparation_model_identity\":"; Pointer(out, context.preparation_model_identity);
  out << ",\"preparation_context_identity\":"; Pointer(out, context.preparation_context_identity);
  out << ",\"preparation_owner_character_id\":"; Number(out, context.preparation_owner_character_id);
  out << ",\"context_matches_preparation\":"; Boolean(out, context.context_matches_preparation);
  out << ",\"owner_matches_preparation\":"; Boolean(out, context.owner_matches_preparation);
  out << ",\"pc_matches_preparation_post\":"; Boolean(out, context.pc_matches_preparation_post);
  out << ",\"reason\":"; Reason(out, context.reason);
  out << '}';
}

void Output(std::ostream &out, const KnightConsumedOutput12004 &output) {
  out << "{\"ready\":" << (output.ready ? "true" : "false") << ",\"max_size\":";
  Number(out, output.max_size);
  out << ",\"siege_value_raw\":"; Raw64(out, output.siege_value_raw);
  out << ",\"damage_raw\":"; Raw64(out, output.damage_raw);
  out << ",\"toughness_raw\":"; Raw64(out, output.toughness_raw);
  out << ",\"pursuit_raw\":"; Raw64(out, output.pursuit_raw);
  out << ",\"screen_raw\":"; Raw64(out, output.screen_raw);
  out << ",\"reason\":"; Reason(out, output.reason);
  out << '}';
}

void Event(std::ostream &out, const KnightStatConsumptionEvent12004 &event) {
  out << "{\"sequence\":"; Raw64(out, event.sequence);
  out << ",\"thread_id\":" << event.thread_id << ",\"observed_date_raw\":";
  Number(out, event.observed_date_raw);
  out << ",\"wrapper_caller_return_rva\":"; Raw64(out, event.wrapper_caller_return_rva);
  out << ",\"origin\":"; String(out, event.origin);
  out << ",\"regiment_id\":"; Number(out, event.regiment_id);
  out << ",\"target_province_id\":"; Number(out, event.target_province_id);
  out << ",\"linked_character_id\":"; Number(out, event.linked_character_id);
  out << ",\"linked_character_identity\":"; Pointer(out, event.linked_character_identity);
  out << ",\"linked_prowess_points\":"; Number(out, event.linked_prowess_points);
  out << ",\"loaded_damage_multiplier\":"; Number(out, event.loaded_damage_multiplier);
  out << ",\"loaded_toughness_multiplier\":"; Number(out, event.loaded_toughness_multiplier);
  out << ",\"output_cache_identity\":"; Pointer(out, event.output_cache_identity);
  out << ",\"native_return_identity\":"; Pointer(out, event.native_return_identity);
  out << ",\"contexts\":[";
  for (std::size_t index = 0; index < event.contexts.size(); ++index) {
    if (index != 0) out << ',';
    Context(out, event.contexts[index]);
  }
  out << "],\"observed_output\":"; Output(out, event.observed_output);
  out << ",\"entry_association_proven\":" << (event.entry_association_proven ? "true" : "false");
  out << ",\"capture_reason\":"; Reason(out, event.capture_reason);
  out << '}';
}

} // namespace

std::string SerializeKnightStatConsumptionQuery12004(
    const KnightStatConsumptionQuery12004 &query) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kKnightStatConsumptionSchema12004);
  out << ",\"build_version\":"; String(out, query.build_version);
  out << ",\"executable_sha256\":"; String(out, query.executable_sha256);
  out << ",\"configured\":" << (query.configured ? "true" : "false");
  out << ",\"observer_installed\":" << (query.observer_installed ? "true" : "false");
  out << ",\"oldest_available_sequence\":"; Raw64(out, query.oldest_available_sequence);
  out << ",\"latest_sequence\":"; Raw64(out, query.latest_sequence);
  out << ",\"overwritten_events\":"; Raw64(out, query.overwritten_events);
  out << ",\"events\":[";
  for (std::size_t index = 0; index < query.events.size(); ++index) {
    if (index != 0) out << ',';
    Event(out, query.events[index]);
  }
  out << "],\"reason\":"; Reason(out, query.reason);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12004
