// Fixture-owned native stores and typed queue use the same exact-build
// layouts as the provider fixture; its standalone matrix is not rerun.
#include "ck3_12002_faction_gift_router_fixture.hpp"

#include "xar_bridge/ck3_12002_faction_gift_router.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include <filesystem>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
constexpr std::uint32_t source_id = 0x05000003;
bool empty_targeting = false;
int router_checks = 0;
void CheckRouter(bool value) {
  ++router_checks;
  if (!value) std::cerr << "router check failed: " << router_checks << '\n';
  assert(value);
}

class RouterAdapter final : public game::GameAdapter {
public:
  game::Snapshot snapshot{};
  RouterAdapter() {
    snapshot.date_raw = 53175816;
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

bool RootSource(void *opaque, const game::CampaignRootFrameV1 &frame,
    game::CampaignRootContextV1 &out) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(fixture.b.interaction.core, current) ||
      current.played_character_id != frame.played_character_id || current.clock.date_raw != frame.date_raw)
    return false;
  out = fixture.campaign;
  out.snapshot_revision = frame.snapshot_revision;
  return true;
}

bool AlertSource(void *opaque, const game::PlayerFactionAlertsFrameV1 &frame,
    game::PlayerFactionAlertsV1 &out) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  out = {};
  out.status = game::PlayerFactionAlertsStatusV1::available;
  out.snapshot_revision = frame.snapshot_revision;
  out.date_raw = frame.date_raw; out.player_character_id = frame.played_character_id;
  out.readiness.targeting_rows_ready = out.readiness.same_frame_ready = true;
  if (!empty_targeting) {
    game::PlayerTargetingFactionV1 row{};
    if (ReadFactionEntityV1(fixture.factions, fixture.faction_access, source_id, row) !=
        ReadFactionEntityResult12002::available) return false;
    out.targeting_factions.push_back(std::move(row));
  }
  out.targeting_faction_count = static_cast<std::int32_t>(out.targeting_factions.size());
  return true;
}

std::string FramePayload(std::uint64_t revision) {
  return "{\"expected_revision\":" + std::to_string(revision) +
      ",\"expected_date_raw\":53175816,\"expected_player_character_id\":" + std::to_string(actor_id);
}
std::string IdPayload(std::uint64_t revision) {
  return FramePayload(revision) + ",\"source_faction_id\":" + std::to_string(source_id) +
      ",\"recipient_character_id\":" + std::to_string(recipient_id) + "}";
}
void WriteWire(const std::filesystem::path &dir, std::string_view name, const std::string &wire) {
  if (!dir.empty()) std::ofstream(dir / name) << wire << '\n';
}
} // namespace

// This fixture simulates the already-tested queue ownership boundary only.
// The production envelope, actual native gift/faction/opinion readers and
// action/receipt algorithms remain linked unchanged.
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 executor, void *opaque, MainThreadQueryTicketV1 &ticket,
    MainThreadQueryQueuedWakeTraceV1 *) noexcept {
  if (mailbox.executor != nullptr || executor != mailbox.permitted_executor_quattuortrigintary)
    return MainThreadQuerySubmitResultV1::mailbox_busy;
  ticket.sequence = mailbox.published_sequence.fetch_add(1) + 1;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = executor; mailbox.executor_context = opaque;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = ticket.sequence; stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true; stamp.date_raw = 53175816;
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
} // namespace xar::ck3_11906

int main(int argc, char **argv) {
  const std::filesystem::path out = argc > 1 ? argv[1] : "";
  Fixture fixture;
  RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_quattuortrigintary = &ExecuteFactionGiftPrivateMailbox12002;
  FactionGiftPrivateFixtureBindings12002 bindings{};
  bindings.factions = fixture.factions; bindings.gift = fixture.b;
  bindings.context = &fixture; bindings.read_campaign = &RootSource; bindings.read_alerts = &AlertSource;
  FactionGiftPrivateState12002 state;
  std::string wire, failure;
  const auto call = [&](std::string_view step, const std::string &payload, std::uint64_t revision,
      std::string_view request_id = "offline-gift-router-once") {
    return HandleFactionGiftPrivate12002(adapter, mailbox, adapter.snapshot, revision,
        step, payload, request_id, state, wire, failure, &bindings);
  };
  legal = false;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 1));
  CheckRouter(state.last_query && state.last_query->available && !state.last_query->gift_preview.interaction_legal);
  CheckRouter(wire.find("\"status\":\"no_legal_candidate\"") != std::string::npos);
  WriteWire(out, "wire-query-can-send-false.json", wire);
  legal = true;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 1));
  CheckRouter(state.last_query && state.last_query->player_gold_raw == 20'000'000 &&
      state.last_query->recipient_opinion_of_player == 0 &&
      state.last_query->source_faction_power_raw == 11'000'000);
  WriteWire(out, "wire-query-preview.json", wire);
  const std::string submit = FramePayload(1) + ",\"source_faction_id\":" + std::to_string(source_id) +
      ",\"recipient_character_id\":" + std::to_string(recipient_id) +
      ",\"membership_role\":\"leader\",\"definition_stable_hash\":" + std::to_string(definition_hash) +
      ",\"gold_cost_raw\":7500000,\"opinion_delta\":35,\"minimum_gold_reserve_raw\":5000000,"
      "\"expected_native_revision\":1}";
  const auto queues_before = queues;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateSubmitStepV1, submit, 1));
  CheckRouter(state.pending_ack && state.pending_ack->verification_pending &&
      state.action_may_have_submitted && queues == queues_before + 1);
  CheckRouter(wire.find("submitted_verification_pending") != std::string::npos);
  WriteWire(out, "wire-submit-ack-pending.json", wire);
  CheckRouter(!call(ck3_11906::kFactionGiftPrivateSubmitStepV1, submit, 1));
  CheckRouter(queues == queues_before + 1);
  CheckRouter(call(ck3_11906::kFactionGiftPrivateReceiptStepV1, FramePayload(2) + "}", 2));
  CheckRouter(wire.find("gift_gold_delta_not_observed") != std::string::npos &&
      wire.find("\"postcondition_verified\":false") != std::string::npos);
  WriteWire(out, "wire-receipt-unchanged.json", wire);
  Put(fixture.player_extension.data(), 0x100, std::int64_t{12'500'000});
  gift_applied = true;
  Put(opinion_group.data(), 0x14, std::int32_t{1});
  CheckRouter(call(ck3_11906::kFactionGiftPrivateReceiptStepV1, FramePayload(3) + "}", 3));
  CheckRouter(wire.find("\"status\":\"applied\"") != std::string::npos &&
      wire.find("\"postcondition_verified\":true") != std::string::npos);
  WriteWire(out, "wire-receipt-applied.json", wire);
  state = {}; empty_targeting = true;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1, IdPayload(4), 4));
  CheckRouter(wire.find("independent_read_complete") != std::string::npos &&
      wire.find("\"source_faction_present\":true") != std::string::npos &&
      wire.find("\"gift_opinion_present\":true") != std::string::npos);
  WriteWire(out, "wire-cold-persisted-source.json", wire);
  Put(fixture.faction_slots.data(), 3 * 0x10 + 8, static_cast<void *>(nullptr));
  CheckRouter(call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1, IdPayload(5), 5));
  CheckRouter(wire.find("\"source_faction_requery_complete\":true") != std::string::npos &&
      wire.find("\"source_faction_present\":false") != std::string::npos);
  WriteWire(out, "wire-cold-dissolved-source.json", wire);
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(5) + "}", 5));
  CheckRouter(wire.find("\"status\":\"known_empty\"") != std::string::npos && !state.last_query);
  WriteWire(out, "wire-query-known-empty.json", wire);
  CheckRouter(!call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 5));
  CheckRouter(failure == "private_faction_frame_invalid");
  std::cout << "PASS gift private router 1.20: " << router_checks
      << " checks; actual native observation/faction/opinion/context/typed queue; simulated mailbox; no CK3 access\n";
  return 0;
}
