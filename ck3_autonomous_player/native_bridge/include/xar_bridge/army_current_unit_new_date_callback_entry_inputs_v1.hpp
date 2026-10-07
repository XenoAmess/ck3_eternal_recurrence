#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

// Raw subject route count only. Raw Unit170 remains in the existing same-row
// monthly_loss_budget_inputs_v1; this does not forecast a native callback.
struct ArmyCurrentUnitNewDateCallbackEntryInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_unit_new_date_callback_entry_inputs_12004";
  std::string capture_boundary = "current_query_before_unit_new_date_stage";
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason{};
  std::optional<std::uint32_t> subject_army_id_u32{};
  std::optional<std::uint32_t> subject_carmy_id_u32{};
  std::optional<std::int32_t> unit_route_count_i32{};

  friend bool operator==(const ArmyCurrentUnitNewDateCallbackEntryInputsV1 &,
                         const ArmyCurrentUnitNewDateCallbackEntryInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12004 {

// Dependency-free value for the common ArmyBindings.
struct CurrentUnitNewDateCallbackEntryBindings12004 {
  bool enabled = false;
};

} // namespace xar::ck3_12004
