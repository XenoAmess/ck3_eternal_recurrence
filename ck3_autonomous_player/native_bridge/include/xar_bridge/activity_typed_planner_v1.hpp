#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string_view>

namespace xar::bridge {

// A finite NEW software contract. Existing Feast entry points and their
// authorization do not acquire this activity by including this header.
enum class ActivityTypedPlannerKindV1 : std::uint8_t {
  ordinary_pilgrimage_pious = 1,
};

struct ActivityTypedPlannerContractV1 {
  ActivityTypedPlannerKindV1 kind{};
  std::string_view activity_key{};
  std::string_view special_option_key{};
  std::int32_t predefined_phase_count = 0;
};

inline constexpr ActivityTypedPlannerContractV1
    kOrdinaryPilgrimagePiousContractV1{
        ActivityTypedPlannerKindV1::ordinary_pilgrimage_pious,
        "activity_pilgrimage", "pilgrimage_type_pious", 1};

inline bool IsOrdinaryPilgrimagePiousContractV1(
    const ActivityTypedPlannerContractV1 &contract) noexcept {
  const auto &allowed = kOrdinaryPilgrimagePiousContractV1;
  return contract.kind == allowed.kind &&
         contract.activity_key == allowed.activity_key &&
         contract.special_option_key == allowed.special_option_key &&
         contract.predefined_phase_count == allowed.predefined_phase_count;
}

namespace activity_typed_planner_detail_v1 {
template <class T>
inline bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
                   std::uintptr_t base, std::size_t offset,
                   T &value) noexcept {
  return base != 0 && environment.read_memory != nullptr &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         environment.read_memory(environment.context, base + offset,
                                 &value, sizeof(value));
}
} // namespace activity_typed_planner_detail_v1

// The type-vtable operand is already bound by the actual .4 religion addon
// (0x48BFE60); it is an argument so callers reuse their exact profile operand.
// This helper admits ONLY that .4 operand, not an arbitrary caller vtable.
// Native thread, frame, planner and owner checks remain mandatory in callers.
inline bool MatchesActivityTypedPlannerTypeV1(
    const ActivityPlannerDiagEnvironmentV1 &environment,
    std::uintptr_t type, std::uintptr_t expected_type_vtable_rva,
    const ActivityTypedPlannerContractV1 &contract) noexcept {
  using activity_typed_planner_detail_v1::ReadAt;
  if (!environment.enabled ||
      !IsActivity12004BuildV1(environment.admitted_executable_sha256) ||
      !IsOrdinaryPilgrimagePiousContractV1(contract) ||
      environment.module_base == 0 || expected_type_vtable_rva != 0x48BFE60 ||
      expected_type_vtable_rva >
          (std::numeric_limits<std::uintptr_t>::max)() - environment.module_base)
    return false;
  std::uintptr_t vtable = 0, data = 0;
  std::uint64_t length = 0, capacity = 0;
  if (!ReadAt(environment, type, 0, vtable) ||
      vtable != environment.module_base + expected_type_vtable_rva ||
      !ReadAt(environment, type, 0x28, length) ||
      !ReadAt(environment, type, 0x30, capacity) ||
      length != contract.activity_key.size() || length > capacity ||
      length >= 64)
    return false;
  if (capacity > 15) {
    if (!ReadAt(environment, type, 0x18, data) || data == 0) return false;
  } else {
    if (type > (std::numeric_limits<std::uintptr_t>::max)() - 0x18)
      return false;
    data = type + 0x18;
  }
  std::array<char, 64> observed{};
  return environment.read_memory(environment.context, data, observed.data(),
                                 static_cast<std::size_t>(length)) &&
         std::memcmp(observed.data(), contract.activity_key.data(),
                     static_cast<std::size_t>(length)) == 0;
}

inline bool MatchesActivityTypedPlannerHostKeyV1(
    const ActivityPlannerDiagValueV1 &value,
    const ActivityTypedPlannerContractV1 &contract) noexcept {
  return IsOrdinaryPilgrimagePiousContractV1(contract) &&
         value.host_view_activity_key_known &&
         value.host_view_activity_key_size < value.host_view_activity_key.size() &&
         std::string_view(value.host_view_activity_key.data(),
                          value.host_view_activity_key_size) == contract.activity_key;
}

// Produced from the native selected-option getter plus identifier resolution,
// bracketed by identical planner/type/frame observations. A requested key is
// never evidence of the selected key. Producer supports the observed stage;
// cost/Start consumers require stage five explicitly.
struct ActivityTypedPlannerSelectionV1 {
  bool observed = false;
  ActivityTypedPlannerKindV1 kind{};
  ActivityPlannerDiagFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t planning_stage = -1;
  std::uintptr_t native_selected_option = 0;
  std::int32_t native_option_id = -1;
  std::array<char, 96> option_key{};
  std::uint16_t option_key_size = 0;

  friend bool operator==(const ActivityTypedPlannerSelectionV1 &,
                         const ActivityTypedPlannerSelectionV1 &) = default;
};

inline bool MatchesActivityTypedPlannerSelectionV1(
    const ActivityTypedPlannerSelectionV1 &selection,
    const ActivityPlannerDiagFrameV1 &frame, std::uintptr_t planner,
    std::uintptr_t activity_type, std::int32_t required_stage,
    const ActivityTypedPlannerContractV1 &contract) noexcept {
  return IsOrdinaryPilgrimagePiousContractV1(contract) && selection.observed &&
         selection.kind == contract.kind && selection.frame == frame &&
         planner != 0 && selection.planner == planner && activity_type != 0 &&
         selection.activity_type == activity_type &&
         required_stage >= 1 && required_stage <= 5 &&
         selection.planning_stage == required_stage &&
         selection.native_selected_option != 0 && selection.native_option_id >= 0 &&
         selection.option_key_size < selection.option_key.size() &&
         std::string_view(selection.option_key.data(), selection.option_key_size) ==
             contract.special_option_key;
}

using ActivityTypedPlannerReadSelectionV1 = bool (*)(
    void *, const ActivityPlannerDiagFrameV1 &, std::int32_t required_stage,
    ActivityTypedPlannerSelectionV1 &) noexcept;

// Native single predefined-row configuration, read in the current planner.
// A successful Select call alone is not a current destination observation.
struct ActivityTypedPlannerDestinationV1 {
  bool observed = false;
  ActivityTypedPlannerKindV1 kind{};
  ActivityPlannerDiagFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t planning_stage = -1;
  std::int32_t predefined_phase_count = 0;
  std::uint32_t province_id = 0;

  friend bool operator==(const ActivityTypedPlannerDestinationV1 &,
                         const ActivityTypedPlannerDestinationV1 &) = default;
};

// Existing named getter proves these FOUR names only. Their native resource
// indexes are dynamic; no index (including gold) is assumed to be zero.
inline constexpr std::array<std::string_view, 4>
    kActivityTypedPlannerKnownCostNamesV1{
        "gold", "treasury", "piety", "barter_goods"};

struct ActivityTypedPlannerCostQuoteV1 {
  bool observed = false;
  ActivityTypedPlannerKindV1 kind{};
  ActivityPlannerDiagFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t owner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t planning_stage = -1;
  std::uint64_t normal_refresh_sequence = 0;
  std::uint64_t configuration_fingerprint = 0;
  ActivityTypedPlannerSelectionV1 selection{};
  // Configured totals are the ten indexed slots consumed by native GetCost.
  // They are NOT passive-observer raw_aggregate's per-resource subtotal rows.
  std::array<std::int64_t, 10> configured_cost_raw{};
  std::array<std::int64_t, 10> diagnostic_aggregate_raw{};
  std::array<bool, 10> named_cost_verified{};
  std::array<std::uint32_t, 4> known_name_resource_indices{
      10, 10, 10, 10};
  bool final_can_start_observed = false;
  bool final_can_start = false;
  // GetCanProgressPlanningStageTooltip has no admitted getter in this package.
  bool failure_display_known = false;

  friend bool operator==(const ActivityTypedPlannerCostQuoteV1 &,
                         const ActivityTypedPlannerCostQuoteV1 &) = default;
};

} // namespace xar::bridge
