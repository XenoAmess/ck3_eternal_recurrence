#include "xar_bridge/ck3_12003_current_province_supply_contributors.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"

#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {

template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

void *Resolve(void **slot, std::int32_t id, std::size_t id_offset) noexcept {
  if (slot == nullptr || *slot == nullptr || id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = Load<std::int32_t>(*slot, 0x2C);
  if (capacity < 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const void *objects = Load<const void *>(*slot, 0x20);
  if (objects == nullptr) return nullptr;
  void *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 0x08);
  return object != nullptr && Load<std::int32_t>(object, id_offset) == id ? object : nullptr;
}

game::ArmyProvinceSupplyContributorOccurrenceV1 ReadOccurrence(
    const ck3_12002::ArmyBindings &bindings, void *subject_owner,
    std::int32_t stored_index, std::int32_t unit_id) {
  game::ArmyProvinceSupplyContributorOccurrenceV1 result{};
  result.stored_index = stored_index;
  result.army_id = unit_id;
  const auto unavailable = [&](std::string reason) {
    result.unavailable_reason = std::move(reason);
    return result;
  };
  void *unit = Resolve(bindings.unit_storage_slot, unit_id, 0x10);
  if (unit == nullptr) return unavailable("province_contributor_unit_unresolved");
  const auto owner_id = Load<std::int32_t>(unit, 0x174);
  void *owner = Resolve(bindings.monthly_loss_budget_bindings.character_storage_slot, owner_id, 0x18);
  if (owner == nullptr) return unavailable("province_contributor_owner_unresolved");
  result.owner_character_id = owner_id;
  const bool same_owner = owner == subject_owner;
  result.included = same_owner || bindings.current_province_supply_contributor_bindings
      .shares_current_war_side(subject_owner, owner, nullptr);
  result.inclusion_basis = same_owner ? "same_owner" :
      *result.included ? "native_common_war_side" : "native_not_common_war_side";
  if (!*result.included) {
    result.available = true;
    return result;
  }
  const auto army_id = Load<std::int32_t>(unit, 0x178);
  void *army = Resolve(bindings.internal_army_storage_slot, army_id, 0x10);
  if (army == nullptr) return unavailable("province_contributor_army_unresolved");
  result.native_carmy_id = army_id;
  const auto *descriptor = static_cast<std::byte *>(army) + 0x38;
  result.native_eligible_current_soldiers = bindings.get_army_current_soldiers(
      const_cast<std::byte *>(descriptor), 2);
  const auto count = Load<std::int32_t>(army, 0x44);
  const void *ids = Load<const void *>(army, 0x38);
  if (count < 0 || (count > 0 && ids == nullptr))
    return unavailable("province_contributor_regiment_roster_unavailable");
  bool partial = false;
  for (std::int32_t index = 0; index < count; ++index) {
    game::ArmyProvinceSupplyContributorRegimentV1 row{};
    row.stored_index = index;
    row.army_regiment_id = Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4);
    void *regiment = Resolve(bindings.regiment_storage_slot, row.army_regiment_id, 0x10);
    if (regiment == nullptr || Load<std::uint32_t>(regiment, 0x14) != 0x41725267U) {
      row.unavailable_reason = "province_contributor_regiment_unresolved";
      partial = true;
    } else {
      row.current_soldiers = Load<std::int32_t>(regiment, 0x38);
      row.maximum_soldiers = Load<std::int32_t>(regiment, 0x3C);
      row.native_supply_loss_eligible = bindings.is_regiment_supply_loss_eligible(regiment);
      row.available = true;
      if (*row.native_supply_loss_eligible) {
        row.replenishment_records_v1 = ReadArmyRegimentReplenishmentRecordsV1(
            bindings, regiment, row.army_regiment_id);
      }
    }
    result.regiments.push_back(std::move(row));
  }
  result.available = !partial;
  if (partial) result.unavailable_reason = "province_contributor_regiments_partial";
  return result;
}

} // namespace

game::ArmyCurrentProvinceSupplyContributorsV1
ReadCurrentProvinceSupplyContributors12003(
    const ck3_12002::ArmyBindings &bindings, void *subject_army,
    void *subject_unit, void *current_province) {
  game::ArmyCurrentProvinceSupplyContributorsV1 result{};
  const auto unavailable = [&](std::string reason) {
    result.unavailable_reason = std::move(reason);
    return result;
  };
  if (!bindings.enabled || !bindings.current_province_supply_contributor_bindings.enabled ||
      bindings.current_province_supply_contributor_bindings.shares_current_war_side == nullptr ||
      bindings.get_province_supply_limit == nullptr || bindings.get_province_supply_usage == nullptr ||
      bindings.get_army_current_soldiers == nullptr || bindings.is_regiment_supply_loss_eligible == nullptr)
    return unavailable("native_current_province_contributor_bindings_unavailable");
  if (subject_army == nullptr || subject_unit == nullptr || current_province == nullptr)
    return unavailable("validated_current_province_context_unavailable");
  result.subject_army_id = Load<std::int32_t>(subject_unit, 0x10);
  result.subject_carmy_id = Load<std::int32_t>(subject_army, 0x10);
  result.province_id = Load<std::int32_t>(current_province, 0x10);
  const auto owner_id = Load<std::int32_t>(subject_unit, 0x174);
  void *owner = Resolve(bindings.monthly_loss_budget_bindings.character_storage_slot, owner_id, 0x18);
  if (owner == nullptr) return unavailable("current_province_subject_owner_unresolved");
  result.owner_character_id = owner_id;
  void *commander = Resolve(bindings.monthly_loss_budget_bindings.character_storage_slot,
      Load<std::int32_t>(subject_army, 0x120), 0x18);
  if (commander == nullptr) commander = bindings.province_supply_character_fallback_slot == nullptr
      ? nullptr : *bindings.province_supply_character_fallback_slot;
  if (commander == nullptr) return unavailable("current_province_commander_fallback_unavailable");
  result.native_supply_limit_soldiers = bindings.get_province_supply_limit(
      current_province, owner, commander, nullptr);
  result.native_supply_usage_soldiers = bindings.get_province_supply_usage(
      current_province, owner, 0, nullptr);
  result.current_usage_ready = true;
  const auto count = Load<std::int32_t>(current_province, 0x74C);
  result.native_province_unit_count = count;
  const void *ids = Load<const void *>(current_province, 0x740);
  if (count < 0 || (count > 0 && ids == nullptr)) {
    result.status = "partial";
    return unavailable("current_province_native_roster_unavailable");
  }
  bool partial = false;
  for (std::int32_t index = 0; index < count; ++index) {
    result.occurrences.push_back(ReadOccurrence(bindings, owner, index,
        Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4)));
    partial = partial || !result.occurrences.back().available;
  }
  result.contributors_ready = !partial;
  result.status = partial ? "partial" : "available";
  if (partial) result.unavailable_reason = "current_province_contributors_partial";
  return result;
}

} // namespace xar::ck3_12003
