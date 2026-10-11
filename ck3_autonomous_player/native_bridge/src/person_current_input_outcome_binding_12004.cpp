#include "xar_bridge/person_current_input_outcome_binding_12004.hpp"
#include "xar_bridge/knight_stat_consumption_12004.hpp"

#include <algorithm>
#include <array>
#include <iomanip>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {

template <std::size_t N>
std::optional<bool> AllKnownTrue(
    const std::array<std::optional<bool>, N> &facts) noexcept {
  bool missing = false;
  for (const auto fact : facts) {
    if (fact && !*fact) return false;
    if (!fact) missing = true;
  }
  return missing ? std::nullopt : std::optional<bool>(true);
}

template <class Event>
bool EventAvailable(const Event &event) noexcept {
  return event.clock_identity != 0 && event.sequence != 0 &&
      event.thread_id && *event.thread_id != 0;
}

bool CaptureHasOwner(const PersonSixStageCapture12004DTO &capture) noexcept {
  return capture.capture_observed && capture.character_identity &&
      capture.character_id;
}

bool HasModelContextOwner(
    const PersonSixStageCapture12004DTO &capture) noexcept {
  return capture.capture_observed && capture.preparation_model.observed &&
      capture.preparation_model.model_identity && capture.context_identity &&
      capture.preparation_model.owner_character_identity &&
      capture.preparation_model.owner_character_id;
}

bool PcInputAvailable(const PersonFollowing2922680Pc &pc) noexcept {
  if (!pc.ready || !pc.admitted || !*pc.admitted || !pc.identity ||
      *pc.identity == 0 || !pc.count_i32 || *pc.count_i32 < 0 ||
      !pc.properties || !pc.properties->keys_u16 ||
      !pc.properties->values_q64) return false;
  const auto count = static_cast<std::size_t>(*pc.count_i32);
  return pc.properties->keys_u16->size() == count &&
      pc.properties->values_q64->size() == count;
}

void JsonString(std::ostream &out, std::string_view value) {
  constexpr char digits[] = "0123456789abcdef";
  out << '"';
  for (const char raw : value) {
    const auto ch = static_cast<unsigned char>(raw);
    switch (ch) {
    case '"': out << "\\\""; break;
    case '\\': out << "\\\\"; break;
    case '\b': out << "\\b"; break;
    case '\f': out << "\\f"; break;
    case '\n': out << "\\n"; break;
    case '\r': out << "\\r"; break;
    case '\t': out << "\\t"; break;
    default:
      if (ch < 0x20U) out << "\\u00" << digits[ch >> 4U] << digits[ch & 0xFU];
      else out << raw;
    }
  }
  out << '"';
}

void Pointer(std::ostream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}

void OptionalPointer(std::ostream &out, std::optional<std::uintptr_t> value) {
  if (value) Pointer(out, *value);
  else out << "null";
}

void Boolean(std::ostream &out, std::optional<bool> value) {
  if (!value) out << "null";
  else out << (*value ? "true" : "false");
}

} // namespace

PersonCurrentInputOutcomeBinding12004 BindPersonCurrentInputOutcome12004(
    const PersonCallbackEntryInputs12004 &entry,
    const KnightConsumedContext12004 &consumption) noexcept {
  PersonCurrentInputOutcomeBinding12004 out;
  out.selected_character_identity = entry.selected_character_identity;
  out.selected_character_id = entry.selected_character_id;
  out.getter_caller_return_rva = entry.getter_caller_return_rva;
  out.returned_character_identity = consumption.selected_character_identity;
  out.returned_character_id = consumption.selected_character_id;
  out.returned_context_identity = consumption.context_identity;
  const auto site = std::find(kPersonCallbackEntryGetterReturns12004.begin(),
      kPersonCallbackEntryGetterReturns12004.end(), entry.getter_caller_return_rva);
  if (!entry.exact_image_bound || !entry.getter_site_observed ||
      site == kPersonCallbackEntryGetterReturns12004.end() ||
      entry.selected_character_identity == 0) {
    out.reason = "person_entry_source_binding_unavailable";
    return out;
  }

  if (consumption.selected_character_identity && consumption.selected_character_id)
    out.selected_full_generation_matches_return =
        *consumption.selected_character_identity == entry.selected_character_identity &&
        *consumption.selected_character_id == entry.selected_character_id;
  const auto index = static_cast<std::uint16_t>(
      site - kPersonCallbackEntryGetterReturns12004.begin());
  out.getter_site_matches_return =
      consumption.caller_return_rva == entry.getter_caller_return_rva &&
      consumption.property_key == static_cast<std::uint16_t>(0xC1U + index);

  if (entry.entry_event_observed && EventAvailable(entry.getter_begin_event) &&
      consumption.installed_transfer_lineage) {
    const auto &lineage = *consumption.installed_transfer_lineage;
    const auto &begin = lineage.getter_begin_event;
    const auto &end = lineage.getter_completed_event;
    if (EventAvailable(begin) && EventAvailable(end))
      out.getter_occurrence_matches_return =
          entry.getter_begin_event.clock_identity == begin.clock_identity &&
          entry.getter_begin_event.sequence == begin.sequence &&
          entry.getter_begin_event.thread_id == begin.thread_id &&
          begin.clock_identity == end.clock_identity &&
          begin.thread_id == end.thread_id && begin.sequence < end.sequence;
  }

  out.entry_preparation_owner_and_thread_match = AllKnownTrue(
      std::array<std::optional<bool>, 4>{entry.capture_identity_matches_selected,
          entry.capture_thread_matches_entry, entry.completion_thread_matches_entry,
          entry.preparation_owner_matches_selected});
  if (entry.preparation_at_entry && consumption.preparation_capture_at_consumption) {
    const auto &before = *entry.preparation_at_entry;
    const auto &after = *consumption.preparation_capture_at_consumption;
    if (CaptureHasOwner(before) && CaptureHasOwner(after) &&
        before.capture_sequence != 0 && after.capture_sequence != 0)
      out.same_native65_preparation_identity =
          before.capture_sequence == after.capture_sequence &&
          before.character_identity == after.character_identity &&
          before.character_id == after.character_id &&
          *after.character_identity == entry.selected_character_identity &&
          *after.character_id == entry.selected_character_id;
    if (HasModelContextOwner(before) && HasModelContextOwner(after))
      out.same_preparation_model_context_owner =
          before.preparation_model.model_identity == after.preparation_model.model_identity &&
          before.context_identity == after.context_identity &&
          before.preparation_model.owner_character_identity ==
              after.preparation_model.owner_character_identity &&
          before.preparation_model.owner_character_id ==
              after.preparation_model.owner_character_id &&
          *after.preparation_model.owner_character_identity == entry.selected_character_identity &&
          *after.preparation_model.owner_character_id == entry.selected_character_id &&
          consumption.context_identity == before.context_identity;
    if (before.post_six_aggregate.observed && PcInputAvailable(before.post_six_aggregate.pc) &&
        after.post_six_aggregate.observed && PcInputAvailable(after.post_six_aggregate.pc))
      out.entry_pc_matches_returned_preparation =
          before.post_six_aggregate.pc == after.post_six_aggregate.pc;
  }
  if (entry.preparation_at_entry) {
    const auto &before = *entry.preparation_at_entry;
    if (before.capture_observed && before.post_six_aggregate.observed &&
        PcInputAvailable(before.post_six_aggregate.pc) && PcInputAvailable(consumption.consumed_pc))
      out.entry_pc_matches_consumed_pc =
          before.post_six_aggregate.pc == consumption.consumed_pc;
  }
  out.source_input_bound_to_consumption = AllKnownTrue(
      std::array<std::optional<bool>, 8>{out.selected_full_generation_matches_return,
          out.getter_site_matches_return, out.getter_occurrence_matches_return,
          out.entry_preparation_owner_and_thread_match,
          out.same_native65_preparation_identity, out.same_preparation_model_context_owner,
          out.entry_pc_matches_returned_preparation, out.entry_pc_matches_consumed_pc});
  if (!out.source_input_bound_to_consumption)
    out.reason = "person_current_input_outcome_fields_unavailable";
  else if (!*out.source_input_bound_to_consumption)
    out.reason = "person_current_input_outcome_source_mismatch";
  else
    out.reason = "person_entry_inputs_equal_same_getter_consumption";
  return out;
}

std::string SerializePersonCurrentInputOutcomeBinding12004(
    const PersonCurrentInputOutcomeBinding12004 &binding) {
  std::ostringstream out;
  out << "{\"schema\":\"xar.ck3.person-current-input-outcome-binding-12004-v1\""
      << ",\"selected_character_identity\":";
  Pointer(out, binding.selected_character_identity);
  out << ",\"selected_character_id\":" << binding.selected_character_id
      << ",\"getter_caller_return_rva\":";
  Pointer(out, binding.getter_caller_return_rva);
  out << ",\"returned_character_identity\":";
  OptionalPointer(out, binding.returned_character_identity);
  out << ",\"returned_character_id\":";
  if (binding.returned_character_id) out << *binding.returned_character_id;
  else out << "null";
  out << ",\"returned_context_identity\":";
  OptionalPointer(out, binding.returned_context_identity);
  const std::array<std::pair<std::string_view, std::optional<bool>>, 9> facts{{
      {"selected_full_generation_matches_return", binding.selected_full_generation_matches_return},
      {"getter_site_matches_return", binding.getter_site_matches_return},
      {"getter_occurrence_matches_return", binding.getter_occurrence_matches_return},
      {"entry_preparation_owner_and_thread_match", binding.entry_preparation_owner_and_thread_match},
      {"same_native65_preparation_identity", binding.same_native65_preparation_identity},
      {"same_preparation_model_context_owner", binding.same_preparation_model_context_owner},
      {"entry_pc_matches_returned_preparation", binding.entry_pc_matches_returned_preparation},
      {"entry_pc_matches_consumed_pc", binding.entry_pc_matches_consumed_pc},
      {"source_input_bound_to_consumption", binding.source_input_bound_to_consumption},
  }};
  for (const auto &[name, value] : facts) {
    out << ",\"" << name << "\":";
    Boolean(out, value);
  }
  out << ",\"reason\":";
  JsonString(out, binding.reason);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12004
