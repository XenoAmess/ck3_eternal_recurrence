#pragma once

#include "xar_bridge/person_callback_entry_inputs_12004.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

struct KnightConsumedContext12004;

struct PersonCurrentInputOutcomeBinding12004 {
  std::uintptr_t selected_character_identity = 0;
  std::uint32_t selected_character_id = 0; // Entire generation-bearing ID.
  std::uintptr_t getter_caller_return_rva = 0;
  std::optional<std::uintptr_t> returned_character_identity;
  std::optional<std::uint32_t> returned_character_id;
  std::optional<std::uintptr_t> returned_context_identity;
  std::optional<bool> selected_full_generation_matches_return;
  std::optional<bool> getter_site_matches_return;
  std::optional<bool> getter_occurrence_matches_return;
  std::optional<bool> entry_preparation_owner_and_thread_match;
  std::optional<bool> same_native65_preparation_identity;
  std::optional<bool> same_preparation_model_context_owner;
  std::optional<bool> entry_pc_matches_returned_preparation;
  std::optional<bool> entry_pc_matches_consumed_pc;
  // Equality of supplied entry inputs and this same getter consumption only.
  // This is neither native callback truth nor goal/action success.
  std::optional<bool> source_input_bound_to_consumption;
  std::string_view reason = "person_entry_input_binding_unavailable";
  friend bool operator==(const PersonCurrentInputOutcomeBinding12004 &,
                         const PersonCurrentInputOutcomeBinding12004 &) = default;
};

// Pure comparisons of owned copies. No memory reader, native call, global
// journal, current-query resolver, counter, or clock is owned by this leaf.
PersonCurrentInputOutcomeBinding12004 BindPersonCurrentInputOutcome12004(
    const PersonCallbackEntryInputs12004 &entry,
    const KnightConsumedContext12004 &consumption) noexcept;

std::string SerializePersonCurrentInputOutcomeBinding12004(
    const PersonCurrentInputOutcomeBinding12004 &binding);

} // namespace xar::ck3_12004
