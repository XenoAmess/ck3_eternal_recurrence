#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <vector>
#include <windows.h>

namespace {
using namespace xar::game;
using namespace xar::ck3_1210;
constexpr std::array<std::string_view, 1> kCapabilities{kCoreFrameCapabilityV1};
const AdapterDescriptor kDescriptor{kAdapterId, kGameVersion,
    kExecutableSha256, "xar_checkpoint", kCapabilities};
class FixtureAdapter final : public GameAdapter {
public:
  explicit FixtureAdapter(const AdapterDescriptor &d) : descriptor_(d) {}
  const AdapterDescriptor &descriptor() const noexcept override {
    return descriptor_;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(xar::game::Snapshot &output) const noexcept override {
    output = {};
    return false;
  }
  xar::game::PauseSubmitResult
  submit_pause_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::PauseSubmitResult::unavailable;
  }
  xar::game::ResumeSubmitResult
  submit_resume_map(xar::game::Snapshot *observed_snapshot) const noexcept override {
    if (observed_snapshot != nullptr) {
      *observed_snapshot = {};
    }
    return xar::game::ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SelectEventOptionResult
  submit_select_event_option(std::int32_t) const noexcept override {
    return xar::game::SelectEventOptionResult::unavailable;
  }
  xar::game::SaveCheckpointResult
  submit_save_checkpoint() const noexcept override {
    return {};
  }
  xar::game::ReplyPendingInteractionResult
  submit_reply_to_pending_interaction(
      xar::game::PendingInteractionReply) const noexcept override {
    return xar::game::ReplyPendingInteractionResult::unavailable;
  }
  xar::game::RaiseTroopsResult
  submit_raise_troops_default() const noexcept override {
    return xar::game::RaiseTroopsResult::unavailable;
  }
  xar::game::MoveArmyResult
  submit_move_army(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MoveArmyResult::unavailable;
  }
  xar::game::PreviewMoveArmyResult
  preview_move_army(std::int32_t, std::int32_t) const noexcept override {
    return {};
  }
  xar::game::DisbandArmyResult
  submit_disband_army(std::int32_t) const noexcept override {
    return xar::game::DisbandArmyResult::unavailable;
  }
  xar::game::SplitArmyHalfResult
  submit_split_army_half(std::int32_t) const noexcept override {
    return xar::game::SplitArmyHalfResult::unavailable;
  }
  xar::game::MergeArmiesResult
  submit_merge_armies(std::int32_t, std::int32_t) const noexcept override {
    return xar::game::MergeArmiesResult::unavailable;
  }
  xar::game::StartAssaultResult
  submit_start_assault(std::int32_t) const noexcept override {
    return xar::game::StartAssaultResult::unavailable;
  }
  xar::game::StopAssaultResult
  submit_stop_assault(std::int32_t) const noexcept override {
    return xar::game::StopAssaultResult::unavailable;
  }
  bool read_declarable_wars(
      std::vector<xar::game::DeclarableWarSnapshot> &output) const noexcept override {
    output.clear();
    return false;
  }
  xar::game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &output)
      const noexcept override {
    output.clear();
    return xar::game::ReadDeclarableWarsResult::unavailable;
  }
  xar::game::DeclareWarResult submit_declare_war(
      const xar::game::DeclarableWarSnapshot &) const noexcept override {
    return xar::game::DeclareWarResult::unavailable;
  }
  xar::game::ReadArrangeMarriageChoicesResult
  read_arrange_marriage_choices(
      std::vector<xar::game::ArrangeMarriageChoice> &output,
      xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    output.clear();
    diagnostics = {};
    return xar::game::ReadArrangeMarriageChoicesResult::unavailable;
  }
  xar::game::ArrangeMarriageResult submit_arrange_marriage(
      const xar::game::ArrangeMarriageChoice &) const noexcept override {
    return xar::game::ArrangeMarriageResult::unavailable;
  }
  xar::game::EnforceDemandsResult
  submit_enforce_demands(std::int32_t) const noexcept override {
    return xar::game::EnforceDemandsResult::unavailable;
  }
  xar::game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<xar::game::ArmyStrengthSnapshot> &output) const noexcept override {
    output.clear();
    return xar::game::ReadArmyStrengthsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsResult
  read_combat_simulation_inputs(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsResult::unavailable;
  }
  xar::game::ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const xar::game::CombatSimulationInputsRequest &,
      xar::game::CombatSimulationInputsV3Snapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadCombatSimulationInputsV3Result::unavailable;
  }
  xar::game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t,
      xar::game::WarTerminationOptionsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationOptionsResult::unavailable;
  }
  xar::game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t,
      xar::game::WarTerminationTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationTermsResult::unavailable;
  }
  xar::game::ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t,
      xar::game::WarTerminationExitTermsSnapshot &output) const noexcept override {
    output = {};
    return xar::game::ReadWarTerminationExitTermsResult::unavailable;
  }
  xar::game::SurrenderWarResult
  submit_surrender_war(std::int32_t) const noexcept override {
    return xar::game::SurrenderWarResult::unavailable;
  }
  xar::game::OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t) const noexcept override {
    return xar::game::OfferWhitePeaceResult::unavailable;
  }
private:
  const AdapterDescriptor &descriptor_;
};
void *gPlayer = nullptr;
std::size_t gReads = 0;
CoreBindings gBindings{};
void *LocalPlayer(void *) { return gPlayer; }
template<class T, class Buffer>
void Store(Buffer &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
}
bool ReadPrefix(const GameAdapter &, Snapshot &snapshot) noexcept {
  ++gReads;
  CoreSnapshotPrefix core{};
  if (!ReadCoreSnapshot(gBindings, core)) return false;
  snapshot = {};
  snapshot.date_raw = core.clock.date_raw;
  snapshot.speed = core.clock.speed;
  snapshot.paused = core.clock.paused;
  snapshot.player_id = core.local_player_id;
  snapshot.map_ready = core.map_ready;
  snapshot.has_played_character = core.has_played_character;
  snapshot.played_character_id = core.played_character_id;
  snapshot.played_character_alive = core.played_character_alive;
  return true;
}
} // namespace
#define CHECK(expression) do { if (!(expression)) { std::cerr << #expression << std::endl; return 1; } } while (false)

int wmain(int argc, wchar_t **argv) {
  using namespace xar::ck3_1210;
  constexpr std::int32_t id = 0x01000001;
  std::array<std::byte, 0x74> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1E0> character{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x20> slots{};
  Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4});
  // State +A0 requires the complete fixture buffer, separate from clock span.
  std::vector<std::byte> complete_state(0xA8);
  std::memcpy(complete_state.data(), state.data(), state.size());
  Store(complete_state, 0xA0, data.data());
  Store(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
  Store(players, 0x1F0, std::int32_t{7}); Store(player, 0x70, std::int32_t{7});
  Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
  Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
  Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, id);
  Store(character, 0x18, id); Store(storage, 0x20, slots.data());
  Store(storage, 0x2C, std::int32_t{2}); Store(slots, 0x18, character.data());
  void *gs = complete_state.data(), *js = jomini.data(), *ss = storage.data();
  gPlayer = player.data(); gBindings = {true, &gs, &js, &ss, &LocalPlayer};
  CoreSnapshotPrefix core{};
  CHECK(ReadCoreSnapshot(gBindings, core));
  CHECK(core.clock.date_raw == 123456 && core.clock.speed == 5 && core.clock.paused);
  CHECK(core.map_ready && core.local_player_id == 7 && core.has_played_character);
  CHECK(core.played_character_id == id && core.played_character_alive);
  Store(character, 0x18, std::int32_t{0x02000001});
  CHECK(ReadCoreSnapshot(gBindings, core) && !core.has_played_character);
  Store(character, 0x18, id); Store(character, 0x1D0, static_cast<void *>(character.data()));
  CHECK(ReadCoreSnapshot(gBindings, core) && core.has_played_character && !core.played_character_alive);
  Store(character, 0x1D0, static_cast<void *>(nullptr));
  Store(complete_state, 0x70, std::int32_t{5});
  CHECK(!ReadCoreSnapshot(gBindings, core)); Store(complete_state, 0x70, std::int32_t{4});
  ClockPrefix clock{};
  CHECK(!DecodeClockPrefix(std::span<const std::byte>{state}.first(0x73), jomini, clock));
  CHECK(!BindCoreImage(0x140000000, "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518").enabled);
  CHECK(!BindCoreImage(0, kExecutableSha256).enabled);
  const auto exact = BindCoreImage(0x140000000, kExecutableSha256);
  CHECK(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.game_state_slot) == 0x140000000 + kGameStateSlotRva);
  FixtureAdapter adapter(kDescriptor);
  CoreFrameMailboxContextV1 context{&adapter, &ReadPrefix, {}};
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = 1; stamp.pump_epoch = 1; stamp.date_raw = 123456; stamp.paused = true;
  CHECK(ExecuteCoreFrameMailboxV1(&context, stamp) && context.observation.core_available && gReads == 1);
  const auto wire = SerializeCoreFrameV1(context.observation);
  const auto partial_reply = SerializeCoreFrameCommandResultV1("producer-partial", context.observation);
  CHECK(wire.find("ck3_1210_core_frame_v1") != std::string::npos);
  CHECK(wire.find("ck3-1.21.0-native-headless-main-thread") != std::string::npos);
  ++stamp.date_raw;
  CHECK(ExecuteCoreFrameMailboxV1(&context, stamp) && !context.observation.core_available);
  CHECK(context.observation.unavailable_reason == "core_frame_changed");
  const auto unavailable_wire = SerializeCoreFrameV1(context.observation);
  const auto unavailable_reply = SerializeCoreFrameCommandResultV1("producer-unavailable", context.observation);
  CHECK(!BindThreadRuntimeImage(1, "wrong").exact_build_admitted);
  CHECK(!BindThreadRuntimeImage(0, kExecutableSha256).exact_build_admitted);
  const std::array<xar::ck3_11906::MainThreadQueryExecutorV1, 4> allowed{&ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1};
  CHECK(BindThreadRuntimeImage(1,kExecutableSha256,allowed).permitted_executor_quaternary==&ExecuteCoreFrameMailboxV1);
  const std::array<xar::ck3_11906::MainThreadQueryExecutorV1, 5> too_many{&ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1, &ExecuteCoreFrameMailboxV1,&ExecuteCoreFrameMailboxV1};
  CHECK(!BindThreadRuntimeImage(1, kExecutableSha256, too_many).exact_build_admitted);
  CHECK(!VerifyThreadRuntimeImage(0));
  if (argc == 2) {
    // Resource-only Windows mapping: no entry point, imported function, game
    // process, native callback, or function pointer in this image is executed.
    HMODULE resource = LoadLibraryExW(argv[1], nullptr, LOAD_LIBRARY_AS_IMAGE_RESOURCE);
    CHECK(resource != nullptr);
    const auto mapped = reinterpret_cast<std::uintptr_t>(resource) & ~std::uintptr_t{3};
    CHECK(VerifyThreadRuntimeImage(mapped));
    CHECK(FreeLibrary(resource));
  }
  std::cout << wire << std::endl << unavailable_wire << std::endl
            << partial_reply << std::endl << unavailable_reply << std::endl;
  std::cout << "PASS Florin core/clock/full-generation/partial-frame/thread guards; no game code executed" << std::endl;
  return 0;
}
