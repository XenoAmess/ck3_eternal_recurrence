#include "xar_bridge/conception_pair_shortcircuit_12004.hpp"

#include <array>
#include <bit>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace xar::ck3_12004;
namespace {

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

ConceptionCharacterPredicate12004Input Basic(std::uint32_t id,
                                           std::uint8_t selector = 0) {
  ConceptionCharacterPredicate12004Input input;
  input.character_id = id;
  input.selector_1a1 = selector;
  input.measure_6c = std::int16_t{20};
  input.minimum_zero_selector = 20;
  input.minimum_nonzero_selector = 20;
  input.maximum_nonzero_selector = 20;
  input.current_modifier_bf_raw = 0;
  input.trait_count_raw = 0;
  return input;
}

} // namespace

int main() {
  try {
    // One new source-bound conditional-stage focus; no original native calls.
    auto first = Basic(29829);
    auto second = Basic(34730);
    first.measure_6c = std::int16_t{19};
    first.trait_count_raw.reset();
    auto pair = EvaluateConceptionPairShortCircuit12004(first, {});
    Check(pair.first_output_raw == 0 && !pair.second_evaluated &&
          pair.first.reason == "below_selected_minimum", "first short circuit");

    first = Basic(29829);
    first.measure_6c = std::int16_t{-1};
    auto read = EvaluateConceptionCharacterPredicate12004(first);
    Check(!read.predicate_true && read.reason == "fallback_measure_68_unread",
          "negative6c demands fallback");
    first.fallback_measure_68 = std::int16_t{20};
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == false && read.selected_measure == 20,
          "fallback measure selection");
    first.measure_6c = std::int16_t{20};
    first.fallback_measure_68 = std::int16_t{-32768};
    first.maximum_nonzero_selector.reset();
    first.current_modifier_bf_raw.reset();
    pair = EvaluateConceptionPairShortCircuit12004(first, second);
    Check(pair.short_circuits_to_zero == false && !pair.first_output_raw &&
          pair.second_evaluated && !pair.first.adjusted_maximum,
          "zero selector skips max and bothfalse is not output");

    first = Basic(29829, 1);
    first.current_modifier_bf_raw = 50'000;
    first.measure_6c = std::int16_t{21};
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == false && read.rounded_modifier == 1 &&
          read.adjusted_maximum == 21, "positive half and max equality");
    first.measure_6c = std::int16_t{22};
    first.trait_count_raw.reset();
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == true && read.trait_occurrences_evaluated == 0,
          "max reject skips traits");
    first.measure_6c = std::int16_t{20};
    first.current_modifier_bf_raw = -50'000;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == true && read.rounded_modifier == -1 &&
          read.adjusted_maximum == 19, "negative half and signed max");
    first.current_modifier_bf_raw = -49'999;
    first.trait_count_raw = 0;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == false && read.rounded_modifier == 0,
          "negative below half");

    std::array<std::optional<std::uint32_t>, 3> flags{0x28U, 0x20U, 0x8U};
    first = Basic(29829);
    first.trait_count_raw = 3;
    first.trait_definition_flags = flags;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == true &&
          read.first_blocking_trait_occurrence == 2U &&
          read.trait_occurrences_evaluated == 3,
          "bit5 independent of old bit3");
    flags[0].reset();
    flags[1] = 0;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(!read.predicate_true && read.trait_occurrences_evaluated == 0,
          "unread earlier definition cannot be skipped");
    flags[0] = 0;
    flags[1].reset();
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == true && read.trait_occurrences_evaluated == 1,
          "early blocking definition skips unread tail");
    first.trait_count_raw = 0xFFFFFFFFU;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.predicate_true == true,
          "raw DWORD negative spelling is not empty");

    first = Basic(29829);
    second.measure_6c = std::int16_t{19};
    pair = EvaluateConceptionPairShortCircuit12004(first, second);
    Check(pair.second_evaluated && pair.first_output_raw == 0 &&
          pair.reason == "second_predicate_true", "second short circuit");
    first.measure_6c.reset();
    pair = EvaluateConceptionPairShortCircuit12004(first, second);
    Check(!pair.short_circuits_to_zero && !pair.second_evaluated &&
          pair.reason == "first_predicate_unavailable",
          "unknown first cannot use second rejecting result");

    first = Basic(0, 1);
    first.maximum_nonzero_selector = std::numeric_limits<std::int32_t>::max();
    first.current_modifier_bf_raw = 100'000;
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.character_id == 0 && read.predicate_true == true &&
          read.adjusted_maximum == std::numeric_limits<std::int32_t>::min(),
          "fullID0 and native32bit maximum wrap");
    first.current_modifier_bf_raw = std::numeric_limits<std::int64_t>::max();
    const auto wrapped = std::bit_cast<std::int64_t>(
        std::bit_cast<std::uint64_t>(*first.current_modifier_bf_raw) + 50'000U);
    read = EvaluateConceptionCharacterPredicate12004(first);
    Check(read.rounded_modifier == wrapped / 100'000,
          "native64bit rounding addition wrap");
    std::cout << "GREEN: actual4 conditional pair short circuit; 16 branch scenarios\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
