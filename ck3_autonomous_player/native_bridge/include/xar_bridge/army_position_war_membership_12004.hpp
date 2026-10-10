#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"
#include <optional>
#include <vector>

namespace xar::ck3_12004 {
struct ArmyPositionWarMembershipSide12004Read {
  std::optional<std::int32_t> raw_count;
  std::optional<bool> data_present;
  // Stored order, duplicates and full generation bits survive. Native first
  // match stops the scan; this is the evaluated prefix, not a full roster.
  std::vector<std::optional<std::int32_t>> evaluated_full_ids;
  std::optional<std::size_t> matched_index;
  ArmyRegularCoreReadonlyPredicate12004 predicate;
};

// Actual callback2494B30: CMP DWORD[RCX+8],EDX; SETE AL; RET.
bool ArmyPositionParticipantMatchesFullId12004(
    std::int32_t record_full_id, std::int32_t requested_full_id) noexcept;

// Descriptor is the actual caller-supplied RCX, not a War object. This helper
// consumes only descriptor+8 data, signed count+14, pointer stride8 and record+8
// full DWORD IDs. Root owns exact-build/frame/read-budget binding.
ArmyPositionWarMembershipSide12004Read ReadArmyWarMembershipSide12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t descriptor,
    std::int32_t requested_full_id) noexcept;

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2494B4012004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t descriptor,
    std::int32_t requested_full_id) noexcept;
} // namespace xar::ck3_12004
