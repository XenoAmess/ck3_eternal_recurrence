#pragma once
#include "xar_bridge/conception_value_arithmetic_12004.hpp"
#include "xar_bridge/conception_modifier_context_12004.hpp"
#include "xar_bridge/ck3_12002_family_value.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kConceptionSecondThresholdCount12004 = 0x545FD64;
inline constexpr std::uintptr_t kConceptionSecondThresholdPointer12004 = 0x545FD58;
inline constexpr std::uintptr_t kConceptionSecondMultiplierPointer12004 = 0x545FE08;
inline constexpr std::uintptr_t kConceptionFinalConditionalFactor12004 = 0x5C69E10;

struct ConceptionSecondValueInputs12004 {
  std::int64_t fertility_seed_raw = 0;
  std::int16_t selected_age_raw = 0;
  std::int64_t modifier_bf_raw = 0;
  ConceptionModifierContextObservation12004 modifier_context;
  std::int32_t threshold_count_raw = 0;
  // Original native order, ending at first matching threshold or at count.
  std::vector<std::int32_t> thresholds_prefix;
  std::int32_t selected_band_index = 0;
  std::int64_t selected_multiplier_raw = 0;
  bool extension_1b0_present = false;
  bool pointer_1b8_present = false;
  bool pointer_1c0_present = false;
  bool pointer_1c8_present = false;
  std::optional<std::int64_t> conditional_final_factor_raw;
};

struct ConceptionSecondValue12004 {
  bool ready = false;
  std::string reason;
  std::optional<std::int32_t> adjusted_age_raw;
  std::optional<std::int32_t> selected_band_index;
  std::optional<std::int64_t> prefinal_raw;
  std::optional<std::int64_t> value_raw;
};

ConceptionSecondValue12004 ComputeConceptionSecondValue12004(
    const ConceptionSecondValueInputs12004 &input);

using ConceptionSecondValueRead12004 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t bytes) noexcept;
struct ConceptionSecondValueBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionSecondValueRead12004 read_memory = nullptr;
  void *read_context = nullptr;
  // Observer copy budget; exceeding it is explicit unavailable, never zero.
  std::uint32_t age_threshold_read_budget = 1024;
};

ConceptionSecondValueBindings12004 BindConceptionSecondValue12004(
    std::uintptr_t module_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionSecondValueRead12004 read_memory,
    void *read_context = nullptr) noexcept;

// Root supplies the independently generation-resolved, same-frame Character
// and existing actual4 Family fertility seed. This function calls no getter,
// gate, lazy initializer or native value writer. Owned and initialized-default
// contexts use the shared resolver and are rechecked before publication.
bool ReadConceptionSecondValueInputs12004(
    const ConceptionSecondValueBindings12004 &bindings,
    std::uintptr_t actual_character, std::int32_t expected_full_character_id,
    const ck3_12002::family_value::FertilityRead &seed,
    ConceptionSecondValueInputs12004 &output, std::string &reason);
} // namespace xar::ck3_12004
