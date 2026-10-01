#define XAR_SWAY_STATE_FIXTURE_NO_MAIN
#include "ck3_12002_sway_state_test.cpp"

namespace {
namespace game = xar::game;
class SwayFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway", {}};
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
bool ExecuteFixture(ActiveSwayMailboxContext12002 &q, SwayFrameAdapter &adapter,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox, StateFixture &fixture,
    std::uint64_t epoch) {
  using namespace xar::ck3_11906;
  q.envelope.game = &adapter; q.envelope.mailbox = &mailbox;
  q.envelope.ticket.sequence = epoch; q.envelope.expected_snapshot = adapter.frame;
  q.envelope.expected_snapshot_revision = 7; q.envelope.typed_context = &q;
  q.source = fixture.source; q.commands = fixture.command.bindings; q.target = target_id;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = epoch; mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = &ExecuteActiveSwayMailbox12002; mailbox.executor_context = &q.envelope;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch; stamp.thread_id = GetCurrentThreadId(); stamp.paused = true;
  stamp.date_raw = static_cast<std::int32_t>(adapter.frame.date_raw);
  stamp.tls_initialized = 1; stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1; stamp.jomini_state = 1; stamp.game_state = 1;
  return ExecuteActiveSwayMailbox12002(&q.envelope, stamp) && q.completed && q.envelope.frame_stable;
}
}
int main() {
  try {
    StateFixture fixture; can_send = true;
    SwayFrameAdapter adapter;
    adapter.frame.date_raw = 53220000; adapter.frame.paused = true; adapter.frame.speed = 1;
    adapter.frame.player_id = 0; adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true; adapter.frame.played_character_id = actor_id;
    adapter.frame.played_character_alive = true;
    xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;
    ActiveSwayMailboxContext12002 read{};
    Check(ExecuteFixture(read, adapter, mailbox, fixture, 40) && read.failure.empty() &&
        read.active.row_count == 0 && read.terms.complete_can_send && read.opinion == -15 &&
        !SerializeActiveSwayRead12002(read).empty(),
        "actual owner envelope source/terms query completed and stable");
    ActiveSwayMailboxContext12002 submit{};
    submit.formal = true; submit.action_id = "sway-mailbox-fixture";
    submit.expected_capture_epoch = 40; submit.expected_container_generation = read.active.container_generation;
    submit.expected_opinion = -15;
    Check(ExecuteFixture(submit, adapter, mailbox, fixture, 41) && submit.failure.empty() &&
        submit.ack.verification_pending && submit.ack.submit_call_count == 1 && queues == 1 &&
        !SerializeActiveSwayFormal12002(submit).empty(),
        "actual owner executor submits once and publishes pending ACK");
    ActiveSwayMailboxContext12002 missing{};
    missing.formal = true; missing.receipt_mode = true; missing.action_id = submit.action_id;
    missing.prior_ack = submit.ack;
    Check(ExecuteFixture(missing, adapter, mailbox, fixture, 42) && !missing.failure.empty() &&
        !missing.receipt.postcondition_verified && SerializeActiveSwayFormal12002(missing).empty(),
        "actual owner receipt cannot accept ACK without native instance");
    fixture.Add(1, 1);
    ActiveSwayMailboxContext12002 receipt{};
    receipt.formal = true; receipt.receipt_mode = true; receipt.action_id = submit.action_id;
    receipt.prior_ack = submit.ack;
    Check(ExecuteFixture(receipt, adapter, mailbox, fixture, 43) && receipt.failure.empty() &&
        receipt.receipt.postcondition_verified && receipt.receipt.scheme_instance_id == 1 &&
        !SerializeActiveSwayFormal12002(receipt).empty() && queues == 1,
        "actual owner fresh receipt independently sees new matching native instance");
    std::cout << "PASS actual Sway owning QueryMailboxEnvelope: read, once-only pending, missing-instance RED, fresh start receipt\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
