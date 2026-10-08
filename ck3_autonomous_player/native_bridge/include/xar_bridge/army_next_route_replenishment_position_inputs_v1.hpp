#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

struct ArmyNextRouteReplenishmentPositionInputsV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::int32_t unit_full_id = -1;
  std::string route_read_status;
  std::optional<std::int32_t> route_source_count;
  std::vector<std::int32_t> route_province_ids;
  std::optional<std::int32_t> current_province_id;
  std::optional<std::int32_t> first_target_province_id;
  std::optional<std::uint32_t> first_target_province_magic_raw;
  std::optional<std::int32_t> owner_requested_full_id;
  std::optional<std::int32_t> owner_resolved_full_id;
  std::optional<bool> owner_used_fallback;
  std::optional<std::int32_t> holder_requested_full_id;
  std::optional<std::int32_t> holder_resolved_full_id;
  std::optional<bool> holder_used_fallback;
  std::optional<bool> native_owner_holder_eligible;
  std::optional<bool> native_first_target_position_eligible;

  friend bool operator==(const ArmyNextRouteReplenishmentPositionInputsV1 &,
                         const ArmyNextRouteReplenishmentPositionInputsV1 &) = default;
};

} // namespace xar::game
