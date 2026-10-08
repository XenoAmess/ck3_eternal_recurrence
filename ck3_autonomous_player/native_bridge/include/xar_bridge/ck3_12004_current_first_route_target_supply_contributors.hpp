#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_current_province_supply_contributors.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <utility>

namespace xar::ck3_12004 {
namespace first_route_target_supply_detail {

template<class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

inline void *ResolveUnit(const ck3_12002::ArmyBindings &bindings,
                         std::int32_t id) noexcept {
  if (bindings.unit_storage_slot == nullptr || *bindings.unit_storage_slot == nullptr || id == -1)
    return nullptr;
  const void *storage = *bindings.unit_storage_slot;
  const auto count = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (count < 0 || index >= static_cast<std::uint32_t>(count)) return nullptr;
  const void *rows = Load<const void *>(storage, 0x20);
  if (rows == nullptr) return nullptr;
  void *unit = Load<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 8);
  return unit != nullptr && Load<std::int32_t>(unit, 0x10) == id ? unit : nullptr;
}

inline void *ResolveProvince(const ck3_12002::ArmyBindings &bindings,
                             std::int32_t id) noexcept {
  if (bindings.game_state_slot == nullptr || *bindings.game_state_slot == nullptr) return nullptr;
  void *data = Load<void *>(*bindings.game_state_slot, 0xA0);
  if (data == nullptr) return nullptr;
  const auto count = Load<std::int32_t>(data, 0x14C);
  if (id < 0 || id >= count) return nullptr;
  const void *provinces = Load<const void *>(data, 0x140);
  if (provinces == nullptr) return nullptr;
  void *province = Load<void *>(provinces, static_cast<std::size_t>(id) * sizeof(void *));
  return province != nullptr && Load<std::int32_t>(province, 0x10) == id ? province : nullptr;
}

} // namespace first_route_target_supply_detail

// Capture CURRENT target roster inputs for the original committed first edge.
// No preview route is generated and no hypothetical arrival/Unit mutation is run.
inline game::ArmyCurrentFirstRouteTargetSupplyContributorsV1
ReadCurrentFirstRouteTargetSupplyContributors12004(
    const ck3_12002::ArmyBindings &bindings, void *army, void *unit) {
  using first_route_target_supply_detail::Load;
  game::ArmyCurrentFirstRouteTargetSupplyContributorsV1 result{};
  const auto unavailable = [&](const char *reason) {
    result.unavailable_reason = reason;
    return result;
  };
  if (!bindings.enabled || !bindings.current_province_supply_contributor_bindings.enabled)
    return unavailable("native_first_route_target_contributor_bindings_unavailable");
  if (army == nullptr || unit == nullptr)
    return unavailable("validated_first_route_target_subject_unavailable");
  result.subject_army_id = Load<std::int32_t>(unit, 0x10);
  result.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  const void *current_province = Load<const void *>(unit, 0x20);
  if (current_province != nullptr)
    result.current_province_id = Load<std::int32_t>(current_province, 0x10);
  const auto count = Load<std::int32_t>(unit, 0x44);
  result.route_source_count = count;
  if (count == 0) {
    result.status = "no_committed_target";
    return result;
  }
  const void *ids = Load<const void *>(unit, 0x38);
  if (count < 0 || ids == nullptr)
    return unavailable("first_route_target_route_descriptor_unavailable");
  const auto target_id = Load<std::int32_t>(ids, 0);
  result.first_route_target_province_id = target_id;
  void *target = first_route_target_supply_detail::ResolveProvince(bindings, target_id);
  if (target == nullptr)
    return unavailable("first_route_target_province_unresolved");

  // The existing implementation is Province-context based: native limit/usage
  // consume its passed Province; +740/+74C preserves its actual roster. It has
  // no subject-current-Province or subject-membership requirement. The distinct
  // outer DTO names the target context; the current-Province DTO is unchanged.
  auto contributors = ck3_12003::ReadCurrentProvinceSupplyContributors12003(
      bindings, army, unit, target);
  result.current_target_inputs_ready = contributors.current_usage_ready && contributors.contributors_ready;
  result.status = result.current_target_inputs_ready ? "available" : contributors.status;
  result.unavailable_reason = contributors.unavailable_reason;
  for (const auto &occurrence : contributors.occurrences) {
    // Use genuine resolved pointer identity, retaining every original duplicate.
    if (first_route_target_supply_detail::ResolveUnit(bindings, occurrence.army_id) == unit)
      result.subject_matching_occurrence_indices.push_back(occurrence.stored_index);
  }
  if (contributors.contributors_ready) {
    result.subject_included_occurrence_count = 0;
    for (const auto &occurrence : contributors.occurrences) {
      if (first_route_target_supply_detail::ResolveUnit(bindings, occurrence.army_id) == unit &&
          occurrence.included == true)
        ++*result.subject_included_occurrence_count;
    }
  }
  result.target_contributors_v1 = std::move(contributors);
  return result;
}

} // namespace xar::ck3_12004
