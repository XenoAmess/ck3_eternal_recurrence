#include "xar_bridge/ck3_12003_call_ally_private_action.hpp"
#include "xar_bridge/ck3_12002_family_obligations_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <array>
#include <fstream>
#include <iostream>
#include <stdexcept>

// Offline transport fixture: the production mailbox and serializer are
// unchanged. The native send callback is stubbed here; real native command
// construction, clone and queue are covered by the separate sender fixture.
namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t actor_id = 29829;
constexpr std::int32_t recipient_id = 16810493;
constexpr std::int32_t war_id = 129;
constexpr std::int32_t date_raw = 53236608;
constexpr std::uint64_t revision = 53;
constexpr std::array<std::int64_t, 10> quoted_costs{
    5, 60000000, 7, 8, 9, 10, 11, 12, 13, 14};
const family_obligations_alliance::Bindings *expected_bindings = nullptr;
unsigned native_submit_calls = 0;
unsigned unrelated_query_calls = 0;
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
} // namespace

namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  return adapter;
}
FamilyObligationsBreakBindingsV1 BindFamilyObligationsBreakImageV1(
    std::uintptr_t, std::string_view) noexcept { return {}; }
FamilyObligationsBreakTermsV1 ReadFamilyObligationsBreakTermsV1(
    const FamilyObligationsBreakBindingsV1 &, std::int32_t, std::int32_t) noexcept {
  ++unrelated_query_calls; return {};
}
} // namespace xar::ck3_12002

namespace xar::ck3_12002::family_obligations_lineage {
Bindings BindImage(std::uintptr_t, std::string_view) noexcept { return {}; }
bool Read(const Bindings &, std::int32_t, std::int32_t, bool,
          Snapshot &, std::string_view *) noexcept {
  ++unrelated_query_calls; return false;
}
} // namespace xar::ck3_12002::family_obligations_lineage

namespace xar::ck3_12002::family_obligations_alliance {
Bindings BindImage(std::uintptr_t, std::string_view) noexcept { return {}; }
bool Read(const Bindings &, const CoreSnapshotPrefix &, std::int32_t,
          std::int32_t, Snapshot &, std::string_view *) noexcept {
  ++unrelated_query_calls; return false;
}
bool ReadCurrentAllies(const Bindings &, const CoreSnapshotPrefix &,
                      CurrentAlliesSnapshot &, std::string_view *) noexcept {
  ++unrelated_query_calls; return false;
}
CommandSubmitResult SubmitCallAlly(const Bindings &bindings,
    const CoreSnapshotPrefix &frame, const CallAllySubmitRequest &request,
    CallAllySubmitReceipt &receipt, std::string_view *reason) noexcept {
  ++native_submit_calls;
  // Use explicit failure rather than throwing through the noexcept producer.
  const bool valid = &bindings == expected_bindings && bindings.enabled &&
      frame.clock.paused && frame.clock.date_raw == date_raw && frame.clock.speed == 2 &&
      frame.local_player_id == 0 && frame.map_ready && frame.has_played_character &&
      frame.played_character_id == actor_id && frame.played_character_alive &&
      request.recipient_character_id == recipient_id && request.war_id == war_id &&
      request.expected_send_cost_raw == quoted_costs;
  if (!valid) {
    if (reason != nullptr) *reason = "fixture_submit_inputs_changed";
    return CommandSubmitResult::rejected;
  }
  if (reason != nullptr) *reason = {};
  receipt.selected_target_native_legal = true;
  receipt.copied_context_identity_verified = true;
  receipt.send_cost_sampled = true;
  receipt.actual_send_cost_raw = request.expected_send_cost_raw;
  return CommandSubmitResult::submitted;
}
} // namespace xar::ck3_12002::family_obligations_alliance

// The production build-identity renderer shares a TU with process adapter
// factories. This transport fixture never creates an adapter from native
// bindings; these link providers keep those unrelated factory paths inert.
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(
    std::uintptr_t, std::string_view) noexcept { return {}; }
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept {
  static const AdapterDescriptor descriptor{
      "ck3-1.20.0.2-msvc-x64", "1.20.0.2", ck3_12002::kExecutableSha256, "fixture", {}};
  return descriptor;
}
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(
    Ck3_12003AdapterBindings) noexcept { return {}; }
} // namespace xar::game

namespace {
using namespace xar;
using namespace xar::ck3_12002;
namespace api = xar::ck3_11906;
class Adapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{
        ck3_12003::kAdapterId, ck3_12003::kGameVersion, ck3_12003::kExecutableSha256, "fixture", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    output = frame; ++reads;
    if (drift && reads > 1) ++output.date_raw;
    return true;
  }
  game::PauseSubmitResult submit_pause_map(game::Snapshot *) const noexcept override { return {}; }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot *) const noexcept override { return {}; }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SelectEventOptionResult submit_select_event_option(std::int32_t) const noexcept override { return {}; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply) const noexcept override { return {}; }
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override { return {}; }
  game::MoveArmyResult submit_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::DisbandArmyResult submit_disband_army(std::int32_t) const noexcept override { return {}; }
  game::SplitArmyHalfResult submit_split_army_half(std::int32_t) const noexcept override { return {}; }
  game::MergeArmiesResult submit_merge_armies(std::int32_t, std::int32_t) const noexcept override { return {}; }
  game::StartAssaultResult submit_start_assault(std::int32_t) const noexcept override { return {}; }
  game::StopAssaultResult submit_stop_assault(std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(std::int32_t, std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return {}; }
  game::DeclareWarResult submit_declare_war(const game::DeclarableWarSnapshot &) const noexcept override { return {}; }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &) const noexcept override { return {}; }
  game::ArrangeMarriageResult submit_arrange_marriage(const game::ArrangeMarriageChoice &) const noexcept override { return {}; }
  game::EnforceDemandsResult submit_enforce_demands(std::int32_t) const noexcept override { return {}; }
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &) const noexcept override { return {}; }
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationOptionsResult read_war_termination_options(std::int32_t, game::WarTerminationOptionsSnapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationTermsResult read_war_termination_terms(std::int32_t, game::WarTerminationTermsSnapshot &) const noexcept override { return {}; }
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(std::int32_t, game::WarTerminationExitTermsSnapshot &) const noexcept override { return {}; }
  game::SurrenderWarResult submit_surrender_war(std::int32_t) const noexcept override { return {}; }
  game::OfferWhitePeaceResult submit_offer_white_peace(std::int32_t) const noexcept override { return {}; }
};

void Prepare(Adapter &adapter, api::MainThreadQueryMailboxV1 &mailbox,
             FamilyObligationsMailboxContext12002 &query,
             api::MainThreadExecutionStampV1 &stamp) {
  adapter.frame = {};
  adapter.reads = 0;
  adapter.frame.paused = adapter.frame.map_ready = true;
  adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
  adapter.frame.played_character_id = actor_id;
  adapter.frame.player_id = 0;
  adapter.frame.date_raw = date_raw;
  adapter.frame.speed = 2;
  game::ActiveWarSnapshot war{};
  war.war_id = war_id;
  war.player_is_primary_war_leader = true;
  war.player_side = game::PlayerWarSide::defender;
  war.primary_opponent_character_id = 32750;
  adapter.frame.active_wars.push_back(war);
  query.envelope = {};
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = revision;
  query.envelope.ticket.sequence = 5;
  query.envelope.typed_context = &query;
  mailbox.state = api::MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = 5;
  mailbox.owner_thread_id = adapter.owner;
  mailbox.executor = &ExecuteFamilyObligationsMailbox12002;
  mailbox.executor_context = &query.envelope;
  stamp = {};
  stamp.pump_epoch = 5;
  stamp.thread_id = adapter.owner;
  stamp.paused = true;
  stamp.date_raw = date_raw;
  stamp.tls_initialized = stamp.tls_main_thread_marker = 1;
  stamp.tls_context = stamp.jomini_state = stamp.game_state = 1;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Adapter adapter{};
    api::MainThreadQueryMailboxV1 mailbox{};
    FamilyObligationsMailboxContext12002 query{};
    api::MainThreadExecutionStampV1 stamp{};
    query.call_ally_submission = true;
    query.alliance_bindings.enabled = true;
    const std::string payload =
        "{\"expected_revision\":53,\"recipient_character_id\":16810493,\"war_id\":129,"
        "\"expected_send_cost_raw\":[5,60000000,7,8,9,10,11,12,13,14]}";
    CallAllyPrivateActionRequest12003 parsed{};
    Check(ParseCallAllyPrivateActionRequest12003(payload, parsed) &&
          parsed.expected_revision == revision,
          "real action parser retains current revision and typed request");
    query.call_ally_request = parsed.native_request;
    expected_bindings = &query.alliance_bindings;
    Prepare(adapter, mailbox, query, stamp);
    Check(ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp),
          "production owning-thread executor returns");
    Check(query.completed && query.envelope.frame_stable &&
          query.call_ally_result == CommandSubmitResult::submitted,
          "fresh paused core reaches native submission callback");
    Check(native_submit_calls == 1 && unrelated_query_calls == 0,
          "exactly one submission without unrelated marriage/alliance reads");
    Check(query.call_ally_receipt.selected_target_native_legal &&
          query.call_ally_receipt.copied_context_identity_verified &&
          query.call_ally_receipt.send_cost_sampled &&
          query.call_ally_receipt.actual_send_cost_raw == quoted_costs,
          "actual callback receipt retained by production context");
    const auto wire = SerializeCallAllySubmissionResult12003(
        "call-ally-mailbox-fixture", query);
    Check(!wire.empty(), "registered action serializer emits native wire");
    if (argc >= 2) {
      std::ofstream out(argv[1], std::ios::binary);
      out << wire << '\n';
      Check(static_cast<bool>(out), "native mailbox wire saved");
    }
    if (argc == 3) {
      FamilyObligationsObservation12002 quote{};
      quote.frame = adapter.frame;
      quote.snapshot_revision = revision;
      quote.request.ally_character_id = recipient_id;
      quote.request.expected_snapshot_revision = revision;
      quote.alliance_available = true;
      quote.alliance.first_character_id = actor_id;
      quote.alliance.second_character_id = recipient_id;
      quote.alliance.first_has_second = quote.alliance.second_has_first = true;
      family_obligations_alliance::WarExposure row{};
      row.war_id = war_id;
      row.caller_character_id = row.primary_defender_character_id = actor_id;
      row.recipient_character_id = recipient_id;
      row.primary_attacker_character_id = 32750;
      row.attacker_character_ids = {32750};
      row.defender_character_ids = {actor_id};
      row.caller_side = family_obligations_alliance::Side::defender;
      row.caller_is_primary_war_leader = true;
      row.native_target_can_be_picked = row.native_target_row_selectable = true;
      row.native_complete_can_send = true;
      row.recipient_answer_status_raw = 1;
      row.recipient_acceptance_raw = 100000;
      row.send_cost_raw = quoted_costs;
      quote.alliance.first_wars.push_back(row);
      // Fixture-owned legal quote DTO through the actual production serializer;
      // it does not claim a native game read of this synthetic recipient.
      const auto quote_wire = game::RenderCrozierBuildIdentity(
          SerializeFamilyObligationsResult12002("call-ally-quote-fixture", quote),
          adapter.descriptor());
      std::ofstream out(argv[2], std::ios::binary);
      out << quote_wire << '\n';
      Check(static_cast<bool>(out), "production family quote wire saved");
    }
    // Reentry uses the same query envelope: its EnterQueryMailbox guard must
    // prevent submitting a second command when the callback is seen again.
    ExecuteFamilyObligationsMailbox12002(&query.envelope, stamp);
    Check(native_submit_calls == 1, "same envelope does not resubmit");
    std::cout << "PASS production CallAlly mailbox -> original Bindings stub once -> native action serializer; no CK3 process\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
