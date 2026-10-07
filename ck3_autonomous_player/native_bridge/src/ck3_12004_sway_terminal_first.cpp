// AUTHORED_NOTRUN. Unique retained-row FIRST, not an old GREEN replay.
#include "xar_bridge/ck3_12004_sway_terminal.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
namespace game = xar::game;
namespace actual4 = xar::ck3_12004;
using namespace xar::ck3_12002;
using namespace xar::ck3_11906;
constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uint64_t kRevision = 19;
constexpr std::int32_t kDate = 53288448;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kTarget = 34333;
constexpr std::uint32_t kScheme = 134217986;
constexpr std::uint32_t kIndex = kScheme & 0x00FFFFFFu;

template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *gLocal = nullptr;
void *Local(void *) { return gLocal; }

struct World {
  SwayCompletionBindings12002 bindings =
      actual4::BindSwayTerminalImage12004(kBase, actual4::kExecutableSha256);
  SwayStateBindings12002 profile =
      actual4::BindSwayStateImage12004(kBase, actual4::kExecutableSha256);
  std::array<std::byte, 0xA8> state{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22400);
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x80> local{};
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x200> character{};
  std::array<std::byte, 0x40> characters{};
  std::vector<std::byte> character_slots =
      std::vector<std::byte>((static_cast<std::size_t>(kActor) + 1) * 0x10);
  std::array<std::byte, 0x40> storage{};
  std::vector<std::byte> slots =
      std::vector<std::byte>((static_cast<std::size_t>(kIndex) + 1) * 0x10);
  std::array<std::byte, 0x40> type{};
  std::array<std::byte, 0x40> scheme{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *characters_pointer = characters.data();
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls_context{};

  World() {
    Check(bindings.enabled && profile.enabled && bindings.image_base == kBase &&
          profile.executable_sha256 == actual4::kExecutableSha256 &&
          reinterpret_cast<std::uintptr_t>(bindings.core.game_state_slot) ==
              kBase + actual4::kGameStateSlotRva &&
          reinterpret_cast<std::uintptr_t>(bindings.core.jomini_state_slot) ==
              kBase + actual4::kJominiStateSlotRva &&
          reinterpret_cast<std::uintptr_t>(bindings.core.character_storage_slot) ==
              kBase + actual4::kCharacterStorageSlotRva &&
          reinterpret_cast<std::uintptr_t>(bindings.core.get_local_player) ==
              kBase + actual4::kGetLocalPlayerRva &&
          bindings.success_chance == nullptr && bindings.can_continue == nullptr,
          "actual4 image binding precedes only fixture-owned core operands");
    Check(!actual4::BindSwayTerminalImage12004(kBase,
              xar::ck3_12002::kExecutableSha256).enabled,
          "legacy image identity cannot bind actual4 terminal");
    bindings.core.game_state_slot = &state_pointer;
    bindings.core.jomini_state_slot = &jomini_pointer;
    bindings.core.character_storage_slot = &characters_pointer;
    bindings.core.get_local_player = &Local;
    gLocal = local.data();
    Put(state.data(), actual4::kGameStateDateOffset, kDate);
    Put(state.data(), actual4::kGameStateDataOffset, data.data());
    Put(state.data(), actual4::kGameStateSpeedOffset, std::int32_t{0});
    Put(jomini.data(), actual4::kJominiPlayersOffset, players.data());
    Put(jomini.data(), actual4::kJominiPausedOffset, std::uint8_t{1});
    Put(players.data(), actual4::kPlayersLocalPlayerIdOffset, std::int32_t{0});
    Put(local.data(), actual4::kPlayerIdOffset, std::int32_t{0});
    Put(data.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerEntriesOffset, entries.data());
    Put(data.data(), actual4::kPlayerCharacterManagerOffset +
        actual4::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry.data(), actual4::kPlayerEntryLocalPlayerIdOffset, std::int32_t{0});
    Put(entry.data(), actual4::kPlayerEntryCharacterIdOffset, kActor);
    Put(character.data(), actual4::kCharacterFullIdOffset, kActor);
    Put(characters.data(), actual4::kCharacterStorageSlotsOffset, character_slots.data());
    Put(characters.data(), actual4::kCharacterStorageCapacityOffset, kActor + 1);
    Put(character_slots.data(), static_cast<std::size_t>(kActor) * 0x10 + 8,
        character.data());
    Put(data.data(), profile.manager_offset, kBase + profile.manager_vtable_rva);
    Put(data.data(), profile.manager_offset + 0x20, storage.data());
    Put(storage.data(), 0, kBase + profile.storage_vtable_rva);
    Put(storage.data(), 0x20, slots.data());
    Put(storage.data(), 0x2C, static_cast<std::int32_t>(kIndex + 1));
    Put(type.data(), 0, kBase + profile.type_vtable_rva);
    std::memcpy(type.data() + 0x18, "sway", 5);
    Put(type.data(), 0x28, std::uint64_t{4});
    Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(scheme.data(), 0, kBase + profile.instance_vtable_rva);
    Put(scheme.data(), 0x10, kScheme);
    Put(scheme.data(), 0x20, type.data());
    Put(scheme.data(), 0x28, std::int32_t{0});
    Put(scheme.data(), 0x2C, static_cast<std::uint32_t>(kActor));
    Put(scheme.data(), 0x30, std::uint32_t{0});
    Put(scheme.data(), 0x34, static_cast<std::uint32_t>(kTarget));
    Put(slots.data(), static_cast<std::size_t>(kIndex) * 0x10 + 8, scheme.data());
    Put(tls_context.data(), 0x20, std::uint8_t{1});
  }
};

class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        actual4::kAdapterId, actual4::kGameVersion, actual4::kExecutableSha256,
        "offline-sway-terminal-12004-first", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame; return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

bool Execute(World &world, FrameAdapter &adapter,
    SwayCompletionMailboxContextV1 &query, std::uint64_t epoch) {
  MainThreadQueryMailboxV1 mailbox{};
  mailbox.permitted_executor_sway_completion12002 =
      &actual4::ExecuteSwayTerminalMailbox12004;
  mailbox.state = MainThreadQueryMailboxStateV1::idle;
  mailbox.executor_submission_enabled = true;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.paused_owner_verified_pump_epochs =
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
  query.bindings = world.bindings;
  query.request = {kRevision, kActor, kTarget, kScheme};
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = kRevision;
  query.envelope.typed_context = &query;
  Check(TrySubmitMainThreadQueryV1(mailbox, &actual4::ExecuteSwayTerminalMailbox12004,
          &query.envelope, query.envelope.ticket) == MainThreadQuerySubmitResultV1::submitted,
        "existing exact completion callback admission");
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = reinterpret_cast<std::uintptr_t>(&world.tls_initialized);
  stamp.tls_initialized = world.tls_initialized;
  stamp.tls_context = reinterpret_cast<std::uintptr_t>(world.tls_context.data());
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(world.jomini.data());
  stamp.game_state = reinterpret_cast<std::uintptr_t>(world.state.data());
  stamp.date_raw = kDate;
  stamp.paused = true;
  return actual4::ExecuteSwayTerminalMailbox12004(&query.envelope, stamp) &&
      query.completed && query.failure.empty() && query.envelope.frame_stable;
}
void Save(const std::filesystem::path &output, const char *name,
    const SwayCompletionMailboxContextV1 &query, const FrameAdapter &adapter) {
  const auto packet = actual4::SerializeSwayTerminalCommandResult12004(
      query.result, query.envelope.expected_snapshot_revision,
      query.envelope.execution_stamp.date_raw, name, adapter.descriptor());
  std::ofstream stream(output / name, std::ios::binary);
  stream << packet << '\n';
  Check(stream.good(), "whole actual4 production command result");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "one unique output-directory argument");
    const std::filesystem::path output{argv[1]};
    std::filesystem::create_directories(output);
    World world;
    FrameAdapter adapter;
    adapter.frame.date_raw = kDate; adapter.frame.paused = true;
    adapter.frame.speed = 1; adapter.frame.player_id = 0;
    adapter.frame.map_ready = true; adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = kActor;
    adapter.frame.played_character_alive = true;
    SwayCompletionMailboxContextV1 current{};
    Check(Execute(world, adapter, current, 68) && current.result.available &&
          current.result.exact_instance_join_ready && current.result.instance_present &&
          current.result.native_status_raw == 0 &&
          !current.result.native_terminal_state_observed &&
          !current.result.native_success_chance_observed &&
          !current.result.native_can_continue_observed,
          "current exact gen8 row with nullable unmapped roll inputs");
    Save(output, "current.json", current, adapter);
    Put(world.scheme.data(), 0x28, std::int32_t{1});
    Put(world.scheme.data(), 0x2C, std::uint32_t{0xFFFFFFFFu});
    SwayCompletionMailboxContextV1 terminal{};
    Check(Execute(world, adapter, terminal, 69) && terminal.result.available &&
          terminal.result.owner_cleared && terminal.result.exact_instance_join_ready &&
          terminal.result.scheme_instance_generation == 8 &&
          terminal.result.native_terminal_state_observed &&
          terminal.result.native_status_key == "terminated_unattributed" &&
          !terminal.result.terminal_cause_observed && terminal.result.terminal_cause == "unknown",
          "real retained-row read preserves fullID and unattributed terminal");
    Save(output, "terminated.json", terminal, adapter);
    Put(world.scheme.data(), 0x10, kScheme + 0x01000000u);
    SwayCompletionMailboxContextV1 reused{};
    Check(Execute(world, adapter, reused, 70) && reused.result.available &&
          reused.result.storage_slot_reused && !reused.result.instance_present &&
          !reused.result.native_terminal_state_observed,
          "same index replacement cannot become original terminal");
    Save(output, "reused.json", reused, adapter);
    Put(world.slots.data(), static_cast<std::size_t>(kIndex) * 0x10 + 8,
        static_cast<void *>(nullptr));
    SwayCompletionMailboxContextV1 purged{};
    Check(Execute(world, adapter, purged, 71) && purged.result.available &&
          purged.result.instance_source_observed && !purged.result.instance_present &&
          !purged.result.native_terminal_state_observed,
          "purged row publishes only actual absence");
    Save(output, "purged.json", purged, adapter);
    std::string serialized, failure;
    const auto stale_payload = "{\"expected_revision\":18,\"actor_character_id\":29829,"
        "\"target_character_id\":34333,\"scheme_instance_id\":134217986}";
    MainThreadQueryMailboxV1 stale_mailbox{};
    Check(!actual4::HandleSwayTerminal12004(adapter, stale_mailbox, adapter.frame,
          kRevision, kSwayCompletionStepV1, stale_payload, "stale", serialized, failure) &&
          serialized.empty() && failure == "sway_terminal_frame_or_request_invalid",
          "production handler rejects stale native revision before query submission");
    std::ofstream manifest(output / "manifest.json", std::ios::binary);
    manifest << "{\"qualification\":\"offline synthetic FIRST, not live\","
        "\"native_packets\":[\"current.json\",\"terminated.json\",\"reused.json\",\"purged.json\"],"
        "\"production_executor\":\"ExecuteSwayTerminalMailbox12004\","
        "\"production_serializer\":\"SerializeSwayTerminalCommandResult12004\","
        "\"stale_handler_rejected\":true,\"command_submissions\":0,\"compound_cases\":1}\n";
    Check(manifest.good(), "FIRST manifest");
    std::cout << "PASS unique actual4 retained terminal whole-producer FIRST\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
