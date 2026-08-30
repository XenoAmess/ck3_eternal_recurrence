#include "xar_bridge/ck3_11906_adapter.hpp"

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/title_map_navigation_v1.hpp"

#include <array>
#include <memory>

namespace xar::game {
namespace {

constexpr std::array<std::string_view, 65> kCapabilities{
    "game.state.snapshot",
    "game.state.xar-one-life-settlement",
    "game.state.map-ready",
    "game.state.played-character",
    "game.state.active-event",
    "game.state.pending-character-interaction",
    "game.state.active-wars",
    "game.state.war-primary-opponent",
    "game.state.war-objectives",
    "game.state.war-objective-occupation",
    "game.state.war-objective-fort-level",
    "game.state.war-objective-garrison",
    "game.state.war-objective-siege-progress",
    "game.state.war-objective-assault",
    "game.state.player-armies",
    "game.state.army-routes",
    "game.command.pause-map",
    "game.command.resume-map",
    "game.command.set-speed-1",
    "game.command.set-speed-2",
    "game.command.set-speed-3",
    "game.command.set-speed-4",
    "game.command.set-speed-5",
    "game.command.research-arm-tactical-daily-sentinel-v1-N",
    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
    "game.command.research-query-tactical-daily-sentinel-v1",
    "game.command.select-event-option-N",
    "game.command.save-checkpoint",
    "game.command.accept-pending-character-interaction",
    "game.command.reject-pending-character-interaction",
    "game.command.acknowledge-pending-character-interaction",
    "game.command.raise-troops-default",
    "game.command.preview-move-army-N-to-N",
    "game.command.query-route-contact-horizon-v1-N",
    "game.command.query-actual-contact-scope-v1-N",
    "game.command.query-battle-control-snapshot-v1-N",
    "game.command.query-battle-transition-v1-N",
    "game.command.query-battle-terminal-transition-v1",
    "game.command.query-battle-reinforcement-assignment-v1-N",
    "game.command.move-army-N-to-N",
    "game.command.disband-army-N",
    "game.command.split-army-half-N",
    "game.command.merge-armies-N-with-N",
    "game.command.start-assault-N",
    "game.command.stop-assault-N",
    "game.command.query-declarable-wars",
    "game.command.query-war-entry-assessments-v1-N",
    "game.command.declare-war-N",
    "game.command.enforce-demands-N",
    "game.command.query-army-strengths-v1",
    "game.command.query-campaign-root-context-v1",
    "game.command.query-loaded-feature-manifest-v1",
    "game.command.query-pending-character-interaction-context-v1",
    "game.command.query-current-event-window-context-v1",
    ck3_11906::kTitleMapNavigationV1Capability,
    "game.command.query-combat-simulation-inputs-v2-N",
    "game.command.query-combat-simulation-inputs-v3-N",
    "game.command.query-war-termination-options-N",
    "game.command.query-war-termination-terms-v1-N",
    "game.command.surrender-war-N",
    "game.command.offer-white-peace-N",
    "game.command.query-arrange-marriage-choices",
    "game.command.arrange-marriage-N",
    "game.adapter.exact-build",
    "game.adapter.minimized-headless",
};

const AdapterDescriptor kDescriptor{
    "ck3-1.19.0.6-msvc-x64",
    "1.19.0.6",
    ck3_11906::kExecutableSha256,
    ck3_11906::kCheckpointSaveName,
    kCapabilities,
};

class Ck3_11906Adapter final : public GameAdapter {
public:
  explicit Ck3_11906Adapter(ck3_11906::Bindings bindings) noexcept
      : bindings_(bindings) {}

  const AdapterDescriptor &descriptor() const noexcept override {
    return kDescriptor;
  }
  bool enabled() const noexcept override { return bindings_.enabled; }
  bool read_snapshot(Snapshot &output) const noexcept override {
    return ck3_11906::ReadSnapshot(bindings_, output);
  }
  PauseSubmitResult submit_pause_map() const noexcept override {
    return ck3_11906::SubmitPauseMap(bindings_);
  }
  ResumeSubmitResult submit_resume_map() const noexcept override {
    return ck3_11906::SubmitResumeMap(bindings_);
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    return ck3_11906::SubmitSetSpeed(bindings_, speed);
  }
  SelectEventOptionResult
  submit_select_event_option(std::int32_t option_index) const noexcept override {
    return ck3_11906::SubmitSelectEventOption(bindings_, option_index);
  }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    return ck3_11906::SubmitSaveCheckpoint(bindings_);
  }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction(
      PendingInteractionReply reply) const noexcept override {
    return ck3_11906::SubmitReplyToPendingInteraction(bindings_, reply);
  }
  AcknowledgePendingInteractionResult
  submit_acknowledge_pending_interaction(
      std::int32_t pending_interaction_id) const noexcept override {
    return ck3_11906::SubmitAcknowledgePendingInteraction(
        bindings_, pending_interaction_id);
  }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override {
    return ck3_11906::SubmitRaiseTroopsDefault(bindings_);
  }
  MoveArmyResult submit_move_army(std::int32_t army_id,
                                  std::int32_t province_id) const
      noexcept override {
    return ck3_11906::SubmitMoveArmy(bindings_, army_id, province_id);
  }
  PreviewMoveArmyResult
  preview_move_army(std::int32_t army_id,
                    std::int32_t province_id) const noexcept override {
    return ck3_11906::PreviewMoveArmy(bindings_, army_id, province_id);
  }
  DisbandArmyResult
  submit_disband_army(std::int32_t army_id) const noexcept override {
    return ck3_11906::SubmitDisbandArmy(bindings_, army_id);
  }
  SplitArmyHalfResult
  submit_split_army_half(std::int32_t army_id) const noexcept override {
    return ck3_11906::SubmitSplitArmyHalf(bindings_, army_id);
  }
  MergeArmiesResult submit_merge_armies(
      std::int32_t destination_army_id,
      std::int32_t source_army_id) const noexcept override {
    return ck3_11906::SubmitMergeArmies(bindings_, destination_army_id,
                                        source_army_id);
  }
  StartAssaultResult
  submit_start_assault(std::int32_t siege_id) const noexcept override {
    return ck3_11906::SubmitStartAssault(bindings_, siege_id);
  }
  StopAssaultResult
  submit_stop_assault(std::int32_t siege_id) const noexcept override {
    return ck3_11906::SubmitStopAssault(bindings_, siege_id);
  }
  bool read_declarable_wars(
      std::vector<DeclarableWarSnapshot> &output) const noexcept override {
    return ck3_11906::ReadDeclarableWars(bindings_, output);
  }
  ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_character_id,
      std::vector<DeclarableWarSnapshot> &output) const noexcept override {
    return ck3_11906::ReadDeclarableWarsForTarget(
        bindings_, target_character_id, output);
  }
  DeclareWarResult submit_declare_war(
      const DeclarableWarSnapshot &declaration) const noexcept override {
    return ck3_11906::SubmitDeclareWar(bindings_, declaration);
  }
  ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<ArrangeMarriageChoice> &output,
      ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    return ck3_11906::ReadArrangeMarriageChoices(bindings_, output,
                                                  diagnostics);
  }
  ArrangeMarriageResult submit_arrange_marriage(
      const ArrangeMarriageChoice &choice) const noexcept override {
    return ck3_11906::SubmitArrangeMarriage(bindings_, choice);
  }
  EnforceDemandsResult
  submit_enforce_demands(std::int32_t war_id) const noexcept override {
    return ck3_11906::SubmitEnforceDemands(bindings_, war_id);
  }
  ReadArmyStrengthsResult read_army_strengths(
      std::vector<ArmyStrengthSnapshot> &output) const noexcept override {
    return ck3_11906::ReadArmyStrengths(bindings_, output);
  }
  ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsSnapshot &output) const noexcept override {
    return ck3_11906::ReadCombatSimulationInputs(bindings_, request, output);
  }
  ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsV3Snapshot &output) const noexcept override {
    return ck3_11906::ReadCombatSimulationInputsV3(bindings_, request, output);
  }
  ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id,
      WarTerminationOptionsSnapshot &output) const noexcept override {
    return ck3_11906::ReadWarTerminationOptions(bindings_, war_id, output);
  }
  ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t war_id,
      WarTerminationTermsSnapshot &output) const noexcept override {
    return ck3_11906::ReadWarTerminationTerms(bindings_, war_id, output);
  }
  ReadWarTerminationExitTermsResult read_war_termination_exit_terms(
      std::int32_t war_id,
      WarTerminationExitTermsSnapshot &output) const noexcept override {
    return ck3_11906::ReadWarTerminationExitTerms(bindings_, war_id, output);
  }
  std::string_view last_war_termination_exit_terms_unavailable_reason()
      const noexcept override {
    return ck3_11906::LastWarTerminationExitTermsUnavailableReason();
  }
  SurrenderWarResult
  submit_surrender_war(std::int32_t war_id) const noexcept override {
    return ck3_11906::SubmitSurrenderWar(bindings_, war_id);
  }
  OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t war_id) const noexcept override {
    return ck3_11906::SubmitOfferWhitePeace(bindings_, war_id);
  }

private:
  ck3_11906::Bindings bindings_;
};

} // namespace

const AdapterDescriptor &Ck3_11906AdapterDescriptor() noexcept {
  return kDescriptor;
}

std::unique_ptr<GameAdapter>
CreateCk3_11906Adapter(std::string_view executable_sha256) noexcept {
  return std::make_unique<Ck3_11906Adapter>(
      ck3_11906::BindCurrentProcess(
          executable_sha256 == kDescriptor.executable_sha256));
}

} // namespace xar::game
