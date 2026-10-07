#pragma once

#include "xar_bridge/army_current_unit_new_date_callback_entry_inputs_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace xar::ck3_12004 {

inline CurrentUnitNewDateCallbackEntryBindings12004 BindCurrentUnitNewDateCallbackEntryInputs12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  // Root source-qualified actual [24AB6B0,24AB6D7) complete39-byte prefix.
  return {image_base != 0 && executable_sha256 == kExecutableSha256};
}

namespace unit_new_date_callback_entry_detail {
template <class T> inline T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result);
  return result;
}
} // namespace unit_new_date_callback_entry_detail

// The common production whole collector resolves the scoped Unit and supplies
// normalized IDs. No CArmy receiver is read and no native function is called.
inline game::ArmyCurrentUnitNewDateCallbackEntryInputsV1 ReadCurrentUnitNewDateCallbackEntryInputs12004(
    const CurrentUnitNewDateCallbackEntryBindings12004 &binding,
    const void *unit, std::uint32_t subject_army_id,
    std::optional<std::uint32_t> subject_carmy_id) {
  using unit_new_date_callback_entry_detail::Load;
  game::ArmyCurrentUnitNewDateCallbackEntryInputsV1 result{};
  result.subject_army_id_u32 = subject_army_id;
  result.subject_carmy_id_u32 = subject_carmy_id;
  const auto unavailable = [&](std::string_view reason) {
    result.unavailable_reason = std::string(reason);
    return result;
  };
  if (!binding.enabled)
    return unavailable("current_unit_new_date_callback_entry_binding_unavailable");
  if (unit == nullptr)
    return unavailable("current_unit_new_date_callback_entry_subject_unavailable");
  // Only the actual174 caller's source-used Unit tag/sentinel admission.
  if (Load<std::uint32_t>(unit, 0x14) != 0x556E6974U ||
      Load<std::int32_t>(unit, 0x10) == -1)
    return unavailable("current_unit_new_date_callback_entry_unit_type_unavailable");
  // Actual39: 24AB6C7 compares this exact signed raw field to0; negatives
  // are observed values and select the nonzero branch, not an unavailable gate.
  result.unit_route_count_i32 = Load<std::int32_t>(unit, 0x44);
  result.status = "available";
  result.ready = true;
  return result;
}

} // namespace xar::ck3_12004
