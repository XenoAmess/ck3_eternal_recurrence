#define main SwayTerminationPreviousFixtureMain
#include "ck3_12002_sway_completion_termination_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"

namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
class TerminationFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-termination", {}};
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
SwayTerminationQueryResult12002 ObserveCopied(TerminationFixture &fixture,
    TerminationFrameAdapter &adapter, std::uint64_t after, std::uint64_t epoch) {
  api::MainThreadQueryMailboxV1 mailbox;
  SwayCompletionTerminationMailboxContextV1 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.ticket.sequence = epoch; query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701; query.envelope.typed_context = &query;
  query.recorder = &fixture.recorder; query.request = fixture.Query(after);
  mailbox.state = api::MainThreadQueryMailboxStateV1::executing;
  mailbox.published_sequence = epoch; mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.executor = &ExecuteSwayCompletionTerminationMailboxV1;
  mailbox.executor_context = &query.envelope;
  api::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = epoch; stamp.thread_id = GetCurrentThreadId(); stamp.paused = true;
  stamp.date_raw = static_cast<std::int32_t>(adapter.frame.date_raw);
  stamp.tls_initialized = 1; stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1; stamp.jomini_state = 1; stamp.game_state = 1;
  Check(ExecuteSwayCompletionTerminationMailboxV1(&query.envelope, stamp) &&
      query.completed && query.failure.empty() && query.envelope.frame_stable,
      "actual termination owner envelope executes on one stable paused frame");
  return query.result;
}
void SaveFull(const std::filesystem::path &output, const char *filename,
    const SwayTerminationQueryResult12002 &result) {
  const auto wire = SerializeSwayCompletionTerminationCommandResultV1(
      result, 701, 53220000, std::string("fixture-termination-") + filename);
  std::ofstream file(output / filename); file << wire << '\n';
  Check(file.good(), "actual termination full-command wire saved");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "owning termination artifact directory");
    const std::filesystem::path output{argv[1]};
    TerminationFixture f; TerminationFrameAdapter adapter;
    adapter.frame.date_raw = 53220000; adapter.frame.paused = true; adapter.frame.speed = 1;
    adapter.frame.player_id = 0; adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true; adapter.frame.played_character_id = actor;
    adapter.frame.played_character_alive = true;
    Check(f.Install() && f.recorder.ObserverAttached(), "actual native fixture observer attached before capture");
    f.RunSource(1); // Installed entry copies Before, forwards typed original, captures After.
    Put(f.jomini.data(), 0x20, std::uint8_t{1});
    auto result = ObserveCopied(f, adapter, 0, 40);
    Check(result.available && result.records.size() == 1 &&
        result.records[0].source.source_class == SwayTerminationSourceClass12002::authored_end_scheme_false_execute &&
        result.records[0].source.executing_source_observed &&
        result.records[0].source.native_terminal_transition_observed &&
        result.records[0].source.scheme_id == scheme &&
        result.records[0].source.actor_character_id == actor &&
        result.records[0].source.target_character_id == target &&
        result.records[0].source.post_owner == 0xFFFFFFFFu,
        "native copied full identities and independently observed transition survive input token destruction");
    SaveFull(output, "terminal-transition-wire.json", result);
    f.Reset(); f.post = FixturePost::unchanged; Put(f.jomini.data(), 0x20, std::uint8_t{0});
    f.RunSource(2); Put(f.jomini.data(), 0x20, std::uint8_t{1});
    result = ObserveCopied(f, adapter, 1, 41);
    Check(result.available && result.records.size() == 1 &&
        result.records[0].source.source_class == SwayTerminationSourceClass12002::authored_end_scheme_true_execute &&
        result.records[0].source.executing_source_observed && result.records[0].source.post_status_observed &&
        result.records[0].source.post_status == 0 &&
        !result.records[0].source.native_terminal_state_observed &&
        !result.records[0].source.native_terminal_transition_observed,
        "observed end-source execution is not a terminal result when original leaves native row unchanged");
    SaveFull(output, "original-no-terminal-wire.json", result);
    f.Reset(); f.post = FixturePost::purge; Put(f.jomini.data(), 0x20, std::uint8_t{0});
    f.RunSource(0); Put(f.jomini.data(), 0x20, std::uint8_t{1});
    result = ObserveCopied(f, adapter, 2, 42);
    Check(result.available && result.records.size() == 1 &&
        result.records[0].source.source_class == SwayTerminationSourceClass12002::end_scheme_command_execute &&
        result.records[0].source.executing_source_observed && result.records[0].source.post_read_succeeded &&
        !result.records[0].source.post_instance_present && !result.records[0].source.post_status_observed &&
        !result.records[0].source.native_terminal_state_observed &&
        !result.records[0].source.native_terminal_transition_observed,
        "post absence after original preserves copied source and does not invent a terminal state");
    SaveFull(output, "absent-post-wire.json", result);
    Check(f.original_calls == std::array<std::size_t, 3>{1, 1, 1} && f.original_arguments_match,
        "each of three typed originals forwarded exactly once with unchanged used inputs");
    std::cout << "PASS native 3 installed Execute inputs -> actual typed originals -> copied pre/post recorder -> "
                 "owning mailbox -> full formatter: terminal transition, unchanged original, absent post\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
