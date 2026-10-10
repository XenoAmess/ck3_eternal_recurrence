#pragma once

#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"
#include "xar_bridge/construction_numeric_child_24cef10_12004.hpp"
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kConstructionNumeric2C39B80SourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uintptr_t kConstructionNumeric2C39B80ScalarRva12004 = 0x5C69450;

enum class Numeric2C39B80InputFailureV1 : std::uint8_t {
  none, exact_build, read_callback, province_identity, context,
  receiver_read, image_base, scalar_read, source_changed,
};

struct LoadedNumeric2C39B80InputsV1 {
  bool observed = false;
  Numeric2C39B80InputFailureV1 failure = Numeric2C39B80InputFailureV1::none;
  std::string_view source_pin = kConstructionNumeric2C39B80SourcePin12004;
  // Supplied unchanged by outer captured CampaignRootFrame snapshot_revision.
  // This reader neither invents nor advances a frame/event coordinate.
  std::uint64_t frame_key = 0;
  std::int32_t province_id = -1;
  std::uintptr_t province_pointer = 0, slots_pointer = 0;
  std::uintptr_t context_pointer = 0, receiver_pointer = 0;
  std::uintptr_t image_base = 0, scalar_address = 0;
  std::optional<std::int64_t> scalar_raw;
  // Equal bookends remain copies, not original instruction consumed values.
  bool actual_original_consumed_values = false;
};

inline LoadedNumeric2C39B80InputsV1 ReadLoadedNumericHelper2C39B80InputsV1(
    const LoadedInputAccessV1 &access, std::uintptr_t province,
    std::int32_t expected_province_id, std::uintptr_t image_base,
    std::uint64_t frame_key) noexcept {
  LoadedNumeric2C39B80InputsV1 result;
  result.province_pointer = province;
  result.province_id = expected_province_id;
  result.image_base = image_base;
  result.frame_key = frame_key;
  const auto fail = [&](Numeric2C39B80InputFailureV1 failure) {
    result.failure = failure;
    result.observed = false;
    return result;
  };
  if (!access.exact_12004_bound) return fail(Numeric2C39B80InputFailureV1::exact_build);
  if (!access.read_memory) return fail(Numeric2C39B80InputFailureV1::read_callback);
  std::int32_t observed_id = -1;
  if (expected_province_id <= 0 || !ReadOffsetV1(access, province, 0x10, observed_id) ||
      observed_id != expected_province_id)
    return fail(Numeric2C39B80InputFailureV1::province_identity);
  if (!AddOffsetV1(province, 0x620, result.slots_pointer) ||
      !ReadOffsetV1(access, result.slots_pointer, 0xF0, result.context_pointer) ||
      result.context_pointer == 0)
    return fail(Numeric2C39B80InputFailureV1::context);
  // A copied null receiver is retained. The separately source-owned child
  // defines its null behavior; this parent reader does not substitute one.
  if (!ReadOffsetV1(access, result.context_pointer, 0x848, result.receiver_pointer))
    return fail(Numeric2C39B80InputFailureV1::receiver_read);
  if (!AddOffsetV1(image_base, kConstructionNumeric2C39B80ScalarRva12004,
                   result.scalar_address))
    return fail(Numeric2C39B80InputFailureV1::image_base);
  std::int64_t scalar = 0;
  if (!ReadOffsetV1(access, image_base, kConstructionNumeric2C39B80ScalarRva12004, scalar))
    return fail(Numeric2C39B80InputFailureV1::scalar_read);
  result.scalar_raw = scalar;
  std::uintptr_t after_context = 0, after_receiver = 0;
  std::int64_t after_scalar = 0;
  if (!ReadOffsetV1(access, province, 0x10, observed_id) ||
      observed_id != expected_province_id ||
      !ReadOffsetV1(access, result.slots_pointer, 0xF0, after_context) ||
      after_context != result.context_pointer ||
      !ReadOffsetV1(access, result.context_pointer, 0x848, after_receiver) ||
      after_receiver != result.receiver_pointer ||
      !ReadOffsetV1(access, image_base, kConstructionNumeric2C39B80ScalarRva12004, after_scalar) ||
      after_scalar != scalar)
    return fail(Numeric2C39B80InputFailureV1::source_changed);
  result.observed = true;
  return result;
}

struct Numeric2C39B80ArithmeticV1 {
  std::int32_t child_signed32_raw = 0;
  std::int64_t scalar_signed64_raw = 0, child_scaled100000_raw = 0;
  std::int64_t first_stage_raw = 0, second_stage_raw = 0, output_raw = 0;
  bool second_stage_slow = false;
};

// Conditional copied-input arithmetic only. The caller must independently
// qualify the24CEF10 child source, same receiver/context/frame and exact pin.
// No native getter, constructor, publisher or direct helper call is made.
inline Numeric2C39B80ArithmeticV1 EvaluateNumericHelper2C39B80V1(
    std::int32_t child_signed32, std::int64_t scalar_signed64) noexcept {
  Numeric2C39B80ArithmeticV1 result;
  result.child_signed32_raw = child_signed32;
  result.scalar_signed64_raw = scalar_signed64;
  result.child_scaled100000_raw = static_cast<std::int64_t>(child_signed32) * 100000;
  result.first_stage_raw = SignedScaleProduct100000V1(
      result.child_scaled100000_raw, scalar_signed64);
  constexpr std::int64_t bound = 0x53E2D6238DA3LL;
  constexpr std::int64_t scale = 100000, divisor = 10000000;
  const auto input = result.first_stage_raw;
  if (input >= -bound && input <= bound) {
    result.second_stage_raw = (input * scale) / divisor;
  } else {
    result.second_stage_slow = true;
    // Literal2C39C85..2C39D19 decomposition. Each division truncates toward
    // zero; preserve its intermediate order rather than fusing scales.
    const auto scaled_quotient = WrappedProductV1(input / scale, scale);
    const auto remainder = SignedBitsV1(static_cast<std::uint64_t>(input) -
                                       static_cast<std::uint64_t>(scaled_quotient));
    const auto whole = scaled_quotient / divisor;
    const auto whole_remainder = SignedBitsV1(static_cast<std::uint64_t>(scaled_quotient) -
        static_cast<std::uint64_t>(WrappedProductV1(whole, divisor)));
    const auto remainder_scaled_divided = WrappedProductV1(remainder, scale) / divisor;
    const auto whole_remainder_scaled_divided = WrappedProductV1(whole_remainder, scale) / divisor;
    result.second_stage_raw = SignedBitsV1(
        static_cast<std::uint64_t>(WrappedProductV1(whole, scale)) +
        static_cast<std::uint64_t>(remainder_scaled_divided) +
        static_cast<std::uint64_t>(whole_remainder_scaled_divided));
  }
  result.output_raw = SignedBitsV1(
      static_cast<std::uint64_t>(result.second_stage_raw) + scale);
  return result;
}

enum class Numeric2C39B80ObservationFailureV1 : std::uint8_t {
  none, parent_inputs, child_inputs, child_provenance, source_changed,
};

struct ConstructionNumericHelper2C39B80ObservationV1 {
  bool observed = false;
  Numeric2C39B80ObservationFailureV1 failure = Numeric2C39B80ObservationFailureV1::none;
  LoadedNumeric2C39B80InputsV1 inputs_before;
  ConstructionNumericChild24CEF10ObservationV1 child;
  LoadedNumeric2C39B80InputsV1 inputs_after_child;
  std::optional<Numeric2C39B80ArithmeticV1> conditional_arithmetic;
  bool actual_original_consumed_values = false;
};

// Direct reuse of the separately source-owned readonly24CEF10 reader. The
// parent does not reread38C itself or bypass the child's bit35/fallback gate.
inline ConstructionNumericHelper2C39B80ObservationV1 ReadConstructionNumericHelper2C39B80V1(
    const LoadedInputAccessV1 &access, std::uintptr_t province,
    std::int32_t expected_province_id, std::uintptr_t image_base,
    std::uint64_t frame_key) {
  ConstructionNumericHelper2C39B80ObservationV1 result;
  const auto fail = [&](Numeric2C39B80ObservationFailureV1 failure) {
    result.failure = failure;
    result.observed = false;
    return result;
  };
  result.inputs_before = ReadLoadedNumericHelper2C39B80InputsV1(
      access, province, expected_province_id, image_base, frame_key);
  if (!result.inputs_before.observed)
    return fail(Numeric2C39B80ObservationFailureV1::parent_inputs);
  result.child = ReadConstructionNumericChild24CEF10V1(
      access, image_base, result.inputs_before.receiver_pointer, frame_key);
  if (!result.child.observed || !result.child.eax_signed_i32)
    return fail(Numeric2C39B80ObservationFailureV1::child_inputs);
  if (result.child.source_pin != result.inputs_before.source_pin ||
      result.child.frame_key != result.inputs_before.frame_key ||
      result.child.receiver_pointer != result.inputs_before.receiver_pointer)
    return fail(Numeric2C39B80ObservationFailureV1::child_provenance);
  result.inputs_after_child = ReadLoadedNumericHelper2C39B80InputsV1(
      access, province, expected_province_id, image_base, frame_key);
  const auto &before = result.inputs_before;
  const auto &after = result.inputs_after_child;
  if (!after.observed || after.source_pin != before.source_pin ||
      after.frame_key != before.frame_key || after.province_id != before.province_id ||
      after.province_pointer != before.province_pointer ||
      after.slots_pointer != before.slots_pointer ||
      after.context_pointer != before.context_pointer ||
      after.receiver_pointer != before.receiver_pointer ||
      after.image_base != before.image_base || after.scalar_address != before.scalar_address ||
      after.scalar_raw != before.scalar_raw)
    return fail(Numeric2C39B80ObservationFailureV1::source_changed);
  result.conditional_arithmetic = EvaluateNumericHelper2C39B80V1(
      *result.child.eax_signed_i32, *before.scalar_raw);
  result.observed = true;
  return result;
}

void VerifyConstructionNumericHelper2C39B80OwnedCases12004();
} // namespace xar::ck3_12004::construction_owner_mode3
