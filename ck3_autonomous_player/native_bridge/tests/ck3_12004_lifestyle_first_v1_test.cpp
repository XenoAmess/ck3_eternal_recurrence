#include "xar_bridge/ck3_12004_lifestyle_transport.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace life = xar::ck3_12004::lifestyle;
using namespace xar::ck3_11906;
namespace game = xar::game;
namespace {
constexpr std::string_view kFrozenPreviousImageSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
void Require(bool value, const char *reason) { if (!value) throw std::runtime_error(reason); }
struct Fixture {
  PlayerLifestyleSnapshotFrameV1 frame{};
  PlayerLifestyleSourceSampleV1 sample{};
  unsigned frame_calls = 0;
  unsigned source_calls = 0;
  bool drift = false;
};
bool Main(void *) noexcept { return true; }
bool Frame(void *opaque, PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.frame_calls;
  output = fixture.frame;
  return true;
}
bool Source(void *opaque, std::uintptr_t character,
            PlayerLifestyleSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.source_calls;
  if (character != fixture.frame.played_character) return false;
  output = fixture.sample;
  if (fixture.drift && fixture.source_calls == 2)
    output.state.actor_traits_ready = !output.state.actor_traits_ready;
  return true;
}
void Write(const std::filesystem::path &path, const std::string &value) {
  std::ofstream stream(path, std::ios::binary | std::ios::trunc);
  stream << value << '\n';
  Require(stream.good(), "wire output failed");
}
void InitializeFixture(Fixture &fixture, bool present) {
  constexpr std::string_view id = "native:7";
  std::copy(id.begin(), id.end(), fixture.frame.snapshot_id.begin());
  fixture.frame.public_revision = 7;
  fixture.frame.native_revision = 7;
  fixture.frame.proof_epoch = 7;
  fixture.frame.date_raw = 1234;
  fixture.frame.paused = true;
  fixture.frame.map_ready = true;
  fixture.frame.has_played_character = true;
  fixture.frame.played_character_alive = true;
  fixture.frame.played_character_id = 29829;
  fixture.frame.played_character = 0x123450;
  fixture.frame.played_character_identity_round_trip = true;
  fixture.sample.player_character_id = 29829;
  fixture.sample.player_identity_round_trip = true;
  auto &state = fixture.sample.state;
  state.current_focus_presence = present
      ? game::PlayerLifestyleFocusPresenceV1::present
      : game::PlayerLifestyleFocusPresenceV1::absent;
  if (present) {
    Require(life::AssignPlayerLifestyleStableKey12004V1("stewardship_wealth_focus", state.current_focus_key), "focus key");
    Require(life::AssignPlayerLifestyleStableKey12004V1("stewardship_lifestyle", state.current_lifestyle_key), "lifestyle key");
    state.current_lifestyle_progress_present = true;
    auto &progress = state.current_lifestyle_progress;
    progress.lifestyle_key = state.current_lifestyle_key;
    progress.xp_total_raw = 12345678;
    progress.xp_within_level_raw = 2345678;
    progress.xp_per_level = 1000;
    progress.unspent_perk_points = 2;
    progress.used_perk_points = 3;
    state.owned_perk_count = 1;
    Require(life::AssignPlayerLifestyleStableKey12004V1("cutting_corners_perk", state.owned_perk_keys[0]), "perk key");
  }
}
void Case(const std::filesystem::path &directory, std::string_view name,
          bool present, bool drift, bool old_sha) {
  auto fixture_storage = std::make_unique<Fixture>();
  auto &fixture = *fixture_storage;
  InitializeFixture(fixture, present);
  fixture.drift = drift;
  const auto original = std::make_unique<PlayerLifestyleSourceSampleV1>(fixture.sample);
  PlayerLifestyleSnapshotEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 = old_sha
      ? kFrozenPreviousImageSha : xar::ck3_12004::kExecutableSha256;
  environment.offline_fixture = true;
  PlayerLifestyleSnapshotAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Frame;
  access.is_main_thread = &Main;
  access.read_offline_fixture_source = &Source;
  PlayerLifestyleSnapshotRequestV1 request{"native:7", 7, 7, 1234, 29829};
  auto context = std::make_unique<life::PlayerLifestyleFormalWireContext12004V1>();
  context->snapshot = std::make_unique<game::PlayerLifestyleSnapshotV1>();
  context->mode = PlayerLifestyleFormalWireModeV1::query_state_only;
  context->episode_run_id = "native-29829-fixture";
  context->snapshot_id = "native:7";
  context->expected_revision = 7;
  const auto result = life::ReadPlayerLifestyleSnapshot12004V1(
      environment, access, request, *context->snapshot);
  Require(fixture.sample == *original, "fixture native input changed");
  if (old_sha) {
    Require(result == game::ReadPlayerLifestyleSnapshotResultV1::unavailable &&
        context->snapshot->unavailable_reason == game::PlayerLifestyleSnapshotFailureV1::exact_build_not_admitted &&
        fixture.frame_calls == 0 && fixture.source_calls == 0, "old SHA admitted");
  } else if (drift) {
    Require(result == game::ReadPlayerLifestyleSnapshotResultV1::unavailable &&
        context->snapshot->unavailable_reason == game::PlayerLifestyleSnapshotFailureV1::native_sample_drift &&
        fixture.frame_calls == 1 && fixture.source_calls == 2, "drift semantics");
  } else {
    Require(result == game::ReadPlayerLifestyleSnapshotResultV1::available &&
        context->snapshot->readiness.current_focus_ready &&
        context->snapshot->readiness.owned_perks_ready &&
        context->snapshot->readiness.same_frame_ready &&
        !context->snapshot->readiness.legal_perk_candidates_ready &&
        !context->snapshot->readiness.legal_focus_candidates_ready &&
        fixture.frame_calls == 2 && fixture.source_calls == 2, "snapshot readiness");
    Require(context->snapshot->state == fixture.sample.state, "snapshot fields changed");
  }
  context->completed = result == game::ReadPlayerLifestyleSnapshotResultV1::available;
  context->failure = life::PlayerLifestyleSnapshotFailureKey12004V1(context->snapshot->unavailable_reason);
  const auto stem = std::string(name);
  Write(directory / (stem + ".json"), life::RenderPlayerLifestyle12004(
      stem, kPlayerLifestyleFormalPrivateCurrentStateStepV1, *context,
      xar::game::Ck3_12004AdapterDescriptor()));
  Write(directory / (stem + "-snapshot.json"),
      life::SerializePlayerLifestyleSnapshot12004V1(*context->snapshot));
}
}
int main(int argc, char **argv) {
  try {
    Require(argc == 3 && std::string_view(argv[1]) == "--wire-dir", "usage: --wire-dir fresh-directory");
    const auto directory = std::filesystem::path(argv[2]);
    std::filesystem::create_directories(directory);
    // Factory address checks invoke no bound game function and read no game memory.
    constexpr std::uintptr_t base = 0x140000000;
    const auto binding = life::BindPlayerLifestyleImage12004(base, xar::ck3_12004::kExecutableSha256);
    Require(binding.enabled && binding.core.enabled, "actual4 binder disabled");
    Require(reinterpret_cast<std::uintptr_t>(binding.snapshot.current_focus) == base + 0x29194B0 &&
        reinterpret_cast<std::uintptr_t>(binding.snapshot.current_lifestyle) == base + 0x29193C0 &&
        reinterpret_cast<std::uintptr_t>(binding.snapshot.unspent_perk_points) == base + 0x2918BB0 &&
        reinterpret_cast<std::uintptr_t>(binding.snapshot.used_perk_points) == base + 0x2918C30 &&
        reinterpret_cast<std::uintptr_t>(binding.snapshot.lifestyle_xp) == base + 0x2918D30 &&
        reinterpret_cast<std::uintptr_t>(binding.snapshot.unlocked_perks) == base + 0x2919340, "actual4 callback address");
    Require(!life::BindPlayerLifestyleImage12004(base, kFrozenPreviousImageSha).enabled, "old image binder alias");
    Case(directory, "01-no-current-focus", false, false, false);
    Case(directory, "02-current-focus-progress", true, false, false);
    Case(directory, "03-native-sample-drift", false, true, false);
    Case(directory, "04-old-sha-rejected", false, false, true);
    std::cout << "lifestyle actual4 first fixture: 4 cases; synthetic frame/source, actual reader/serializer\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
