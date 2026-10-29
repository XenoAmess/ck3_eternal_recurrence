package org.xar.ck3.control.application.planning;

import java.time.Clock;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Complete composition of actual ordinary producers. This is not a second
 * scheduler: OrdinaryPlanner owns execution order and all action admission.
 * Constructing this record grants no native qualification or migration credit.
 */
public record OrdinaryPlanningPipeline(
        OrdinaryPolicy successionPreflight,
        OrdinaryPolicy pendingMaterialPublication,
        OrdinaryPolicy terminalAndForegroundWindows,
        OrdinaryPolicy openingLifestyleFocus,
        OrdinaryCorePolicy ordinaryCore,
        OrdinaryPolicy threeWayWarExit,
        OrdinaryPolicy eventAndInteractionContinuation,
        OrdinaryPolicy warRendezvous,
        OrdinaryPolicy siegeAndBattleForecast,
        OrdinaryPolicy routeOriginExposure,
        OrdinaryPolicy activeCombatAndDateGuards,
        OrdinaryPolicy ordinaryRetreat,
        OrdinaryPolicy warMercenaryCurrentCash,
        OrdinaryPolicy prisonerReleaseDiscovery,
        OrdinaryPolicy holyOrderReinforcement,
        OrdinaryPolicy commanderQuality,
        OrdinaryPolicy m5JointPeacetime,
        OrdinaryPolicy lifestyle,
        OrdinaryPolicy factionGift,
        OrdinaryPolicy construction,
        OrdinaryPolicy familyAndEducation,
        OrdinaryPolicy prisonerRansom,
        OrdinaryPolicy prisonerRelease,
        OrdinaryPolicy m5WartimeObservation,
        OrdinaryPolicy council,
        OrdinaryPolicy crownAuthority,
        OrdinaryPolicy feast,
        OrdinaryPolicy deferredSuccessionRoot,
        OrdinaryPolicy holyWarDefenderObservation,
        OrdinaryPolicy prewarForceCoalition,
        OrdinaryPolicy ordinarySway,
        OrdinaryPolicy eventMaterialPostcondition,
        OrdinaryPolicy campaignAdvanceCap,
        RealmLifecycle realmMembershipPublication) {
    public OrdinaryPlanningPipeline {
        stage(successionPreflight, PlanningStage.SUCCESSION_PREFLIGHT);
        stage(pendingMaterialPublication, PlanningStage.PENDING_MATERIAL_PUBLICATION);
        stage(terminalAndForegroundWindows, PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS);
        stage(openingLifestyleFocus, PlanningStage.OPENING_LIFESTYLE_FOCUS);
        stage(ordinaryCore, PlanningStage.ORDINARY_CORE);
        stage(threeWayWarExit, PlanningStage.THREE_WAY_WAR_EXIT);
        stage(eventAndInteractionContinuation, PlanningStage.EVENT_AND_INTERACTION_CONTINUATION);
        stage(warRendezvous, PlanningStage.WAR_RENDEZVOUS);
        stage(siegeAndBattleForecast, PlanningStage.SIEGE_AND_BATTLE_FORECAST);
        stage(routeOriginExposure, PlanningStage.ROUTE_ORIGIN_EXPOSURE);
        stage(activeCombatAndDateGuards, PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS);
        stage(ordinaryRetreat, PlanningStage.ORDINARY_RETREAT);
        stage(warMercenaryCurrentCash, PlanningStage.WAR_MERCENARY_CURRENT_CASH);
        stage(prisonerReleaseDiscovery, PlanningStage.PRISONER_RELEASE_DISCOVERY);
        stage(holyOrderReinforcement, PlanningStage.HOLY_ORDER_REINFORCEMENT);
        stage(commanderQuality, PlanningStage.COMMANDER_QUALITY);
        stage(m5JointPeacetime, PlanningStage.M5_JOINT_PEACETIME);
        stage(lifestyle, PlanningStage.LIFESTYLE);
        stage(factionGift, PlanningStage.FACTION_GIFT);
        stage(construction, PlanningStage.CONSTRUCTION);
        stage(familyAndEducation, PlanningStage.FAMILY_AND_EDUCATION);
        stage(prisonerRansom, PlanningStage.PRISONER_RANSOM);
        stage(prisonerRelease, PlanningStage.PRISONER_RELEASE);
        stage(m5WartimeObservation, PlanningStage.M5_WARTIME_OBSERVATION);
        stage(council, PlanningStage.COUNCIL);
        stage(crownAuthority, PlanningStage.CROWN_AUTHORITY);
        stage(feast, PlanningStage.FEAST);
        stage(deferredSuccessionRoot, PlanningStage.DEFERRED_SUCCESSION_ROOT);
        stage(holyWarDefenderObservation, PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION);
        stage(prewarForceCoalition, PlanningStage.PREWAR_FORCE_COALITION);
        stage(ordinarySway, PlanningStage.ORDINARY_SWAY);
        stage(eventMaterialPostcondition, PlanningStage.EVENT_MATERIAL_POSTCONDITION);
        stage(campaignAdvanceCap, PlanningStage.CAMPAIGN_ADVANCE_CAP);
        stage(realmMembershipPublication, PlanningStage.REALM_MEMBERSHIP_PUBLICATION);
    }

    public List<OrdinaryPolicy> policies() {
        return List.of(successionPreflight, pendingMaterialPublication, terminalAndForegroundWindows,
                openingLifestyleFocus, ordinaryCore, threeWayWarExit, eventAndInteractionContinuation,
                warRendezvous, siegeAndBattleForecast, routeOriginExposure, activeCombatAndDateGuards,
                ordinaryRetreat, warMercenaryCurrentCash, prisonerReleaseDiscovery, holyOrderReinforcement,
                commanderQuality, m5JointPeacetime, lifestyle, factionGift, construction, familyAndEducation,
                prisonerRansom, prisonerRelease, m5WartimeObservation, council, crownAuthority, feast,
                deferredSuccessionRoot, holyWarDefenderObservation, prewarForceCoalition, ordinarySway,
                eventMaterialPostcondition, campaignAdvanceCap, realmMembershipPublication);
    }

    public OrdinaryPlanner create(Clock clock) {
        OrdinaryPlanner planner = new OrdinaryPlanner(policies(), Objects.requireNonNull(clock), realmMembershipPublication);
        StrictJson.require(planner.missingStages().isEmpty(), "complete actual ordinary producer set required");
        return planner;
    }

    private static void stage(OrdinaryPolicy producer, PlanningStage expected) {
        Objects.requireNonNull(producer, "actual ordinary producer required for " + expected);
        StrictJson.require(producer.stage() == expected, "ordinary producer installed at the wrong stage: " + expected);

    }
}
