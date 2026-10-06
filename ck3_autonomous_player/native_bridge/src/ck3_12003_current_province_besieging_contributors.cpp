#include "xar_bridge/ck3_12003_current_province_besieging_contributors.hpp"
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
  if (slot == nullptr || *slot == nullptr) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(Load<std::int32_t>(*slot, 0x2C))) return nullptr;
  const auto objects = Load<void *>(*slot, 0x20);
  if (objects == nullptr) return nullptr;
  auto *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Load<std::int32_t>(object, id_offset) == id ? object : nullptr;
}
void *Fallback(void **slot) noexcept { return slot == nullptr ? nullptr : *slot; }

game::ArmyProvinceBesiegingOccurrenceV1 ReadOccurrence(
    const ck3_12002::ArmyBindings &b, void *province, std::int32_t index,
    std::int32_t unit_id) {
  game::ArmyProvinceBesiegingOccurrenceV1 row{};
  row.stored_index = index;
  row.public_unit_id = unit_id;
  const auto &native = b.current_province_besieging_bindings;
  const auto unavailable = [&](std::string reason) {
    row.unavailable_reason = std::move(reason);
    return row;
  };
  void *unit = Resolve(b.unit_storage_slot, unit_id, 0x10);
  row.unit_used_fallback = unit == nullptr;
  if (unit == nullptr) unit = Fallback(native.unit_fallback_slot);
  if (unit == nullptr) return unavailable("besieging_unit_fallback_unavailable");
  row.resolved_unit_id = Load<std::int32_t>(unit, 0x10);
  void *unit_province = Load<void *>(unit, 0x20);
  row.current_province_used_fallback = unit_province == nullptr;
  if (unit_province == nullptr) unit_province = Fallback(native.province_fallback_slot);
  if (unit_province == nullptr) return unavailable("besieging_current_province_fallback_unavailable");
  row.current_province_id = Load<std::int32_t>(unit_province, 0x10);
  row.raw_unit18 = Load<std::int32_t>(unit, 0x18);
  row.raw_unit170 = Load<std::int32_t>(unit, 0x170);
  row.raw_unit44 = Load<std::int32_t>(unit, 0x44);
  const auto exclude = [&] {
    row.eligible = false;
    row.available = true;
    return row;
  };
  if (*row.current_province_id != Load<std::int32_t>(province, 0x10) ||
      *row.raw_unit18 != 0 || *row.raw_unit170 > 0 || *row.raw_unit44 != 0)
    return exclude();
  const auto resolve_army = [&]() {
    void *army = Resolve(b.internal_army_storage_slot, Load<std::int32_t>(unit, 0x178), 0x10);
    row.army_used_fallback = army == nullptr;
    if (army == nullptr) army = Fallback(native.army_fallback_slot);
    if (army != nullptr) row.native_carmy_id = Load<std::int32_t>(army, 0x10);
    return army;
  };
  void *army = resolve_army();
  if (army == nullptr) return unavailable("besieging_army_fallback_unavailable");
  if (native.army_excluded == nullptr) return unavailable("besieging_combat_predicate_unavailable");
  if (native.army_excluded(army) != 0 || Load<std::int32_t>(province, 0x788) == -1)
    return exclude();
  if (native.army_province_eligible == nullptr)
    return unavailable("besieging_province_predicate_unavailable");
  if (native.army_province_eligible(army, province) == 0) return exclude();
  row.eligible = true;
  // 247F2F6 resolves the Army again after the native qualification call.
  army = resolve_army();
  if (army == nullptr) return unavailable("besieging_count_army_unavailable");
  if (b.get_army_current_soldiers == nullptr)
    return unavailable("besieging_flags0_current_getter_unavailable");
  row.native_whole_current_soldiers = b.get_army_current_soldiers(
      static_cast<std::byte *>(army) + 0x38, 0);
  const auto count = Load<std::int32_t>(army, 0x44);
  const auto ids = Load<void *>(army, 0x38);
  if (count > 0 && ids == nullptr) return unavailable("besieging_ArRg_roster_unavailable");
  bool partial = false;
  for (std::int32_t stored = 0; stored < count; ++stored) {
    game::ArmyProvinceBesiegingRegimentV1 regiment{};
    regiment.stored_index = stored;
    regiment.army_regiment_id = Load<std::int32_t>(ids, static_cast<std::size_t>(stored) * 4);
    void *object = Resolve(b.regiment_storage_slot, regiment.army_regiment_id, 0x10);
    if (object == nullptr || Load<std::uint32_t>(object, 0x14) != 0x41725267U) {
      regiment.unavailable_reason = "besieging_ArRg_unresolved";
      partial = true;
    } else {
      regiment.current_soldiers = Load<std::int32_t>(object, 0x38);
      regiment.maximum_soldiers = Load<std::int32_t>(object, 0x3C);
      regiment.replenishment_records_v1 = ReadArmyRegimentReplenishmentRecordsV1(
          b, object, regiment.army_regiment_id);
      regiment.available = true;
    }
    row.regiments.push_back(std::move(regiment));
  }
  row.available = !partial;
  if (partial) row.unavailable_reason = "besieging_ArRg_rows_partial";
  return row;
}
} // namespace

game::ArmyCurrentProvinceBesiegingContributorsV1 ReadCurrentProvinceBesiegingContributors12003(
    const ck3_12002::ArmyBindings &b, void *province) {
  game::ArmyCurrentProvinceBesiegingContributorsV1 out{};
  const auto &native = b.current_province_besieging_bindings;
  if (!b.enabled || !native.enabled || province == nullptr) {
    out.unavailable_reason = "validated_current_besieging_province_unavailable";
    return out;
  }
  out.province_id = Load<std::int32_t>(province, 0x10);
  if (native.besieging_strength != nullptr)
    out.native_besieging_strength = native.besieging_strength(province);
  const auto count = Load<std::int32_t>(province, 0x74C);
  out.native_province_unit_count = count;
  const auto ids = Load<void *>(province, 0x740);
  if (count > 0 && ids == nullptr) {
    out.status = "partial";
    out.unavailable_reason = "besieging_Province_occurrences_unavailable";
  } else {
    bool partial = false;
    for (std::int32_t index = 0; index < count; ++index) {
      out.occurrences.push_back(ReadOccurrence(b, province, index,
          Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4)));
      partial = partial || !out.occurrences.back().available;
    }
    out.contributors_ready = !partial;
    out.status = partial ? "partial" : "available";
    if (partial) out.unavailable_reason = "besieging_current_contributors_partial";
  }
  auto &context = out.assault_context;
  const auto siege_id = Load<std::int32_t>(province, 0x788);
  if (siege_id == -1) {
    context.status = "available";
    context.has_active_siege = false;
    return out;
  }
  void *siege = Resolve(native.siege_storage_slot, siege_id, 8);
  if (siege == nullptr || Load<void *>(siege, 0x200) != province) {
    context.unavailable_reason = "current_besieging_siege_context_unresolved";
    return out;
  }
  context.status = "available";
  context.has_active_siege = true;
  context.siege_id = siege_id;
  context.breach_level_raw = Load<std::int32_t>(siege, 0x3D8);
  if (native.assault_expected_loss != nullptr)
    out.native_assault_expected_loss = native.assault_expected_loss(siege);
  if (native.casualty_percentage_count != nullptr)
    context.casualty_percentage_count = *native.casualty_percentage_count;
  const auto percentage_index = static_cast<std::int64_t>(*context.breach_level_raw) - 1;
  if (context.casualty_percentage_count && percentage_index >= 0 &&
      percentage_index < *context.casualty_percentage_count) {
    if (native.casualty_percentage_table_slot != nullptr &&
        *native.casualty_percentage_table_slot != nullptr) {
      context.casualty_percentage_raw = (*native.casualty_percentage_table_slot)[
          static_cast<std::size_t>(percentage_index)];
    } else {
      context.status = "partial";
      context.unavailable_reason = "assault_loaded_percentage_entry_unavailable";
    }
  }
  return out;
}
} // namespace xar::ck3_12003
