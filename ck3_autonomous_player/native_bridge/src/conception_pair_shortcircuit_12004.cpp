#include "xar_bridge/conception_pair_shortcircuit_12004.hpp"

#include <bit>

namespace xar::ck3_12004 {
namespace {

ConceptionCharacterPredicate12004Read Complete(
    ConceptionCharacterPredicate12004Read result, bool predicate_true,
    std::string_view reason) noexcept {
  result.status = "available";
  result.reason = reason;
  result.predicate_true = predicate_true;
  return result;
}

//2B96984..9B4: ADD RCX,+/-50000 wraps64, then signed division100000.
std::int64_t RoundCurrentModifier(std::int64_t raw) noexcept {
  auto bits = std::bit_cast<std::uint64_t>(raw);
  if (raw < 0) bits -= 50'000U;
  else bits += 50'000U;
  return std::bit_cast<std::int64_t>(bits) / 100'000;
}

} // namespace

ConceptionCharacterPredicate12004Read EvaluateConceptionCharacterPredicate12004(
    const ConceptionCharacterPredicate12004Input &input) noexcept {
  ConceptionCharacterPredicate12004Read result;
  result.character_id = input.character_id;
  if (input.character_id == 0xFFFFFFFFU) return result;
  if (!input.selector_1a1) { result.reason = "selector_unread"; return result; }
  if (!input.measure_6c) { result.reason = "measure_6c_unread"; return result; }
  std::int32_t measure = *input.measure_6c;
  if (measure < 0) {
    if (!input.fallback_measure_68) {
      result.reason = "fallback_measure_68_unread";
      return result;
    }
    measure = *input.fallback_measure_68;
  }
  result.selected_measure = measure;
  const bool nonzero_selector = *input.selector_1a1 != 0;
  const auto minimum = nonzero_selector ? input.minimum_nonzero_selector :
                                        input.minimum_zero_selector;
  if (!minimum) { result.reason = "selected_minimum_unread"; return result; }
  result.selected_minimum = *minimum;
  if (measure < *minimum)
    return Complete(result, true, "below_selected_minimum");

  if (nonzero_selector) {
    if (!input.current_modifier_bf_raw) {
      result.reason = "current_modifier_bf_unread";
      return result;
    }
    if (!input.maximum_nonzero_selector) {
      result.reason = "maximum_nonzero_selector_unread";
      return result;
    }
    const auto rounded = RoundCurrentModifier(*input.current_modifier_bf_raw);
    result.rounded_modifier = rounded;
    // Actual ADD ECX,EDX is a32bit addition, followed by signed CMP.
    const auto max_bits = std::bit_cast<std::uint32_t>(
        *input.maximum_nonzero_selector) + static_cast<std::uint32_t>(rounded);
    const auto maximum = std::bit_cast<std::int32_t>(max_bits);
    result.adjusted_maximum = maximum;
    if (measure > maximum)
      return Complete(result, true, "above_adjusted_maximum");
  }

  if (!input.trait_count_raw) { result.reason = "trait_count_unread"; return result; }
  for (std::uint32_t occurrence = 0; occurrence < *input.trait_count_raw;
       ++occurrence) {
    if (occurrence >= input.trait_definition_flags.size() ||
        !input.trait_definition_flags[occurrence]) {
      result.reason = "trait_definition_flags_unread";
      return result;
    }
    ++result.trait_occurrences_evaluated;
    //2B96D31..3C tests bit5, then clear branches to AL1.
    if ((*input.trait_definition_flags[occurrence] & 0x20U) == 0) {
      result.first_blocking_trait_occurrence = occurrence;
      return Complete(result, true, "trait_bit5_clear");
    }
  }
  return Complete(result, false, "predicate_false_continue_provider");
}

ConceptionPairShortCircuit12004Read EvaluateConceptionPairShortCircuit12004(
    const ConceptionCharacterPredicate12004Input &first,
    const ConceptionCharacterPredicate12004Input &second) noexcept {
  ConceptionPairShortCircuit12004Read result;
  result.first_character_id = first.character_id;
  result.second_character_id = second.character_id;
  result.first_evaluated = true;
  result.first = EvaluateConceptionCharacterPredicate12004(first);
  if (!result.first.predicate_true) { result.reason = "first_predicate_unavailable"; return result; }
  if (*result.first.predicate_true) {
    result.status = "available";
    result.reason = "first_predicate_true";
    result.short_circuits_to_zero = true;
    result.first_output_raw = 0;
    return result;
  }
  result.second_evaluated = true;
  result.second = EvaluateConceptionCharacterPredicate12004(second);
  if (!result.second.predicate_true) { result.reason = "second_predicate_unavailable"; return result; }
  result.status = "available";
  result.short_circuits_to_zero = *result.second.predicate_true;
  result.reason = *result.second.predicate_true ? "second_predicate_true" :
                                               "both_false_continue_provider";
  if (*result.second.predicate_true) result.first_output_raw = 0;
  return result;
}

} // namespace xar::ck3_12004
