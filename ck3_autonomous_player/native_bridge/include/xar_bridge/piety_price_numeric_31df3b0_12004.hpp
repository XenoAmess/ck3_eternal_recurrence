#pragma once

#include "xar_bridge/piety_price_evaluator_1233a40_readonly_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::construction_owner_mode3 {
struct RawReceiverAccessV1;
}

namespace xar::ck3_12004::piety_price_raw_inputs {

inline constexpr std::string_view kPietyPrice31DF3B0SourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::size_t kPietyPrice31DF3B0ExpressionOffset12004 = 0x2A8;

using Numeric31DF3B0Bindings12004 = PietyPriceNumericAccess12004;

inline Numeric31DF3B0Bindings12004 BindPietyPriceNumeric31DF3B012004(
    std::uintptr_t module_base, std::string_view held_executable_sha256,
    bool (*guarded_read)(void*, const void*, void*, std::size_t) noexcept,
    void* context) noexcept {
  return {module_base, context, guarded_read,
          guarded_read != nullptr &&
              held_executable_sha256 == kPietyPrice31DF3B0SourcePin12004};
}

struct Numeric31DF3B0Observation12004 {
  bool source_ready = false;
  const char* status = "unavailable";
  std::string reason = "not_read";
  std::uintptr_t definition_pointer = 0;
  std::uintptr_t current_rite_pointer = 0;
  std::uint64_t frame_key = 0;
  std::string_view source_pin = kPietyPrice31DF3B0SourcePin12004;
  std::optional<std::uintptr_t> selected_expression_identity;
  std::optional<std::int32_t> native_eax_raw;
  std::optional<PietyPriceEvaluator1233A40Readonly12004> copied_diagnostics;
  bool actual_original_consumed_values = false;
};

// Actual31DF3C5 selects definition+2A8. Unique11/40 retain the reached
// numeric dependency and its operand coherence. Rite and revision are full
// identity carriers; mode0 does not invent a context or name prerequisite.
Numeric31DF3B0Observation12004 ReadPietyPriceNumeric31DF3B012004(
    const Numeric31DF3B0Bindings12004& bindings, std::uintptr_t definition,
    std::uintptr_t current_rite, std::uint64_t unchanged_snapshot_revision);

// The actual alternate price consumer uses this source-model callback.
// Context is unused. False leaves native_eax_raw unchanged, including when
// the required raw source is absent or a reached dynamic mode is unknown.
bool ReadPietyPriceNumeric31DF3B0Adapter12004(
    void* context,
    const construction_owner_mode3::RawReceiverAccessV1& access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision,
    std::int32_t& native_eax_raw) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
