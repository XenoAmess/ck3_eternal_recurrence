#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/army_strength_query_diagnostic_v1.hpp"

#include <windows.h>
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_events.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_war.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12003_army_reserve.hpp"
#include "xar_bridge/ck3_12003_war_occupation.hpp"
#include "xar_bridge/ck3_12003_title_holder.hpp"
#include "xar_bridge/ck3_12004_title_holder.hpp"
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
    "game.command.halt-army-N",
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
  explicit Ck3_12002Adapter(Ck3_12002AdapterBindings bindings,
      const AdapterDescriptor &descriptor = kDescriptor) noexcept
      : bindings_(std::move(bindings)), descriptor_(&descriptor) {
    if (IsCk3_12003Descriptor(descriptor)) {
      reserve_bindings_ = ck3_12003::BindPlayerArmyReserveImageV1(
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
          descriptor.executable_sha256);
      title_holder_bindings_ = ck3_12003::BindTitleHolderImageV1(
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
          descriptor.executable_sha256);
      occupation_bindings_ = ck3_12003::BindWarOccupationTargetsImageV1(
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
          descriptor.executable_sha256);
    } else if (IsCk3_12004Descriptor(descriptor)) {
      const auto image_base =
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
      reserve_bindings_ = ck3_12004::BindPlayerArmyReserveImage12004V1(
          image_base, descriptor.executable_sha256);
      title_holder_bindings_ = ck3_12004::BindTitleHolderImageV1(
          image_base, descriptor.executable_sha256);
      occupation_bindings_ = ck3_12004::BindWarOccupationTargets12004(
          image_base, descriptor.executable_sha256, bindings_.world,
          bindings_.provinces);
    }
    // Both callbacks borrow this member, never the temporary binding bundle.
    bindings_.events.submit_context = &bindings_.commands;
    bindings_.events.submit_command = ck3_12002::SubmitCommandCopyCompat;
    bindings_.military.submit_context = &bindings_.commands;
    bindings_.military.submit_copy = ck3_12002::SubmitCommandCopyCompat;
  }

  const AdapterDescriptor &descriptor() const noexcept override {
    return *descriptor_;
  }
  bool enabled() const noexcept override { return bindings_.core.enabled; }

  const ck3_12002::DeclarationsBindings *BorrowDeclarations12004() const noexcept {
    return IsCk3_12004Descriptor(descriptor()) ? &bindings_.declarations : nullptr;
  }

  bool read_snapshot(Snapshot &output) const noexcept override {
    output = {};
    if (IsCk3_12004Descriptor(descriptor()))
      return ReadCk3_12004Snapshot(bindings_, output);
    ck3_12002::CoreSnapshotPrefix prefix{};
    if (!bindings_.read_core_snapshot(bindings_.core, prefix)) return false;
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
  // Command-only core observation. It must not be published as a full snapshot.
  bool ReadTimelineCoreSnapshot(Snapshot &output) const noexcept {
    output = {};
    ck3_12002::CoreSnapshotPrefix prefix{};
    if (!bindings_.read_core_snapshot(bindings_.core, prefix)) return false;
    output.date_raw = prefix.clock.date_raw;
    output.speed = prefix.clock.speed;
    output.paused = prefix.clock.paused;
    output.player_id = prefix.local_player_id;
    output.map_ready = prefix.map_ready;
    output.has_played_character = prefix.has_played_character;
    output.played_character_id = prefix.played_character_id;
    output.played_character_alive = prefix.played_character_alive;
    return true;
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
    return IsCk3_12004Descriptor(*descriptor_)
        ? ck3_12004::SubmitSelectEventOption(bindings_.events, option_index)
        : ck3_12002::SubmitSelectEventOption(bindings_.events, option_index);
  }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    return ck3_12002::SubmitSaveCheckpoint(bindings_.commands, bindings_.core);
  }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction(
      PendingInteractionReply reply) const noexcept override {
    return IsCk3_12004Descriptor(*descriptor_)
        ? ck3_12004::SubmitReplyToPendingInteraction(bindings_.events, reply)
        : ck3_12002::SubmitReplyToPendingInteraction(bindings_.events, reply);
  }
  AcknowledgePendingInteractionResult submit_acknowledge_pending_interaction(
      std::int32_t id) const noexcept override {
    return IsCk3_12004Descriptor(*descriptor_)
        ? ck3_12004::SubmitAcknowledgePendingInteraction(bindings_.events, id)
        : ck3_12002::SubmitAcknowledgePendingInteraction(bindings_.events, id);
  }
  ck3_12002::PrewarDefaultMusterStatusV1 ReadPlayerDefaultRaise(
      ck3_12002::PlayerDefaultRaiseObservationV1 &output) const noexcept {
    output = {};
    if (!IsCk3_12003Descriptor(*descriptor_) &&
        !IsCk3_12004Descriptor(*descriptor_)) return output.status;
    const auto status = ck3_12002::ReadPlayerDefaultRaiseV1(
        bindings_.military, WorldAccess(), output);
    ck3_12003::ReadPlayerUnraisedTroopsV1(reserve_bindings_, WorldAccess(), output);
    return status;
  }
  bool ReadWarCashCurrentResources(
      const Snapshot &snapshot,
      ck3_12003::war_cash_current::ActorResources &output) const noexcept {
    output = {};
    if (!IsCk3_12003Descriptor(*descriptor_) || !snapshot.paused ||
        !snapshot.map_ready || !snapshot.has_played_character ||
        !snapshot.played_character_alive || snapshot.played_character_id <= 0)
      return false;
    return ck3_12003::war_cash_current::ReadActor(
        bindings_.war_cash_current,
        ck3_12002::ResolveCoreCharacter(bindings_.core, snapshot.played_character_id),
        snapshot.played_character_id, output);
  }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override {
    return ck3_12002::SubmitRaiseTroopsDefault(bindings_.military, WorldAccess());
  }
  MoveArmyResult submit_move_army(std::int32_t army,
                                  std::int32_t province) const noexcept override {
    return ck3_12002::SubmitMoveArmy(bindings_.military, WorldAccess(), army,
                                    province);
  }
  HaltArmyResult submit_halt_army(std::int32_t army) const noexcept override {
    return ck3_12002::SubmitHaltArmy(bindings_.military, WorldAccess(), army);
  }
  PreviewMoveArmyResult preview_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    auto preview = ck3_12002::PreviewMoveArmy(
        bindings_.military, WorldAccess(), army, province);
    if (preview.status == PreviewMoveArmyStatus::available &&
        IsCk3_12003Descriptor(*descriptor_)) {
      preview.province_supply = ck3_12002::ReadArmyProvinceSupplyForPreview(
          bindings_.armies, WorldAccess(), preview);
    }
    return preview;
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
    auto &diagnostic = ck3_12002::g_army_strength_query_diagnostic_v1;
    diagnostic.reader.store("native_snapshot");
    Snapshot scope{};
    const bool snapshot_ok = read_snapshot(scope);
    diagnostic.native_snapshot.store(snapshot_ok);
    if (!snapshot_ok) {
      output.clear();
      return ReadArmyStrengthsResult::unavailable;
    }
    diagnostic.reader.store("baseline");
    const auto result = ck3_12002::ReadArmyStrengths(bindings_.armies, scope, output);
    diagnostic.baseline_result.store(static_cast<std::int64_t>(result));
    diagnostic.scope_rows.store(static_cast<std::int64_t>(output.size()));
    if (result == ReadArmyStrengthsResult::available ||
        result == ReadArmyStrengthsResult::partial)
      ck3_12002::AttachCommittedRouteTimelineToArmyRows(
          bindings_.movement_routes, scope, output);
    if ((result == ReadArmyStrengthsResult::available ||
         result == ReadArmyStrengthsResult::partial) &&
        bindings_.native_owner_recall.enabled) {
      auto provinces = bindings_.provinces;
      auto recall = bindings_.native_owner_recall;
      recall.province_context = &provinces;
      recall.resolve_province = [](void *context, std::int32_t id) -> void * {
        return ck3_12002::ResolveObjectiveProvince(
            *static_cast<const ck3_12002::ProvinceBindings *>(context), id);
      };
      for (auto &row : output) {
        diagnostic.army_id.store(row.army_id);
        diagnostic.reader.store("owner_recall_attach");
        row.native_owner_recall_inputs_v1.emplace();
        ck3_12003::AttachBattleNativeOwnerRecallInputsForUnitsV1(
            recall, scope, std::vector<std::int32_t>{row.army_id},
            *row.native_owner_recall_inputs_v1);
        diagnostic.reader.store("owner_recall_returned");
      }
    }
    if (result == ReadArmyStrengthsResult::available ||
        result == ReadArmyStrengthsResult::partial)
      AttachNativeMaaRecruitmentInputsToArmyRowsV1(
          bindings_.native_maa_recruitment, output);
    if (result == ReadArmyStrengthsResult::available ||
        result == ReadArmyStrengthsResult::partial)
      AttachPlayerOwnedRegimentsToArmyRowsV1(
          bindings_.core, bindings_.owned_regiments, scope, output);
    diagnostic.reader.store(result == ReadArmyStrengthsResult::unavailable
        ? "baseline_unavailable" : "returned");
    return result;
  }
  ReadCombatSimulationInputsResult read_combat_simulation_inputs(
      const CombatSimulationInputsRequest &request,
      CombatSimulationInputsSnapshot &output) const noexcept override {
    Snapshot scope{};
    if (!read_snapshot(scope)) {
      output = {};
      return ReadCombatSimulationInputsResult::unavailable;
    }
    const auto result = ck3_12002::ReadCombatSimulationInputs(
        bindings_.combat, scope, request, output);
    if (result == ReadCombatSimulationInputsResult::available) {
      // Partial contextual observation is independent of existing v2 readiness.
      (void)ck3_12002::ReadContextualAdvantageInputs(
          bindings_.phase, scope, output, output.contextual_advantage);
      ck3_12004::AttachPhaseEventCalendarInputs12004(
          bindings_.phase_event_calendar12004, output);
    }
    return result;
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
  ReadTitleHolderV1Result read_title_holder_v1(
      std::int32_t title_id, TitleHolderV1 &output) const noexcept override {
    output = {};
    if (!IsCk3_12003Descriptor(*descriptor_) &&
        !IsCk3_12004Descriptor(*descriptor_))
      return ReadTitleHolderV1Result::unavailable;
    Snapshot scope{};
    if (!read_snapshot(scope))
      return ReadTitleHolderV1Result::unavailable;
    return ck3_12003::ReadTitleHolderV1(
        title_holder_bindings_, scope, title_id, output);
  }
  ReadWarOccupationTargetsV1Result read_war_occupation_targets_v1(
      std::int32_t war, WarOccupationTargetsV1 &output) const noexcept override {
    output = {};
    if (!IsCk3_12003Descriptor(*descriptor_) &&
        !IsCk3_12004Descriptor(*descriptor_))
      return ReadWarOccupationTargetsV1Result::unavailable;
    Snapshot scope{};
    if (!read_snapshot(scope))
      return ReadWarOccupationTargetsV1Result::unavailable;
    return ck3_12003::ReadWarOccupationTargetsV1(
        occupation_bindings_, scope, war, output);
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

  NativeMaaRegularPersonalCreateSubmissionV1 SubmitRegularMaaCreate(
      const NativeMaaRegularPersonalCreateRequestV1 &request) const noexcept {
    return ck3_12003::SubmitNativeMaaRegularPersonalCreateV1(
        bindings_.native_maa_create, request);
  }

private:
  bool MatchesCoreSnapshot(const Snapshot &observed) const noexcept {
    ck3_12002::CoreSnapshotPrefix current{};
    return bindings_.read_core_snapshot(bindings_.core, current) &&
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
  ck3_12003::PlayerArmyReserveBindingsV1 reserve_bindings_{};
  ck3_12003::TitleHolderBindingsV1 title_holder_bindings_{};
  ck3_12003::WarOccupationTargetsBindingsV1 occupation_bindings_{};
  const AdapterDescriptor *descriptor_;
};

} // namespace

void AttachNativeMaaRecruitmentInputsToArmyRowsV1(
    const ck3_12003::NativeMaaRecruitmentBindings &bindings,
    std::vector<ArmyStrengthSnapshot> &output) noexcept {
  if (!bindings.enabled) return;
  std::vector<NativeMaaRecruitmentInputsV1> observed_owners;
  for (auto &row : output) {
    if (row.scope_role != ArmyStrengthScopeRole::player) continue;
    std::optional<std::int32_t> owner_id;
    if (row.native_owner_recall_inputs_v1 &&
        row.native_owner_recall_inputs_v1->available &&
        row.native_owner_recall_inputs_v1->owners_in_stored_order.size() == 1) {
      owner_id = row.native_owner_recall_inputs_v1
                     ->owners_in_stored_order.front().owner_character_id;
    }
    for (const auto &observed : observed_owners) {
      if (owner_id && observed.owner_character_id == owner_id) {
        row.native_maa_recruitment_inputs_v1 = observed;
        break;
      }
    }
    if (row.native_maa_recruitment_inputs_v1) continue;
    auto observed = ck3_12003::ReadNativeMaaRecruitmentInputsForUnitV1(
        bindings, row.army_id);
    row.native_maa_recruitment_inputs_v1 = observed;
    if (observed.owner_character_id)
      observed_owners.push_back(std::move(observed));
  }
}


void AttachPlayerOwnedRegimentsToArmyRowsV1(
    const ck3_12002::CoreBindings &core,
    const ck3_12003::OwnedRegimentsBindingsV1 &bindings,
    const Snapshot &scope, std::vector<ArmyStrengthSnapshot> &output) noexcept {
  if (!bindings.read_type || !scope.has_played_character) return;
  for (auto &row : output) {
    if (row.scope_role != ArmyStrengthScopeRole::player) continue;
    row.owned_regiments_v1.emplace();
    ck3_12003::ReadPlayerOwnedRegimentsV1(
        bindings, ck3_12002::ResolveCoreCharacter(core, scope.played_character_id),
        scope.played_character_id, *row.owned_regiments_v1);
    return;
  }
}

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

bool ReadCk3_12002TimelineCoreSnapshot(
    const GameAdapter &adapter, Snapshot &output) noexcept {
  output = {};
  const auto &source = ck3_12002::NativeAdapter12002(adapter);
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&source);
  return native != nullptr && native->ReadTimelineCoreSnapshot(output);
}

const ck3_12002::DeclarationsBindings *BorrowOrdinaryHolyWarDeclarations12004(
    const GameAdapter &adapter) noexcept {
  const auto &source = ck3_12002::NativeAdapter12002(adapter);
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&source);
  return native != nullptr ? native->BorrowDeclarations12004() : nullptr;
}

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

ck3_12002::PrewarDefaultMusterStatusV1 ReadCk3_12003PlayerDefaultRaiseV1(
    const GameAdapter &adapter,
    ck3_12002::PlayerDefaultRaiseObservationV1 &output) noexcept {
  output = {};
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&adapter);
  return native == nullptr ? output.status : native->ReadPlayerDefaultRaise(output);
}

bool ReadCk3_12003WarCashCurrentResourcesV1(
    const GameAdapter &adapter, const Snapshot &snapshot,
    ck3_12003::war_cash_current::ActorResources &output) noexcept {
  output = {};
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&adapter);
  return native != nullptr && native->ReadWarCashCurrentResources(snapshot, output);
}

NativeMaaRegularPersonalCreateSubmissionV1 SubmitNativeMaaRegularPersonalCreate(
    const GameAdapter &adapter,
    const NativeMaaRegularPersonalCreateRequestV1 &request) noexcept {
  const auto *native = dynamic_cast<const Ck3_12002Adapter *>(&adapter);
  if (native != nullptr) return native->SubmitRegularMaaCreate(request);
  NativeMaaRegularPersonalCreateSubmissionV1 output;
  output.owner_character_id = request.owner_character_id;
  output.type_index = request.type_index;
  output.reason = "native_adapter_unavailable";
  return output;
}

std::unique_ptr<GameAdapter> CreateCk3_12002AdapterFromBindings(
    Ck3_12002AdapterBindings bindings) noexcept {
  return std::make_unique<Ck3_12002Adapter>(std::move(bindings));
}

std::unique_ptr<GameAdapter> CreateCrozierAdapterFromBindings(
    Ck3_12002AdapterBindings bindings,
    const AdapterDescriptor &descriptor) noexcept {
  return std::make_unique<Ck3_12002Adapter>(std::move(bindings), descriptor);
}

std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(
    Ck3_12003AdapterBindings bindings) noexcept {
  return std::make_unique<Ck3_12002Adapter>(
      std::move(bindings), Ck3_12003AdapterDescriptor());
}

std::unique_ptr<GameAdapter> CreateCk3_12002Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12002AdapterFromBindings(BindCk3_12002AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), executable_sha256));
}

} // namespace xar::game
