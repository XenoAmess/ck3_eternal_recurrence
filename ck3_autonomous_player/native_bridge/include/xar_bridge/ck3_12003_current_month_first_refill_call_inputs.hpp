#pragma once

// SOURCE_PREPARED / NOTRUN. Cache-derived exact .3 input, no native callback.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_current_month_first_refill_call_inputs_v1.hpp"

#include <cstddef>
#include <cstring>
#include <string_view>

namespace xar::ck3_12003 {
inline CurrentMonthFirstRefillCallBindings12003 BindCurrentMonthFirstRefillCallImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  return {image_base != 0 && executable_sha256 ==
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"};
}

inline game::ArmyCurrentMonthFirstRefillCallInputsV1 ReadCurrentMonthFirstRefillCallInputs12003(
    const CurrentMonthFirstRefillCallBindings12003 &binding,
    const ck3_12002::ArmyBindings &existing, const void *army, const void *unit) {
  game::ArmyCurrentMonthFirstRefillCallInputsV1 result{};
  if (!binding.enabled || !existing.enabled) {
    result.unavailable_reason = "native_month_first_refill_call_bindings_unavailable";
    return result;
  }
  if (army == nullptr || unit == nullptr) {
    result.unavailable_reason = "native_month_first_refill_call_context_unavailable";
    return result;
  }
  std::int32_t unit_id = 0, army_id = 0;
  std::memcpy(&unit_id, static_cast<const std::byte *>(unit) + 0x10, sizeof unit_id);
  std::memcpy(&army_id, static_cast<const std::byte *>(army) + 0x10, sizeof army_id);
  result.subject_army_id = unit_id;
  result.subject_carmy_id = army_id;
  if (existing.game_state_slot == nullptr || *existing.game_state_slot == nullptr) {
    result.unavailable_reason = "native_month_first_game_state_unavailable";
    return result;
  }
  std::uint8_t flags = 0;
  //2A9A2E1 and2A9A675 consume precisely this BYTE, not a DWORD/date-derived value.
  std::memcpy(&flags, static_cast<const std::byte *>(*existing.game_state_slot) + 0xC0,
              sizeof flags);
  result.game_state_calendar_flags_raw_u8 = flags;
  result.month_first_mask_2_set = (flags & 0x02U) != 0;
  result.status = "available";
  result.ready = true;
  return result;
}
} // namespace xar::ck3_12003
