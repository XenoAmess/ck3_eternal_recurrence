#pragma once

#include "xar_bridge/army_future_daily_supply_schedule_v1.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {

inline FutureDailySupplyScheduleBindings12004 BindFutureDailySupplySchedule12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  return {image_base != 0 && executable_sha256 == kExecutableSha256};
}

namespace future_daily_supply_schedule_detail {
template <class T>
inline T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}
} // namespace future_daily_supply_schedule_detail

// AUTHORED_NOTRUN. The application-main Strength caller supplies the validated
// same-query Unit/CArmy pair. Only current headers and original pointer slots
// are read: no native callback, mutator, other-Army dereference or game store.
inline game::ArmyFutureDailySupplyScheduleInputsV1 ReadFutureDailySupplyScheduleInputs12004(
    const FutureDailySupplyScheduleBindings12004 &binding,
    const ck3_12002::ArmyBindings &existing,
    const void *resolved_army, const void *resolved_unit) {
  using future_daily_supply_schedule_detail::Load;
  game::ArmyFutureDailySupplyScheduleInputsV1 result{};
  const auto unavailable = [&](std::string_view reason) {
    result.unavailable_reason = std::string(reason);
    return result;
  };
  if (!binding.enabled || !existing.enabled)
    return unavailable("native_future_daily_supply_schedule_bindings_unavailable");
  if (resolved_army == nullptr || resolved_unit == nullptr)
    return unavailable("same_capture_future_daily_supply_schedule_subject_unavailable");
  result.subject_army_id_u32 = Load<std::uint32_t>(resolved_unit, 0x10);
  result.subject_carmy_id_u32 = Load<std::uint32_t>(resolved_army, 0x10);
  if (existing.game_state_slot == nullptr || *existing.game_state_slot == nullptr)
    return unavailable("future_daily_supply_schedule_game_state_unavailable");
  const void *state = *existing.game_state_slot;
  result.current_date_storage_raw64 = Load<std::int64_t>(state, 0x08);
  result.current_date_raw_i32 = Load<std::int32_t>(state, 0x08);
  result.native_day_index_raw_i32 = Load<std::int32_t>(state, 0x9C);
  result.selected_phase_index_i32 = static_cast<std::int32_t>(
      static_cast<std::uint32_t>(*result.native_day_index_raw_i32) % 30U);
  const void *game_data = Load<const void *>(state, 0xA0);
  if (game_data == nullptr)
    return unavailable("future_daily_supply_schedule_game_data_unavailable");
  const auto *secondary = static_cast<const std::byte *>(game_data) + 0x2A548;
  bool partial = false;
  result.phases.reserve(30);
  for (std::int32_t phase_index = 0; phase_index < 30; ++phase_index) {
    game::ArmyFutureDailySupplySchedulePhaseV1 phase{};
    phase.phase_index_i32 = phase_index;
    const auto *header = secondary + 0x190 +
        static_cast<std::size_t>(phase_index) * 24;
    const void *pointers = Load<const void *>(header, 0);
    const auto count = Load<std::int32_t>(header, 0x0C);
    phase.capacity_raw_i32 = Load<std::int32_t>(header, 0x08);
    phase.count_raw_i32 = count;
    phase.data_pointer_present = pointers != nullptr;
    // The dispatcher consumes signed count and original pointer order.
    // Capacity is retained independently and never gates these inputs.
    if (count < 0) {
      phase.unavailable_reason = "future_daily_supply_schedule_negative_bucket_count";
      partial = true;
    } else if (count > 0 && pointers == nullptr) {
      phase.unavailable_reason = "future_daily_supply_schedule_bucket_pointer_data_unavailable";
      partial = true;
    } else {
      phase.matching_positions.emplace();
      for (std::int32_t index = 0; index < count; ++index) {
        if (Load<const void *>(pointers, static_cast<std::size_t>(index) * 8) == resolved_army)
          phase.matching_positions->push_back(index);
      }
      phase.subject_occurrence_count_i32 =
          static_cast<std::int32_t>(phase.matching_positions->size());
      phase.status = "available";
      phase.ready = true;
    }
    result.phases.push_back(std::move(phase));
  }
  result.status = partial ? "partial" : "available";
  result.ready = !partial;
  if (partial)
    result.unavailable_reason = "future_daily_supply_schedule_phase_inputs_partial";
  return result;
}

} // namespace xar::ck3_12004
