package org.xar.ck3.control.application.planning.warentry;

import static org.xar.ck3.control.application.planning.warentry.WarEntryJson.*;
import static org.xar.ck3.control.application.planning.warentry.WarEntryCandidates.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.capabilities.CapabilityFlags;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.prewaradmission.OrdinaryPrewarAdmission;

/** The original ordinary-policy peacetime branch, at strategy.py 15151-15764. No submission authority. */
public final class PeacetimeWarEntryPlanner {
    @FunctionalInterface public interface CommandFactory {
        CommandProposal propose(PlanningRequest request,String selectedStep,Obj completePlan);
    }
    public sealed interface CommandProposal permits Ready,Unavailable { }
    public record Ready(ActionCommand command) implements CommandProposal {public Ready {Objects.requireNonNull(command);}}
    public record Unavailable(String missingProducer) implements CommandProposal {public Unavailable {if(Objects.requireNonNull(missingProducer).isBlank())throw new IllegalArgumentException("specific missing producer required");}}
    private final CommandFactory commands;
    public PeacetimeWarEntryPlanner(CommandFactory commands) {this.commands=Objects.requireNonNull(commands);}

    public OrdinaryPolicy.Decision evaluate(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        Objects.requireNonNull(request);Objects.requireNonNull(previous);
        Set<String> steps=request.observations().actionSteps().stream().map(key->key.value()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        final Optional<Obj> selected;
        try {selected=select(request.observations().snapshot(),request.observations().history(),steps);}
        catch(IllegalArgumentException | NullPointerException invalid) {return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INVALID_FRAME,"peacetime war-entry producer input rejected: "+invalid.getMessage());}
        if(selected.isEmpty())return new OrdinaryPolicy.NotApplicable("the original peacetime war-entry branch has no declaration/discovery opportunity");
        Obj plan=selected.orElseThrow();String step=text(plan.get("selected_step"));Optional<ActionCommand> command=Optional.empty();
        if(step!=null) {
            CommandProposal proposal=Objects.requireNonNull(commands.propose(request,step,plan),"command factory must report Ready or concrete Unavailable");
            if(proposal instanceof Unavailable missing)return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,"peacetime selected "+step+"; missing actual producer: "+missing.missingProducer());
            ActionCommand actual=((Ready)proposal).command();
            if(!actual.before().equals(request.before()) || !actual.source().equals(request.source()) || !actual.sessionId().equals(request.sessionId()) || !actual.operation().value().equals(step) || !actual.deadline().equals(request.deadline()))return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INVALID_FRAME,"peacetime command factory changed source/frame/session/operation/deadline binding");
            command=Optional.of(actual);
        }
        OrdinaryPolicy.Purpose purpose=step==null || step.startsWith("query-")?OrdinaryPolicy.Purpose.READ_ONLY:WarEntryHistoryAdvance.isAdvance(step)?OrdinaryPolicy.Purpose.DATE_ADVANCE:OrdinaryPolicy.Purpose.WORLD_ACTION;
        String reason=Objects.requireNonNull(text(plan.get("reason")));
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft("one-life-turn-v1",text(plan.get("phase")),reason,OrdinaryPolicy.Kind.ORDINARY,command,purpose,Optional.empty(),plan),reason);
    }

    /** Pure actual selector. Original NO_DECLARE decisions require their original input mismatch; no Java-glue veto. */
    public static Optional<Obj> select(Obj snapshot,List<Obj> history,Set<String> steps) {
        Objects.requireNonNull(snapshot);history=List.copyOf(history);steps=Set.copyOf(steps);
        for(Obj row:history)if(row.get("index")!=null && !(row.get("index") instanceof Nil) && !(row.get("index") instanceof IntegerValue))throw new IllegalArgumentException("history index must use an exact integer token");
        Obj cooldown=postwarCooldown(snapshot,history);
        if(cooldown!=null)return Optional.of(progress(steps,"native_postwar_reentry_cooldown","the previous terminal war action has materialized; keep the verified peaceful state for the bounded 30-day horizon before considering another declaration","the previous terminal war action is inside its peaceful re-entry horizon, but this backend cannot advance time").value("postwar_reentry",cooldown).build());
        Obj continuity=child(snapshot,"war_declaration_continuity_v1");
        if(continuity!=null && is(continuity.get("schema"),"war-declaration-continuity-v1") && !is(continuity.get("status"),"war_started") && !is(continuity.get("status"),"native_rejected") && !is(continuity.get("status"),"not_submitted")) {
            boolean advance=is(continuity.get("status"),"declaration_submitted") && is(continuity.get("native_response"),"accepted") && no(continuity.get("in_flight")) && WarEntryCollector.latest(history,"declare-war-",true,false).compareTo(WarEntryCollector.latestAdvance(history))>0 && steps.contains("life-advance");
            return Optional.of(plan("native_war_declaration_pending",advance?"life-advance":null,"retain the original declaration until its native response and unique actual war identity resolve; never submit another declaration").text("status","pending").value("war_declaration_continuity_v1",continuity).bool("request_retried",false).build());
        }
        BigInteger lifeIndex=WarEntryCollector.latestAdvance(history);
        if(WarEntryCollector.latest(history,"declare-war-",true,true).compareTo(lifeIndex)>0)return Optional.of(progress(steps,"native_war_declaration_progress","the native declaration was submitted; advance once for the war state to materialize","the native declaration was submitted but this backend cannot advance the map").build());
        Obj discoveryCooldown=child(snapshot,"declaration_opportunity_cooldown_v1");boolean peace=snapshot.get("active_wars") instanceof Arr && array(snapshot.get("active_wars")).isEmpty();
        if(discoveryCooldown!=null && is(discoveryCooldown.get("status"),"active") && peace)return Optional.of(progress(steps,"native_war_discovery_cooldown","two completed declaration queries caused no actual declaration; wait one game month","declaration opportunity cooldown is active but date advance is unavailable").value("declaration_opportunity_cooldown_v1",discoveryCooldown).build());
        WarEntryCollector.Collected collected=WarEntryCollector.collect(snapshot,history);
        List<Obj> declarations=collected.declarations();Map<BigInteger,Obj> assessments=collected.assessments();Obj root=collected.campaignRoot().orElse(null);
        BigInteger actor=number(child(snapshot,"played_character"),"character_id");List<Obj> claims=playerClaims(declarations,actor);
        if(!claims.isEmpty() && peace) {
            if(root==null && steps.contains("query-campaign-root-context-v1"))return Optional.of(plan("native_player_claim_scope_assessment","query-campaign-root-context-v1","read the same-frame feudal, independence, adjacency, county and peacetime-budget scope before evaluating player claims").value("claim_declarations",rows(claims)).build());
            if(!claimScopeReady(root))return Optional.of(plan("native_player_claim_evidence_required",advance(steps),"player claims are final-legal, but the same-frame adjacent independent county scope is incomplete; choose NO_DECLARE").value("decision",noDeclare(CLAIM_RULE)).value("claim_declarations",rows(claims)).build());
            List<Obj> bounded=adjacentClaims(claims,root);List<BigInteger> missing=bounded.stream().map(row->required(row,"target_character_id")).filter(target->!assessments.containsKey(target)).distinct().sorted().toList();
            if(!missing.isEmpty()) {
                final Set<String> assessmentSteps=steps;
                BigInteger target=missing.stream().filter(value->assessmentSteps.contains(assessmentStep(value))).findFirst().orElse(missing.getFirst());String query=assessmentStep(target);
                if(query!=null && steps.contains(query)) {
                    Obj declaration=bounded.stream().filter(row->target.equals(number(row,"target_character_id"))).findFirst().orElseThrow();
                    return Optional.of(plan("native_player_claim_power_assessment",query,"read every same-frame adjacent independent county claim target before comparing complete native power totals").value("declaration",declaration).value("remaining_unassessed_target_character_ids",numbers(missing)).build());
                }
                return Optional.of(plan("native_player_claim_evidence_required",advance(steps),"one or more adjacent independent county claims lack a same-frame native power assessment; choose NO_DECLARE").value("decision",noDeclare(CLAIM_RULE)).value("missing_target_character_ids",numbers(missing)).build());
            }
            if(!bounded.isEmpty()) {Obj candidate=claim(bounded,assessments,root,steps,peace);if(is(candidate.get("status"),"forecast_required"))return Optional.of(forecastPlan(child(candidate,"declaration"),child(candidate,"assessment"),candidate,root,steps,snapshot));}
        }
        Obj declaration=WarEntryCollector.preferred(declarations,assessments,actor);
        if(declaration!=null) {
            BigInteger target=number(declaration,"target_character_id");String query=assessmentStep(target);Obj assessment=assessments.get(target);boolean fresh=assessment!=null;
            if(!fresh && query!=null && steps.contains(query))return Optional.of(plan("native_war_entry_assessment",query,"read CK3's exact strategic power lane for the current declaration target before considering time advance or war").value("declaration",declaration).build());
            Obj power=powerProjection(assessment);
            if(!fresh)return Optional.of(deferred(steps,declaration,null,power,List.of("fresh_power_assessment"),null,"the native declaration is legal, but its same-frame native power assessment is missing and cannot be queried now; choose NO_DECLARE and refresh before reconsidering").text("required_step",query).value("missing_fields",strings(List.of("war_entry_assessment"))).build());
            if(required(assessment,"actor_power_base_raw").compareTo(required(assessment,"target_power_total_raw"))<0 && !yes(WarEntryForceAdmission.assess(snapshot,declaration).get("declare_admitted"))) {
                List<Obj> unassessed=declarations.stream().filter(row->number(row,"target_character_id")!=null && !assessments.containsKey(number(row,"target_character_id"))).toList();
                Obj alternative=WarEntryCollector.preferred(unassessed,Map.of(),actor);String alternativeQuery=assessmentStep(number(alternative,"target_character_id"));
                if(alternativeQuery!=null && steps.contains(alternativeQuery))return Optional.of(plan("native_war_entry_assessment_alternative",alternativeQuery,"the current target depends on more strategic power than the actor's own adjusted base; inspect the next legal target on the same paused frame before choosing a diagnostic war-entry candidate").value("declaration",alternative).value("rejected_power_declaration",declaration).value("rejected_war_entry_assessment",assessment).value("rejected_war_entry_expected_utility",power).build());
            }
            Obj candidate=deJure(declaration,assessment,root,steps,peace);
            if(is(candidate.get("status"),"forecast_required"))return Optional.of(forecastPlan(declaration,assessment,candidate,root,steps,snapshot));
            String typed=typedStep(declaration);boolean economic=yes(get(root,"independent")) && feudal(root,false) && economic(root,false);
            BigInteger claimant=number(declaration,"claimant_character_id");boolean claimantValid=!is(declaration.get("casus_belli_key"),"claim_cb") || (claimant!=null && claimant.signum()>0 && claimant.equals(number(root,"player_character_id")));
            Obj alert=collected.factionAlert().orElse(null),faction=WarEntryCollector.factionContext(root,alert);
            boolean generalReady=peace && fresh && economic && claimantValid && is(declaration.get("source"),"native") && typed!=null && steps.contains(typed);
            if(generalReady && alert==null && steps.contains("query-player-faction-alerts-v1"))return Optional.of(plan("native_war_entry_faction_assessment","query-player-faction-alerts-v1","read current targeting and county-exposure faction danger before the bounded battle prior").value("declaration",declaration).value("war_entry_assessment",assessment).value("war_entry_faction_context",faction).value("required_capabilities",strings(List.of(CapabilityFlags.PLAYER_FACTION_ALERTS_V1_QUERY_SUPPORTED.capability()))).build());
            if(generalReady && yes(faction.get("prior_scope_eligible"))) {
                Obj general=obj().text("rule_id","general-native-war-entry-battle-prior-v1").text("typed_declaration_step",typed).bool("typed_declaration_available",true).text("status","forecast_required").build();
                return Optional.of(forecastPlan(declaration,assessment,general,root,steps,snapshot).with("war_entry_faction_context",faction));
            }
            List<String> blockers=new ArrayList<>();if(!peace)blockers.add("at_peace");if(!fresh)blockers.add("fresh_power_assessment");if(!economic)blockers.add("independent_feudal_economic_scope");if(!yes(faction.get("prior_scope_eligible")))blockers.add("current_faction_alert_"+text(faction.get("status")));if(!claimantValid)blockers.add("claimant_identity");if(!is(declaration.get("source"),"native"))blockers.add("native_declaration");if(typed==null || !steps.contains(typed))blockers.add("typed_declaration_available");
            String reason=generalReady && is(faction.get("status"),"dangerous")?"the current faction alert reports a dangerous threat; defer the bounded battle prior":generalReady && is(faction.get("status"),"unavailable")?"current faction-alert inputs are unavailable; choose NO_DECLARE and refresh after one bounded interval":"the native declaration is legal but does not satisfy the bounded battle prior's same-frame strategy scope; choose NO_DECLARE and reassess after one bounded interval";
            if(!steps.contains("life-advance"))reason="the native declaration is legal but does not satisfy the bounded battle prior's same-frame strategy scope";
            return Optional.of(deferred(steps,declaration,assessment,power,blockers,faction,reason).build());
        }
        if(steps.contains("query-declarable-wars")) {
            if(WarEntryCollector.latest(history,"query-declarable-wars",false,true).compareTo(lifeIndex)>0 && steps.contains("life-advance"))return Optional.of(plan("native_war_discovery_progress","life-advance","no war was currently declarable; advance once before the next native query").build());
            return Optional.of(plan("native_war_discovery","query-declarable-wars","enumerate current native war declarations before using visual diplomacy").build());
        }
        return Optional.empty();
    }
    private static Builder plan(String phase,String step,String reason) {return obj().text("policy","one-life-turn-v1").text("phase",phase).text("selected_step",step).text("reason",reason);}
    private static String advance(Set<String> steps) {return steps.contains("life-advance")?"life-advance":null;}
    private static Builder progress(Set<String> steps,String phase,String reason,String unavailable) {boolean can=steps.contains("life-advance");Builder result=plan(can?phase:phase+"_unsupported",can?"life-advance":null,can?reason:unavailable);return can?result:result.text("required_step","life-advance");}
    private static Obj noDeclare(String policy) {return obj().text("policy",policy).text("outcome","NO_DECLARE").bool("automatic_declaration_enabled",false).build();}
    private static Builder deferred(Set<String> steps,Obj declaration,Obj assessment,Obj power,List<String> blockers,Obj faction,String reason) {
        String advance=advance(steps);Builder result=plan(advance!=null?"native_war_entry_no_declare":"native_war_entry_evidence_required",advance,reason);
        if(advance!=null || assessment==null)result.value("decision",obj().text("policy","war-entry-minimal-defer-v1").text("outcome","NO_DECLARE").value("declaration_id",declaration.get("declaration_id")).value("target_character_id",declaration.get("target_character_id")).value("casus_belli_key",declaration.get("casus_belli_key")).bool("native_power_assessment_consumed",assessment!=null).value("eu_lower_raw",power.get("eu_lower_raw")).text("advance_contract",advance==null?null:"native_life_advance").bool("automatic_declaration_enabled",false).bool("native_ai_equivalent",false).bool("semantic_optimal",false).value("missing_components",power.get("missing_components")).build());
        result.value("required_capabilities",strings(List.of("game.command.query-combat-simulation-inputs-v3-N","game.forecast.combat-monte-carlo-v1","game.command.query-war-entry-assessments-v1-N"))).value("general_battle_prior_scope_blockers",strings(blockers)).value("declaration",declaration).value("war_entry_assessment",assessment).value("war_entry_expected_utility",power);
        if(faction!=null)result.value("war_entry_faction_context",faction);return result;
    }
    private static Obj forecastPlan(Obj declaration,Obj assessment,Obj candidate,Obj root,Set<String> steps,Obj snapshot) {
        Obj forecast=PrewarBattlePrior.forecast(assessment,text(declaration.get("declaration_id"))),admission=PrewarBattlePrior.admission(forecast),force=WarEntryForceAdmission.assess(snapshot,declaration);String typed=text(candidate.get("typed_declaration_step"));
        boolean typedAvailable=yes(candidate.get("typed_declaration_available")) && typed!=null && steps.contains(typed),declare=yes(force.get("declare_admitted")) && typedAvailable;
        String advance=advance(steps),policy=text(candidate.get("rule_id"));
        Builder decision=obj().text("policy",policy).text("outcome",declare?"DECLARE":"NO_DECLARE").value("declaration_id",declaration.get("declaration_id")).value("target_character_id",declaration.get("target_character_id")).value("casus_belli_key",declaration.get("casus_belli_key")).value("claimant_character_id",declaration.get("claimant_character_id")).bool("native_power_assessment_consumed",true).bool("automatic_declaration_enabled",declare);
        if(declare)decision.value("forecast_model_fidelity",forecast.get("model_fidelity")).bool("force_risk_qualified",true).value("force_risk_policy",get(child(force,"force_risk"),"policy"));
        else decision.bool("campaign_root_context_consumed",true).bool("force_coalition_coverage_required",is(force.get("status"),"unknown")).value("eu_lower_raw",null).text("advance_contract",advance==null?null:"native_life_advance");
        Builder result=plan(declare?"native_war_declaration":"native_war_entry_forecast_required",declare?typed:advance,declare?"the same-frame legal declaration has complete executable force and potential enemy coverage within the current force risk budget":"the current force and coalition evaluation does not authorize this declaration: "+text(force.get("reason"))).value("decision",decision.build()).value("declaration",declaration).value("selected_declaration",WarEntryForceAdmission.selectedDeclaration(declaration)).value("war_entry_assessment",assessment).value("war_entry_candidate",candidate).value("prewar_battle_forecast",forecast).value("prewar_forecast_admission",admission).bool("prewar_forecast_admission_available",is(forecast.get("status"),"estimated")).value("prewar_force_admission",force);
        if(!declare)result.value("required_capabilities",strings(List.of(OrdinaryPrewarAdmission.CAPABILITY))).value("required_prewar_force_coalition_query",typedAvailable?force.get("required_prewar_force_coalition_query"):null).value("war_entry_expected_utility",powerProjection(assessment)).value("campaign_root_context",project(root,"snapshot_revision","date_raw","player_character_id","independent","government","player_monthly_gold_income","player_domain_size","player_domain_limit","player_targeting_faction_count"));
        return result.build();
    }
    private static Obj postwarCooldown(Obj snapshot,List<Obj> history) {
        BigInteger now=number(snapshot,"date_raw");if(now==null)return null;
        Set<BigInteger> wars=objects(snapshot.get("active_wars")).stream().map(row->number(row,"war_id")).filter(Objects::nonNull).collect(java.util.stream.Collectors.toSet());
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);String command=WarEntryCollector.effectiveCommand(row);if(command==null || !(command.startsWith("offer-white-peace-") || command.startsWith("surrender-war-")))continue;
            Obj action=child(WarEntryCollector.effectiveResult(row),"war_termination_result");String status=text(get(action,"status"));
            if(action==null || !same(action.get("episode_run_id"),snapshot.get("episode_run_id")) || !("submitted_pending".equals(status)||"applied".equals(status)))continue;
            BigInteger war=number(action,"war_id"),submitted=number(action,"submitted_date_raw");if(war==null || wars.contains(war) || submitted==null)continue;
            BigInteger elapsed=now.subtract(submitted);if(elapsed.signum()>=0 && elapsed.compareTo(BigInteger.valueOf(720))<0)return obj().text("status","cooldown").number("war_id",war).value("outcome",action.get("outcome")).number("submitted_date_raw",submitted).number("elapsed_raw",elapsed).number("remaining_raw",BigInteger.valueOf(720).subtract(elapsed)).value("history_index",row.get("index")).build();
            return null;
        }
        return null;
    }
}
