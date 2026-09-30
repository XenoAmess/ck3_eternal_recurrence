#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

// Offline-tested foundation for the new adapter. No runtime registration or
// process binding until the owning-thread and complete snapshot paths migrate.
namespace xar::ck3_12002 {

inline constexpr char kExecutableSha256[] =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kJominiStateSlotRva = 0x5C6A520;
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
