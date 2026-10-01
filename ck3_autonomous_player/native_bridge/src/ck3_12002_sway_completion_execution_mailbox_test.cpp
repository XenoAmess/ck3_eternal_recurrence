// Reuse the frozen actual-memory Execute fixture without rerunning its suite.
#define main SwayExecutionInputFixtureMainUnused
#include "ck3_12002_sway_completion_execution_test.cpp"
#undef main

#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"

namespace {
namespace game = xar::game;
class ExecutionFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-execution", {}};
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

bool ExecuteTransport(SwayCompletionExecutionMailboxContextV1 &query,
                      ExecutionFrameAdapter &adapter,
                      xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
                      const SwayExecutionRecorder12002 &recorder,
                      const SwayExecutionQuery12002 &request,
                      std::uint64_t epoch) {
  using namespace xar::ck3_11906;
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.ticket.sequence = epoch;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 7;
  query.envelope.typed_context = &query;
  query.recorder = &recorder;
  query.request = request;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = epoch;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = &ExecuteSwayCompletionExecutionMailboxV1;
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
  return ExecuteSwayCompletionExecutionMailboxV1(&query.envelope, stamp) &&
         query.completed && query.envelope.frame_stable && query.failure.empty();
}

void SaveCommand(const std::filesystem::path &directory, const char *name,
                 const SwayCompletionExecutionMailboxContextV1 &query,
                 std::string_view request_id) {
  const auto wire = SerializeSwayCompletionExecutionCommandResultV1(
      query.result, query.envelope.expected_snapshot_revision,
      query.envelope.execution_stamp.date_raw, request_id);
  Check(!wire.empty(), "full production command_result formatter emits wire");
  std::ofstream output(directory / name);
  output << wire << '\n';
  Check(output.good(), "full command_result saved for SDK fixture consumption");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "transport artifact directory argument");
    const std::filesystem::path output{argv[1]};
    Fixture native;
    SwayExecutionRecorder12002 recorder;
    ExecutionFrameAdapter adapter;
    adapter.frame.date_raw = date_raw;
    adapter.frame.paused = true;
    adapter.frame.speed = 1;
    adapter.frame.player_id = 0;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = actor_id;
    adapter.frame.played_character_alive = true;
    xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;

    SwayCompletionExecutionMailboxContextV1 unattached{};
    Check(ExecuteTransport(unattached, adapter, mailbox, recorder, Request(), 71) &&
          !unattached.result.available && !unattached.result.observer_attached &&
          unattached.result.unavailable_reason == "sway_execution_observer_not_attached" &&
          unattached.result.records.empty(),
          "unattached actual recorder passes owning mailbox and reports unavailable");
    SaveCommand(output, "not-attached-command-result.json", unattached, "execution-unattached");

    // Attachment is a fixture input; root owns the real native entry installer.
    recorder.SetObserverAttached(true);
    Check(native.Record(recorder) == SwayExecutionCaptureResult12002::captured,
          "actual Execute memory capture appends hidden good source input");
    SwayCompletionExecutionMailboxContextV1 matched{};
    Check(ExecuteTransport(matched, adapter, mailbox, recorder, Request(), 72) &&
          matched.result.available && matched.result.observer_attached &&
          matched.result.records.size() == 1 &&
          matched.result.records[0].sequence == 1 &&
          matched.result.records[0].source.date_raw == date_raw &&
          matched.result.records[0].source.actor_character_id == actor_id &&
          matched.result.records[0].source.target_character_id == target_id &&
          matched.result.records[0].source.scheme_id == scheme_id &&
          matched.result.records[0].source.branch ==
              SwayExecutionSourceBranch12002::hidden_phase_success_source,
          "owning mailbox query joins the copied actual good source by all full IDs");
    SaveCommand(output, "hidden-good-command-result.json", matched, "execution-hidden-good");

    auto wrong_generation = Request();
    wrong_generation.scheme_id = 0x0200000Bu;
    SwayCompletionExecutionMailboxContextV1 filtered{};
    Check(ExecuteTransport(filtered, adapter, mailbox, recorder, wrong_generation, 73) &&
          filtered.result.available && filtered.result.observer_attached &&
          filtered.result.records.empty() && filtered.result.latest_sequence == 1,
          "same scheme slot with a different full generation yields legal empty history");
    SaveCommand(output, "wrong-generation-command-result.json", filtered, "execution-wrong-generation");

    std::cout << "PASS " << checks << " checks; 3 actual owning mailbox command_result cases: "
                 "not-attached, captured hidden good full-ID join, wrong-generation empty; "
                 "no real observer installation or material/terminal claim\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
