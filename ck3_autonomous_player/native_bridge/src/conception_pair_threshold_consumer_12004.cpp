#include "xar_bridge/conception_pair_threshold_consumer_12004.hpp"

#include <bit>

namespace xar::ck3_12004 {
namespace {
std::uint64_t Bits(std::int64_t value) noexcept {
  return std::bit_cast<std::uint64_t>(value);
}
std::int64_t Signed(std::uint64_t value) noexcept {
  return std::bit_cast<std::int64_t>(value);
}
std::int64_t MultiplyWrapped(std::int64_t first, std::int64_t second) noexcept {
  return Signed(Bits(first) * Bits(second));
}
bool FastRange(std::int64_t value) noexcept {
  // Actual LEA and JA use 64-bit wrap followed by an unsigned comparison.
  return Bits(value) + UINT64_C(0xB504F333) <= UINT64_C(0x16A09E666);
}
ConceptionThresholdArithmeticStage12004 Scale(std::int64_t first,
                                               std::int64_t second) noexcept {
  ConceptionThresholdArithmeticStage12004 result{};
  result.first_raw = first;
  result.second_raw = second;
  if (FastRange(first) && FastRange(second)) {
    result.path = "native_fast64";
    const auto product = MultiplyWrapped(first, second);
    result.product_wrapped_raw = product;
    // Actual reciprocal signed-high/SAR14/sign correction implements this
    // exact signed quotient. Both branches truncate toward zero.
    result.result_raw = product / INT64_C(100000);
    return result;
  }
  result.path = "native_minmax_wrap64";
  const auto maximum = first > second ? first : second;
  const auto minimum = first > second ? second : first;
  const auto quotient = maximum / INT64_C(100000);
  const auto remainder = Signed(Bits(maximum) -
      Bits(MultiplyWrapped(quotient, INT64_C(100000))));
  const auto remainder_product = MultiplyWrapped(remainder, minimum);
  const auto quotient_product = MultiplyWrapped(quotient, minimum);
  result.maximum_raw = maximum;
  result.minimum_raw = minimum;
  result.maximum_quotient_raw = quotient;
  result.maximum_remainder_raw = remainder;
  result.remainder_product_wrapped_raw = remainder_product;
  result.quotient_product_wrapped_raw = quotient_product;
  result.result_raw = Signed(Bits(remainder_product / INT64_C(100000)) +
                             Bits(quotient_product));
  return result;
}

bool ValidParent(const ConceptionThresholdParentKey12004 &parent) noexcept {
  return parent.clock_identity != 0 && parent.parent_scope_id != 0 &&
      parent.process_clock != 0 && parent.thread_id != 0 &&
      parent.first_character != 0 && parent.second_character != 0 &&
      parent.first_full_id != UINT32_MAX && parent.second_full_id != UINT32_MAX &&
      parent.sample_receiver != 0 &&
      parent.source_pin == kConceptionThresholdExecutableSha12004;
}
bool Input(const ConceptionCapturedQ64Input12004 &input,
           const ConceptionThresholdInputs12004 &inputs, std::uint32_t bit,
           ConceptionThresholdObservation12004 &output) noexcept {
  if (!input.raw) {
    output.missing_inputs_mask |= bit;
    output.reason = "threshold_input_unavailable";
    return false;
  }
  if (input.parent != inputs.parent) {
    output.mismatched_inputs_mask |= bit;
    output.reason = "threshold_input_parent_mismatch";
    return false;
  }
  if (!input.actual_original_value) output.non_consumed_original_inputs_mask |= bit;
  return true;
}
void ObserveCompletion(const ConceptionThresholdInputs12004 &inputs,
                       ConceptionThresholdObservation12004 &output) noexcept {
  if (!inputs.completion || inputs.completion->parent != inputs.parent) return;
  const auto &completion = *inputs.completion;
  if (!completion.original_called_once || !completion.original_returned) return;
  if (completion.original_al && *completion.original_al <= 1)
    output.native_parent_accepted = *completion.original_al == 1;
  if (completion.pair_generation_unchanged == true &&
      completion.first_extended_before && completion.first_extended_after &&
      *completion.first_extended_before != 0 &&
      completion.first_extended_before == completion.first_extended_after &&
      completion.candidate_flag_after && completion.candidate_target_after) {
    output.observed_write_pair_matches = *completion.candidate_flag_after == 1 &&
        *completion.candidate_target_after == inputs.parent.second_character;
  }
}
void Causal(const ConceptionThresholdInputs12004 &inputs,
            ConceptionThresholdObservation12004 &output) noexcept {
  ObserveCompletion(inputs, output);
  if (output.conditional_accepts != true) {
    output.causal_reason = output.conditional_accepts == false
        ? "conditional_branch_rejected" : "conditional_acceptance_unavailable";
    return;
  }
  if (output.non_consumed_original_inputs_mask != 0) {
    output.causal_reason = "conditional_input_not_consumed_original";
    return;
  }
  if (!output.native_parent_accepted) {
    output.causal_reason = "same_parent_original_completion_unavailable";
    return;
  }
  if (output.native_parent_accepted != true) {
    output.causal_reason = "native_parent_return_disagrees";
    return;
  }
  if (output.observed_write_pair_matches != true) {
    output.causal_reason = "candidate_write_pair_not_proven";
    return;
  }
  output.accepted_causal = true;
  output.causal_reason = {};
}
void OriginalCompare(const ConceptionThresholdInputs12004 &inputs,
                     ConceptionThresholdObservation12004 &output) noexcept {
  const auto &threshold = inputs.original_comparison_threshold;
  if (!threshold.raw) return;
  if (threshold.parent != inputs.parent) {
    output.original_compare_reason = "original_comparison_parent_mismatch";
    return;
  }
  output.original_threshold_raw = threshold.raw;
  if (!inputs.sample.raw) {
    output.original_compare_reason = "original_comparison_sample_unavailable";
    return;
  }
  if (inputs.sample.parent != inputs.parent) {
    output.original_compare_reason = "original_comparison_parent_mismatch";
    return;
  }
  if (!threshold.actual_original_value || !inputs.sample.actual_original_value) {
    output.original_compare_reason = "original_comparison_input_not_consumed_original";
    return;
  }
  if (*threshold.raw <= 0) {
    output.original_compare_reason = "original_comparison_threshold_not_positive";
    return;
  }
  output.original_compare_available = true;
  output.original_sample_below_threshold = *inputs.sample.raw < *threshold.raw;
  if (output.original_sample_below_threshold != true) {
    output.original_compare_reason = "original_comparison_rejected";
    return;
  }
  if (!output.native_parent_accepted) {
    output.original_compare_reason = "same_parent_original_completion_unavailable";
    return;
  }
  if (output.native_parent_accepted != true) {
    output.original_compare_reason = "native_parent_return_disagrees";
    return;
  }
  if (output.observed_write_pair_matches != true) {
    output.original_compare_reason = "candidate_write_pair_not_proven";
    return;
  }
  output.original_compare_causal = true;
  output.original_compare_reason = {};
}
} // namespace

ConceptionThresholdObservation12004 EvaluateConceptionThreshold12004(
    const ConceptionThresholdInputs12004 &inputs) noexcept {
  ConceptionThresholdObservation12004 output{};
  if (inputs.executable_sha256 != kConceptionThresholdExecutableSha12004 ||
      !ValidParent(inputs.parent)) return output;
  ObserveCompletion(inputs, output);
  OriginalCompare(inputs, output);
  if (!Input(inputs.provider_first_qword, inputs, conception_threshold_provider, output))
    return output;
  if (*inputs.provider_first_qword.raw == 0) {
    output.conditional_available = true;
    output.reason = {};
    output.branch = "provider_zero";
    output.conditional_accepts = false;
    Causal(inputs, output);
    return output;
  }
  if (!Input(inputs.monthly_scalar, inputs, conception_threshold_scalar, output)) return output;
  output.first_stage = Scale(*inputs.provider_first_qword.raw, *inputs.monthly_scalar.raw);
  if (!Input(inputs.original_r9_modifier, inputs, conception_threshold_modifier, output))
    return output;
  output.second_stage = Scale(output.first_stage->result_raw, *inputs.original_r9_modifier.raw);
  const bool lower = Input(inputs.lower_clamp, inputs, conception_threshold_lower, output);
  const bool upper = Input(inputs.upper_clamp, inputs, conception_threshold_upper, output);
  if (!lower || !upper) return output;
  const auto value = output.second_stage->result_raw;
  const auto lo = *inputs.lower_clamp.raw;
  const auto hi = *inputs.upper_clamp.raw;
  if (value < lo) {
    output.clamp_branch = "lower";
    output.threshold_raw = lo;
  } else if (value > hi) {
    output.clamp_branch = "upper";
    output.threshold_raw = hi;
  } else {
    output.clamp_branch = "inside";
    output.threshold_raw = value;
  }
  if (*output.threshold_raw <= 0) {
    output.conditional_available = true;
    output.reason = {};
    output.branch = "nonpositive_threshold";
    output.conditional_accepts = false;
    Causal(inputs, output);
    return output;
  }
  if (!Input(inputs.sample, inputs, conception_threshold_sample, output)) return output;
  output.conditional_available = true;
  output.reason = {};
  output.conditional_accepts = *inputs.sample.raw < *output.threshold_raw;
  output.branch = *output.conditional_accepts ? "sample_below_threshold" :
                                               "sample_at_or_above_threshold";
  if (*output.conditional_accepts) {
    output.expected_candidate_flag = 1;
    output.expected_candidate_target = inputs.parent.second_character;
  }
  Causal(inputs, output);
  return output;
}
} // namespace xar::ck3_12004
