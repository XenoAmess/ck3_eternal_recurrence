#include "xar_bridge/ck3_12002_adapter.hpp"

#include <windows.h>
#include "xar_bridge/ck3_12002_war_cash_treasury.hpp"
#include "xar_bridge/ck3_12002_actor_resources.hpp"

#include <array>
#include <utility>

namespace xar::game {
namespace {

constexpr auto kCapabilities = std::to_array<std::string_view>({
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
    "game.command.center-map-on-landed-title-v1",
    "game.command.query-combat-simulation-inputs-v2-N",
    "game.command.query-war-termination-options-N",
    "game.command.query-war-termination-terms-v1-N",
    "game.command.surrender-war-N",
    "game.command.offer-white-peace-N",
    "game.command.query-arrange-marriage-choices",
    "game.command.arrange-marriage-N",
    "game.adapter.exact-build",
    "game.adapter.minimized-headless",
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
    "game.command.query-player-faction-alerts-v1",
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
    "game.command.query-war-prisoner-release-pairs-v1-N",
#endif
});

const AdapterDescriptor kDescriptor{
    "ck3-1.20.0.2-msvc-x64", "1.20.0.2", ck3_12002::kExecutableSha256,
    ck3_12002::kCheckpointSaveName, kCapabilities};

class Ck3_12002Adapter final : public GameAdapter {
public:
  explicit Ck3_12002Adapter(Ck3_12002AdapterBindings bindings) noexcept
      : bindings_(std::move(bindings)) {
    // Both callbacks borrow this member, never the temporary binding bundle.
    bindings_.events.submit_context = &bindings_.commands;
    bindings_.events.submit_command = ck3_12002::SubmitCommandCopyCompat;
    bindings_.military.submit_context = &bindings_.commands;
    bindings_.military.submit_copy = ck3_12002::SubmitCommandCopyCompat;
  }

  const AdapterDescriptor &descriptor() const noexcept override {
    return kDescriptor;
  }
  bool enabled() const noexcept override { return bindings_.core.enabled; }

  bool read_snapshot(Snapshot &output) const noexcept override {
    output = {};
    ck3_12002::CoreSnapshotPrefix prefix{};
    if (!ck3_12002::ReadCoreSnapshot(bindings_.core, prefix)) return false;
    Snapshot observed{};
    observed.date_raw = prefix.clock.date_raw;
    observed.speed = prefix.clock.speed;
    observed.paused = prefix.clock.paused;
    observed.player_id = prefix.local_player_id;
    observed.map_ready = prefix.map_ready;
    observed.has_played_character = prefix.has_played_character;
    observed.played_character_id = prefix.played_character_id;
    observed.played_character_alive = prefix.played_character_alive;
    if (!prefix.map_ready) {
      // The local-player sentinel makes this a startup/menu prefix, before
      // category registries are populated, as in the previous adapter.
      output = std::move(observed);
      return true;
    }
    if (prefix.has_played_character) {
      std::int64_t treasury_raw = 0;
      if (!ck3_12002::ReadWarCashTreasury(
              bindings_.core, prefix.played_character_id, treasury_raw))
        return false;
      observed.played_character_gold.raw = treasury_raw;
      const auto read_resource_memory = +[](void *, std::uintptr_t address,
                                            void *target, std::size_t size) noexcept {
        SIZE_T copied = 0;
        return target != nullptr && address != 0 && size != 0 &&
            ReadProcessMemory(GetCurrentProcess(),
                reinterpret_cast<const void *>(address), target, size,
                &copied) != FALSE && copied == size;
      };
      ck3_12002::ActorResourceBalances12002 resources{};
      const auto actor = reinterpret_cast<std::uintptr_t>(
          ck3_12002::ResolveCoreCharacter(bindings_.core, prefix.played_character_id));
      if (!ck3_12002::ReadActorResourceBalances12002(read_resource_memory,
              nullptr, actor, prefix.played_character_id, resources)) return false;
      observed.played_character_prestige.raw = resources.prestige_raw;
      observed.played_character_piety.raw = resources.piety_raw;
      observed.played_character_stress_points = resources.stress_points;
      PlayedCharacterRelationships12002 relationships{};
      if (!ck3_12002::ReadPlayedCharacterRelationships(
              bindings_.core, prefix.played_character_id, relationships))
        return false;
      observed.played_character_betrothed_id =
          relationships.betrothed_character_id;
      observed.played_character_primary_spouse_id =
          relationships.primary_spouse_character_id;
      observed.played_character_spouse_ids =
          std::move(relationships.spouse_character_ids);
    }
    if (!ck3_12002::ReadEventsSnapshot(bindings_.events, observed) ||
        ck3_12002::ReadWorldSnapshot(bindings_.world, bindings_.armies,
                                    bindings_.provinces, prefix, observed) !=
            ck3_12002::WorldReadResult::available)
      return false;
    const auto settlement = ck3_12002::ReadSettlement(
        bindings_.settlement, bindings_.core, observed);
    if (settlement != ck3_12002::SettlementReadResult::published &&
        settlement != ck3_12002::SettlementReadResult::not_published)
      return false;
    output = std::move(observed);
    return true;
  }

  PauseSubmitResult submit_pause_map(
      Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot == nullptr)
      return ck3_12002::SubmitPauseMap(bindings_.commands, bindings_.core);
    *observed_snapshot = {};
    Snapshot observed{};
    if (!read_snapshot(observed)) return PauseSubmitResult::unavailable;
    *observed_snapshot = observed;
    return PauseFromSnapshot(observed);
  }
  ResumeSubmitResult submit_resume_map(
      Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot == nullptr)
      return ck3_12002::SubmitResumeMap(bindings_.commands, bindings_.core);
    *observed_snapshot = {};
    Snapshot observed{};
    if (!read_snapshot(observed)) return ResumeSubmitResult::unavailable;
    *observed_snapshot = observed;
    return ResumeFromSnapshot(observed);
  }
  PauseSubmitResult SubmitObservedPause(
      const Snapshot &observed) const noexcept {
    return MatchesCoreSnapshot(observed) ? PauseFromSnapshot(observed)
                                        : PauseSubmitResult::unavailable;
  }
  ResumeSubmitResult SubmitObservedResume(
      const Snapshot &observed) const noexcept {
    return MatchesCoreSnapshot(observed) ? ResumeFromSnapshot(observed)
                                        : ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    return ck3_12002::SubmitSetSpeed(bindings_.commands, bindings_.core, speed);
  }
  SelectEventOptionResult submit_select_event_option(
      std::int32_t option_index) const noexcept override {
    return ck3_12002::SubmitSelectEventOption(bindings_.events, option_index);
  }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    return ck3_12002::SubmitSaveCheckpoint(bindings_.commands, bindings_.core);
  }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction(
      PendingInteractionReply reply) const noexcept override {
    return ck3_12002::SubmitReplyToPendingInteraction(bindings_.events, reply);
  }
  AcknowledgePendingInteractionResult submit_acknowledge_pending_interaction(
      std::int32_t id) const noexcept override {
    return ck3_12002::SubmitAcknowledgePendingInteraction(bindings_.events, id);
  }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override {
    return ck3_12002::SubmitRaiseTroopsDefault(bindings_.military, WorldAccess());
  }
  MoveArmyResult submit_move_army(std::int32_t army,
                                  std::int32_t province) const noexcept override {
    return ck3_12002::SubmitMoveArmy(bindings_.military, WorldAccess(), army,
                                    province);
  }
  PreviewMoveArmyResult preview_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    return ck3_12002::PreviewMoveArmy(bindings_.military, WorldAccess(), army,
                                     province);
  }
  DisbandArmyResult submit_disband_army(std::int32_t army) const noexcept override {
    return ck3_12002::SubmitDisbandArmy(bindings_.military, WorldAccess(), army);
  }
  SplitArmyHalfResult submit_split_army_half(
      std::int32_t army) const noexcept override {
    return ck3_12002::SubmitSplitArmyHalf(bindings_.military, WorldAccess(), army);
  }
  MergeArmiesResult submit_merge_armies(
      std::int32_t destination, std::int32_t source) const noexcept override {
    return ck3_12002::SubmitMergeArmies(bindings_.military, WorldAccess(),
                                       destination, source);
  }
  StartAssaultResult submit_start_assault(std::int32_t siege) const noexcept override {
    return ck3_12002::SubmitStartAssault(bindings_.military, WorldAccess(), siege);
  }
  StopAssaultResult submit_stop_assault(std::int32_t siege) const noexcept override {
    return ck3_12002::SubmitStopAssault(bindings_.military, WorldAccess(), siege);
  }
  bool read_declarable_wars(
      std::vector<DeclarableWarSnapshot> &output) const noexcept override {
    return ck3_12002::ReadDeclarableWars(bindings_.declarations, output);
  }
  ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_character_id,
      std::vector<DeclarableWarSnapshot> &output) const noexcept override {
    return ck3_12002::ReadDeclarableWarsForTarget(
        bindings_.declarations, target_character_id, output);
  }
  DeclareWarResult submit_declare_war(
      const DeclarableWarSnapshot &declaration) const noexcept override {
    return ck3_12002::SubmitDeclareWar(bindings_.declarations, declaration);
  }
  ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<ArrangeMarriageChoice> &output,
      ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    return ck3_12002::ReadArrangeMarriageChoices(bindings_.marriage, output,
                                                 diagnostics);
  }
  ArrangeMarriageResult submit_arrange_marriage(
      const ArrangeMarriageChoice &choice) const noexcept override {
    return ck3_12002::SubmitArrangeMarriage(bindings_.marriage, choice);
  }
  ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_character_id,
      std::vector<ArrangeMarriageFamilyCandidateV1> &output,
      ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    return ck3_12002::ReadArrangeMarriageFamilyCandidatesV1(
        bindings_.family, subject_character_id, output, diagnostics);
#else
    static_cast<void>(subject_character_id);
    output.clear();
    diagnostics = {};
    return ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
#endif
  }
  EnforceDemandsResult submit_enforce_demands(
      std::int32_t war) const noexcept override {
    return ck3_12002::SubmitEnforceDemands(bindings_.diplomacy, war);
  }
  ReadArmyStrengthsResult read_army_strengths(
      std::vector<ArmyStrengthSnapshot> &output) const noexcept override {
    Snapshot scope{};
    if (!read_snapshot(scope)) {
      output.clear();
      return ReadArmyStrengthsResult::unavailable;
    }
    return ck3_12002::ReadArmyStrengths(bindings_.armies, scope, output);
  }
  ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsSnapshot &output) const noexcept override {
    Snapshot scope{};
    if (!read_snapshot(scope)) {
      output = {};
      return ReadCombatSimulationInputsResult::unavailable;
    }
    return ck3_12002::ReadCombatSimulationInputs(bindings_.combat, scope, request,
                                                output);
  }
  ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsV3Snapshot &output) const noexcept override {
    output = {};
    Snapshot scope{};
    if (!read_snapshot(scope)) return ReadCombatSimulationInputsV3Result::unavailable;
    return ck3_12002::ReadCombatSimulationInputsV3(bindings_.phase, scope,
                                                  request, output);
  }
  ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war, WarTerminationOptionsSnapshot &output) const noexcept override {
    return ck3_12002::ReadWarTerminationOptions(bindings_.diplomacy, war, output);
  }
  ReadWarTerminationTermsResult read_war_termination_terms(
      std::int32_t war, WarTerminationTermsSnapshot &output) const noexcept override {
    return ck3_12002::ReadWarTerminationTerms(bindings_.terms, war, output);
  }
  ReadWarTerminationExitTermsResult read_war_termination_exit_terms(
      std::int32_t, WarTerminationExitTermsSnapshot &output) const noexcept override {
    output = {};
    return ReadWarTerminationExitTermsResult::unavailable;
  }
  std::string_view last_war_termination_exit_terms_unavailable_reason()
      const noexcept override {
    return "native_effect_preview_production_disabled_after_11906_access_violations";
  }
  SurrenderWarResult submit_surrender_war(std::int32_t war) const noexcept override {
    return ck3_12002::SubmitSurrenderWar(bindings_.diplomacy, war);
  }
  OfferWhitePeaceResult submit_offer_white_peace(std::int32_t war) const noexcept override {
    return ck3_12002::SubmitOfferWhitePeace(bindings_.diplomacy, war);
  }

private:
  bool MatchesCoreSnapshot(const Snapshot &observed) const noexcept {
    ck3_12002::CoreSnapshotPrefix current{};
    return ck3_12002::ReadCoreSnapshot(bindings_.core, current) &&
           current.clock.date_raw == observed.date_raw &&
           current.clock.speed == observed.speed &&
           current.clock.paused == observed.paused &&
           current.local_player_id == observed.player_id &&
           current.map_ready == observed.map_ready &&
           current.has_played_character == observed.has_played_character &&
           current.played_character_id == observed.played_character_id &&
           current.played_character_alive == observed.played_character_alive;
  }
  bool TimelineReady(const Snapshot &observed) const noexcept {
    return bindings_.commands.enabled &&
           bindings_.commands.pause_primary_vtable != 0 &&
           bindings_.commands.pause_secondary_vtable != 0 &&
           observed.map_ready && observed.player_id >= 0;
  }
  bool QueueTimeline(const Snapshot &observed, bool paused) const noexcept {
    ck3_12002::TimeCommand command{};
    command.primary_vtable = bindings_.commands.pause_primary_vtable;
    command.secondary_vtable = bindings_.commands.pause_secondary_vtable;
    command.flags = 8;
    command.value = observed.player_id;
    command.paused = paused ? 1 : 0;
    return ck3_12002::SubmitCommandCopy(bindings_.commands, &command) ==
           ck3_12002::CommandSubmitResult::submitted;
  }
  PauseSubmitResult PauseFromSnapshot(const Snapshot &observed) const noexcept {
    if (!TimelineReady(observed)) return PauseSubmitResult::unavailable;
    if (observed.paused) return PauseSubmitResult::already_paused;
    return QueueTimeline(observed, true) ? PauseSubmitResult::submitted
                                         : PauseSubmitResult::unavailable;
  }
  ResumeSubmitResult ResumeFromSnapshot(const Snapshot &observed) const noexcept {
    if (!TimelineReady(observed)) return ResumeSubmitResult::unavailable;
    if (!observed.paused) return ResumeSubmitResult::already_running;
    return QueueTimeline(observed, false) ? ResumeSubmitResult::submitted
                                          : ResumeSubmitResult::unavailable;
  }
  static const Ck3_12002Adapter &Self(void *context) noexcept {
    return *static_cast<const Ck3_12002Adapter *>(context);
  }
  static bool ReadSnapshotCallback(void *context, Snapshot &output) noexcept {
    return Self(context).read_snapshot(output);
  }
  static void *ResolveCharacter(void *context, std::int32_t id) noexcept {
    return ck3_12002::ResolveCoreCharacter(Self(context).bindings_.core, id);
  }
  static void *ResolveUnit(void *context, std::int32_t id) noexcept {
    return ck3_12002::ResolveArmyUnit(Self(context).bindings_.armies, id);
  }
  static void *ResolveProvince(void *context, std::int32_t id) noexcept {
    return ck3_12002::ResolveObjectiveProvince(Self(context).bindings_.provinces, id);
  }
  static void *ResolveSiege(void *context, std::int32_t id) noexcept {
    return ck3_12002::ResolveObjectiveSiege(Self(context).bindings_.provinces, id);
  }
  ck3_12002::MilitaryWorldAccess WorldAccess() const noexcept {
    return {const_cast<Ck3_12002Adapter *>(this), ReadSnapshotCallback,
            ResolveCharacter, ResolveUnit, ResolveProvince, ResolveSiege};
  }
  Ck3_12002AdapterBindings bindings_;
};

} // namespace

Ck3_12002AdapterBindings BindCk3_12002AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  Ck3_12002AdapterBindings bindings{};
  bindings.core = ck3_12002::BindCoreImage(image_base, executable_sha256);
  bindings.commands = ck3_12002::BindCommandImage(image_base, executable_sha256);
  bindings.events = ck3_12002::BindEventsImage(image_base, executable_sha256);
  bindings.armies = ck3_12002::BindArmyImage(image_base, executable_sha256);
  bindings.world = ck3_12002::BindWorldImage(image_base, executable_sha256);
  bindings.provinces = ck3_12002::BindProvinceImage(image_base, executable_sha256);
  bindings.military = ck3_12002::BindMilitaryImage(image_base, executable_sha256,
                                                  bindings.commands);
  bindings.marriage = ck3_12002::BindContextImage(image_base, executable_sha256);
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  bindings.family = ck3_12002::BindFamilyImage(image_base, executable_sha256);
#endif
  bindings.diplomacy = ck3_12002::BindDiplomacyImage(image_base, executable_sha256);
  bindings.declarations = ck3_12002::BindDeclarationsImage(image_base, executable_sha256);
  bindings.terms = ck3_12002::BindClaimTermsImage(image_base, executable_sha256);
  bindings.combat = ck3_12002::BindCombatImage(image_base, executable_sha256);
  bindings.phase = ck3_12002::BindPhaseImage(image_base, executable_sha256);
  bindings.settlement = ck3_12002::BindSettlementImage(image_base, executable_sha256);
  // Adapter construction rebinds borrowed command pointers to stable members.
  bindings.military.submit_context = nullptr;
  return bindings;
}

const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept { return kDescriptor; }

PauseSubmitResult SubmitCk3_12002PauseMapObserved(
    const GameAdapter &adapter, const Snapshot &observed_snapshot) noexcept {
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&adapter);
  return native == nullptr ? PauseSubmitResult::unavailable
                           : native->SubmitObservedPause(observed_snapshot);
}
ResumeSubmitResult SubmitCk3_12002ResumeMapObserved(
    const GameAdapter &adapter, const Snapshot &observed_snapshot) noexcept {
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&adapter);
  return native == nullptr ? ResumeSubmitResult::unavailable
                           : native->SubmitObservedResume(observed_snapshot);
}

std::unique_ptr<GameAdapter> CreateCk3_12002AdapterFromBindings(
    Ck3_12002AdapterBindings bindings) noexcept {
  return std::make_unique<Ck3_12002Adapter>(std::move(bindings));
}

std::unique_ptr<GameAdapter> CreateCk3_12002Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12002AdapterFromBindings(BindCk3_12002AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), executable_sha256));
}

} // namespace xar::game
