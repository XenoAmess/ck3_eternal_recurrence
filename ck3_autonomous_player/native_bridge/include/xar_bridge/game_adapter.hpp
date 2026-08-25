#pragma once

#include "xar_bridge/combat_v3.hpp"

#include <cstdint>
#include <memory>
#include <span>
#include <string_view>
#include <vector>

namespace xar::game {

struct AdapterDescriptor {
  std::string_view adapter_id;
  std::string_view game_version;
  std::string_view executable_sha256;
  std::string_view checkpoint_save_name;
  std::span<const std::string_view> capabilities;
};

// Strict v2 hypothetical-contact literal grammar:
// query-combat-simulation-inputs-v2-<target>-<entry>-a-<Acount>-<A...>
// -d-<Dcount>-<D...>. Counts are exact, each side is non-empty, and all
// public full-generation ArmyIDs are distinct across both partitions.
bool ParseCombatSimulationInputsStep(
    std::string_view step, CombatSimulationInputsRequest &request) noexcept;

// Strict production v3 grammar. It deliberately shares the canonical request
// body with v2 while selecting the atomic phase-event observation contract.
bool ParseCombatSimulationInputsV3Step(
    std::string_view step, CombatSimulationInputsRequest &request) noexcept;

// Stable semantic API implemented by one exact-build CK3 adapter. ABI details
// are private to the implementation selected by the registry.
class GameAdapter {
public:
  virtual ~GameAdapter() = default;

  [[nodiscard]] virtual const AdapterDescriptor &descriptor() const noexcept = 0;
  [[nodiscard]] virtual bool enabled() const noexcept = 0;
  [[nodiscard]] bool supports(std::string_view capability) const noexcept;
  [[nodiscard]] bool supports_snapshot() const noexcept;
  [[nodiscard]] bool supports_step(std::string_view step) const noexcept;

  virtual bool read_snapshot(Snapshot &output) const noexcept = 0;
  virtual PauseSubmitResult submit_pause_map() const noexcept = 0;
  virtual ResumeSubmitResult submit_resume_map() const noexcept = 0;
  virtual bool submit_set_speed(std::int32_t speed) const noexcept = 0;
  virtual SelectEventOptionResult
  submit_select_event_option(std::int32_t option_index) const noexcept = 0;
  virtual SaveCheckpointResult submit_save_checkpoint() const noexcept = 0;
  virtual ReplyPendingInteractionResult submit_reply_to_pending_interaction(
      PendingInteractionReply reply) const noexcept = 0;
  virtual RaiseTroopsResult submit_raise_troops_default() const noexcept = 0;
  virtual MoveArmyResult submit_move_army(std::int32_t army_id,
                                          std::int32_t province_id) const
      noexcept = 0;
  virtual PreviewMoveArmyResult
  preview_move_army(std::int32_t army_id,
                    std::int32_t province_id) const noexcept = 0;
  virtual DisbandArmyResult submit_disband_army(std::int32_t army_id) const
      noexcept = 0;
  virtual SplitArmyHalfResult
  submit_split_army_half(std::int32_t army_id) const noexcept = 0;
  virtual MergeArmiesResult
  submit_merge_armies(std::int32_t destination_army_id,
                      std::int32_t source_army_id) const noexcept = 0;
  virtual StartAssaultResult
  submit_start_assault(std::int32_t siege_id) const noexcept = 0;
  virtual StopAssaultResult
  submit_stop_assault(std::int32_t siege_id) const noexcept = 0;
  virtual bool read_declarable_wars(
      std::vector<DeclarableWarSnapshot> &output) const noexcept = 0;
  virtual DeclareWarResult
  submit_declare_war(const DeclarableWarSnapshot &declaration) const
      noexcept = 0;
  virtual ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<ArrangeMarriageChoice> &output,
      ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept = 0;
  virtual ArrangeMarriageResult
  submit_arrange_marriage(const ArrangeMarriageChoice &choice) const
      noexcept = 0;
  virtual EnforceDemandsResult
  submit_enforce_demands(std::int32_t war_id) const noexcept = 0;
  virtual ReadArmyStrengthsResult read_army_strengths(
      std::vector<ArmyStrengthSnapshot> &output) const noexcept = 0;
  virtual ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsSnapshot &output) const noexcept = 0;
  virtual ReadCombatSimulationInputsV3Result
  read_combat_simulation_inputs_v3(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsV3Snapshot &output) const noexcept = 0;
  virtual ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id,
      WarTerminationOptionsSnapshot &output) const noexcept = 0;
  virtual ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t war_id,
      WarTerminationTermsSnapshot &output) const noexcept = 0;
  virtual ReadWarTerminationExitTermsResult
  read_war_termination_exit_terms(
      std::int32_t war_id,
      WarTerminationExitTermsSnapshot &output) const noexcept = 0;
  // Error-only diagnostic for the immediately preceding exit-terms read on
  // this bridge thread.  It never exposes a partial terms payload and is not
  // part of the versioned wire contract.
  [[nodiscard]] virtual std::string_view
  last_war_termination_exit_terms_unavailable_reason() const noexcept {
    return {};
  }
  virtual SurrenderWarResult
  submit_surrender_war(std::int32_t war_id) const noexcept = 0;
  virtual OfferWhitePeaceResult
  submit_offer_white_peace(std::int32_t war_id) const noexcept = 0;
};

using AdapterFactory = std::unique_ptr<GameAdapter> (*)(
    std::string_view executable_sha256) noexcept;

// Deterministic registry primitive: returns the first enabled adapter, or the
// first disabled adapter as the preferred diagnostic descriptor when none of
// the exact builds match. An empty factory set returns nullptr.
std::unique_ptr<GameAdapter>
SelectAdapter(std::string_view executable_sha256,
              std::span<const AdapterFactory> factories) noexcept;

// The registry tries known exact-build adapters and returns the matching one.
// With no match it returns a disabled adapter so the transport can continue to
// provide identity/heartbeat/ping without advertising gameplay capabilities.
std::unique_ptr<GameAdapter> SelectCurrentProcessAdapter() noexcept;

// Metadata for the preferred known adapter, used by the pre-session exported
// identity. It comes from the same descriptor as session hello metadata.
const AdapterDescriptor &PreferredAdapterDescriptor() noexcept;

// Compatibility wrappers keep bridge dispatch compact while all calls still
// cross the version-neutral GameAdapter boundary.
inline bool ReadSnapshot(const GameAdapter &game, Snapshot &output) noexcept {
  return game.read_snapshot(output);
}
inline PauseSubmitResult SubmitPauseMap(const GameAdapter &game) noexcept {
  return game.submit_pause_map();
}
inline ResumeSubmitResult SubmitResumeMap(const GameAdapter &game) noexcept {
  return game.submit_resume_map();
}
inline bool SubmitSetSpeed(const GameAdapter &game,
                           std::int32_t speed) noexcept {
  return game.submit_set_speed(speed);
}
inline SelectEventOptionResult
SubmitSelectEventOption(const GameAdapter &game,
                        std::int32_t option_index) noexcept {
  return game.submit_select_event_option(option_index);
}
inline SaveCheckpointResult
SubmitSaveCheckpoint(const GameAdapter &game) noexcept {
  return game.submit_save_checkpoint();
}
inline ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const GameAdapter &game, PendingInteractionReply reply) noexcept {
  return game.submit_reply_to_pending_interaction(reply);
}
inline RaiseTroopsResult
SubmitRaiseTroopsDefault(const GameAdapter &game) noexcept {
  return game.submit_raise_troops_default();
}
inline MoveArmyResult SubmitMoveArmy(const GameAdapter &game,
                                     std::int32_t army_id,
                                     std::int32_t province_id) noexcept {
  return game.submit_move_army(army_id, province_id);
}
inline PreviewMoveArmyResult
PreviewMoveArmy(const GameAdapter &game, std::int32_t army_id,
                std::int32_t province_id) noexcept {
  return game.preview_move_army(army_id, province_id);
}
inline DisbandArmyResult SubmitDisbandArmy(const GameAdapter &game,
                                           std::int32_t army_id) noexcept {
  return game.submit_disband_army(army_id);
}
inline SplitArmyHalfResult SubmitSplitArmyHalf(const GameAdapter &game,
                                               std::int32_t army_id) noexcept {
  return game.submit_split_army_half(army_id);
}
inline MergeArmiesResult SubmitMergeArmies(
    const GameAdapter &game, std::int32_t destination_army_id,
    std::int32_t source_army_id) noexcept {
  return game.submit_merge_armies(destination_army_id, source_army_id);
}
inline StartAssaultResult SubmitStartAssault(const GameAdapter &game,
                                             std::int32_t siege_id) noexcept {
  return game.submit_start_assault(siege_id);
}
inline StopAssaultResult SubmitStopAssault(const GameAdapter &game,
                                           std::int32_t siege_id) noexcept {
  return game.submit_stop_assault(siege_id);
}
inline bool ReadDeclarableWars(
    const GameAdapter &game,
    std::vector<DeclarableWarSnapshot> &output) noexcept {
  return game.read_declarable_wars(output);
}
inline DeclareWarResult
SubmitDeclareWar(const GameAdapter &game,
                 const DeclarableWarSnapshot &declaration) noexcept {
  return game.submit_declare_war(declaration);
}
inline ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const GameAdapter &game,
    std::vector<ArrangeMarriageChoice> &output,
    ArrangeMarriageQueryDiagnostics &diagnostics) noexcept {
  return game.read_arrange_marriage_choices(output, diagnostics);
}
inline ArrangeMarriageResult
SubmitArrangeMarriage(const GameAdapter &game,
                      const ArrangeMarriageChoice &choice) noexcept {
  return game.submit_arrange_marriage(choice);
}
inline EnforceDemandsResult
SubmitEnforceDemands(const GameAdapter &game, std::int32_t war_id) noexcept {
  return game.submit_enforce_demands(war_id);
}
inline ReadArmyStrengthsResult ReadArmyStrengths(
    const GameAdapter &game,
    std::vector<ArmyStrengthSnapshot> &output) noexcept {
  return game.read_army_strengths(output);
}
inline ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const GameAdapter &game, const CombatSimulationInputsRequest &request,
    CombatSimulationInputsSnapshot &output) noexcept {
  return game.read_combat_simulation_inputs(request, output);
}
inline ReadCombatSimulationInputsV3Result ReadCombatSimulationInputsV3(
    const GameAdapter &game, const CombatSimulationInputsRequest &request,
    CombatSimulationInputsV3Snapshot &output) noexcept {
  return game.read_combat_simulation_inputs_v3(request, output);
}
inline ReadWarTerminationOptionsResult ReadWarTerminationOptions(
    const GameAdapter &game, std::int32_t war_id,
    WarTerminationOptionsSnapshot &output) noexcept {
  return game.read_war_termination_options(war_id, output);
}
inline ReadWarTerminationTermsResult ReadWarTerminationTerms(
    const GameAdapter &game, std::int32_t war_id,
    WarTerminationTermsSnapshot &output) noexcept {
  return game.read_war_termination_terms(war_id, output);
}
inline ReadWarTerminationExitTermsResult ReadWarTerminationExitTerms(
    const GameAdapter &game, std::int32_t war_id,
    WarTerminationExitTermsSnapshot &output) noexcept {
  return game.read_war_termination_exit_terms(war_id, output);
}
inline std::string_view LastWarTerminationExitTermsUnavailableReason(
    const GameAdapter &game) noexcept {
  return game.last_war_termination_exit_terms_unavailable_reason();
}
inline SurrenderWarResult SubmitSurrenderWar(
    const GameAdapter &game, std::int32_t war_id) noexcept {
  return game.submit_surrender_war(war_id);
}
inline OfferWhitePeaceResult SubmitOfferWhitePeace(
    const GameAdapter &game, std::int32_t war_id) noexcept {
  return game.submit_offer_white_peace(war_id);
}

} // namespace xar::game
