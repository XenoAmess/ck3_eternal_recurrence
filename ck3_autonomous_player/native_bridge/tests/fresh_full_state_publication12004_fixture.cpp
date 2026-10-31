#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <array>
#include <charconv>
#include <limits>
#include <optional>
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/player_event_trait_membership_12004.hpp"
#include "xar_bridge/province_besieging_army_selection_v1.hpp"
#include "xar_bridge/siege_membership_v1.hpp"
#include <atomic>
#include <cstdio>
#include <cstring>
#include <thread>
#include <utility>
#include <vector>

namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;

#define CHECK(expression) do { if (!(expression)) { \
  std::fprintf(stderr, "semantic fixture line %d: %s\n", __LINE__, #expression); \
  return false; } } while (false)

class FixtureAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> raw_reads{0};
  mutable std::atomic<std::uint32_t> semantic_calls{0};
  mutable std::atomic<std::uint32_t> wrong_owner{0};
  mutable std::atomic<DWORD> queue_thread{0};
  mutable std::atomic<std::int32_t> last_event_option{-1};
  mutable std::atomic<std::int32_t> last_army{-1};
  mutable std::atomic<std::int32_t> last_province{-1};
  mutable std::atomic<std::int32_t> last_family_subject{-1};
  bool reader_available = true;
  bool declarations_available = true;
  bool family_available = true;
  bool patch3 = false;
  bool patch4 = false;

  FixtureAdapter() {
    frame.date_raw = 123456;
    frame.speed = 3;
    frame.player_id = 7;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_id = 0x12000015;
    frame.played_character_alive = true;
    frame.has_active_event = true;
    frame.active_event_instance_id = 91;
    frame.active_event_option_count = 3;
    game::ArmySnapshot army{};
    army.army_id = 0x23000031;
    army.owner_character_id = frame.played_character_id;
    army.controllable = true;
    army.has_current_province = true;
    army.current_province_id = 900;
    frame.player_armies.push_back(army);
  }

  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 1> capabilities{
      "game.state.snapshot"};
    static const game::AdapterDescriptor value{
      xar::ck3_12004::kAdapterId, xar::ck3_12004::kGameVersion,
      xar::ck3_12004::kExecutableSha256, "offline-fresh-fixture",
      std::span<const std::string_view>{capabilities}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  void RecordSemantic() const noexcept {
    ++semantic_calls;
    if (GetCurrentThreadId() != owner) ++wrong_owner;
  }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++raw_reads;
    if (GetCurrentThreadId() != owner) {
      ++wrong_owner;
      output = {};
      return false;
    }
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::ResumeSubmitResult::submitted;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    queue_thread = GetCurrentThreadId();
    return speed == 4;
  }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return {game::SaveCheckpointStatus::submitted, 123456};
  }
  game::SelectEventOptionResult submit_select_event_option(
      std::int32_t option) const noexcept override {
    RecordSemantic();
    last_event_option = option;
    return option < 0 || option >= frame.active_event_option_count
      ? game::SelectEventOptionResult::option_out_of_range
      : game::SelectEventOptionResult::submitted;
  }
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return false;
    output.push_back({0x14000042, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return true;
  }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_id,
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return game::ReadDeclarableWarsResult::unavailable;
    if (target_id != 0x14000042) return game::ReadDeclarableWarsResult::target_not_found;
    output.push_back({target_id, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return game::ReadDeclarableWarsResult::available;
  }
  game::MoveArmyResult submit_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    RecordSemantic();
    last_army = army;
    last_province = province;
    return army == frame.player_armies.front().army_id && province == 901
      ? game::MoveArmyResult::submitted : game::MoveArmyResult::validation_failed;
  }
  game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<game::ArmyStrengthSnapshot> &output) const noexcept override {
    RecordSemantic();
    game::ArmyStrengthSnapshot row{};
    row.available = true;
    row.army_id = frame.player_armies.front().army_id;
    row.regiment_count = 2;
    row.current_soldiers = 734;
    row.maximum_soldiers = 1000;
    row.ai_base_power_raw = 123456789;
    output = {row};
    return game::ReadArmyStrengthsResult::available;
  }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    output = {{frame.played_character_id, 0x15000011}};
    diagnostics = {};
    diagnostics.storage_capacity = 17;
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageChoicesResult::available;
  }
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept override {
    RecordSemantic();
    output = {};
    if (frame.active_wars.empty() || frame.active_wars.front().war_id != war_id)
      return game::ReadWarTerminationOptionsResult::war_not_found;
    output.war_id = war_id;
    output.player_relative_war_score = frame.active_wars.front().player_relative_war_score;
    return game::ReadWarTerminationOptionsResult::available;
  }
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    last_family_subject = subject_id;
    output.clear();
    diagnostics = {};
    if (subject_id != 0x13000016)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::subject_not_found;
    diagnostics.storage_capacity = 17;
    diagnostics.slots_scanned = 2;
    if (!family_available)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = frame.played_character_id;
    row.subject_character_id = subject_id;
    row.candidate_character_id = 0x15000011;
    row.recipient_matchmaker_character_id = 0x14000042;
    row.recipient_ai_accept_raw = 2'500'000;
    row.recipient_answer_status_raw = 1;
    row.complete_can_send = true;
    row.recipient_answer_allows_send = true;
    row.heir_adult_measure_raw = std::int16_t{17};
    row.candidate_adult_measure_raw = std::int16_t{19};
    row.played_dynasty_id = 71;
    row.heir_dynasty_id = 71;
    row.candidate_dynasty_id = 72;
    row.realm_backed_actor_recipient = true;
    output.push_back(row);
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageFamilyCandidatesResultV1::available;
  }

#define UNAVAILABLE_RESULT(Result, Name, Parameters) \
  game::Result Name Parameters const noexcept override { \
    RecordSemantic(); return game::Result::unavailable; }
  UNAVAILABLE_RESULT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
                     (game::PendingInteractionReply))
  UNAVAILABLE_RESULT(AcknowledgePendingInteractionResult, submit_acknowledge_pending_interaction,
                     (std::int32_t))
  UNAVAILABLE_RESULT(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE_RESULT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE_RESULT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE_RESULT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE_RESULT(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE_RESULT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE_RESULT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE_RESULT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE_RESULT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE_RESULT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE_RESULT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationTermsResult, read_war_termination_terms,
                     (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
                     (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef UNAVAILABLE_RESULT
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override {
    RecordSemantic();
    return {};
  }
};

#include "fresh_bridge_snapshot_support.inc"

// Test only null-lifetime publication path; this fixture never calls MaybeInstall.
struct WarEntryApplicationMainMailboxWorkerLifetime {
  void MaybeInstall(const game::Snapshot &) noexcept { std::terminate(); }
};
#include "fresh_bridge_publish.inc"
bool TestForcedFreshPublication() {
  struct Handles {
    HANDLE read = nullptr;
    HANDLE write = nullptr;
    ~Handles() {
      if (read != nullptr) CloseHandle(read);
      if (write != nullptr) CloseHandle(write);
    }
  } pipe;
  if (!CreatePipe(&pipe.read, &pipe.write, nullptr, 65536)) return false;
  FixtureAdapter native;
  native.patch4 = true;
  auto observed = native.frame;
  observed.played_character_gold = {111, 100000};
  CheckpointSubmission checkpoint{};
  std::optional<game::Snapshot> previous;
  std::uint64_t revision = 0;
  std::uint64_t checkpoint_sequence = 0;
  SnapshotPublishDiagnostics diagnostic;
  const auto read_equals = [&](std::string_view id, std::uint64_t expected) {
    const auto packet = xar::bridge::TryReadFrame(pipe.read);
    return packet.status == xar::bridge::ReadStatus::frame &&
           packet.payload == StateSnapshotFrame(
               observed, expected, checkpoint, {}, id);
  };
  const auto publish = [&](std::string_view id) {
    return PublishSnapshot(pipe.write, native, previous, revision,
        checkpoint, checkpoint_sequence, nullptr, &diagnostic, &observed, id);
  };
  constexpr std::string_view escaped_id = "request\"with\\characters";
  if (!publish(escaped_id) || diagnostic.status != "written" ||
      revision != 1 || previous != std::optional{observed}) return false;
  const auto first = xar::bridge::TryReadFrame(pipe.read);
  if (first.status != xar::bridge::ReadStatus::frame ||
      first.payload != StateSnapshotFrame(observed, 1, checkpoint, {}, escaped_id))
    return false;
  const auto marker = first.payload.find(
      "\"read_request_id\":\"request\\\"with\\\\characters\"");
  const auto state = first.payload.find("\"state\":");
  const auto uncorrelated = StateSnapshotFrame(observed, 1, checkpoint);
  const auto old_state = uncorrelated.find("\"state\":");
  if (marker == std::string::npos || state == std::string::npos ||
      marker >= state || old_state == std::string::npos ||
      first.payload.substr(state) != uncorrelated.substr(old_state)) return false;
  if (!publish("unchanged-1") || diagnostic.status != "written" ||
      revision != 1 || !read_equals("unchanged-1", 1)) return false;
  observed.played_character_gold.raw = 222;
  if (!publish("changed-2") || diagnostic.status != "written" ||
      revision != 2 || !read_equals("changed-2", 2)) return false;
  if (!publish("unchanged-2") || diagnostic.status != "written" ||
      revision != 2 || !read_equals("unchanged-2", 2)) return false;
  if (!publish({}) || diagnostic.status != "deduplicated" ||
      xar::bridge::TryReadFrame(pipe.read).status != xar::bridge::ReadStatus::none)
    return false;
  const auto before = previous;
  const auto old_revision = revision;
  const auto old_checkpoint_sequence = checkpoint_sequence;
  const auto reads = native.raw_reads.load();
  if (!PublishSnapshot(pipe.write, native, previous, revision,
          checkpoint, checkpoint_sequence, nullptr, &diagnostic,
          nullptr, "requires-real-observation") ||
      diagnostic.status != "fresh_observation_required" ||
      native.raw_reads.load() != reads || previous != before ||
      revision != old_revision || checkpoint_sequence != old_checkpoint_sequence ||
      xar::bridge::TryReadFrame(pipe.read).status != xar::bridge::ReadStatus::none)
    return false;
  observed.played_character_gold.raw = 333;
  checkpoint.sequence = 7;
  checkpoint.date_raw = observed.date_raw;
  checkpoint.save_name = "fixture-checkpoint";
  if (PublishSnapshot(INVALID_HANDLE_VALUE, native, previous, revision,
          checkpoint, checkpoint_sequence, nullptr, &diagnostic,
          &observed, "failed-write") ||
      diagnostic.status != "write_failed" || previous != before ||
      revision != old_revision || checkpoint_sequence != old_checkpoint_sequence)
    return false;
  std::puts("fresh-publication: unchanged correlation, changed revision, original state, no cache fallback, failed-write no commit");
  return true;
}
} // namespace
int main() { return TestForcedFreshPublication() ? 0 : 1; }
