#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::ck3_11906::Bindings;

std::array<std::byte, 0x78> g_player{};
bool g_submit_called = false;
enum class ExpectedCommand { pause, resume, speed };
ExpectedCommand g_expected_command = ExpectedCommand::pause;

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &target, std::size_t offset,
           Value value) {
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

void *FixtureGetLocalPlayer(void *) { return g_player.data(); }

void FixtureSubmit(void *manager, void *opaque_command, std::uint32_t flags) {
  const auto *command = static_cast<const std::byte *>(opaque_command);
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t player_id = -1;
  std::memcpy(&primary, command, sizeof(primary));
  std::memcpy(&secondary, command + 0x18, sizeof(secondary));
  std::memcpy(&player_id, command + 0x20, sizeof(player_id));
  const auto paused = static_cast<std::uint8_t>(command[0x24]);
  const auto command_flags = static_cast<std::uint8_t>(command[0x08]);
  if (g_expected_command == ExpectedCommand::pause ||
      g_expected_command == ExpectedCommand::resume) {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x11111111 &&
                      secondary == 0x22222222 && command_flags == 0x08 &&
                      player_id == 41 &&
                      paused ==
                          (g_expected_command == ExpectedCommand::pause ? 1 : 0);
  } else {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x33333333 &&
                      secondary == 0x44444444 && command_flags == 0 &&
                      player_id == 4;
  }
}

int Fail(const char *message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

} // namespace

int main() {
  std::array<std::byte, 0x78> game_state{};
  std::array<std::byte, 0x28> jomini_state{};
  std::array<std::byte, 0x200> players{};
  void *game_state_pointer = game_state.data();
  void *jomini_state_pointer = jomini_state.data();
  Store(game_state, 0x08, std::int32_t{43'823'104});
  Store(game_state, 0x70, std::int32_t{3});
  Store(jomini_state, 0x18, static_cast<void *>(players.data()));
  Store(jomini_state, 0x20, std::uint8_t{0});
  Store(players, 0x1F0, std::int32_t{41});
  Store(g_player, 0x70, std::int32_t{41});

  Bindings bindings{};
  bindings.enabled = true;
  bindings.game_state_slot = &game_state_pointer;
  bindings.jomini_state_slot = &jomini_state_pointer;
  bindings.command_manager = reinterpret_cast<void *>(0x1234);
  bindings.pause_primary_vtable = 0x11111111;
  bindings.pause_secondary_vtable = 0x22222222;
  bindings.set_speed_primary_vtable = 0x33333333;
  bindings.set_speed_secondary_vtable = 0x44444444;
  bindings.submit_command = FixtureSubmit;
  bindings.get_local_player = FixtureGetLocalPlayer;

  xar::ck3_11906::Snapshot snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("fixture snapshot was unavailable");
  }
  if (snapshot.date_raw != 43'823'104 || snapshot.speed != 4 ||
      snapshot.paused || snapshot.player_id != 41) {
    return Fail("fixture snapshot fields did not match the pinned offsets");
  }
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("pause-map did not construct and submit the pinned command");
  }

  g_expected_command = ExpectedCommand::speed;
  g_submit_called = false;
  if (!xar::ck3_11906::SubmitSetSpeed(bindings, 5) || !g_submit_called ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 0) ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 6)) {
    return Fail("set-speed did not construct the pinned command for 1..5");
  }

  Store(jomini_state, 0x20, std::uint8_t{1});
  g_expected_command = ExpectedCommand::pause;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::already_paused ||
      g_submit_called) {
    return Fail("already-paused fixture should be idempotent");
  }

  g_expected_command = ExpectedCommand::resume;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("resume-map did not submit paused=false");
  }
  Store(jomini_state, 0x20, std::uint8_t{0});
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::already_running ||
      g_submit_called) {
    return Fail("already-running fixture should be idempotent");
  }

  bindings.enabled = false;
  if (xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("disabled build binding exposed game state");
  }
  std::cout << "PASS: snapshot=1 pause_resume_command_layout=1 "
               "set_speed_zero_based_mapping=1 exact_build_gate=1\n";
  return 0;
}
