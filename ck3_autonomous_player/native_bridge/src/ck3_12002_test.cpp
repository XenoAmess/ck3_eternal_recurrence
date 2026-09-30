#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <iostream>

int main() {
  using namespace xar::ck3_12002;
  // Synthetic copies use the independently disassembled engine field offsets.
  // Sentinels around fields catch width/offset mistakes and stale output reuse.
  std::array<std::byte, 0x78> state;
  state.fill(std::byte{0xA5});
  std::array<std::byte, 0x28> jomini{};
  const std::int32_t date = 53175816;
  std::memcpy(state.data() + 8, &date, 4);
  ClockPrefix clock{};
  for (std::int32_t native_speed = 0; native_speed < 5; ++native_speed) {
    std::memcpy(state.data() + 0x70, &native_speed, 4);
    for (const bool paused : {false, true}) {
      jomini[0x20] = paused ? std::byte{1} : std::byte{};
      if (!DecodeClockPrefix(state, jomini, clock) || clock.date_raw != date ||
          clock.speed != native_speed + 1 || clock.paused != paused) {
        return 1;
      }
    }
  }
  for (const std::int32_t invalid : {-1, 5}) {
    std::memcpy(state.data() + 0x70, &invalid, 4);
    if (DecodeClockPrefix(state, jomini, clock) || clock.speed != 0 ||
        clock.date_raw != 0 || clock.paused) {
      return 2;
    }
  }
  if (DecodeClockPrefix(std::span(state).first(0x73), jomini, clock) ||
      DecodeClockPrefix(state, std::span(jomini).first(0x20), clock)) {
    return 3;
  }
  std::array<std::byte, 0x1F8> players{};
  std::int32_t player = 7, decoded = 0;
  std::memcpy(players.data() + 0x1F0, &player, 4);
  if (!DecodeLocalPlayerId(players, decoded) || decoded != player ||
      DecodeLocalPlayerId(std::span(players).first(0x1F3), decoded) ||
      decoded != -1) {
    return 4;
  }
  // Native UI construction writes these exact 0x28-byte payloads. These are
  // stack-owned values only; this test never queues a game command.
  constexpr std::uintptr_t base = 0x140000000;
  std::array<std::byte, 0x28> expected{};
  const std::uintptr_t primary = base + 0x476C898;
  const std::uintptr_t secondary = base + 0x476C868;
  std::memcpy(expected.data(), &primary, 8);
  expected[8] = std::byte{8};
  std::memcpy(expected.data() + 0x18, &secondary, 8);
  std::memcpy(expected.data() + 0x20, &player, 4);
  expected[0x24] = std::byte{1};
  const auto pause = MakePauseCommand(base, player, true);
  if (std::memcmp(&pause, expected.data(), expected.size()) != 0 ||
      MakePauseCommand(base, player, false).paused != 0) {
    return 5;
  }
  for (std::int32_t speed = 1; speed <= 5; ++speed) {
    const auto command = MakeSetSpeedCommand(base, speed);
    if (!command || command->value != speed - 1 || command->flags != 0 ||
        command->paused != 0 ||
        command->primary_vtable != base + 0x476C708 ||
        command->secondary_vtable != base + 0x476C640) {
      return 6;
    }
  }
  if (MakeSetSpeedCommand(base, 0) || MakeSetSpeedCommand(base, 6)) {
    return 7;
  }
  std::cout << "PASS 1.20.0.2 offline clock/player/pause/speed fixtures\n";
}
