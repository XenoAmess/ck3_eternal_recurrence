#pragma once

#include "xar_bridge/army_current_unit_new_date_schedule_inputs_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Root actual174 complete-body receipt; neither direct target is invoked.
inline constexpr std::uintptr_t kUnitNewDateManagerMethodRva12004 = 0x2AD66E0;

inline CurrentUnitNewDateScheduleBindings12004 BindCurrentUnitNewDateSchedule12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return {};
  // Root actual outer20 [22A1D30,22A1D44): GameData+2A508, virtual18.
  // Actual174 supplies the method target; no vtable RVA is copied or guessed.
  return {true, image_base + kUnitNewDateManagerMethodRva12004};
}

namespace unit_new_date_schedule_detail {
template <class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result);
  return result;
}
} // namespace unit_new_date_schedule_detail

// Captured once by the common Strength collector with an enabled exact4 binding.
// Slot18 is read and compared,
// never invoked. The owned vector preserves the initial count and raw order.
inline CurrentUnitNewDateScheduleInventory12004 CaptureCurrentUnitNewDateSchedule12004(
    const CurrentUnitNewDateScheduleBindings12004 &binding,
    const ck3_12002::ArmyBindings &existing) {
  using unit_new_date_schedule_detail::Load;
  CurrentUnitNewDateScheduleInventory12004 result{};
  const auto unavailable = [&](std::string_view reason) {
    result.unavailable_reason = std::string(reason);
    return result;
  };
  if (!binding.enabled || !existing.enabled || binding.expected_new_date_target == 0)
    return unavailable("current_unit_new_date_schedule_binding_unavailable");
  if (existing.game_state_slot == nullptr || *existing.game_state_slot == nullptr)
    return unavailable("current_unit_new_date_schedule_gamestate_unavailable");
  const void *state = *existing.game_state_slot;
  const void *data = Load<const void *>(state, 0xA0);
  if (data == nullptr)
    return unavailable("current_unit_new_date_schedule_gamedata_unavailable");
  // Actual outer22A1D30 loads state+A0; 22A1D37 adds embedded secondary2A508.
  const auto *secondary = static_cast<const std::byte *>(data) + 0x2A508;
  const void *vtable = Load<const void *>(secondary, 0);
  if (vtable == nullptr || Load<std::uintptr_t>(vtable, 0x18) != binding.expected_new_date_target)
    return unavailable("current_unit_new_date_schedule_binding_unavailable");
  // Actual174: 2AD66EA pointer+20, 2AD66EE signed count+2C, fixed end/stride4.
  const void *ids = Load<const void *>(secondary, 0x20);
  const auto count = Load<std::int32_t>(secondary, 0x2C);
  result.vector_header_count_i32 = count;
  result.vector_data_present = ids != nullptr;
  if (count < 0)
    return unavailable("current_unit_new_date_schedule_vector_count_negative");
  if (count > 0 && ids == nullptr)
    return unavailable("current_unit_new_date_schedule_vector_data_unavailable");
  result.stored_unit_ids.emplace();
  result.stored_unit_ids->reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    result.stored_unit_ids->push_back(
        Load<std::uint32_t>(ids, static_cast<std::size_t>(index) * 4));
  }
  result.status = "available";
  return result;
}

// Subject IDs come from the already validated whole Strength row. Raw equality
// does not reproduce the native registry/fallback/tag checks or its callbacks.
inline game::ArmyCurrentUnitNewDateScheduleInputsV1 BuildCurrentUnitNewDateScheduleInputs12004(
    const CurrentUnitNewDateScheduleInventory12004 &capture,
    std::uint32_t subject_army_id, std::optional<std::uint32_t> subject_carmy_id) {
  game::ArmyCurrentUnitNewDateScheduleInputsV1 result{};
  result.subject_army_id_u32 = subject_army_id;
  result.subject_carmy_id_u32 = subject_carmy_id;
  result.vector_header_count_i32 = capture.vector_header_count_i32;
  result.vector_data_present = capture.vector_data_present;
  result.unavailable_reason = capture.unavailable_reason;
  if (capture.status != "available") return result;
  if (!subject_carmy_id) {
    result.unavailable_reason = "current_unit_new_date_schedule_subject_unavailable";
    return result;
  }
  if (!capture.stored_unit_ids) {
    result.unavailable_reason = "current_unit_new_date_schedule_vector_id_unavailable";
    return result;
  }
  result.subject_stored_id_positions.emplace();
  for (std::size_t index = 0; index < capture.stored_unit_ids->size(); ++index) {
    if ((*capture.stored_unit_ids)[index] == subject_army_id)
      result.subject_stored_id_positions->push_back(static_cast<std::int32_t>(index));
  }
  result.subject_stored_id_occurrence_count_i32 =
      static_cast<std::int32_t>(result.subject_stored_id_positions->size());
  result.status = "available";
  result.ready = true;
  result.unavailable_reason.reset();
  return result;
}

} // namespace xar::ck3_12004
