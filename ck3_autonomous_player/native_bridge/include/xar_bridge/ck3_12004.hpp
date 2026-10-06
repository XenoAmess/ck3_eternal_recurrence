#pragma once

#include "xar_bridge/ck3_12002.hpp"

// CK3 1.20.0.4 Crozier, Steam build 25734779. Root's frozen PE metadata
// identifies the native ASCII version at RVA 71871232/file offset 71866624.
// Address and layout bindings require the separate actual-build ABI ledger.
namespace xar::ck3_12004 {
inline constexpr char kGameVersion[] = "1.20.0.4";
inline constexpr char kAdapterId[] = "ck3-1.20.0.4-msvc-x64";
inline constexpr char kSteamBuildId[] = "25734779";
inline constexpr char kExecutableSha256[] =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

// Actual .4 source-use operands: CORE-LAYOUT-OPERAND-PAIRS.json, frozen 0597.
// The mapped GetLocalPlayer body is in CORE-FUNCTION-MAP.json.
inline constexpr std::uintptr_t kJominiStateSlotRva = 0x5C6A520;
inline constexpr std::uintptr_t kGameStateSlotRva = 0x5C68C50;
inline constexpr std::uintptr_t kCharacterStorageSlotRva = 0x5C67568;
inline constexpr std::uintptr_t kGetLocalPlayerRva = 0x383E290;
inline constexpr std::size_t kPlayerCharacterManagerOffset = 0x222E8;
inline constexpr std::size_t kCharacterDeathDataOffset = 0x1D0;
inline constexpr std::size_t kGameStateDateOffset = 0x08;
inline constexpr std::size_t kGameStateSpeedOffset = 0x70;
inline constexpr std::size_t kGameStateDataOffset = 0xA0;
inline constexpr std::size_t kJominiPlayersOffset = 0x18;
inline constexpr std::size_t kJominiPausedOffset = 0x20;
inline constexpr std::size_t kPlayersLocalPlayerIdOffset = 0x1F0;
inline constexpr std::size_t kPlayerIdOffset = 0x70;
inline constexpr std::size_t kPlayerManagerEntriesOffset = 0x58;
inline constexpr std::size_t kPlayerManagerCountOffset = 0x64;
inline constexpr std::size_t kPlayerEntryLocalPlayerIdOffset = 0xD8;
inline constexpr std::size_t kPlayerEntryCharacterIdOffset = 0xB0;
inline constexpr std::size_t kCharacterStorageSlotsOffset = 0x20;
inline constexpr std::size_t kCharacterStorageCapacityOffset = 0x2C;
inline constexpr std::size_t kCharacterStorageSlotStride = 0x10;
inline constexpr std::size_t kCharacterStorageObjectOffset = 0x08;
inline constexpr std::size_t kCharacterFullIdOffset = 0x18;

// These are caller-owned software DTOs, not an admission of old image RVAs.
using CoreBindings = ck3_12002::CoreBindings;
using ClockPrefix = ck3_12002::ClockPrefix;
using CoreSnapshotPrefix = ck3_12002::CoreSnapshotPrefix;
CoreBindings BindCoreImage(std::uintptr_t image_base,
                           std::string_view executable_sha256) noexcept;
void *ResolveCoreCharacter(const CoreBindings &bindings,
                           std::int32_t character_id) noexcept;
bool ReadCoreSnapshot(const CoreBindings &bindings,
                      CoreSnapshotPrefix &output) noexcept;
bool DecodeClockPrefix(std::span<const std::byte> game_state,
                       std::span<const std::byte> jomini_state,
                       ClockPrefix &output) noexcept;
} // namespace xar::ck3_12004
