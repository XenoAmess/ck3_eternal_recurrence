#include "xar_bridge/player_lifestyle_current_state_only_v1.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

namespace {

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

struct Fixture {
  ck3::PlayerLifestyleSnapshotFrameV1 frame{};
  ck3::PlayerLifestyleSourceSampleV1 source{};
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
  bool source_available = true;
};

game::PlayerLifestyleStableKeyV1 Key(std::string_view value) {
  game::PlayerLifestyleStableKeyV1 output{};
  if (!ck3::AssignPlayerLifestyleStableKeyV1(value, output)) {
    std::abort();
  }
  return output;
}

bool Capture(void *opaque,
             ck3::PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.frame_calls;
  output = fixture.frame;
  return true;
}

bool IsMain(void *) noexcept { return true; }

bool ReadSource(void *opaque, std::uintptr_t character,
                ck3::PlayerLifestyleSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (!fixture.source_available ||
      character != fixture.frame.played_character) {
    return false;
  }
  ++fixture.source_calls;
  output = fixture.source;
  return true;
}

Fixture Base() {
  Fixture fixture{};
  constexpr std::string_view id = "life-state-only-001";
  std::memcpy(fixture.frame.snapshot_id.data(), id.data(), id.size());
  fixture.frame.public_revision = 701;
  fixture.frame.native_revision = 9001;
  fixture.frame.proof_epoch = 17;
  fixture.frame.date_raw = 54'321'000;
  fixture.frame.paused = true;
  fixture.frame.map_ready = true;
  fixture.frame.has_played_character = true;
  fixture.frame.played_character_alive = true;
  fixture.frame.played_character_id = 32'904;
  fixture.frame.played_character = 0x123456780ULL;
  fixture.frame.played_character_identity_round_trip = true;
  fixture.source.player_character_id = fixture.frame.played_character_id;
  fixture.source.player_identity_round_trip = true;
  auto &state = fixture.source.state;
  state.current_focus_presence = game::PlayerLifestyleFocusPresenceV1::present;
  state.current_focus_key = Key("stewardship_wealth_focus");
  state.current_lifestyle_key = Key("stewardship_lifestyle");
  state.current_lifestyle_progress_present = true;
  state.current_lifestyle_progress.lifestyle_key =
      state.current_lifestyle_key;
  state.current_lifestyle_progress.xp_total_raw = 25'100'000;
  state.current_lifestyle_progress.xp_within_level_raw = 25'100'000;
  state.current_lifestyle_progress.xp_per_level = 1000;
  state.current_lifestyle_progress.unspent_perk_points = 1;
  state.current_lifestyle_progress.used_perk_points = 0;
  state.owned_perk_count = 1;
  state.owned_perk_keys[0] = Key("tax_man_perk");
  // Both final candidate sets intentionally retain LIFE2's default
  // lifestyle_window_unavailable reason. No candidate producer is invoked.
  return fixture;
}

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  auto fixture = Base();
  ck3::PlayerLifestyleSnapshotEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3::kPlayerLifestyleSnapshotExecutableSha256V1;
  environment.offline_fixture = true;
  const ck3::PlayerLifestyleSnapshotAccessV1 access{
      &fixture, &Capture, &IsMain, nullptr, &ReadSource};
  const ck3::PlayerLifestyleSnapshotRequestV1 request{
      "life-state-only-001", 701, 9001, 54'321'000, 32'904};
  game::PlayerLifestyleSnapshotV1 state{};
  if (ck3::ReadPlayerLifestyleSnapshotV1(environment, access, request,
                                          state) !=
          game::ReadPlayerLifestyleSnapshotResultV1::available ||
      !ck3::PlayerLifestyleCurrentStateOnlyReadyV1(state) ||
      state.readiness.legal_focus_candidates_ready ||
      state.readiness.legal_perk_candidates_ready ||
      state.state.current_lifestyle_progress.xp_total_raw != 25'100'000 ||
      state.state.current_lifestyle_progress.unspent_perk_points != 1 ||
      state.state.owned_perk_count != 1 || fixture.frame_calls != 2 ||
      fixture.source_calls != 2) {
    return Fail("window-unbound final candidates erased typed LIFE2 state");
  }
  if (ck3::SerializePlayerLifestyleSnapshotV1(state).find(
          "\"status\":\"available\"") == std::string::npos) {
    return Fail("state-only LIFE2 serialization was unavailable");
  }
  state.readiness.current_focus_ready = false;
  if (ck3::PlayerLifestyleCurrentStateOnlyReadyV1(state)) {
    return Fail("missing current focus was accepted as state-only ready");
  }
  fixture = Base();
  fixture.source_available = false;
  state = {};
  if (ck3::ReadPlayerLifestyleSnapshotV1(environment, access, request,
                                          state) !=
          game::ReadPlayerLifestyleSnapshotResultV1::unavailable ||
      ck3::PlayerLifestyleCurrentStateOnlyReadyV1(state)) {
    return Fail("failed native state source was reported ready");
  }
  std::cout << "LIFE2 state-only window-unbound source GREEN\n";
  return 0;
}
