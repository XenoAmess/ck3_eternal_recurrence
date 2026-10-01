// Synthetic native stores and native-call substitutions exercise the actual
// 1.20 source adapter, LAW4/LAW5 binder, worker handler and wire serializers.
#include "ck3_12002_realm_law_action_mailbox_fixture.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include <filesystem>
#include <fstream>
#include <windows.h>
namespace {
using namespace xar;
class RouterAdapter final : public game::GameAdapter {
public:
  game::Snapshot snapshot{};
  RouterAdapter() {
    snapshot.date_raw = 53169072;
    snapshot.paused = snapshot.map_ready = snapshot.has_played_character = snapshot.played_character_alive = true;
    snapshot.played_character_id = actor_id;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor d{"ck3-1.20.0.2-msvc-x64", "1.20.0.2", kExecutableSha256, "fixture", {}};
    return d;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override { out = snapshot; return true; }
#define XAR_R0(T, M) game::T M() const noexcept override { return {}; }
#define XAR_R1(T, M, A) game::T M(A) const noexcept override { return {}; }
#define XAR_R2(T, M, A, B) game::T M(A, B) const noexcept override { return {}; }
#define XAR_R3(T, M, A, B, C) game::T M(A, B, C) const noexcept override { return {}; }
  XAR_R1(PauseSubmitResult, submit_pause_map, game::Snapshot *)
  XAR_R1(ResumeSubmitResult, submit_resume_map, game::Snapshot *)
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  XAR_R1(SelectEventOptionResult, submit_select_event_option, std::int32_t)
  XAR_R0(SaveCheckpointResult, submit_save_checkpoint)
  XAR_R1(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, game::PendingInteractionReply)
  XAR_R0(RaiseTroopsResult, submit_raise_troops_default)
  XAR_R2(MoveArmyResult, submit_move_army, std::int32_t, std::int32_t)
  XAR_R2(PreviewMoveArmyResult, preview_move_army, std::int32_t, std::int32_t)
  XAR_R1(DisbandArmyResult, submit_disband_army, std::int32_t)
  XAR_R1(SplitArmyHalfResult, submit_split_army_half, std::int32_t)
  XAR_R2(MergeArmiesResult, submit_merge_armies, std::int32_t, std::int32_t)
  XAR_R1(StartAssaultResult, submit_start_assault, std::int32_t)
  XAR_R1(StopAssaultResult, submit_stop_assault, std::int32_t)
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
  XAR_R2(ReadDeclarableWarsResult, read_declarable_wars_for_target, std::int32_t, std::vector<game::DeclarableWarSnapshot> &)
  XAR_R1(DeclareWarResult, submit_declare_war, const game::DeclarableWarSnapshot &)
  XAR_R2(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &)
  XAR_R1(ArrangeMarriageResult, submit_arrange_marriage, const game::ArrangeMarriageChoice &)
  XAR_R1(EnforceDemandsResult, submit_enforce_demands, std::int32_t)
  XAR_R1(ReadArmyStrengthsResult, read_army_strengths, std::vector<game::ArmyStrengthSnapshot> &)
  XAR_R2(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &)
  XAR_R2(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &)
  XAR_R2(ReadWarTerminationOptionsResult, read_war_termination_options, std::int32_t, game::WarTerminationOptionsSnapshot &)
  XAR_R2(ReadWarTerminationTermsResult, read_war_termination_terms, std::int32_t, game::WarTerminationTermsSnapshot &)
  XAR_R2(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, std::int32_t, game::WarTerminationExitTermsSnapshot &)
  XAR_R1(SurrenderWarResult, submit_surrender_war, std::int32_t)
  XAR_R1(OfferWhitePeaceResult, submit_offer_white_peace, std::int32_t)
#undef XAR_R0
#undef XAR_R1
#undef XAR_R2
#undef XAR_R3
};

std::string Payload(std::uint64_t revision) {
  return "{\"expected_revision\":" + std::to_string(revision) +
      ",\"expected_date_raw\":53169072,\"expected_player_character_id\":" + std::to_string(actor_id);
}
void Write(const std::filesystem::path &directory, std::string_view name, const std::string &wire) {
  if (!directory.empty()) { std::ofstream out(directory/name, std::ios::binary); out << wire << '\n'; assert(out.good()); }
}
}
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
namespace xar::ck3_11906 {
// Queue scheduling is the sole mailbox substitution. All production owner
// and frame checks are executed by the actual QueryMailboxEnvelope code.
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 executor, void *opaque, MainThreadQueryTicketV1 &ticket,
    MainThreadQueryQueuedWakeTraceV1 *) noexcept {
  if (mailbox.executor != nullptr || executor != mailbox.permitted_executor_septentrigintary)
    return MainThreadQuerySubmitResultV1::mailbox_busy;
  ticket.sequence = mailbox.published_sequence.fetch_add(1) + 1;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = executor; mailbox.executor_context = opaque;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = ticket.sequence; stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true; stamp.date_raw = 53169072;
  stamp.tls_initialized = stamp.tls_main_thread_marker = 1;
  stamp.tls_context = stamp.jomini_state = stamp.game_state = 1;
  const bool ok = executor(opaque, stamp);
  mailbox.state = ok ? MainThreadQueryMailboxStateV1::completed : MainThreadQueryMailboxStateV1::executor_failed;
  return MainThreadQuerySubmitResultV1::submitted;
}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &, std::uint32_t, MainThreadQueryQueuedWakeTraceV1 *,
    std::uint32_t) noexcept {
  return mailbox.state == MainThreadQueryMailboxStateV1::completed
      ? MainThreadQueryWaitResultV1::completed : MainThreadQueryWaitResultV1::executor_failed;
}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &) noexcept {
  mailbox.state = MainThreadQueryMailboxStateV1::idle;
  mailbox.executor = nullptr; mailbox.executor_context = nullptr;
  return MainThreadQueryReclaimResultV1::reclaimed;
}
}
int main(int argc, char **argv) {
  const std::filesystem::path output = argc == 2 ? argv[1] : "";
  Fixture fixture;
  RouterAdapter adapter;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_septentrigintary = &ExecuteRealmLawPrivateAction12002;
  law::AddLawCommandOfflineCallsV1 calls{&fixture, Fixture::Validate, Fixture::Clone, Fixture::Queue, Fixture::DestroyCommand};
  RealmLawActionMailboxFixture12002 bindings{};
  bindings.module_base = base; bindings.context = &fixture; bindings.read_memory = Fixture::Memory;
  bindings.final_operations = {{Fixture::Kind, Fixture::Active, Fixture::Final, Fixture::Cost}, Fixture::Reason, Fixture::DestroyReason};
  bindings.component_operations = {true, Fixture::Scope, Fixture::Component, Fixture::DestroyScope, Fixture::DestroyScope};
  bindings.primary_title = Fixture::Primary;
  bindings.command_access.module_base = base;
  bindings.command_access.submit_enabled = true;
  bindings.command_access.mutation_abi_proof.verified = true;
  bindings.command_access.offline_calls = &calls;
  auto state = std::make_unique<RealmLawActionMailboxState12002>();
  std::string wire, failure;
  const auto call = [&](std::string_view step, const std::string &payload, std::uint64_t revision) {
    const bool ok = HandleRealmLawPrivateWithState12002(*state, adapter, mailbox, adapter.snapshot,
        revision, step, payload, "unique-wire-id-" + std::to_string(mailbox.published_sequence.load()), wire, failure, &bindings);
    if (!ok) std::cerr << "failure: " << failure << "; source: " << state->source.failure << '\n';
    return ok;
  };
  assert(call(kRealmLawCrownActionQueryStep12002, Payload(40) + "}", 40));
  assert(wire.find("\"status\":\"available\"") != std::string::npos);
  assert(wire.find("\"proof_epoch\":40") != std::string::npos);
  assert(wire.find("\"amount_raw\":50000000") != std::string::npos);
  assert(wire.find("\"successor_character_ids\":[33554434,50331651]") != std::string::npos);
  Write(output, "wire-law-crown-query.json", wire);
  const auto submit = Payload(40) + ",\"submitted_request_id\":\"selected-law-action\","
      "\"group_key\":\"crown_authority\",\"law_key\":\"crown_authority_1\","
      "\"expected_native_revision\":40,\"expected_proof_epoch\":40,\"budget_prestige_raw\":20000000}";
  assert(call(kRealmLawCrownEnactStep12002, submit, 40));
  assert(state->has_pending_ack && state->binder.submit_pending && fixture.queued == 1);
  assert(wire.find("submitted_verification_pending") != std::string::npos);
  Write(output, "wire-law-crown-submit-pending.json", wire);
  assert(!call(kRealmLawCrownEnactStep12002, submit, 40));
  assert(fixture.queued == 1);
  assert(call(kRealmLawCrownReceiptStep12002,
      Payload(41) + ",\"submitted_request_id\":\"selected-law-action\"}", 41));
  assert(wire.find("\"status\":\"failed\"") != std::string::npos && state->has_pending_ack);
  Write(output, "wire-law-crown-receipt-unchanged.json", wire);
  for (const auto &[address, index] : fixture.laws) if (index == 1) fixture.Put(fixture.active_slots, address);
  fixture.Put(resource + 0x130, std::int64_t{30'000'000});
  assert(call(kRealmLawCrownReceiptStep12002,
      Payload(42) + ",\"submitted_request_id\":\"selected-law-action\"}", 42));
  assert(wire.find("\"status\":\"enacted\"") != std::string::npos);
  assert(wire.find("\"resources_verified\":true") != std::string::npos);
  assert(wire.find("\"succession_verified\":true") != std::string::npos);
  assert(!state->has_pending_ack && !state->binder.submit_pending && fixture.queued == 1);
  Write(output, "wire-law-crown-receipt-enacted.json", wire);
  assert(!call(kRealmLawCrownActionQueryStep12002, Payload(40) + "}", 42));
  state = std::make_unique<RealmLawActionMailboxState12002>(); fixture.allowed = false;
  assert(call(kRealmLawCrownEnactStep12002, submit, 40));
  assert(wire.find("rejected_before_submit") != std::string::npos && fixture.queued == 1);
  Write(output, "wire-law-crown-submit-native-denied.json", wire);
  std::cout << "PASS actual 1.20 law worker/source/binder/wire: query, chosen typed submit, ACK pending, unchanged failed receipt, independent effective law/resource/full-successor success, native denial and stale frame no-op; no CK3 access\n";
}
