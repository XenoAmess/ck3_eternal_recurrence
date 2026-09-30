#include "xar_bridge/ck3_12002.hpp"

#include <cstring>

namespace xar::ck3_12002 {

bool DecodeClockPrefix(std::span<const std::byte> game_state,
                       std::span<const std::byte> jomini_state,
                       ClockPrefix &output) noexcept {
  output = {};
  if (game_state.size() < 0x74 || jomini_state.size() < 0x21) {
    return false;
  }
  std::int32_t native_speed = 0;
  std::memcpy(&native_speed, game_state.data() + 0x70, sizeof(native_speed));
  if (native_speed < 0 || native_speed > 4) {
    return false;
  }
  std::memcpy(&output.date_raw, game_state.data() + 0x08,
              sizeof(output.date_raw));
  output.speed = native_speed + 1;
  output.paused = jomini_state[0x20] != std::byte{};
  return true;
}

bool DecodeLocalPlayerId(std::span<const std::byte> players,
                         std::int32_t &output) noexcept {
  output = -1;
  if (players.size() < 0x1F4) {
    return false;
  }
  std::memcpy(&output, players.data() + 0x1F0, sizeof(output));
  return true;
}

TimeCommand MakePauseCommand(std::uintptr_t image_base,
                             std::int32_t player_id, bool paused) noexcept {
  TimeCommand result{};
  result.primary_vtable = image_base + kPausePrimaryVtableRva;
  result.secondary_vtable = image_base + kPauseSecondaryVtableRva;
  result.flags = 8;
  result.value = player_id;
  result.paused = paused ? 1 : 0;
  return result;
}

std::optional<TimeCommand> MakeSetSpeedCommand(std::uintptr_t image_base,
                                              std::int32_t public_speed) noexcept {
  if (public_speed < 1 || public_speed > 5) {
    return std::nullopt;
  }
  TimeCommand result{};
  result.primary_vtable = image_base + kSetSpeedPrimaryVtableRva;
  result.secondary_vtable = image_base + kSetSpeedSecondaryVtableRva;
  result.value = public_speed - 1;
  return result;
}

} // namespace xar::ck3_12002
