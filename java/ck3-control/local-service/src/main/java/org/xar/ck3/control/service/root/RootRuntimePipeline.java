package org.xar.ck3.control.service.root;

import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure assembly of the actual 34 producers and actual domain publication outcomes. */
public final class RootRuntimePipeline {
    private RootRuntimePipeline() { }
    private static EnumMap<PlanningStage,OrdinaryPolicy> selected(List<RootDomainInstallation> domains) {
        var result=new EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var domain:List.copyOf(domains))for(var policy:domain.policies()) {
            Objects.requireNonNull(policy);StrictJson.require(policy.implementationSource().bytes()>0,"actual policy source required");
            StrictJson.require(result.putIfAbsent(policy.stage(),policy)==null,"two actual producers claim one ordinary planning stage");
        }
        return result;
    }
    public static Set<PlanningStage> missing(List<RootDomainInstallation> domains) {
        var result=EnumSet.allOf(PlanningStage.class);result.removeAll(selected(domains).keySet());return Set.copyOf(result);
    }
    public static OrdinaryPlanningPipeline assemble(List<RootDomainInstallation> domains) {
        var required=selected(domains);var missing=EnumSet.allOf(PlanningStage.class);missing.removeAll(required.keySet());
        StrictJson.require(missing.isEmpty(),"actual full ordinary pipeline is unavailable; missing "+missing);
        StrictJson.require(required.get(PlanningStage.ORDINARY_CORE) instanceof OrdinaryCorePolicy,"actual shared ordinary core required");
        StrictJson.require(required.get(PlanningStage.REALM_MEMBERSHIP_PUBLICATION) instanceof M7CampaignPolicies.RealmLifecycle,
                "actual source-aware M7 realm publication required");
        var core=(OrdinaryCorePolicy)required.get(PlanningStage.ORDINARY_CORE);
        var realm=(M7CampaignPolicies.RealmLifecycle)required.get(PlanningStage.REALM_MEMBERSHIP_PUBLICATION);
        return new OrdinaryPlanningPipeline(
                required.get(PlanningStage.SUCCESSION_PREFLIGHT),
                required.get(PlanningStage.PENDING_MATERIAL_PUBLICATION),
                required.get(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS),
                required.get(PlanningStage.OPENING_LIFESTYLE_FOCUS),
                core,
                required.get(PlanningStage.THREE_WAY_WAR_EXIT),
                required.get(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION),
                required.get(PlanningStage.WAR_RENDEZVOUS),
                required.get(PlanningStage.SIEGE_AND_BATTLE_FORECAST),
                required.get(PlanningStage.ROUTE_ORIGIN_EXPOSURE),
                required.get(PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS),
                required.get(PlanningStage.ORDINARY_RETREAT),
                required.get(PlanningStage.WAR_MERCENARY_CURRENT_CASH),
                required.get(PlanningStage.PRISONER_RELEASE_DISCOVERY),
                required.get(PlanningStage.HOLY_ORDER_REINFORCEMENT),
                required.get(PlanningStage.COMMANDER_QUALITY),
                required.get(PlanningStage.M5_JOINT_PEACETIME),
                required.get(PlanningStage.LIFESTYLE),
                required.get(PlanningStage.FACTION_GIFT),
                required.get(PlanningStage.CONSTRUCTION),
                required.get(PlanningStage.FAMILY_AND_EDUCATION),
                required.get(PlanningStage.PRISONER_RANSOM),
                required.get(PlanningStage.PRISONER_RELEASE),
                required.get(PlanningStage.M5_WARTIME_OBSERVATION),
                required.get(PlanningStage.COUNCIL),
                required.get(PlanningStage.CROWN_AUTHORITY),
                required.get(PlanningStage.FEAST),
                required.get(PlanningStage.DEFERRED_SUCCESSION_ROOT),
                required.get(PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION),
                required.get(PlanningStage.PREWAR_FORCE_COALITION),
                required.get(PlanningStage.ORDINARY_SWAY),
                required.get(PlanningStage.EVENT_MATERIAL_POSTCONDITION),
                required.get(PlanningStage.CAMPAIGN_ADVANCE_CAP),
                realm);
    }
    /** Stop immediately on an authoritative head change; the next producer needs a new observation. */
    public static final class Completion implements OrdinaryPlanCompletion {
        private final List<OrdinaryPlanCompletion> actual;
        public Completion(List<OrdinaryPlanCompletion> actual) { this.actual=List.copyOf(actual);this.actual.forEach(Objects::requireNonNull); }
        @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
            AwaitingOutcome waiting=null;
            for(var producer:actual) {
                var result=Objects.requireNonNull(producer.afterPlanning(original,planned));
                if(!(result instanceof Unchanged) && !(result instanceof AwaitingOutcome))return result;
                if(result instanceof AwaitingOutcome next) {
                    StrictJson.require(waiting==null || waiting.command().equals(next.command()),"domain completions retained different exact commands");
                    waiting=next;
                }
            }
            return waiting==null?new Unchanged("actual domain completions published no changed head"):waiting;
        }
        @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) {
            for(var producer:actual) {
                var result=Objects.requireNonNull(producer.afterExecution(receipt));
                if(!(result instanceof Unchanged))return result;
            }
            return new Unchanged("actual domain outcomes published no changed head");
        }
    }
}

