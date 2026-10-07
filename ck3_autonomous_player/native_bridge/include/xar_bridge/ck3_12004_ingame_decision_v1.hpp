#pragma once

#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

// Finite named primary-vtable/COL/type-name closure from the actual .4 image.
// These are individually verified tables, not a table-shift rule.
struct IngameDecisionTypeIdentity12004V1 {
  std::uintptr_t vtable_rva;
  std::uint32_t type_descriptor_rva;
};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionApplicationType12004V1{0x449BDB8,0x5667F58};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionLogicalType12004V1{0x44D6058,0x55072C0};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionGfxType12004V1{0x44BC418,0x5514460};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionHandlerType12004V1{0x44BA8A0,0x5694B20};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionListType12004V1{0x455CC90,0x5794D80};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionDetailType12004V1{0x455D4F8,0x5795050};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionDefinitionType12004V1{0x48BD150,0x5586B90};
inline constexpr IngameDecisionTypeIdentity12004V1 kDecisionNullDefinitionType12004V1{0x48931A0,0x5AB0518};

// Complete original getter/OnSelect/wrapper/SetDecision instruction spans.
inline constexpr std::uintptr_t kDecisionGroupsGetterRva12004V1 = 0x1456090;
inline constexpr std::uintptr_t kDecisionDefinitionGetterRva12004V1 = 0xA935B0;
inline constexpr std::uintptr_t kDecisionRowOnSelectRva12004V1 = 0x14582B0;
inline constexpr std::uintptr_t kDecisionRowOnSelectWrapperRva12004V1 = 0x1459510;
inline constexpr std::uintptr_t kDecisionSetDecisionRva12004V1 = 0x1471630;
// SetDecision's actual tail edge names this function; the existing guard pins
// only its first 32 bytes and makes no complete-body claim for that prefix.
inline constexpr std::uintptr_t kDecisionDetailDispatchRva12004V1 = 0x1471210;
inline constexpr std::uintptr_t kDecisionActorReferenceSlotRva12004V1 = 0x54DBC00;

} // namespace xar::ck3_12004
