#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
void *fixture_local_player = nullptr;
void *GetFixtureLocalPlayer(void *) { return fixture_local_player; }

template <typename T>
void Put(std::span<std::byte> bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

bool CheckCoreSnapshot() {
  using namespace xar::ck3_12002;
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data(0x36780);
  std::array<std::byte, 0xE0> other{}, stale{}, current{};
  std::array<void *, 3> entries{other.data(), stale.data(), current.data()};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x80> slots{};
  std::array<std::byte, 0x1D8> character{};
  constexpr std::int32_t id = 0x03000004;
  Put(state, 8, std::int32_t{53175816});
  Put(state, 0x70, std::int32_t{2});
  Put(state, 0xA0, data.data());
  Put(jomini, 0x18, players.data());
  jomini[0x20] = std::byte{1};
  Put(players, 0x1F0, std::int32_t{7});
  Put(player, 0x70, std::int32_t{7});
  Put(std::span(data), 0x222E8 + 0x58, entries.data());
  Put(std::span(data), 0x222E8 + 0x64, std::int32_t{3});
  Put(other, 0xD8, std::int32_t{8});
  Put(other, 0xB0, id);
  Put(stale, 0xD8, std::int32_t{7});
  Put(stale, 0xB0, std::int32_t{0x02000004});
  Put(current, 0xD8, std::int32_t{7});
  Put(current, 0xB0, id);
  Put(storage, 0x20, slots.data());
  Put(storage, 0x2C, std::int32_t{8});
  Put(slots, 4 * 0x10 + 8, character.data());
  Put(character, 0x18, id);
  // A non-null value at the OLD death offset proves that stale-layout reads
  // cannot silently pass this fixture. The new death pointer remains null.
  Put(character, 0x1C8, static_cast<void *>(other.data()));
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *storage_pointer = storage.data();
  CoreBindings bindings{true, &state_pointer, &jomini_pointer, &storage_pointer,
                        &GetFixtureLocalPlayer};
  CoreSnapshotPrefix snapshot{};
  fixture_local_player = player.data();
  if (!ReadCoreSnapshot(bindings, snapshot) || !snapshot.map_ready ||
      !snapshot.has_played_character || snapshot.played_character_id != id ||
      !snapshot.played_character_alive || snapshot.local_player_id != 7 ||
      snapshot.clock.date_raw != 53175816 || snapshot.clock.speed != 3 ||
      !snapshot.clock.paused) {
    return false;
  }
  Put(character, 0x1D0, static_cast<void *>(other.data()));
  if (!ReadCoreSnapshot(bindings, snapshot) || snapshot.played_character_alive) {
    return false;
  }
  Put(character, 0x18, std::int32_t{0x04000004});
  if (!ReadCoreSnapshot(bindings, snapshot) || snapshot.has_played_character ||
      snapshot.played_character_id != -1 || snapshot.played_character_alive) {
    return false;
  }
  fixture_local_player = nullptr;
  if (!ReadCoreSnapshot(bindings, snapshot) || snapshot.map_ready ||
      snapshot.has_played_character || snapshot.clock.speed != 3) {
    return false;
  }
  bindings.enabled = false;
  if (ReadCoreSnapshot(bindings, snapshot) || snapshot.clock.speed != 0 ||
      snapshot.local_player_id != -1) {
    return false;
  }
  const auto bound = BindCoreImage(0x140000000, kExecutableSha256);
  return bound.enabled &&
         reinterpret_cast<std::uintptr_t>(bound.game_state_slot) == 0x145C68C50 &&
         reinterpret_cast<std::uintptr_t>(bound.character_storage_slot) == 0x145C67568 &&
         !BindCoreImage(0x140000000, "old-or-unknown").enabled &&
         !BindCoreImage(0, kExecutableSha256).enabled;
}
} // namespace

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
  if (!CheckCoreSnapshot()) {
    return 8;
  }
  std::cout << "PASS 1.20.0.2 offline clock/player/pause/speed fixtures\n";
}
