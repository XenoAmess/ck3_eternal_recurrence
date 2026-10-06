#include "xar_bridge/ck3_12003_current_land_resupply.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

void *ResolveOwner(void **slot, std::int32_t id) noexcept {
  if (slot == nullptr || *slot == nullptr || id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = Load<std::int32_t>(*slot, 0x2C);
  if (capacity < 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const void *objects = Load<const void *>(*slot, 0x20);
  if (objects == nullptr) return nullptr;
  void *owner = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  return owner != nullptr && Load<std::int32_t>(owner, 0x18) == id ? owner : nullptr;
}
} // namespace

game::ArmyCurrentLandResupplyV1 ReadCurrentLandResupply12003(
    const CurrentLandResupplyBindings12003 &bindings, void *army,
    void *unit, void *current_province) {
  game::ArmyCurrentLandResupplyV1 result{};
  const auto unavailable = [&](std::string reason) {
    result.unavailable_reason = std::move(reason);
    return result;
  };
  if (!bindings.enabled)
    return unavailable("native_current_land_resupply_bindings_unavailable");
  if (bindings.loaded_gain_raw != nullptr)
    result.loaded_gain_raw = Load<std::int64_t>(bindings.loaded_gain_raw, 0);
  if (army == nullptr || unit == nullptr || current_province == nullptr)
    return unavailable("validated_current_province_context_unavailable");
  result.province_id = Load<std::int32_t>(current_province, 0x10);
  if (bindings.is_army_fleet_supply_active == nullptr)
    return unavailable("native_supply_change_branch_unavailable");
  result.native_land_branch_applicable = !bindings.is_army_fleet_supply_active(army);
  if (!*result.native_land_branch_applicable) {
    // 24E51A0 does not evaluate this admission predicate on its fleet path.
    result.status = "not_land";
    return result;
  }
  const auto owner_id = Load<std::int32_t>(unit, 0x174);
  void *owner = ResolveOwner(bindings.character_storage_slot, owner_id);
  if (owner == nullptr)
    return unavailable("current_province_resupply_owner_unresolved");
  result.owner_character_id = owner_id;
  if (bindings.is_resupply_eligible == nullptr || bindings.loaded_gain_raw == nullptr)
    return unavailable("native_resupply_admission_or_gain_unavailable");
  result.native_resupply_eligible = bindings.is_resupply_eligible(owner, current_province);
  result.status = "available";
  result.current_observation_ready = true;
  return result;
}
} // namespace xar::ck3_12003
