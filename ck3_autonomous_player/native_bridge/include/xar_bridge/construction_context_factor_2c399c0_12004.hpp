#pragma once

#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"

#include <optional>
#include <string_view>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kContextFactor2C399C0SourcePinV1 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uintptr_t kContextFactorLoadedSlotRvaV1 = 0x5C69440;

enum class ContextFactor2C399C0FailureV1 : std::uint8_t {
  none, exact_build, frame_key, read_callback, context_pointer,
  object_read, global_read, source_changed, provider_unavailable,
  provider_binding, provider_source_pin,
};

struct LoadedContextFactor2C399C0InputsV1 {
  bool source_ready = false;
  ContextFactor2C399C0FailureV1 failure = ContextFactor2C399C0FailureV1::none;
  std::string_view source_pin = kContextFactor2C399C0SourcePinV1;
  // Original CampaignRootFrameV1::snapshot_revision. Do not hash/re-encode.
  std::uint64_t frame_key = 0;
  std::uintptr_t context_pointer = 0, context_object = 0;
  std::uintptr_t image_base = 0, loaded_slot_address = 0;
  std::optional<std::int64_t> loaded_qword_raw;
};

//30d owns the actual24D3260 raw source. A copied output is qualified by
//that owner, then joined to this source context and unchanged frame.
struct ContextFactorProviderFirstQwordV1 {
  bool source_ready = false;
  std::string_view source_pin{};
  std::uint64_t frame_key = 0;
  std::uintptr_t context_object = 0;
  std::optional<std::int64_t> first_qword_raw;
};

struct ContextFactorSecondScaleTraceV1 {
  std::string_view path{}; // native_fast64 or native_decomposed64.
  std::int64_t input_raw = 0, result_raw = 0;
  std::optional<std::int64_t> fast_product_raw;
  std::optional<std::int64_t> quotient_100000_raw, whole_product_raw;
  std::optional<std::int64_t> remainder_100000_raw;
  std::optional<std::int64_t> whole_quotient_10000000_raw;
  std::optional<std::int64_t> whole_remainder_10000000_raw;
  std::optional<std::int64_t> fractional_product_raw, fractional_quotient_raw;
  std::optional<std::int64_t> whole_remainder_product_raw;
  std::optional<std::int64_t> whole_remainder_quotient_raw, result_whole_product_raw;
};

struct ContextFactor2C399C0ObservationV1 {
  bool observed = false;
  ContextFactor2C399C0FailureV1 failure = ContextFactor2C399C0FailureV1::none;
  std::uint64_t frame_key = 0;
  std::uintptr_t context_object = 0, loaded_slot_address = 0;
  std::optional<std::int64_t> first_child_qword_raw, loaded_qword_raw;
  std::optional<std::int64_t> difference_100000_raw, first_scaled_raw;
  std::string_view first_scale_path{};
  std::optional<ContextFactorSecondScaleTraceV1> second_scale;
  std::optional<std::int64_t> factor_qword_raw;
};

// Already-qualified same-frame context supplied by03. This reader copies
// only context+848 and module5C69440, retaining unknown distinct from zero.
LoadedContextFactor2C399C0InputsV1 ReadContextFactor2C399C0InputsV1(
    const LoadedInputAccessV1 &, std::uintptr_t image_base,
    std::uintptr_t already_qualified_context, std::uint64_t frame_key) noexcept;

// Pure copied-input projection. No getter, initializer, native call or tax name.
ContextFactor2C399C0ObservationV1 EvaluateContextFactor2C399C0V1(
    const LoadedContextFactor2C399C0InputsV1 &,
    const ContextFactorProviderFirstQwordV1 &) noexcept;

// Called once only by03/10's new connected compound; no standalone main.
void VerifyContextFactor2C399C0ConnectedCasesV1();

} // namespace xar::ck3_12004::construction_owner_mode3
