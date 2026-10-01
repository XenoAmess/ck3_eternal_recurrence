// Reuse the complete existing memory fixture, and execute only this new
// independent material provider -> actual full mailbox serializer path.
#define XAR_SWAY_OUTCOME_FIXTURE_REUSE
#include "ck3_12002_sway_outcome_test.cpp"
#include "xar_bridge/ck3_12002_sway_outcome_mailbox.hpp"

namespace {
namespace game = xar::game;
class OutcomeFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        xar::ck3_12002::kExecutableSha256, "offline-outcome-opinion", {}};
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

bool ReadOnOwningExecutor(SwayFixture &fixture,
                         xar::ck3_12002::SwayOutcomeOpinionV1 &output) {
  using namespace xar::ck3_12002;
  using namespace xar::ck3_11906;
  OutcomeFrameAdapter adapter;
  adapter.frame.paused = true;
  adapter.frame.map_ready = true;
  adapter.frame.has_played_character = true;
  adapter.frame.played_character_alive = true;
  adapter.frame.played_character_id = kCharacterId;
  adapter.frame.date_raw = 741221;
  MainThreadQueryMailboxV1 mailbox{};
  SwayOutcomeMailboxContextV1 query{};
  query.opinion_only = true;
  query.bindings = fixture.outcome_bindings;
  query.request.expected_revision = kRevision;
  query.request.actor_character_id = kCharacterId;
  query.request.target_character_id = kSwayTarget;
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = kRevision;
  query.envelope.typed_context = &query;
  // Admission uses only the newly named fixed callback permit. All generic
  // and other named callback fields remain null in the fresh mailbox.
  mailbox.state = MainThreadQueryMailboxStateV1::idle;
  mailbox.executor_submission_enabled = true;
  mailbox.permitted_executor_sway_outcome_opinion12002 = &ExecuteSwayOutcomeMailboxV1;
  mailbox.owner_thread_id = GetCurrentThreadId();
  mailbox.paused_owner_verified_pump_epochs =
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
  if (mailbox.permitted_executor != nullptr ||
      TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayOutcomeMailboxV1,
                                &query.envelope, query.envelope.ticket) !=
          MainThreadQuerySubmitResultV1::submitted)
    return false;
  mailbox.state = MainThreadQueryMailboxStateV1::executing;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 1;
  stamp.thread_id = GetCurrentThreadId();
  stamp.date_raw = 741221;
  stamp.paused = true;
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 1;
  stamp.jomini_state = 1;
  stamp.game_state = 1;
  if (!ExecuteSwayOutcomeMailboxV1(&query.envelope, stamp) ||
      !query.completed || !query.failure.empty() ||
      !query.envelope.entered || !query.envelope.frame_stable)
    return false;
  output = query.opinion_result;
  return true;
}
} // namespace

int main() {
  using namespace xar::ck3_12002;
  SwayFixture fixture;
  // This query must remain useful after the visible event has been consumed.
  g_active_event = nullptr;
  g_opinion_calls = 0;
  g_opinion = 37;
  g_sway_modifier_value = 0;
  SwayOutcomeOpinionV1 row{};
  if (!ReadOnOwningExecutor(fixture, row) ||
      !row.available || row.target_opinion_of_actor != 37 ||
      !row.scheme_sway_opinion.observed || !row.scheme_sway_opinion.present ||
      row.scheme_sway_opinion.value != 0 ||
      !row.sway_blocker_opinion.observed || row.sway_blocker_opinion.present ||
      row.sway_blocker_opinion.value) return 1;
  std::cout << SerializeSwayOutcomeOpinionResponseV1(
      row, kRevision, 741221, "fixture-opinion-present") << '\n';
  Store<std::int32_t>(fixture.opinion_group.data(), 0x14, 0);
  g_opinion_calls = 0;
  if (!ReadOnOwningExecutor(fixture, row) ||
      !row.scheme_sway_opinion.observed || row.scheme_sway_opinion.present ||
      row.scheme_sway_opinion.value || !row.sway_blocker_opinion.observed ||
      row.sway_blocker_opinion.present || row.sway_blocker_opinion.value)
    return 1;
  std::cout << SerializeSwayOutcomeOpinionResponseV1(
      row, kRevision, 741221, "fixture-opinion-absent") << '\n';
  return 0;
}
