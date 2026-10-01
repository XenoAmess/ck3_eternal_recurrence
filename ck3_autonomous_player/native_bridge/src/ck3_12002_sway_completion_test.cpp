#include "xar_bridge/ck3_12002_sway_completion_mailbox.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
namespace game = xar::game;
constexpr std::uintptr_t image_base = 0x140000000;
constexpr std::int32_t actor_id = 0x03000001;
constexpr std::int32_t target_id = 0x03000002;
constexpr std::uint32_t scheme_id = 1;
constexpr std::uint64_t revision = 7;
constexpr std::int32_t date_raw = 53220000;

template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *local_player = nullptr;
const void *expected_scheme = nullptr;
std::int64_t chance_raw = 6'875'000;
int chance_calls = 0;
void *LocalPlayer(void *) { return local_player; }
std::int64_t *CurrentChance(const void *scheme, std::int64_t *out) {
  Check(scheme == expected_scheme && out != nullptr, "native current roll exact scheme/output ABI");
  ++chance_calls; *out = chance_raw; return out;
}

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x23000);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void *, 1> player_entries{player_entry.data()};
  std::array<std::byte, 0x30> character_storage{};
  std::array<std::byte, 16 * 0x10> character_slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x58> scheme_storage{};
  std::array<std::byte, 16 * 0x10> scheme_slots{};
  std::array<std::byte, 0x358> scheme{};
  std::array<std::byte, 0xA60> type{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *characters_pointer = character_storage.data();
  SwayCompletionBindings12002 bindings{};
  SwayCompletionRequestV1 request{revision, actor_id, target_id, scheme_id};
  Fixture() {
    local_player = local.data(); expected_scheme = scheme.data(); chance_calls = 0;
    Put(state.data(), 8, date_raw); Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data()); Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0}); Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, player_entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{0}); Put(player_entry.data(), 0xB0, actor_id);
    Put(character_storage.data(), 0x20, character_slots.data());
    Put(character_storage.data(), 0x2C, std::int32_t{16});
    for (int index = 0; index != 2; ++index) {
      Put(characters[index].data(), 0x18, actor_id + index);
      Put(character_slots.data(), static_cast<std::size_t>(index + 1) * 0x10 + 8,
          characters[index].data());
    }
    Put(game.data(), kSwayManagerOffset12002, image_base + kSwayManagerVtableRva12002);
    Put(game.data(), kSwayManagerOffset12002 + 0x20, scheme_storage.data());
    Put(scheme_storage.data(), 0, image_base + kSwayStorageVtableRva12002);
    Put(scheme_storage.data(), 0x20, scheme_slots.data());
    Put(scheme_storage.data(), 0x2C, std::int32_t{16});
    Put(scheme_slots.data(), 0x10 + 8, scheme.data());
    Put(scheme.data(), 0, image_base + kSwayInstanceVtableRva12002);
    Put(scheme.data(), 0x10, scheme_id); Put(scheme.data(), 0x20, type.data());
    Put(scheme.data(), 0x28, std::int32_t{0}); Put(scheme.data(), 0x2C, actor_id);
    Put(scheme.data(), 0x30, std::uint32_t{0}); Put(scheme.data(), 0x34, target_id);
    Put(type.data(), 0, image_base + kSwayTypeVtableRva12002);
    std::memcpy(type.data() + 0x18, "sway", 5);
    Put(type.data(), 0x28, std::uint64_t{4}); Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    bindings.enabled = true; bindings.image_base = image_base;
    bindings.core = {true, &state_pointer, &jomini_pointer, &characters_pointer, &LocalPlayer};
    bindings.success_chance = &CurrentChance;
  }
};

// A fixture-owned semantic frame and execution stamp exercise the real domain
// executor. The legacy abstract action methods are inert interface stubs.
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-completion", {}};
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

bool Execute(Fixture &fixture, FrameAdapter &adapter,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox, std::uint64_t epoch,
    SwayCompletionStateV1 &output) {
  using namespace xar::ck3_11906;
  SwayCompletionMailboxContextV1 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.ticket.sequence = epoch; query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = revision; query.envelope.typed_context = &query;
  query.request = fixture.request; query.bindings = fixture.bindings;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = epoch; mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = &ExecuteSwayCompletionMailboxV1; mailbox.executor_context = &query.envelope;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch; stamp.thread_id = GetCurrentThreadId(); stamp.paused = true;
  stamp.date_raw = date_raw; stamp.tls_initialized = 1; stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1; stamp.jomini_state = 1; stamp.game_state = 1;
  const bool executed = ExecuteSwayCompletionMailboxV1(&query.envelope, stamp);
  output = query.result;
  return executed && query.completed && query.failure.empty() && query.envelope.frame_stable;
}
void Save(const std::filesystem::path &dir, const char *filename, const SwayCompletionStateV1 &row) {
  const auto wire = SerializeSwayCompletionCommandResultV1(row, revision, date_raw,
      std::string("fixture-sway-completion-") + filename);
  Check(!wire.empty(), "actual completion serializer output");
  std::ofstream file(dir / filename); file << wire << '\n';
  Check(file.good(), "actual wire file saved");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "fixture output-directory argument");
    const std::filesystem::path output{argv[1]};
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.date_raw = date_raw; adapter.frame.paused = true; adapter.frame.speed = 1;
    adapter.frame.player_id = 0; adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true; adapter.frame.played_character_id = actor_id;
    adapter.frame.played_character_alive = true;
    xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;
    SwayCompletionStateV1 row{};
    Check(Execute(fixture, adapter, mailbox, 40, row) && row.available &&
        row.instance_source_observed && row.instance_present && row.exact_instance_join_ready &&
        row.scheme_instance_generation == 0 && row.owner_matches_actor && !row.owner_cleared &&
        row.native_status_observed && row.native_status_raw == 0 && row.native_status_key == "continue" &&
        !row.native_terminal_state_observed && row.native_success_chance_observed &&
        row.native_success_chance_raw == 6'875'000 && row.native_success_chance_scale == 100000 &&
        !row.terminal_cause_observed && row.terminal_cause == "unknown",
        "current complete-ID Sway and actual native current-roll input through owner envelope");
    Save(output, "current-wire.json", row);
    // A native phase resets progress without setting the terminal status.
    Put(fixture.scheme.data(), 0x78, std::int32_t{0});
    chance_raw = -125'000;
    Check(Execute(fixture, adapter, mailbox, 41, row) && row.available &&
        row.native_success_chance_raw == -125'000 && !row.native_terminal_state_observed,
        "reset phase does not terminate; signed native roll input is preserved");
    const auto calls_before_terminal = chance_calls;
    Put(fixture.scheme.data(), 0x28, std::int32_t{1});
    Check(Execute(fixture, adapter, mailbox, 42, row) && row.available &&
        row.native_terminal_state_observed && row.native_status_key == "invalidated" &&
        row.owner_matches_actor && !row.native_success_chance_observed &&
        chance_calls == calls_before_terminal && !row.terminal_cause_observed,
        "native status proves termination while actor is still stored, without guessing cause");
    Put(fixture.scheme.data(), 0x2C, std::uint32_t{0xFFFFFFFFu});
    Check(Execute(fixture, adapter, mailbox, 43, row) && row.available &&
        row.instance_present && row.exact_instance_join_ready && row.owner_cleared &&
        !row.owner_matches_actor && row.native_owner_raw == 0xFFFFFFFFu &&
        row.native_terminal_state_observed && !row.terminal_cause_observed,
        "full-ID/type/target readback remains after native terminal path clears owner");
    Save(output, "terminated-owner-cleared-wire.json", row);
    Put(fixture.scheme_slots.data(), 0x10 + 8, static_cast<void *>(nullptr));
    Check(Execute(fixture, adapter, mailbox, 44, row) && row.available &&
        row.instance_source_observed && !row.instance_present && !row.storage_slot_reused &&
        !row.native_status_observed && !row.native_terminal_state_observed && !row.terminal_cause_observed,
        "manager purge publishes observed absence, without inferring a terminal outcome");
    Save(output, "purged-absence-wire.json", row);
    Put(fixture.scheme_slots.data(), 0x10 + 8, fixture.scheme.data());
    Put(fixture.scheme.data(), 0x10, std::uint32_t{0x01000001u});
    Check(Execute(fixture, adapter, mailbox, 45, row) && row.available &&
        row.storage_slot_reused && !row.instance_present && !row.native_terminal_state_observed,
        "new generation occupying same slot is not the tracked instance");
    Save(output, "reused-slot-wire.json", row);
    Put(fixture.scheme.data(), 0x10, scheme_id); Put(fixture.scheme.data(), 0x2C, actor_id);
    Put(fixture.scheme.data(), 0x28, std::int32_t{2});
    Check(Execute(fixture, adapter, mailbox, 46, row) && row.available &&
        row.instance_present && row.native_status_key == "invalid" && !row.native_terminal_state_observed,
        "native invalid sentinel stays distinct from terminated state");
    Save(output, "invalid-sentinel-wire.json", row);
    fixture.bindings.enabled = false;
    Check(Execute(fixture, adapter, mailbox, 47, row) && !row.available &&
        !row.instance_source_observed && !row.native_terminal_state_observed,
        "unbound provider returns unavailable through the real domain executor");
    Save(output, "unavailable-wire.json", row);
    fixture.bindings.enabled = true;
    fixture.state_pointer = nullptr;
    Check(Execute(fixture, adapter, mailbox, 48, row) && !row.available &&
        row.request == fixture.request && row.scheme_instance_generation == 0 &&
        !row.instance_source_observed && !row.instance_present && !row.native_terminal_state_observed,
        "core unavailable preserves actual request identity for SDK correlation");
    Save(output, "core-unavailable-wire.json", row);
    const auto bound = BindSwayCompletionImage12002(image_base, kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.success_chance) ==
        image_base + 0x2A4A400 && !BindSwayCompletionImage12002(image_base, "1.19.0.6").enabled,
        "bind only the exact new executable and native current-roll getter");
    std::cout << "PASS Sway current/terminal/cleared-owner/absence/reused/sentinel/unavailable/binding cases; "
                 "actual reader + owner QueryMailboxEnvelope + serializer\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
