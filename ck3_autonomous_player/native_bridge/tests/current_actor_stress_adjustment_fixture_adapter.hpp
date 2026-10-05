#pragma once
// Test-local adapter only; the production descriptor/profile predicates are linked unchanged.
using namespace xar::game;
class FixtureAdapter final : public xar::game::GameAdapter {
public:
  xar::game::Snapshot frame{};
  bool admitted=true;
  xar::game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion, xar::ck3_12003::kExecutableSha256, "offline", {}};
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable:4100)
#endif
  const AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return admitted; }
  bool read_snapshot(Snapshot &output) const noexcept override { output=frame; return admitted; }
  PauseSubmitResult submit_pause_map(Snapshot *observed_snapshot = nullptr) const noexcept override { return {}; }
  ResumeSubmitResult submit_resume_map(Snapshot *observed_snapshot = nullptr) const noexcept override { return {}; }
  bool submit_set_speed(std::int32_t speed) const noexcept override { return {}; }
  SelectEventOptionResult submit_select_event_option(std::int32_t option_index) const noexcept override { return {}; }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction( PendingInteractionReply reply) const noexcept override { return {}; }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override { return {}; }
  MoveArmyResult submit_move_army(std::int32_t army_id, std::int32_t province_id) const noexcept override { return {}; }
  PreviewMoveArmyResult preview_move_army(std::int32_t army_id, std::int32_t province_id) const noexcept override { return {}; }
  DisbandArmyResult submit_disband_army(std::int32_t army_id) const noexcept override { return {}; }
  SplitArmyHalfResult submit_split_army_half(std::int32_t army_id) const noexcept override { return {}; }
  MergeArmiesResult submit_merge_armies(std::int32_t destination_army_id, std::int32_t source_army_id) const noexcept override { return {}; }
  StartAssaultResult submit_start_assault(std::int32_t siege_id) const noexcept override { return {}; }
  StopAssaultResult submit_stop_assault(std::int32_t siege_id) const noexcept override { return {}; }
  bool read_declarable_wars( std::vector<DeclarableWarSnapshot> &output) const noexcept override { return {}; }
  ReadDeclarableWarsResult read_declarable_wars_for_target( std::int32_t target_character_id, std::vector<DeclarableWarSnapshot> &output) const noexcept override { return {}; }
  DeclareWarResult submit_declare_war(const DeclarableWarSnapshot &declaration) const noexcept override { return {}; }
  ReadArrangeMarriageChoicesResult read_arrange_marriage_choices( std::vector<ArrangeMarriageChoice> &output, ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override { return {}; }
  ArrangeMarriageResult submit_arrange_marriage(const ArrangeMarriageChoice &choice) const noexcept override { return {}; }
  EnforceDemandsResult submit_enforce_demands(std::int32_t war_id) const noexcept override { return {}; }
  ReadArmyStrengthsResult read_army_strengths( std::vector<ArmyStrengthSnapshot> &output) const noexcept override { return {}; }
  ReadCombatSimulationInputsResult read_combat_simulation_inputs( const CombatSimulationInputsRequest &request, CombatSimulationInputsSnapshot &output) const noexcept override { return {}; }
  ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3( const CombatSimulationInputsRequest &request, CombatSimulationInputsV3Snapshot &output) const noexcept override { return {}; }
  ReadWarTerminationOptionsResult read_war_termination_options( std::int32_t war_id, WarTerminationOptionsSnapshot &output) const noexcept override { return {}; }
  ReadWarTerminationTermsResult read_war_termination_terms( std::int32_t war_id, WarTerminationTermsSnapshot &output) const noexcept override { return {}; }
  ReadWarTerminationExitTermsResult read_war_termination_exit_terms( std::int32_t war_id, WarTerminationExitTermsSnapshot &output) const noexcept override { return {}; }
  SurrenderWarResult submit_surrender_war(std::int32_t war_id) const noexcept override { return {}; }
  OfferWhitePeaceResult submit_offer_white_peace(std::int32_t war_id) const noexcept override { return {}; }
#if defined(_MSC_VER)
#pragma warning(pop)
#endif
};
