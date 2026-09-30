#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

// Offline-tested foundation for the new adapter. No runtime registration or
// automatic process discovery; owning-thread and full snapshot paths pending.
namespace xar::ck3_12002 {

inline constexpr char kExecutableSha256[] =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kJominiStateSlotRva = 0x5C6A520;
inline constexpr std::uintptr_t kGameStateSlotRva = 0x5C68C50;
inline constexpr std::uintptr_t kCharacterStorageSlotRva = 0x5C67568;
inline constexpr std::size_t kPlayerCharacterManagerOffset = 0x222E8;
inline constexpr std::size_t kCharacterDeathDataOffset = 0x1D0;
inline constexpr std::uintptr_t kGetLocalPlayerRva = 0x383E2B0;
inline constexpr std::uintptr_t kPausePrimaryVtableRva = 0x476C898;
inline constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x476C868;
inline constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x476C708;
inline constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x476C640;

struct ClockPrefix {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0; // Public speed 1..5.
  bool paused = false;
};

// Caller-owned copies only: this function does not read a running process.
bool DecodeClockPrefix(std::span<const std::byte> game_state,
                       std::span<const std::byte> jomini_state,
                       ClockPrefix &output) noexcept;
bool DecodeLocalPlayerId(std::span<const std::byte> players,
                         std::int32_t &output) noexcept;

using GetLocalPlayer = void *(*)(void *jomini_state);
struct CoreBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void **character_storage_slot = nullptr;
  GetLocalPlayer get_local_player = nullptr;
};

// Pure address calculation. The caller supplies its own module base/hash;
// this function neither discovers a process nor dereferences these addresses.
CoreBindings BindCoreImage(std::uintptr_t image_base,
                           std::string_view executable_sha256) noexcept;

struct CoreSnapshotPrefix {
  ClockPrefix clock;
  std::int32_t local_player_id = -1;
  bool map_ready = false;
  bool has_played_character = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
};

// In-process reader, currently exercised only with fixture-owned objects.
// Events, relationships, wars, armies and settlement are separate pending
// migrations: this prefix must not be published as the complete Snapshot.
bool ReadCoreSnapshot(const CoreBindings &bindings,
                      CoreSnapshotPrefix &output) noexcept;

struct alignas(8) TimeCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> reserved{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t value = 0; // PlayerID for pause; native speed for set-speed.
  std::uint8_t paused = 0;
  std::array<std::byte, 3> tail{};
};
static_assert(sizeof(TimeCommand) == 0x28);
static_assert(offsetof(TimeCommand, flags) == 0x08);
static_assert(offsetof(TimeCommand, secondary_vtable) == 0x18);
static_assert(offsetof(TimeCommand, value) == 0x20);
static_assert(offsetof(TimeCommand, paused) == 0x24);

TimeCommand MakePauseCommand(std::uintptr_t image_base,
                             std::int32_t player_id, bool paused) noexcept;
std::optional<TimeCommand> MakeSetSpeedCommand(std::uintptr_t image_base,
                                              std::int32_t public_speed) noexcept;

} // namespace xar::ck3_12002
