#include "xar_bridge/ck3_12004_adapter.hpp"
#define XAR_CK3_FACTION_GIFT_DYNAMIC_FIXTURE_IDS 1
#include "ck3_12004_faction_adopted_fixture.hpp"
#include "xar_bridge/ck3_12004_faction_gift_router.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <filesystem>
#include <type_traits>
static_assert(std::is_same_v<decltype(xar::game::Snapshot{}.played_character_id), std::int32_t>,
    "raw private character conversion requires the public signed32 field contract");
namespace {
using namespace xar;
using namespace xar::ck3_12004;
constexpr std::uint32_t source_id = 0x05000003;
bool empty_targeting = false;
int router_checks = 0;
void CheckRouterAt(bool value, int line) {
  ++router_checks;
  if (!value) std::cerr << "router check failed: " << router_checks
      << " line " << line << std::endl;
  assert(value);
}
#define CheckRouter(value) CheckRouterAt((value), __LINE__)

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
  if (dir.empty()) return;
  std::ofstream(dir / name) << wire << '\n';
  HANDLE reader=nullptr,writer=nullptr;
  assert(CreatePipe(&reader,&writer,nullptr,128*1024));
  assert(bridge::WriteFrame(writer,wire));
  CloseHandle(writer);
  std::ofstream packet(dir/(std::string(name)+".packet.bin"),std::ios::binary);
  std::array<char,8192> block{};DWORD count=0;
  while(ReadFile(reader,block.data(),static_cast<DWORD>(block.size()),&count,nullptr)&&count!=0)
    packet.write(block.data(),count);
  CloseHandle(reader);
}

} // namespace
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


int main(int argc,char **argv) {
  if(argc!=4)return 90;
  actor_id=static_cast<std::uint32_t>(std::stoul(argv[1]));
  recipient_id=static_cast<std::uint32_t>(std::stoul(argv[2]));
  const std::filesystem::path out=argv[3];std::filesystem::create_directories(out);
  Fixture fixture;RouterAdapter adapter;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};mailbox.offline_fixture=true;
  mailbox.permitted_executor_quattuortrigintary=&ExecuteFactionGiftPrivateMailbox12004;
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions=fixture.factions;bindings.gift=fixture.b;
  bindings.context=&fixture;bindings.read_campaign=&RootSource;bindings.read_alerts=&AlertSource;
  FactionGiftPrivateState12004 state;std::string wire,failure;
  const auto call=[&](std::string_view step,const std::string &payload,std::uint64_t revision,
                      std::string_view id="faction-gift-00000000000000000000000000000001") {
    std::ofstream(out/(std::string(step)+".request.json"))<<payload<<'\n';
    const bool handled=HandleFactionGiftPrivate12004(adapter,mailbox,adapter.snapshot,revision,
        step,payload,id,state,wire,failure,&bindings);
    if(handled)WriteWire(out,std::string(step)+".json",wire);
    else std::ofstream(out/(std::string(step)+".failure.txt"))<<failure<<'\n';
    return handled;
  };
  const bool preview=call(ck3_11906::kFactionGiftPrivateQueryStepV1,FramePayload(1)+"}",1);
  const std::string submit=FramePayload(1)+",\"source_faction_id\":"+std::to_string(source_id)+
      ",\"recipient_character_id\":"+std::to_string(recipient_id)+
      ",\"membership_role\":\"leader\",\"definition_stable_hash\":"+std::to_string(definition_hash)+
      ",\"gold_cost_raw\":7500000,\"opinion_delta\":35,\"minimum_gold_reserve_raw\":5000000,\"expected_native_revision\":1}";
  const bool submitted=preview&&call(ck3_11906::kFactionGiftPrivateSubmitStepV1,submit,1);
  const bool pending=state.pending_ack&&state.action_may_have_submitted;
  const int after_submit=queues;
  bool duplicate_rejected=false,receipt=false,cold=false,receipt_verified=false;
  if(pending){
    duplicate_rejected=!call(ck3_11906::kFactionGiftPrivateSubmitStepV1,submit,1);
    assert(queues==after_submit);
    Put(fixture.player_extension.data(),0x100,std::int64_t{12'500'000});
    gift_applied=true;Put(opinion_group.data(),0x14,std::int32_t{1});
    receipt=call(ck3_11906::kFactionGiftPrivateReceiptStepV1,FramePayload(2)+"}",2,
        "faction-gift-independent-receipt-00000000000000000001");
    receipt_verified=state.verified_receipt&&state.verified_receipt->postcondition_verified&&state.verified_receipt->mitigation_applied;
    state={};
    cold=call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,IdPayload(3),3);
  }
  std::ofstream(out/"SUMMARY.json")<<"{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"software_fixture\":true,\"mailbox_transport_substituted\":true,\"engine_callbacks_substituted\":true,"
    <<"\"actor_raw_bits\":"<<actor_id<<",\"recipient_raw_bits\":"<<recipient_id
    <<",\"preview_handled\":"<<(preview?"true":"false")<<",\"submit_handled\":"<<(submitted?"true":"false")
    <<",\"pending\":"<<(pending?"true":"false")<<",\"duplicate_rejected\":"<<(duplicate_rejected?"true":"false")
    <<",\"receipt_handled\":"<<(receipt?"true":"false")<<",\"cold_handled\":"<<(cold?"true":"false")
    <<",\"queue_calls\":"<<queues<<",\"clone_calls\":"<<clones<<",\"constructs\":"<<constructs<<",\"destroys\":"<<destroys<<"}\n";
  std::cout<<"preview="<<preview<<" submit="<<submitted<<" pending="<<pending<<" queues="<<queues<<" receipt="<<receipt<<" cold="<<cold<<'\n';
  CheckRouter(preview&&submitted&&pending&&duplicate_rejected&&receipt&&receipt_verified&&cold);
  CheckRouter(queues==1&&clones==1&&destroys==constructs+queues);
  return 0;
}
