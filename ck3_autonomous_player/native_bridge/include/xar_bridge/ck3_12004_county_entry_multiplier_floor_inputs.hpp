#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {

struct CountyEntryMultiplierFloorBindings12004 {
  bool enabled = false;
  const std::int64_t *base_floor_raw = nullptr;
  const std::int64_t *army_1d4_nonzero_floor_raw = nullptr;
  // Same guarded copy primitive as the existing readonly collectors. Override
  // supports a bounded owning-query reader; it never invokes a native getter.
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
};

namespace county_multiplier_floor_detail {
template<class T>
inline std::optional<T> Read(const CountyEntryMultiplierFloorBindings12004 &b,
                            const void *object, std::size_t offset = 0) noexcept {
  if (!object) return std::nullopt;
  T value{};
  const void *address = static_cast<const std::byte *>(object) + offset;
  const bool copied = b.read_memory
      ? b.read_memory(b.read_context, address, &value, sizeof value)
      : ck3_12002::current_stored_context_12003::CopyBytes(&value, address, sizeof value);
  return copied ? std::optional<T>{value} : std::nullopt;
}

inline bool Identity(const CountyEntryMultiplierFloorBindings12004 &b,
                     const void *army, const void *unit,
                     std::int32_t army_id, std::int32_t unit_id) noexcept {
  return army_id != -1 && unit_id != -1 &&
      Read<std::int32_t>(b, army, 0x10) == army_id &&
      Read<std::int32_t>(b, unit, 0x10) == unit_id &&
      Read<std::int32_t>(b, army, 0x124) == unit_id &&
      Read<std::int32_t>(b, unit, 0x178) == army_id;
}
} // namespace county_multiplier_floor_detail

inline game::ArmyCountyEntryMultiplierFloorInputsV1 SampleCountyEntryMultiplierFloors12004(
    const CountyEntryMultiplierFloorBindings12004 &b, const void *army,
    const void *unit, std::int32_t army_id, std::int32_t unit_id) noexcept {
  using county_multiplier_floor_detail::Read;
  game::ArmyCountyEntryMultiplierFloorInputsV1 out{};
  if (!b.base_floor_raw || !b.army_1d4_nonzero_floor_raw) {
    out.unavailable_reason = "county_multiplier_floor_bindings_unavailable";
    return out;
  }
  if (!county_multiplier_floor_detail::Identity(b, army, unit, army_id, unit_id)) {
    out.unavailable_reason = "county_multiplier_floor_army_unit_identity_unavailable";
    return out;
  }
  const auto base = Read<std::int64_t>(b, b.base_floor_raw);
  const auto nonzero = Read<std::int64_t>(b, b.army_1d4_nonzero_floor_raw);
  const auto flag = Read<std::uint8_t>(b, army, 0x1D4);
  if (!base || !nonzero || !flag) {
    out.unavailable_reason = !base ? "county_multiplier_base_floor_read_failed"
        : !nonzero ? "county_multiplier_army_1d4_nonzero_floor_read_failed"
                   : "county_multiplier_army_1d4_read_failed";
    return out;
  }
  if (!county_multiplier_floor_detail::Identity(b, army, unit, army_id, unit_id)) {
    out.unavailable_reason = "county_multiplier_floor_army_unit_identity_changed";
    return out;
  }
  out.available = true;
  out.base_floor_raw = *base;
  out.army_1d4_nonzero_floor_raw = *nonzero;
  out.army_1d4_raw = *flag;
  return out;
}

// The caller samples before and after its existing county getters. No extra
// native call is made. Any changed operand invalidates only this child.
inline game::ArmyCountyEntryMultiplierFloorInputsV1 FinishCountyEntryMultiplierFloors12004(
    const game::ArmyCountyEntryMultiplierFloorInputsV1 &before,
    const game::ArmyCountyEntryMultiplierFloorInputsV1 &after) noexcept {
  if (!before.available) return before;
  if (!after.available) return after;
  if (before == after) return after;
  game::ArmyCountyEntryMultiplierFloorInputsV1 out{};
  out.unavailable_reason = "county_multiplier_floor_inputs_changed_during_read";
  return out;
}

} // namespace xar::ck3_12004
