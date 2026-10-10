#include "xar_bridge/army_position_war_membership_12004.hpp"
#include <utility>

namespace xar::ck3_12004 {
namespace {
template <typename T>
bool Copy(const ArmyRegularCoreReadonlyAccess12004 &access,
          std::uintptr_t address, T &value) noexcept {
  return access.read(access.read_context, address, &value, sizeof(value));
}
} // namespace

bool ArmyPositionParticipantMatchesFullId12004(
    std::int32_t record_full_id, std::int32_t requested_full_id) noexcept {
  return record_full_id == requested_full_id;
}

ArmyPositionWarMembershipSide12004Read ReadArmyWarMembershipSide12004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t descriptor, std::int32_t requested_full_id) noexcept {
  ArmyPositionWarMembershipSide12004Read out;
  auto &reason = out.predicate.unavailable_reason;
  if (access.read == nullptr || descriptor == 0) {
    reason = "army_position_membership_descriptor_unavailable";
    return out;
  }
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  if (!Copy(access, descriptor + 8, data)) {
    reason = "army_position_membership_data_header_unread";
    return out;
  }
  out.data_present = data != 0;
  if (!Copy(access, descriptor + 0x14, count)) {
    reason = "army_position_membership_count_unread";
    return out;
  }
  out.raw_count = count;
  if (count < 0 || static_cast<std::size_t>(count) > access.maximum_occurrences) {
    reason = "army_position_membership_count_unavailable";
    return out;
  }
  if (count != 0 && data == 0) {
    reason = "army_position_membership_nonempty_data_absent";
    return out;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    out.evaluated_full_ids.emplace_back();
    std::uintptr_t record = 0;
    if (!Copy(access, data + static_cast<std::uintptr_t>(index) * 8, record) ||
        record == 0) {
      reason = "army_position_membership_record_unavailable";
      return out;
    }
    std::int32_t raw_id = 0;
    if (!Copy(access, record + 8, raw_id)) {
      reason = "army_position_membership_record_id_unread";
      return out;
    }
    out.evaluated_full_ids.back() = raw_id;
    if (ArmyPositionParticipantMatchesFullId12004(raw_id, requested_full_id)) {
      out.matched_index = static_cast<std::size_t>(index);
      break;
    }
  }
  // Actual2494B8C/90 reread the descriptor's data/count before returning.
  // A changed/unread ending header cannot certify this captured prefix.
  std::uintptr_t ending_data = 0;
  std::int32_t ending_count = 0;
  if (!Copy(access, descriptor + 8, ending_data) ||
      !Copy(access, descriptor + 0x14, ending_count)) {
    reason = "army_position_membership_ending_header_unread";
    return out;
  }
  if (ending_data != data || ending_count != count) {
    reason = "army_position_membership_header_changed";
    return out;
  }
  out.predicate.value = out.matched_index.has_value();
  return out;
}

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2494B4012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t descriptor, std::int32_t requested_full_id) noexcept {
  return ReadArmyWarMembershipSide12004(access, descriptor,
                                       requested_full_id).predicate;
}
} // namespace xar::ck3_12004
