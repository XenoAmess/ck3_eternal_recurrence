#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {

// Actual unique callbacks and the primary controller table are closed by
// deathmapper-onlypacket/FAMILY-MAP.json and SUCCESSION-WINDOW-TABLE.json.
// Shared handler identity is closed by Faith's route-tables. The actual .4
// IngameHandlerGetter-DETAIL.json closes both cast types and root+10/idler+88.
// These are source-defined native input pins, not a live-readiness claim.
inline constexpr bool kSuccessionModalNativePinsReady12004 = true;
inline constexpr std::uintptr_t kSuccessionRuntimeDynamicCastRva12004 = 0x4260E74;
inline constexpr std::uintptr_t kSuccessionIdlerBaseTypeDescriptorRva12004 = 0x5514438;
inline constexpr std::uintptr_t kSuccessionIngameIdlerTypeDescriptorRva12004 = 0x5514460;
inline constexpr std::uintptr_t kSuccessionHandlerPrimaryVtableRva12004 = 0x44BA8A0;
inline constexpr std::uintptr_t kSuccessionControllerPrimaryVtableRva12004 = 0x4522DA0;
inline constexpr std::uintptr_t kSuccessionControllerCloseRva12004 = 0x10D8900;
inline constexpr std::uintptr_t kSuccessionControllerOpenRva12004 = 0x10D8BC0;
inline constexpr std::uintptr_t kIsPausedBySuccessionRva12004 = 0xA7C440;
inline constexpr std::uintptr_t kHasOpenSuccessionRva12004 = 0xA7C4D0;
inline constexpr std::size_t kSuccessionIdlerBaseOffset12004 = 0x10;
inline constexpr std::size_t kSuccessionIngameHandlerOffset12004 = 0x88;
inline constexpr std::size_t kSuccessionHandlerControllerOffset12004 = 0x260;
inline constexpr std::size_t kSuccessionControllerOpenVslot12004 = 0x38;
inline constexpr std::size_t kSuccessionControllerCloseVslot12004 = 0x88;

} // namespace xar::ck3_12004
