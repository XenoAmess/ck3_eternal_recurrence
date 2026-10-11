#include "xar_bridge/person_callback_entry_inputs_12004.hpp"

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
PersonSixStageCapture12004DTO ReadHistory(
    void *, std::uintptr_t selected, std::uint32_t full_id) noexcept {
  return ReadPersonSixStageCaptureForCharacter12004(selected, full_id);
}
void JsonString(std::ostream &out, std::string_view text) {
  out << '"';
  for (const char raw : text) {
    const auto value = static_cast<unsigned char>(raw);
    switch (value) {
    case '"': out << "\\\""; break;
    case '\\': out << "\\\\"; break;
    case '\n': out << "\\n"; break;
    case '\r': out << "\\r"; break;
    case '\t': out << "\\t"; break;
    default:
      if (value < 0x20)
        out << "\\u00" << std::hex << std::setw(2) << std::setfill('0')
            << static_cast<unsigned int>(value) << std::dec << std::setfill(' ');
      else out << raw;
    }
  }
  out << '"';
}
void Pointer(std::ostream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}
void Boolean(std::ostream &out, std::optional<bool> value) {
  if (!value) out << "null";
  else out << (*value ? "true" : "false");
}
} // namespace

PersonCallbackEntryInputsBindings12004 BindPersonCallbackEntryInputs12004(
    std::string_view executable_sha256) noexcept {
  if (executable_sha256 != kPersonCallbackEntryInputsExeSha12004) return {};
  return {true, nullptr, ReadHistory};
}

PersonCallbackEntryInputs12004 CapturePersonCallbackEntryInputs12004(
    const PersonCallbackEntryInputsBindings12004 &bindings,
    std::uintptr_t selected_character_identity,
    std::uint32_t selected_character_id,
    std::uintptr_t actual_getter_caller_return_rva,
    const PersonInstalledTransferEvent12004 &existing_begin_event) noexcept {
  PersonCallbackEntryInputs12004 out;
  out.selected_character_identity = selected_character_identity;
  out.selected_character_id = selected_character_id;
  out.getter_caller_return_rva = actual_getter_caller_return_rva;
  out.getter_begin_event = existing_begin_event;
  out.exact_image_bound = bindings.exact_image_bound;
  out.getter_site_observed = std::find(
      kPersonCallbackEntryGetterReturns12004.begin(),
      kPersonCallbackEntryGetterReturns12004.end(),
      actual_getter_caller_return_rva) !=
      kPersonCallbackEntryGetterReturns12004.end();
  out.entry_event_observed = existing_begin_event.clock_identity != 0 &&
      existing_begin_event.sequence != 0 && existing_begin_event.thread_id &&
      *existing_begin_event.thread_id != 0;
  if (!bindings.exact_image_bound || !bindings.read_history) {
    out.reason = "getter_entry_history_binding_unavailable";
    return out;
  }
  if (!out.getter_site_observed) {
    out.reason = "getter_entry_site_unobserved";
    return out;
  }
  if (selected_character_identity == 0) {
    out.reason = "getter_entry_selected_character_null";
    return out;
  }
  try {
    auto capture = bindings.read_history(bindings.history_context,
        selected_character_identity, selected_character_id);
    if (capture.character_identity && capture.character_id)
      out.capture_identity_matches_selected =
          *capture.character_identity == selected_character_identity &&
          *capture.character_id == selected_character_id;
    if (capture.capture_thread_id && existing_begin_event.thread_id)
      out.capture_thread_matches_entry =
          *capture.capture_thread_id == *existing_begin_event.thread_id;
    if (capture.capture_complete && capture.query_thread_id &&
        existing_begin_event.thread_id)
      out.completion_thread_matches_entry =
          *capture.query_thread_id == *existing_begin_event.thread_id;
    if (capture.preparation_model.owner_character_identity &&
        capture.preparation_model.owner_character_id)
      out.preparation_owner_matches_selected =
          *capture.preparation_model.owner_character_identity ==
              selected_character_identity &&
          *capture.preparation_model.owner_character_id == selected_character_id;
    out.reason = !capture.capture_observed
        ? "preparation_unobserved_at_getter_entry"
        : capture.capture_complete
            ? "owned_preparation_at_getter_entry"
            : "owned_partial_preparation_at_getter_entry";
    out.preparation_at_entry.emplace(std::move(capture));
  } catch (...) {
    out.reason = "getter_entry_owned_history_copy_failed";
  }
  return out;
}

std::string SerializePersonCallbackEntryInputs12004(
    const PersonCallbackEntryInputs12004 &inputs) {
  std::ostringstream out;
  out << "{\"schema\":\"xar.ck3.person-callback-entry-inputs-12004-v1\""
      << ",\"source_stage\":\"before_original_ci_getter\""
      << ",\"selected_character_identity\":";
  Pointer(out, inputs.selected_character_identity);
  out << ",\"selected_character_id\":" << inputs.selected_character_id
      << ",\"getter_caller_return_rva\":";
  Pointer(out, inputs.getter_caller_return_rva);
  out << ",\"getter_begin_event\":{\"clock_identity\":";
  Pointer(out, inputs.getter_begin_event.clock_identity);
  out << ",\"sequence\":" << inputs.getter_begin_event.sequence
      << ",\"thread_id\":";
  if (inputs.getter_begin_event.thread_id)
    out << *inputs.getter_begin_event.thread_id;
  else out << "null";
  out << "},\"exact_image_bound\":"
      << (inputs.exact_image_bound ? "true" : "false")
      << ",\"getter_site_observed\":"
      << (inputs.getter_site_observed ? "true" : "false")
      << ",\"entry_event_observed\":"
      << (inputs.entry_event_observed ? "true" : "false")
      << ",\"preparation_at_entry\":";
  if (inputs.preparation_at_entry)
    out << SerializePersonSixStageCapture12004(*inputs.preparation_at_entry);
  else out << "null";
  out << ",\"capture_identity_matches_selected\":";
  Boolean(out, inputs.capture_identity_matches_selected);
  out << ",\"capture_thread_matches_entry\":";
  Boolean(out, inputs.capture_thread_matches_entry);
  out << ",\"completion_thread_matches_entry\":";
  Boolean(out, inputs.completion_thread_matches_entry);
  out << ",\"preparation_owner_matches_selected\":";
  Boolean(out, inputs.preparation_owner_matches_selected);
  out << ",\"reason\":";
  JsonString(out, inputs.reason);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12004
