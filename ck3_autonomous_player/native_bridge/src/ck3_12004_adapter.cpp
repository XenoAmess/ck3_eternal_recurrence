#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_tactical_daily_sentinel.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_events.hpp"
#include "xar_bridge/ck3_12004_combat.hpp"
#include "xar_bridge/ck3_12004_phase.hpp"
#include "xar_bridge/ck3_12004_military.hpp"
#include "xar_bridge/ck3_12004_diplomacy.hpp"
#include "xar_bridge/ck3_12004_war_declarations.hpp"
#include "xar_bridge/ck3_12004_war_cash_claim_terms.hpp"
#include "xar_bridge/ck3_12004_family_relationships.hpp"
#include "xar_bridge/ck3_12004_family_actions.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/ck3_12004_world.hpp"
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_routes.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"
#include "xar_bridge/frontend_gui_route_v1.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/ordinary_interaction_request_v1.hpp"
#include "xar_bridge/normal_exit_map_v1.hpp"
#include "xar_bridge/grant_title_picker_v1.hpp"
#include "xar_bridge/ingame_decisions_opener_v1.hpp"
#include "xar_bridge/ingame_decision_item_v1.hpp"

#include <windows.h>
#include <array>
#include <utility>

namespace xar::game {
namespace {
void ReplaceIdentityToken(std::string &serialized, std::string_view from,
                          std::string_view to) {
  std::size_t at = 0;
  while ((at = serialized.find(from, at)) != std::string::npos) {
    serialized.replace(at, from.size(), to);
    at += to.size();
  }
}
} // namespace

const AdapterDescriptor &Ck3_12004AdapterDescriptor() noexcept {
  static constexpr auto capabilities = std::to_array<std::string_view>({
      "game.query.core-frame.v1",
      "game.state.snapshot", "game.state.xar-one-life-settlement",
      "game.state.map-ready", "game.state.played-character",
      "game.state.active-event", "game.state.pending-character-interaction",
      "game.state.active-wars", "game.state.war-primary-opponent",
      "game.state.war-objectives", "game.state.war-objective-occupation",
      "game.state.war-objective-fort-level", "game.state.war-objective-garrison",
      "game.state.war-objective-siege-progress", "game.state.war-objective-assault",
      "game.state.player-armies", "game.state.army-routes",
      "game.command.query-army-strengths-v1",
      "game.command.query-title-holder-v1-N",
      kPlayerClaimsV1Capability,
      "game.command.query-pending-character-interaction-context-v1",
      "game.command.query-current-event-window-context-v1",
#if defined(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1)
      ck3_12003::kNormalExitMapV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1)
      ck3_12003::kGrantTitlePickerQueryV1Capability,
      ck3_12003::kGrantTitlePickerPrepareV1Capability,
      ck3_12003::kGrantTitlePickerSelectV1Capability,
      ck3_12003::kGrantTitlePickerSendV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1)
      ck3_12003::kOrdinaryInteractionQueryV1Capability,
      ck3_12003::kOrdinaryInteractionInitiateV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)
      ck3_11906::kIngameDecisionsOpenV1Capability,
      ck3_11906::kIngameDecisionItemQueryV1Capability,
#if defined(XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1)
      ck3_11906::kIngameDecisionItemSelectV1Capability,
      ck3_11906::kIngameDecisionItemConfirmV1Capability,
#if defined(XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1)
      ck3_11906::kIngameDecisionOutcomeConfirmV1Capability,
#endif
#endif
#endif
      "game.command.center-map-on-landed-title-v1",
      ck3_11906::kStewardDevelopCountyCandidatesV1Capability,
      "game.command.select-event-option-N",
      "game.command.accept-pending-character-interaction",
      "game.command.reject-pending-character-interaction",
      "game.command.acknowledge-pending-character-interaction",
      ck3_11906::kIngameUiNavigationV1Capability,
      ck3_11906::kIngameUiWindowQueryV1Capability,
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1) && \
    defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
      ck3_11906::kFrontendGuiRouteV1Capability,
      ck3_11906::kFrontendGuiTreeInspectionV1Capability,
      ck3_11906::kGuiWindowTreeInspectionV1Capability,
      ck3_11906::kFrontendGuiOpenNewGameV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1)
      ck3_11906::kFrontendBookmarkModelProbeV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
      ck3_11906::kFrontendGuiSelectSupported1066CharacterV1Capability,
      ck3_11906::kFrontendGuiStartSelectedBookmarkV1Capability,
#endif
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
      ck3_11906::kFrontendGameRulesV1Capability,
      ck3_11906::kFrontendOpenGameRulesV1Capability,
      ck3_11906::kFrontendGameRulesControlV1Capability,
      ck3_11906::kFrontendSelectGameRuleV1Capability,
      ck3_11906::kFrontendApplyGameRulesV1Capability,
      ck3_11906::kFrontendHideGameRulesV1Capability,
      ck3_11906::kFrontendAppliedGameRulesV1Capability,
#endif
      "game.command.query-route-contact-horizon-v1-N",
      "game.command.query-actual-contact-scope-v1-N",
      "game.command.query-projected-contact-scope-v1-N",
      ck3_12003::kArmyCommanderCandidatesCapability,
      ck3_12003::kArmyCommanderCandidatesForTargetCapability,
      ck3_12003::kArmyCommanderAssignmentCapability,
      "game.command.query-player-mercenary-context-v1",
      "game.command.hire-mercenary-v1", "game.command.hire-holy-order-v1",
      "game.command.query-loaded-feature-manifest-v1",
      ck3_11906::kTacticalDailySentinelCapabilityV1,
      ck3_11906::kTacticalDailySentinelStatusCapabilityV1,
      ck3_11906::kTacticalDailySentinelCancelCapabilityV1,
      "game.command.query-campaign-root-context-v1",
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
      "game.command.query-player-faction-alerts-v1",
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
      "game.command.query-war-prisoner-release-pairs-v1-N",
#endif
      "game.command.query-combat-simulation-inputs-v2-N",
      "game.command.query-player-default-raise-v1",
      "game.command.raise-troops-default",
      "game.command.preview-move-army-N-to-N",
      "game.command.move-army-N-to-N",
      "game.command.halt-army-N",
      "game.command.disband-army-N",
      "game.command.split-army-half-N",
      "game.command.merge-armies-N-with-N",
      "game.command.start-assault-N",
      "game.command.stop-assault-N",
      "game.command.query-battle-control-snapshot-v1-N",
      "game.command.query-battle-transition-v1-N",
      "game.command.query-battle-terminal-transition-v1",
      "game.command.query-battle-reinforcement-assignment-v1-N",
      "game.command.query-war-entry-assessments-v1-N",
      "game.command.query-declarable-wars",
      "game.command.declare-war-N",
      "game.command.enforce-demands-N",
      "game.command.query-arrange-marriage-choices",
      "game.command.arrange-marriage-N",
      "game.command.query-war-occupation-targets-v1-N",
      "game.command.query-war-termination-options-N",
      "game.command.query-war-termination-terms-v1-N",
      "game.command.surrender-war-N",
      "game.command.offer-white-peace-N",
      "game.adapter.exact-build",
      "game.adapter.minimized-headless",
      "game.command.pause-map", "game.command.resume-map",
      "game.command.set-speed-1", "game.command.set-speed-2",
      "game.command.set-speed-3", "game.command.set-speed-4",
      "game.command.set-speed-5", "game.command.save-checkpoint"});
  static const AdapterDescriptor descriptor{
      ck3_12004::kAdapterId, ck3_12004::kGameVersion,
      ck3_12004::kExecutableSha256, ck3_12002::kCheckpointSaveName,
      capabilities};
  return descriptor;
}

Ck3_12004AdapterBindings BindCk3_12004AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  Ck3_12004AdapterBindings bindings{};
  bindings.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  if (!bindings.core.enabled) return bindings;
  bindings.commands = ck3_12004::BindCommandImage12004(
      image_base, executable_sha256);
  bindings.events = ck3_12004::BindEventsImage(image_base, executable_sha256);
  bindings.marriage = ck3_12004::BindArrangeMarriageImage(
      image_base, executable_sha256, bindings.commands);
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  bindings.family = ck3_12004::BindFamilyImage(
      image_base, executable_sha256);
#endif
  bindings.combat = ck3_12004::BindCombatImage12004(
      image_base, executable_sha256);
  bindings.phase = ck3_12004::BindPhaseImage12004(
      image_base, executable_sha256);
  bindings.phase_event_calendar12004 =
      ck3_12004::BindPhaseEventCalendarImage12004(image_base, executable_sha256);
  bindings.phase_event_role_compatibility12004 =
      ck3_12004::BindPhaseEventRoleImage12004(image_base, executable_sha256);
  bindings.military = ck3_12004::BindMilitaryImage12004(
      image_base, executable_sha256, bindings.commands);
  bindings.native_maa_recruitment =
      ck3_12004::BindNativeMaaRecruitmentImage12004(
          image_base, executable_sha256);
  bindings.native_maa_create = ck3_12004::BindNativeMaaCreateImage12004(
      image_base, executable_sha256);
  // The concrete adapter repairs this borrow after moving the bundle.
  bindings.military.submit_context = nullptr;
  bindings.armies = ck3_12004::BindArmyImage12004(image_base, executable_sha256);
  bindings.movement_routes = ck3_12004::BindRouteImage12004(
      image_base, executable_sha256);
  bindings.owned_regiments.persistent_regiment_storage_slot =
      bindings.armies.persistent_regiment_storage_slot;
  bindings.owned_regiments.read_type = ck3_12002::ReadOwnedRegimentTypeV1;
  bindings.world = ck3_12004::BindWorldImage12004(image_base, executable_sha256);
  bindings.provinces = ck3_12004::BindProvinceImage12004(
      image_base, executable_sha256, bindings.armies);
  bindings.diplomacy = ck3_12004::BindDiplomacyImage(
      image_base, executable_sha256, bindings.core, bindings.commands);
  bindings.declarations = ck3_12004::BindDeclarationsImage12004(
      image_base, executable_sha256, bindings.commands);
  bindings.player_claims12004 = ck3_12004::BindPlayerClaimsImageV1(
      image_base, executable_sha256, bindings.core, bindings.provinces);
  bindings.terms = ck3_12004::BindClaimTermsImage(
      image_base, executable_sha256, bindings.core, bindings.world,
      bindings.provinces);
  try {
    bindings.snapshot_foundation12004 =
        std::make_shared<const ck3_12004::SnapshotFoundationBindings>(
            ck3_12004::BindSnapshotFoundationImage(image_base, executable_sha256));
  } catch (...) {
    // The independent core observation remains available if the software
    // snapshot bundle cannot be allocated.
    bindings.snapshot_foundation12004.reset();
  }
  return bindings;
}

bool ReadCk3_12004Snapshot(const Ck3_12004AdapterBindings &bindings,
                         Snapshot &output) noexcept {
  output = {};
  ck3_12004::CoreSnapshotPrefix prefix{};
  if (bindings.read_core_snapshot == nullptr ||
      !bindings.read_core_snapshot(bindings.core, prefix)) return false;
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
    output = std::move(observed);
    return true;
  }
  const auto &foundation = bindings.snapshot_foundation12004;
  if (!foundation) return false;
  if (prefix.has_played_character) {
    ck3_12004::ActorResourceBalances resources{};
    if (!ck3_12004::ReadActorResourceBalances(
            bindings.core, prefix.played_character_id, resources)) return false;
    observed.played_character_gold.raw = resources.gold_raw;
    observed.played_character_prestige.raw = resources.prestige_raw;
    observed.played_character_piety.raw = resources.piety_raw;
    observed.played_character_stress_points = resources.stress_points;
    PlayedCharacterRelationships12002 relationships{};
    if (!ck3_12004::ReadPlayedCharacterRelationships(
            bindings.core, prefix.played_character_id, relationships)) return false;
    observed.played_character_betrothed_id = relationships.betrothed_character_id;
    observed.played_character_primary_spouse_id =
        relationships.primary_spouse_character_id;
    observed.played_character_spouse_ids =
        std::move(relationships.spouse_character_ids);
    auto event_traits = foundation->event_traits;
    event_traits.core = bindings.core;
    ck3_12004::person_events::PlayerEventTraitMembershipV1 membership;
    ck3_12004::person_events::ReadPlayerEventTraitMembershipForSnapshotV1(
        event_traits, prefix.clock.date_raw, prefix.played_character_id, membership);
    observed.played_character_event_trait_membership = std::move(membership);
  }
  auto events = foundation->events;
  events.core = bindings.core;
  if (!ck3_12004::ReadEventsSnapshot(events, observed) ||
      ck3_12004::ReadWorldSnapshot12004(bindings.world, bindings.armies,
          bindings.provinces, prefix, observed) !=
              ck3_12004::WorldReadResult::available) return false;
  const auto settlement = ck3_12004::ReadSettlement(
      foundation->settlement, bindings.core, observed);
  if (settlement != ck3_12004::SettlementReadResult::published &&
      settlement != ck3_12004::SettlementReadResult::not_published) return false;
  output = std::move(observed);
  return true;
}

std::unique_ptr<GameAdapter> CreateCk3_12004AdapterFromBindings(
    Ck3_12004AdapterBindings bindings) noexcept {
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  return CreateCrozierAdapterFromBindings(
      std::move(bindings), Ck3_12004AdapterDescriptor());
}

std::unique_ptr<GameAdapter> CreateCk3_12004Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12004AdapterFromBindings(BindCk3_12004AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      executable_sha256));
}

std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (!IsCk3_12004Descriptor(descriptor)) return serialized;
  serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
  // The shared event-window serializer retains its historical .2 locator.
  // The independently mapped .4 factory uses 0x44BC418 (SOURCE-CLOSURE.json).
  if (serialized.find("\"schema\":\"current-event-window-context-v1\"") !=
      std::string::npos) {
    ReplaceIdentityToken(serialized,
        "\"idler_vtable_rva\":\"0x44BC408\"",
        "\"idler_vtable_rva\":\"0x44BC418\"");
  }
  for (const auto old_version : {"1.20.0.2", "1.20.0.3"}) {
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"" + old_version + "\"",
          std::string("\"") + key + "\":\"1.20.0.4\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"ck3-" + old_version + "-",
          std::string("\"") + key + "\":\"ck3-1.20.0.4-");
    }
    ReplaceIdentityToken(serialized,
        std::string("\"adapter_id\":\"ck3-") + old_version + "-msvc-x64\"",
        "\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\"");
    ReplaceIdentityToken(serialized,
        std::string("\"played-character-event-icon-indicators-") + old_version + "-v1\"",
        "\"played-character-event-icon-indicators-1.20.0.4-v1\"");
  }
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12004_");
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12003_", "\"schema\":\"ck3_12004_");
  // Confucian DTO schemas describe the shared semantic wire contract, not the
  // executable build. Their exact Python/reader normalizers retain these names.
  for (const auto schema : {"confucian_assembly_predicates_v1",
                           "confucian_religious_title_v1",
                           "confucian_challenger_graph_v1"}) {
    ReplaceIdentityToken(serialized,
        std::string("\"schema\":\"ck3_12004_") + schema + "\"",
        std::string("\"schema\":\"ck3_12003_") + schema + "\"");
  }
  // This nested Army semantic contract is independent of executable identity.
  // Its production normalizer and shared serializer retain the canonical name.
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12004_owned_regiments_v1\"",
      "\"schema\":\"ck3_12003_owned_regiments_v1\"");
  // Knight semantic contracts retain their canonical schema across builds.
  // The actual V2 consumer rejected a rewritten effectiveness schema in R0060.
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_effectiveness_context_v1\"",
      "\"schema\":\"ck3_12003_knight_effectiveness_context_v1\"");
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_current_model_association_v1\"",
      "\"schema\":\"ck3_12003_knight_current_model_association_v1\"");
  for (const auto old_hash : {std::string_view(ck3_12002::kExecutableSha256),
                            std::string_view(ck3_12003::kExecutableSha256)}) {
    ReplaceIdentityToken(serialized, std::string("\"") + std::string(old_hash) + "\"",
        std::string("\"") + ck3_12004::kExecutableSha256 + "\"");
  }
  for (const auto old_hash : {
      "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"}) {
    ReplaceIdentityToken(serialized, std::string("\"") + old_hash + "\"",
        "\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"");
  }
  return serialized;
}
} // namespace xar::game
