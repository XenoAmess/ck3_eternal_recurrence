#include "xar_bridge/conception_pair_threshold_consumer_12004.hpp"

#include <limits>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
void Require(bool condition, const char *case_name) {
  if (!condition) throw std::runtime_error(case_name);
}
ConceptionCapturedQ64Input12004 Copy(
    std::int64_t raw, const ConceptionThresholdParentKey12004 &parent,
    bool actual = false) {
  return {raw, parent, actual};
}
ConceptionThresholdInputs12004 Base() {
  ConceptionThresholdInputs12004 inputs{};
  inputs.executable_sha256 = kConceptionThresholdExecutableSha12004;
  inputs.parent = {0x3000, 11, 11, 7, 0x1000, 0x2000,
                   0xC0000027U, 0xD0000031U, 0x4000,
                   kConceptionThresholdExecutableSha12004};
  inputs.provider_first_qword = Copy(25000, inputs.parent);
  inputs.monthly_scalar = Copy(100000, inputs.parent);
  inputs.original_r9_modifier = Copy(100000, inputs.parent);
  inputs.lower_clamp = Copy(1000, inputs.parent);
  inputs.upper_clamp = Copy(1000000, inputs.parent);
  inputs.sample = Copy(24999, inputs.parent);
  return inputs;
}
void Completion(ConceptionThresholdInputs12004 &inputs) {
  ConceptionThresholdCompletion12004 completion{};
  completion.parent = inputs.parent;
  completion.original_called_once = completion.original_returned = true;
  completion.original_al = 1;
  completion.pair_generation_unchanged = true;
  completion.first_extended_before = completion.first_extended_after = 0x5000;
  completion.candidate_flag_after = 1;
  completion.candidate_target_after = inputs.parent.second_character;
  inputs.completion = completion;
}
void AllConsumed(ConceptionThresholdInputs12004 &inputs) {
  inputs.provider_first_qword.actual_original_value = true;
  inputs.monthly_scalar.actual_original_value = true;
  inputs.original_r9_modifier.actual_original_value = true;
  inputs.lower_clamp.actual_original_value = true;
  inputs.upper_clamp.actual_original_value = true;
  inputs.sample.actual_original_value = true;
}
void OriginalCompare(ConceptionThresholdInputs12004 &inputs) {
  inputs.original_comparison_threshold = Copy(25000, inputs.parent, true);
  inputs.sample.actual_original_value = true;
  Completion(inputs);
}
} // namespace

// New cases for the single central19b/18b/45b compound. These owned copied
// inputs and synthetic completion facts qualify this pure leaf only.
void VerifyConceptionThreshold12004ConnectedCases() {
  {
    const auto result = EvaluateConceptionThreshold12004(Base());
    Require(result.conditional_accepts == true && result.threshold_raw == 25000 &&
            result.first_stage->path == "native_fast64" &&
            result.second_stage->path == "native_fast64" &&
            result.expected_candidate_flag == 1 &&
            result.expected_candidate_target == 0x2000 &&
            !result.accepted_causal && !result.original_compare_causal,
            "fast copied model accepts without causal credit");
  }
  {
    auto inputs = Base();
    inputs.sample.raw = 25000;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.conditional_accepts == false &&
            result.branch == "sample_at_or_above_threshold" &&
            !result.expected_candidate_flag,
            "signed sample equality rejects");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword.raw = 0;
    inputs.monthly_scalar = inputs.original_r9_modifier = {};
    inputs.lower_clamp = inputs.upper_clamp = inputs.sample = {};
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.conditional_available && result.conditional_accepts == false &&
            result.branch == "provider_zero" && result.missing_inputs_mask == 0 &&
            !result.first_stage && !result.threshold_raw,
            "zero provider skips unused suffix inputs");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword.raw = -25000;
    inputs.lower_clamp.raw = 0;
    inputs.sample = {};
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.first_stage->result_raw == -25000 &&
            result.second_stage->result_raw == -25000 &&
            result.threshold_raw == 0 && result.conditional_accepts == false &&
            result.branch == "nonpositive_threshold" && result.missing_inputs_mask == 0,
            "negative nonzero provider reaches arithmetic and nonpositive clamp");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword.raw = 10000;
    inputs.lower_clamp.raw = 20000;
    inputs.upper_clamp.raw = 5000;
    inputs.sample.raw = 20000;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.threshold_raw == 20000 && result.clamp_branch == "lower" &&
            result.conditional_accepts == false,
            "inverted clamp preserves lower-first branch");
  }
  {
    auto inputs = Base();
    inputs.upper_clamp.raw = 20000;
    inputs.sample.raw = 19999;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.threshold_raw == 20000 && result.clamp_branch == "upper" &&
            result.conditional_accepts == true, "signed upper clamp");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword.raw = (std::numeric_limits<std::int64_t>::max)();
    inputs.monthly_scalar.raw = (std::numeric_limits<std::int64_t>::max)() - 1;
    inputs.lower_clamp.raw = 0;
    inputs.upper_clamp.raw = (std::numeric_limits<std::int64_t>::max)();
    inputs.sample.raw = 5;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    const auto &stage = *result.first_stage;
    Require(stage.path == "native_minmax_wrap64" &&
            stage.maximum_quotient_raw == INT64_C(92233720368547) &&
            stage.maximum_remainder_raw == 75807 &&
            stage.remainder_product_wrapped_raw == INT64_C(9223372036854624194) &&
            stage.quotient_product_wrapped_raw == INT64_C(9223187569414038714) &&
            stage.result_raw == INT64_C(9223279803134407260) &&
            result.second_stage->result_raw == stage.result_raw &&
            result.conditional_accepts == true,
            "slow independently wrapped products differ from one full128 division");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword.raw = 1;
    inputs.original_r9_modifier.raw = (std::numeric_limits<std::int64_t>::min)();
    inputs.lower_clamp.raw = (std::numeric_limits<std::int64_t>::min)();
    inputs.upper_clamp.raw = (std::numeric_limits<std::int64_t>::max)();
    inputs.sample = {};
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.first_stage->path == "native_fast64" &&
            result.second_stage->path == "native_minmax_wrap64" &&
            result.second_stage->result_raw == -INT64_C(92233720368547) &&
            result.conditional_accepts == false && result.missing_inputs_mask == 0,
            "second-stage signed minimum slow path truncates toward zero");
  }
  {
    auto inputs = Base();
    inputs.provider_first_qword = {};
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.conditional_available && !result.conditional_accepts &&
            result.missing_inputs_mask == conception_threshold_provider &&
            !result.threshold_raw, "missing provider remains unknown");
  }
  {
    auto inputs = Base();
    inputs.sample = {};
    Completion(inputs);
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.conditional_accepts && result.threshold_raw == 25000 &&
            result.missing_inputs_mask == conception_threshold_sample &&
            result.native_parent_accepted == true &&
            result.observed_write_pair_matches == true &&
            !result.accepted_causal && !result.original_compare_causal,
            "actual completion is independent of missing sample model");
  }
  {
    auto inputs = Base();
    inputs.sample.parent.second_full_id ^= 0x10000000U;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.conditional_accepts &&
            result.mismatched_inputs_mask == conception_threshold_sample,
            "full generation bits participate in sample join");
  }
  {
    auto inputs = Base();
    AllConsumed(inputs);
    Completion(inputs);
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.accepted_causal && result.causal_reason.empty() &&
            !result.original_compare_causal,
            "all original arithmetic inputs plus completion qualifies stronger plane");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.conditional_accepts == true && !result.accepted_causal &&
            result.causal_reason == "conditional_input_not_consumed_original" &&
            result.original_compare_available && result.original_compare_causal &&
            result.original_sample_below_threshold == true &&
            result.original_threshold_raw == 25000,
            "actual comparison closes smaller plane with raw scalar bookends");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.provider_first_qword = inputs.monthly_scalar = {};
    inputs.original_r9_modifier = inputs.lower_clamp = inputs.upper_clamp = {};
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.conditional_available &&
            result.missing_inputs_mask == conception_threshold_provider &&
            result.original_compare_causal && !result.accepted_causal,
            "actual comparison is evaluated despite unavailable provider and arithmetic");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.sample.raw = 25000;
    inputs.completion->original_al = 0;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.original_compare_available &&
            result.original_sample_below_threshold == false &&
            !result.original_compare_causal &&
            result.original_compare_reason == "original_comparison_rejected",
            "original comparison equality preserves rejection");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.original_comparison_threshold.actual_original_value = false;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.original_compare_available && !result.original_sample_below_threshold &&
            !result.original_compare_causal &&
            result.original_compare_reason == "original_comparison_input_not_consumed_original",
            "projected threshold never grants original compare credit");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.completion->candidate_target_after = 0xDEAD;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(result.native_parent_accepted == true &&
            result.observed_write_pair_matches == false &&
            !result.original_compare_causal &&
            result.original_compare_reason == "candidate_write_pair_not_proven",
            "actual target mismatch withholds causal write pair");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.completion->parent.thread_id = 8;
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.native_parent_accepted && !result.observed_write_pair_matches &&
            !result.original_compare_causal,
            "different thread completion is not joined");
  }
  {
    auto inputs = Base();
    OriginalCompare(inputs);
    inputs.parent.source_pin = "old executable";
    const auto result = EvaluateConceptionThreshold12004(inputs);
    Require(!result.conditional_available && !result.original_compare_available &&
            !result.native_parent_accepted && !result.original_compare_causal,
            "current exact source pin admission precedes both planes");
  }
}
} // namespace xar::ck3_12004
