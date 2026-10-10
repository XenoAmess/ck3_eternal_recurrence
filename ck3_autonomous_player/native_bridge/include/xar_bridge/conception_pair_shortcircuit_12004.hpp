#pragma once

#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace xar::ck3_12004 {

// Conditional current-input stage, not an original-function binding. Root must
// supply every used value from one actual4 current household query frame.
struct ConceptionCharacterPredicate12004Input {
  std::uint32_t character_id = 0xFFFFFFFFU;
  std::optional<std::uint8_t> selector_1a1;
  std::optional<std::int16_t> measure_6c;
  std::optional<std::int16_t> fallback_measure_68;
  std::optional<std::int32_t> minimum_nonzero_selector;
  std::optional<std::int32_t> minimum_zero_selector;
  std::optional<std::int32_t> maximum_nonzero_selector;
  // Completed current modifier key BF lookup: native no-match is raw0.
  // A failed/unperformed lookup remains null, including an unread context.
  std::optional<std::int64_t> current_modifier_bf_raw;
  // Actual loop uses DWORD equality, not a signed<=0 empty shortcut.
  std::optional<std::uint32_t> trait_count_raw;
  // Ordered resolved definition DWORD4A4, including native invalid-definition
  // fallback when independently observed. Null is an unread definition.
  std::span<const std::optional<std::uint32_t>> trait_definition_flags;
};

struct ConceptionCharacterPredicate12004Read {
  std::uint32_t character_id = 0xFFFFFFFFU;
  std::string_view status = "unavailable";
  std::string_view reason = "character_input_unavailable";
  std::optional<bool> predicate_true;
  std::optional<std::int32_t> selected_measure;
  std::optional<std::int32_t> selected_minimum;
  std::optional<std::int32_t> adjusted_maximum;
  std::optional<std::int64_t> rounded_modifier;
  std::uint32_t trait_occurrences_evaluated = 0;
  std::optional<std::uint32_t> first_blocking_trait_occurrence;
};

struct ConceptionPairShortCircuit12004Read {
  std::string_view source = "conditional_actual4_pair_provider_shortcircuit";
  std::string_view status = "unavailable";
  std::string_view reason = "pair_input_unavailable";
  std::uint32_t first_character_id = 0xFFFFFFFFU;
  std::uint32_t second_character_id = 0xFFFFFFFFU;
  bool first_evaluated = false;
  bool second_evaluated = false;
  ConceptionCharacterPredicate12004Read first;
  ConceptionCharacterPredicate12004Read second;
  std::optional<bool> short_circuits_to_zero;
  // Present only for a closed rejecting branch. Both false does not provide a
  // final pair value and leaves this field null.
  std::optional<std::int64_t> first_output_raw;
};

// Actual predicate2B96730 under mode1 and null text receiver only.
ConceptionCharacterPredicate12004Read EvaluateConceptionCharacterPredicate12004(
    const ConceptionCharacterPredicate12004Input &input) noexcept;

// Actual parent2B95670 under entry mode3/fifth0 only. Does not call either
// original function, mutate native state, or infer conception probability.
ConceptionPairShortCircuit12004Read EvaluateConceptionPairShortCircuit12004(
    const ConceptionCharacterPredicate12004Input &first,
    const ConceptionCharacterPredicate12004Input &second) noexcept;

} // namespace xar::ck3_12004
