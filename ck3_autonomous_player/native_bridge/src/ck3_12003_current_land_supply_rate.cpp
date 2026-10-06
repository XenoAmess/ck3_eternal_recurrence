#include "xar_bridge/ck3_12003_current_land_supply_rate.hpp"
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result);
  return result;
}
void *Resolve(void **slot, std::int32_t id) noexcept {
  if (slot == nullptr || *slot == nullptr) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = Load<std::int32_t>(*slot, 0x2C);
  if (capacity < 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const void *objects = Load<void *>(*slot, 0x20);
  if (objects == nullptr) return nullptr;
  void *character = Load<void *>(objects, static_cast<std::size_t>(index) * 16 + 8);
  return character != nullptr && Load<std::int32_t>(character, 0x18) == id
      ? character : nullptr;
}
} // namespace

game::ArmyCurrentLandSupplyRateInputsV1 ReadCurrentLandSupplyRateInputs12003(
    const CurrentLandSupplyRateBindings12003 &b, void *army, void *unit,
    void *province, const game::ArmyCurrentLandResupplyV1 *resupply) {
  game::ArmyCurrentLandSupplyRateInputsV1 result{};
  const auto unavailable = [&](std::string reason) {
    result.unavailable_reason = std::move(reason); return result;
  };
  if (!b.enabled) return unavailable("native_land_supply_rate_bindings_unavailable");
  if (b.loaded_excess_slope_raw) result.loaded_excess_slope_raw = Load<std::int64_t>(b.loaded_excess_slope_raw, 0);
  if (b.loaded_min_loss_raw) result.loaded_min_loss_raw = Load<std::int64_t>(b.loaded_min_loss_raw, 0);
  if (b.loaded_max_loss_raw) result.loaded_max_loss_raw = Load<std::int64_t>(b.loaded_max_loss_raw, 0);
  if (b.loaded_divisor_floor_raw) result.loaded_divisor_floor_raw = Load<std::int64_t>(b.loaded_divisor_floor_raw, 0);
  if (army == nullptr || unit == nullptr || province == nullptr || resupply == nullptr)
    return unavailable("same_capture_land_supply_context_unavailable");
  result.subject_army_id = Load<std::int32_t>(unit, 0x10);
  result.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  result.province_id = Load<std::int32_t>(province, 0x10);
  result.owner_character_id = resupply->owner_character_id;
  result.native_land_branch_applicable = resupply->native_land_branch_applicable;
  if (result.native_land_branch_applicable == false) {
    result.status = "not_land"; return result;
  }
  if (!resupply->current_observation_ready)
    return unavailable("same_capture_land_resupply_unavailable");
  if (!b.province_component_condition || !b.read_province_component)
    return unavailable("native_province_supply_component_reader_unavailable");
  result.native_province_component_applicable = b.province_component_condition(province);
  result.province_component_raw = 0;
  if (*result.native_province_component_applicable) {
    std::int64_t local = 0;
    const auto *output = b.read_province_component(&local,
        static_cast<std::byte *>(province) + 0x30, 0x1AB, nullptr, 100000, 0);
    if (!output) { result.province_component_raw.reset();
      return unavailable("native_province_supply_component_output_unavailable"); }
    result.province_component_raw = Load<std::int64_t>(output, 0);
  }
  result.commander_raw_full_id = Load<std::int32_t>(army, 0x120);
  void *commander = Resolve(b.character_storage_slot, *result.commander_raw_full_id);
  result.commander_used_native_fallback = commander == nullptr;
  if (commander == nullptr && b.character_fallback_slot != nullptr)
    commander = *b.character_fallback_slot;
  if (!commander || !b.get_character_modifier_aggregator || !b.read_character_modifier)
    return unavailable("native_supply_commander_modifier_reader_unavailable");
  result.commander_resolved_full_id = Load<std::int32_t>(commander, 0x18);
  void *aggregator = b.get_character_modifier_aggregator(commander);
  if (!aggregator) return unavailable("native_supply_commander_aggregator_unavailable");
  std::int64_t local = 0;
  const auto *output = b.read_character_modifier(
      static_cast<std::byte *>(aggregator) + 0x68, &local, 0x1A9);
  if (!output) return unavailable("native_supply_commander_modifier_output_unavailable");
  result.commander_modifier_1a9_raw = Load<std::int64_t>(output, 0);
  if (!result.loaded_excess_slope_raw || !result.loaded_min_loss_raw ||
      !result.loaded_max_loss_raw || !result.loaded_divisor_floor_raw)
    return unavailable("loaded_land_supply_rate_parameters_unavailable");
  result.status = "available";
  result.current_observation_ready = true;
  return result;
}
} // namespace xar::ck3_12003
