#pragma once

#include "xar_bridge/ck3_12002_family_value.hpp"
#include "xar_bridge/conception_modifier_context_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

// These are the concrete first-role provider inputs, not a couple probability,
// conception date, pregnancy state or a renamed Character fertility value.
struct ConceptionFirstValue12004Inputs {
  std::int64_t seed_raw = 0;
  std::int32_t children_count_raw = 0;
  std::int64_t per_child_decrement_raw = 0;
  std::int16_t age_raw = 0;
  std::int16_t age_override_raw = -1;
  std::int64_t modifier_bf_raw = 0;
  std::int32_t age_threshold_count_low32 = 0;
  // Only thresholds actually consumed up to the selected native band.
  std::vector<std::int32_t> age_threshold_prefix;
  std::int32_t sampled_age_band_index = 0;
  std::int64_t selected_age_multiplier_raw = 0;
  bool final_multiplier_applies = false;
  std::optional<std::int64_t> final_multiplier_raw;
};

struct ConceptionFirstValue12004Read {
  std::string_view source = "native_conception_first_value";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "native_conception_first_inputs_unavailable";
  std::optional<std::int64_t> seed_after_children_raw;
  std::optional<std::int32_t> adjusted_age_raw;
  std::optional<std::int32_t> selected_age_band_index;
  std::optional<std::int64_t> age_product_raw;
  std::optional<std::int64_t> first_output_raw;
};

// Caller passes a complete observed input object; nullopt means unread input,
// whereas zero and negative output qwords are valid observed numerical values.
ConceptionFirstValue12004Read EvaluateConceptionFirstValue12004(
    const std::optional<ConceptionFirstValue12004Inputs> &inputs) noexcept;

using ConceptionFirstValue12004ReadMemory = bool (*)(
    void *context, const void *address, void *output, std::size_t size) noexcept;

struct ConceptionFirstValue12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionFirstValue12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

ConceptionFirstValue12004Bindings BindConceptionFirstValue12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base, ConceptionFirstValue12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Root owns the same-frame current household/full-ID join. The qualified
// actual4 Family value supplies seed and age, avoiding another native gate
// call. All additional accesses use the read callback. No lazy modifier getter
// or original provider is invoked. The owned model branch is supported; the
// default model initialization branch remains an explicit unavailable result.
std::optional<ConceptionFirstValue12004Inputs>
ReadConceptionFirstValueInputsForCharacter12004(
    const ConceptionFirstValue12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id,
    const ck3_12002::family_value::CharacterValue &current_value,
    std::string_view *reason = nullptr);

// Same-query increment: the shared resolver selects the actual owned/default
// branch and proves current default storage alive. Read actual BF fields, then
// recheck the shared observation before accepting first-specific inputs.
std::optional<ConceptionFirstValue12004Inputs>
ReadConceptionFirstValueInputsWithModifierContext12004(
    const ConceptionFirstValue12004Bindings &bindings,
    const ConceptionModifierContextBindings12004 &modifier_bindings,
    std::uintptr_t character, std::uint32_t expected_full_id,
    const ck3_12002::family_value::CharacterValue &current_value,
    const ConceptionModifierContextObservation12004 &modifier_context,
    std::string_view *reason = nullptr);

} // namespace xar::ck3_12004
