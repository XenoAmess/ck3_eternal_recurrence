#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include <mutex>
#include <optional>

namespace xar::ck3_12002 {

// The bridge worker reads a published owner-thread snapshot and submits only
// these fixed semantic operations to the same proven application-main actor.
class WorkerAdapter final : public game::GameAdapter {
public:
  WorkerAdapter(const game::GameAdapter &native_adapter,
                ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept;
  const game::GameAdapter &native_adapter() const noexcept;
  const game::AdapterDescriptor &descriptor() const noexcept override;
  bool enabled() const noexcept override;
  bool read_snapshot(game::Snapshot &) const noexcept override;
  game::PauseSubmitResult submit_pause_map() const noexcept override;
  game::ResumeSubmitResult submit_resume_map() const noexcept override;
  bool submit_set_speed(std::int32_t) const noexcept override;
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override;
  game::SelectEventOptionResult submit_select_event_option(std::int32_t option_index) const noexcept override;
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply reply) const noexcept override;
  game::AcknowledgePendingInteractionResult submit_acknowledge_pending_interaction(std::int32_t pending_id) const noexcept override;
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override;
  game::MoveArmyResult submit_move_army(std::int32_t army_id, std::int32_t province_id) const noexcept override;
  game::DisbandArmyResult submit_disband_army(std::int32_t army_id) const noexcept override;
  game::SplitArmyHalfResult submit_split_army_half(std::int32_t army_id) const noexcept override;
  game::MergeArmiesResult submit_merge_armies(std::int32_t destination, std::int32_t source) const noexcept override;
  game::StartAssaultResult submit_start_assault(std::int32_t siege_id) const noexcept override;
  game::StopAssaultResult submit_stop_assault(std::int32_t siege_id) const noexcept override;
  game::DeclareWarResult submit_declare_war(const game::DeclarableWarSnapshot &declaration) const noexcept override;
  game::ArrangeMarriageResult submit_arrange_marriage(const game::ArrangeMarriageChoice &choice) const noexcept override;
  game::EnforceDemandsResult submit_enforce_demands(std::int32_t war_id) const noexcept override;
  game::SurrenderWarResult submit_surrender_war(std::int32_t war_id) const noexcept override;
  game::OfferWhitePeaceResult submit_offer_white_peace(std::int32_t war_id) const noexcept override;
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override;
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override;
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &) const noexcept override;
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &) const noexcept override;
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &) const noexcept override;
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(
      const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &) const noexcept override;
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t, game::WarTerminationOptionsSnapshot &) const noexcept override;
  game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t, game::WarTerminationTermsSnapshot &) const noexcept override;
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(
      std::int32_t, game::WarTerminationExitTermsSnapshot &) const noexcept override;
  bool Observe(const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

private:
  struct SemanticRequest;
  bool Run(SemanticRequest &) const noexcept;
  const game::GameAdapter *native_ = nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox_ = nullptr;
  mutable std::mutex snapshot_mutex_;
  std::optional<game::Snapshot> snapshot_;
  std::uint64_t snapshot_epoch_ = 0;
  std::uint64_t snapshot_revision_ = 0;
  std::uint64_t next_snapshot_sample_ms_ = 0;
  friend bool ExecuteSemanticAdapter12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
};

bool ExecuteSemanticAdapter12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool ObserveAdapterSnapshot12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &) noexcept;

} // namespace xar::ck3_12002
