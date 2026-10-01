// Compile the frozen source fixture helpers, without running its old matrix.
#define XAR_SWAY_INVALIDATION_REASON_FIXTURE_ENTRY ReasonPreviousFixtureMainNotExecuted
#include "ck3_12002_sway_completion_invalidation_reason_test.cpp"
#undef XAR_SWAY_INVALIDATION_REASON_FIXTURE_ENTRY

#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"

namespace {
namespace game = xar::game;
class ReasonFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-invalidation-reason", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    return true;
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

bool ExecuteReasonTransport(SwayCompletionInvalidationReasonMailboxContextV1 &query,
                            ReasonFrameAdapter &adapter,
                            xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
                            const InvalidationReasonFixture &fixture,
                            std::uint64_t after_sequence, std::uint64_t epoch) {
  using namespace xar::ck3_11906;
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.ticket.sequence = epoch;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 7;
  query.envelope.typed_context = &query;
  query.recorder = &fixture.recorder;
  query.request = fixture.Query(after_sequence);
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = epoch;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = &ExecuteSwayCompletionInvalidationReasonMailboxV1;
  mailbox.executor_context = &query.envelope;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = static_cast<std::int32_t>(adapter.frame.date_raw);
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1;
  stamp.jomini_state = 1;
  stamp.game_state = 1;
  return ExecuteSwayCompletionInvalidationReasonMailboxV1(&query.envelope, stamp) &&
         query.completed && query.envelope.frame_stable && query.failure.empty();
}

void SaveReasonCommand(const std::filesystem::path &output, const char *name,
                       const SwayCompletionInvalidationReasonMailboxContextV1 &query,
                       std::string_view request_id) {
  const auto wire = SerializeSwayCompletionInvalidationReasonCommandResultV1(
      query.result, query.envelope.expected_snapshot_revision,
      query.envelope.execution_stamp.date_raw, request_id);
  Check(!wire.empty(), "actual reason command_result formatter emits full wire");
  std::ofstream file(output / name);
  file << wire << '\n';
  Check(file.good(), "actual full reason command_result saved for SDK");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "reason transport artifact directory argument");
    const std::filesystem::path output{argv[1]};
    InvalidationReasonFixture fixture;
    // Only fixture-owned observation state; no CK3 wrapper installation.
    fixture.recorder.SetObserverAttached(true);
    ReasonFrameAdapter adapter;
    adapter.frame.date_raw = 53220000;
    adapter.frame.paused = true;
    adapter.frame.speed = 1;
    adapter.frame.player_id = 0;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = actor;
    adapter.frame.played_character_alive = true;
    xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;

    Check(fixture.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured,
          "actual stock direct-tooltip/global-command input captured as dead source");
    SwayCompletionInvalidationReasonMailboxContextV1 dead{};
    Check(ExecuteReasonTransport(dead, adapter, mailbox, fixture, 0, 81) &&
          dead.result.available && dead.result.records.size() == 1 &&
          dead.result.records[0].source.branch ==
              SwayInvalidationNotificationBranch12002::target_dead_notification_source &&
          dead.result.records[0].source.actor_character_id == actor &&
          dead.result.records[0].source.target_character_id == target &&
          dead.result.records[0].source.scheme_id == scheme,
          "owning reason mailbox joins actual Env32 overrides and inherited Script24 Scheme");
    SaveReasonCommand(output, "dead-command-result.json", dead, "reason-dead");

    *fixture.reason_key = "scheme_target_not_in_diplomatic_range";
    Put(fixture.child.data(), 0, base + 0x4931D10);
    Put(fixture.child.data(), 8, std::int32_t{9});
    Check(fixture.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured,
          "actual direct-description/global-command input captured as range source");
    SwayCompletionInvalidationReasonMailboxContextV1 range{};
    Check(ExecuteReasonTransport(range, adapter, mailbox, fixture, 1, 82) &&
          range.result.available && range.result.records.size() == 1 &&
          range.result.records[0].sequence == 2 &&
          range.result.records[0].source.branch ==
              SwayInvalidationNotificationBranch12002::out_of_range_notification_source &&
          range.result.records[0].source.scheme_id == scheme,
          "owner reason mailbox publishes only the actual selected range source after sequence");
    SaveReasonCommand(output, "range-command-result.json", range, "reason-range");

    // Preserve this existing authored notification as an opaque identity only.
    *fixture.reason_key = "sway_invalidated_war";
    Put(fixture.child.data(), 0, base + 0x4931918);
    Put(fixture.child.data(), 8, std::int32_t{8});
    Check(fixture.ExistingExecuteSink() == SwayInvalidationReasonCapture12002::captured,
          "existing authored direct-tooltip source copied opaquely");
    SwayCompletionInvalidationReasonMailboxContextV1 opaque{};
    Check(ExecuteReasonTransport(opaque, adapter, mailbox, fixture, 2, 83) &&
          opaque.result.available && opaque.result.records.size() == 1 &&
          opaque.result.records[0].sequence == 3 &&
          opaque.result.records[0].source.branch ==
              SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source &&
          opaque.result.records[0].source.scheme_id == scheme,
          "actual owner query retains opaque notification without inferred terminal reason");
    SaveReasonCommand(output, "opaque-command-result.json", opaque, "reason-opaque");
    Check(fixture.original_calls == 3 && global_getter_calls == 6 && native_lookup_calls == 9,
          "actual three source captures use distinct global command and native scope lookup ABIs");
    std::cout << "PASS " << checks << " checks; 3 actual owning reason mailbox command_result cases: "
                 "selected dead/range/opaque direct-child source, global command domain, "
                 "effective scope overlay/fallback; no CK3/named-queue/terminal claim\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
