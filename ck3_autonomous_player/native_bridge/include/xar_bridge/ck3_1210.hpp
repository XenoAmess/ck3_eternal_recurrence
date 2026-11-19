#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

// Installation identity supplied by Runtime M0. No address or layout is
// admitted by these constants; Florin gameplay bindings remain unported.
namespace xar::ck3_1210 {
enum class ImageBuildV1 { original26622941, hotfix26757580, unknown };
inline constexpr char kGameVersion[] = "1.21.0";
inline constexpr char kAdapterId[] = "ck3-1.21.0-msvc-x64";
inline constexpr char kSteamBuildId[] = "26622941";
inline constexpr char kExecutableSha256[] =
    "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
inline constexpr std::size_t kExecutableFileSize = 114756216;
// Florin native source-use operands. The evidence ledger records the exact
// executable and instruction windows; these do not admit any other build.
inline constexpr std::uintptr_t kJominiStateSlotRva = 0x68B3800;
inline constexpr std::uintptr_t kGameStateSlotRva = 0x68B1D58;
inline constexpr std::uintptr_t kCharacterStorageSlotRva = 0x68A8628;
inline constexpr std::uintptr_t kGetLocalPlayerRva = 0x3E653B0;
inline constexpr std::size_t kPlayerCharacterManagerOffset = 0x26F58;
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

struct ClockPrefix {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0;
  bool paused = false;
};
using GetLocalPlayer = void *(*)(void *jomini_state);
struct CoreBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void **character_storage_slot = nullptr;
  GetLocalPlayer get_local_player = nullptr;
  ImageBuildV1 image_build = ImageBuildV1::original26622941;
};
struct CoreSnapshotPrefix {
  ClockPrefix clock{};
  std::int32_t local_player_id = -1;
  bool map_ready = false;
  bool has_played_character = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
};
// Address calculation only; process discovery and all live ownership remain
// with the caller. A nonmatching hash returns an entirely empty binding.
CoreBindings BindCoreImage(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
void *ResolveCoreCharacter(const CoreBindings &bindings,
    std::int32_t character_id) noexcept;
bool ReadCoreSnapshot(const CoreBindings &bindings,
    CoreSnapshotPrefix &output) noexcept;
bool DecodeClockPrefix(std::span<const std::byte> game_state,
    std::span<const std::byte> jomini_state, ClockPrefix &output) noexcept;
} // namespace xar::ck3_1210
