#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstring>
#include <string_view>

namespace xar::ck3_12004 {

struct NextRouteReplenishmentPositionBindings12004 {
  bool enabled = false;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **province_fallback_slot = nullptr;
  std::int32_t *(*read_province_holder)(void *, std::int32_t *) = nullptr;
  bool (*owner_holder_eligible)(void *, void *) = nullptr;
};

inline NextRouteReplenishmentPositionBindings12004
BindNextRouteReplenishmentPositionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  NextRouteReplenishmentPositionBindings12004 result{};
  if (base == 0 || sha !=
      "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")
    return result;
  result.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  result.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  result.province_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E390);
  result.read_province_holder = reinterpret_cast<decltype(result.read_province_holder)>(
      base + 0x247D010);
  result.owner_holder_eligible = reinterpret_cast<decltype(result.owner_holder_eligible)>(
      base + 0x2C097F0);
  result.enabled = true;
  return result;
}

namespace next_route_replenishment_detail {
template <class T> T Read(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

inline const char *RouteStatus(game::ArmyRouteReadStatus status) noexcept {
  switch (status) {
  case game::ArmyRouteReadStatus::complete_empty: return "complete_empty";
  case game::ArmyRouteReadStatus::complete_nonempty: return "complete_nonempty";
  case game::ArmyRouteReadStatus::target_only: return "target_only";
  case game::ArmyRouteReadStatus::invalid_header: return "invalid_header";
  case game::ArmyRouteReadStatus::unresolved_entry: return "unresolved_entry";
  default: return "not_attempted";
  }
}

// Same registry snapshot and fallback for both operands, matching24ACAA0.
inline void *Character(void *registry, void *fallback, std::int32_t id,
                       bool &used_fallback) noexcept {
  used_fallback = true;
  if (registry != nullptr) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto capacity = Read<std::uint32_t>(registry, 0x2C);
    if (index < capacity) {
      void *rows = Read<void *>(registry, 0x20);
      if (rows != nullptr) {
        void *entry = Read<void *>(rows, std::size_t{index} * 0x10 + 8);
        if (entry != nullptr && Read<std::int32_t>(entry, 0x18) == id) {
          used_fallback = false;
          return entry;
        }
      }
    }
  }
  return fallback;
}
} // namespace next_route_replenishment_detail

inline game::ArmyNextRouteReplenishmentPositionInputsV1
ReadNextRouteReplenishmentPositionInputs12004(
    const NextRouteReplenishmentPositionBindings12004 &bindings,
    void *unit, const game::ArmySnapshot &route, void *first_target_province) {
  using namespace next_route_replenishment_detail;
  game::ArmyNextRouteReplenishmentPositionInputsV1 result{};
  result.route_read_status = RouteStatus(route.route_read_status);
  result.route_source_count = route.route_source_count;
  result.route_province_ids = route.route_province_ids;
  if (unit == nullptr) {
    result.unavailable_reason = "actual_unit_unavailable";
    return result;
  }
  result.unit_full_id = Read<std::int32_t>(unit, 0x10);
  void *current = Read<void *>(unit, 0x20);
  if (current == nullptr && bindings.province_fallback_slot != nullptr)
    current = *bindings.province_fallback_slot;
  if (current != nullptr) result.current_province_id = Read<std::int32_t>(current, 0x10);
  if (route.route_read_status == game::ArmyRouteReadStatus::complete_empty) {
    result.status = "not_applicable";
    result.unavailable_reason = "no_stored_first_route_target";
    return result;
  }
  if (route.route_read_status == game::ArmyRouteReadStatus::complete_nonempty &&
      !route.route_province_ids.empty())
    result.first_target_province_id = route.route_province_ids.front();
  if (route.route_read_status != game::ArmyRouteReadStatus::complete_nonempty ||
      route.route_province_ids.empty() || first_target_province == nullptr) {
    result.unavailable_reason = "original_complete_first_route_target_unavailable";
    return result;
  }
  if (Read<std::int32_t>(first_target_province, 0x10) != *result.first_target_province_id) {
    result.unavailable_reason = "first_route_target_identity_mismatch";
    return result;
  }
  result.first_target_province_magic_raw = Read<std::uint32_t>(first_target_province, 0x85C);
  if (*result.first_target_province_magic_raw != 0x50726F76U) {
    result.status = "available";
    result.native_first_target_position_eligible = false;
    return result;
  }
  if (!bindings.enabled || bindings.character_storage_slot == nullptr ||
      bindings.character_fallback_slot == nullptr ||
      bindings.read_province_holder == nullptr || bindings.owner_holder_eligible == nullptr) {
    result.unavailable_reason = "next_route_owner_holder_bindings_unavailable";
    return result;
  }
  void *registry = *bindings.character_storage_slot;
  void *fallback = *bindings.character_fallback_slot;
  void *owner = fallback;
  bool owner_fallback = true;
  if (registry != nullptr) {
    result.owner_requested_full_id = Read<std::int32_t>(unit, 0x174);
    owner = Character(registry, fallback, *result.owner_requested_full_id, owner_fallback);
  }
  result.owner_used_fallback = owner_fallback;
  if (owner != nullptr) result.owner_resolved_full_id = Read<std::int32_t>(owner, 0x18);
  std::int32_t holder_out = -1;
  const auto *holder_ref = bindings.read_province_holder(first_target_province, &holder_out);
  if (holder_ref == nullptr) {
    result.unavailable_reason = "native_target_holder_reference_unavailable";
    return result;
  }
  void *holder = fallback;
  bool holder_fallback = true;
  if (registry != nullptr) {
    result.holder_requested_full_id = *holder_ref;
    holder = Character(registry, fallback, *result.holder_requested_full_id, holder_fallback);
  }
  result.holder_used_fallback = holder_fallback;
  if (holder != nullptr) result.holder_resolved_full_id = Read<std::int32_t>(holder, 0x18);
  if (owner == nullptr || holder == nullptr) {
    result.unavailable_reason = "native_target_owner_holder_operand_unavailable";
    return result;
  }
  result.native_owner_holder_eligible = bindings.owner_holder_eligible(owner, holder);
  result.native_first_target_position_eligible = result.native_owner_holder_eligible;
  result.status = "available";
  return result;
}

} // namespace xar::ck3_12004
