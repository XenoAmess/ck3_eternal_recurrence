#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_console_fixture.hpp"
#include "xar_bridge/verified_owner_wake_v1.hpp"
#include <atomic>
#include <mutex>
#include <optional>

namespace xar::ck3_12002 {

struct SnapshotObserverDiagnostics12002 {
  std::uint64_t started_ms = 0;
  std::uint64_t completed_ms = 0;
  std::uint64_t last_read_ms = 0;
  bool last_read_available = false;
  bool snapshot_cached = false;
};

// The bridge worker reads a published owner-thread snapshot and submits only
// these fixed semantic operations to the same proven application-main actor.
class WorkerAdapter final : public game::GameAdapter {
public:
  WorkerAdapter(const game::GameAdapter &native_adapter,
                ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept;
  WorkerAdapter(const game::GameAdapter &native_adapter,
                ck3_11906::MainThreadQueryMailboxV1 &mailbox,
                const ConsoleFixtureBindings &console_fixture) noexcept;
  const game::GameAdapter &native_adapter() const noexcept;
  const game::AdapterDescriptor &descriptor() const noexcept override;
  bool enabled() const noexcept override;
  bool read_snapshot(game::Snapshot &) const noexcept override;
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override;
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override;
  bool submit_set_speed(std::int32_t) const noexcept override;
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override;
  game::SelectEventOptionResult submit_select_event_option(std::int32_t option_index) const noexcept override;
  game::ReplyPendingInteractionResult submit_reply_to_pending_interaction(game::PendingInteractionReply reply) const noexcept override;
  game::AcknowledgePendingInteractionResult submit_acknowledge_pending_interaction(std::int32_t pending_id) const noexcept override;
  game::RaiseTroopsResult submit_raise_troops_default() const noexcept override;
  game::MoveArmyResult submit_move_army(std::int32_t army_id, std::int32_t province_id) const noexcept override;
  game::HaltArmyResult submit_halt_army(std::int32_t army_id) const noexcept override;
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
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_character_id,
      std::vector<game::DeclarableWarSnapshot> &) const noexcept override;
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &) const noexcept override;
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_character_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &,
      game::ArrangeMarriageQueryDiagnostics &) const noexcept override;
  game::ReadArmyStrengthsResult read_army_strengths(std::vector<game::ArmyStrengthSnapshot> &) const noexcept override;
  game::ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &) const noexcept override;
  game::ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(
      const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &) const noexcept override;
  game::ReadTitleHolderV1Result read_title_holder_v1(
      std::int32_t, game::TitleHolderV1 &) const noexcept override;
  game::ReadWarOccupationTargetsV1Result read_war_occupation_targets_v1(
      std::int32_t, game::WarOccupationTargetsV1 &) const noexcept override;
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t, game::WarTerminationOptionsSnapshot &) const noexcept override;
  game::ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t, game::WarTerminationTermsSnapshot &) const noexcept override;
  game::ReadWarTerminationExitTermsResult read_war_termination_exit_terms(
      std::int32_t, game::WarTerminationExitTermsSnapshot &) const noexcept override;
  bool Observe(const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
  SnapshotObserverDiagnostics12002 snapshot_observer_diagnostics() const noexcept;
  ck3_11906::VerifiedOwnerWakeDiagnosticsV1 owner_wake_diagnostics() const noexcept;
  bool read_marriage_diagnostic(std::string &) const noexcept;
  // Private fixed fixture step; no command or inbox path can be supplied.
  bool run_inbox_fixture(std::string &) const noexcept;

private:
  struct SemanticRequest;
  bool Run(SemanticRequest &) const noexcept;
  void WakeAfterDirectControlSubmit() const noexcept;
  mutable ck3_11906::VerifiedOwnerWakeCountersV1 owner_wake_counters_{};
  const game::GameAdapter *native_ = nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox_ = nullptr;
  ConsoleFixtureBindings console_fixture_{};
  mutable std::mutex snapshot_mutex_;
  std::optional<game::Snapshot> snapshot_;
  std::uint64_t snapshot_epoch_ = 0;
  std::uint64_t snapshot_revision_ = 0;
  std::uint64_t next_snapshot_sample_ms_ = 0;
  std::atomic<std::uint64_t> observer_started_ms_{0};
  std::atomic<std::uint64_t> observer_completed_ms_{0};
  std::atomic<std::uint64_t> observer_last_read_ms_{0};
  std::atomic<bool> observer_last_read_available_{false};
  friend bool ExecuteSemanticAdapter12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
};

bool ExecuteSemanticAdapter12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool ObserveAdapterSnapshot12002(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &) noexcept;

} // namespace xar::ck3_12002
