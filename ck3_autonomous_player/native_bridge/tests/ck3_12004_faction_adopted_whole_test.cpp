// Fixture-owned native stores and typed queue use the same exact-build
// layouts as the provider fixture; its standalone matrix is not rerun.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "ck3_12004_faction_adopted_fixture.hpp"

#include "xar_bridge/ck3_12004_faction_gift_router.hpp"
#include "xar_bridge/ck3_12004_faction_mailbox.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include <filesystem>

namespace {
using namespace xar;
using namespace xar::ck3_12004;
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
    static const game::AdapterDescriptor d{"ck3-1.20.0.4-msvc-x64", "1.20.0.4", kExecutableSha256, "fixture", {}};
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
  if (!ck3_12004::ReadCoreSnapshot(fixture.b.interaction.core, current) ||
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
    if (ck3_12004::ReadFactionEntity12004(fixture.factions, fixture.faction_access, source_id, row) !=
        ReadFactionEntityResult12004::available) return false;
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

void *alert_county_province = nullptr;
void *AlertProvince(void *) { return alert_county_province; }
std::int32_t AlertCountyOpinion(void *) { return 0; }
std::int64_t *AlertCountyJoin(void *, std::int64_t *out, void *) { *out = 0; return out; }
bool AlertCanAdd(void *, void *) { return false; }

void RunAlertWholes(Fixture &fixture, RouterAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const std::filesystem::path &out) {
  // Fresh synthetic objects exercise the actual .4 handler and typed collector.
  // Callback values are authored; they do not prove the native engine ABI.
  std::array<std::byte, 0x228> land{};
  std::array<std::int32_t, 1> targeting{static_cast<std::int32_t>(source_id)};
  std::array<std::byte, 0x30> title_store{}, culture_store{};
  std::array<std::byte, 8 * 0x10> title_slots{};
  std::array<std::byte, 0x10> culture_slots{};
  std::array<std::byte, 0x340> title{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x3C0> county{};
  std::array<std::byte, 0x18> county_row{}, culture{};
  void *title_store_pointer = title_store.data();
  void *culture_store_pointer = culture_store.data();
  void *fallback = nullptr;
  const std::int32_t county_id = 0x06000004;
  const std::int32_t leave_threshold = -10;
  const auto original = fixture.factions;
  auto environment = original;
  environment.character_fallback_slot = &fallback;
  environment.landed_title_storage_slot = &title_store_pointer;
  environment.landed_title_fallback_slot = &fallback;
  environment.culture_storage_slot = &culture_store_pointer;
  environment.culture_fallback_slot = &fallback;
  environment.title_province = &AlertProvince;
  environment.county_observations_12003 = true;
  environment.county_opinion = &AlertCountyOpinion;
  environment.county_faction_finals = {&AlertCountyJoin, &AlertCanAdd, &leave_threshold};
  Put(fixture.characters[0].data(), 0x1C0, land.data());
  Put(land.data(), 0x120, targeting.data());
  Put(title_store.data(), 0x20, title_slots.data());
  Put(title_store.data(), 0x2C, std::int32_t{8});
  Put(title_slots.data(), 4 * 0x10 + 8, title.data());
  Put(title.data(), 0x10, county_id);
  Put(title.data(), 0x128, actor_id);
  Put(title.data(), 0x108, std::int32_t{-1});
  Put(province.data(), 0x10, county_id);
  Put(province.data(), 0x85C, std::uint32_t{0x50726F76});
  Put(province.data(), 0x848, county.data());
  Put(county.data(), 0x18, county_id);
  Put(culture_store.data(), 0x20, culture_slots.data());
  Put(culture_store.data(), 0x2C, std::int32_t{1});
  Put(culture_slots.data(), 8, culture.data());
  Put(culture.data(), 0x10, std::int32_t{0});
  Put(county_row.data(), 8, county_id);
  Put(county_row.data(), 0x10, fixture.faction.data());
  alert_county_province = province.data();
  mailbox.permitted_executor_secondary = &ExecutePlayerFactionAlertsMailbox12004;
  std::string wire, failure;
  const auto call = [&](std::string_view filename) {
    const bool handled = HandlePlayerFactionAlerts12004(adapter, mailbox, adapter.snapshot,
        1, "{\"expected_revision\":1}", filename, wire, failure, &environment);
    if (!handled) std::cerr << "faction alerts handler failed: " << filename << ": " << failure << '\n';
    CheckRouter(handled);
    CheckRouter(wire.find("\"game_version\":\"1.20.0.4\"") != std::string::npos);
    WriteWire(out, filename, wire);
  };
  call("alerts-known-empty.command-result.json");
  CheckRouter(wire.find("\"targeting_faction_count\":0") != std::string::npos);
  Put(land.data(), 0x12C, std::int32_t{1});
  call("alerts-character-member.command-result.json");
  CheckRouter(wire.find("\"targeting_faction_count\":1") != std::string::npos);
  Put(fixture.faction.data(), 0x54, std::int32_t{0});
  Put(fixture.faction.data(), 0x60, county_row.data());
  Put(fixture.faction.data(), 0x6C, std::int32_t{1});
  const std::string_view populist = "populist_faction";
  Put(fixture.faction_type.data() + 0x18, 0, populist.data());
  Put(fixture.faction_type.data(), 0x28, std::uint64_t{populist.size()});
  Put(fixture.faction_type.data(), 0x30, std::uint64_t{16});
  call("alerts-county-member.command-result.json");
  CheckRouter(wire.find("\"county_opinion\":{\"raw\":0,\"scale\":1}") != std::string::npos);
  CheckRouter(wire.find("\"native_county_join_score\":{\"raw\":0,\"scale\":100000}") != std::string::npos);
  environment.exact_build_admitted = false;
  call("alerts-unavailable.command-result.json");
  CheckRouter(wire.find("\"unavailable_reason\":\"unsupported_build\"") != std::string::npos);
  fixture.factions = original;
  Put(fixture.characters[0].data(), 0x1C0, static_cast<void *>(nullptr));
  Put(fixture.faction.data(), 0x54, std::int32_t{1});
  Put(fixture.faction.data(), 0x60, static_cast<void *>(nullptr));
  Put(fixture.faction.data(), 0x6C, std::int32_t{0});
  std::memcpy(fixture.faction_type.data() + 0x18, "liberty_faction", 15);
  Put(fixture.faction_type.data(), 0x28, std::uint64_t{15});
  Put(fixture.faction_type.data(), 0x30, std::uint64_t{15});
}
} // namespace

// This fixture simulates the already-tested queue ownership boundary only.
// The production envelope, actual native gift/faction/opinion readers and
// action/receipt algorithms remain linked unchanged.

namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1 &mailbox,
    MainThreadQueryExecutorV1 executor, void *opaque, MainThreadQueryTicketV1 &ticket,
    MainThreadQueryQueuedWakeTraceV1 *) noexcept {
  if (mailbox.executor != nullptr || (executor != mailbox.permitted_executor_quattuortrigintary && executor != mailbox.permitted_executor_secondary))
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
  const auto &envelope = *static_cast<const ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope.entered || !envelope.frame_stable) {
    game::Snapshot captured{};
    const bool read = envelope.game != nullptr && envelope.game->read_snapshot(captured);
    std::cerr << "faction fixture envelope failed: entered=" << envelope.entered
        << " frame_stable=" << envelope.frame_stable << " snapshot_read=" << read
        << " snapshot_equal=" << (read && captured == envelope.expected_snapshot)
        << " descriptor_12004=" << (envelope.game != nullptr && game::IsCk3_12004Descriptor(envelope.game->descriptor()))
        << " owning_thread=" << ck3_12002::IsQueryOwningThread(const_cast<ck3_12002::QueryMailboxEnvelope *>(&envelope))
        << " expected_revision=" << envelope.expected_snapshot_revision
        << " captured_date=" << captured.date_raw << " stamp_date=" << stamp.date_raw
        << " ticket=" << envelope.ticket.sequence << " published=" << mailbox.published_sequence.load()
        << " owner=" << mailbox.owner_thread_id.load() << " thread=" << stamp.thread_id
        << " executor_equal=" << (mailbox.executor == envelope.executor)
        << " context_equal=" << (mailbox.executor_context == &envelope)
        << " failure_flags=" << mailbox.failure_flags.load()
        << " stop_requested=" << mailbox.stop_requested.load() << '\n';
  }
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
  if (!out.empty()) std::filesystem::create_directories(out);
  Fixture fixture;
  RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_quattuortrigintary = &ExecuteFactionGiftPrivateMailbox12004;
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions = fixture.factions; bindings.gift = fixture.b;
  bindings.context = &fixture; bindings.read_campaign = &RootSource; bindings.read_alerts = &AlertSource;
  FactionGiftPrivateState12004 state;
  std::string wire, failure;
  const auto call = [&](std::string_view step, const std::string &payload, std::uint64_t revision,
      std::string_view request_id = "faction-gift-00000000000000000000000000000001") {
    return HandleFactionGiftPrivate12004(adapter, mailbox, adapter.snapshot, revision,
        step, payload, request_id, state, wire, failure, &bindings);
  };
  RunAlertWholes(fixture, adapter, mailbox, out);
  legal = false;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 1));
  CheckRouter(state.last_query && state.last_query->available && !state.last_query->gift_preview.interaction_legal);
  CheckRouter(wire.find("\"status\":\"no_legal_candidate\"") != std::string::npos);
  WriteWire(out, "gift-can-send-false.command-result.json", wire);
  legal = true;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 1));
  CheckRouter(state.last_query && state.last_query->player_gold_raw == 20'000'000 &&
      state.last_query->recipient_opinion_of_player == 0 &&
      state.last_query->source_faction_power_raw == 11'000'000);
  WriteWire(out, "gift-preview.command-result.json", wire);
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
  WriteWire(out, "gift-submit-pending.command-result.json", wire);
  CheckRouter(!call(ck3_11906::kFactionGiftPrivateSubmitStepV1, submit, 1));
  CheckRouter(queues == queues_before + 1);
  CheckRouter(call(ck3_11906::kFactionGiftPrivateReceiptStepV1, FramePayload(2) + "}", 2));
  CheckRouter(wire.find("gift_gold_delta_not_observed") != std::string::npos &&
      wire.find("\"postcondition_verified\":false") != std::string::npos);
  WriteWire(out, "gift-receipt-unchanged.command-result.json", wire);
  Put(fixture.player_extension.data(), 0x100, std::int64_t{12'500'000});
  gift_applied = true;
  Put(opinion_group.data(), 0x14, std::int32_t{1});
  CheckRouter(call(ck3_11906::kFactionGiftPrivateReceiptStepV1, FramePayload(3) + "}", 3));
  CheckRouter(wire.find("\"status\":\"applied\"") != std::string::npos &&
      wire.find("\"postcondition_verified\":true") != std::string::npos);
  WriteWire(out, "gift-receipt-applied.command-result.json", wire);
  state = {}; empty_targeting = true;
  CheckRouter(call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1, IdPayload(4), 4));
  CheckRouter(wire.find("independent_read_complete") != std::string::npos &&
      wire.find("\"source_faction_present\":true") != std::string::npos &&
      wire.find("\"gift_opinion_present\":true") != std::string::npos);
  WriteWire(out, "gift-cold-persisted.command-result.json", wire);
  Put(fixture.faction_slots.data(), 3 * 0x10 + 8, static_cast<void *>(nullptr));
  CheckRouter(call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1, IdPayload(5), 5));
  CheckRouter(wire.find("\"source_faction_requery_complete\":true") != std::string::npos &&
      wire.find("\"source_faction_present\":false") != std::string::npos);
  WriteWire(out, "gift-cold-absent.command-result.json", wire);
  CheckRouter(call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(5) + "}", 5));
  CheckRouter(wire.find("\"status\":\"known_empty\"") != std::string::npos && !state.last_query);
  WriteWire(out, "gift-known-empty.command-result.json", wire);
  CheckRouter(!call(ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}", 5));
  CheckRouter(failure == "private_faction_frame_invalid");
  std::cout << "PASS authored faction whole source fixture 1.20.0.4: " << router_checks
      << " checks; actual native observation/faction/opinion/context/typed queue; substituted fixture transport; no CK3 access or ABI qualification\n";
  return 0;
}
