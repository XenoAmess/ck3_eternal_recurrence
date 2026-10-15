#pragma once

#include "xar_bridge/army_captured_target_land_supply_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_current_land_resupply.hpp"
#include "xar_bridge/ck3_12003_current_land_supply_rate.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12003 {
namespace captured_target_land_supply_detail {
template<class T>
inline T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof result);
  return result;
}
inline game::ArmyTargetLossAdjustmentOperandsV1 ReadLossOperands(
    const CurrentLandSupplyRateBindings12003 &b, void *army) {
  game::ArmyTargetLossAdjustmentOperandsV1 r{};
  const auto unavailable = [&](const char *reason) {
    r.unavailable_reason = reason; return r;
  };
  if (!b.enabled || army == nullptr)
    return unavailable("captured_target_commander_context_unavailable");
  if (b.loaded_excess_slope_raw) r.loaded_excess_slope_raw = Load<std::int64_t>(b.loaded_excess_slope_raw,0);
  if (b.loaded_min_loss_raw) r.loaded_min_loss_raw = Load<std::int64_t>(b.loaded_min_loss_raw,0);
  if (b.loaded_max_loss_raw) r.loaded_max_loss_raw = Load<std::int64_t>(b.loaded_max_loss_raw,0);
  if (b.loaded_divisor_floor_raw) r.loaded_divisor_floor_raw = Load<std::int64_t>(b.loaded_divisor_floor_raw,0);
  r.commander_raw_full_id = Load<std::int32_t>(army,0x120);
  void *commander = nullptr;
  if (b.character_storage_slot && *b.character_storage_slot) {
    const auto index = static_cast<std::uint32_t>(*r.commander_raw_full_id) & 0x00FFFFFFU;
    const auto capacity = Load<std::int32_t>(*b.character_storage_slot,0x2C);
    const void *objects = Load<void *>(*b.character_storage_slot,0x20);
    if (capacity >= 0 && index < static_cast<std::uint32_t>(capacity) && objects) {
      commander = Load<void *>(objects,static_cast<std::size_t>(index)*16+8);
      if (commander && Load<std::int32_t>(commander,0x18) != *r.commander_raw_full_id)
        commander = nullptr;
    }
  }
  r.commander_used_native_fallback = commander == nullptr;
  if (!commander && b.character_fallback_slot) commander = *b.character_fallback_slot;
  if (!commander || !b.get_character_modifier_aggregator || !b.read_character_modifier)
    return unavailable("native_target_commander_modifier_reader_unavailable");
  r.commander_resolved_full_id = Load<std::int32_t>(commander,0x18);
  void *aggregate = b.get_character_modifier_aggregator(commander);
  if (!aggregate) return unavailable("native_target_commander_aggregator_unavailable");
  std::int64_t local=0;
  const auto *output = b.read_character_modifier(
      static_cast<std::byte *>(aggregate)+0x68,&local,0x1A9);
  if (!output) return unavailable("native_target_commander_modifier_output_unavailable");
  r.commander_modifier_1a9_raw = Load<std::int64_t>(output,0);
  if (!r.loaded_excess_slope_raw || !r.loaded_min_loss_raw ||
      !r.loaded_max_loss_raw || !r.loaded_divisor_floor_raw)
    return unavailable("loaded_target_loss_parameters_unavailable");
  r.status="available"; r.observation_ready=true; return r;
}
} // namespace captured_target_land_supply_detail

// All four objects are resolved by the existing available route preview. Reuse
// its actual owner, target Province and exact .3 bindings without querying the
// present Fleet/land branch or invoking any supply/movement mutator.
inline game::ArmyCapturedTargetLandSupplyInputsV1
ReadCapturedTargetLandSupplyInputs12003(
    const CurrentLandSupplyRateBindings12003 &rate,
    const CurrentLandResupplyBindings12003 &resupply,
    void *army, void *unit, void *owner, void *target_province) {
  using captured_target_land_supply_detail::Load;
  game::ArmyCapturedTargetLandSupplyInputsV1 result{};
  if (rate.capture_target_loss_operands)
    result.loss_adjustment_operands_v1 = captured_target_land_supply_detail::ReadLossOperands(rate,army);
  if (resupply.enabled && resupply.loaded_gain_raw != nullptr)
    result.loaded_gain_raw = Load<std::int64_t>(resupply.loaded_gain_raw, 0);
  if (army != nullptr) result.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  if (unit != nullptr) {
    result.subject_army_id = Load<std::int32_t>(unit, 0x10);
    result.owner_character_id = Load<std::int32_t>(unit, 0x174);
  }
  if (target_province != nullptr)
    result.province_id = Load<std::int32_t>(target_province, 0x10);

  if (army == nullptr || unit == nullptr || owner == nullptr ||
      target_province == nullptr) {
    result.province_component_unavailable_reason =
        "captured_target_land_supply_context_unavailable";
    result.resupply_unavailable_reason =
        "captured_target_land_supply_context_unavailable";
  } else {
    if (!rate.enabled || rate.province_component_condition == nullptr) {
      result.province_component_unavailable_reason =
          "native_target_province_component_predicate_unavailable";
    } else {
      result.native_province_component_applicable =
          rate.province_component_condition(target_province);
      if (!*result.native_province_component_applicable) {
        result.province_component_raw = 0;
        result.province_component_observation_ready = true;
      } else if (rate.read_province_component == nullptr) {
        result.province_component_unavailable_reason =
            "native_target_province_component_reader_unavailable";
      } else {
        std::int64_t local = 0;
        const auto *output = rate.read_province_component(
            &local, static_cast<std::byte *>(target_province) + 0x30,
            0x1AB, nullptr, 100000, 0);
        if (output == nullptr) {
          result.province_component_unavailable_reason =
              "native_target_province_component_output_unavailable";
        } else {
          result.province_component_raw = Load<std::int64_t>(output, 0);
          result.province_component_observation_ready = true;
        }
      }
    }

    if (!resupply.enabled || resupply.is_resupply_eligible == nullptr) {
      result.resupply_unavailable_reason =
          "native_target_resupply_predicate_unavailable";
    } else {
      result.native_resupply_eligible =
          resupply.is_resupply_eligible(owner, target_province);
      // This flag qualifies the observed owner/target Boolean. Loaded gain is
      // an independent optional raw input; its missing read does not erase a
      // real false/true predicate or qualify a complete target rate.
      result.resupply_observation_ready = true;
    }
  }

  result.current_inputs_ready = result.province_component_observation_ready &&
                                result.resupply_observation_ready;
  result.status = result.current_inputs_ready ? "available"
      : (result.province_component_observation_ready ||
         result.resupply_observation_ready) ? "partial" : "unavailable";
  if (!result.current_inputs_ready) {
    result.unavailable_reason = result.province_component_unavailable_reason
        ? result.province_component_unavailable_reason
        : result.resupply_unavailable_reason;
  }
  return result;
}

} // namespace xar::ck3_12003
