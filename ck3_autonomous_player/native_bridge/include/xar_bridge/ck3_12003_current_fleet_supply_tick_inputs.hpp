#pragma once

// Candidate only: Root must adopt the DTO/shared hooks and qualify the first
// new production reader/serializer wire. This file has not been compiled.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_current_fleet_supply_tick_inputs_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {
inline CurrentFleetSupplyTickBindings12003 BindCurrentFleetSupplyTickImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CurrentFleetSupplyTickBindings12003 result{};
  if (image_base == 0 || executable_sha256 !=
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6")
    return result;
  result.enabled = true;
  result.loaded_fleet_loss_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69A78);
  result.loaded_divisor_floor_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C68F68);
  result.loaded_max_loss_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69A40);
  return result;
}

namespace current_fleet_tick_detail {
template <class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}

// Exact low24/stride16/+8/full-ID resolution and actual native fallback.
// Fleet ID offset is10; Character ID offset is18. Neither fallback is
// replaced with a guessed zero or rejected by an extra magic check.
inline void *Resolve(void **storage_slot, void **fallback_slot,
    std::int32_t request, std::size_t id_offset, bool &used_fallback) noexcept {
  used_fallback = true;
  if (storage_slot != nullptr && *storage_slot != nullptr) {
    const void *storage = *storage_slot;
    const auto index = static_cast<std::uint32_t>(request) & 0x00FFFFFFU;
    const auto capacity = Load<std::int32_t>(storage, 0x2C);
    const void *slots = Load<void *>(storage, 0x20);
    if (capacity >= 0 && index < static_cast<std::uint32_t>(capacity) && slots != nullptr) {
      void *object = Load<void *>(slots, static_cast<std::size_t>(index) * 16 + 8);
      if (object != nullptr && Load<std::int32_t>(object, id_offset) == request) {
        used_fallback = false;
        return object;
      }
    }
  }
  return fallback_slot == nullptr ? nullptr : *fallback_slot;
}
} // namespace current_fleet_tick_detail

inline game::ArmyCurrentFleetSupplyTickInputsV1 ReadCurrentFleetSupplyTickInputs12003(
    const CurrentFleetSupplyTickBindings12003 &bindings,
    const ck3_12002::ArmyBindings &existing, void *army,
    void *unit, void *current_province,
    std::optional<bool> same_capture_native_fleet_branch = std::nullopt,
    std::optional<std::int32_t> same_capture_native_date = std::nullopt,
    std::optional<std::int64_t> same_capture_divisor_floor = std::nullopt,
    std::optional<std::int64_t> same_capture_max_loss = std::nullopt) {
  using current_fleet_tick_detail::Load;
  game::ArmyCurrentFleetSupplyTickInputsV1 result{};
  const auto missing = [&](std::string_view reason) {
    if (!result.unavailable_reason) result.unavailable_reason = std::string(reason);
  };
  if (!bindings.enabled || !existing.enabled) {
    missing("native_fleet_supply_tick_bindings_unavailable"); return result;
  }
  const auto &native = existing.monthly_loss_budget_bindings;
  if (army == nullptr || unit == nullptr || current_province == nullptr) {
    missing("same_capture_fleet_supply_context_unavailable"); return result;
  }
  result.subject_army_id = Load<std::int32_t>(unit, 0x10);
  result.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  result.province_id = Load<std::int32_t>(current_province, 0x10);
  result.native_fleet_branch_applicable = same_capture_native_fleet_branch;
  if (!result.native_fleet_branch_applicable && native.is_army_fleet_supply_active != nullptr)
    result.native_fleet_branch_applicable = native.is_army_fleet_supply_active(army);
  if (!result.native_fleet_branch_applicable) {
    missing("native_fleet_supply_branch_unavailable"); return result;
  }
  if (!*result.native_fleet_branch_applicable) {
    result.status = "not_fleet"; result.ready = true; return result;
  }

  result.current_native_date_low32 = same_capture_native_date;
  if (!result.current_native_date_low32 && existing.game_state_slot != nullptr &&
      *existing.game_state_slot != nullptr)
    result.current_native_date_low32 = Load<std::int32_t>(*existing.game_state_slot, 8);
  if (!result.current_native_date_low32) missing("native_fleet_supply_clock_unavailable");
  result.fleet_raw_full_id = Load<std::int32_t>(army, 0x12C);
  bool fleet_fallback = false;
  void *fleet = current_fleet_tick_detail::Resolve(native.fleet_storage_slot,
      native.fleet_fallback_slot, *result.fleet_raw_full_id, 0x10, fleet_fallback);
  if (fleet != nullptr) {
    result.fleet_resolved_full_id = Load<std::int32_t>(fleet, 0x10);
    result.fleet_used_native_fallback = fleet_fallback;
    result.fleet_day_raw = Load<std::int32_t>(fleet, 0x20);
  } else missing("native_fleet_supply_date_object_unavailable");
  if (native.fleet_date_sentinel != nullptr)
    result.loaded_fleet_day_sentinel_raw = Load<std::int32_t>(native.fleet_date_sentinel, 0);
  else missing("loaded_fleet_supply_date_sentinel_unavailable");

  // Do not stop at TODAY's suppressed date. That would repeat the current
  // boolean-only blind spot. Capture the date-independent current payload so
  // an explicitly replaced date can become numerically ready.
  void *province_definition = Load<void *>(current_province, 0x20);
  void *terrain = province_definition == nullptr ? nullptr
      : Load<void *>(province_definition, 0xB8);
  if (terrain == nullptr) {
    missing("native_fleet_supply_terrain_unavailable"); return result;
  }
  result.terrain_magic_38_raw = Load<std::uint32_t>(terrain, 0x38);
  const auto finish = [&]() {
    if (!result.unavailable_reason) { result.status = "available"; result.ready = true; }
    return result;
  };
  if (*result.terrain_magic_38_raw != 0x4744624FU) return finish();
  result.terrain_modifier_772_id = Load<std::uint16_t>(terrain, 0x772);
  result.commander_raw_full_id = Load<std::int32_t>(army, 0x120);
  bool commander_fallback = false;
  void *commander = current_fleet_tick_detail::Resolve(native.character_storage_slot,
      native.character_fallback_slot, *result.commander_raw_full_id, 0x18, commander_fallback);
  if (commander == nullptr || native.get_character_modifier_aggregator == nullptr ||
      native.read_character_modifier == nullptr) {
    missing("native_fleet_supply_commander_reader_unavailable"); return result;
  }
  result.commander_resolved_full_id = Load<std::int32_t>(commander, 0x18);
  result.commander_used_native_fallback = commander_fallback;
  void *aggregator = native.get_character_modifier_aggregator(commander);
  if (aggregator == nullptr) {
    missing("native_fleet_supply_commander_aggregator_unavailable"); return result;
  }
  void *component = static_cast<std::byte *>(aggregator) + 0x68;
  const auto read_modifier = [&](std::uint16_t ordinal) -> std::optional<std::int64_t> {
    std::int64_t local = 0;
    const auto *output = native.read_character_modifier(component, &local, ordinal);
    return output == nullptr ? std::nullopt
        : std::optional<std::int64_t>(Load<std::int64_t>(output, 0));
  };
  result.terrain_modifier_772_raw = read_modifier(*result.terrain_modifier_772_id);
  if (!result.terrain_modifier_772_raw) {
    missing("native_fleet_supply_terrain_modifier_output_unavailable"); return result;
  }
  //23037B0's complete terminal is signed SETG, not sparse-key presence.
  if (*result.terrain_modifier_772_raw > 0) return finish();
  if (bindings.loaded_fleet_loss_raw == nullptr) {
    missing("loaded_fleet_supply_base_loss_unavailable"); return result;
  }
  result.loaded_fleet_loss_raw = Load<std::int64_t>(bindings.loaded_fleet_loss_raw, 0);
  // wrap64(-loss) is negative exactly for signed positive loss, except INT64_MIN
  // whose wrapping negation is itself negative. Avoid performing signed negation.
  const bool negative_component = *result.loaded_fleet_loss_raw > 0 ||
      *result.loaded_fleet_loss_raw == (-9223372036854775807LL - 1LL);
  if (!negative_component) return finish();
  result.commander_modifier_1a9_raw = read_modifier(0x1A9);
  if (!result.commander_modifier_1a9_raw)
    missing("native_fleet_supply_fixed_modifier_output_unavailable");
  result.loaded_divisor_floor_raw = same_capture_divisor_floor;
  if (!result.loaded_divisor_floor_raw && bindings.loaded_divisor_floor_raw != nullptr)
    result.loaded_divisor_floor_raw = Load<std::int64_t>(bindings.loaded_divisor_floor_raw, 0);
  result.loaded_max_loss_raw = same_capture_max_loss;
  if (!result.loaded_max_loss_raw && bindings.loaded_max_loss_raw != nullptr)
    result.loaded_max_loss_raw = Load<std::int64_t>(bindings.loaded_max_loss_raw, 0);
  if (!result.loaded_divisor_floor_raw || !result.loaded_max_loss_raw)
    missing("loaded_fleet_supply_adjustment_parameters_unavailable");
  return finish();
}
} // namespace xar::ck3_12003
