#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kConceptionThresholdExecutableSha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

// Shared13 clock and active19b parent coordinate. No capture/journal ordinal
// is substituted for this process-local clock. Full IDs retain every bit.
struct ConceptionThresholdParentKey12004 {
  std::uintptr_t clock_identity = 0;
  std::uint64_t parent_scope_id = 0;
  std::uint64_t process_clock = 0;
  std::uint32_t thread_id = 0;
  std::uintptr_t first_character = 0, second_character = 0;
  std::uint32_t first_full_id = UINT32_MAX, second_full_id = UINT32_MAX;
  std::uintptr_t sample_receiver = 0;
  std::string_view source_pin{};
  bool operator==(const ConceptionThresholdParentKey12004 &) const = default;
};

struct ConceptionCapturedQ64Input12004 {
  std::optional<std::int64_t> raw;
  ConceptionThresholdParentKey12004 parent;
  // True only for a genuinely consumed original-invocation value. Guarded
  // scalar/clamp bookends and query/software projections retain false.
  bool actual_original_value = false;
};

struct ConceptionThresholdCompletion12004 {
  ConceptionThresholdParentKey12004 parent;
  bool original_called_once = false, original_returned = false;
  std::optional<std::uint8_t> original_al;
  std::optional<bool> pair_generation_unchanged;
  std::optional<std::uintptr_t> first_extended_before, first_extended_after;
  std::optional<std::uint8_t> candidate_flag_after;
  std::optional<std::uintptr_t> candidate_target_after;
};

struct ConceptionThresholdInputs12004 {
  std::string_view executable_sha256{};
  ConceptionThresholdParentKey12004 parent;
  ConceptionCapturedQ64Input12004 provider_first_qword;
  ConceptionCapturedQ64Input12004 monthly_scalar; // Actual loaded slot5C69EC8.
  ConceptionCapturedQ64Input12004 original_r9_modifier;
  ConceptionCapturedQ64Input12004 lower_clamp; // Actual slot5C69F00; key unknown.
  ConceptionCapturedQ64Input12004 upper_clamp; // Actual slot5C69F10; key unknown.
  ConceptionCapturedQ64Input12004 sample; //18b original E46530 returnedRAX.
  //18b source-bound caller RBX at E46530 entry, preserved through that helper
  // to the actual CMP RAX,RBX at2929D99. Independent of the scalar model.
  ConceptionCapturedQ64Input12004 original_comparison_threshold;
  std::optional<ConceptionThresholdCompletion12004> completion;
};

enum ConceptionThresholdInputMask12004 : std::uint32_t {
  conception_threshold_provider = 1U << 0,
  conception_threshold_scalar = 1U << 1,
  conception_threshold_modifier = 1U << 2,
  conception_threshold_lower = 1U << 3,
  conception_threshold_upper = 1U << 4,
  conception_threshold_sample = 1U << 5,
};

struct ConceptionThresholdArithmeticStage12004 {
  std::string_view path{}; // native_fast64 or native_minmax_wrap64.
  std::int64_t first_raw = 0, second_raw = 0, result_raw = 0;
  std::optional<std::int64_t> product_wrapped_raw;
  std::optional<std::int64_t> maximum_raw, minimum_raw;
  std::optional<std::int64_t> maximum_quotient_raw, maximum_remainder_raw;
  std::optional<std::int64_t> remainder_product_wrapped_raw;
  std::optional<std::int64_t> quotient_product_wrapped_raw;
};

struct ConceptionThresholdObservation12004 {
  bool conditional_available = false;
  std::string_view reason = "threshold_parent_unavailable";
  std::string_view branch = "unavailable";
  std::uint32_t missing_inputs_mask = 0, mismatched_inputs_mask = 0;
  std::uint32_t non_consumed_original_inputs_mask = 0;
  std::optional<ConceptionThresholdArithmeticStage12004> first_stage, second_stage;
  std::string_view clamp_branch{}; // lower, upper, inside.
  std::optional<std::int64_t> threshold_raw;
  std::optional<bool> conditional_accepts;
  std::optional<std::uint8_t> expected_candidate_flag;
  std::optional<std::uintptr_t> expected_candidate_target;
  // Independent actual return and post-write facts, never computed from a
  // missing sample or substituted query projection.
  std::optional<bool> native_parent_accepted;
  std::optional<bool> observed_write_pair_matches;
  // Stronger arithmetic-input claim; unsampled scalar/clamp bookends keep
  // this false even when the smaller original comparison is proven below.
  bool accepted_causal = false;
  std::string_view causal_reason = "conditional_acceptance_unavailable";
  // Original comparison plane is evaluated before any model early return.
  // It needs only the actual same-parent sample/threshold and original-once
  // AL1 plus matching candidate writes, never a projected provider/global.
  bool original_compare_available = false;
  std::optional<std::int64_t> original_threshold_raw;
  std::optional<bool> original_sample_below_threshold;
  bool original_compare_causal = false;
  std::string_view original_compare_reason = "original_comparison_threshold_unavailable";
};

// Copied input only: no memory reader, native call, random draw or clock.
ConceptionThresholdObservation12004 EvaluateConceptionThreshold12004(
    const ConceptionThresholdInputs12004 &) noexcept;

// New owned cases are called only by central10's connected19b/18b/45b compound.
void VerifyConceptionThreshold12004ConnectedCases();

} // namespace xar::ck3_12004
