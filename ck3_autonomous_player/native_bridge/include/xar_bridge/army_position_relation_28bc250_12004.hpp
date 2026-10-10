#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

// Derived from BOTH retained actual4 lookup tail instructions; no new scan.
inline constexpr std::uintptr_t kArmyPositionRelationFallbackSlot12004 =
    0x5D27B70;

struct ArmyPositionRelation28BC25012004 {
  std::optional<std::uintptr_t> relation_identity;
  // Full raw 32-bit field. -1 is the caller's valid no-war sentinel.
  std::optional<std::int32_t> war_id;
  std::string unavailable_reason;
};

// Pure guarded reads matching held actual4 28BC250..28BC300. The caller
// supplies the actual holder/selected Character pointers from its same frame.
// This does not invoke a native getter, create a relation, resolve CWar,
// assign a relation kind, or substitute a current query for the original frame.
ArmyPositionRelation28BC25012004 ReadArmyPositionRelation28BC25012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t owner, std::uintptr_t toward) noexcept;

} // namespace xar::ck3_12004
