#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kConstructionOwnerFactorRva12004 = 0x2B9CBA0;
inline constexpr std::uintptr_t kConstructionOwnerFactorSelectorRva12004 = 0x28C2DF0;
inline constexpr std::uintptr_t kConstructionOwnerFactorScopeRva12004 = 0xB17C70;
inline constexpr std::uintptr_t kConstructionOwnerFactorModifierRva12004 = 0xC86670;
inline constexpr std::size_t kConstructionOwnerFactorSelectorByteOffset12004 = 0x4D6;
inline constexpr std::uint32_t kConstructionOwnerFactorModifierIndex12004 = 0x4E;

// A copied actual source binding from the current admitted .4 frame. The owner
// supplies the source-closed selector result; this leaf never invokes a getter.
struct ConstructionOwnerFactorBinding12004 {
  std::uintptr_t input_receiver = 0;
  std::uintptr_t selector_result_object = 0;
  std::uint64_t frame_key = 0;
  bool source_ready = false;
};

// A source-closed, already computed/captured signed Q64 from index 4E with the
// B17C70-equivalent actor context for this exact receiver and frame. A native
// return alone and a guessed zero do not admit this packet.
struct ConstructionOwnerModifier4EInput12004 {
  std::uintptr_t context_receiver = 0;
  std::uint64_t frame_key = 0;
  std::uint32_t modifier_index = kConstructionOwnerFactorModifierIndex12004;
  std::optional<std::int64_t> returned_q64;
  bool source_ready = false;
};

struct ConstructionOwnerFactorInputs12004 {
  ConstructionOwnerFactorBinding12004 binding;
  std::optional<std::uint8_t> selector_byte_4d6;
  std::optional<ConstructionOwnerModifier4EInput12004> modifier_4e;
};

struct ConstructionOwnerFactorResult12004 {
  ConstructionOwnerFactorBinding12004 binding;
  std::optional<std::uint8_t> selector_byte_4d6;
  std::optional<std::int64_t> modifier_4e_returned_q64;
  std::optional<std::int64_t> factor_raw;
  bool modifier_branch_taken = false;
  std::string_view unavailable_reason;
};

using ConstructionOwnerFactorReadBytes12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

// Copies exactly the one byte consumed at actual 2B9CBDC. The selected object
// must already have been resolved by its separately owned readonly source.
inline ConstructionOwnerFactorInputs12004 ReadConstructionOwnerFactorInputs12004(
    const ConstructionOwnerFactorBinding12004 &binding,
    ConstructionOwnerFactorReadBytes12004 read_bytes, void *read_context,
    const std::optional<ConstructionOwnerModifier4EInput12004> &modifier_4e =
        std::nullopt) noexcept {
  ConstructionOwnerFactorInputs12004 out;
  out.binding = binding;
  out.modifier_4e = modifier_4e;
  if (!binding.source_ready || !binding.input_receiver ||
      !binding.selector_result_object || !read_bytes ||
      binding.selector_result_object >
          std::numeric_limits<std::uintptr_t>::max() -
              kConstructionOwnerFactorSelectorByteOffset12004)
    return out;
  std::uint8_t raw = 0;
  if (read_bytes(read_context,
                 binding.selector_result_object +
                     kConstructionOwnerFactorSelectorByteOffset12004,
                 &raw, sizeof(raw)))
    out.selector_byte_4d6 = raw;
  return out;
}

// Actual 2B9CBA0 with the caller's fifth detail argument NULL. The byte!=5
// branch does not construct/evaluate a context and remains available without
// any modifier supplier. Only byte==5 depends on the same-frame 4E packet.
inline ConstructionOwnerFactorResult12004 EvaluateNullDetailFactor12004(
    const ConstructionOwnerFactorInputs12004 &inputs) noexcept {
  ConstructionOwnerFactorResult12004 out;
  out.binding = inputs.binding;
  out.selector_byte_4d6 = inputs.selector_byte_4d6;
  if (!inputs.binding.source_ready || !inputs.binding.input_receiver ||
      !inputs.binding.selector_result_object) {
    out.unavailable_reason = "actual_receiver_selector_source_unavailable";
    return out;
  }
  if (!inputs.selector_byte_4d6) {
    out.unavailable_reason = "selector_byte_4d6_unavailable";
    return out;
  }
  if (*inputs.selector_byte_4d6 != 5) {
    out.factor_raw = 100000; // Actual 2B9CBE5 stores signed Q64 0x186A0.
    return out;
  }
  out.modifier_branch_taken = true;
  if (!inputs.modifier_4e || !inputs.modifier_4e->source_ready ||
      !inputs.modifier_4e->returned_q64) {
    out.unavailable_reason = "actual_context_modifier_4e_source_unavailable";
    return out;
  }
  const auto &modifier = *inputs.modifier_4e;
  out.modifier_4e_returned_q64 = modifier.returned_q64;
  if (modifier.context_receiver != inputs.binding.input_receiver ||
      modifier.frame_key != inputs.binding.frame_key ||
      modifier.modifier_index != kConstructionOwnerFactorModifierIndex12004) {
    out.unavailable_reason = "actual_context_modifier_4e_binding_mismatch";
    return out;
  }
  const auto raw = *modifier.returned_q64;
  out.factor_raw = raw >= 0 ? raw : 0; // Actual signed CMP + CMOVGE.
  return out;
}

} // namespace xar::ck3_12004
