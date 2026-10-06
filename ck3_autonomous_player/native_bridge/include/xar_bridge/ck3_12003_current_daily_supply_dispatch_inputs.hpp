#pragma once
#include "xar_bridge/army_current_daily_supply_dispatch_inputs_v1.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace xar::ck3_12003 {
inline CurrentDailySupplyDispatchBindings12003 BindCurrentDailySupplyDispatch12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  return {image_base != 0 && executable_sha256 ==
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"};
}
namespace daily_supply_dispatch_detail {
template <class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result);
  return result;
}
} // namespace daily_supply_dispatch_detail

// SOURCE_PREPARED/NOTRUN. Owning-thread Strength caller already resolved full
// Unit/CArmy identity and the Unit backlink. No native function is invoked.
inline game::ArmyCurrentDailySupplyDispatchInputsV1 ReadCurrentDailySupplyDispatchInputs12003(
    const CurrentDailySupplyDispatchBindings12003 &binding,
    const ck3_12002::ArmyBindings &existing, const void *army, const void *unit,
    const game::ArmySupplyTimingSnapshot *same_capture_clock = nullptr) {
  using daily_supply_dispatch_detail::Load;
  game::ArmyCurrentDailySupplyDispatchInputsV1 result{};
  const auto unavailable = [&](std::string_view reason) {
    result.unavailable_reason = std::string(reason);
    return result;
  };
  if (!binding.enabled || !existing.enabled)
    return unavailable("native_daily_supply_dispatch_bindings_unavailable");
  if (army == nullptr || unit == nullptr)
    return unavailable("same_capture_daily_supply_dispatch_subject_unavailable");
  result.subject_army_id = Load<std::int32_t>(unit, 0x10);
  result.subject_carmy_id = Load<std::int32_t>(army, 0x10);
  if (existing.game_state_slot == nullptr || *existing.game_state_slot == nullptr)
    return unavailable("daily_supply_dispatch_game_state_unavailable");
  const void *state = *existing.game_state_slot;
  if (same_capture_clock != nullptr) {
    result.current_date_raw = same_capture_clock->current_date_raw;
    result.native_day_index = same_capture_clock->native_day_index;
  }
  if (!result.current_date_raw) result.current_date_raw = Load<std::int32_t>(state, 8);
  if (!result.native_day_index) result.native_day_index = Load<std::int32_t>(state, 0x9C);
  // The original dispatcher uses unsigned stored D, not calendar/date arithmetic.
  const auto phase = static_cast<std::uint32_t>(*result.native_day_index) % 30U;
  result.selected_bucket_phase = static_cast<std::int32_t>(phase);
  const void *data = Load<const void *>(state, 0xA0);
  if (data == nullptr) return unavailable("daily_supply_dispatch_game_data_unavailable");
  const auto *secondary = static_cast<const std::byte *>(data) + 0x2A548;
  const auto *bucket = secondary + 0x190 + static_cast<std::size_t>(phase) * 24;
  const void *pointers = Load<const void *>(bucket, 0);
  const auto capacity = Load<std::int32_t>(bucket, 8);
  const auto count = Load<std::int32_t>(bucket, 0xC);
  result.selected_bucket_capacity_raw = capacity;
  result.selected_bucket_count_raw = count;
  result.selected_bucket_data_present = pointers != nullptr;
  // The dispatcher consumes count and original pointer order; capacity is only
  // independent raw context and never changes dispatch-input readiness.
  if (count < 0 || (count > 0 && pointers == nullptr))
    return unavailable("daily_supply_dispatch_bucket_header_invalid");
  result.subject_occurrence_indices.emplace();
  for (std::int32_t index = 0; index < count; ++index) {
    if (Load<const void *>(pointers, static_cast<std::size_t>(index) * 8) == army)
      result.subject_occurrence_indices->push_back(index);
  }
  result.subject_dispatch_occurrence_count =
      static_cast<std::int32_t>(result.subject_occurrence_indices->size());
  result.status = "available";
  result.ready = true;
  return result;
}
} // namespace xar::ck3_12003
