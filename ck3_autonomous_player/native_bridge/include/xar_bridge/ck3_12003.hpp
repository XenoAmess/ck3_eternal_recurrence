#pragma once

#include "xar_bridge/ck3_12002.hpp"

// CK3 1.20.0.3 Crozier, Steam build 25652598. The frozen .3 foundation
// and complete production ABI comparison preserve these .2 addresses/layouts.
// This is a separate exact executable identity, never a wildcard patch gate.
namespace xar::ck3_12003 {
inline constexpr char kGameVersion[] = "1.20.0.3";
inline constexpr char kAdapterId[] = "ck3-1.20.0.3-msvc-x64";
inline constexpr char kExecutableSha256[] =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr auto kJominiStateSlotRva = ck3_12002::kJominiStateSlotRva;
inline constexpr auto kGameStateSlotRva = ck3_12002::kGameStateSlotRva;
inline constexpr auto kCharacterStorageSlotRva = ck3_12002::kCharacterStorageSlotRva;
inline constexpr auto kPlayerCharacterManagerOffset = ck3_12002::kPlayerCharacterManagerOffset;
inline constexpr auto kCharacterDeathDataOffset = ck3_12002::kCharacterDeathDataOffset;
inline constexpr auto kGetLocalPlayerRva = ck3_12002::kGetLocalPlayerRva;
} // namespace xar::ck3_12003
