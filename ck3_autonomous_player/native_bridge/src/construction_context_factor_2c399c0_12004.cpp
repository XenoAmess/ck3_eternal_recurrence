#include "xar_bridge/construction_context_factor_2c399c0_12004.hpp"

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
std::int64_t WrappedAdd(std::int64_t first, std::int64_t second) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(first) +
                      static_cast<std::uint64_t>(second));
}
std::int64_t WrappedSubtract(std::int64_t first, std::int64_t second) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(first) -
                      static_cast<std::uint64_t>(second));
}
bool FastFirst(std::int64_t value) noexcept {
  return static_cast<std::uint64_t>(value) + UINT64_C(0xB504F333) <=
      UINT64_C(0x16A09E666);
}
ContextFactorSecondScaleTraceV1 SecondScale(std::int64_t value) noexcept {
  ContextFactorSecondScaleTraceV1 trace{};
  trace.input_raw = value;
  if (static_cast<std::uint64_t>(value) + UINT64_C(0x53E2D6238DA3) <=
      UINT64_C(0xA7C5AC471B46)) {
    trace.path = "native_fast64";
    trace.fast_product_raw = WrappedProductV1(value, INT64_C(100000));
    // Actual negative reciprocal signed-high/ADD/SAR23/sign correction is
    // the exact signed quotient by10000000, truncated toward zero.
    trace.result_raw = *trace.fast_product_raw / INT64_C(10000000);
    return trace;
  }
  trace.path = "native_decomposed64";
  const auto quotient = value / INT64_C(100000);
  const auto whole = WrappedProductV1(quotient, INT64_C(100000));
  const auto remainder = WrappedSubtract(value, whole);
  const auto whole_quotient = whole / INT64_C(10000000);
  const auto whole_remainder = WrappedSubtract(whole,
      WrappedProductV1(whole_quotient, INT64_C(10000000)));
  const auto fractional_product = WrappedProductV1(remainder, INT64_C(100000));
  const auto fractional_quotient = fractional_product / INT64_C(10000000);
  const auto whole_remainder_product =
      WrappedProductV1(whole_remainder, INT64_C(100000));
  const auto whole_remainder_quotient =
      whole_remainder_product / INT64_C(10000000);
  const auto result_whole = WrappedProductV1(whole_quotient, INT64_C(100000));
  trace.quotient_100000_raw = quotient;
  trace.whole_product_raw = whole;
  trace.remainder_100000_raw = remainder;
  trace.whole_quotient_10000000_raw = whole_quotient;
  trace.whole_remainder_10000000_raw = whole_remainder;
  trace.fractional_product_raw = fractional_product;
  trace.fractional_quotient_raw = fractional_quotient;
  trace.whole_remainder_product_raw = whole_remainder_product;
  trace.whole_remainder_quotient_raw = whole_remainder_quotient;
  trace.result_whole_product_raw = result_whole;
  trace.result_raw = WrappedAdd(WrappedAdd(result_whole, fractional_quotient),
                               whole_remainder_quotient);
  return trace;
}
} // namespace

LoadedContextFactor2C399C0InputsV1 ReadContextFactor2C399C0InputsV1(
    const LoadedInputAccessV1 &access, std::uintptr_t image_base,
    std::uintptr_t context, std::uint64_t frame_key) noexcept {
  LoadedContextFactor2C399C0InputsV1 inputs{};
  inputs.context_pointer = context;
  inputs.image_base = image_base;
  inputs.frame_key = frame_key;
  const auto fail = [&](ContextFactor2C399C0FailureV1 failure) {
    inputs.failure = failure;
    return inputs;
  };
  if (!access.exact_12004_bound) return fail(ContextFactor2C399C0FailureV1::exact_build);
  if (frame_key == 0) return fail(ContextFactor2C399C0FailureV1::frame_key);
  if (access.read_memory == nullptr) return fail(ContextFactor2C399C0FailureV1::read_callback);
  if (context == 0) return fail(ContextFactor2C399C0FailureV1::context_pointer);
  if (!AddOffsetV1(image_base, kContextFactorLoadedSlotRvaV1, inputs.loaded_slot_address))
    return fail(ContextFactor2C399C0FailureV1::global_read);
  if (!ReadOffsetV1(access, context, 0x848, inputs.context_object))
    return fail(ContextFactor2C399C0FailureV1::object_read);
  std::int64_t loaded = 0;
  if (!ReadOffsetV1(access, image_base, kContextFactorLoadedSlotRvaV1, loaded))
    return fail(ContextFactor2C399C0FailureV1::global_read);
  inputs.loaded_qword_raw = loaded;
  std::uintptr_t after_object = 0;
  std::int64_t after_loaded = 0;
  if (!ReadOffsetV1(access, context, 0x848, after_object) ||
      !ReadOffsetV1(access, image_base, kContextFactorLoadedSlotRvaV1, after_loaded) ||
      after_object != inputs.context_object || after_loaded != loaded)
    return fail(ContextFactor2C399C0FailureV1::source_changed);
  inputs.source_ready = true;
  return inputs;
}

ContextFactor2C399C0ObservationV1 EvaluateContextFactor2C399C0V1(
    const LoadedContextFactor2C399C0InputsV1 &inputs,
    const ContextFactorProviderFirstQwordV1 &provider) noexcept {
  ContextFactor2C399C0ObservationV1 output{};
  output.frame_key = inputs.frame_key;
  output.context_object = inputs.context_object;
  output.loaded_slot_address = inputs.loaded_slot_address;
  const auto fail = [&](ContextFactor2C399C0FailureV1 failure) {
    output.failure = failure;
    return output;
  };
  if (inputs.source_pin != kContextFactor2C399C0SourcePinV1)
    return fail(ContextFactor2C399C0FailureV1::exact_build);
  if (!inputs.source_ready || !inputs.loaded_qword_raw)
    return fail(inputs.failure == ContextFactor2C399C0FailureV1::none
        ? ContextFactor2C399C0FailureV1::global_read : inputs.failure);
  if (inputs.frame_key == 0) return fail(ContextFactor2C399C0FailureV1::frame_key);
  std::uintptr_t expected_slot = 0;
  if (!AddOffsetV1(inputs.image_base, kContextFactorLoadedSlotRvaV1, expected_slot) ||
      inputs.loaded_slot_address != expected_slot)
    return fail(ContextFactor2C399C0FailureV1::global_read);
  output.loaded_qword_raw = inputs.loaded_qword_raw;
  if (!provider.source_ready || !provider.first_qword_raw)
    return fail(ContextFactor2C399C0FailureV1::provider_unavailable);
  if (provider.source_pin != inputs.source_pin)
    return fail(ContextFactor2C399C0FailureV1::provider_source_pin);
  if (provider.frame_key != inputs.frame_key ||
      provider.context_object != inputs.context_object)
    return fail(ContextFactor2C399C0FailureV1::provider_binding);
  const auto first = *provider.first_qword_raw;
  const auto loaded = *inputs.loaded_qword_raw;
  const auto difference = WrappedSubtract(INT64_C(100000), loaded);
  output.first_child_qword_raw = first;
  output.difference_100000_raw = difference;
  output.first_scale_path = FastFirst(first) && FastFirst(difference)
      ? "native_fast64" : "native_minmax_wrap64";
  output.first_scaled_raw = SignedScaleProduct100000V1(first, difference);
  output.second_scale = SecondScale(*output.first_scaled_raw);
  output.factor_qword_raw = WrappedAdd(output.second_scale->result_raw, loaded);
  output.observed = true;
  return output;
}
} // namespace xar::ck3_12004::construction_owner_mode3
